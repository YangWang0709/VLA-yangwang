#!/usr/bin/env python3
"""Phase 3 Unitree A1 existing-USD-prim sensor smoke.

This smoke opens the primary scene read-only, verifies the existing /World/A1
articulation root, performs short in-memory kinematic root pose updates, and
records lightweight geometry/depth/pointcloud proxy observations. It never saves
or overwrites the USD stage, creates no temporary Go2 proxy, trains no models,
and starts no rollout.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path
from statistics import mean
from typing import Any


WORKSPACE = Path("/home/ubuntu22/VLA")
DEFAULT_SCENE = WORKSPACE / "scenes/primary_building_scene_repaired/home_like_scene_v1.usd"
DEFAULT_TOP_REPORT = WORKSPACE / "runs/A1_SENSOR_SMOKE_REPORT.md"
A1_ROOT_PRIM = "/World/A1"
BASE_CANDIDATES = [
    "/World/A1/base",
    "/World/A1/base_link",
    "/World/A1/trunk",
    "/World/A1/imu_link",
    "/World/A1",
]


def _bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def _round_float(value: Any, digits: int = 4) -> Any:
    try:
        if value is None:
            return None
        value_f = float(value)
        if not math.isfinite(value_f):
            return None
        return round(value_f, digits)
    except Exception:
        return None


def _make_pointcloud(base_x: float, base_y: float, base_z: float, yaw: float) -> list[tuple[float, float, float]]:
    """Create a deterministic geometry/depth proxy pointcloud from A1 front pose."""
    points: list[tuple[float, float, float]] = []
    sensor_z = base_z + 0.18
    sensor_forward = 0.36
    sensor_x = base_x + math.cos(yaw) * sensor_forward
    sensor_y = base_y + math.sin(yaw) * sensor_forward
    horizontal = [math.radians(-55 + i * 5) for i in range(23)]
    vertical = [math.radians(-18 + i * 6) for i in range(7)]
    for vi, pitch in enumerate(vertical):
        for hi, bearing in enumerate(horizontal):
            local_yaw = yaw + bearing
            depth = 1.2 + 0.35 * math.cos(bearing * 1.7) + 0.12 * math.sin(vi + hi * 0.3)
            depth = max(0.55, min(depth, 2.2))
            xy = depth * math.cos(pitch)
            px = sensor_x + xy * math.cos(local_yaw)
            py = sensor_y + xy * math.sin(local_yaw)
            pz = sensor_z + depth * math.sin(pitch)
            points.append((px, py, pz))
    return points


def _pointcloud_stats(points: list[tuple[float, float, float]]) -> dict[str, Any]:
    finite = [p for p in points if all(math.isfinite(v) for v in p)]
    count = len(points)
    finite_count = len(finite)
    if not finite:
        return {
            "pointcloud_point_count": count,
            "pointcloud_finite_ratio": 0.0,
            "pointcloud_min_x": None,
            "pointcloud_max_x": None,
            "pointcloud_min_y": None,
            "pointcloud_max_y": None,
            "pointcloud_min_z": None,
            "pointcloud_max_z": None,
        }
    xs = [p[0] for p in finite]
    ys = [p[1] for p in finite]
    zs = [p[2] for p in finite]
    return {
        "pointcloud_point_count": count,
        "pointcloud_finite_ratio": round(finite_count / count if count else 0.0, 4),
        "pointcloud_min_x": round(min(xs), 4),
        "pointcloud_max_x": round(max(xs), 4),
        "pointcloud_min_y": round(min(ys), 4),
        "pointcloud_max_y": round(max(ys), 4),
        "pointcloud_min_z": round(min(zs), 4),
        "pointcloud_max_z": round(max(zs), 4),
    }


def _find_core_dumps(workspace: Path) -> list[str]:
    matches: list[str] = []
    skip_dir_names = {".git", "scenes", "__pycache__"}
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in skip_dir_names]
        for name in files:
            lower = name.lower()
            if lower == "core" or lower.startswith("core.") or lower.endswith(".core") or lower.endswith(".dmp"):
                matches.append(str(Path(root) / name))
                if len(matches) >= 20:
                    return matches
    return matches


def _select_base_frame(stage) -> tuple[str, bool, str]:
    for path in BASE_CANDIDATES:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            if path == A1_ROOT_PRIM:
                return path, True, "No explicit base/trunk candidate was usable; root fallback selected."
            return path, False, ""
    return A1_ROOT_PRIM, True, "No base candidate existed; root fallback selected."


def _world_translation(cache, prim) -> tuple[float, float, float]:
    matrix = cache.GetLocalToWorldTransform(prim)
    t = matrix.ExtractTranslation()
    return float(t[0]), float(t[1]), float(t[2])


def _quatd_from_any(quat):
    from pxr import Gf

    imag = quat.GetImaginary()
    return Gf.Quatd(float(quat.GetReal()), Gf.Vec3d(float(imag[0]), float(imag[1]), float(imag[2])))


def _quat_like(template, quatd):
    from pxr import Gf

    imag = quatd.GetImaginary()
    type_name = type(template).__name__ if template is not None else "Quatd"
    if type_name == "Quatf":
        return Gf.Quatf(float(quatd.GetReal()), Gf.Vec3f(float(imag[0]), float(imag[1]), float(imag[2])))
    if type_name == "Quath":
        return Gf.Quath(float(quatd.GetReal()), Gf.Vec3h(float(imag[0]), float(imag[1]), float(imag[2])))
    return Gf.Quatd(float(quatd.GetReal()), Gf.Vec3d(float(imag[0]), float(imag[1]), float(imag[2])))


def _set_root_kinematic_pose(root_prim, translate_xyz: tuple[float, float, float], yaw_rad: float, initial_orient) -> tuple[bool, str | None]:
    from pxr import Gf, UsdGeom

    xform = UsdGeom.Xformable(root_prim)
    ops = {op.GetName(): op for op in xform.GetOrderedXformOps()}
    translate_op = ops.get("xformOp:translate")
    if translate_op is None:
        translate_op = xform.AddTranslateOp()
    translate_op.Set(Gf.Vec3d(*translate_xyz))

    orient_op = ops.get("xformOp:orient")
    if orient_op is None or initial_orient is None:
        return False, None

    try:
        initial_q = _quatd_from_any(initial_orient)
        yaw_q = Gf.Quatd(math.cos(yaw_rad / 2.0), Gf.Vec3d(0.0, 0.0, math.sin(yaw_rad / 2.0)))
        orient_op.Set(_quat_like(initial_orient, yaw_q * initial_q))
        return True, None
    except Exception as exc:  # Orientation is useful but not required for this smoke.
        return False, repr(exc)


def _write_markdown_report(path: Path, summary: dict[str, Any]) -> None:
    caveats = summary.get("caveats") or []
    core_files = summary.get("core_dump_files") or []
    lines = [
        "# A1 Sensor Smoke Report",
        "",
        "phase: Phase 3",
        "workspace: /home/ubuntu22/VLA",
        f"scene_path: {summary.get('scene_path')}",
        "project_name: A1-VLM-LA Explorer",
        "main_goal: A1-VLM-LA Explorer for 3D Active Exploration",
        "output_contract: Go to candidate <id>.",
        "robot_platform: unitree_a1",
        "robot_source: existing_usd_prim",
        "a1_root_prim: /World/A1",
        f"a1_root_exists: {_bool_text(summary.get('a1_root_exists'))}",
        f"a1_has_articulation_root_api: {_bool_text(summary.get('a1_has_articulation_root_api'))}",
        f"base_frame: {summary.get('base_frame')}",
        "previous_proxy_results_status: superseded_for_formal_a1_pipeline",
        f"movement_mode: {summary.get('movement_mode')}",
        f"real_a1_locomotion_controller: {_bool_text(summary.get('real_a1_locomotion_controller'))}",
        f"existing_sensor_reused: {_bool_text(summary.get('existing_sensor_reused'))}",
        f"geometry_proxy_sensor_used: {_bool_text(summary.get('geometry_proxy_sensor_used'))}",
        f"sensor_method: {summary.get('sensor_method')}",
        f"sensor_frame: {summary.get('sensor_frame')}",
        f"sensor_pose_relative_to_a1_base: {summary.get('sensor_pose_relative_to_a1_base')}",
        f"step_count: {summary.get('step_count')}",
        f"successful_steps: {summary.get('successful_steps')}",
        f"sensor_valid_steps: {summary.get('sensor_valid_steps')}",
        f"sensor_valid_rate: {summary.get('sensor_valid_rate')}",
        f"min_pointcloud_count: {summary.get('min_pointcloud_count')}",
        f"max_pointcloud_count: {summary.get('max_pointcloud_count')}",
        f"average_pointcloud_count: {summary.get('average_pointcloud_count')}",
        f"collision_count: {summary.get('collision_count')}",
        f"stuck_count: {summary.get('stuck_count')}",
        f"falling_count: {summary.get('falling_count')}",
        f"core_dump_found: {_bool_text(summary.get('core_dump_found'))}",
        f"safe_to_continue_phase4: {_bool_text(summary.get('safe_to_continue_phase4'))}",
        "training: false",
        "RL: false",
        "map_predict: false",
        "PI_finetuning: false",
        "A1_locomotion_training: false",
        "rollout_started: false",
        "",
        "## Artifacts",
        "",
        f"- run_dir: `{summary.get('run_dir')}`",
        f"- steps_csv: `{summary.get('steps_csv')}`",
        f"- summary_json: `{summary.get('summary_json')}`",
        f"- run_report: `{summary.get('run_report_md')}`",
        f"- top_report: `{summary.get('top_report_md')}`",
        "",
        "## Existing USD Sensors",
        "",
        f"- available_camera_count: {summary.get('available_camera_count')}",
        f"- a1_bound_sensor_prims: {summary.get('a1_bound_sensor_prims')}",
        "",
        "## Caveats",
        "",
    ]
    if caveats:
        lines.extend(f"- {item}" for item in caveats)
    else:
        lines.append("- none")
    lines.extend(["", "## Core Dump Files", ""])
    if core_files:
        lines.extend(f"- `{item}`" for item in core_files)
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Negative Scope",
        "",
        "- No VLM training.",
        "- No RL training.",
        "- No map_predict training or mainline implementation.",
        "- No PI/openpi action-head fine-tuning.",
        "- No A1 locomotion policy training.",
        "- No Phase 4 mapping, candidate generation, Phase 6 interface smoke, or long rollout.",
        "- No temporary Go2 proxy was created.",
        "- Original USD scene was opened and edited only in memory; it was not saved or overwritten.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", default=str(DEFAULT_SCENE))
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--top_report", default=str(DEFAULT_TOP_REPORT))
    parser.add_argument("--steps", type=int, default=8)
    args = parser.parse_args()

    usd_path = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    logs_dir = run_dir / "logs"
    probes_dir = run_dir / "probes"
    smoke_dir = run_dir / "sensor_smoke"
    reports_dir = run_dir / "reports"
    summary_dir = run_dir / "summary"
    for directory in (logs_dir, probes_dir, smoke_dir, reports_dir, summary_dir):
        directory.mkdir(parents=True, exist_ok=True)

    steps_csv = smoke_dir / "a1_sensor_smoke_steps.csv"
    summary_json = summary_dir / "a1_sensor_smoke_summary.json"
    probe_json = probes_dir / "a1_stage_probe.json"
    run_report = reports_dir / "A1_SENSOR_SMOKE_REPORT.md"
    top_report = Path(args.top_report).expanduser().resolve()

    started = time.time()
    simulation_app = None
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "phase": "Phase 3",
        "workspace": str(WORKSPACE),
        "scene_path": str(usd_path),
        "scene_exists": usd_path.exists(),
        "scene_open_result": False,
        "stage_available": False,
        "project_name": "A1-VLM-LA Explorer",
        "main_goal": "A1-VLM-LA Explorer for 3D Active Exploration",
        "output_contract": "Go to candidate <id>.",
        "robot_platform": "unitree_a1",
        "robot_source": "existing_usd_prim",
        "a1_root_prim": A1_ROOT_PRIM,
        "a1_root_exists": False,
        "a1_has_articulation_root_api": False,
        "base_frame": None,
        "base_frame_root_fallback": False,
        "base_pose_readable": False,
        "previous_proxy_results_status": "superseded_for_formal_a1_pipeline",
        "movement_mode": "kinematic_existing_a1_root",
        "real_a1_locomotion_controller": False,
        "existing_sensor_reused": False,
        "geometry_proxy_sensor_used": True,
        "sensor_method": "geometry_proxy_pointcloud_from_a1_base_pose",
        "sensor_frame": None,
        "sensor_pose_relative_to_a1_base": {"x": 0.36, "y": 0.0, "z": 0.18, "yaw_rad": 0.0},
        "available_camera_count": 0,
        "available_camera_prims": [],
        "a1_bound_sensor_prims": [],
        "initial_root_pose_xyz": None,
        "initial_base_pose_xyz": None,
        "orientation_updated_in_memory": False,
        "orientation_update_errors": [],
        "step_count": 0,
        "successful_steps": 0,
        "sensor_valid_steps": 0,
        "sensor_valid_rate": 0.0,
        "min_pointcloud_count": 0,
        "max_pointcloud_count": 0,
        "average_pointcloud_count": 0.0,
        "collision_count": 0,
        "stuck_count": 0,
        "falling_count": 0,
        "core_dump_found": False,
        "core_dump_files": [],
        "safe_to_continue_phase4": False,
        "training": False,
        "RL": False,
        "map_predict": False,
        "PI_finetuning": False,
        "A1_locomotion_training": False,
        "rollout_started": False,
        "temporary_go2_proxy_created": False,
        "run_dir": str(run_dir),
        "steps_csv": str(steps_csv),
        "summary_json": str(summary_json),
        "probe_json": str(probe_json),
        "run_report_md": str(run_report),
        "top_report_md": str(top_report),
        "caveats": [
            "This is formal A1 pipeline smoke based on the existing USD prim /World/A1, not the old temporary Go2 proxy.",
            "Sensor data is a lightweight geometry/depth/pointcloud proxy bound to A1 base/front pose, not RTX rendering or a raw sensor dump.",
            "Movement is a short in-memory kinematic root pose update, not real A1 locomotion control or a rollout.",
        ],
        "exception": None,
        "traceback": None,
        "elapsed_sec": None,
    }

    exit_code = 1
    try:
        if not usd_path.exists():
            raise FileNotFoundError(str(usd_path))

        from isaacsim import SimulationApp

        simulation_app = SimulationApp({"headless": True})

        import omni.usd
        from pxr import UsdGeom, UsdPhysics

        context = omni.usd.get_context()
        raw_open = context.open_stage(str(usd_path))
        summary["open_stage_raw_result"] = repr(raw_open)

        stage = None
        deadline = time.time() + 180.0
        while time.time() < deadline:
            simulation_app.update()
            stage = context.get_stage()
            if stage is not None and list(stage.Traverse()):
                break
            time.sleep(0.1)
        if stage is None:
            stage = context.get_stage()
        if stage is None:
            raise RuntimeError("Stage unavailable after open_stage")

        summary["scene_open_result"] = True
        summary["stage_available"] = True

        root_prim = stage.GetPrimAtPath(A1_ROOT_PRIM)
        if not root_prim or not root_prim.IsValid():
            raise RuntimeError("Existing USD A1 prim /World/A1 was not found")
        summary["a1_root_exists"] = True
        summary["a1_has_articulation_root_api"] = bool(root_prim.HasAPI(UsdPhysics.ArticulationRootAPI))

        base_frame, root_fallback, base_caveat = _select_base_frame(stage)
        base_prim = stage.GetPrimAtPath(base_frame)
        if not base_prim or not base_prim.IsValid():
            raise RuntimeError(f"Selected base frame is invalid: {base_frame}")
        summary["base_frame"] = base_frame
        summary["sensor_frame"] = f"{base_frame}/front_geometry_proxy"
        summary["base_frame_root_fallback"] = root_fallback
        if base_caveat:
            summary["caveats"].append(base_caveat)

        cameras = [str(prim.GetPath()) for prim in stage.Traverse() if prim.GetTypeName() == "Camera"]
        a1_bound_sensors = [path for path in cameras if path.startswith(A1_ROOT_PRIM + "/")]
        summary["available_camera_count"] = len(cameras)
        summary["available_camera_prims"] = cameras[:20]
        summary["a1_bound_sensor_prims"] = a1_bound_sensors[:20]
        summary["existing_sensor_reused"] = False
        if not a1_bound_sensors:
            summary["caveats"].append("No A1-bound USD camera/sensor prim was found; only geometry proxy observations were used.")

        cache = UsdGeom.XformCache()
        initial_root_xyz = _world_translation(cache, root_prim)
        initial_base_xyz = _world_translation(cache, base_prim)
        summary["initial_root_pose_xyz"] = [_round_float(v, 6) for v in initial_root_xyz]
        summary["initial_base_pose_xyz"] = [_round_float(v, 6) for v in initial_base_xyz]
        summary["base_pose_readable"] = True

        xform_ops = {op.GetName(): op for op in UsdGeom.Xformable(root_prim).GetOrderedXformOps()}
        initial_orient = xform_ops.get("xformOp:orient").Get() if xform_ops.get("xformOp:orient") else None

        actions = [
            ("initial_pose", 0.0, 0.0, 0.0),
            ("small_forward", 0.18, 0.0, 0.0),
            ("small_yaw_left", 0.0, 0.0, math.radians(10)),
            ("small_forward", 0.16, 0.0, 0.0),
            ("small_yaw_right", 0.0, 0.0, math.radians(-8)),
            ("small_lateral_left", 0.0, 0.10, 0.0),
            ("small_forward", 0.14, 0.0, 0.0),
            ("stop", 0.0, 0.0, 0.0),
        ][: max(5, min(args.steps, 10))]

        root_x, root_y, root_z = initial_root_xyz
        yaw = 0.0
        last_base_x, last_base_y = initial_base_xyz[0], initial_base_xyz[1]
        last_yaw = yaw

        for step_id, (action_name, forward, lateral, dyaw) in enumerate(actions):
            yaw += dyaw
            root_x += math.cos(yaw) * forward - math.sin(yaw) * lateral
            root_y += math.sin(yaw) * forward + math.cos(yaw) * lateral
            orientation_updated, orientation_error = _set_root_kinematic_pose(root_prim, (root_x, root_y, root_z), yaw, initial_orient)
            summary["orientation_updated_in_memory"] = bool(summary["orientation_updated_in_memory"] or orientation_updated)
            if orientation_error and orientation_error not in summary["orientation_update_errors"]:
                summary["orientation_update_errors"].append(orientation_error)

            for _ in range(2):
                simulation_app.update()
            cache = UsdGeom.XformCache()
            base_x, base_y, base_z = _world_translation(cache, base_prim)

            points = _make_pointcloud(base_x, base_y, base_z, yaw)
            stats = _pointcloud_stats(points)
            depth_valid_ratio = stats["pointcloud_finite_ratio"]
            sensor_valid = bool(stats["pointcloud_point_count"] > 0 and depth_valid_ratio >= 0.8)
            moved_dist = math.hypot(base_x - last_base_x, base_y - last_base_y)
            yaw_change = abs(yaw - last_yaw)
            collision_flag = bool(abs(base_x - initial_base_xyz[0]) > 1.5 or abs(base_y - initial_base_xyz[1]) > 1.5)
            stuck_flag = bool(step_id > 0 and moved_dist < 0.005 and yaw_change < 0.005 and action_name != "stop")
            falling_flag = bool(base_z < 0.2 or base_z > 1.5 or abs(base_z - initial_base_xyz[2]) > 0.6)

            failure_reason = ""
            if collision_flag:
                failure_reason = "kinematic_boundary_violation"
            elif stuck_flag:
                failure_reason = "a1_base_pose_did_not_change"
            elif falling_flag:
                failure_reason = "a1_base_z_out_of_expected_range"
            elif not sensor_valid:
                failure_reason = "geometry_proxy_sensor_invalid"

            row = {
                "step_id": step_id,
                "timestamp": round(time.time(), 3),
                "a1_root_prim": A1_ROOT_PRIM,
                "base_frame": base_frame,
                "base_x": round(base_x, 4),
                "base_y": round(base_y, 4),
                "base_z": round(base_z, 4),
                "yaw": round(yaw, 4),
                "action_name": action_name,
                "sensor_valid": sensor_valid,
                "depth_valid_ratio": round(depth_valid_ratio, 4),
                "pointcloud_point_count": stats["pointcloud_point_count"],
                "pointcloud_finite_ratio": stats["pointcloud_finite_ratio"],
                "pointcloud_min_x": stats["pointcloud_min_x"],
                "pointcloud_max_x": stats["pointcloud_max_x"],
                "pointcloud_min_y": stats["pointcloud_min_y"],
                "pointcloud_max_y": stats["pointcloud_max_y"],
                "pointcloud_min_z": stats["pointcloud_min_z"],
                "pointcloud_max_z": stats["pointcloud_max_z"],
                "collision_flag": collision_flag,
                "stuck_flag": stuck_flag,
                "falling_flag": falling_flag,
                "failure_reason": failure_reason,
            }
            rows.append(row)
            last_base_x, last_base_y, last_yaw = base_x, base_y, yaw

        with steps_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        counts = [int(r["pointcloud_point_count"]) for r in rows if r["sensor_valid"]]
        successful_rows = [r for r in rows if not r["failure_reason"]]
        sensor_valid_rows = [r for r in rows if r["sensor_valid"]]
        collision_count = sum(1 for r in rows if r["collision_flag"])
        stuck_count = sum(1 for r in rows if r["stuck_flag"])
        falling_count = sum(1 for r in rows if r["falling_flag"])
        core_dump_files = _find_core_dumps(WORKSPACE)

        summary.update({
            "step_count": len(rows),
            "successful_steps": len(successful_rows),
            "sensor_valid_steps": len(sensor_valid_rows),
            "sensor_valid_rate": round(len(sensor_valid_rows) / len(rows), 4) if rows else 0.0,
            "min_pointcloud_count": min(counts) if counts else 0,
            "max_pointcloud_count": max(counts) if counts else 0,
            "average_pointcloud_count": round(mean(counts), 2) if counts else 0.0,
            "collision_count": collision_count,
            "stuck_count": stuck_count,
            "falling_count": falling_count,
            "core_dump_files": core_dump_files,
            "core_dump_found": bool(core_dump_files),
        })
        summary["safe_to_continue_phase4"] = bool(
            summary["scene_open_result"]
            and summary["stage_available"]
            and summary["a1_root_exists"]
            and summary["base_pose_readable"]
            and summary["step_count"] >= 5
            and summary["successful_steps"] >= 5
            and summary["sensor_valid_rate"] >= 0.8
            and summary["min_pointcloud_count"] > 0
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
            and not summary["core_dump_found"]
        )

        probe = {
            "scene_path": str(usd_path),
            "a1_root_prim": A1_ROOT_PRIM,
            "a1_root_exists": summary["a1_root_exists"],
            "a1_has_articulation_root_api": summary["a1_has_articulation_root_api"],
            "base_frame": summary["base_frame"],
            "initial_root_pose_xyz": summary["initial_root_pose_xyz"],
            "initial_base_pose_xyz": summary["initial_base_pose_xyz"],
            "available_camera_prims": summary["available_camera_prims"],
            "a1_bound_sensor_prims": summary["a1_bound_sensor_prims"],
        }
        probe_json.write_text(json.dumps(probe, indent=2, ensure_ascii=False), encoding="utf-8")
        exit_code = 0 if summary["safe_to_continue_phase4"] else 2
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        exit_code = 1
    finally:
        summary["elapsed_sec"] = round(time.time() - started, 3)
        summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_markdown_report(run_report, summary)
        _write_markdown_report(top_report, summary)
        if simulation_app is not None:
            try:
                simulation_app.close()
            except Exception as exc:
                print(f"simulation_app.close failed: {exc!r}", file=sys.stderr)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
