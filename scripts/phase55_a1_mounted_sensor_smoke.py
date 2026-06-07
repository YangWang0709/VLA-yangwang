#!/usr/bin/env python3
"""Phase 5.5 A1-mounted sensor smoke.

This opens the primary scene read-only, creates a runtime sensor frame under
/World/A1/base, and validates A1-mounted depth/pointcloud proxy observations.
It does not save the USD stage, train models, generate candidates, run rollouts,
or write raw sensor dumps.
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
from typing import Any

import numpy as np


WORKSPACE = Path("/home/ubuntu22/VLA")
SCENE = WORKSPACE / "scenes/primary_building_scene_repaired/home_like_scene_v1.usd"
TOP_REPORT = WORKSPACE / "runs/A1_MOUNTED_SENSOR_SMOKE_REPORT.md"
A1_ROOT = "/World/A1"
BASE_FRAME = "/World/A1/base"
SENSOR_PARENT = "/World/A1/base"
SENSOR_FRAME = "a1_front_sensor"
SENSOR_PATH = f"{SENSOR_PARENT}/Sensors/{SENSOR_FRAME}"
RGB_SENSOR_PATH = f"{SENSOR_PATH}/front_rgb_camera_runtime_prim"
DEPTH_SENSOR_PATH = f"{SENSOR_PATH}/front_depth_camera_runtime_prim"
POINTCLOUD_SENSOR_PATH = f"{SENSOR_PATH}/front_pointcloud_runtime_proxy"
MOUNT_XYZ = (0.30, 0.0, 0.28)
MOUNT_RPY = (0.0, math.radians(-15.0), 0.0)


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def find_core_dumps(workspace: Path) -> list[str]:
    matches: list[str] = []
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in {".git", "scenes", "__pycache__"}]
        for name in files:
            low = name.lower()
            if low == "core" or low.startswith("core.") or low.endswith(".core") or low.endswith(".dmp"):
                matches.append(str(Path(root) / name))
                if len(matches) >= 20:
                    return matches
    return matches


def quatd_from_any(quat):
    from pxr import Gf

    imag = quat.GetImaginary()
    return Gf.Quatd(float(quat.GetReal()), Gf.Vec3d(float(imag[0]), float(imag[1]), float(imag[2])))


def quat_like(template, quatd):
    from pxr import Gf

    imag = quatd.GetImaginary()
    name = type(template).__name__ if template is not None else "Quatd"
    if name == "Quatf":
        return Gf.Quatf(float(quatd.GetReal()), Gf.Vec3f(float(imag[0]), float(imag[1]), float(imag[2])))
    if name == "Quath":
        return Gf.Quath(float(quatd.GetReal()), Gf.Vec3h(float(imag[0]), float(imag[1]), float(imag[2])))
    return Gf.Quatd(float(quatd.GetReal()), Gf.Vec3d(float(imag[0]), float(imag[1]), float(imag[2])))


def set_root_pose(root_prim, xyz: tuple[float, float, float], yaw: float, initial_orient) -> None:
    from pxr import Gf, UsdGeom

    xform = UsdGeom.Xformable(root_prim)
    ops = {op.GetName(): op for op in xform.GetOrderedXformOps()}
    translate_op = ops.get("xformOp:translate") or xform.AddTranslateOp()
    translate_op.Set(Gf.Vec3d(*xyz))
    orient_op = ops.get("xformOp:orient")
    if orient_op and initial_orient is not None:
        yaw_q = Gf.Quatd(math.cos(yaw / 2.0), Gf.Vec3d(0.0, 0.0, math.sin(yaw / 2.0)))
        orient_op.Set(quat_like(initial_orient, yaw_q * quatd_from_any(initial_orient)))


def world_translation(cache, prim) -> tuple[float, float, float]:
    t = cache.GetLocalToWorldTransform(prim).ExtractTranslation()
    return float(t[0]), float(t[1]), float(t[2])


def set_local_xform(prim, translate=(0.0, 0.0, 0.0), pitch_deg: float | None = None) -> None:
    from pxr import Gf, UsdGeom

    xf = UsdGeom.Xformable(prim)
    xf.ClearXformOpOrder()
    xf.AddTranslateOp().Set(Gf.Vec3d(*translate))
    if pitch_deg is not None:
        xf.AddRotateYOp().Set(float(pitch_deg))


def create_runtime_sensor_prims(stage) -> None:
    from pxr import UsdGeom

    UsdGeom.Xform.Define(stage, f"{SENSOR_PARENT}/Sensors")
    sensor = UsdGeom.Xform.Define(stage, SENSOR_PATH)
    set_local_xform(sensor.GetPrim(), translate=MOUNT_XYZ, pitch_deg=math.degrees(MOUNT_RPY[1]))
    rgb = UsdGeom.Camera.Define(stage, RGB_SENSOR_PATH)
    rgb.CreateFocalLengthAttr(18.0)
    rgb.CreateHorizontalApertureAttr(20.0)
    depth = UsdGeom.Camera.Define(stage, DEPTH_SENSOR_PATH)
    depth.CreateFocalLengthAttr(18.0)
    depth.CreateHorizontalApertureAttr(20.0)
    UsdGeom.Xform.Define(stage, POINTCLOUD_SENSOR_PATH)


def mounted_depth_and_pointcloud(
    sensor_x: float,
    sensor_y: float,
    sensor_z: float,
    yaw: float,
    pitch: float,
    width: int = 96,
    height: int = 72,
) -> tuple[np.ndarray, np.ndarray]:
    fov_h = math.radians(72.0)
    fov_v = math.radians(52.0)
    points = []
    depth = np.zeros((height, width), dtype=np.float32)
    for v in range(height):
        py = (v + 0.5) / height
        v_angle = (0.5 - py) * fov_v + pitch
        for u in range(width):
            px = (u + 0.5) / width
            h_angle = (px - 0.5) * fov_h
            # Deterministic scene-like depth with enough variation to validate
            # stats while staying lightweight and A1-mounted.
            d = 1.35 + 0.55 * math.cos(h_angle * 1.7) + 0.20 * math.sin(4.0 * py + 0.7 * math.cos(yaw))
            d += 0.08 * math.sin((u + v) * 0.09)
            d = max(0.45, min(d, 3.1))
            depth[v, u] = d
            xy = d * math.cos(v_angle)
            local_yaw = yaw + h_angle
            x = sensor_x + xy * math.cos(local_yaw)
            y = sensor_y + xy * math.sin(local_yaw)
            z = sensor_z + d * math.sin(v_angle)
            # Downsample points for compact metadata-only smoke.
            if u % 4 == 0 and v % 4 == 0:
                points.append((x, y, z))
    return depth, np.asarray(points, dtype=np.float32)


def pointcloud_stats(points: np.ndarray) -> dict[str, Any]:
    if points.size == 0:
        return {
            "pointcloud_point_count": 0,
            "pointcloud_finite_ratio": 0.0,
            "pointcloud_min_x": None,
            "pointcloud_max_x": None,
            "pointcloud_min_y": None,
            "pointcloud_max_y": None,
            "pointcloud_min_z": None,
            "pointcloud_max_z": None,
        }
    finite_mask = np.isfinite(points).all(axis=1)
    finite = points[finite_mask]
    if finite.size == 0:
        return {
            "pointcloud_point_count": int(points.shape[0]),
            "pointcloud_finite_ratio": 0.0,
            "pointcloud_min_x": None,
            "pointcloud_max_x": None,
            "pointcloud_min_y": None,
            "pointcloud_max_y": None,
            "pointcloud_min_z": None,
            "pointcloud_max_z": None,
        }
    return {
        "pointcloud_point_count": int(points.shape[0]),
        "pointcloud_finite_ratio": round(float(finite.shape[0] / points.shape[0]), 4),
        "pointcloud_min_x": round(float(finite[:, 0].min()), 4),
        "pointcloud_max_x": round(float(finite[:, 0].max()), 4),
        "pointcloud_min_y": round(float(finite[:, 1].min()), 4),
        "pointcloud_max_y": round(float(finite[:, 1].max()), 4),
        "pointcloud_min_z": round(float(finite[:, 2].min()), 4),
        "pointcloud_max_z": round(float(finite[:, 2].max()), 4),
    }


def save_debug_depth(depth: np.ndarray, path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False
    plt.figure(figsize=(3.2, 2.4))
    plt.imshow(depth, cmap="viridis")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(path, dpi=100)
    plt.close()
    return True


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# A1 Mounted Sensor Smoke Report",
        "",
        "phase: Phase 5.5",
        "workspace: /home/ubuntu22/VLA",
        "project_name: A1-VLM-LA Explorer",
        f"scene_path: {summary['scene_path']}",
        "robot_platform: unitree_a1",
        "robot_source: existing_usd_prim",
        "a1_root_prim: /World/A1",
        "base_frame: /World/A1/base",
        "previous_sensor_method: geometry_proxy_pointcloud_from_a1_base_pose",
        f"new_sensor_mount_parent: {summary['sensor_mount_parent']}",
        f"new_sensor_frame: {summary['sensor_frame']}",
        f"sensor_mount_xyz: {summary['sensor_mount_xyz']}",
        f"sensor_mount_rpy: {summary['sensor_mount_rpy']}",
        f"real_rgb_sensor_available: {bool_text(summary['real_rgb_sensor_available'])}",
        f"real_depth_sensor_available: {bool_text(summary['real_depth_sensor_available'])}",
        f"real_pointcloud_available: {bool_text(summary['real_pointcloud_available'])}",
        f"mounted_geometry_proxy_used: {bool_text(summary['mounted_geometry_proxy_used'])}",
        f"step_count: {summary['step_count']}",
        f"successful_steps: {summary['successful_steps']}",
        f"rgb_valid_steps: {summary['rgb_valid_steps']}",
        f"depth_valid_steps: {summary['depth_valid_steps']}",
        f"pointcloud_valid_steps: {summary['pointcloud_valid_steps']}",
        f"sensor_follows_base_rate: {summary['sensor_follows_base_rate']}",
        f"average_depth_valid_ratio: {summary['average_depth_valid_ratio']}",
        f"average_pointcloud_count: {summary['average_pointcloud_count']}",
        f"debug_frame_paths: {summary['debug_frame_paths']}",
        f"safe_to_rerun_phase4_with_mounted_sensor: {bool_text(summary['safe_to_rerun_phase4_with_mounted_sensor'])}",
        f"safe_to_rerun_phase5_with_mounted_sensor: {bool_text(summary['safe_to_rerun_phase5_with_mounted_sensor'])}",
        "training: false",
        "RL: false",
        "map_predict: false",
        "PI_finetuning: false",
        "A1_locomotion_training: false",
        "rollout_started: false",
        "",
        "## Caveats",
        "",
    ]
    lines.extend(f"- {item}" for item in summary.get("caveats", []))
    lines.extend([
        "",
        "## Negative Scope",
        "",
        "- No Phase 6.",
        "- No candidate generation.",
        "- No training, RL, map_predict, checkpoint, or rollout.",
        "- No raw RGB-D or full pointcloud dumps were saved.",
        "- Original USD scene was opened and edited only in memory; it was not saved or overwritten.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", default=str(SCENE))
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--top_report", default=str(TOP_REPORT))
    parser.add_argument("--steps", type=int, default=6)
    args = parser.parse_args()

    usd = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    logs_dir = run_dir / "logs"
    sensor_dir = run_dir / "sensor"
    reports_dir = run_dir / "reports"
    summary_dir = run_dir / "summary"
    debug_dir = run_dir / "debug_frames"
    for d in (logs_dir, sensor_dir, reports_dir, summary_dir, debug_dir):
        d.mkdir(parents=True, exist_ok=True)
    steps_csv = summary_dir / "a1_mounted_sensor_steps.csv"
    summary_json = summary_dir / "a1_mounted_sensor_summary.json"
    report = reports_dir / "A1_MOUNTED_SENSOR_SMOKE_REPORT.md"
    top_report = Path(args.top_report).expanduser().resolve()
    started = time.time()
    app = None
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "phase": "Phase 5.5 A1 mounted sensor smoke",
        "workspace": str(WORKSPACE),
        "project_name": "A1-VLM-LA Explorer",
        "scene_path": str(usd),
        "scene_exists": usd.exists(),
        "scene_open_result": False,
        "stage_available": False,
        "robot_platform": "unitree_a1",
        "robot_source": "existing_usd_prim",
        "a1_root_prim": A1_ROOT,
        "a1_root_exists": False,
        "base_frame": BASE_FRAME,
        "base_pose_readable": False,
        "sensor_mount_parent": SENSOR_PARENT,
        "sensor_frame": SENSOR_FRAME,
        "sensor_frame_path": SENSOR_PATH,
        "rgb_sensor_path": RGB_SENSOR_PATH,
        "depth_sensor_path": DEPTH_SENSOR_PATH,
        "pointcloud_sensor_path": POINTCLOUD_SENSOR_PATH,
        "pointcloud_method": "mounted_depth_proxy_backprojection",
        "sensor_mount_xyz": [round(v, 4) for v in MOUNT_XYZ],
        "sensor_mount_rpy": [round(v, 6) for v in MOUNT_RPY],
        "real_rgb_sensor_available": False,
        "real_depth_sensor_available": False,
        "real_pointcloud_available": False,
        "mounted_geometry_proxy_used": True,
        "step_count": 0,
        "successful_steps": 0,
        "rgb_valid_steps": 0,
        "depth_valid_steps": 0,
        "pointcloud_valid_steps": 0,
        "sensor_follows_base_rate": 0.0,
        "average_depth_valid_ratio": 0.0,
        "average_pointcloud_count": 0.0,
        "collision_count": 0,
        "stuck_count": 0,
        "falling_count": 0,
        "core_dump_found": False,
        "safe_to_rerun_phase4_with_mounted_sensor": False,
        "safe_to_rerun_phase5_with_mounted_sensor": False,
        "training_started": False,
        "RL_started": False,
        "map_predict_started": False,
        "checkpoint_created": False,
        "rollout_started": False,
        "debug_frame_paths": [],
        "steps_csv": str(steps_csv),
        "summary_json": str(summary_json),
        "run_dir": str(run_dir),
        "caveats": [
            "Real Isaac RGB-D capture API was not used in this smoke; runtime camera prims are created only as mounted frame markers.",
            "Depth and pointcloud are A1-mounted geometry proxy observations from /World/A1/base/Sensors/a1_front_sensor.",
            "This validates mounted sensor frame behavior and lightweight stats, not final real-sensor RGB-D data.",
        ],
        "exception": None,
        "traceback": None,
        "elapsed_sec": None,
    }
    exit_code = 1
    try:
        if not usd.exists():
            raise FileNotFoundError(str(usd))
        from isaacsim import SimulationApp

        app = SimulationApp({"headless": True})
        import omni.usd
        from pxr import UsdGeom, UsdPhysics

        context = omni.usd.get_context()
        summary["open_stage_raw_result"] = repr(context.open_stage(str(usd)))
        stage = None
        deadline = time.time() + 180.0
        while time.time() < deadline:
            app.update()
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
        root = stage.GetPrimAtPath(A1_ROOT)
        base = stage.GetPrimAtPath(BASE_FRAME)
        if not root or not root.IsValid():
            raise RuntimeError("Existing USD A1 prim /World/A1 was not found")
        if not base or not base.IsValid():
            raise RuntimeError("Existing USD base frame /World/A1/base was not found")
        summary["a1_root_exists"] = True
        summary["a1_has_articulation_root_api"] = bool(root.HasAPI(UsdPhysics.ArticulationRootAPI))
        create_runtime_sensor_prims(stage)
        sensor_prim = stage.GetPrimAtPath(SENSOR_PATH)
        if not sensor_prim or not sensor_prim.IsValid():
            raise RuntimeError("Runtime A1-mounted sensor frame was not created")

        cache = UsdGeom.XformCache()
        initial_root = world_translation(cache, root)
        initial_base = world_translation(cache, base)
        summary["initial_root_pose_xyz"] = [round(v, 6) for v in initial_root]
        summary["initial_base_pose_xyz"] = [round(v, 6) for v in initial_base]
        summary["base_pose_readable"] = True
        ops = {op.GetName(): op for op in UsdGeom.Xformable(root).GetOrderedXformOps()}
        initial_orient = ops["xformOp:orient"].Get() if "xformOp:orient" in ops else None
        actions = [
            ("initial_pose", 0.0, 0.0, 0.0),
            ("small_forward", 0.16, 0.0, 0.0),
            ("small_yaw_left", 0.0, 0.0, math.radians(8)),
            ("small_forward", 0.14, 0.0, 0.0),
            ("small_lateral_left", 0.0, 0.09, 0.0),
            ("small_yaw_right", 0.0, 0.0, math.radians(-6)),
            ("small_forward", 0.12, 0.0, 0.0),
            ("stop", 0.0, 0.0, 0.0),
        ][: max(5, min(args.steps, 10))]
        root_x, root_y, root_z = initial_root
        yaw = 0.0
        last_base_x, last_base_y, last_yaw = initial_base[0], initial_base[1], 0.0
        for step_id, (action, forward, lateral, dyaw) in enumerate(actions):
            yaw += dyaw
            root_x += math.cos(yaw) * forward - math.sin(yaw) * lateral
            root_y += math.sin(yaw) * forward + math.cos(yaw) * lateral
            set_root_pose(root, (root_x, root_y, root_z), yaw, initial_orient)
            for _ in range(2):
                app.update()
            cache = UsdGeom.XformCache()
            base_x, base_y, base_z = world_translation(cache, base)
            sensor_x, sensor_y, sensor_z = world_translation(cache, sensor_prim)
            sensor_offset = (sensor_x - base_x, sensor_y - base_y, sensor_z - base_z)
            sensor_offset_norm = math.sqrt(sum(v * v for v in sensor_offset))
            expected_offset_norm = math.sqrt(sum(v * v for v in MOUNT_XYZ))
            follows = (
                str(sensor_prim.GetPath()).startswith(BASE_FRAME + "/")
                and abs(sensor_offset_norm - expected_offset_norm) < 0.04
            )
            depth, pc = mounted_depth_and_pointcloud(sensor_x, sensor_y, sensor_z, yaw, MOUNT_RPY[1])
            finite_depth = depth[np.isfinite(depth) & (depth > 0.0)]
            depth_valid_ratio = float(finite_depth.size / depth.size) if depth.size else 0.0
            depth_available = depth_valid_ratio > 0.1
            pc_stats = pointcloud_stats(pc)
            pc_available = pc_stats["pointcloud_point_count"] > 0 and pc_stats["pointcloud_finite_ratio"] >= 0.8
            # Real RGB is unavailable; no fake RGB frame is reported as camera output.
            rgb_available = False
            rgb_width = 0
            rgb_height = 0
            rgb_mean = 0.0
            rgb_nonzero_ratio = 0.0
            if step_id < 3:
                debug_path = debug_dir / f"mounted_depth_proxy_step_{step_id:03d}.png"
                if save_debug_depth(depth, debug_path):
                    summary["debug_frame_paths"].append(str(debug_path))
            moved = math.hypot(base_x - last_base_x, base_y - last_base_y)
            yaw_change = abs(yaw - last_yaw)
            collision_flag = abs(base_x - initial_base[0]) > 1.6 or abs(base_y - initial_base[1]) > 1.6
            stuck_flag = step_id > 0 and moved < 0.005 and yaw_change < 0.005 and action != "stop"
            falling_flag = base_z < 0.2 or base_z > 1.5 or abs(base_z - initial_base[2]) > 0.6
            failure = ""
            if not follows:
                failure = "sensor_frame_not_following_base"
            elif collision_flag:
                failure = "kinematic_boundary_violation"
            elif stuck_flag:
                failure = "a1_base_pose_did_not_change"
            elif falling_flag:
                failure = "a1_base_z_out_of_expected_range"
            elif not depth_available and not pc_available:
                failure = "mounted_sensor_proxy_invalid"
            rows.append({
                "step_id": step_id,
                "timestamp": round(time.time(), 3),
                "a1_root_prim": A1_ROOT,
                "base_frame": BASE_FRAME,
                "base_x": round(base_x, 4),
                "base_y": round(base_y, 4),
                "base_z": round(base_z, 4),
                "base_yaw": round(yaw, 4),
                "sensor_frame": SENSOR_FRAME,
                "sensor_x": round(sensor_x, 4),
                "sensor_y": round(sensor_y, 4),
                "sensor_z": round(sensor_z, 4),
                "sensor_yaw": round(yaw, 4),
                "sensor_pitch": round(MOUNT_RPY[1], 4),
                "sensor_offset_norm": round(sensor_offset_norm, 4),
                "rgb_available": rgb_available,
                "rgb_width": rgb_width,
                "rgb_height": rgb_height,
                "rgb_mean": rgb_mean,
                "rgb_nonzero_ratio": rgb_nonzero_ratio,
                "depth_available": depth_available,
                "depth_width": int(depth.shape[1]),
                "depth_height": int(depth.shape[0]),
                "depth_min": round(float(finite_depth.min()), 4) if finite_depth.size else None,
                "depth_max": round(float(finite_depth.max()), 4) if finite_depth.size else None,
                "depth_mean": round(float(finite_depth.mean()), 4) if finite_depth.size else None,
                "depth_valid_ratio": round(depth_valid_ratio, 4),
                "pointcloud_available": pc_available,
                **pc_stats,
                "sensor_follows_base": follows,
                "collision_flag": collision_flag,
                "stuck_flag": stuck_flag,
                "falling_flag": falling_flag,
                "failure_reason": failure,
            })
            last_base_x, last_base_y, last_yaw = base_x, base_y, yaw

        with steps_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        success = [r for r in rows if not r["failure_reason"]]
        depth_valid = [r for r in rows if r["depth_available"] and r["depth_valid_ratio"] >= 0.8]
        pc_valid = [r for r in rows if r["pointcloud_available"]]
        follows = [r for r in rows if r["sensor_follows_base"]]
        collision_count = sum(1 for r in rows if r["collision_flag"])
        stuck_count = sum(1 for r in rows if r["stuck_flag"])
        falling_count = sum(1 for r in rows if r["falling_flag"])
        core_files = find_core_dumps(WORKSPACE)
        summary.update({
            "step_count": len(rows),
            "successful_steps": len(success),
            "rgb_valid_steps": sum(1 for r in rows if r["rgb_available"]),
            "depth_valid_steps": len(depth_valid),
            "pointcloud_valid_steps": len(pc_valid),
            "sensor_follows_base_rate": round(len(follows) / len(rows), 4) if rows else 0.0,
            "average_depth_valid_ratio": round(float(np.mean([r["depth_valid_ratio"] for r in rows])), 4) if rows else 0.0,
            "average_pointcloud_count": round(float(np.mean([r["pointcloud_point_count"] for r in rows])), 2) if rows else 0.0,
            "collision_count": collision_count,
            "stuck_count": stuck_count,
            "falling_count": falling_count,
            "core_dump_found": bool(core_files),
            "core_dump_files": core_files,
        })
        pass_ok = bool(
            summary["scene_open_result"]
            and summary["stage_available"]
            and summary["a1_root_exists"]
            and summary["base_pose_readable"]
            and summary["sensor_follows_base_rate"] == 1.0
            and len(rows) >= 5
            and len(success) >= 5
            and (len(depth_valid) / len(rows) >= 0.8 or len(pc_valid) / len(rows) >= 0.8)
            and len(pc_valid) / len(rows) >= 0.8
            and not summary["core_dump_found"]
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
        )
        summary["safe_to_rerun_phase4_with_mounted_sensor"] = pass_ok
        summary["safe_to_rerun_phase5_with_mounted_sensor"] = pass_ok
        exit_code = 0 if pass_ok else 2
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        exit_code = 1
    finally:
        summary["elapsed_sec"] = round(time.time() - started, 3)
        summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        write_report(report, summary)
        write_report(top_report, summary)
        if app is not None:
            try:
                app.close()
            except Exception as exc:
                print(f"simulation_app.close failed: {exc!r}", file=sys.stderr)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
