#!/usr/bin/env python3
"""Phase 5R A1 real-sensor candidate gain smoke.

This script opens the primary USD read-only, reuses the real Isaac/Omniverse
RGB-D sensor route from Phase 5.6/4R, updates a BEV partial map from
depth-backprojected camera points, and scores candidate viewpoints with a
classical information-gain heuristic. It does not train, run VLM inference,
run Phase 6, run a long rollout, use geometry proxies, or save the USD.
"""

from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
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

from phase4r_a1_real_sensor_mapping_smoke import (  # noqa: E402
    KNOWN_FREE,
    OCCUPIED,
    UNKNOWN,
    RealSensorBevMap,
    camera_points_to_world,
)
from phase56_a1_real_sensor_suite_smoke import (  # noqa: E402
    A1_ROOT,
    BASE_FRAME,
    CAMERA_PATH,
    LIDAR_PATH,
    MOUNT_RPY,
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


PHASE = "Phase 5R-real A1 candidate viewpoint + information gain smoke with real sensors"
TOP_REPORT = WORKSPACE / "runs/A1_REAL_SENSOR_CANDIDATE_GAIN_REPORT.md"
PROJECT_NAME = "A1-VLM-LA Explorer"
MAIN_GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"
SENSOR_METHOD = "real_isaac_omniverse_rgbd"
CAMERA_POINTCLOUD_SOURCE = "depth_backprojection"
MAP_TYPE = "BEV occupancy grid"
MAPPING_METHOD = "raycast_real_sensor_bev_mapping"
MAP_UPDATE_SOURCE = "depth_backprojection_pointcloud"
CANDIDATE_SAMPLING_METHOD = "radial_24_candidates_3_radii_8_angles_around_a1_base"
PATH_COST_METHOD = "astar_bev_grid_unknown_penalty"
INFORMATION_GAIN_METHOD = "real_sensor_bev_unknown_visibility"
SCORE_FORMULA = "score = information_gain - 0.2 * path_cost - 1.0 * collision_penalty - 200.0 * invalid_penalty"


def finite(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def angle_wrap(angle: float) -> float:
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def cell_to_world(bev: RealSensorBevMap, row: int, col: int) -> tuple[float, float]:
    return (
        bev.origin_x + (col + 0.5) * bev.resolution_m,
        bev.origin_y + (row + 0.5) * bev.resolution_m,
    )


def ray_cells(bev: RealSensorBevMap, x0: float, y0: float, x1: float, y1: float) -> list[tuple[int, int]]:
    dist = math.hypot(x1 - x0, y1 - y0)
    steps = max(2, int(math.ceil(dist / max(1e-6, bev.resolution_m * 0.5))))
    cells: list[tuple[int, int]] = []
    last = None
    for idx in range(steps + 1):
        t = idx / steps
        cell = bev.world_to_cell(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
        if cell is not None and cell != last:
            cells.append(cell)
            last = cell
    return cells


def ray_blocked_by_occupied(bev: RealSensorBevMap, x0: float, y0: float, x1: float, y1: float) -> bool:
    cells = ray_cells(bev, x0, y0, x1, y1)
    for row, col in cells[1:-1]:
        if int(bev.grid[row, col]) == OCCUPIED:
            return True
    return False


def occupied_near_count(bev: RealSensorBevMap, row: int, col: int, radius_m: float = 0.35) -> int:
    rad = max(1, int(math.ceil(radius_m / bev.resolution_m)))
    count = 0
    for rr in range(max(0, row - rad), min(bev.height, row + rad + 1)):
        for cc in range(max(0, col - rad), min(bev.width, col + rad + 1)):
            wx, wy = cell_to_world(bev, rr, cc)
            cx, cy = cell_to_world(bev, row, col)
            if math.hypot(wx - cx, wy - cy) <= radius_m and int(bev.grid[rr, cc]) == OCCUPIED:
                count += 1
    return count


def astar_path_cost(bev: RealSensorBevMap, start: tuple[int, int] | None, goal: tuple[int, int] | None) -> tuple[float, bool]:
    if start is None or goal is None:
        return float("inf"), False
    if int(bev.grid[goal[0], goal[1]]) == OCCUPIED:
        return float("inf"), False
    if start == goal:
        return 0.0, True

    def heuristic(cell: tuple[int, int]) -> float:
        return math.hypot(cell[0] - goal[0], cell[1] - goal[1]) * bev.resolution_m

    neighbors = [
        (-1, 0, 1.0),
        (1, 0, 1.0),
        (0, -1, 1.0),
        (0, 1, 1.0),
        (-1, -1, math.sqrt(2.0)),
        (-1, 1, math.sqrt(2.0)),
        (1, -1, math.sqrt(2.0)),
        (1, 1, math.sqrt(2.0)),
    ]
    open_heap: list[tuple[float, float, tuple[int, int]]] = [(heuristic(start), 0.0, start)]
    best = {start: 0.0}
    visited = set()
    while open_heap:
        _, cost, cell = heapq.heappop(open_heap)
        if cell in visited:
            continue
        if cell == goal:
            return round(cost, 4), True
        visited.add(cell)
        row, col = cell
        for dr, dc, step_scale in neighbors:
            nr, nc = row + dr, col + dc
            if nr < 0 or nr >= bev.height or nc < 0 or nc >= bev.width:
                continue
            value = int(bev.grid[nr, nc])
            if value == OCCUPIED:
                continue
            unknown_penalty = 0.08 if value == UNKNOWN else 0.0
            step_cost = bev.resolution_m * step_scale + unknown_penalty
            new_cost = cost + step_cost
            ncell = (nr, nc)
            if new_cost + 1e-9 < best.get(ncell, float("inf")):
                best[ncell] = new_cost
                heapq.heappush(open_heap, (new_cost + heuristic(ncell), new_cost, ncell))
    return float("inf"), False


def visible_unknown_cells(
    bev: RealSensorBevMap,
    x: float,
    y: float,
    yaw: float,
    radius_m: float = 3.0,
    fov_rad: float = math.radians(95.0),
) -> int:
    center = bev.world_to_cell(x, y)
    if center is None:
        return 0
    rad = max(1, int(math.ceil(radius_m / bev.resolution_m)))
    count = 0
    cr, cc = center
    for row in range(max(0, cr - rad), min(bev.height, cr + rad + 1)):
        for col in range(max(0, cc - rad), min(bev.width, cc + rad + 1)):
            if int(bev.grid[row, col]) != UNKNOWN:
                continue
            wx, wy = cell_to_world(bev, row, col)
            dist = math.hypot(wx - x, wy - y)
            if dist > radius_m or dist < bev.resolution_m:
                continue
            bearing = math.atan2(wy - y, wx - x)
            if abs(angle_wrap(bearing - yaw)) > fov_rad / 2.0:
                continue
            if ray_blocked_by_occupied(bev, x, y, wx, wy):
                continue
            count += 1
    return int(count)


def generate_candidates(base_x: float, base_y: float, base_z: float, base_yaw: float) -> list[dict[str, float | int]]:
    candidates: list[dict[str, float | int]] = []
    radii = [1.0, 2.2, 3.6]
    angle_offsets = [math.radians(v) for v in (-157.5, -112.5, -67.5, -22.5, 22.5, 67.5, 112.5, 157.5)]
    candidate_id = 0
    for radius in radii:
        for offset in angle_offsets:
            yaw = angle_wrap(base_yaw + offset)
            x = base_x + math.cos(yaw) * radius
            y = base_y + math.sin(yaw) * radius
            candidates.append({
                "candidate_id": candidate_id,
                "x": x,
                "y": y,
                "z": base_z,
                "yaw": yaw,
                "dx": x - base_x,
                "dy": y - base_y,
                "dyaw": angle_wrap(yaw - base_yaw),
                "distance_to_robot": radius,
            })
            candidate_id += 1
    return candidates


def score_candidates(bev: RealSensorBevMap, base_pose: dict[str, float]) -> list[dict[str, Any]]:
    base_cell = bev.world_to_cell(base_pose["x"], base_pose["y"])
    scored: list[dict[str, Any]] = []
    for candidate in generate_candidates(base_pose["x"], base_pose["y"], base_pose["z"], base_pose["yaw"]):
        row: dict[str, Any] = {
            "candidate_id": int(candidate["candidate_id"]),
            "base_x": round(base_pose["x"], 4),
            "base_y": round(base_pose["y"], 4),
            "base_z": round(base_pose["z"], 4),
            "base_yaw": round(base_pose["yaw"], 4),
            "x": round(float(candidate["x"]), 4),
            "y": round(float(candidate["y"]), 4),
            "z": round(float(candidate["z"]), 4),
            "yaw": round(float(candidate["yaw"]), 4),
            "dx": round(float(candidate["dx"]), 4),
            "dy": round(float(candidate["dy"]), 4),
            "dyaw": round(float(candidate["dyaw"]), 4),
            "distance_to_robot": round(float(candidate["distance_to_robot"]), 4),
            "path_cost_method": PATH_COST_METHOD,
            "information_gain_method": INFORMATION_GAIN_METHOD,
        }
        cell = bev.world_to_cell(float(candidate["x"]), float(candidate["y"]))
        reasons: list[str] = []
        occupied = False
        near_occupied = 0
        if cell is None:
            reasons.append("outside_bev_map")
        else:
            occupied = int(bev.grid[cell[0], cell[1]]) == OCCUPIED
            if occupied:
                reasons.append("occupied_cell")
            near_occupied = occupied_near_count(bev, cell[0], cell[1])
            if near_occupied > 0:
                reasons.append("collision_margin_occupied")
        is_valid = cell is not None and not occupied and near_occupied == 0
        path_cost, reachable = astar_path_cost(bev, base_cell, cell)
        if not reachable:
            reasons.append("astar_unreachable")
        gain = visible_unknown_cells(bev, float(candidate["x"]), float(candidate["y"]), float(candidate["yaw"])) if is_valid else 0
        collision_penalty = float(near_occupied * 2.0 + (50.0 if occupied else 0.0))
        invalid_penalty = 0.0 if is_valid and reachable else 1.0
        score = float(gain) - 0.2 * (path_cost if math.isfinite(path_cost) else 999.0) - collision_penalty - 200.0 * invalid_penalty
        row.update({
            "is_valid": bool(is_valid),
            "is_reachable": bool(reachable),
            "collision_risk": bool(near_occupied > 0 or occupied),
            "collision_penalty": round(collision_penalty, 4),
            "path_cost": round(path_cost, 4) if math.isfinite(path_cost) else None,
            "visible_unknown_cells": int(gain),
            "information_gain": int(gain),
            "score": round(score, 4),
            "selected_by_classical": False,
            "failure_reason": ";".join(reasons) if reasons else "",
        })
        scored.append(row)

    selectable = [r for r in scored if r["is_valid"] and r["is_reachable"] and int(r["information_gain"]) > 0]
    if selectable:
        selected = max(selectable, key=lambda r: (float(r["score"]), int(r["information_gain"]), -int(r["candidate_id"])))
        selected["selected_by_classical"] = True
    return scored


def write_step_candidate_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def render_candidate_overlay(
    bev: RealSensorBevMap,
    step_id: int,
    base_pose: dict[str, float],
    sensor_pose: tuple[float, float, float],
    rows: list[dict[str, Any]],
    path: Path,
) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    cmap = matplotlib.colors.ListedColormap(["#1f2933", "#d9ead3", "#b3342b"])
    plt.figure(figsize=(6.0, 6.0))
    plt.imshow(bev.grid, origin="lower", cmap=cmap, interpolation="nearest")

    robot_cell = bev.world_to_cell(base_pose["x"], base_pose["y"])
    sensor_cell = bev.world_to_cell(sensor_pose[0], sensor_pose[1])
    if robot_cell:
        plt.scatter([robot_cell[1]], [robot_cell[0]], s=80, marker="o", color="#2b6cff", label="A1")
    if sensor_cell:
        plt.scatter([sensor_cell[1]], [sensor_cell[0]], s=70, marker="x", color="#ffbf00", label="sensor")

    valid_rows = [r for r in rows if r["is_valid"] and r["is_reachable"]]
    invalid_rows = [r for r in rows if not (r["is_valid"] and r["is_reachable"])]
    for subset, marker, color, label in [
        (invalid_rows, "x", "#8a8f98", "invalid"),
        (valid_rows, "o", "#14b8a6", "valid"),
    ]:
        xs, ys, labels = [], [], []
        for row in subset:
            cell = bev.world_to_cell(float(row["x"]), float(row["y"]))
            if cell:
                ys.append(cell[0])
                xs.append(cell[1])
                labels.append(str(row["candidate_id"]))
        if xs:
            plt.scatter(xs, ys, s=38, marker=marker, color=color, label=label)
            for x, y, text in zip(xs, ys, labels):
                plt.text(x + 0.6, y + 0.4, text, fontsize=6, color="#f8fafc")

    selected = [r for r in rows if r["selected_by_classical"]]
    if selected:
        cell = bev.world_to_cell(float(selected[0]["x"]), float(selected[0]["y"]))
        if cell:
            plt.scatter([cell[1]], [cell[0]], s=150, marker="*", color="#f97316", label="selected")
            plt.text(cell[1] + 0.8, cell[0] - 1.2, f"id {selected[0]['candidate_id']}", fontsize=8, color="#f97316")

    plt.title(f"Phase 5R candidate overlay step {step_id}")
    plt.legend(loc="lower right", fontsize=7)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=110)
    plt.close()
    return True


def write_overlay_ascii(path: Path, bev: RealSensorBevMap, rows: list[dict[str, Any]], selected_id: int | None) -> None:
    chars = {UNKNOWN: "?", KNOWN_FREE: ".", OCCUPIED: "#"}
    candidate_cells = {}
    for row in rows:
        cell = bev.world_to_cell(float(row["x"]), float(row["y"]))
        if cell:
            candidate_cells[cell] = "*" if selected_id == int(row["candidate_id"]) else "c"
    lines = []
    for row in range(bev.height - 1, -1, -1):
        parts = []
        for col in range(bev.width):
            parts.append(candidate_cells.get((row, col), chars[int(bev.grid[row, col])]))
        lines.append("".join(parts))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# A1 Real Sensor Candidate Gain Smoke Report",
        "",
        "phase: Phase 5R-real",
        "workspace: /home/ubuntu22/VLA",
        f"project_name: {PROJECT_NAME}",
        f"scene_path: {summary.get('scene_path')}",
        "robot_platform: unitree_a1",
        "robot_source: existing_usd_prim",
        "a1_root_prim: /World/A1",
        "base_frame: /World/A1/base",
        f"sensor_method: {SENSOR_METHOD}",
        f"real_rgb_sensor_available: {bool_text(summary.get('real_rgb_sensor_available'))}",
        f"real_depth_sensor_available: {bool_text(summary.get('real_depth_sensor_available'))}",
        f"camera_params_available: {bool_text(summary.get('camera_params_available'))}",
        f"camera_intrinsics_available: {bool_text(summary.get('camera_intrinsics_available'))}",
        f"real_camera_pointcloud_available: {bool_text(summary.get('real_camera_pointcloud_available'))}",
        f"camera_pointcloud_source: {summary.get('camera_pointcloud_source')}",
        f"semantic_segmentation_available: {bool_text(summary.get('semantic_segmentation_available'))}",
        f"instance_segmentation_available: {bool_text(summary.get('instance_segmentation_available'))}",
        f"rtx_lidar_available: {bool_text(summary.get('rtx_lidar_available'))}",
        f"lidar_used_for_candidate_gain: {bool_text(summary.get('lidar_used_for_candidate_gain'))}",
        "lidar_is_required_for_pass: false",
        f"geometry_proxy_used: {bool_text(summary.get('geometry_proxy_used'))}",
        f"mounted_geometry_proxy_used: {bool_text(summary.get('mounted_geometry_proxy_used'))}",
        f"map_type: {summary.get('map_type')}",
        f"mapping_method: {summary.get('mapping_method')}",
        f"map_update_source: {summary.get('map_update_source')}",
        f"candidate_sampling_method: {summary.get('candidate_sampling_method')}",
        f"path_cost_method: {summary.get('path_cost_method')}",
        f"information_gain_method: {summary.get('information_gain_method')}",
        f"score_formula: {summary.get('score_formula')}",
        f"step_count: {summary.get('step_count')}",
        f"candidate_count_per_step: {summary.get('candidate_count_per_step')}",
        f"total_candidate_rows: {summary.get('total_candidate_rows')}",
        f"valid_candidate_ratio: {summary.get('valid_candidate_ratio')}",
        f"positive_gain_candidate_ratio: {summary.get('positive_gain_candidate_ratio')}",
        f"selected_candidate_valid_rate: {summary.get('selected_candidate_valid_rate')}",
        f"selected_is_top_score_rate: {summary.get('selected_is_top_score_rate')}",
        f"path_cost_constant: {bool_text(summary.get('path_cost_constant'))}",
        f"min_path_cost: {summary.get('min_path_cost')}",
        f"max_path_cost: {summary.get('max_path_cost')}",
        f"min_information_gain: {summary.get('min_information_gain')}",
        f"max_information_gain: {summary.get('max_information_gain')}",
        f"failure_count: {summary.get('failure_count')}",
        f"BEV candidate render path: {summary.get('bev_candidate_render_path')}",
        f"candidate_summary path: {summary.get('candidate_summary_csv')}",
        f"candidate_steps path: {summary.get('candidate_steps_jsonl')}",
        f"safe_to_continue_phase6: {bool_text(summary.get('safe_to_continue_phase6'))}",
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
        f"- candidate_summary_json: {summary.get('summary_json')}",
        f"- candidate_summary_csv: {summary.get('candidate_summary_csv')}",
        f"- candidate_steps_jsonl: {summary.get('candidate_steps_jsonl')}",
        f"- bev_renders_dir: {summary.get('bev_renders_dir')}",
        "- Candidate scoring used the BEV map updated from depth-backprojected real RGB-D pointclouds.",
        "- RTX LiDAR and segmentation were recorded only as optional telemetry.",
        "- The original USD scene was not saved or overwritten.",
        "",
        "## Negative Scope",
        "",
        "- No Phase 6 was run automatically.",
        "- No VLM inference or fine-tuning.",
        "- No training, RL, map_predict, checkpoint, or rollout.",
        "- No geometry proxy or mounted geometry proxy candidate-gain source.",
        "- No Go2 label is used as the actual robot platform.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_initial_summary(usd: Path, run_dir: Path) -> dict[str, Any]:
    return {
        "phase": PHASE,
        "workspace": str(WORKSPACE),
        "project_name": PROJECT_NAME,
        "main_goal": MAIN_GOAL,
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
        "sensor_method": SENSOR_METHOD,
        "real_rgb_sensor_available": False,
        "real_depth_sensor_available": False,
        "camera_params_available": False,
        "camera_intrinsics_available": False,
        "real_camera_pointcloud_available": False,
        "camera_pointcloud_source": "unavailable",
        "semantic_segmentation_available": False,
        "instance_segmentation_available": False,
        "rtx_lidar_available": False,
        "lidar_used_for_candidate_gain": False,
        "lidar_is_required_for_pass": False,
        "geometry_proxy_used": False,
        "mounted_geometry_proxy_used": False,
        "map_type": MAP_TYPE,
        "mapping_method": MAPPING_METHOD,
        "map_update_source": MAP_UPDATE_SOURCE,
        "candidate_sampling_method": CANDIDATE_SAMPLING_METHOD,
        "path_cost_method": PATH_COST_METHOD,
        "information_gain_method": INFORMATION_GAIN_METHOD,
        "score_formula": SCORE_FORMULA,
        "movement_mode": "kinematic_existing_a1_root_smoke",
        "real_a1_locomotion_controller": False,
        "training_started": False,
        "RL_started": False,
        "map_predict_started": False,
        "checkpoint_created": False,
        "rollout_started": False,
        "safe_to_continue_phase6": False,
        "run_dir": str(run_dir),
        "exception": None,
        "traceback": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", default=str(SCENE))
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--top_report", default=str(TOP_REPORT))
    parser.add_argument("--steps", type=int, default=6)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--map_resolution_m", type=float, default=0.1)
    args = parser.parse_args()

    usd = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    logs_dir = run_dir / "logs"
    candidates_dir = run_dir / "candidates"
    plots_dir = run_dir / "plots"
    reports_dir = run_dir / "reports"
    summary_dir = run_dir / "summary"
    bev_renders_dir = run_dir / "bev_renders"
    debug_dir = run_dir / "debug_frames"
    for directory in [logs_dir, candidates_dir, plots_dir, reports_dir, summary_dir, bev_renders_dir, debug_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    summary_json = summary_dir / "candidate_summary.json"
    candidate_csv = summary_dir / "candidate_summary.csv"
    candidate_steps_jsonl = summary_dir / "candidate_steps.jsonl"
    report = reports_dir / "A1_REAL_SENSOR_CANDIDATE_GAIN_REPORT.md"
    top_report = Path(args.top_report).expanduser().resolve()
    started = time.time()
    summary = build_initial_summary(usd, run_dir)
    app = None
    exit_code = 1

    rows: list[dict[str, Any]] = []
    step_rows: list[dict[str, Any]] = []
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

        create_runtime_prims(stage, int(args.width), int(args.height))
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
            ("forward_observe", 0.12, 0.00, 0.0),
            ("yaw_left_observe", 0.08, 0.00, math.radians(6.0)),
            ("strafe_left_observe", 0.04, 0.06, 0.0),
            ("yaw_right_observe", 0.08, 0.00, math.radians(-8.0)),
            ("forward_final", 0.12, 0.00, math.radians(3.0)),
            ("settle_observe", 0.00, 0.00, 0.0),
        ][: max(5, min(int(args.steps), 8))]

        bev = RealSensorBevMap(initial_base[0], initial_base[1], resolution_m=float(args.map_resolution_m))
        root_x, root_y, root_z = initial_root
        yaw = 0.0
        last_base_x, last_base_y, last_yaw = initial_base[0], initial_base[1], 0.0
        first_rgb = last_rgb = None
        first_depth = last_depth = None
        first_semantic = last_semantic = None

        for step_id, (_action, forward, lateral, dyaw) in enumerate(actions):
            yaw = angle_wrap(yaw + dyaw)
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
                pc_source = CAMERA_POINTCLOUD_SOURCE
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
            base_pose = {"x": base_x, "y": base_y, "z": base_z, "yaw": yaw}
            scored = score_candidates(bev, base_pose)
            selected = [r for r in scored if r["selected_by_classical"]]
            selected_id = int(selected[0]["candidate_id"]) if selected else None
            failure_reason = None if selected else "no_valid_positive_gain_candidate"

            for row in scored:
                row["step_id"] = step_id
                row["sensor_method"] = SENSOR_METHOD
                row["camera_pointcloud_source"] = pc_source
                row["geometry_proxy_used"] = False
                row["mounted_geometry_proxy_used"] = False
                rows.append(row)
            write_step_candidate_csv(candidates_dir / f"candidate_step_{step_id:03d}.csv", scored)

            render_rel = f"bev_renders/candidate_overlay_step_{step_id:03d}.png"
            render_path = run_dir / render_rel
            if not render_candidate_overlay(bev, step_id, base_pose, (camera_x, camera_y, camera_z), scored, render_path):
                render_rel = f"bev_renders/candidate_overlay_step_{step_id:03d}.txt"
                render_path = run_dir / render_rel
                write_overlay_ascii(render_path, bev, scored, selected_id)

            if step_id == 0:
                first_rgb = rgb["array"]
                first_depth = depth["array"]
                first_semantic = semantic_data
            last_rgb = rgb["array"]
            last_depth = depth["array"]
            last_semantic = semantic_data

            moved = math.hypot(base_x - last_base_x, base_y - last_base_y)
            yaw_change = abs(angle_wrap(yaw - last_yaw))
            collision_flag = abs(base_x - initial_base[0]) > 2.0 or abs(base_y - initial_base[1]) > 2.0
            stuck_flag = step_id > 0 and moved < 0.005 and yaw_change < 0.005 and forward != 0.0
            falling_flag = base_z < 0.2 or base_z > 1.5 or abs(base_z - initial_base[2]) > 0.6
            sensor_failure = ""
            if not camera_follows:
                sensor_failure = "camera_not_synced_to_a1_base"
            elif not rgb["available"]:
                sensor_failure = "rgb_invalid"
            elif not depth["available"]:
                sensor_failure = "depth_invalid"
            elif not camera_params_available:
                sensor_failure = "camera_params_unavailable"
            elif not intrinsics_available:
                sensor_failure = "camera_intrinsics_unavailable"
            elif not pc["available"]:
                sensor_failure = "depth_backprojection_pointcloud_invalid"
            elif pc_source != CAMERA_POINTCLOUD_SOURCE:
                sensor_failure = "camera_pointcloud_source_invalid"
            elif collision_flag:
                sensor_failure = "kinematic_boundary_violation"
            elif stuck_flag:
                sensor_failure = "a1_base_pose_did_not_change"
            elif falling_flag:
                sensor_failure = "a1_base_z_out_of_expected_range"
            elif failure_reason:
                sensor_failure = failure_reason

            valid_count = sum(1 for r in scored if r["is_valid"] and r["is_reachable"])
            positive_gain_count = sum(1 for r in scored if int(r["information_gain"]) > 0)
            step_row = {
                "phase": PHASE,
                "step_id": step_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "a1_root_prim": A1_ROOT,
                "base_frame": BASE_FRAME,
                "sensor_method": SENSOR_METHOD,
                "camera_pointcloud_source": pc_source,
                "geometry_proxy_used": False,
                "mounted_geometry_proxy_used": False,
                "base_pose": {
                    "x": round(base_x, 4),
                    "y": round(base_y, 4),
                    "z": round(base_z, 4),
                    "yaw": round(yaw, 4),
                },
                "sensor_pose": {
                    "x": round(camera_x, 4),
                    "y": round(camera_y, 4),
                    "z": round(camera_z, 4),
                    "yaw": round(yaw, 4),
                    "pitch": round(MOUNT_RPY[1], 4),
                },
                "map_stats": {
                    "known_ratio": map_stats["known_ratio"],
                    "occupied_cells": map_stats["occupied_cells"],
                    "known_free_cells": map_stats["known_free_cells"],
                    "unknown_cells": map_stats["unknown_cells"],
                    "new_known_cells": map_stats["new_known_cells"],
                },
                "candidate_count": len(scored),
                "valid_candidate_count": valid_count,
                "positive_gain_candidate_count": positive_gain_count,
                "selected_candidate_id": selected_id,
                "selected_score": selected[0]["score"] if selected else None,
                "failure_reason": sensor_failure or None,
                "bev_candidate_render": render_rel,
                "rgb_available": rgb["available"],
                "depth_available": depth["available"],
                "camera_params_available": camera_params_available,
                "camera_intrinsics_available": intrinsics_available,
                "camera_pointcloud_available": pc["available"],
                "camera_follows_base": camera_follows,
                "semantic_available": semantic_available,
                "instance_available": instance_available,
                "lidar_available": lidar_available,
                "lidar_point_count": lidar_point_count,
                "lidar_finite_ratio": round(lidar_finite_ratio, 4),
                "collision_flag": collision_flag,
                "stuck_flag": stuck_flag,
                "falling_flag": falling_flag,
            }
            step_rows.append(step_row)
            last_base_x, last_base_y, last_yaw = base_x, base_y, yaw

        with candidate_csv.open("w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "step_id",
                "candidate_id",
                "base_x",
                "base_y",
                "base_z",
                "base_yaw",
                "x",
                "y",
                "z",
                "yaw",
                "dx",
                "dy",
                "dyaw",
                "distance_to_robot",
                "is_valid",
                "is_reachable",
                "collision_risk",
                "collision_penalty",
                "path_cost",
                "path_cost_method",
                "visible_unknown_cells",
                "information_gain",
                "information_gain_method",
                "score",
                "selected_by_classical",
                "failure_reason",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

        with candidate_steps_jsonl.open("w", encoding="utf-8") as f:
            for step_row in step_rows:
                f.write(json.dumps(step_row, ensure_ascii=False) + "\n")

        debug_paths = []
        for name, array, saver in [
            ("first_rgb.png", first_rgb, save_rgb_png),
            ("last_rgb.png", last_rgb, save_rgb_png),
            ("first_depth_vis.png", first_depth, save_depth_vis),
            ("last_depth_vis.png", last_depth, save_depth_vis),
        ]:
            out = debug_dir / name
            if saver(array, out):
                debug_paths.append(str(out))
        summary["debug_frame_paths"] = debug_paths

        if last_semantic is not None:
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                plt.imsave(debug_dir / "last_semantic.png", np.asarray(last_semantic.get("data", last_semantic)), cmap="tab20")
                summary.setdefault("debug_frame_paths", []).append(str(debug_dir / "last_semantic.png"))
            except Exception as exc:
                summary.setdefault("semantic_debug_errors", []).append(repr(exc))

        core_files = find_core_dumps(WORKSPACE)
        selected_rows = [r for r in rows if r["selected_by_classical"]]
        valid_rows = [r for r in rows if r["is_valid"] and r["is_reachable"]]
        positive_rows = [r for r in rows if int(r["information_gain"]) > 0]
        path_costs = [finite(r["path_cost"], float("nan")) for r in rows if r["path_cost"] is not None]
        path_costs = [v for v in path_costs if math.isfinite(v)]
        gains = [int(r["information_gain"]) for r in rows]
        candidate_counts = [int(r["candidate_count"]) for r in step_rows]
        valid_step_counts = [int(r["valid_candidate_count"]) for r in step_rows]
        positive_step_counts = [int(r["positive_gain_candidate_count"]) for r in step_rows]

        selected_valid = [
            r for r in selected_rows
            if r["is_valid"] and r["is_reachable"] and int(r["information_gain"]) > 0
        ]
        top_score_matches = 0
        selected_steps = 0
        for step_id in sorted({int(r["step_id"]) for r in rows}):
            step_candidates = [r for r in rows if int(r["step_id"]) == step_id]
            selectable = [r for r in step_candidates if r["is_valid"] and r["is_reachable"] and int(r["information_gain"]) > 0]
            selected = [r for r in step_candidates if r["selected_by_classical"]]
            if not selected:
                continue
            selected_steps += 1
            best = max(selectable, key=lambda r: (float(r["score"]), int(r["information_gain"]), -int(r["candidate_id"]))) if selectable else None
            if best is not None and int(best["candidate_id"]) == int(selected[0]["candidate_id"]):
                top_score_matches += 1

        successful_steps = [
            r for r in step_rows
            if r["failure_reason"] is None
            and bool(r["rgb_available"])
            and bool(r["depth_available"])
            and bool(r["camera_params_available"])
            and bool(r["camera_intrinsics_available"])
            and bool(r["camera_pointcloud_available"])
            and bool(r["camera_follows_base"])
        ]
        rgb_valid = [r for r in step_rows if bool(r["rgb_available"])]
        depth_valid = [r for r in step_rows if bool(r["depth_available"])]
        pc_valid = [r for r in step_rows if bool(r["camera_pointcloud_available"]) and r["camera_pointcloud_source"] == CAMERA_POINTCLOUD_SOURCE]
        follows = [r for r in step_rows if bool(r["camera_follows_base"])]
        collision_count = sum(1 for r in step_rows if bool(r["collision_flag"]))
        stuck_count = sum(1 for r in step_rows if bool(r["stuck_flag"]))
        falling_count = sum(1 for r in step_rows if bool(r["falling_flag"]))
        final_stats = step_rows[-1]["map_stats"] if step_rows else {}
        initial_stats = step_rows[0]["map_stats"] if step_rows else {}

        path_cost_constant = len(path_costs) > 1 and (max(path_costs) - min(path_costs)) < 1e-6
        failure_count = len(step_rows) - len(successful_steps)
        pass_ok = bool(
            summary["scene_open_result"]
            and summary["stage_available"]
            and summary["a1_root_exists"]
            and summary["base_pose_readable"]
            and len(step_rows) >= 5
            and len(successful_steps) >= 5
            and min(candidate_counts or [0]) >= 16
            and min(valid_step_counts or [0]) > 0
            and any(count > 0 for count in positive_step_counts)
            and len(rgb_valid) / len(step_rows) >= 0.8
            and len(depth_valid) / len(step_rows) >= 0.8
            and len(pc_valid) / len(step_rows) >= 0.8
            and len(follows) == len(step_rows)
            and len(selected_rows) == len(step_rows)
            and len(selected_valid) == len(selected_rows)
            and selected_steps > 0
            and top_score_matches == selected_steps
            and path_costs
            and not path_cost_constant
            and gains
            and max(gains) > min(gains)
            and max(gains) > 0
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
            and not core_files
            and summary["geometry_proxy_used"] is False
            and summary["mounted_geometry_proxy_used"] is False
        )

        summary.update({
            "step_count": len(step_rows),
            "successful_steps": len(successful_steps),
            "candidate_count_per_step": candidate_counts[0] if candidate_counts and len(set(candidate_counts)) == 1 else candidate_counts,
            "total_candidate_rows": len(rows),
            "valid_candidate_ratio": round(len(valid_rows) / len(rows), 4) if rows else 0.0,
            "positive_gain_candidate_ratio": round(len(positive_rows) / len(rows), 4) if rows else 0.0,
            "selected_candidate_valid_rate": round(len(selected_valid) / len(selected_rows), 4) if selected_rows else 0.0,
            "selected_is_top_score_rate": round(top_score_matches / selected_steps, 4) if selected_steps else 0.0,
            "path_cost_constant": bool(path_cost_constant),
            "min_path_cost": round(min(path_costs), 4) if path_costs else None,
            "max_path_cost": round(max(path_costs), 4) if path_costs else None,
            "min_information_gain": min(gains) if gains else None,
            "max_information_gain": max(gains) if gains else None,
            "failure_count": failure_count,
            "real_rgb_sensor_available": len(rgb_valid) / len(step_rows) >= 0.8 if step_rows else False,
            "real_depth_sensor_available": len(depth_valid) / len(step_rows) >= 0.8 if step_rows else False,
            "camera_params_available": all(bool(r["camera_params_available"]) for r in step_rows) if step_rows else False,
            "camera_intrinsics_available": all(bool(r["camera_intrinsics_available"]) for r in step_rows) if step_rows else False,
            "real_camera_pointcloud_available": len(pc_valid) / len(step_rows) >= 0.8 if step_rows else False,
            "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE if pc_valid else "unavailable",
            "semantic_segmentation_available": any(bool(r["semantic_available"]) for r in step_rows),
            "instance_segmentation_available": any(bool(r["instance_available"]) for r in step_rows),
            "rtx_lidar_available": bool(summary["rtx_lidar_available"]) or any(bool(r["lidar_available"]) for r in step_rows),
            "lidar_used_for_candidate_gain": False,
            "camera_follows_base_rate": round(len(follows) / len(step_rows), 4) if step_rows else 0.0,
            "map_resolution_m": float(args.map_resolution_m),
            "initial_known_ratio": initial_stats.get("known_ratio"),
            "final_known_ratio": final_stats.get("known_ratio"),
            "final_occupied_cells": final_stats.get("occupied_cells"),
            "final_known_free_cells": final_stats.get("known_free_cells"),
            "final_unknown_cells": final_stats.get("unknown_cells"),
            "total_new_known_cells": int(sum(int(r["map_stats"]["new_known_cells"]) for r in step_rows)),
            "map_update_behavior": "pass" if final_stats.get("known_ratio", 0.0) > initial_stats.get("known_ratio", -1.0) else "flat",
            "bev_candidate_render_path": str(bev_renders_dir),
            "bev_renders_dir": str(bev_renders_dir),
            "candidate_summary_csv": str(candidate_csv),
            "candidate_steps_jsonl": str(candidate_steps_jsonl),
            "summary_json": str(summary_json),
            "collision_count": collision_count,
            "stuck_count": stuck_count,
            "falling_count": falling_count,
            "core_dump_found": bool(core_files),
            "core_dump_files": core_files,
            "safe_to_continue_phase6": pass_ok,
            "caveats": [
                "Candidate gain is classical scoring, not VLM inference.",
                "BEV map and candidate gains use depth-backprojected real RGB-D pointclouds.",
                "RTX LiDAR and segmentation are optional telemetry and not required for pass/fail.",
                "Runtime sensors and light are in-memory; the primary USD is not saved.",
            ],
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
