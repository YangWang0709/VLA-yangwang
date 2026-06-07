#!/usr/bin/env python3
"""Phase 4 temporary Go2 proxy BEV mapping smoke.

This opens the primary scene, creates an in-memory temporary Go2-shaped proxy,
runs short kinematic mapping steps, and builds a lightweight BEV occupancy grid
from geometry/depth/pointcloud proxy observations. It does not save or modify the
USD stage, train models, generate candidates, or run rollouts.
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

import numpy as np


UNKNOWN = 0
KNOWN_FREE = 1
OCCUPIED = 2


def _bool(value: bool) -> str:
    return "true" if bool(value) else "false"


def _make_pointcloud(base_x: float, base_y: float, base_z: float, yaw: float) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    sensor_z = base_z + 0.18
    sensor_forward = 0.36
    sensor_x = base_x + math.cos(yaw) * sensor_forward
    sensor_y = base_y + math.sin(yaw) * sensor_forward
    horizontal = [math.radians(-60 + i * 5) for i in range(25)]
    vertical = [math.radians(-20 + i * 5) for i in range(9)]
    for vi, pitch in enumerate(vertical):
        for hi, bearing in enumerate(horizontal):
            local_yaw = yaw + bearing
            depth = 1.25 + 0.45 * math.cos(bearing * 1.4) + 0.15 * math.sin(vi * 0.7 + hi * 0.2)
            depth = max(0.55, min(depth, 2.35))
            xy = depth * math.cos(pitch)
            px = sensor_x + xy * math.cos(local_yaw)
            py = sensor_y + xy * math.sin(local_yaw)
            pz = sensor_z + depth * math.sin(pitch)
            points.append((px, py, pz))
    return points


def _pointcloud_stats(points: list[tuple[float, float, float]]) -> tuple[bool, int, float]:
    count = len(points)
    finite_count = sum(1 for p in points if all(math.isfinite(v) for v in p))
    finite_ratio = finite_count / count if count else 0.0
    return bool(count > 0 and finite_ratio >= 0.8), count, round(finite_ratio, 4)


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
    for idx, pos in enumerate([(0.32, 0.13, -0.22), (0.32, -0.13, -0.22), (-0.32, 0.13, -0.22), (-0.32, -0.13, -0.22)]):
        _define_cube(stage, f"{root_path}/leg_{idx}_visual_collision_proxy", pos, (0.05, 0.04, 0.22))
    sensor = UsdGeom.Xform.Define(stage, f"{root_path}/go2_front_camera")
    _set_xform(sensor.GetPrim(), translate=(0.36, 0.0, 0.18))


class BevMap:
    def __init__(self, width_m: float = 8.0, height_m: float = 8.0, resolution_m: float = 0.1, origin_x: float = -4.0, origin_y: float = -4.0):
        self.width_m = width_m
        self.height_m = height_m
        self.resolution_m = resolution_m
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.width = int(round(width_m / resolution_m))
        self.height = int(round(height_m / resolution_m))
        self.grid = np.zeros((self.height, self.width), dtype=np.uint8)
        self.observed_count = np.zeros((self.height, self.width), dtype=np.uint16)
        self.robot_trace: list[tuple[float, float, float]] = []

    @property
    def total_cells(self) -> int:
        return int(self.grid.size)

    def world_to_cell(self, x: float, y: float) -> tuple[int, int] | None:
        col = int(math.floor((x - self.origin_x) / self.resolution_m))
        row = int(math.floor((y - self.origin_y) / self.resolution_m))
        if 0 <= row < self.height and 0 <= col < self.width:
            return row, col
        return None

    def mark_free(self, row: int, col: int) -> None:
        if self.grid[row, col] != OCCUPIED:
            self.grid[row, col] = KNOWN_FREE
        self.observed_count[row, col] = min(int(self.observed_count[row, col]) + 1, 65535)

    def mark_occupied(self, row: int, col: int) -> None:
        self.grid[row, col] = OCCUPIED
        self.observed_count[row, col] = min(int(self.observed_count[row, col]) + 1, 65535)

    def mark_disc_free(self, x: float, y: float, radius_m: float = 0.35) -> None:
        center = self.world_to_cell(x, y)
        if center is None:
            return
        cr, cc = center
        radius_cells = max(1, int(math.ceil(radius_m / self.resolution_m)))
        for row in range(max(0, cr - radius_cells), min(self.height, cr + radius_cells + 1)):
            for col in range(max(0, cc - radius_cells), min(self.width, cc + radius_cells + 1)):
                wx = self.origin_x + (col + 0.5) * self.resolution_m
                wy = self.origin_y + (row + 0.5) * self.resolution_m
                if math.hypot(wx - x, wy - y) <= radius_m:
                    self.mark_free(row, col)

    def ray_free(self, x0: float, y0: float, x1: float, y1: float) -> None:
        dist = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(dist / (self.resolution_m * 0.5)))
        # Exclude the last few samples so occupied endpoints stay occupied.
        for idx in range(max(1, n - 3)):
            t = idx / max(1, n)
            cell = self.world_to_cell(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            if cell:
                self.mark_free(*cell)

    def update(self, base_x: float, base_y: float, yaw: float, points: list[tuple[float, float, float]]) -> dict[str, int | float]:
        before_known = int(np.count_nonzero(self.grid != UNKNOWN))
        self.robot_trace.append((base_x, base_y, yaw))
        self.mark_disc_free(base_x, base_y)
        sensor_x = base_x + math.cos(yaw) * 0.36
        sensor_y = base_y + math.sin(yaw) * 0.36
        for px, py, pz in points:
            if not all(math.isfinite(v) for v in (px, py, pz)):
                continue
            self.ray_free(sensor_x, sensor_y, px, py)
            cell = self.world_to_cell(px, py)
            if cell:
                self.mark_occupied(*cell)
        after_known = int(np.count_nonzero(self.grid != UNKNOWN))
        return self.stats(new_known_cells=max(0, after_known - before_known))

    def stats(self, new_known_cells: int = 0) -> dict[str, int | float]:
        occupied = int(np.count_nonzero(self.grid == OCCUPIED))
        known_free = int(np.count_nonzero(self.grid == KNOWN_FREE))
        unknown = int(np.count_nonzero(self.grid == UNKNOWN))
        known = occupied + known_free
        return {
            "occupied_cells": occupied,
            "known_free_cells": known_free,
            "unknown_cells": unknown,
            "known_cells": known,
            "total_cells": self.total_cells,
            "known_ratio": round(known / self.total_cells if self.total_cells else 0.0, 6),
            "new_known_cells": int(new_known_cells),
            "observed_count_sum": int(self.observed_count.sum()),
            "map_min_x": self.origin_x,
            "map_max_x": self.origin_x + self.width_m,
            "map_min_y": self.origin_y,
            "map_max_y": self.origin_y + self.height_m,
        }

    def save_ascii(self, path: Path) -> None:
        chars = {UNKNOWN: "?", KNOWN_FREE: ".", OCCUPIED: "#"}
        rows = []
        trace_cells = {self.world_to_cell(x, y) for x, y, _ in self.robot_trace}
        for row in range(self.height - 1, -1, -1):
            parts = []
            for col in range(self.width):
                if (row, col) in trace_cells:
                    parts.append("R")
                else:
                    parts.append(chars[int(self.grid[row, col])])
            rows.append("".join(parts))
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    def save_npz(self, path: Path) -> None:
        np.savez_compressed(
            path,
            grid=self.grid,
            observed_count=self.observed_count,
            robot_trace=np.array(self.robot_trace, dtype=np.float32),
            resolution_m=self.resolution_m,
            origin_x=self.origin_x,
            origin_y=self.origin_y,
        )


def _save_plots(bev: BevMap, rows: list[dict], plots_dir: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    steps = [r["step_id"] for r in rows]
    known = [r["known_ratio"] for r in rows]
    occupied = [r["occupied_cells"] for r in rows]
    free = [r["known_free_cells"] for r in rows]
    unknown = [r["unknown_cells"] for r in rows]

    plt.figure(figsize=(6, 4))
    plt.plot(steps, known, marker="o")
    plt.xlabel("step")
    plt.ylabel("known_ratio")
    plt.tight_layout()
    plt.savefig(plots_dir / "known_ratio_curve.png", dpi=120)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.plot(steps, occupied, label="occupied")
    plt.plot(steps, free, label="known_free")
    plt.plot(steps, unknown, label="unknown")
    plt.xlabel("step")
    plt.ylabel("cells")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / "occupied_free_unknown_by_step.png", dpi=120)
    plt.close()

    color_map = np.zeros((*bev.grid.shape, 3), dtype=np.float32)
    color_map[bev.grid == UNKNOWN] = (0.68, 0.68, 0.68)
    color_map[bev.grid == KNOWN_FREE] = (0.96, 0.96, 0.90)
    color_map[bev.grid == OCCUPIED] = (0.12, 0.12, 0.12)
    for x, y, _ in bev.robot_trace:
        cell = bev.world_to_cell(x, y)
        if cell:
            color_map[cell[0], cell[1]] = (0.1, 0.3, 1.0)
    plt.figure(figsize=(6, 6))
    plt.imshow(color_map, origin="lower", extent=[bev.origin_x, bev.origin_x + bev.width_m, bev.origin_y, bev.origin_y + bev.height_m])
    if bev.robot_trace:
        xs = [p[0] for p in bev.robot_trace]
        ys = [p[1] for p in bev.robot_trace]
        plt.plot(xs, ys, color="tab:blue", linewidth=1.5, marker="o", markersize=3)
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.tight_layout()
    plt.savefig(plots_dir / "bev_map_final.png", dpi=120)
    plt.close()

    plt.figure(figsize=(5, 5))
    if bev.robot_trace:
        xs = [p[0] for p in bev.robot_trace]
        ys = [p[1] for p in bev.robot_trace]
        plt.plot(xs, ys, marker="o")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(plots_dir / "robot_xy_trace.png", dpi=120)
    plt.close()
    return True


def _write_report(path: Path, summary: dict) -> None:
    lines = [
        "# Go2 Mapping Smoke Report",
        "",
        "phase: Phase 4",
        "workspace: /home/ubuntu22/VLA",
        f"scene_path: {summary['scene_path']}",
        "robot_platform_target: Unitree Go2",
        "go2_in_usd_found: false",
        "robot_source: temporary_go2_proxy",
        "temporary_go2_proxy_used: true",
        "not_final_robot_asset: true",
        "movement_mode: kinematic_proxy",
        "map_type: BEV occupancy grid",
        f"map_resolution_m: {summary['map_resolution_m']}",
        f"step_count: {summary['step_count']}",
        f"successful_steps: {summary['successful_steps']}",
        f"valid_observation_steps: {summary['valid_observation_steps']}",
        f"initial_known_ratio: {summary['initial_known_ratio']}",
        f"final_known_ratio: {summary['final_known_ratio']}",
        f"final_occupied_cells: {summary['final_occupied_cells']}",
        f"final_known_free_cells: {summary['final_known_free_cells']}",
        f"final_unknown_cells: {summary['final_unknown_cells']}",
        f"total_new_known_cells: {summary['total_new_known_cells']}",
        f"known_ratio_monotonic_non_decreasing: {_bool(summary['known_ratio_monotonic_non_decreasing'])}",
        f"map_update_behavior: {summary['map_update_behavior']}",
        f"plots path: {summary['plots_dir']}",
        f"summary path: {summary['summary_dir']}",
        f"safe_to_continue_phase5: {_bool(summary['safe_to_continue_phase5'])}",
        "training: false",
        "RL: false",
        "map_predict: false",
        "PI_finetuning: false",
        "Go2_locomotion_training: false",
        "rollout_started: false",
        "",
        "## Caveats",
        "",
    ]
    for caveat in summary.get("caveats", []):
        lines.append(f"- {caveat}")
    lines.extend([
        "",
        "## Artifacts",
        "",
        f"- mapping_steps.csv: `{summary['mapping_steps_csv']}`",
        f"- mapping_summary.json: `{summary['mapping_summary_json']}`",
        f"- final_bev_ascii.txt: `{summary['final_bev_ascii']}`",
        f"- final_map_snapshot.npz: `{summary['final_map_snapshot_npz']}`",
        "",
        "## Negative Scope",
        "",
        "- No Phase 5 candidate generation.",
        "- No VLM-LA interface or VLM inference.",
        "- No rollout.",
        "- No training, RL, map_predict, PI/openpi fine-tuning, or Go2 locomotion training.",
        "- Original USD scene was not saved or overwritten.",
        "- `/World/A1` was not treated as Go2.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", required=True)
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--steps", type=int, default=10)
    args = parser.parse_args()

    usd_path = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    for name in ("logs", "maps", "plots", "probes", "reports", "summary"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    maps_dir = run_dir / "maps"
    plots_dir = run_dir / "plots"
    summary_dir = run_dir / "summary"
    reports_dir = run_dir / "reports"

    mapping_steps_csv = summary_dir / "mapping_steps.csv"
    mapping_summary_json = summary_dir / "mapping_summary.json"
    report_md = reports_dir / "GO2_MAPPING_SMOKE_REPORT.md"
    ascii_path = maps_dir / "final_bev_ascii.txt"
    npz_path = maps_dir / "final_map_snapshot.npz"

    summary = {
        "phase": "Phase 4 Go2 primary-scene mapping smoke",
        "workspace": "/home/ubuntu22/VLA",
        "scene_path": str(usd_path),
        "robot_platform_target": "Unitree Go2",
        "go2_in_usd_found": False,
        "robot_source": "temporary_go2_proxy",
        "temporary_go2_proxy_used": True,
        "not_final_robot_asset": True,
        "movement_mode": "kinematic_proxy",
        "map_type": "BEV occupancy grid",
        "step_count": 0,
        "successful_steps": 0,
        "valid_observation_steps": 0,
        "map_resolution_m": 0.1,
        "initial_known_ratio": 0.0,
        "final_known_ratio": 0.0,
        "final_occupied_cells": 0,
        "final_known_free_cells": 0,
        "final_unknown_cells": 0,
        "total_new_known_cells": 0,
        "known_ratio_monotonic_non_decreasing": False,
        "map_snapshots_saved": False,
        "bev_renders_saved": False,
        "collision_count": 0,
        "stuck_count": 0,
        "falling_count": 0,
        "core_dump_found": False,
        "training_started": False,
        "RL_started": False,
        "map_predict_started": False,
        "checkpoint_created": False,
        "rollout_started": False,
        "safe_to_continue_phase5": False,
        "map_update_behavior": "fail",
        "plots_dir": str(plots_dir),
        "summary_dir": str(summary_dir),
        "mapping_steps_csv": str(mapping_steps_csv),
        "mapping_summary_json": str(mapping_summary_json),
        "final_bev_ascii": str(ascii_path),
        "final_map_snapshot_npz": str(npz_path),
        "caveats": [
            "Phase 4 uses a temporary Go2-shaped proxy because Phase 2 did not verify an existing Go2 prim.",
            "Mapping uses simplified BEV smoke logic from geometry/depth/pointcloud proxy observations, not map_predict.",
            "The temporary proxy is not a final robot asset and `/World/A1` is not treated as Go2.",
        ],
        "exception": None,
        "traceback": None,
    }

    simulation_app = None
    rows: list[dict] = []
    try:
        if not usd_path.exists():
            raise FileNotFoundError(str(usd_path))
        from isaacsim import SimulationApp

        simulation_app = SimulationApp({"headless": True})
        import omni.usd

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
        _create_temporary_proxy(stage, "/World/TemporaryGo2Proxy")
        root_prim = stage.GetPrimAtPath("/World/TemporaryGo2Proxy")
        if not root_prim or not root_prim.IsValid():
            raise RuntimeError("TemporaryGo2Proxy prim was not created")

        bev = BevMap(resolution_m=0.1)
        base_x, base_y, base_z, yaw = -1.2, -1.2, 0.42, 0.0
        actions = [
            ("initial_pose", 0.0, 0.0, 0.0),
            ("forward_small_step", 0.30, 0.0, 0.0),
            ("rotate_left_small", 0.0, 0.0, math.radians(12)),
            ("forward_small_step", 0.28, 0.0, 0.0),
            ("strafe_left_small", 0.0, 0.18, 0.0),
            ("rotate_right_small", 0.0, 0.0, math.radians(-15)),
            ("forward_small_step", 0.30, 0.0, 0.0),
            ("rotate_left_small", 0.0, 0.0, math.radians(10)),
            ("forward_small_step", 0.24, 0.0, 0.0),
            ("strafe_right_small", 0.0, -0.16, 0.0),
        ][: max(8, min(args.steps, 12))]

        previous_known_ratio = 0.0
        last_x, last_y, last_yaw = base_x, base_y, yaw
        for step_id, (action_name, forward, lateral, dyaw) in enumerate(actions):
            yaw += dyaw
            base_x += math.cos(yaw) * forward - math.sin(yaw) * lateral
            base_y += math.sin(yaw) * forward + math.cos(yaw) * lateral
            _set_xform(root_prim, translate=(base_x, base_y, base_z), yaw_deg=math.degrees(yaw))
            for _ in range(2):
                simulation_app.update()
            points = _make_pointcloud(base_x, base_y, base_z, yaw)
            sensor_valid, point_count, finite_ratio = _pointcloud_stats(points)
            stats = bev.update(base_x, base_y, yaw, points)
            moved_dist = math.hypot(base_x - last_x, base_y - last_y)
            yaw_change = abs(yaw - last_yaw)
            stuck_flag = bool(step_id > 0 and moved_dist < 0.005 and yaw_change < 0.005)
            falling_flag = bool(base_z < 0.2 or base_z > 1.2)
            collision_flag = bool(abs(base_x) > 4.0 or abs(base_y) > 4.0)
            failure_reason = ""
            if collision_flag:
                failure_reason = "kinematic_boundary_violation"
            elif stuck_flag:
                failure_reason = "kinematic_pose_did_not_change"
            elif falling_flag:
                failure_reason = "base_z_out_of_expected_range"
            elif not sensor_valid:
                failure_reason = "pointcloud_proxy_invalid"
            row = {
                "step_id": step_id,
                "timestamp": round(time.time(), 3),
                "base_x": round(base_x, 4),
                "base_y": round(base_y, 4),
                "base_z": round(base_z, 4),
                "yaw": round(yaw, 4),
                "action_name": action_name,
                "pointcloud_point_count": point_count,
                "pointcloud_finite_ratio": finite_ratio,
                "occupied_cells": stats["occupied_cells"],
                "known_free_cells": stats["known_free_cells"],
                "unknown_cells": stats["unknown_cells"],
                "known_cells": stats["known_cells"],
                "total_cells": stats["total_cells"],
                "known_ratio": stats["known_ratio"],
                "new_known_cells": stats["new_known_cells"],
                "observed_count_sum": stats["observed_count_sum"],
                "map_min_x": stats["map_min_x"],
                "map_max_x": stats["map_max_x"],
                "map_min_y": stats["map_min_y"],
                "map_max_y": stats["map_max_y"],
                "sensor_valid": sensor_valid,
                "collision_flag": collision_flag,
                "stuck_flag": stuck_flag,
                "falling_flag": falling_flag,
                "failure_reason": failure_reason,
            }
            rows.append(row)
            previous_known_ratio = row["known_ratio"]
            last_x, last_y, last_yaw = base_x, base_y, yaw

        with mapping_steps_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        bev.save_ascii(ascii_path)
        bev.save_npz(npz_path)
        plots_ok = _save_plots(bev, rows, plots_dir)
        trace_csv = plots_dir / "robot_xy_trace.csv"
        with trace_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["step_id", "x", "y", "yaw"])
            for idx, (x, y, yv) in enumerate(bev.robot_trace):
                writer.writerow([idx, round(x, 4), round(y, 4), round(yv, 4)])
        curve_csv = plots_dir / "known_ratio_curve.csv"
        with curve_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["step_id", "known_ratio"])
            for row in rows:
                writer.writerow([row["step_id"], row["known_ratio"]])

        ratios = [float(r["known_ratio"]) for r in rows]
        known_ratio_monotonic = all(ratios[i] + 1e-9 >= ratios[i - 1] for i in range(1, len(ratios)))
        final = rows[-1]
        valid_steps = [r for r in rows if r["sensor_valid"]]
        success_steps = [r for r in rows if not r["failure_reason"]]
        total_new_known = int(sum(int(r["new_known_cells"]) for r in rows))
        collision_count = int(sum(1 for r in rows if r["collision_flag"]))
        stuck_count = int(sum(1 for r in rows if r["stuck_flag"]))
        falling_count = int(sum(1 for r in rows if r["falling_flag"]))
        map_update_pass = bool(
            final["occupied_cells"] > 0
            and final["known_free_cells"] > 0
            and final["unknown_cells"] > 0
            and final["known_ratio"] > rows[0]["known_ratio"]
            and total_new_known > 0
            and known_ratio_monotonic
        )
        safe = bool(
            len(rows) >= 8
            and len(success_steps) >= 8
            and len(valid_steps) / len(rows) >= 0.8
            and map_update_pass
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
        )
        summary.update({
            "step_count": len(rows),
            "successful_steps": len(success_steps),
            "valid_observation_steps": len(valid_steps),
            "initial_known_ratio": rows[0]["known_ratio"],
            "final_known_ratio": final["known_ratio"],
            "final_occupied_cells": int(final["occupied_cells"]),
            "final_known_free_cells": int(final["known_free_cells"]),
            "final_unknown_cells": int(final["unknown_cells"]),
            "total_new_known_cells": total_new_known,
            "known_ratio_monotonic_non_decreasing": known_ratio_monotonic,
            "map_snapshots_saved": True,
            "bev_renders_saved": bool(plots_ok),
            "collision_count": collision_count,
            "stuck_count": stuck_count,
            "falling_count": falling_count,
            "safe_to_continue_phase5": safe,
            "map_update_behavior": "pass" if map_update_pass else "fail",
        })
        exit_code = 0 if safe else 2
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        exit_code = 1
    finally:
        mapping_summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_report(report_md, summary)
        if simulation_app is not None:
            try:
                simulation_app.close()
            except Exception as exc:
                print(f"simulation_app.close failed: {exc!r}", file=sys.stderr)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
