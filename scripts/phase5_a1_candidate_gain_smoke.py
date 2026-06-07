#!/usr/bin/env python3
"""Phase 5 Unitree A1 candidate viewpoint and information-gain smoke."""

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
TOP_REPORT = WORKSPACE / "runs/A1_CANDIDATE_GAIN_REPORT.md"
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

    def cell_to_world(self, row: int, col: int) -> tuple[float, float]:
        return self.origin_x + (col + 0.5) * self.resolution_m, self.origin_y + (row + 0.5) * self.resolution_m

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
                wx, wy = self.cell_to_world(row, col)
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

    def line_cells(self, x0: float, y0: float, x1: float, y1: float) -> list[tuple[int, int]]:
        dist = math.hypot(x1 - x0, y1 - y0)
        steps = max(1, int(dist / (self.resolution_m * 0.5)))
        cells: list[tuple[int, int]] = []
        seen = set()
        for idx in range(steps + 1):
            t = idx / steps
            cell = self.world_to_cell(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            if cell and cell not in seen:
                cells.append(cell)
                seen.add(cell)
        return cells

    def local_occupied_count(self, x: float, y: float, radius_m: float = 0.25) -> int:
        cell = self.world_to_cell(x, y)
        if cell is None:
            return 9999
        cr, cc = cell
        rad = max(1, int(math.ceil(radius_m / self.resolution_m)))
        count = 0
        for row in range(max(0, cr - rad), min(self.height, cr + rad + 1)):
            for col in range(max(0, cc - rad), min(self.width, cc + rad + 1)):
                wx, wy = self.cell_to_world(row, col)
                if math.hypot(wx - x, wy - y) <= radius_m and self.grid[row, col] == OCCUPIED:
                    count += 1
        return count

    def visible_unknown_cells(self, x: float, y: float, yaw: float, radius_m: float = 2.2, fov_rad: float = math.radians(95)) -> int:
        cell = self.world_to_cell(x, y)
        if cell is None:
            return 0
        cr, cc = cell
        rad = int(math.ceil(radius_m / self.resolution_m))
        count = 0
        for row in range(max(0, cr - rad), min(self.height, cr + rad + 1)):
            for col in range(max(0, cc - rad), min(self.width, cc + rad + 1)):
                if self.grid[row, col] != UNKNOWN:
                    continue
                wx, wy = self.cell_to_world(row, col)
                dx, dy = wx - x, wy - y
                dist = math.hypot(dx, dy)
                if dist <= 0.05 or dist > radius_m:
                    continue
                angle = math.atan2(dy, dx)
                delta = abs(math.atan2(math.sin(angle - yaw), math.cos(angle - yaw)))
                if delta > fov_rad / 2.0:
                    continue
                blocked = False
                for rr, cc2 in self.line_cells(x, y, wx, wy)[:-1]:
                    if self.grid[rr, cc2] == OCCUPIED:
                        blocked = True
                        break
                if not blocked:
                    count += 1
        return count


def candidate_rows_for_step(bev: BevMap, step_id: int, base: tuple[float, float, float], base_yaw: float) -> list[dict[str, Any]]:
    base_x, base_y, base_z = base
    rows: list[dict[str, Any]] = []
    radii = [0.9, 1.5, 2.2]
    angles = [base_yaw + math.radians(i * 45) for i in range(8)]
    for radius_idx, radius in enumerate(radii):
        for angle_idx, angle in enumerate(angles):
            candidate_id = radius_idx * len(angles) + angle_idx
            x = base_x + radius * math.cos(angle)
            y = base_y + radius * math.sin(angle)
            z = base_z
            yaw = math.atan2(y - base_y, x - base_x)
            cell = bev.world_to_cell(x, y)
            in_map = cell is not None
            occupied_here = bool(in_map and bev.grid[cell] == OCCUPIED)
            margin_hits = bev.local_occupied_count(x, y, radius_m=0.25)
            collision_risk = min(1.0, margin_hits / 3.0) if in_map else 1.0
            collision_penalty = 2.5 * collision_risk
            line = bev.line_cells(base_x, base_y, x, y) if in_map else []
            blocked_cells = sum(1 for c in line if bev.grid[c] == OCCUPIED)
            unknown_cells_on_path = sum(1 for c in line if bev.grid[c] == UNKNOWN)
            is_reachable = bool(in_map and not occupied_here and blocked_cells <= 1 and unknown_cells_on_path <= max(10, len(line) * 0.65))
            is_valid = bool(in_map and not occupied_here and margin_hits == 0)
            distance = math.hypot(x - base_x, y - base_y)
            path_cost = distance + 0.45 * blocked_cells + 0.08 * unknown_cells_on_path + 0.65 * collision_risk
            visible_unknown = bev.visible_unknown_cells(x, y, yaw)
            info_gain = float(visible_unknown)
            invalid_penalty = 1000.0 if not (is_valid and is_reachable) else 0.0
            score = info_gain - 0.35 * path_cost - collision_penalty - invalid_penalty
            reason = ""
            if not in_map:
                reason = "candidate_outside_map"
            elif occupied_here:
                reason = "candidate_on_occupied_cell"
            elif margin_hits > 0:
                reason = "collision_margin_occupied"
            elif not is_reachable:
                reason = "approx_bev_unreachable"
            rows.append({
                "step_id": step_id,
                "candidate_id": candidate_id,
                "base_x": round(base_x, 4),
                "base_y": round(base_y, 4),
                "base_z": round(base_z, 4),
                "base_yaw": round(base_yaw, 4),
                "x": round(x, 4),
                "y": round(y, 4),
                "z": round(z, 4),
                "yaw": round(yaw, 4),
                "dx": round(x - base_x, 4),
                "dy": round(y - base_y, 4),
                "dyaw": round(math.atan2(math.sin(yaw - base_yaw), math.cos(yaw - base_yaw)), 4),
                "distance_to_robot": round(distance, 4),
                "is_valid": is_valid,
                "is_reachable": is_reachable,
                "collision_risk": round(collision_risk, 4),
                "collision_penalty": round(collision_penalty, 4),
                "path_cost": round(path_cost, 4),
                "path_cost_method": "euclidean_plus_obstacle_penalty",
                "visible_unknown_cells": visible_unknown,
                "information_gain": round(info_gain, 4),
                "information_gain_method": "bev_unknown_visibility_proxy",
                "score": round(score, 4),
                "selected_by_classical": False,
                "failure_reason": reason,
            })
    valid = [r for r in rows if r["is_valid"] and r["is_reachable"] and r["information_gain"] > 0]
    if valid:
        selected = max(valid, key=lambda r: (float(r["score"]), float(r["information_gain"]), -float(r["path_cost"])))
        selected["selected_by_classical"] = True
    return rows


def render_candidates(bev: BevMap, rows: list[dict[str, Any]], base: tuple[float, float, float], selected_id: int | None, out_path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False
    cmap = matplotlib.colors.ListedColormap(["#222222", "#d7f0d0", "#c23b22"])
    plt.figure(figsize=(7, 7))
    plt.imshow(bev.grid, origin="lower", cmap=cmap, interpolation="nearest")
    bcell = bev.world_to_cell(base[0], base[1])
    if bcell:
        plt.scatter([bcell[1]], [bcell[0]], marker="*", s=120, c="#2b6cff", label="A1")
    max_score = max(float(r["score"]) for r in rows if r["is_valid"] and r["is_reachable"]) if any(r["is_valid"] and r["is_reachable"] for r in rows) else 1.0
    min_score = min(float(r["score"]) for r in rows if r["is_valid"] and r["is_reachable"]) if any(r["is_valid"] and r["is_reachable"] for r in rows) else 0.0
    span = max(1e-6, max_score - min_score)
    for r in rows:
        cell = bev.world_to_cell(float(r["x"]), float(r["y"]))
        if not cell:
            continue
        is_selected = selected_id is not None and int(r["candidate_id"]) == selected_id
        color = "#f4d35e" if is_selected else ("#4cc9f0" if r["is_valid"] and r["is_reachable"] else "#8d99ae")
        size = 90 if is_selected else 35 + 45 * max(0.0, (float(r["score"]) - min_score) / span)
        plt.scatter([cell[1]], [cell[0]], c=color, s=size, edgecolors="black", linewidths=0.6)
        plt.text(cell[1] + 0.5, cell[0] + 0.5, str(r["candidate_id"]), color="white", fontsize=7)
    plt.title(f"A1 candidate overlay step {rows[0]['step_id']}")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    return True


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# A1 Candidate Gain Report",
        "",
        "phase: Phase 5",
        "workspace: /home/ubuntu22/VLA",
        "project_name: A1-VLM-LA Explorer",
        f"scene_path: {summary['scene_path']}",
        "robot_platform: unitree_a1",
        "robot_source: existing_usd_prim",
        "a1_root_prim: /World/A1",
        "base_frame: /World/A1/base",
        "previous_proxy_results_status: superseded_for_formal_a1_pipeline",
        f"sensor_method: {summary['sensor_method']}",
        f"map_type: {summary['map_type']}",
        f"mapping_method: {summary['mapping_method']}",
        f"candidate_sampling_method: {summary['candidate_sampling_method']}",
        f"path_cost_method: {summary['path_cost_method']}",
        f"information_gain_method: {summary['information_gain_method']}",
        f"score_formula: {summary['score_formula']}",
        f"step_count: {summary['step_count']}",
        f"candidate_count_per_step: {summary['candidate_count_per_step']}",
        f"total_candidate_rows: {summary['total_candidate_rows']}",
        f"valid_candidate_ratio: {summary['valid_candidate_ratio']}",
        f"positive_gain_candidate_ratio: {summary['positive_gain_candidate_ratio']}",
        f"selected_candidate_valid_rate: {summary['selected_candidate_valid_rate']}",
        f"selected_is_top_score_rate: {summary['selected_is_top_score_rate']}",
        f"path_cost_constant: {bool_text(summary['path_cost_constant'])}",
        f"min_path_cost: {summary['min_path_cost']}",
        f"max_path_cost: {summary['max_path_cost']}",
        f"min_information_gain: {summary['min_information_gain']}",
        f"max_information_gain: {summary['max_information_gain']}",
        f"failure_count: {summary['failure_count']}",
        f"BEV_candidate_render_path: {summary['bev_renders_dir']}",
        f"candidate_summary_path: {summary['candidate_summary_csv']}",
        f"candidate_steps_path: {summary['candidate_steps_jsonl']}",
        f"safe_to_continue_phase6: {bool_text(summary['safe_to_continue_phase6'])}",
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
    lines.extend(f"- {caveat}" for caveat in summary.get("caveats", []))
    lines.extend([
        "",
        "## Negative Scope",
        "",
        "- No VLM training or inference.",
        "- No VLM-LA interface smoke.",
        "- No RL training.",
        "- No map_predict training or mainline implementation.",
        "- No PI/openpi action-head fine-tuning.",
        "- No A1 locomotion policy training.",
        "- No long rollout.",
        "- No temporary Go2 proxy was created or used as formal data.",
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
    candidates_dir = run_dir / "candidates"
    plots_dir = run_dir / "plots"
    reports_dir = run_dir / "reports"
    summary_dir = run_dir / "summary"
    bev_renders_dir = run_dir / "bev_renders"
    for d in (logs_dir, candidates_dir, plots_dir, reports_dir, summary_dir, bev_renders_dir):
        d.mkdir(parents=True, exist_ok=True)

    candidate_csv = summary_dir / "candidate_summary.csv"
    candidate_json = summary_dir / "candidate_summary.json"
    candidate_steps_jsonl = summary_dir / "candidate_steps.jsonl"
    report = reports_dir / "A1_CANDIDATE_GAIN_REPORT.md"
    top_report = Path(args.top_report).expanduser().resolve()
    started = time.time()
    app = None
    all_rows: list[dict[str, Any]] = []
    step_records: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "phase": "Phase 5 A1 candidate viewpoint + information gain smoke",
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
        "sensor_method": "geometry_proxy_pointcloud_from_a1_base_pose",
        "map_type": "BEV occupancy grid",
        "mapping_method": "raycast_bev_proxy_mapping",
        "candidate_sampling_method": "radial_24_candidates_3_radii_8_angles_around_a1_base",
        "path_cost_method": "euclidean_plus_obstacle_penalty",
        "information_gain_method": "bev_unknown_visibility_proxy",
        "score_formula": "score = information_gain - 0.35 * path_cost - collision_penalty - invalid_penalty",
        "step_count": 0,
        "candidate_count_per_step": 24,
        "total_candidate_rows": 0,
        "valid_candidate_ratio": 0.0,
        "positive_gain_candidate_ratio": 0.0,
        "selected_candidate_valid_rate": 0.0,
        "selected_is_top_score_rate": 0.0,
        "path_cost_constant": True,
        "min_path_cost": 0.0,
        "max_path_cost": 0.0,
        "min_information_gain": 0.0,
        "max_information_gain": 0.0,
        "failure_count": 0,
        "safe_to_continue_phase6": False,
        "training_started": False,
        "RL_started": False,
        "map_predict_started": False,
        "checkpoint_created": False,
        "rollout_started": False,
        "temporary_go2_proxy_created": False,
        "run_dir": str(run_dir),
        "candidate_summary_csv": str(candidate_csv),
        "candidate_summary_json": str(candidate_json),
        "candidate_steps_jsonl": str(candidate_steps_jsonl),
        "bev_renders_dir": str(bev_renders_dir),
        "reports_dir": str(reports_dir),
        "caveats": [
            "This is proxy-mapping based candidate smoke from existing USD A1, not final real-sensor data.",
            "Information gain uses BEV unknown visibility proxy, not real RGB-D SLAM or VLM inference.",
            "Path cost uses Euclidean distance plus BEV obstacle/unknown penalties, not a full planner.",
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
        base_prim = stage.GetPrimAtPath(BASE_FRAME)
        if not root or not root.IsValid():
            raise RuntimeError("Existing USD A1 prim /World/A1 was not found")
        if not base_prim or not base_prim.IsValid():
            raise RuntimeError("Existing USD base frame /World/A1/base was not found")
        summary["a1_root_exists"] = True
        summary["a1_has_articulation_root_api"] = bool(root.HasAPI(UsdPhysics.ArticulationRootAPI))
        cache = UsdGeom.XformCache()
        initial_root = world_translation(cache, root)
        initial_base = world_translation(cache, base_prim)
        summary["initial_root_pose_xyz"] = [round(v, 6) for v in initial_root]
        summary["initial_base_pose_xyz"] = [round(v, 6) for v in initial_base]
        summary["base_pose_readable"] = True
        ops = {op.GetName(): op for op in UsdGeom.Xformable(root).GetOrderedXformOps()}
        initial_orient = ops["xformOp:orient"].Get() if "xformOp:orient" in ops else None
        cameras = [str(p.GetPath()) for p in stage.Traverse() if p.GetTypeName() == "Camera"]
        summary["available_camera_count"] = len(cameras)
        summary["a1_bound_sensor_prims"] = [p for p in cameras if p.startswith(A1_ROOT + "/")][:20]
        if not summary["a1_bound_sensor_prims"]:
            summary["caveats"].append("No A1-bound USD camera/sensor prim was found; candidates use proxy BEV observations only.")

        bev = BevMap(initial_base[0], initial_base[1], resolution_m=0.1)
        actions = [
            ("initial_pose", 0.0, 0.0, 0.0),
            ("small_forward", 0.18, 0.0, 0.0),
            ("small_forward", 0.16, 0.0, 0.0),
            ("small_yaw_left", 0.0, 0.0, math.radians(10)),
            ("small_forward", 0.16, 0.0, 0.0),
            ("small_lateral_left", 0.0, 0.12, 0.0),
            ("small_yaw_right", 0.0, 0.0, math.radians(-8)),
            ("small_forward", 0.16, 0.0, 0.0),
        ][: max(5, min(args.steps, 10))]
        root_x, root_y, root_z = initial_root
        yaw = 0.0
        for step_id, (_action, forward, lateral, dyaw) in enumerate(actions):
            yaw += dyaw
            root_x += math.cos(yaw) * forward - math.sin(yaw) * lateral
            root_y += math.sin(yaw) * forward + math.cos(yaw) * lateral
            set_root_pose(root, (root_x, root_y, root_z), yaw, initial_orient)
            for _ in range(2):
                app.update()
            cache = UsdGeom.XformCache()
            base = world_translation(cache, base_prim)
            points = make_pointcloud(base[0], base[1], base[2], yaw)
            sensor_valid, _point_count, _finite_ratio = pointcloud_stats(points)
            map_stats = bev.update(base[0], base[1], yaw, points)
            rows = candidate_rows_for_step(bev, step_id, base, yaw)
            selected = next((r for r in rows if r["selected_by_classical"]), None)
            selected_id = int(selected["candidate_id"]) if selected else None
            render_path = bev_renders_dir / f"candidate_overlay_step_{step_id:03d}.png"
            render_saved = render_candidates(bev, rows, base, selected_id, render_path)
            valid_count = sum(1 for r in rows if r["is_valid"] and r["is_reachable"])
            positive_count = sum(1 for r in rows if r["is_valid"] and r["is_reachable"] and r["information_gain"] > 0)
            failure_reason = None if selected else "no_valid_positive_gain_candidate"
            step_record = {
                "phase": summary["phase"],
                "step_id": step_id,
                "timestamp": round(time.time(), 3),
                "a1_root_prim": A1_ROOT,
                "base_frame": BASE_FRAME,
                "base_pose": {"x": round(base[0], 4), "y": round(base[1], 4), "z": round(base[2], 4), "yaw": round(yaw, 4)},
                "map_stats": {
                    "known_ratio": map_stats["known_ratio"],
                    "occupied_cells": map_stats["occupied_cells"],
                    "known_free_cells": map_stats["known_free_cells"],
                    "unknown_cells": map_stats["unknown_cells"],
                },
                "candidate_count": len(rows),
                "valid_candidate_count": valid_count,
                "positive_gain_candidate_count": positive_count,
                "selected_candidate_id": selected_id,
                "selected_score": selected["score"] if selected else None,
                "failure_reason": failure_reason,
                "bev_candidate_render": str(render_path.relative_to(run_dir)) if render_saved else None,
                "sensor_valid": sensor_valid,
            }
            step_records.append(step_record)
            all_rows.extend(rows)

        with candidate_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)
        with candidate_steps_jsonl.open("w", encoding="utf-8") as f:
            for record in step_records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        valid_rows = [r for r in all_rows if r["is_valid"] and r["is_reachable"]]
        positive_rows = [r for r in all_rows if r["information_gain"] > 0]
        selected_rows = [r for r in all_rows if r["selected_by_classical"]]
        selected_valid = [r for r in selected_rows if r["is_valid"] and r["is_reachable"]]
        selected_top = 0
        for record in step_records:
            step_rows = [r for r in all_rows if r["step_id"] == record["step_id"] and r["is_valid"] and r["is_reachable"] and r["information_gain"] > 0]
            selected = [r for r in step_rows if r["selected_by_classical"]]
            if selected and selected[0]["score"] == max(r["score"] for r in step_rows):
                selected_top += 1
        path_costs = [float(r["path_cost"]) for r in all_rows]
        gains = [float(r["information_gain"]) for r in all_rows]
        failure_count = sum(1 for r in step_records if r["failure_reason"])
        path_cost_constant = bool(max(path_costs) - min(path_costs) < 1e-6)
        core_files = find_core_dumps(WORKSPACE)
        summary.update({
            "step_count": len(step_records),
            "candidate_count_per_step": 24,
            "total_candidate_rows": len(all_rows),
            "valid_candidate_ratio": round(len(valid_rows) / len(all_rows), 4) if all_rows else 0.0,
            "positive_gain_candidate_ratio": round(len(positive_rows) / len(all_rows), 4) if all_rows else 0.0,
            "selected_candidate_valid_rate": round(len(selected_valid) / len(selected_rows), 4) if selected_rows else 0.0,
            "selected_is_top_score_rate": round(selected_top / len(step_records), 4) if step_records else 0.0,
            "path_cost_constant": path_cost_constant,
            "min_path_cost": round(min(path_costs), 4) if path_costs else 0.0,
            "max_path_cost": round(max(path_costs), 4) if path_costs else 0.0,
            "min_information_gain": round(min(gains), 4) if gains else 0.0,
            "max_information_gain": round(max(gains), 4) if gains else 0.0,
            "failure_count": failure_count,
            "core_dump_found": bool(core_files),
            "core_dump_files": core_files,
        })
        summary["safe_to_continue_phase6"] = bool(
            summary["scene_open_result"]
            and summary["stage_available"]
            and summary["a1_root_exists"]
            and summary["base_pose_readable"]
            and len(step_records) >= 5
            and all(r["candidate_count"] >= 16 for r in step_records)
            and any(r["valid_candidate_count"] > 0 for r in step_records)
            and any(r["positive_gain_candidate_count"] > 0 for r in step_records)
            and not path_cost_constant
            and summary["max_information_gain"] > summary["min_information_gain"]
            and summary["selected_candidate_valid_rate"] == 1.0
            and summary["selected_is_top_score_rate"] == 1.0
            and not summary["core_dump_found"]
        )
        candidate_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        exit_code = 0 if summary["safe_to_continue_phase6"] else 2
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        exit_code = 1
    finally:
        summary["elapsed_sec"] = round(time.time() - started, 3)
        candidate_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
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
