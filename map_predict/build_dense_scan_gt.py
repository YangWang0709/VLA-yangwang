#!/usr/bin/env python3
"""MapPredict Phase 1 Route A: dense-scan pseudo full occupancy GT.

This script opens the repaired USD scenes read-only, creates a runtime RGB-D
camera, scans each scene from a small grid of virtual camera poses, backprojects
real Isaac/Omniverse depth into world points, and fuses the observations into a
bounded 3D occupancy prototype.

The generated occupancy is explicitly pseudo GT. It is useful for MVP dataset
construction and smoke training only after separate approval; it is not perfect
mesh ground truth.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


WORKSPACE = Path("/home/ubuntu22/VLA")
RUNS_DIR = WORKSPACE / "runs"
DATA_ROOT = WORKSPACE / "data/map_predict/full_occupancy_gt"
SCRIPT_DIR = WORKSPACE / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase56_a1_real_sensor_suite_smoke import (  # noqa: E402
    CAMERA_PATH,
    LIGHT_PATH,
    attach_camera_annotators,
    create_runtime_prims,
    depth_stats,
    intrinsics_from_camera_params,
    pointcloud_from_depth,
    set_world_look_at,
    set_world_translate,
)
from phase4r_a1_real_sensor_mapping_smoke import camera_points_to_world  # noqa: E402


PHASE = "MapPredict Phase 1 full occupancy GT prototype"
PROJECT = "A1-VLM-LA Explorer"
GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"
VOXEL_SIZE_DEFAULT = 0.2
MAX_VOXELS_DEFAULT = 10_000_000


@dataclass(frozen=True)
class SceneSpec:
    scene_id: str
    scene_path: Path
    quality_dir: Path


SCENES = [
    SceneSpec(
        scene_id="old_home_like_scene_v1",
        scene_path=WORKSPACE / "scenes/primary_building_scene_repaired/home_like_scene_v1.usd",
        quality_dir=RUNS_DIR / "phase9_human_review_packet_20260607_213732",
    ),
    SceneSpec(
        scene_id="new_building_scene_1",
        scene_path=WORKSPACE / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda",
        quality_dir=RUNS_DIR / "new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002",
    ),
]


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
            if limit is not None and len(rows) >= limit:
                break
    return rows


def estimate_bounds_from_quality(scene: SceneSpec) -> dict[str, Any]:
    rows = read_jsonl(scene.quality_dir / "quality/accepted_samples.jsonl", limit=80)
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for row in rows:
        sample = row.get("sample") or {}
        pose = sample.get("robot_pose") or {}
        if "x" in pose and "y" in pose:
            xs.append(float(pose["x"]))
            ys.append(float(pose["y"]))
            zs.append(float(pose.get("z", 0.6)))
        for cand in sample.get("candidates") or []:
            if "x" in cand and "y" in cand:
                xs.append(float(cand["x"]))
                ys.append(float(cand["y"]))
                zs.append(float(cand.get("z", 0.6)))
    if not xs or not ys:
        return {
            "source": "fallback_origin_window",
            "min_x": -4.5,
            "max_x": 4.5,
            "min_y": -6.5,
            "max_y": 2.5,
            "min_z": 0.0,
            "max_z": 2.6,
        }
    return {
        "source": "quality_sample_robot_and_candidate_bounds",
        "min_x": min(xs) - 1.5,
        "max_x": max(xs) + 1.5,
        "min_y": min(ys) - 1.5,
        "max_y": max(ys) + 1.5,
        "min_z": 0.0,
        "max_z": max(2.6, max(zs) + 1.6),
    }


def grid_from_bounds(bounds: dict[str, Any], voxel_size: float, max_voxels: int) -> dict[str, Any]:
    voxel = float(voxel_size)
    while True:
        width = max(1.0, float(bounds["max_x"]) - float(bounds["min_x"]))
        height = max(1.0, float(bounds["max_y"]) - float(bounds["min_y"]))
        depth = max(1.0, float(bounds["max_z"]) - float(bounds["min_z"]))
        w = max(1, int(math.ceil(width / voxel)))
        h = max(1, int(math.ceil(height / voxel)))
        d = max(1, int(math.ceil(depth / voxel)))
        voxels = d * h * w
        if voxels <= max_voxels:
            break
        voxel += 0.05
    origin = [float(bounds["min_x"]), float(bounds["min_y"]), float(bounds["min_z"])]
    transform = np.eye(4, dtype=np.float32)
    transform[0, 0] = 1.0 / voxel
    transform[1, 1] = 1.0 / voxel
    transform[2, 2] = 1.0 / voxel
    transform[0, 3] = -origin[0] / voxel
    transform[1, 3] = -origin[1] / voxel
    transform[2, 3] = -origin[2] / voxel
    return {
        "voxel_size": voxel,
        "origin_xyz": origin,
        "grid_shape": [d, h, w],
        "world_to_grid": transform,
        "voxel_count": voxels,
    }


def generate_scan_poses(bounds: dict[str, Any], views: int) -> list[dict[str, Any]]:
    min_x, max_x = float(bounds["min_x"]), float(bounds["max_x"])
    min_y, max_y = float(bounds["min_y"]), float(bounds["max_y"])
    xs = np.linspace(min_x + 0.22 * (max_x - min_x), max_x - 0.22 * (max_x - min_x), 3)
    ys = np.linspace(min_y + 0.22 * (max_y - min_y), max_y - 0.22 * (max_y - min_y), 3)
    yaws = [0.0, math.pi / 2.0, math.pi, -math.pi / 2.0]
    poses: list[dict[str, Any]] = []
    for y in ys:
        for x in xs:
            for yaw in yaws:
                eye = (float(x), float(y), 1.2)
                target = (
                    eye[0] + math.cos(yaw) * 2.0,
                    eye[1] + math.sin(yaw) * 2.0,
                    0.95,
                )
                poses.append({"eye": eye, "target": target, "yaw": float(yaw)})
                if len(poses) >= views:
                    return poses
    return poses


class DenseOccupancyGrid:
    def __init__(self, grid_meta: dict[str, Any]) -> None:
        self.voxel_size = float(grid_meta["voxel_size"])
        self.origin = np.asarray(grid_meta["origin_xyz"], dtype=np.float32)
        self.shape = tuple(int(v) for v in grid_meta["grid_shape"])
        self.free = np.zeros(self.shape, dtype=bool)
        self.occupied = np.zeros(self.shape, dtype=bool)

    def point_to_index(self, xyz: np.ndarray | tuple[float, float, float]) -> tuple[int, int, int] | None:
        p = np.asarray(xyz, dtype=np.float32)
        xyz_idx = np.floor((p - self.origin) / self.voxel_size).astype(np.int32)
        ix, iy, iz = int(xyz_idx[0]), int(xyz_idx[1]), int(xyz_idx[2])
        d, h, w = self.shape
        if 0 <= ix < w and 0 <= iy < h and 0 <= iz < d:
            return iz, iy, ix
        return None

    def mark_free(self, xyz: np.ndarray) -> None:
        idx = self.point_to_index(xyz)
        if idx is not None:
            self.free[idx] = True

    def mark_occupied(self, xyz: np.ndarray) -> None:
        idx = self.point_to_index(xyz)
        if idx is not None:
            self.occupied[idx] = True

    def integrate_points(self, eye: tuple[float, float, float], world_points: np.ndarray, max_points: int = 1800) -> int:
        pts = np.asarray(world_points, dtype=np.float32).reshape(-1, 3)
        finite = np.isfinite(pts).all(axis=1)
        pts = pts[finite]
        if pts.shape[0] > max_points:
            pts = pts[:: max(1, int(math.ceil(pts.shape[0] / max_points)))]
        eye_arr = np.asarray(eye, dtype=np.float32)
        used = 0
        for point in pts:
            if self.point_to_index(point) is None:
                continue
            vec = point - eye_arr
            dist = float(np.linalg.norm(vec))
            if not math.isfinite(dist) or dist < 0.05:
                continue
            steps = max(1, int(dist / (self.voxel_size * 0.5)))
            for step in range(max(1, steps - 2)):
                t = step / max(1, steps)
                self.mark_free(eye_arr + vec * t)
            self.mark_occupied(point)
            used += 1
        return used

    def finalize(self) -> dict[str, np.ndarray]:
        free = self.free & ~self.occupied
        occupied = self.occupied
        observed = free | occupied
        unknown = ~observed
        return {
            "occupancy": occupied.astype(np.uint8),
            "free_mask": free.astype(np.uint8),
            "occupied_mask": occupied.astype(np.uint8),
            "observed_mask": observed.astype(np.uint8),
            "unknown_mask": unknown.astype(np.uint8),
        }


def save_scene_plots(scene_id: str, arrays: dict[str, np.ndarray], poses: list[dict[str, Any]], plots_dir: Path) -> list[str]:
    paths: list[str] = []
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return paths

    scene_dir = plots_dir / scene_id
    scene_dir.mkdir(parents=True, exist_ok=True)
    plot_specs = [
        ("bev_occupancy_dense_scan.png", arrays["occupied_mask"].max(axis=0), "BEV occupied pseudo GT"),
        ("bev_free_dense_scan.png", arrays["free_mask"].max(axis=0), "BEV observed free"),
        ("bev_unknown_dense_scan.png", arrays["unknown_mask"].mean(axis=0), "BEV unknown ratio"),
    ]
    for name, data, title in plot_specs:
        path = scene_dir / name
        plt.figure(figsize=(5, 5))
        plt.imshow(data, origin="lower", cmap="magma")
        plt.title(title)
        plt.tight_layout()
        plt.savefig(path, dpi=120)
        plt.close()
        paths.append(str(path))

    occ = arrays["occupied_mask"]
    z_indices = sorted({0, occ.shape[0] // 3, (2 * occ.shape[0]) // 3, occ.shape[0] - 1})
    fig, axes = plt.subplots(1, len(z_indices), figsize=(4 * len(z_indices), 4))
    if len(z_indices) == 1:
        axes = [axes]
    for ax, z in zip(axes, z_indices):
        ax.imshow(occ[z], origin="lower", cmap="gray_r")
        ax.set_title(f"z slice {z}")
        ax.axis("off")
    z_path = scene_dir / "z_slice_occupancy_examples.png"
    fig.tight_layout()
    fig.savefig(z_path, dpi=120)
    plt.close(fig)
    paths.append(str(z_path))

    pose_path = scene_dir / "dense_scan_camera_poses_topdown.png"
    plt.figure(figsize=(5, 5))
    xs = [p["eye"][0] for p in poses]
    ys = [p["eye"][1] for p in poses]
    dx = [math.cos(p["yaw"]) * 0.35 for p in poses]
    dy = [math.sin(p["yaw"]) * 0.35 for p in poses]
    plt.quiver(xs, ys, dx, dy, angles="xy", scale_units="xy", scale=1.0)
    plt.scatter(xs, ys, s=10)
    plt.axis("equal")
    plt.title("Dense scan camera poses")
    plt.tight_layout()
    plt.savefig(pose_path, dpi=120)
    plt.close()
    paths.append(str(pose_path))
    return paths


def scene_quality(arrays: dict[str, np.ndarray], grid_meta: dict[str, Any]) -> dict[str, Any]:
    occ = arrays["occupied_mask"].astype(bool)
    free = arrays["free_mask"].astype(bool)
    observed = arrays["observed_mask"].astype(bool)
    unknown = arrays["unknown_mask"].astype(bool)
    total = int(occ.size)
    occupied_count = int(np.count_nonzero(occ))
    free_count = int(np.count_nonzero(free))
    observed_count = int(np.count_nonzero(observed))
    unknown_count = int(np.count_nonzero(unknown))
    overlap = int(np.count_nonzero(occ & free))
    observed_unknown_overlap = int(np.count_nonzero(observed & unknown))
    quality_pass = (
        occupied_count > 0
        and free_count > 0
        and observed_count > 0
        and total > 0
        and occupied_count < total
        and free_count < total
        and observed_unknown_overlap == 0
        and overlap <= max(1, int(0.01 * total))
        and grid_meta["voxel_size"] > 0.0
        and total <= MAX_VOXELS_DEFAULT
    )
    return {
        "grid_shape": [int(v) for v in arrays["occupancy"].shape],
        "voxel_size": float(grid_meta["voxel_size"]),
        "occupied_count": occupied_count,
        "free_count": free_count,
        "observed_count": observed_count,
        "unknown_count": unknown_count,
        "occupied_ratio": round(occupied_count / total if total else 0.0, 6),
        "free_ratio": round(free_count / total if total else 0.0, 6),
        "observed_ratio": round(observed_count / total if total else 0.0, 6),
        "occupied_free_overlap_count": overlap,
        "observed_unknown_overlap_count": observed_unknown_overlap,
        "quality_pass": bool(quality_pass),
    }


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# MapPredict Phase 1 Full Occupancy GT Report",
        "",
        "phase: MapPredict Phase 1",
        "purpose: generate full occupancy GT prototype for SceneSense-style map_predict",
        f"workspace: {summary.get('workspace')}",
        f"project_name: {summary.get('project_name')}",
        f"main_goal: {summary.get('main_goal')}",
        "map_predict_role: feature_provider",
        "planner: false",
        "VLA: false",
        "training_started: false",
        "map_predict_training_started: false",
        "SFT_started: false",
        "GDPO_started: false",
        "RL_started: false",
        "rollout_started: false",
        "",
        "## Route Status",
        "",
        f"route_a_dense_scan_status: {summary.get('route_a_dense_scan_status')}",
        f"route_b_usd_voxelization_status: {summary.get('route_b_usd_voxelization_status')}",
        f"full_occupancy_gt_type: {summary.get('full_occupancy_gt_type')}",
        f"safe_to_build_local_voxel_dataset: {bool_text(summary.get('safe_to_build_local_voxel_dataset'))}",
        "next_phase: MapPredict Phase 2 local voxel crop dataset generation",
        "",
        "## Scenes Processed",
        "",
    ]
    for scene in summary.get("scenes", []):
        lines.extend(
            [
                f"### {scene.get('scene_id')}",
                "",
                f"scene_path: {scene.get('scene_path')}",
                f"dense_scan_status: {scene.get('dense_scan_status')}",
                f"usd_voxelization_status: {scene.get('usd_voxelization_status')}",
                f"gt_path: {scene.get('gt_path')}",
                f"usd_voxel_gt_path: {scene.get('usd_voxel_gt_path')}",
                f"voxel_size: {scene.get('voxel_size')}",
                f"grid_shape: {scene.get('grid_shape')}",
                f"occupied_count: {scene.get('occupied_count')}",
                f"free_count: {scene.get('free_count')}",
                f"observed_count: {scene.get('observed_count')}",
                f"unknown_count: {scene.get('unknown_count')}",
                f"occupied_ratio: {scene.get('occupied_ratio')}",
                f"free_ratio: {scene.get('free_ratio')}",
                f"observed_ratio: {scene.get('observed_ratio')}",
                f"quality_pass: {bool_text(scene.get('quality_pass'))}",
                f"failure_reason: {scene.get('failure_reason')}",
                f"plot_paths: {scene.get('plot_paths')}",
                "",
            ]
        )
    lines.extend(
        [
            "## SceneSense GitHub Alignment",
            "",
            "* Reviewed repository: https://github.com/arpg/SceneSense",
            "* Reviewed project page: https://arpg.github.io/scenesense/",
            "* SceneSense uses local occupancy/pointmap-style representations from partial observations.",
            "* SceneSense-style inference must preserve observed geometry: observed free and occupied voxels are not overwritten.",
            "* Frontier handling is a site for selecting or enriching prediction crops, not an action output interface.",
            "* This VLA map_predict implementation keeps the same role boundary: feature provider only.",
            "",
            "## Quality Checks",
            "",
            "* occupied_count > 0",
            "* free_count > 0",
            "* observed_count > 0",
            "* grid_shape below max_voxels",
            "* occupancy is not all zero or all one",
            "* observed_mask and unknown_mask are mutually exclusive",
            "* occupied_mask and free_mask are de-overlapped before saving",
            "* BEV and z-slice visualizations are generated under the run directory",
            "",
            "## Limitations",
            "",
            "* Dense scan GT is `dense_scan_pseudo_gt`, not final perfect mesh GT.",
            "* Unknown regions can remain unknown if not observed by the scan poses.",
            "* Route B USD voxelization is a bbox-style prototype unless a later phase implements exact mesh voxelization.",
            "* The generated `.npz` files are kept out of Git by default.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def process_scene(scene: SceneSpec, args: argparse.Namespace, app, rep, omni_usd) -> dict[str, Any]:
    record: dict[str, Any] = {
        "scene_id": scene.scene_id,
        "scene_path": str(scene.scene_path),
        "dense_scan_status": "failed",
        "usd_voxelization_status": "skipped",
        "gt_path": None,
        "usd_voxel_gt_path": None,
        "voxel_size": None,
        "grid_shape": None,
        "occupied_count": 0,
        "free_count": 0,
        "observed_count": 0,
        "unknown_count": 0,
        "occupied_ratio": 0.0,
        "free_ratio": 0.0,
        "observed_ratio": 0.0,
        "quality_pass": False,
        "failure_reason": None,
        "plot_paths": [],
    }
    if not scene.scene_path.exists():
        record["dense_scan_status"] = "skipped"
        record["failure_reason"] = "scene_missing"
        return record

    try:
        context = omni_usd.get_context()
        context.open_stage(str(scene.scene_path))
        stage = None
        deadline = time.time() + float(args.open_timeout_sec)
        while time.time() < deadline:
            app.update()
            stage = context.get_stage()
            if stage is not None and list(stage.Traverse()):
                break
            time.sleep(0.1)
        if stage is None:
            raise RuntimeError("Stage unavailable after open_stage")

        create_runtime_prims(stage, int(args.width), int(args.height))
        camera_prim = stage.GetPrimAtPath(CAMERA_PATH)
        light_prim = stage.GetPrimAtPath(LIGHT_PATH)
        if not camera_prim or not camera_prim.IsValid():
            raise RuntimeError("Runtime camera was not created")

        render_product = rep.create.render_product(CAMERA_PATH, (int(args.width), int(args.height)))
        annotators, annotator_errors = attach_camera_annotators(rep, render_product)
        required = {"distance_to_image_plane", "camera_params"}
        if not required.issubset(annotators):
            raise RuntimeError(f"Required annotators unavailable: {annotator_errors}")
        try:
            rep.orchestrator.set_capture_on_play(False)
        except Exception:
            pass

        bounds = estimate_bounds_from_quality(scene)
        grid_meta = grid_from_bounds(bounds, float(args.voxel_size), int(args.max_voxels))
        grid = DenseOccupancyGrid(grid_meta)
        scan_poses = generate_scan_poses(bounds, int(args.views))
        valid_views = 0
        point_count_total = 0

        for view_id, pose in enumerate(scan_poses):
            eye = pose["eye"]
            target = pose["target"]
            set_world_look_at(camera_prim, eye, target)
            if light_prim and light_prim.IsValid():
                set_world_translate(light_prim, (eye[0], eye[1], eye[2] + 1.5))
            for _ in range(2):
                app.update()
            for _ in range(3):
                app.update()
                try:
                    rep.orchestrator.step()
                except Exception:
                    pass
                app.update()

            depth = depth_stats(annotators["distance_to_image_plane"].get_data())
            camera_params_data = annotators["camera_params"].get_data()
            intr_ok, intrinsics = intrinsics_from_camera_params(
                camera_params_data,
                depth["width"] or int(args.width),
                depth["height"] or int(args.height),
            )
            if not depth["available"] or not intr_ok:
                continue
            cam_points = pointcloud_from_depth(depth["array"], intrinsics, stride=int(args.depth_stride))
            world_points = camera_points_to_world(cam_points, eye, target)
            used = grid.integrate_points(eye, world_points, max_points=int(args.max_points_per_view))
            if used > 0:
                valid_views += 1
                point_count_total += used

        arrays = grid.finalize()
        quality = scene_quality(arrays, grid_meta)
        output_dir = DATA_ROOT / scene.scene_id
        output_dir.mkdir(parents=True, exist_ok=True)
        gt_path = output_dir / "full_occupancy_dense_scan.npz"
        np.savez_compressed(
            gt_path,
            occupancy=arrays["occupancy"],
            free_mask=arrays["free_mask"],
            occupied_mask=arrays["occupied_mask"],
            observed_mask=arrays["observed_mask"],
            unknown_mask=arrays["unknown_mask"],
            voxel_size=np.asarray(grid_meta["voxel_size"], dtype=np.float32),
            origin_xyz=np.asarray(grid_meta["origin_xyz"], dtype=np.float32),
            grid_shape=np.asarray(grid_meta["grid_shape"], dtype=np.int32),
            world_to_grid=np.asarray(grid_meta["world_to_grid"], dtype=np.float32),
            scene_id=np.asarray(scene.scene_id),
            scene_path=np.asarray(str(scene.scene_path)),
            gt_type=np.asarray("dense_scan_pseudo_gt"),
        )
        plot_paths = save_scene_plots(scene.scene_id, arrays, scan_poses, Path(args.run_dir) / "plots")
        record.update(quality)
        record.update(
            {
                "dense_scan_status": "success" if quality["quality_pass"] else "failed",
                "gt_path": str(gt_path),
                "voxel_size": grid_meta["voxel_size"],
                "origin_xyz": grid_meta["origin_xyz"],
                "world_to_grid": np.asarray(grid_meta["world_to_grid"]).round(6).tolist(),
                "bounds": bounds,
                "bounds_source": bounds.get("source"),
                "scan_pose_count": len(scan_poses),
                "valid_scan_view_count": valid_views,
                "integrated_point_count": int(point_count_total),
                "full_occupancy_gt_type": "dense_scan_pseudo_gt",
                "plot_paths": plot_paths,
                "failure_reason": None if quality["quality_pass"] else "quality_checks_failed",
            }
        )
        return record
    except Exception as exc:
        record["failure_reason"] = repr(exc)
        record["traceback"] = traceback.format_exc()
        return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--views", type=int, default=36)
    parser.add_argument("--width", type=int, default=160)
    parser.add_argument("--height", type=int, default=120)
    parser.add_argument("--voxel-size", type=float, default=VOXEL_SIZE_DEFAULT)
    parser.add_argument("--depth-stride", type=int, default=8)
    parser.add_argument("--max-points-per-view", type=int, default=1800)
    parser.add_argument("--max-voxels", type=int, default=MAX_VOXELS_DEFAULT)
    parser.add_argument("--open-timeout-sec", type=float, default=180.0)
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.run_dir) if args.run_dir else RUNS_DIR / f"map_predict_phase1_full_occupancy_gt_{timestamp}"
    args.run_dir = str(run_dir)
    for rel in ["logs", "gt", "dense_scan", "voxelization", "reports", "summary", "plots", "debug"]:
        (run_dir / rel).mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "phase": PHASE,
        "workspace": str(WORKSPACE),
        "project_name": PROJECT,
        "main_goal": GOAL,
        "map_predict_role": "feature_provider",
        "planner": False,
        "VLA": False,
        "training_started": False,
        "map_predict_training_started": False,
        "SFT_started": False,
        "GDPO_started": False,
        "RL_started": False,
        "rollout_started": False,
        "checkpoint_created": False,
        "source_vla_data_modified": False,
        "full_occupancy_gt_type": "dense_scan_pseudo_gt",
        "route_a_dense_scan_status": "failed",
        "route_b_usd_voxelization_status": "skipped",
        "voxel_size_requested": float(args.voxel_size),
        "max_voxels": int(args.max_voxels),
        "run_dir": str(run_dir),
        "scenes": [],
        "safe_to_build_local_voxel_dataset": False,
        "next_phase": "Fix MapPredict Phase 1 full occupancy GT generation",
    }

    app = None
    try:
        from isaacsim import SimulationApp

        app = SimulationApp({"headless": True})
        import omni.replicator.core as rep
        import omni.usd

        for scene in SCENES:
            scene_record = process_scene(scene, args, app, rep, omni.usd)
            summary["scenes"].append(scene_record)
        success_count = sum(1 for scene in summary["scenes"] if scene.get("dense_scan_status") == "success")
        summary["route_a_dense_scan_status"] = "success" if success_count == len(SCENES) else "partial_success" if success_count else "failed"
        summary["safe_to_build_local_voxel_dataset"] = bool(success_count > 0 and all(s.get("quality_pass") for s in summary["scenes"] if s.get("dense_scan_status") == "success"))
        if summary["safe_to_build_local_voxel_dataset"]:
            summary["next_phase"] = "MapPredict Phase 2 local voxel crop dataset generation"
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
    finally:
        summary_path = run_dir / "summary/full_occupancy_gt_summary.json"
        report_path = RUNS_DIR / "MAP_PREDICT_PHASE1_FULL_OCCUPANCY_GT_REPORT.md"
        run_report_path = run_dir / "reports/MAP_PREDICT_PHASE1_FULL_OCCUPANCY_GT_REPORT.md"
        write_summary(summary_path, summary)
        write_report(report_path, summary)
        write_report(run_report_path, summary)
        if app is not None:
            app.close()

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("safe_to_build_local_voxel_dataset") else 2


if __name__ == "__main__":
    raise SystemExit(main())
