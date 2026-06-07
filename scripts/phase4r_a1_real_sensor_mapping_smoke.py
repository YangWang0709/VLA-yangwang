#!/usr/bin/env python3
"""Phase 4R A1 real-sensor BEV mapping smoke.

This reuses the Phase 5.6 real Isaac/Omniverse RGB-D sensor route, converts
depth-backprojected camera points into world-frame points, and updates a
lightweight BEV occupancy map. It does not use geometry proxy observations,
does not generate candidates, does not run Phase 6, and does not save the USD.
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
SCRIPT_DIR = WORKSPACE / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase56_a1_real_sensor_suite_smoke import (  # noqa: E402
    A1_ROOT,
    BASE_FRAME,
    CAMERA_PATH,
    LIDAR_PATH,
    MOUNT_RPY,
    MOUNT_XYZ,
    SCENE,
    attach_camera_annotators,
    bool_text,
    create_runtime_prims,
    depth_stats,
    expected_sensor_pose,
    find_core_dumps,
    intrinsics_from_camera_params,
    lidar_stats,
    pointcloud_from_depth,
    pointcloud_stats,
    rgb_stats,
    save_depth_vis,
    save_rgb_png,
    segmentation_available,
    set_root_pose,
    set_world_look_at,
    set_world_translate,
    try_create_lidar,
    world_translation,
)


TOP_REPORT = WORKSPACE / "runs/A1_REAL_SENSOR_MAPPING_SMOKE_REPORT.md"
UNKNOWN = 0
KNOWN_FREE = 1
OCCUPIED = 2


def norm3(v: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(x * x for x in v))
    if length < 1e-9:
        return (1.0, 0.0, 0.0)
    return tuple(x / length for x in v)


def cross3(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def camera_basis(eye: tuple[float, float, float], target: tuple[float, float, float]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    forward = norm3((target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]))
    up_hint = (0.0, 0.0, 1.0)
    right = cross3(forward, up_hint)
    if math.sqrt(sum(x * x for x in right)) < 1e-6:
        up_hint = (0.0, 1.0, 0.0)
        right = cross3(forward, up_hint)
    right = norm3(right)
    true_up = cross3(right, forward)
    return np.asarray(right, dtype=np.float32), np.asarray(true_up, dtype=np.float32), np.asarray(forward, dtype=np.float32)


def camera_points_to_world(points: np.ndarray, eye: tuple[float, float, float], target: tuple[float, float, float]) -> np.ndarray:
    if points is None or points.size == 0:
        return np.empty((0, 3), dtype=np.float32)
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 3)
    right, up, forward = camera_basis(eye, target)
    eye_arr = np.asarray(eye, dtype=np.float32)
    world = eye_arr + pts[:, [0]] * right + pts[:, [1]] * up + pts[:, [2]] * forward
    return world.astype(np.float32)


class RealSensorBevMap:
    def __init__(self, cx: float, cy: float, width_m: float = 9.0, height_m: float = 9.0, resolution_m: float = 0.1):
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
        self.sensor_trace: list[tuple[float, float, float]] = []

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

    def update(
        self,
        base_x: float,
        base_y: float,
        yaw: float,
        sensor_x: float,
        sensor_y: float,
        sensor_z: float,
        world_points: np.ndarray,
    ) -> dict[str, int | float]:
        before = int(np.count_nonzero(self.grid != UNKNOWN))
        self.robot_trace.append((base_x, base_y, yaw))
        self.sensor_trace.append((sensor_x, sensor_y, sensor_z))
        self.mark_disc_free(base_x, base_y)
        self.mark_disc_free(sensor_x, sensor_y, radius_m=0.2)
        pts = np.asarray(world_points, dtype=np.float32).reshape(-1, 3)
        if pts.shape[0] > 5000:
            pts = pts[:: max(1, int(math.ceil(pts.shape[0] / 5000)))]
        for px, py, pz in pts:
            if not all(math.isfinite(float(v)) for v in (px, py, pz)):
                continue
            if pz < 0.05 or pz > 3.0:
                continue
            self.ray_free(sensor_x, sensor_y, float(px), float(py))
            cell = self.world_to_cell(float(px), float(py))
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
        robot_cells = {self.world_to_cell(x, y) for x, y, _ in self.robot_trace}
        sensor_cells = {self.world_to_cell(x, y) for x, y, _ in self.sensor_trace}
        lines = []
        for row in range(self.height - 1, -1, -1):
            parts = []
            for col in range(self.width):
                if (row, col) in robot_cells:
                    parts.append("R")
                elif (row, col) in sensor_cells:
                    parts.append("S")
                else:
                    parts.append(chars[int(self.grid[row, col])])
            lines.append("".join(parts))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_semantic_png(data: Any, path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from phase56_a1_real_sensor_suite_smoke import array_from_annotator_data

        arr = array_from_annotator_data(data)
        if arr is None or arr.size == 0:
            return False
        plt.imsave(path, np.asarray(arr), cmap="tab20")
        return True
    except Exception:
        return False


def save_plots(bev: RealSensorBevMap, rows: list[dict[str, Any]], plots_dir: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    plots_dir.mkdir(parents=True, exist_ok=True)
    steps = [int(r["step_id"]) for r in rows]

    plt.figure(figsize=(6, 4))
    plt.plot(steps, [float(r["known_ratio"]) for r in rows], marker="o")
    plt.xlabel("step")
    plt.ylabel("known ratio")
    plt.title("A1 real-sensor BEV known ratio")
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
    robot_cells = [bev.world_to_cell(x, y) for x, y, _ in bev.robot_trace]
    sensor_cells = [bev.world_to_cell(x, y) for x, y, _ in bev.sensor_trace]
    robot_cells = [c for c in robot_cells if c]
    sensor_cells = [c for c in sensor_cells if c]
    if robot_cells:
        plt.plot([c[1] for c in robot_cells], [c[0] for c in robot_cells], color="#2b6cff", marker="o", linewidth=1.4, markersize=3, label="robot")
    if sensor_cells:
        plt.plot([c[1] for c in sensor_cells], [c[0] for c in sensor_cells], color="#ffbf00", marker="x", linewidth=1.0, markersize=3, label="sensor")
    if robot_cells or sensor_cells:
        plt.legend(loc="lower right", fontsize=8)
    plt.title("Final real-sensor BEV map")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(plots_dir / "bev_map_final.png", dpi=120)
    plt.close()

    plt.figure(figsize=(5, 5))
    if bev.robot_trace:
        plt.plot([x for x, _, _ in bev.robot_trace], [y for _, y, _ in bev.robot_trace], marker="o", label="robot")
    if bev.sensor_trace:
        plt.plot([x for x, _, _ in bev.sensor_trace], [y for _, y, _ in bev.sensor_trace], marker="x", label="sensor")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("A1 robot and sensor XY trace")
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / "robot_and_sensor_xy_trace.png", dpi=120)
    plt.close()
    return True


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# A1 Real Sensor Mapping Smoke Report",
        "",
        "phase: Phase 4R-real",
        "workspace: /home/ubuntu22/VLA",
        "project_name: A1-VLM-LA Explorer",
        f"scene_path: {summary.get('scene_path')}",
        "robot_platform: unitree_a1",
        "robot_source: existing_usd_prim",
        "a1_root_prim: /World/A1",
        "base_frame: /World/A1/base",
        "previous_sensor_method: mounted_geometry_proxy_pointcloud_from_a1_front_sensor",
        "sensor_method: real_isaac_omniverse_rgbd",
        f"real_rgb_sensor_available: {bool_text(summary.get('real_rgb_sensor_available'))}",
        f"real_depth_sensor_available: {bool_text(summary.get('real_depth_sensor_available'))}",
        f"camera_params_available: {bool_text(summary.get('camera_params_available'))}",
        f"camera_intrinsics_available: {bool_text(summary.get('camera_intrinsics_available'))}",
        f"real_camera_pointcloud_available: {bool_text(summary.get('real_camera_pointcloud_available'))}",
        f"camera_pointcloud_source: {summary.get('camera_pointcloud_source')}",
        f"semantic_segmentation_available: {bool_text(summary.get('semantic_segmentation_available'))}",
        f"instance_segmentation_available: {bool_text(summary.get('instance_segmentation_available'))}",
        f"rtx_lidar_available: {bool_text(summary.get('rtx_lidar_available'))}",
        f"lidar_used_for_mapping: {bool_text(summary.get('lidar_used_for_mapping'))}",
        "lidar_is_required_for_pass: false",
        f"geometry_proxy_used: {bool_text(summary.get('geometry_proxy_used'))}",
        f"mounted_geometry_proxy_used: {bool_text(summary.get('mounted_geometry_proxy_used'))}",
        f"camera_follows_base_rate: {summary.get('camera_follows_base_rate')}",
        "movement_mode: kinematic_existing_a1_root",
        "real_a1_locomotion_controller: false",
        "map_type: BEV occupancy grid",
        f"mapping_method: {summary.get('mapping_method')}",
        f"map_update_source: {summary.get('map_update_source')}",
        f"map_resolution_m: {summary.get('map_resolution_m')}",
        f"step_count: {summary.get('step_count')}",
        f"successful_steps: {summary.get('successful_steps')}",
        f"valid_rgb_steps: {summary.get('valid_rgb_steps')}",
        f"valid_depth_steps: {summary.get('valid_depth_steps')}",
        f"valid_camera_pointcloud_steps: {summary.get('valid_camera_pointcloud_steps')}",
        f"valid_lidar_steps: {summary.get('valid_lidar_steps')}",
        f"initial_known_ratio: {summary.get('initial_known_ratio')}",
        f"final_known_ratio: {summary.get('final_known_ratio')}",
        f"final_occupied_cells: {summary.get('final_occupied_cells')}",
        f"final_known_free_cells: {summary.get('final_known_free_cells')}",
        f"final_unknown_cells: {summary.get('final_unknown_cells')}",
        f"total_new_known_cells: {summary.get('total_new_known_cells')}",
        f"known_ratio_monotonic_non_decreasing: {bool_text(summary.get('known_ratio_monotonic_non_decreasing'))}",
        f"map_update_behavior: {summary.get('map_update_behavior')}",
        f"plots_path: {summary.get('plots_path')}",
        f"summary_path: {summary.get('summary_json')}",
        f"safe_to_rerun_phase5_with_real_sensors: {bool_text(summary.get('safe_to_rerun_phase5_with_real_sensors'))}",
        "safe_to_continue_phase6: false",
        f"caveats: {summary.get('caveats')}",
        "training: false",
        "RL: false",
        "map_predict: false",
        "PI_finetuning: false",
        "A1_locomotion_training: false",
        "rollout_started: false",
        "",
        "## Evidence",
        "",
        f"- run_dir: {summary.get('run_dir')}",
        f"- mapping_steps_csv: {summary.get('mapping_steps_csv')}",
        f"- mapping_summary_json: {summary.get('summary_json')}",
        "- BEV map was updated from depth-backprojected real camera pointclouds.",
        "- RTX LiDAR was recorded as optional telemetry and was not used for map pass/fail.",
        "- The original USD scene was not saved or overwritten.",
        "",
        "## Negative Scope",
        "",
        "- No Phase 5 was auto-started.",
        "- No Phase 6.",
        "- No candidate generation.",
        "- No training, RL, map_predict, checkpoint, or rollout.",
        "- No geometry proxy or mounted geometry proxy mapping source.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_fallback_csvs(rows: list[dict[str, Any]], bev: RealSensorBevMap, plots_dir: Path) -> None:
    with (plots_dir / "known_ratio_curve.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["step_id", "known_ratio"])
        writer.writeheader()
        writer.writerows({"step_id": r["step_id"], "known_ratio": r["known_ratio"]} for r in rows)
    with (plots_dir / "robot_and_sensor_xy_trace.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["step_id", "robot_x", "robot_y", "sensor_x", "sensor_y"])
        writer.writeheader()
        for i, (robot, sensor) in enumerate(zip(bev.robot_trace, bev.sensor_trace)):
            writer.writerow({"step_id": i, "robot_x": robot[0], "robot_y": robot[1], "sensor_x": sensor[0], "sensor_y": sensor[1]})
    bev.save_ascii(plots_dir / "final_bev_ascii.txt")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", default=str(SCENE))
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--top_report", default=str(TOP_REPORT))
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--map_resolution_m", type=float, default=0.1)
    args = parser.parse_args()

    usd = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    logs_dir = run_dir / "logs"
    maps_dir = run_dir / "maps"
    plots_dir = run_dir / "plots"
    probes_dir = run_dir / "probes"
    reports_dir = run_dir / "reports"
    summary_dir = run_dir / "summary"
    debug_dir = run_dir / "debug_frames"
    for directory in (logs_dir, maps_dir, plots_dir, probes_dir, reports_dir, summary_dir, debug_dir):
        directory.mkdir(parents=True, exist_ok=True)

    steps_csv = summary_dir / "mapping_steps.csv"
    summary_json = summary_dir / "mapping_summary.json"
    report = reports_dir / "A1_REAL_SENSOR_MAPPING_SMOKE_REPORT.md"
    top_report = Path(args.top_report).expanduser().resolve()
    started = time.time()
    rows: list[dict[str, Any]] = []
    app = None
    summary: dict[str, Any] = {
        "phase": "Phase 4R A1 real-sensor mapping smoke",
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
        "camera_prim_path": CAMERA_PATH,
        "sensor_mount_parent": "/World/A1/base (runtime synced)",
        "previous_sensor_method": "mounted_geometry_proxy_pointcloud_from_a1_front_sensor",
        "sensor_method": "real_isaac_omniverse_rgbd",
        "real_rgb_sensor_available": False,
        "real_depth_sensor_available": False,
        "camera_params_available": False,
        "camera_intrinsics_available": False,
        "real_camera_pointcloud_available": False,
        "camera_pointcloud_source": "unavailable",
        "semantic_segmentation_available": False,
        "instance_segmentation_available": False,
        "rtx_lidar_available": False,
        "lidar_used_for_mapping": False,
        "lidar_is_required_for_pass": False,
        "geometry_proxy_used": False,
        "mounted_geometry_proxy_used": False,
        "camera_follows_base_rate": 0.0,
        "movement_mode": "kinematic_existing_a1_root",
        "real_a1_locomotion_controller": False,
        "map_type": "BEV occupancy grid",
        "mapping_method": "raycast_real_sensor_bev_mapping",
        "map_update_source": "depth_backprojection_pointcloud",
        "step_count": 0,
        "successful_steps": 0,
        "valid_rgb_steps": 0,
        "valid_depth_steps": 0,
        "valid_camera_pointcloud_steps": 0,
        "valid_lidar_steps": 0,
        "map_resolution_m": args.map_resolution_m,
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
        "safe_to_rerun_phase5_with_real_sensors": False,
        "safe_to_continue_phase6": False,
        "plots_path": str(plots_dir),
        "maps_path": str(maps_dir),
        "debug_frame_paths": [],
        "mapping_steps_csv": str(steps_csv),
        "summary_json": str(summary_json),
        "run_dir": str(run_dir),
        "caveats": [
            "RTX LiDAR is optional telemetry and not used for mapping pass/fail.",
            "Mapping update source is depth-backprojected real RGB-D pointcloud only.",
            "Runtime sensors and light are in-memory; the primary USD is not saved.",
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
        import omni.replicator.core as rep
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

        create_runtime_prims(stage, args.width, args.height)
        camera_prim = stage.GetPrimAtPath(CAMERA_PATH)
        light_prim = stage.GetPrimAtPath("/World/RuntimeSensors/phase56_runtime_fill_light")
        if not camera_prim or not camera_prim.IsValid():
            raise RuntimeError("Runtime RGB-D camera prim was not created")

        cache = UsdGeom.XformCache()
        initial_root = world_translation(cache, root)
        initial_base = world_translation(cache, base)
        summary["initial_root_pose_xyz"] = [round(v, 6) for v in initial_root]
        summary["initial_base_pose_xyz"] = [round(v, 6) for v in initial_base]
        summary["base_pose_readable"] = True

        ops = {op.GetName(): op for op in UsdGeom.Xformable(root).GetOrderedXformOps()}
        initial_orient = ops["xformOp:orient"].Get() if "xformOp:orient" in ops else None
        eye, target = expected_sensor_pose(initial_base[0], initial_base[1], initial_base[2], 0.0)
        set_world_look_at(camera_prim, eye, target)
        if light_prim and light_prim.IsValid():
            set_world_translate(light_prim, (initial_base[0], initial_base[1], initial_base[2] + 2.5))

        render_product = rep.create.render_product(CAMERA_PATH, (int(args.width), int(args.height)))
        camera_annotators, annotator_errors = attach_camera_annotators(rep, render_product)
        summary["camera_annotator_errors"] = annotator_errors
        required = {"rgb", "distance_to_image_plane", "camera_params"}
        if not required.issubset(camera_annotators):
            raise RuntimeError(f"Required RGB-D camera annotators unavailable: {annotator_errors}")

        lidar_info = try_create_lidar(stage, rep, eye, target)
        lidar_annotator = lidar_info.pop("lidar_annotator", None)
        summary["rtx_lidar_available"] = bool(lidar_info.get("lidar_available"))
        summary["rtx_lidar_attempted"] = bool(lidar_info.get("lidar_attempted"))
        summary["lidar_failure_reason"] = lidar_info.get("lidar_failure_reason", "")

        try:
            rep.orchestrator.set_capture_on_play(False)
        except Exception as exc:
            summary["set_capture_on_play_error"] = repr(exc)

        actions = [
            ("initial_pose", 0.00, 0.00, 0.0),
            ("forward_1", 0.14, 0.00, 0.0),
            ("yaw_left", 0.10, 0.00, math.radians(6.0)),
            ("forward_2", 0.14, 0.00, 0.0),
            ("strafe_left", 0.04, 0.07, 0.0),
            ("yaw_right", 0.10, 0.00, math.radians(-7.0)),
            ("forward_3", 0.14, 0.00, 0.0),
            ("strafe_right", 0.04, -0.07, 0.0),
            ("yaw_left_small", 0.08, 0.00, math.radians(4.0)),
            ("forward_4", 0.12, 0.00, 0.0),
            ("final_observe", 0.00, 0.00, 0.0),
        ][: max(8, min(args.steps, 12))]

        bev = RealSensorBevMap(initial_base[0], initial_base[1], resolution_m=args.map_resolution_m)
        root_x, root_y, root_z = initial_root
        yaw = 0.0
        last_base_x, last_base_y, last_yaw = initial_base[0], initial_base[1], 0.0
        first_rgb = last_rgb = None
        first_depth = last_depth = None
        first_semantic = last_semantic = None

        for step_id, (_action, forward, lateral, dyaw) in enumerate(actions):
            yaw += dyaw
            root_x += math.cos(yaw) * forward - math.sin(yaw) * lateral
            root_y += math.sin(yaw) * forward + math.cos(yaw) * lateral
            set_root_pose(root, (root_x, root_y, root_z), yaw, initial_orient)
            for _ in range(2):
                app.update()

            cache = UsdGeom.XformCache()
            base_x, base_y, base_z = world_translation(cache, base)
            eye, target = expected_sensor_pose(base_x, base_y, base_z, yaw)
            set_world_look_at(camera_prim, eye, target)
            if light_prim and light_prim.IsValid():
                set_world_translate(light_prim, (base_x, base_y, base_z + 2.5))
            lidar_prim = stage.GetPrimAtPath(LIDAR_PATH)
            if lidar_prim and lidar_prim.IsValid():
                set_world_look_at(lidar_prim, eye, target)

            for _ in range(3):
                app.update()
                try:
                    rep.orchestrator.step()
                except Exception as exc:
                    summary.setdefault("orchestrator_step_errors", []).append(repr(exc))
                app.update()

            cache = UsdGeom.XformCache()
            camera_x, camera_y, camera_z = world_translation(cache, camera_prim)
            camera_error = math.sqrt((camera_x - eye[0]) ** 2 + (camera_y - eye[1]) ** 2 + (camera_z - eye[2]) ** 2)
            camera_follows = camera_error < 0.02

            rgb = rgb_stats(camera_annotators["rgb"].get_data())
            depth = depth_stats(camera_annotators["distance_to_image_plane"].get_data())
            camera_params_data = camera_annotators["camera_params"].get_data()
            camera_params_available = isinstance(camera_params_data, dict) and bool(camera_params_data)
            intrinsics_available, intrinsics = intrinsics_from_camera_params(
                camera_params_data,
                depth["width"] or int(args.width),
                depth["height"] or int(args.height),
            )
            if depth["available"] and intrinsics_available:
                camera_points = pointcloud_from_depth(depth["array"], intrinsics)
                world_points = camera_points_to_world(camera_points, eye, target)
                pc = pointcloud_stats(camera_points)
                pc_source = "depth_backprojection"
            else:
                camera_points = np.empty((0, 3), dtype=np.float32)
                world_points = np.empty((0, 3), dtype=np.float32)
                pc = pointcloud_stats(camera_points)
                pc_source = "unavailable"

            lidar_available = False
            lidar_point_count = 0
            lidar_finite_ratio = 0.0
            if lidar_annotator is not None:
                try:
                    stats = lidar_stats(lidar_annotator.get_data())
                    lidar_available = bool(stats["available"])
                    lidar_point_count = int(stats["point_count"])
                    lidar_finite_ratio = float(stats["finite_ratio"])
                except Exception as exc:
                    summary["lidar_failure_reason"] = repr(exc)

            semantic_available = False
            instance_available = False
            semantic_data = None
            if "semantic_segmentation" in camera_annotators:
                try:
                    semantic_data = camera_annotators["semantic_segmentation"].get_data()
                    semantic_available = segmentation_available(semantic_data)
                except Exception as exc:
                    summary.setdefault("semantic_errors", []).append(repr(exc))
            if "instance_segmentation" in camera_annotators:
                try:
                    instance_available = segmentation_available(camera_annotators["instance_segmentation"].get_data())
                except Exception as exc:
                    summary.setdefault("instance_errors", []).append(repr(exc))

            map_stats = bev.update(base_x, base_y, yaw, camera_x, camera_y, camera_z, world_points)
            if step_id == 0:
                first_rgb = rgb["array"]
                first_depth = depth["array"]
                first_semantic = semantic_data
            last_rgb = rgb["array"]
            last_depth = depth["array"]
            last_semantic = semantic_data

            moved = math.hypot(base_x - last_base_x, base_y - last_base_y)
            yaw_change = abs(yaw - last_yaw)
            collision_flag = abs(base_x - initial_base[0]) > 2.0 or abs(base_y - initial_base[1]) > 2.0
            stuck_flag = step_id > 0 and moved < 0.005 and yaw_change < 0.005 and forward != 0.0
            falling_flag = base_z < 0.2 or base_z > 1.5 or abs(base_z - initial_base[2]) > 0.6
            failure = ""
            if not camera_follows:
                failure = "camera_not_synced_to_a1_base"
            elif not rgb["available"]:
                failure = "rgb_invalid"
            elif not depth["available"]:
                failure = "depth_invalid"
            elif not camera_params_available:
                failure = "camera_params_unavailable"
            elif not intrinsics_available:
                failure = "camera_intrinsics_unavailable"
            elif not pc["available"]:
                failure = "depth_backprojection_pointcloud_invalid"
            elif pc_source not in {"depth_backprojection", "isaac_pointcloud_annotator"}:
                failure = "camera_pointcloud_source_invalid"
            elif collision_flag:
                failure = "kinematic_boundary_violation"
            elif stuck_flag:
                failure = "a1_base_pose_did_not_change"
            elif falling_flag:
                failure = "a1_base_z_out_of_expected_range"

            row = {
                "step_id": step_id,
                "timestamp": round(time.time(), 3),
                "a1_root_prim": A1_ROOT,
                "base_frame": BASE_FRAME,
                "base_x": round(base_x, 4),
                "base_y": round(base_y, 4),
                "base_z": round(base_z, 4),
                "base_yaw": round(yaw, 4),
                "camera_prim_path": CAMERA_PATH,
                "camera_x": round(camera_x, 4),
                "camera_y": round(camera_y, 4),
                "camera_z": round(camera_z, 4),
                "camera_yaw": round(yaw, 4),
                "camera_pitch": round(MOUNT_RPY[1], 4),
                "camera_follows_base": camera_follows,
                "rgb_available": rgb["available"],
                "rgb_nonzero_ratio": rgb["nonzero_ratio"],
                "depth_available": depth["available"],
                "depth_valid_ratio": depth["valid_ratio"],
                "camera_params_available": camera_params_available,
                "camera_intrinsics_available": intrinsics_available,
                "camera_pointcloud_available": pc["available"],
                "camera_pointcloud_source": pc_source,
                "camera_pointcloud_point_count": pc["point_count"],
                "camera_pointcloud_finite_ratio": pc["finite_ratio"],
                "semantic_available": semantic_available,
                "instance_available": instance_available,
                "lidar_available": lidar_available,
                "lidar_point_count": lidar_point_count,
                "lidar_finite_ratio": lidar_finite_ratio,
                "sensor_method": "real_isaac_omniverse_rgbd",
                "map_update_source": "depth_backprojection_pointcloud",
                **map_stats,
                "collision_flag": collision_flag,
                "stuck_flag": stuck_flag,
                "falling_flag": falling_flag,
                "failure_reason": failure,
            }
            rows.append(row)
            last_base_x, last_base_y, last_yaw = base_x, base_y, yaw

        with steps_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        debug_paths = []
        for name, array, saver in [
            ("first_rgb.png", first_rgb, save_rgb_png),
            ("last_rgb.png", last_rgb, save_rgb_png),
            ("first_depth_vis.png", first_depth, save_depth_vis),
            ("last_depth_vis.png", last_depth, save_depth_vis),
            ("first_semantic.png", first_semantic, save_semantic_png),
            ("last_semantic.png", last_semantic, save_semantic_png),
        ]:
            out = debug_dir / name
            if saver(array, out):
                debug_paths.append(str(out))
        summary["debug_frame_paths"] = debug_paths

        plots_saved = save_plots(bev, rows, plots_dir)
        write_fallback_csvs(rows, bev, plots_dir)
        bev.save_ascii(maps_dir / "final_bev_ascii.txt")

        success = [r for r in rows if not r["failure_reason"]]
        rgb_valid = [r for r in rows if r["rgb_available"]]
        depth_valid = [r for r in rows if r["depth_available"]]
        pc_valid = [r for r in rows if r["camera_pointcloud_available"] and r["camera_pointcloud_source"] == "depth_backprojection"]
        lidar_valid = [r for r in rows if r["lidar_available"]]
        follows = [r for r in rows if r["camera_follows_base"]]
        collision_count = sum(1 for r in rows if r["collision_flag"])
        stuck_count = sum(1 for r in rows if r["stuck_flag"])
        falling_count = sum(1 for r in rows if r["falling_flag"])
        known_ratios = [float(r["known_ratio"]) for r in rows]
        monotonic = all(known_ratios[i] + 1e-6 >= known_ratios[i - 1] for i in range(1, len(known_ratios)))
        first_positive = any(int(r["new_known_cells"]) > 0 for r in rows[: min(4, len(rows))])
        final = rows[-1]
        core_files = find_core_dumps(WORKSPACE)

        map_ok = bool(
            int(final["occupied_cells"]) > 0
            and int(final["known_free_cells"]) > 0
            and int(final["unknown_cells"]) > 0
            and float(final["known_ratio"]) > float(rows[0]["known_ratio"])
            and first_positive
            and monotonic
        )
        pass_ok = bool(
            summary["scene_open_result"]
            and summary["stage_available"]
            and summary["a1_root_exists"]
            and summary["base_pose_readable"]
            and len(rows) >= 8
            and len(success) >= 8
            and len(rgb_valid) / len(rows) >= 0.8
            and len(depth_valid) / len(rows) >= 0.8
            and len(pc_valid) / len(rows) >= 0.8
            and len(follows) == len(rows)
            and summary["geometry_proxy_used"] is False
            and summary["mounted_geometry_proxy_used"] is False
            and map_ok
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
            and not core_files
        )

        summary.update({
            "step_count": len(rows),
            "successful_steps": len(success),
            "valid_rgb_steps": len(rgb_valid),
            "valid_depth_steps": len(depth_valid),
            "valid_camera_pointcloud_steps": len(pc_valid),
            "valid_lidar_steps": len(lidar_valid),
            "real_rgb_sensor_available": len(rgb_valid) / len(rows) >= 0.8,
            "real_depth_sensor_available": len(depth_valid) / len(rows) >= 0.8,
            "camera_params_available": all(bool(r["camera_params_available"]) for r in rows),
            "camera_intrinsics_available": all(bool(r["camera_intrinsics_available"]) for r in rows),
            "real_camera_pointcloud_available": len(pc_valid) / len(rows) >= 0.8,
            "camera_pointcloud_source": "depth_backprojection" if pc_valid else "unavailable",
            "semantic_segmentation_available": any(bool(r["semantic_available"]) for r in rows),
            "instance_segmentation_available": any(bool(r["instance_available"]) for r in rows),
            "rtx_lidar_available": bool(summary["rtx_lidar_available"]) or bool(lidar_valid),
            "lidar_used_for_mapping": False,
            "camera_follows_base_rate": round(len(follows) / len(rows), 4) if rows else 0.0,
            "initial_known_ratio": rows[0]["known_ratio"],
            "final_known_ratio": final["known_ratio"],
            "final_occupied_cells": final["occupied_cells"],
            "final_known_free_cells": final["known_free_cells"],
            "final_unknown_cells": final["unknown_cells"],
            "total_new_known_cells": int(sum(int(r["new_known_cells"]) for r in rows)),
            "known_ratio_monotonic_non_decreasing": monotonic,
            "map_snapshots_saved": True,
            "bev_renders_saved": bool(plots_saved),
            "map_update_behavior": "pass" if map_ok else "fail",
            "collision_count": collision_count,
            "stuck_count": stuck_count,
            "falling_count": falling_count,
            "core_dump_found": bool(core_files),
            "core_dump_files": core_files,
            "safe_to_rerun_phase5_with_real_sensors": pass_ok,
            "safe_to_continue_phase6": False,
        })
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
