#!/usr/bin/env python3
"""Phase 3 temporary Go2-shaped proxy sensor smoke.

This script opens the primary USD scene read-only, creates a temporary in-memory
Go2-shaped sensor carrier, runs a short kinematic pose/sensor smoke, and writes
only lightweight CSV/JSON/Markdown artifacts. It never saves the USD stage.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
import traceback
from pathlib import Path
from statistics import mean


def _bool(value: bool) -> bool:
    return bool(value)


def _make_pointcloud(base_x: float, base_y: float, base_z: float, yaw: float) -> list[tuple[float, float, float]]:
    """Create a deterministic lightweight geometry/depth proxy pointcloud."""
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
            # Deterministic pseudo-depth with mild angular variation. This is a
            # geometry proxy, not RTX rendering and not a raw sensor dump.
            depth = 1.2 + 0.35 * math.cos(bearing * 1.7) + 0.12 * math.sin(vi + hi * 0.3)
            depth = max(0.55, min(depth, 2.2))
            xy = depth * math.cos(pitch)
            px = sensor_x + xy * math.cos(local_yaw)
            py = sensor_y + xy * math.sin(local_yaw)
            pz = sensor_z + depth * math.sin(pitch)
            points.append((px, py, pz))
    return points


def _pointcloud_stats(points: list[tuple[float, float, float]]) -> dict[str, float | int | bool | None]:
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
            "pointcloud_bounds": None,
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
        "pointcloud_bounds": {
            "min": [round(min(xs), 4), round(min(ys), 4), round(min(zs), 4)],
            "max": [round(max(xs), 4), round(max(ys), 4), round(max(zs), 4)],
        },
    }


def _set_xform(prim, translate=(0.0, 0.0, 0.0), yaw_deg: float | None = None, scale=None) -> None:
    from pxr import Gf, UsdGeom

    xf = UsdGeom.Xformable(prim)
    xf.ClearXformOpOrder()
    xf.AddTranslateOp().Set(Gf.Vec3d(*translate))
    if yaw_deg is not None:
        xf.AddRotateZOp().Set(float(yaw_deg))
    if scale is not None:
        xf.AddScaleOp().Set(Gf.Vec3d(*scale))


def _define_cube(stage, path: str, translate, scale) -> None:
    from pxr import UsdGeom

    cube = UsdGeom.Cube.Define(stage, path)
    cube.CreateSizeAttr(1.0)
    _set_xform(cube.GetPrim(), translate=translate, scale=scale)


def _create_temporary_proxy(stage, root_path: str) -> None:
    from pxr import UsdGeom

    root = UsdGeom.Xform.Define(stage, root_path)
    root.GetPrim().SetCustomDataByKey("robot_platform_target", "Unitree Go2")
    root.GetPrim().SetCustomDataByKey("robot_source", "temporary_go2_proxy")
    root.GetPrim().SetCustomDataByKey("not_final_robot_asset", True)

    UsdGeom.Xform.Define(stage, f"{root_path}/temporary_go2_base_link")
    _define_cube(stage, f"{root_path}/body_visual_collision_proxy", (0.0, 0.0, 0.0), (0.46, 0.18, 0.12))
    leg_positions = [
        (0.32, 0.13, -0.22),
        (0.32, -0.13, -0.22),
        (-0.32, 0.13, -0.22),
        (-0.32, -0.13, -0.22),
    ]
    for idx, pos in enumerate(leg_positions):
        _define_cube(stage, f"{root_path}/leg_{idx}_visual_collision_proxy", pos, (0.05, 0.04, 0.22))
    sensor = UsdGeom.Xform.Define(stage, f"{root_path}/go2_front_camera")
    _set_xform(sensor.GetPrim(), translate=(0.36, 0.0, 0.18))


def _write_markdown_report(path: Path, summary: dict) -> None:
    lines = [
        "# Go2 Sensor Smoke Report",
        "",
        "phase: Phase 3",
        "workspace: /home/ubuntu22/VLA",
        f"scene_path: {summary['scene_path']}",
        "robot_platform_target: Unitree Go2",
        "go2_in_usd_found: false",
        "robot_source: temporary_go2_proxy",
        "temporary_go2_proxy_used: true",
        "not_final_robot_asset: true",
        "movement_mode: kinematic_proxy",
        "real_go2_locomotion_controller: false",
        f"go2_root_prim: {summary['go2_root_prim']}",
        "base_frame: temporary_go2_base_link",
        f"sensor_method: {summary['sensor_method']}",
        f"step_count: {summary['step_count']}",
        f"successful_steps: {summary['successful_steps']}",
        f"sensor_valid_steps: {summary['sensor_valid_steps']}",
        f"sensor_valid_rate: {summary['sensor_valid_rate']}",
        f"min_pointcloud_count: {summary['min_pointcloud_count']}",
        f"max_pointcloud_count: {summary['max_pointcloud_count']}",
        f"average_pointcloud_count: {summary['average_pointcloud_count']}",
        f"collision_count: {summary['collision_count']}",
        f"stuck_count: {summary['stuck_count']}",
        f"falling_count: {summary['falling_count']}",
        f"core_dump_found: {str(summary['core_dump_found']).lower()}",
        f"safe_to_continue_phase4: {str(summary['safe_to_continue_phase4']).lower()}",
        "training: false",
        "RL: false",
        "map_predict: false",
        "PI_finetuning: false",
        "Go2_locomotion_training: false",
        "rollout_started: false",
        "",
        "## Artifacts",
        "",
        f"- steps_csv: `{summary['steps_csv']}`",
        f"- summary_json: `{summary['summary_json']}`",
        "",
        "## Caveats",
        "",
    ]
    for caveat in summary.get("caveats", []):
        lines.append(f"- {caveat}")
    if not summary.get("caveats"):
        lines.append("- none")
    lines.extend([
        "",
        "## Negative Scope",
        "",
        "- No VLM training.",
        "- No RL training.",
        "- No map_predict training or mainline implementation.",
        "- No PI/openpi action-head fine-tuning.",
        "- No Go2 locomotion policy training.",
        "- No long rollout, mapping, candidate generation, or VLM inference.",
        "- Original USD scene was opened and edited only in memory; it was not saved or overwritten.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", required=True)
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--steps", type=int, default=8)
    args = parser.parse_args()

    usd_path = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    logs_dir = run_dir / "logs"
    smoke_dir = run_dir / "sensor_smoke"
    reports_dir = run_dir / "reports"
    probes_dir = run_dir / "probes"
    for directory in (logs_dir, smoke_dir, reports_dir, probes_dir):
        directory.mkdir(parents=True, exist_ok=True)

    steps_csv = smoke_dir / "go2_sensor_smoke_steps.csv"
    summary_json = smoke_dir / "go2_sensor_smoke_summary.json"
    report_md = reports_dir / "GO2_SENSOR_SMOKE_REPORT.md"

    root_path = "/World/TemporaryGo2Proxy"
    simulation_app = None
    started = time.time()
    rows: list[dict] = []
    summary: dict = {
        "phase": "Phase 3",
        "workspace": "/home/ubuntu22/VLA",
        "scene_path": str(usd_path),
        "scene_exists": usd_path.exists(),
        "scene_open_result": False,
        "stage_available": False,
        "robot_platform_target": "Unitree Go2",
        "go2_in_usd_found": False,
        "robot_source": "temporary_go2_proxy",
        "temporary_go2_proxy_used": True,
        "not_final_robot_asset": True,
        "movement_mode": "kinematic_proxy",
        "real_go2_locomotion_controller": False,
        "go2_root_prim": root_path,
        "base_frame": "temporary_go2_base_link",
        "sensor_method": "geometry/depth/pointcloud proxy",
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
        "safe_to_continue_phase4": False,
        "training": False,
        "RL": False,
        "map_predict": False,
        "PI_finetuning": False,
        "Go2_locomotion_training": False,
        "rollout_started": False,
        "steps_csv": str(steps_csv),
        "summary_json": str(summary_json),
        "report_md": str(report_md),
        "caveats": [
            "Phase 2 did not verify an existing Go2 prim; this run uses a temporary Go2-shaped proxy and must not be treated as a final robot asset.",
            "Sensor data is a lightweight geometry/depth/pointcloud proxy, not an RTX camera or raw sensor dump.",
            "Movement is kinematic proxy pose update, not real Go2 locomotion control.",
        ],
        "exception": None,
        "traceback": None,
        "elapsed_sec": None,
    }

    try:
        if not usd_path.exists():
            raise FileNotFoundError(str(usd_path))

        from isaacsim import SimulationApp

        simulation_app = SimulationApp({"headless": True})

        import omni.usd
        from pxr import Gf, UsdGeom

        context = omni.usd.get_context()
        context.open_stage(str(usd_path))
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

        _create_temporary_proxy(stage, root_path)
        root_prim = stage.GetPrimAtPath(root_path)
        if not root_prim or not root_prim.IsValid():
            raise RuntimeError("TemporaryGo2Proxy prim was not created")

        # Conservative default pose. This is intentionally independent of /World/A1.
        base_x = -1.2
        base_y = -1.2
        base_z = 0.42
        yaw = 0.0
        actions = [
            ("initial_pose", 0.0, 0.0, 0.0),
            ("forward_small_step", 0.25, 0.0, 0.0),
            ("rotate_left_small", 0.0, 0.0, math.radians(15)),
            ("forward_small_step", 0.22, 0.0, 0.0),
            ("rotate_right_small", 0.0, 0.0, math.radians(-12)),
            ("strafe_left_small", 0.0, 0.16, 0.0),
            ("forward_small_step", 0.20, 0.0, 0.0),
            ("rotate_right_small", 0.0, 0.0, math.radians(-10)),
        ][: max(5, min(args.steps, 10))]

        last_x, last_y, last_yaw = base_x, base_y, yaw
        for step_id, (action_name, forward, lateral, dyaw) in enumerate(actions):
            yaw += dyaw
            base_x += math.cos(yaw) * forward - math.sin(yaw) * lateral
            base_y += math.sin(yaw) * forward + math.cos(yaw) * lateral
            _set_xform(root_prim, translate=(base_x, base_y, base_z), yaw_deg=math.degrees(yaw))
            for _ in range(2):
                simulation_app.update()

            points = _make_pointcloud(base_x, base_y, base_z, yaw)
            stats = _pointcloud_stats(points)
            depth_valid_ratio = stats["pointcloud_finite_ratio"]
            sensor_valid = bool(depth_valid_ratio >= 0.8 and stats["pointcloud_point_count"] > 0)
            moved_dist = math.hypot(base_x - last_x, base_y - last_y)
            yaw_change = abs(yaw - last_yaw)
            stuck_flag = bool(step_id > 0 and moved_dist < 0.005 and yaw_change < 0.005)
            falling_flag = bool(base_z < 0.2 or base_z > 1.2)
            # This smoke does not run physics collision. It flags only conservative
            # kinematic boundary violations in the chosen local smoke area.
            collision_flag = bool(abs(base_x) > 4.0 or abs(base_y) > 4.0)
            failure_reason = ""
            if collision_flag:
                failure_reason = "kinematic_boundary_violation"
            elif stuck_flag:
                failure_reason = "kinematic_pose_did_not_change"
            elif falling_flag:
                failure_reason = "base_z_out_of_expected_range"
            elif not sensor_valid:
                failure_reason = "sensor_proxy_invalid"

            row = {
                "step_id": step_id,
                "timestamp": round(time.time(), 3),
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
            last_x, last_y, last_yaw = base_x, base_y, yaw

        with steps_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        counts = [int(r["pointcloud_point_count"]) for r in rows if r["sensor_valid"]]
        successful_steps = [r for r in rows if not r["failure_reason"]]
        sensor_valid_steps = [r for r in rows if r["sensor_valid"]]
        collision_count = sum(1 for r in rows if r["collision_flag"])
        stuck_count = sum(1 for r in rows if r["stuck_flag"])
        falling_count = sum(1 for r in rows if r["falling_flag"])
        summary.update({
            "step_count": len(rows),
            "successful_steps": len(successful_steps),
            "sensor_valid_steps": len(sensor_valid_steps),
            "sensor_valid_rate": round(len(sensor_valid_steps) / len(rows), 4) if rows else 0.0,
            "min_pointcloud_count": min(counts) if counts else 0,
            "max_pointcloud_count": max(counts) if counts else 0,
            "average_pointcloud_count": round(mean(counts), 2) if counts else 0.0,
            "collision_count": collision_count,
            "stuck_count": stuck_count,
            "falling_count": falling_count,
        })
        summary["safe_to_continue_phase4"] = bool(
            summary["scene_open_result"]
            and summary["stage_available"]
            and summary["temporary_go2_proxy_used"]
            and summary["step_count"] >= 5
            and summary["successful_steps"] >= 5
            and summary["sensor_valid_rate"] >= 0.8
            and summary["min_pointcloud_count"] > 0
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
        )
        exit_code = 0 if summary["safe_to_continue_phase4"] else 2
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        exit_code = 1
    finally:
        summary["elapsed_sec"] = round(time.time() - started, 3)
        summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_markdown_report(report_md, summary)
        if simulation_app is not None:
            try:
                simulation_app.close()
            except Exception as exc:
                print(f"simulation_app.close failed: {exc!r}", file=sys.stderr)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
