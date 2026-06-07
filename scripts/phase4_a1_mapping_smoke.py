#!/usr/bin/env python3
"""Phase 4 Unitree A1 primary-scene BEV mapping smoke."""

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
TOP_REPORT = WORKSPACE / "runs/A1_MAPPING_SMOKE_REPORT.md"
A1_ROOT = "/World/A1"
BASE_FRAME = "/World/A1/base"
UNKNOWN = 0
KNOWN_FREE = 1
OCCUPIED = 2


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def make_pointcloud(x: float, y: float, z: float, yaw: float) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    sx = x + math.cos(yaw) * 0.36
    sy = y + math.sin(yaw) * 0.36
    sz = z + 0.18
    horizontal = [math.radians(-60 + i * 5) for i in range(25)]
    vertical = [math.radians(-20 + i * 5) for i in range(9)]
    for vi, pitch in enumerate(vertical):
        for hi, bearing in enumerate(horizontal):
            depth = 1.25 + 0.45 * math.cos(bearing * 1.4) + 0.15 * math.sin(vi * 0.7 + hi * 0.2)
            depth = max(0.55, min(depth, 2.35))
            local_yaw = yaw + bearing
            xy = depth * math.cos(pitch)
            points.append((sx + xy * math.cos(local_yaw), sy + xy * math.sin(local_yaw), sz + depth * math.sin(pitch)))
    return points


def pointcloud_stats(points: list[tuple[float, float, float]]) -> tuple[bool, int, float]:
    count = len(points)
    finite_count = sum(1 for p in points if all(math.isfinite(v) for v in p))
    finite_ratio = finite_count / count if count else 0.0
    return count > 0 and finite_ratio >= 0.8, count, round(finite_ratio, 4)


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


class BevMap:
    def __init__(self, cx: float, cy: float, width_m: float = 8.0, height_m: float = 8.0, resolution_m: float = 0.1):
        self.width_m = width_m
        self.height_m = height_m
        self.resolution_m = resolution_m
        self.origin_x = cx - width_m / 2.0
        self.origin_y = cy - height_m / 2.0
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
        rad = max(1, int(math.ceil(radius_m / self.resolution_m)))
        for row in range(max(0, cr - rad), min(self.height, cr + rad + 1)):
            for col in range(max(0, cc - rad), min(self.width, cc + rad + 1)):
                wx = self.origin_x + (col + 0.5) * self.resolution_m
                wy = self.origin_y + (row + 0.5) * self.resolution_m
                if math.hypot(wx - x, wy - y) <= radius_m:
                    self.mark_free(row, col)

    def ray_free(self, x0: float, y0: float, x1: float, y1: float) -> None:
        dist = math.hypot(x1 - x0, y1 - y0)
        steps = max(1, int(dist / (self.resolution_m * 0.5)))
        for idx in range(max(1, steps - 3)):
            t = idx / max(1, steps)
            cell = self.world_to_cell(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            if cell:
                self.mark_free(*cell)

    def update(self, x: float, y: float, yaw: float, points: list[tuple[float, float, float]]) -> dict[str, int | float]:
        before = int(np.count_nonzero(self.grid != UNKNOWN))
        self.robot_trace.append((x, y, yaw))
        self.mark_disc_free(x, y)
        sx = x + math.cos(yaw) * 0.36
        sy = y + math.sin(yaw) * 0.36
        for px, py, pz in points:
            if not all(math.isfinite(v) for v in (px, py, pz)):
                continue
            self.ray_free(sx, sy, px, py)
            cell = self.world_to_cell(px, py)
            if cell:
                self.mark_occupied(*cell)
        after = int(np.count_nonzero(self.grid != UNKNOWN))
        return self.stats(new_known_cells=max(0, after - before))

    def stats(self, new_known_cells: int = 0) -> dict[str, int | float]:
        occupied = int(np.count_nonzero(self.grid == OCCUPIED))
        free = int(np.count_nonzero(self.grid == KNOWN_FREE))
        unknown = int(np.count_nonzero(self.grid == UNKNOWN))
        known = occupied + free
        return {
            "occupied_cells": occupied,
            "known_free_cells": free,
            "unknown_cells": unknown,
            "known_cells": known,
            "total_cells": self.total_cells,
            "known_ratio": round(known / self.total_cells if self.total_cells else 0.0, 6),
            "new_known_cells": int(new_known_cells),
            "observed_count_sum": int(self.observed_count.sum()),
            "map_min_x": round(self.origin_x, 4),
            "map_max_x": round(self.origin_x + self.width_m, 4),
            "map_min_y": round(self.origin_y, 4),
            "map_max_y": round(self.origin_y + self.height_m, 4),
        }

    def save_ascii(self, path: Path) -> None:
        chars = {UNKNOWN: "?", KNOWN_FREE: ".", OCCUPIED: "#"}
        trace = {self.world_to_cell(x, y) for x, y, _ in self.robot_trace}
        lines = []
        for row in range(self.height - 1, -1, -1):
            parts = []
            for col in range(self.width):
                parts.append("R" if (row, col) in trace else chars[int(self.grid[row, col])])
            lines.append("".join(parts))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_plots(bev: BevMap, rows: list[dict[str, Any]], plots_dir: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    steps = [int(r["step_id"]) for r in rows]
    plots_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 4))
    plt.plot(steps, [float(r["known_ratio"]) for r in rows], marker="o")
    plt.xlabel("step")
    plt.ylabel("known ratio")
    plt.title("A1 BEV known ratio")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / "known_ratio_curve.png", dpi=120)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.plot(steps, [int(r["occupied_cells"]) for r in rows], label="occupied")
    plt.plot(steps, [int(r["known_free_cells"]) for r in rows], label="known_free")
    plt.plot(steps, [int(r["unknown_cells"]) for r in rows], label="unknown")
    plt.xlabel("step")
    plt.ylabel("cells")
    plt.title("BEV occupancy cells")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / "occupied_free_unknown_by_step.png", dpi=120)
    plt.close()

    cmap = matplotlib.colors.ListedColormap(["#222222", "#d7f0d0", "#c23b22"])
    plt.figure(figsize=(6, 6))
    plt.imshow(bev.grid, origin="lower", cmap=cmap, interpolation="nearest")
    cells = [bev.world_to_cell(x, y) for x, y, _ in bev.robot_trace]
    cells = [c for c in cells if c]
    if cells:
        plt.plot([c[1] for c in cells], [c[0] for c in cells], color="#2b6cff", marker="o", linewidth=1.5, markersize=3)
    plt.title("Final A1 BEV map")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(plots_dir / "bev_map_final.png", dpi=120)
    plt.close()

    plt.figure(figsize=(5, 5))
    plt.plot([x for x, _, _ in bev.robot_trace], [y for _, y, _ in bev.robot_trace], marker="o")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("A1 XY trace")
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / "robot_xy_trace.png", dpi=120)
    plt.close()
    return True


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# A1 Mapping Smoke Report",
        "",
        "phase: Phase 4",
        "workspace: /home/ubuntu22/VLA",
        "project_name: A1-VLM-LA Explorer",
        f"scene_path: {summary['scene_path']}",
        "robot_platform: unitree_a1",
        "robot_source: existing_usd_prim",
        "a1_root_prim: /World/A1",
        "base_frame: /World/A1/base",
        "previous_proxy_results_status: superseded_for_formal_a1_pipeline",
        f"movement_mode: {summary['movement_mode']}",
        f"real_a1_locomotion_controller: {bool_text(summary['real_a1_locomotion_controller'])}",
        f"existing_sensor_reused: {bool_text(summary['existing_sensor_reused'])}",
        f"geometry_proxy_sensor_used: {bool_text(summary['geometry_proxy_sensor_used'])}",
        f"sensor_method: {summary['sensor_method']}",
        "map_type: BEV occupancy grid",
        f"mapping_method: {summary['mapping_method']}",
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
        f"known_ratio_monotonic_non_decreasing: {bool_text(summary['known_ratio_monotonic_non_decreasing'])}",
        f"map_update_behavior: {summary['map_update_behavior']}",
        f"plots_path: {summary['plots_dir']}",
        f"summary_path: {summary['summary_json']}",
        f"safe_to_continue_phase5: {bool_text(summary['safe_to_continue_phase5'])}",
        "training: false",
        "RL: false",
        "map_predict: false",
        "PI_finetuning: false",
        "A1_locomotion_training: false",
        "rollout_started: false",
        "",
        "## Artifacts",
        "",
        f"- run_dir: `{summary['run_dir']}`",
        f"- steps_csv: `{summary['steps_csv']}`",
        f"- final_bev_ascii: `{summary['final_bev_ascii']}`",
        f"- reports_dir: `{summary['reports_dir']}`",
        "",
        "## Caveats",
        "",
    ]
    lines.extend(f"- {c}" for c in summary.get("caveats", []))
    lines.extend([
        "",
        "## Negative Scope",
        "",
        "- No VLM training or inference.",
        "- No RL training.",
        "- No map_predict training or mainline implementation.",
        "- No PI/openpi action-head fine-tuning.",
        "- No A1 locomotion policy training.",
        "- No Phase 5 candidate generation and no long rollout.",
        "- No temporary Go2 proxy was created or used as formal data.",
        "- Original USD scene was opened and edited only in memory; it was not saved or overwritten.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", default=str(SCENE))
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--top_report", default=str(TOP_REPORT))
    parser.add_argument("--steps", type=int, default=10)
    args = parser.parse_args()

    usd = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    logs_dir = run_dir / "logs"
    maps_dir = run_dir / "maps"
    plots_dir = run_dir / "plots"
    probes_dir = run_dir / "probes"
    reports_dir = run_dir / "reports"
    summary_dir = run_dir / "summary"
    for directory in (logs_dir, maps_dir, plots_dir, probes_dir, reports_dir, summary_dir):
        directory.mkdir(parents=True, exist_ok=True)

    steps_csv = summary_dir / "mapping_steps.csv"
    summary_json = summary_dir / "mapping_summary.json"
    report = reports_dir / "A1_MAPPING_SMOKE_REPORT.md"
    top_report = Path(args.top_report).expanduser().resolve()
    final_bev_ascii = maps_dir / "final_bev_ascii.txt"
    final_grid_csv = maps_dir / "final_bev_grid.csv"
    trace_csv = maps_dir / "robot_xy_trace.csv"
    known_ratio_csv = maps_dir / "known_ratio_curve.csv"
    probe_json = probes_dir / "a1_mapping_stage_probe.json"

    started = time.time()
    app = None
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "phase": "Phase 4 A1 primary-scene mapping smoke",
        "workspace": str(WORKSPACE),
        "project_name": "A1-VLM-LA Explorer",
        "main_goal": "A1-VLM-LA Explorer for 3D Active Exploration",
        "output_contract": "Go to candidate <id>.",
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
        "previous_proxy_results_status": "superseded_for_formal_a1_pipeline",
        "movement_mode": "kinematic_existing_a1_root",
        "real_a1_locomotion_controller": False,
        "sensor_method": "geometry_proxy_pointcloud_from_a1_base_pose",
        "sensor_frame": "derived_from_a1_base",
        "existing_sensor_reused": False,
        "geometry_proxy_sensor_used": True,
        "map_type": "BEV occupancy grid",
        "mapping_method": "raycast_bev_proxy_mapping",
        "map_resolution_m": 0.1,
        "map_width_m": 8.0,
        "map_height_m": 8.0,
        "step_count": 0,
        "successful_steps": 0,
        "valid_observation_steps": 0,
        "initial_known_ratio": 0.0,
        "final_known_ratio": 0.0,
        "final_occupied_cells": 0,
        "final_known_free_cells": 0,
        "final_unknown_cells": 0,
        "total_new_known_cells": 0,
        "known_ratio_monotonic_non_decreasing": False,
        "map_update_behavior": "fail",
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
        "temporary_go2_proxy_created": False,
        "run_dir": str(run_dir),
        "maps_dir": str(maps_dir),
        "plots_dir": str(plots_dir),
        "reports_dir": str(reports_dir),
        "summary_json": str(summary_json),
        "steps_csv": str(steps_csv),
        "final_bev_ascii": str(final_bev_ascii),
        "final_bev_grid_csv": str(final_grid_csv),
        "robot_xy_trace_csv": str(trace_csv),
        "known_ratio_curve_csv": str(known_ratio_csv),
        "probe_json": str(probe_json),
        "caveats": [
            "This is formal A1 mapping smoke based on existing USD prim /World/A1, not the old temporary Go2 proxy.",
            "Sensor data is geometry proxy pointcloud/depth from A1 base pose; this is not real RGB-D SLAM.",
            "Movement is short in-memory kinematic A1 root motion for mapping smoke, not real A1 locomotion control or a rollout.",
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
        cameras = [str(p.GetPath()) for p in stage.Traverse() if p.GetTypeName() == "Camera"]
        summary["available_camera_count"] = len(cameras)
        summary["available_camera_prims"] = cameras[:20]
        summary["a1_bound_sensor_prims"] = [p for p in cameras if p.startswith(A1_ROOT + "/")][:20]
        if not summary["a1_bound_sensor_prims"]:
            summary["caveats"].append("No A1-bound USD camera/sensor prim was found; mapping used geometry proxy observations only.")

        cache = UsdGeom.XformCache()
        initial_root = world_translation(cache, root)
        initial_base = world_translation(cache, base)
        summary["initial_root_pose_xyz"] = [round(v, 6) for v in initial_root]
        summary["initial_base_pose_xyz"] = [round(v, 6) for v in initial_base]
        summary["base_pose_readable"] = True
        ops = {op.GetName(): op for op in UsdGeom.Xformable(root).GetOrderedXformOps()}
        initial_orient = ops["xformOp:orient"].Get() if "xformOp:orient" in ops else None
        bev = BevMap(initial_base[0], initial_base[1], resolution_m=float(summary["map_resolution_m"]))
        actions = [
            ("initial_pose", 0.0, 0.0, 0.0),
            ("small_forward", 0.18, 0.0, 0.0),
            ("small_forward", 0.16, 0.0, 0.0),
            ("small_yaw_left", 0.0, 0.0, math.radians(10)),
            ("small_forward", 0.16, 0.0, 0.0),
            ("small_lateral_left", 0.0, 0.12, 0.0),
            ("small_yaw_right", 0.0, 0.0, math.radians(-8)),
            ("small_forward", 0.16, 0.0, 0.0),
            ("small_lateral_right", 0.0, -0.10, 0.0),
            ("stop", 0.0, 0.0, 0.0),
        ][: max(8, min(args.steps, 12))]
        root_x, root_y, root_z = initial_root
        last_x, last_y = initial_base[0], initial_base[1]
        yaw = 0.0
        last_yaw = yaw
        for step_id, (action, forward, lateral, dyaw) in enumerate(actions):
            yaw += dyaw
            root_x += math.cos(yaw) * forward - math.sin(yaw) * lateral
            root_y += math.sin(yaw) * forward + math.cos(yaw) * lateral
            set_root_pose(root, (root_x, root_y, root_z), yaw, initial_orient)
            for _ in range(2):
                app.update()
            cache = UsdGeom.XformCache()
            x, y, z = world_translation(cache, base)
            points = make_pointcloud(x, y, z, yaw)
            sensor_valid, point_count, finite_ratio = pointcloud_stats(points)
            m = bev.update(x, y, yaw, points)
            moved = math.hypot(x - last_x, y - last_y)
            yaw_change = abs(yaw - last_yaw)
            collision = abs(x - initial_base[0]) > 1.6 or abs(y - initial_base[1]) > 1.6
            stuck = step_id > 0 and moved < 0.005 and yaw_change < 0.005 and action != "stop"
            falling = z < 0.2 or z > 1.5 or abs(z - initial_base[2]) > 0.6
            reason = ""
            if collision:
                reason = "kinematic_boundary_violation"
            elif stuck:
                reason = "a1_base_pose_did_not_change"
            elif falling:
                reason = "a1_base_z_out_of_expected_range"
            elif not sensor_valid:
                reason = "geometry_proxy_sensor_invalid"
            elif int(m["known_cells"]) <= 0:
                reason = "bev_map_not_updated"
            row = {
                "step_id": step_id,
                "timestamp": round(time.time(), 3),
                "a1_root_prim": A1_ROOT,
                "base_frame": BASE_FRAME,
                "base_x": round(x, 4),
                "base_y": round(y, 4),
                "base_z": round(z, 4),
                "yaw": round(yaw, 4),
                "action_name": action,
                "sensor_method": summary["sensor_method"],
                "pointcloud_point_count": point_count,
                "pointcloud_finite_ratio": finite_ratio,
                "occupied_cells": m["occupied_cells"],
                "known_free_cells": m["known_free_cells"],
                "unknown_cells": m["unknown_cells"],
                "known_cells": m["known_cells"],
                "total_cells": m["total_cells"],
                "known_ratio": m["known_ratio"],
                "new_known_cells": m["new_known_cells"],
                "observed_count_sum": m["observed_count_sum"],
                "map_min_x": m["map_min_x"],
                "map_max_x": m["map_max_x"],
                "map_min_y": m["map_min_y"],
                "map_max_y": m["map_max_y"],
                "sensor_valid": sensor_valid,
                "collision_flag": collision,
                "stuck_flag": stuck,
                "falling_flag": falling,
                "failure_reason": reason,
            }
            rows.append(row)
            last_x, last_y, last_yaw = x, y, yaw

        with steps_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        bev.save_ascii(final_bev_ascii)
        np.savetxt(final_grid_csv, bev.grid, fmt="%d", delimiter=",")
        with trace_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["trace_id", "x", "y", "yaw"])
            for idx, (x, y, trace_yaw) in enumerate(bev.robot_trace):
                w.writerow([idx, round(x, 4), round(y, 4), round(trace_yaw, 4)])
        with known_ratio_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["step_id", "known_ratio"])
            for r in rows:
                w.writerow([r["step_id"], r["known_ratio"]])
        plots_saved = save_plots(bev, rows, plots_dir)

        known_ratios = [float(r["known_ratio"]) for r in rows]
        monotonic = all((b + 1e-9) >= a for a, b in zip(known_ratios, known_ratios[1:]))
        final = bev.stats()
        valid = [r for r in rows if r["sensor_valid"]]
        successful = [r for r in rows if not r["failure_reason"]]
        collision_count = sum(1 for r in rows if r["collision_flag"])
        stuck_count = sum(1 for r in rows if r["stuck_flag"])
        falling_count = sum(1 for r in rows if r["falling_flag"])
        core_files = find_core_dumps(WORKSPACE)
        initial_known_ratio = known_ratios[0] if known_ratios else 0.0
        final_known_ratio = known_ratios[-1] if known_ratios else 0.0
        map_pass = (
            final["occupied_cells"] > 0
            and final["known_free_cells"] > 0
            and final["unknown_cells"] > 0
            and final_known_ratio > initial_known_ratio
            and any(int(r["new_known_cells"]) > 0 for r in rows[:4])
            and monotonic
        )
        summary.update({
            "map_snapshots_saved": True,
            "bev_renders_saved": plots_saved,
            "plots_saved": plots_saved,
            "step_count": len(rows),
            "successful_steps": len(successful),
            "valid_observation_steps": len(valid),
            "initial_known_ratio": initial_known_ratio,
            "final_known_ratio": final_known_ratio,
            "final_occupied_cells": int(final["occupied_cells"]),
            "final_known_free_cells": int(final["known_free_cells"]),
            "final_unknown_cells": int(final["unknown_cells"]),
            "total_new_known_cells": int(sum(int(r["new_known_cells"]) for r in rows)),
            "known_ratio_monotonic_non_decreasing": monotonic,
            "map_update_behavior": "pass" if map_pass else "fail",
            "collision_count": collision_count,
            "stuck_count": stuck_count,
            "falling_count": falling_count,
            "core_dump_found": bool(core_files),
            "core_dump_files": core_files,
        })
        summary["safe_to_continue_phase5"] = bool(
            summary["scene_open_result"]
            and summary["stage_available"]
            and summary["a1_root_exists"]
            and summary["base_pose_readable"]
            and len(rows) >= 8
            and len(successful) >= 8
            and len(valid) / len(rows) >= 0.8
            and map_pass
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
            and not summary["core_dump_found"]
        )
        probe_json.write_text(json.dumps({
            "scene_path": str(usd),
            "a1_root_prim": A1_ROOT,
            "a1_root_exists": summary["a1_root_exists"],
            "base_frame": BASE_FRAME,
            "initial_root_pose_xyz": summary.get("initial_root_pose_xyz"),
            "initial_base_pose_xyz": summary.get("initial_base_pose_xyz"),
            "available_camera_prims": summary.get("available_camera_prims"),
            "a1_bound_sensor_prims": summary.get("a1_bound_sensor_prims"),
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        exit_code = 0 if summary["safe_to_continue_phase5"] else 2
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
