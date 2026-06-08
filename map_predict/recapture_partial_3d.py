#!/usr/bin/env python3
"""MapPredict Phase 2.5 real partial 3D occupancy recapture.

This script opens the repaired USD scenes read-only, places the existing A1
robot prim at deterministic capture poses, captures real Isaac/Omniverse RGB-D,
backprojects depth to world points, and builds compact local voxel samples by
3D ray carving. It does not train, run VLA rollout, modify USD, or save raw
RGB-D / pointcloud dumps.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
import time
import traceback
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


WORKSPACE = Path("/home/ubuntu22/VLA")
RUNS_DIR = WORKSPACE / "runs"
DATA_ROOT = WORKSPACE / "data/map_predict/local_voxel_dataset"
SCRIPT_DIR = WORKSPACE / "scripts"
GT_TYPE = "dense_scan_pseudo_gt"
PARTIAL_SOURCE = "real_depth_backprojection_raycast"
PHASE = "MapPredict Phase 2.5 real partial 3D occupancy recapture"
PROJECT = "A1-VLM-LA Explorer"
GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"
FRONTIER_CONNECTIVITY = 6
TOP_REPORT = RUNS_DIR / "MAP_PREDICT_PHASE25_REAL_PARTIAL_3D_RECAPTURE_REPORT.md"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from phase4r_a1_real_sensor_mapping_smoke import camera_points_to_world  # noqa: E402
from phase56_a1_real_sensor_suite_smoke import (  # noqa: E402
    A1_ROOT,
    BASE_FRAME,
    CAMERA_PATH,
    LIGHT_PATH,
    attach_camera_annotators,
    create_runtime_prims,
    depth_stats,
    expected_sensor_pose,
    intrinsics_from_camera_params,
    pointcloud_from_depth,
    rgb_stats,
    set_root_pose,
    set_world_look_at,
    set_world_translate,
    world_translation,
)

try:
    from .crop import crop_3d_from_origin, crop_origin_from_center, grid_centers_xyz
    from .dataset import local_voxel_dataset_manifest
    from .metrics import count_distribution, observed_gt_conflict_ratio, overlap_count, zero_rate
    from .voxelize import VoxelGridSpec, frontier_from_free_unknown, raycast_points_to_occupancy, unknown_from_observed
except ImportError:
    from crop import crop_3d_from_origin, crop_origin_from_center, grid_centers_xyz
    from dataset import local_voxel_dataset_manifest
    from metrics import count_distribution, observed_gt_conflict_ratio, overlap_count, zero_rate
    from voxelize import VoxelGridSpec, frontier_from_free_unknown, raycast_points_to_occupancy, unknown_from_observed


@dataclass(frozen=True)
class SceneSpec:
    scene_id: str
    scene_path: Path
    gt_path: Path


@dataclass(frozen=True)
class DatasetConfig:
    dataset_version: str
    dims: tuple[int, int, int]
    max_points_per_sample: int


@dataclass
class CaptureFrame:
    eye: tuple[float, float, float]
    target: tuple[float, float, float]
    world_points: np.ndarray
    rgb_available: bool
    depth_available: bool
    depth_valid_ratio: float
    intrinsics: dict[str, float]
    camera_pose: np.ndarray


SCENES = [
    SceneSpec(
        scene_id="old_home_like_scene_v1",
        scene_path=WORKSPACE / "scenes/primary_building_scene_repaired/home_like_scene_v1.usd",
        gt_path=WORKSPACE / "data/map_predict/full_occupancy_gt/old_home_like_scene_v1/full_occupancy_dense_scan.npz",
    ),
    SceneSpec(
        scene_id="new_building_scene_1",
        scene_path=WORKSPACE / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda",
        gt_path=WORKSPACE / "data/map_predict/full_occupancy_gt/new_building_scene_1/full_occupancy_dense_scan.npz",
    ),
]

DATASETS = [
    DatasetConfig("local_voxel_v1_real_partial_3d", (24, 64, 64), 2600),
    DatasetConfig("local_voxel_smoke_v1_real_partial_3d", (16, 32, 32), 1600),
]


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def rate(num: int | float, den: int | float) -> float:
    return round(float(num) / float(den), 6) if den else 0.0


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_gt(path: Path) -> dict[str, Any]:
    z = np.load(path, allow_pickle=True)
    return {
        "full_occupancy": z["occupancy"].astype(np.uint8),
        "voxel_size": float(z["voxel_size"]),
        "origin_xyz": tuple(float(x) for x in z["origin_xyz"]),
        "scene_id": str(z["scene_id"].item()),
        "scene_path": str(z["scene_path"].item()),
        "gt_type": str(z["gt_type"].item()),
    }


def start_pose_plan(base_xyz: tuple[float, float, float], start_count: int) -> list[dict[str, float | int]]:
    offsets = [
        (0.0, 0.0, 0.0),
        (0.45, 0.0, 0.25),
        (-0.45, 0.0, -0.25),
        (0.0, 0.45, 0.5),
        (0.0, -0.45, -0.5),
    ]
    while len(offsets) < start_count:
        idx = len(offsets)
        angle = idx * 1.618
        radius = 0.35 + 0.05 * idx
        offsets.append((math.cos(angle) * radius, math.sin(angle) * radius, angle))
    starts = []
    for start_id, (dx, dy, yaw) in enumerate(offsets[:start_count]):
        starts.append({
            "start_id": start_id,
            "x": float(base_xyz[0] + dx),
            "y": float(base_xyz[1] + dy),
            "z": float(base_xyz[2]),
            "yaw": float(yaw),
        })
    return starts


def pose_for_step(start: dict[str, float | int], step_id: int) -> tuple[float, float, float, float]:
    yaw0 = float(start["yaw"])
    forward = 0.16 * step_id
    lateral = 0.10 * math.sin(step_id * 0.75 + int(start["start_id"]) * 0.4)
    yaw = yaw0 + 0.22 * step_id
    x = float(start["x"]) + math.cos(yaw0) * forward - math.sin(yaw0) * lateral
    y = float(start["y"]) + math.sin(yaw0) * forward + math.cos(yaw0) * lateral
    return x, y, float(start["z"]), yaw


def quat_from_yaw_pitch(yaw: float, pitch: float) -> np.ndarray:
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    qw = cy * cp
    qx = -sy * sp
    qy = cy * sp
    qz = sy * cp
    return np.asarray([qx, qy, qz, qw], dtype=np.float32)


def camera_pose_from_eye_target(
    eye: tuple[float, float, float],
    target: tuple[float, float, float],
) -> np.ndarray:
    dx = float(target[0] - eye[0])
    dy = float(target[1] - eye[1])
    dz = float(target[2] - eye[2])
    yaw = math.atan2(dy, dx)
    horiz = max(1e-6, math.hypot(dx, dy))
    pitch = math.atan2(dz, horiz)
    quat = quat_from_yaw_pitch(yaw, pitch)
    return np.concatenate([np.asarray(eye, dtype=np.float32), quat]).astype(np.float32)


def intrinsics_matrix(intrinsics: dict[str, float]) -> np.ndarray:
    return np.asarray(
        [
            [float(intrinsics["fx"]), 0.0, float(intrinsics["cx"])],
            [0.0, float(intrinsics["fy"]), float(intrinsics["cy"])],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )


def robot_gaussian_and_height(
    dims: tuple[int, int, int],
    voxel_size: float,
    crop_origin_xyz: tuple[float, float, float],
    robot_pose: tuple[float, float, float, float],
) -> tuple[np.ndarray, np.ndarray]:
    xx, yy, zz = grid_centers_xyz(dims, crop_origin_xyz, voxel_size)
    sigma_xy = 0.45
    sigma_z = 0.35
    gaussian = np.exp(
        -(((xx - robot_pose[0]) ** 2 + (yy - robot_pose[1]) ** 2) / (2 * sigma_xy**2))
        - (((zz - robot_pose[2]) ** 2) / (2 * sigma_z**2))
    ).astype(np.float32)
    z_min = crop_origin_xyz[2]
    z_extent = max(1e-6, dims[0] * voxel_size)
    height = ((zz - z_min) / z_extent).astype(np.float32)
    return gaussian, height.astype(np.float32)


def filter_world_points(points: np.ndarray) -> np.ndarray:
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 3)
    if pts.size == 0:
        return pts
    finite = np.isfinite(pts).all(axis=1)
    pts = pts[finite]
    if pts.size == 0:
        return pts
    # Remove likely floor/ceiling outliers while preserving object and wall hits.
    mask = (pts[:, 2] > 0.08) & (pts[:, 2] < 2.8)
    return pts[mask].astype(np.float32)


def build_partial_from_history(
    frames: list[CaptureFrame],
    dims: tuple[int, int, int],
    voxel_size: float,
    crop_origin_xyz: tuple[float, float, float],
    max_points_per_sample: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, int]]:
    observed_free = np.zeros(dims, dtype=bool)
    observed_occupied = np.zeros(dims, dtype=bool)
    aggregate = Counter()
    if not frames:
        unknown = unknown_from_observed(observed_free, observed_occupied)
        return observed_free.astype(np.uint8), observed_occupied.astype(np.uint8), unknown.astype(np.uint8), dict(aggregate)

    per_frame_limit = max(200, int(max_points_per_sample / max(1, len(frames))))
    spec = VoxelGridSpec(dims=dims, voxel_size=voxel_size, origin=crop_origin_xyz)
    for frame in frames:
        free, occupied, stats = raycast_points_to_occupancy(
            frame.eye,
            frame.world_points,
            spec,
            max_points=per_frame_limit,
            ray_step_fraction=0.5,
            min_range=0.05,
            max_range=15.0,
        )
        observed_free |= free
        observed_occupied |= occupied
        aggregate.update(stats)

    observed_free &= ~observed_occupied
    unknown = unknown_from_observed(observed_free, observed_occupied)
    return observed_free.astype(np.uint8), observed_occupied.astype(np.uint8), unknown.astype(np.uint8), dict(aggregate)


def evaluate_quality(
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
    unknown_mask: np.ndarray,
    frontier_mask: np.ndarray,
    full_occupancy: np.ndarray,
    valid_mask: np.ndarray,
) -> tuple[str, list[str], dict[str, float | int]]:
    flags: list[str] = []
    status = "pass"
    stats: dict[str, float | int] = {}
    expected_shape = full_occupancy.shape

    for name, arr in [
        ("observed_free", observed_free),
        ("observed_occupied", observed_occupied),
        ("unknown_mask", unknown_mask),
        ("frontier_mask", frontier_mask),
    ]:
        if arr.shape != expected_shape:
            flags.append(f"{name}_shape_wrong")
            status = "reject"

    free_occ_overlap = overlap_count(observed_free, observed_occupied)
    conflict = observed_gt_conflict_ratio(observed_occupied, full_occupancy)
    stats["gt_observed_conflict_ratio"] = float(conflict)
    stats["observed_free_overlaps_occupied"] = int(free_occ_overlap)

    if unknown_mask.sum() == 0:
        flags.append("unknown_mask_all_zero")
        status = "reject"
    if observed_free.sum() + observed_occupied.sum() == 0:
        flags.append("observed_free_and_occupied_all_zero")
        status = "reject"
    if full_occupancy.shape != expected_shape or valid_mask.sum() == 0:
        flags.append("full_occupancy_missing_or_invalid_crop")
        status = "reject"
    if free_occ_overlap > 0:
        flags.append("observed_free_overlaps_observed_occupied")
        status = "reject"
    if observed_occupied.sum() > 0 and conflict > 0.2:
        flags.append("severe_gt_observed_conflict_ratio")
        status = "reject"

    if frontier_mask.sum() == 0:
        flags.append("frontier_mask_all_zero")
        if status != "reject":
            status = "warning"
    if observed_occupied.sum() == 0:
        flags.append("observed_occupied_count_zero")
        if status != "reject":
            status = "warning"
    if full_occupancy.sum() == 0:
        flags.append("full_occupancy_occupied_count_zero")
        if status != "reject":
            status = "warning"
    if observed_free.sum() < 64:
        flags.append("low_observed_free_count")
        if status != "reject":
            status = "warning"

    return status, flags, stats


def save_sample(
    path: Path,
    *,
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
    unknown_mask: np.ndarray,
    frontier_mask: np.ndarray,
    robot_gaussian: np.ndarray,
    height_channel: np.ndarray,
    robot_pose: tuple[float, float, float, float],
    camera_pose: np.ndarray,
    camera_intrinsics: np.ndarray,
    full_occupancy: np.ndarray,
    valid_mask: np.ndarray,
    voxel_size: float,
    crop_origin_xyz: tuple[float, float, float],
    crop_center_xyz: tuple[float, float, float],
    scene: SceneSpec,
    start_id: int,
    step_id: int,
    sample_id: str,
    quality_status: str,
    quality_flags: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        observed_free=observed_free.astype(np.uint8),
        observed_occupied=observed_occupied.astype(np.uint8),
        unknown_mask=unknown_mask.astype(np.uint8),
        frontier_mask=frontier_mask.astype(np.uint8),
        robot_position_gaussian=robot_gaussian.astype(np.float32),
        height_channel=height_channel.astype(np.float32),
        robot_pose=np.asarray(robot_pose, dtype=np.float32),
        camera_pose=np.asarray(camera_pose, dtype=np.float32),
        camera_intrinsics=np.asarray(camera_intrinsics, dtype=np.float32),
        full_occupancy=full_occupancy.astype(np.uint8),
        valid_mask=valid_mask.astype(np.uint8),
        voxel_size=np.asarray(voxel_size, dtype=np.float32),
        crop_origin_xyz=np.asarray(crop_origin_xyz, dtype=np.float32),
        crop_center_xyz=np.asarray(crop_center_xyz, dtype=np.float32),
        scene_id=np.asarray(scene.scene_id),
        scene_path=np.asarray(str(scene.scene_path)),
        episode_id=np.asarray(start_id, dtype=np.int32),
        start_id=np.asarray(start_id, dtype=np.int32),
        step_id=np.asarray(step_id, dtype=np.int32),
        sample_id=np.asarray(sample_id),
        gt_type=np.asarray(GT_TYPE),
        partial_3d_source=np.asarray(PARTIAL_SOURCE),
        quality_status=np.asarray(quality_status),
        quality_flags=np.asarray(json.dumps(quality_flags, sort_keys=True)),
    )


def split_samples(records: list[dict[str, Any]]) -> tuple[dict[str, list[str]], dict[str, Any]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for rec in records:
        groups[f"{rec['scene_id']}::start_{rec['start_id']:03d}"].append(rec["relative_path"])
    keys = sorted(groups)
    split_keys = {"train": [], "val": [], "test": []}
    for idx, key in enumerate(keys):
        bucket = idx % 10
        if bucket < 7:
            split_keys["train"].append(key)
        elif bucket < 9:
            split_keys["val"].append(key)
        else:
            split_keys["test"].append(key)
    splits: dict[str, list[str]] = {}
    for split, group_keys in split_keys.items():
        paths: list[str] = []
        for key in group_keys:
            paths.extend(groups[key])
        splits[split] = sorted(paths)
    summary = {
        "split_method": "deterministic_scene_id_start_id_group_modulo",
        "train_group_count": len(split_keys["train"]),
        "val_group_count": len(split_keys["val"]),
        "test_group_count": len(split_keys["test"]),
        "train_count": len(splits["train"]),
        "val_count": len(splits["val"]),
        "test_count": len(splits["test"]),
        "group_overlap": False,
    }
    return splits, summary


def write_splits(dataset_root: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    splits, summary = split_samples(records)
    split_dir = dataset_root / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)
    for split, paths in splits.items():
        (split_dir / f"{split}.txt").write_text("\n".join(paths) + ("\n" if paths else ""), encoding="utf-8")
    write_json(split_dir / "split_summary.json", summary)
    return summary


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(r["quality_status"] for r in records)
    flags = Counter(flag for r in records for flag in r["quality_flags"])
    observed_occ = [int(r["observed_occupied_count"]) for r in records]
    frontier = [int(r["frontier_count"]) for r in records]
    return {
        "sample_count": len(records),
        "pass_count": status_counts.get("pass", 0),
        "warning_count": status_counts.get("warning", 0),
        "reject_count": status_counts.get("reject", 0),
        "quality_flag_counts": dict(sorted(flags.items())),
        "observed_free_count": count_distribution(r["observed_free_count"] for r in records),
        "observed_occupied_count": count_distribution(observed_occ),
        "unknown_count": count_distribution(r["unknown_count"] for r in records),
        "frontier_count": count_distribution(frontier),
        "full_occupancy_occupied_count": count_distribution(r["full_occupancy_occupied_count"] for r in records),
        "gt_observed_conflict_ratio": count_distribution(r["gt_observed_conflict_ratio"] for r in records),
        "observed_occupied_zero_rate": round(zero_rate(observed_occ), 6),
        "frontier_empty_rate": round(zero_rate(frontier), 6),
        "empty_crop_count": sum(1 for r in records if r["observed_free_count"] + r["observed_occupied_count"] == 0),
        "unknown_empty_count": sum(1 for r in records if r["unknown_count"] == 0),
    }


def save_sample_plots(dataset_root: Path, run_dir: Path, scene_id: str, records: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    if not records:
        return paths
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return paths

    first = next((r for r in records if r["scene_id"] == scene_id), None)
    if not first:
        return paths
    sample_path = dataset_root / first["relative_path"]
    if not sample_path.exists():
        return paths
    z = np.load(sample_path, allow_pickle=True)
    scene_plot_dir = run_dir / "plots" / scene_id
    scene_plot_dir.mkdir(parents=True, exist_ok=True)
    specs = [
        ("sample_bev_observed_free.png", z["observed_free"].max(axis=0), "observed free"),
        ("sample_bev_observed_occupied.png", z["observed_occupied"].max(axis=0), "observed occupied"),
        ("sample_bev_unknown.png", z["unknown_mask"].mean(axis=0), "unknown"),
        ("sample_bev_frontier.png", z["frontier_mask"].max(axis=0), "frontier"),
        ("sample_bev_full_occupancy.png", z["full_occupancy"].max(axis=0), "full occupancy label"),
    ]
    for name, arr, title in specs:
        path = scene_plot_dir / name
        plt.figure(figsize=(5, 5))
        plt.imshow(arr, origin="lower", cmap="magma")
        plt.title(title)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(path, dpi=120)
        plt.close()
        paths.append(str(path))
    occ = z["observed_occupied"]
    full = z["full_occupancy"]
    z_indices = sorted({0, occ.shape[0] // 3, (2 * occ.shape[0]) // 3, occ.shape[0] - 1})
    fig, axes = plt.subplots(2, len(z_indices), figsize=(4 * len(z_indices), 7))
    if len(z_indices) == 1:
        axes = np.asarray(axes).reshape(2, 1)
    for idx, zidx in enumerate(z_indices):
        axes[0, idx].imshow(occ[zidx], origin="lower", cmap="gray_r")
        axes[0, idx].set_title(f"obs occ z={zidx}")
        axes[0, idx].axis("off")
        axes[1, idx].imshow(full[zidx], origin="lower", cmap="gray_r")
        axes[1, idx].set_title(f"label z={zidx}")
        axes[1, idx].axis("off")
    z_path = scene_plot_dir / "sample_z_slices.png"
    fig.tight_layout()
    fig.savefig(z_path, dpi=120)
    plt.close(fig)
    paths.append(str(z_path))
    return paths


def clear_dataset_root(dataset_root: Path) -> None:
    if DATA_ROOT not in dataset_root.parents:
        raise ValueError(f"Refusing to clear unexpected dataset path: {dataset_root}")
    if dataset_root.exists():
        shutil.rmtree(dataset_root)
    dataset_root.mkdir(parents=True, exist_ok=True)


def process_scene(
    scene: SceneSpec,
    args: argparse.Namespace,
    app,
    rep,
    omni_usd,
    dataset_records: dict[str, list[dict[str, Any]]],
    global_ids: dict[str, int],
) -> dict[str, Any]:
    scene_summary: dict[str, Any] = {
        "scene_id": scene.scene_id,
        "scene_path": str(scene.scene_path),
        "status": "failed",
        "route_used": "recapture",
        "capture_step_count": 0,
        "valid_depth_capture_count": 0,
        "valid_rgb_capture_count": 0,
        "world_point_count_total": 0,
        "failure_reason": None,
        "datasets": {},
    }
    if not scene.scene_path.exists():
        scene_summary["status"] = "skipped"
        scene_summary["failure_reason"] = "scene_missing"
        return scene_summary
    if not scene.gt_path.exists():
        scene_summary["status"] = "skipped"
        scene_summary["failure_reason"] = "dense_scan_pseudo_gt_missing"
        return scene_summary

    gt = load_gt(scene.gt_path)
    voxel_size = float(gt["voxel_size"])
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
        scene_summary["failure_reason"] = "stage_unavailable_after_open"
        return scene_summary

    root_prim = stage.GetPrimAtPath(A1_ROOT)
    base_prim = stage.GetPrimAtPath(BASE_FRAME)
    if not root_prim or not root_prim.IsValid() or not base_prim or not base_prim.IsValid():
        scene_summary["failure_reason"] = "a1_root_or_base_missing"
        return scene_summary

    from pxr import UsdGeom

    root_xform = UsdGeom.Xformable(root_prim)
    orient_ops = [op for op in root_xform.GetOrderedXformOps() if op.GetName() == "xformOp:orient"]
    initial_orient = orient_ops[0].Get() if orient_ops else None
    cache = UsdGeom.XformCache()
    base_xyz = world_translation(cache, base_prim)

    create_runtime_prims(stage, int(args.width), int(args.height))
    camera_prim = stage.GetPrimAtPath(CAMERA_PATH)
    light_prim = stage.GetPrimAtPath(LIGHT_PATH)
    if not camera_prim or not camera_prim.IsValid():
        scene_summary["failure_reason"] = "runtime_camera_missing"
        return scene_summary

    render_product = rep.create.render_product(CAMERA_PATH, (int(args.width), int(args.height)))
    annotators, annotator_errors = attach_camera_annotators(rep, render_product)
    required = {"rgb", "distance_to_image_plane", "camera_params"}
    if not required.issubset(annotators):
        scene_summary["failure_reason"] = f"required_annotators_missing: {annotator_errors}"
        return scene_summary
    try:
        rep.orchestrator.set_capture_on_play(False)
    except Exception:
        pass

    starts = start_pose_plan(base_xyz, int(args.start_count))
    for start in starts:
        history: list[CaptureFrame] = []
        start_id = int(start["start_id"])
        for step_id in range(int(args.max_steps_per_start)):
            robot_pose = pose_for_step(start, step_id)
            set_root_pose(root_prim, (robot_pose[0], robot_pose[1], robot_pose[2]), robot_pose[3], initial_orient)
            eye, target = expected_sensor_pose(robot_pose[0], robot_pose[1], robot_pose[2], robot_pose[3])
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

            rgb = rgb_stats(annotators["rgb"].get_data())
            depth = depth_stats(annotators["distance_to_image_plane"].get_data())
            camera_params = annotators["camera_params"].get_data()
            intr_ok, intrinsics = intrinsics_from_camera_params(
                camera_params,
                depth["width"] or int(args.width),
                depth["height"] or int(args.height),
            )
            world_points = np.empty((0, 3), dtype=np.float32)
            if depth["available"] and intr_ok:
                cam_points = pointcloud_from_depth(depth["array"], intrinsics, stride=int(args.depth_stride))
                world_points = filter_world_points(camera_points_to_world(cam_points, eye, target))
            frame = CaptureFrame(
                eye=tuple(float(v) for v in eye),
                target=tuple(float(v) for v in target),
                world_points=world_points,
                rgb_available=bool(rgb["available"]),
                depth_available=bool(depth["available"]),
                depth_valid_ratio=float(depth["valid_ratio"] or 0.0),
                intrinsics=intrinsics if intr_ok else {"fx": 1.0, "fy": 1.0, "cx": 0.0, "cy": 0.0},
                camera_pose=camera_pose_from_eye_target(eye, target),
            )
            history.append(frame)
            scene_summary["capture_step_count"] += 1
            scene_summary["valid_rgb_capture_count"] += int(frame.rgb_available)
            scene_summary["valid_depth_capture_count"] += int(frame.depth_available and intr_ok)
            scene_summary["world_point_count_total"] += int(world_points.shape[0])

            for cfg in DATASETS:
                dataset_root = DATA_ROOT / cfg.dataset_version
                crop_center = (robot_pose[0], robot_pose[1], robot_pose[2])
                crop_origin = crop_origin_from_center(crop_center, cfg.dims, voxel_size)
                full_crop, valid_mask = crop_3d_from_origin(
                    gt["full_occupancy"],
                    gt["origin_xyz"],
                    crop_origin,
                    cfg.dims,
                    voxel_size,
                    fill_value=0,
                )
                observed_free, observed_occupied, unknown_mask, ray_stats = build_partial_from_history(
                    history,
                    cfg.dims,
                    voxel_size,
                    crop_origin,
                    cfg.max_points_per_sample,
                )
                frontier_mask = frontier_from_free_unknown(
                    observed_free,
                    unknown_mask,
                    FRONTIER_CONNECTIVITY,
                ).astype(np.uint8)
                robot_gaussian, height_channel = robot_gaussian_and_height(
                    cfg.dims,
                    voxel_size,
                    crop_origin,
                    robot_pose,
                )
                quality_status, quality_flags, quality_stats = evaluate_quality(
                    observed_free,
                    observed_occupied,
                    unknown_mask,
                    frontier_mask,
                    full_crop,
                    valid_mask,
                )
                if not (frame.depth_available and intr_ok):
                    quality_flags.append("depth_or_intrinsics_unavailable_for_current_step")
                    if quality_status != "reject":
                        quality_status = "warning"

                global_id = global_ids[cfg.dataset_version]
                sample_id = f"{scene.scene_id}_start{start_id:03d}_step{step_id:03d}_real_partial"
                rel_path = Path(scene.scene_id) / f"sample_{global_id:06d}.npz"
                out_path = dataset_root / rel_path
                save_sample(
                    out_path,
                    observed_free=observed_free,
                    observed_occupied=observed_occupied,
                    unknown_mask=unknown_mask,
                    frontier_mask=frontier_mask,
                    robot_gaussian=robot_gaussian,
                    height_channel=height_channel,
                    robot_pose=robot_pose,
                    camera_pose=frame.camera_pose,
                    camera_intrinsics=intrinsics_matrix(frame.intrinsics),
                    full_occupancy=full_crop,
                    valid_mask=valid_mask,
                    voxel_size=voxel_size,
                    crop_origin_xyz=crop_origin,
                    crop_center_xyz=crop_center,
                    scene=scene,
                    start_id=start_id,
                    step_id=step_id,
                    sample_id=sample_id,
                    quality_status=quality_status,
                    quality_flags=quality_flags,
                )
                record = {
                    "dataset_version": cfg.dataset_version,
                    "relative_path": str(rel_path),
                    "scene_id": scene.scene_id,
                    "scene_path": str(scene.scene_path),
                    "start_id": start_id,
                    "step_id": step_id,
                    "sample_id": sample_id,
                    "quality_status": quality_status,
                    "quality_flags": quality_flags,
                    "observed_free_count": int(observed_free.sum()),
                    "observed_occupied_count": int(observed_occupied.sum()),
                    "unknown_count": int(unknown_mask.sum()),
                    "frontier_count": int(frontier_mask.sum()),
                    "full_occupancy_occupied_count": int(full_crop.sum()),
                    "valid_mask_count": int(valid_mask.sum()),
                    "gt_observed_conflict_ratio": float(quality_stats["gt_observed_conflict_ratio"]),
                    "observed_free_overlaps_occupied": int(quality_stats["observed_free_overlaps_occupied"]),
                    "depth_valid_ratio": frame.depth_valid_ratio,
                    "rgb_available": frame.rgb_available,
                    "depth_available": frame.depth_available,
                    "world_point_count": int(world_points.shape[0]),
                    "ray_input_point_count": int(ray_stats.get("input_point_count", 0)),
                    "ray_used_point_count": int(ray_stats.get("used_point_count", 0)),
                    "ray_endpoint_inside_count": int(ray_stats.get("endpoint_inside_count", 0)),
                    "gt_type": GT_TYPE,
                    "partial_3d_source": PARTIAL_SOURCE,
                }
                dataset_records[cfg.dataset_version].append(record)
                global_ids[cfg.dataset_version] += 1

    scene_summary["status"] = "success"
    return scene_summary


def finalize_dataset(
    cfg: DatasetConfig,
    records: list[dict[str, Any]],
    run_dir: Path,
    scenes: list[str],
    voxel_size: float,
) -> dict[str, Any]:
    dataset_root = DATA_ROOT / cfg.dataset_version
    summary = summarize_records(records)
    split_summary = write_splits(dataset_root, records)
    manifest = local_voxel_dataset_manifest(
        dataset_name=cfg.dataset_version,
        gt_type=GT_TYPE,
        scenes=scenes,
        voxel_shape=cfg.dims,
        voxel_size=voxel_size,
        sample_count=int(summary["sample_count"]),
        pass_count=int(summary["pass_count"]),
        warning_count=int(summary["warning_count"]),
        reject_count=int(summary["reject_count"]),
        partial_3d_source=PARTIAL_SOURCE,
        observed_occupied_zero_rate=float(summary["observed_occupied_zero_rate"]),
    )
    manifest.update(
        {
            "dataset_version": cfg.dataset_version,
            "frontier_connectivity": FRONTIER_CONNECTIVITY,
            "sensor_method": "real_isaac_omniverse_rgbd",
            "crop_type": "robot_centered",
            "full_occupancy_used_as_input": False,
            "full_occupancy_label_only": True,
            "gt_is_perfect_ground_truth": False,
            "requires_review": True,
            "training_ready": False,
            "quality_summary": summary,
            "split_summary": split_summary,
        }
    )
    write_json(dataset_root / "dataset_manifest.json", manifest)
    write_json(run_dir / "summary" / f"{cfg.dataset_version}_manifest.json", manifest)
    scene_plot_paths: list[str] = []
    for scene_id in scenes:
        scene_plot_paths.extend(save_sample_plots(dataset_root, run_dir, scene_id, records))
    return {
        "dataset_version": cfg.dataset_version,
        "dataset_path": str(dataset_root),
        "voxel_shape": list(cfg.dims),
        "voxel_size": voxel_size,
        "summary": summary,
        "split_summary": split_summary,
        "visualization_paths": scene_plot_paths,
        "manifest_path": str(dataset_root / "dataset_manifest.json"),
    }


def write_report(summary: dict[str, Any]) -> None:
    main = summary.get("datasets", {}).get("local_voxel_v1_real_partial_3d", {})
    main_summary = main.get("summary", {})
    split_summary = main.get("split_summary", {})
    vis = main.get("visualization_paths", [])
    lines = [
        "# MapPredict Phase 2.5 Real Partial 3D Recapture Report",
        "",
        "phase: MapPredict Phase 2.5",
        "purpose: rebuild real partial 3D occupancy samples",
        f"workspace: {summary.get('workspace')}",
        f"project_name: {summary.get('project_name')}",
        f"main_goal: {summary.get('main_goal')}",
        "map_predict_role: feature_provider",
        "planner: false",
        "VLA: false",
        "training_started: false",
        "map_predict_training_started: false",
        "VLA_training_started: false",
        "SFT_started: false",
        "GDPO_started: false",
        "RL_started: false",
        "rollout_started: false",
        "",
        "## Old Phase 2 Limitation Summary",
        "",
        "* Phase 2 proved dataset schema, crop, manifest, split, and visualization plumbing.",
        "* Phase 2 used reconstructed_from_saved_rollout_metadata_limited because raw per-step 3D depth endpoints were not retained.",
        "* Phase 2 main warning_count was 277 / 277, with observed_occupied_count_zero on every sample.",
        "* Phase 2 safe_to_train_3d_unet_baseline was false.",
        "",
        "## Recapture Method",
        "",
        "route used: recapture",
        "sensor_method: real_isaac_omniverse_rgbd",
        f"partial_3d_source: {PARTIAL_SOURCE}",
        f"gt_type: {GT_TYPE}",
        f"frontier_connectivity: {FRONTIER_CONNECTIVITY}-neighborhood",
        f"start_count_per_scene: {summary.get('start_count_per_scene')}",
        f"max_steps_per_start: {summary.get('max_steps_per_start')}",
        "full_occupancy_used_as_input: false",
        "full_occupancy_label_only: true",
        "dense_scan_pseudo_gt_is_perfect_ground_truth: false",
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
                f"status: {scene.get('status')}",
                f"route_used: {scene.get('route_used')}",
                f"capture_step_count: {scene.get('capture_step_count')}",
                f"valid_rgb_capture_count: {scene.get('valid_rgb_capture_count')}",
                f"valid_depth_capture_count: {scene.get('valid_depth_capture_count')}",
                f"world_point_count_total: {scene.get('world_point_count_total')}",
                f"failure_reason: {scene.get('failure_reason')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Main Dataset Summary",
            "",
            "dataset_version: local_voxel_v1_real_partial_3d",
            f"dataset path: {main.get('dataset_path')}",
            f"sample_count: {main_summary.get('sample_count')}",
            f"pass_count: {main_summary.get('pass_count')}",
            f"warning_count: {main_summary.get('warning_count')}",
            f"reject_count: {main_summary.get('reject_count')}",
            f"observed_occupied_zero_rate: {main_summary.get('observed_occupied_zero_rate')}",
            f"frontier_empty_rate: {main_summary.get('frontier_empty_rate')}",
            f"gt_conflict stats: {main_summary.get('gt_observed_conflict_ratio')}",
            f"observed_free_count: {main_summary.get('observed_free_count')}",
            f"observed_occupied_count: {main_summary.get('observed_occupied_count')}",
            f"unknown_count: {main_summary.get('unknown_count')}",
            f"frontier_count: {main_summary.get('frontier_count')}",
            f"full_occupancy_occupied_count: {main_summary.get('full_occupancy_occupied_count')}",
            f"quality_flag_counts: {main_summary.get('quality_flag_counts')}",
            "",
            "## Split Summary",
            "",
            f"split summary: {split_summary}",
            "",
            "## Visualization Paths",
            "",
        ]
    )
    if vis:
        lines.extend(f"* {path}" for path in vis)
    else:
        lines.append("* none")
    lines.extend(
        [
            "",
            "## Smoke Dataset Summary",
            "",
        ]
    )
    smoke = summary.get("datasets", {}).get("local_voxel_smoke_v1_real_partial_3d", {})
    smoke_summary = smoke.get("summary", {})
    lines.extend(
        [
            "dataset_version: local_voxel_smoke_v1_real_partial_3d",
            f"dataset path: {smoke.get('dataset_path')}",
            f"sample_count: {smoke_summary.get('sample_count')}",
            f"pass_count: {smoke_summary.get('pass_count')}",
            f"warning_count: {smoke_summary.get('warning_count')}",
            f"reject_count: {smoke_summary.get('reject_count')}",
            f"observed_occupied_zero_rate: {smoke_summary.get('observed_occupied_zero_rate')}",
            "",
            "## Decision",
            "",
            f"recapture_completed: {bool_text(summary.get('recapture_completed'))}",
            f"main_reject_rate: {summary.get('main_reject_rate')}",
            f"safe_to_rebuild_phase2_dataset: {bool_text(summary.get('safe_to_rebuild_phase2_dataset'))}",
            f"safe_to_train_3d_unet_baseline: {bool_text(summary.get('safe_to_train_3d_unet_baseline'))}",
            f"next_phase: {summary.get('next_phase')}",
            "",
            "## Constraints Honored",
            "",
            "* map_predict training: false",
            "* 3D U-Net training: false",
            "* diffusion training: false",
            "* VLA training: false",
            "* SFT: false",
            "* GDPO: false",
            "* RL: false",
            "* source USD modified: false",
            "* raw RGB-D saved: false",
            "* raw pointcloud dumps saved: false",
            "* large `.npz` committed: false",
        ]
    )
    TOP_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run_report = Path(summary["run_dir"]) / "reports" / TOP_REPORT.name
    run_report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--start-count", type=int, default=5)
    parser.add_argument("--max-steps-per-start", type=int, default=10)
    parser.add_argument("--width", type=int, default=160)
    parser.add_argument("--height", type=int, default=120)
    parser.add_argument("--depth-stride", type=int, default=4)
    parser.add_argument("--open-timeout-sec", type=float, default=180.0)
    parser.add_argument("--smoke", action="store_true", help="Run fewer captures for local debugging.")
    args = parser.parse_args()

    if args.smoke:
        args.start_count = min(args.start_count, 1)
        args.max_steps_per_start = min(args.max_steps_per_start, 2)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.run_dir) if args.run_dir else RUNS_DIR / f"map_predict_phase25_real_partial_3d_recapture_{timestamp}"
    for rel in ["logs", "partial_maps", "reports", "summary", "plots", "debug"]:
        (run_dir / rel).mkdir(parents=True, exist_ok=True)

    for cfg in DATASETS:
        clear_dataset_root(DATA_ROOT / cfg.dataset_version)

    dataset_records: dict[str, list[dict[str, Any]]] = {cfg.dataset_version: [] for cfg in DATASETS}
    global_ids: dict[str, int] = {cfg.dataset_version: 0 for cfg in DATASETS}
    summary: dict[str, Any] = {
        "phase": PHASE,
        "workspace": str(WORKSPACE),
        "project_name": PROJECT,
        "main_goal": GOAL,
        "run_dir": str(run_dir),
        "route_used": "recapture",
        "sensor_method": "real_isaac_omniverse_rgbd",
        "partial_3d_source": PARTIAL_SOURCE,
        "gt_type": GT_TYPE,
        "start_count_per_scene": int(args.start_count),
        "max_steps_per_start": int(args.max_steps_per_start),
        "training_started": False,
        "map_predict_training_started": False,
        "VLA_training_started": False,
        "SFT_started": False,
        "GDPO_started": False,
        "RL_started": False,
        "source_usd_modified": False,
        "raw_rgbd_saved": False,
        "raw_pointcloud_dump_saved": False,
        "scenes": [],
        "datasets": {},
        "safe_to_rebuild_phase2_dataset": False,
        "safe_to_train_3d_unet_baseline": False,
        "next_phase": "Fix MapPredict Phase 2.5 real partial 3D occupancy recapture",
    }

    app = None
    try:
        from isaacsim import SimulationApp

        app = SimulationApp({"headless": True})
        import omni.replicator.core as rep
        import omni.usd

        for scene in SCENES:
            scene_summary = process_scene(scene, args, app, rep, omni.usd, dataset_records, global_ids)
            summary["scenes"].append(scene_summary)
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()

    voxel_sizes = []
    for scene in SCENES:
        if scene.gt_path.exists():
            try:
                voxel_sizes.append(load_gt(scene.gt_path)["voxel_size"])
            except Exception:
                pass
    voxel_size = float(voxel_sizes[0]) if voxel_sizes else 0.2
    scene_ids = [s.scene_id for s in SCENES]
    for cfg in DATASETS:
        summary["datasets"][cfg.dataset_version] = finalize_dataset(
            cfg,
            dataset_records[cfg.dataset_version],
            run_dir,
            scene_ids,
            voxel_size,
        )

    main = summary["datasets"]["local_voxel_v1_real_partial_3d"]["summary"]
    sample_count = int(main["sample_count"])
    reject_count = int(main["reject_count"])
    warning_count = int(main["warning_count"])
    observed_zero = float(main["observed_occupied_zero_rate"])
    reject_rate = rate(reject_count, sample_count)
    frontier_empty = float(main["frontier_empty_rate"])
    conflict = main["gt_observed_conflict_ratio"]
    conflict_p90 = float(conflict["p90"] or 0.0)
    success_scenes = sum(1 for s in summary["scenes"] if s.get("status") == "success")
    summary["recapture_completed"] = bool(success_scenes == len(SCENES) and sample_count > 0)
    summary["main_reject_rate"] = reject_rate
    summary["safe_to_rebuild_phase2_dataset"] = bool(
        summary["recapture_completed"]
        and observed_zero < 0.50
        and reject_rate <= 0.10
    )
    summary["safe_to_train_3d_unet_baseline"] = bool(
        summary["safe_to_rebuild_phase2_dataset"]
        and reject_count == 0
        and warning_count < sample_count
        and observed_zero <= 0.20
        and frontier_empty <= 0.20
        and conflict_p90 <= 0.20
    )
    if summary["safe_to_train_3d_unet_baseline"]:
        summary["next_phase"] = "MapPredict Phase 3 3D U-Net occupancy completion baseline"
    elif summary["recapture_completed"] and observed_zero < 0.50:
        summary["next_phase"] = "MapPredict Phase 2.6 finalize local voxel dataset with real partial 3D and resolve pseudo-GT alignment conflicts"

    write_json(run_dir / "summary" / "phase25_real_partial_3d_recapture_summary.json", summary)
    write_report(summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if app is not None:
        app.close()
    return 0 if summary.get("safe_to_rebuild_phase2_dataset") else 2


if __name__ == "__main__":
    raise SystemExit(main())
