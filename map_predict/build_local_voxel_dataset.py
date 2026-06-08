"""Build MapPredict Phase 2 local voxel crop dataset.

This script does not train. It builds prototype local voxel samples from Phase 1
dense_scan_pseudo_gt labels and saved rollout metadata. Because raw per-step 3D
point clouds were not retained in the rollout folders, partial observations are
marked as limited metadata reconstruction.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

try:
    from .crop import crop_3d_from_origin, crop_origin_from_center, grid_centers_xyz
    from .dataset import local_voxel_dataset_manifest
    from .metrics import count_distribution, observed_gt_conflict_ratio
    from .voxelize import frontier_from_free_unknown, unknown_from_observed
except ImportError:
    from crop import crop_3d_from_origin, crop_origin_from_center, grid_centers_xyz
    from dataset import local_voxel_dataset_manifest
    from metrics import count_distribution, observed_gt_conflict_ratio
    from voxelize import frontier_from_free_unknown, unknown_from_observed


WORKSPACE = Path("/home/ubuntu22/VLA")
GT_TYPE = "dense_scan_pseudo_gt"
PARTIAL_SOURCE = "reconstructed_from_saved_rollout_metadata_limited"
FRONTIER_CONNECTIVITY = 6
DATASET_MAIN = "local_voxel_v0_dense_scan_pseudo_gt"
DATASET_SMOKE = "local_voxel_smoke_v0_dense_scan_pseudo_gt"


@dataclass(frozen=True)
class SceneSource:
    scene_id: str
    scene_path: Path
    gt_path: Path
    rollout_dir: Path
    quality_dir: Path


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    dims: tuple[int, int, int]
    voxel_size: float
    max_samples_per_scene: int | None


SCENES = [
    SceneSource(
        scene_id="old_home_like_scene_v1",
        scene_path=WORKSPACE / "scenes/primary_building_scene_repaired/home_like_scene_v1.usd",
        gt_path=WORKSPACE / "data/map_predict/full_occupancy_gt/old_home_like_scene_v1/full_occupancy_dense_scan.npz",
        rollout_dir=WORKSPACE / "runs/phase8_a1_vlm_la_long_rollout_20260607_212536",
        quality_dir=WORKSPACE / "runs/phase9_human_review_packet_20260607_213732",
    ),
    SceneSource(
        scene_id="new_building_scene_1",
        scene_path=WORKSPACE / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda",
        gt_path=WORKSPACE / "data/map_predict/full_occupancy_gt/new_building_scene_1/full_occupancy_dense_scan.npz",
        rollout_dir=WORKSPACE / "runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904",
        quality_dir=WORKSPACE / "runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002",
    ),
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_sample_ids(sample_id: str) -> tuple[int, int]:
    match = re.search(r"start(\d+)_step(\d+)", sample_id)
    if not match:
        return 0, 0
    return int(match.group(1)), int(match.group(2))


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def as_float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = row.get(key, default)
    if value in ("", None):
        return default
    return float(value)


def as_int(row: dict[str, Any], key: str, default: int = 0) -> int:
    value = row.get(key, default)
    if value in ("", None):
        return default
    return int(float(value))


def load_gt(path: Path) -> dict[str, Any]:
    z = np.load(path, allow_pickle=True)
    return {
        "full_occupancy": z["occupancy"].astype(np.uint8),
        "voxel_size": float(z["voxel_size"]),
        "origin_xyz": tuple(float(x) for x in z["origin_xyz"]),
        "scene_path": str(z["scene_path"].item()),
        "scene_id": str(z["scene_id"].item()),
        "gt_type": str(z["gt_type"].item()),
    }


def pair_rows_and_samples(scene: SceneSource) -> list[dict[str, Any]]:
    steps_path = scene.rollout_dir / "summary/rollout_steps.csv"
    samples_path = scene.rollout_dir / "samples/vlm_la_samples.jsonl"
    if not steps_path.exists() or not samples_path.exists():
        return []
    step_rows = read_csv_rows(steps_path)
    samples = read_jsonl(samples_path)
    sample_by_key: dict[tuple[int, int], dict[str, Any]] = {}
    for sample in samples:
        start_id, step_id = parse_sample_ids(sample.get("sample_id", ""))
        sample_by_key[(start_id, step_id)] = sample

    out = []
    for row in step_rows:
        start_id = as_int(row, "start_id")
        step_id = as_int(row, "step_id")
        sample = sample_by_key.get((start_id, step_id), {})
        merged = {"step": row, "sample": sample, "start_id": start_id, "step_id": step_id}
        out.append(merged)
    return out


def path_history(rows: list[dict[str, Any]]) -> dict[tuple[int, int], list[tuple[float, float, float, float]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in rows:
        grouped[item["start_id"]].append(item)
    history: dict[tuple[int, int], list[tuple[float, float, float, float]]] = {}
    for start_id, items in grouped.items():
        items.sort(key=lambda x: x["step_id"])
        poses: list[tuple[float, float, float, float]] = []
        for item in items:
            row = item["step"]
            pre_pose = (
                as_float(row, "pre_base_x"),
                as_float(row, "pre_base_y"),
                as_float(row, "pre_base_z", 0.5967),
                as_float(row, "pre_base_yaw"),
            )
            post_pose = (
                as_float(row, "post_base_x"),
                as_float(row, "post_base_y"),
                as_float(row, "post_base_z", pre_pose[2]),
                as_float(row, "post_base_yaw", pre_pose[3]),
            )
            if not poses:
                poses.append(pre_pose)
            poses.append(post_pose)
            history[(start_id, item["step_id"])] = list(poses)
    return history


def deterministic_jitter(sample_id: str) -> tuple[float, float]:
    seed = sum(ord(c) for c in sample_id) % 9973
    angle = (seed % 360) * math.pi / 180.0
    radius = 0.15 + (seed % 11) * 0.01
    return math.cos(angle) * radius, math.sin(angle) * radius


def build_limited_partial(
    dims: tuple[int, int, int],
    voxel_size: float,
    crop_origin_xyz: tuple[float, float, float],
    robot_pose: tuple[float, float, float, float],
    pose_history: list[tuple[float, float, float, float]],
    sample: dict[str, Any],
    step: dict[str, str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build limited partial occupancy from saved rollout metadata only."""

    xx, yy, zz = grid_centers_xyz(dims, crop_origin_xyz, voxel_size)
    observed_free = np.zeros(dims, dtype=bool)
    observed_occupied = np.zeros(dims, dtype=bool)

    known_ratio = as_float(step, "known_ratio_after", 0.05)
    depth_valid_ratio = as_float(step, "depth_valid_ratio", 0.8)
    base_radius = float(np.clip(1.0 + 5.0 * known_ratio, 1.0, 4.25))
    radius = base_radius * float(np.clip(depth_valid_ratio, 0.5, 1.0))
    z_band = (zz >= 0.0) & (zz <= max(1.2, robot_pose[2] + 0.45))

    for idx, pose in enumerate(pose_history):
        px, py, _pz, yaw = pose
        dist = np.sqrt((xx - px) ** 2 + (yy - py) ** 2)
        angle = np.arctan2(yy - py, xx - px)
        delta = np.arctan2(np.sin(angle - yaw), np.cos(angle - yaw))
        local_radius = radius * (0.55 + 0.45 * (idx + 1) / max(1, len(pose_history)))
        free_mask = (dist <= local_radius) & (np.abs(delta) <= math.radians(125.0)) & z_band
        observed_free |= free_mask

    # Raw depth endpoint voxels were not retained in Phase 8 / Phase G. Candidate
    # validity metadata is not a trustworthy replacement for 3D occupied hits, so
    # the first Phase 2 prototype leaves observed_occupied empty and marks the
    # sample as limited. This avoids leaking dense_scan_pseudo_gt into inputs.

    observed_occupied &= ~observed_free
    unknown_mask = unknown_from_observed(observed_free, observed_occupied)
    return observed_free.astype(np.uint8), observed_occupied.astype(np.uint8), unknown_mask.astype(np.uint8)


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
    return gaussian, height


def evaluate_quality(
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
    unknown_mask: np.ndarray,
    frontier_mask: np.ndarray,
    full_occupancy: np.ndarray,
    valid_mask: np.ndarray,
) -> tuple[str, list[str], float]:
    flags: list[str] = []
    status = "pass"

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

    if unknown_mask.sum() == 0:
        flags.append("unknown_mask_all_zero")
        status = "reject"
    if observed_free.sum() + observed_occupied.sum() == 0:
        flags.append("observed_free_and_occupied_all_zero")
        status = "reject"
    if full_occupancy.shape != expected_shape:
        flags.append("full_occupancy_shape_wrong")
        status = "reject"
    if np.logical_and(observed_free, observed_occupied).sum() > 0:
        flags.append("observed_free_overlaps_observed_occupied")
        status = "reject"
    if valid_mask.sum() == 0:
        flags.append("valid_mask_all_zero")
        status = "reject"

    conflict = observed_gt_conflict_ratio(observed_occupied, full_occupancy)
    if observed_occupied.sum() > 32 and conflict > 0.95:
        flags.append("severe_gt_observed_conflict_ratio")
        status = "reject"
    elif observed_occupied.sum() > 0 and conflict > 0.50:
        flags.append("gt_observed_conflict_ratio_high_limited_source")
        if status != "reject":
            status = "warning"

    if frontier_mask.sum() == 0:
        flags.append("frontier_mask_all_zero")
        if status != "reject":
            status = "warning"
    if full_occupancy.sum() == 0:
        flags.append("full_occupancy_occupied_count_zero")
        if status != "reject":
            status = "warning"
    if observed_occupied.sum() == 0:
        flags.append("observed_occupied_count_zero")
        if status != "reject":
            status = "warning"
    flags.append("partial_3d_source_limited")
    if status != "reject":
        status = "warning"
    return status, flags, conflict


def split_samples(records: list[dict[str, Any]]) -> tuple[dict[str, list[str]], dict[str, Any]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for rec in records:
        groups[f"{rec['scene_id']}::start_{rec['start_id']:03d}"].append(rec["relative_path"])
    keys = sorted(groups)
    train_keys: list[str] = []
    val_keys: list[str] = []
    test_keys: list[str] = []
    for idx, key in enumerate(keys):
        bucket = idx % 20
        if bucket < 14:
            train_keys.append(key)
        elif bucket < 17:
            val_keys.append(key)
        else:
            test_keys.append(key)
    split_keys = {"train": train_keys, "val": val_keys, "test": test_keys}
    splits: dict[str, list[str]] = {}
    for split, split_group_keys in split_keys.items():
        paths: list[str] = []
        for key in split_group_keys:
            paths.extend(groups[key])
        splits[split] = sorted(paths)
    summary = {
        "split_method": "deterministic_scene_id_start_id_group_modulo",
        "train_group_count": len(train_keys),
        "val_group_count": len(val_keys),
        "test_group_count": len(test_keys),
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
    (split_dir / "split_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(r["quality_status"] for r in records)
    flags = Counter(flag for r in records for flag in r["quality_flags"])
    return {
        "sample_count": len(records),
        "pass_count": status_counts.get("pass", 0),
        "warning_count": status_counts.get("warning", 0),
        "reject_count": status_counts.get("reject", 0),
        "quality_flag_counts": dict(sorted(flags.items())),
        "observed_free_count": count_distribution(r["observed_free_count"] for r in records),
        "observed_occupied_count": count_distribution(r["observed_occupied_count"] for r in records),
        "unknown_count": count_distribution(r["unknown_count"] for r in records),
        "frontier_count": count_distribution(r["frontier_count"] for r in records),
        "full_occupancy_occupied_count": count_distribution(r["full_occupancy_occupied_count"] for r in records),
        "gt_observed_conflict_ratio": count_distribution(r["gt_observed_conflict_ratio"] for r in records),
        "empty_crop_count": sum(1 for r in records if r["observed_free_count"] + r["observed_occupied_count"] == 0),
        "frontier_empty_count": sum(1 for r in records if r["frontier_count"] == 0),
        "unknown_empty_count": sum(1 for r in records if r["unknown_count"] == 0),
    }


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
    full_occupancy: np.ndarray,
    valid_mask: np.ndarray,
    voxel_size: float,
    crop_origin_xyz: tuple[float, float, float],
    crop_center_xyz: tuple[float, float, float],
    scene: SceneSource,
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


def build_dataset_version(
    cfg: DatasetConfig,
    out_base: Path,
    run_dir: Path,
) -> dict[str, Any]:
    dataset_root = out_base / cfg.name
    records: list[dict[str, Any]] = []
    scenes_processed: list[str] = []
    scene_summaries: list[dict[str, Any]] = []
    global_id = 0

    for scene in SCENES:
        if not scene.gt_path.exists() or not scene.rollout_dir.exists():
            scene_summaries.append({
                "scene_id": scene.scene_id,
                "status": "skipped",
                "reason": "missing_gt_or_rollout",
            })
            continue
        gt = load_gt(scene.gt_path)
        if abs(gt["voxel_size"] - cfg.voxel_size) > 1e-6:
            raise ValueError(f"{scene.scene_id} GT voxel_size {gt['voxel_size']} != cfg {cfg.voxel_size}")
        paired_rows = pair_rows_and_samples(scene)
        if cfg.max_samples_per_scene is not None:
            paired_rows = paired_rows[: cfg.max_samples_per_scene]
        histories = path_history(paired_rows)
        scenes_processed.append(scene.scene_id)
        scene_record_start = len(records)

        for item in paired_rows:
            step = item["step"]
            sample = item["sample"]
            start_id = item["start_id"]
            step_id = item["step_id"]
            robot_pose = (
                as_float(step, "pre_base_x"),
                as_float(step, "pre_base_y"),
                as_float(step, "pre_base_z", 0.5967),
                as_float(step, "pre_base_yaw"),
            )
            crop_center = (robot_pose[0], robot_pose[1], robot_pose[2])
            crop_origin = crop_origin_from_center(crop_center, cfg.dims, cfg.voxel_size)
            full_crop, valid_mask = crop_3d_from_origin(
                gt["full_occupancy"],
                gt["origin_xyz"],
                crop_origin,
                cfg.dims,
                cfg.voxel_size,
                fill_value=0,
            )
            observed_free, observed_occupied, unknown_mask = build_limited_partial(
                cfg.dims,
                cfg.voxel_size,
                crop_origin,
                robot_pose,
                histories.get((start_id, step_id), [robot_pose]),
                sample,
                step,
            )
            frontier_mask = frontier_from_free_unknown(observed_free, unknown_mask, FRONTIER_CONNECTIVITY).astype(np.uint8)
            robot_gaussian, height_channel = robot_gaussian_and_height(cfg.dims, cfg.voxel_size, crop_origin, robot_pose)
            quality_status, quality_flags, conflict = evaluate_quality(
                observed_free,
                observed_occupied,
                unknown_mask,
                frontier_mask,
                full_crop,
                valid_mask,
            )
            sample_id = sample.get("sample_id") or f"{scene.scene_id}_start{start_id:03d}_step{step_id:03d}"
            out_path = dataset_root / scene.scene_id / f"sample_{global_id:06d}.npz"
            save_sample(
                out_path,
                observed_free=observed_free,
                observed_occupied=observed_occupied,
                unknown_mask=unknown_mask,
                frontier_mask=frontier_mask,
                robot_gaussian=robot_gaussian,
                height_channel=height_channel,
                robot_pose=robot_pose,
                full_occupancy=full_crop,
                valid_mask=valid_mask,
                voxel_size=cfg.voxel_size,
                crop_origin_xyz=crop_origin,
                crop_center_xyz=crop_center,
                scene=scene,
                start_id=start_id,
                step_id=step_id,
                sample_id=sample_id,
                quality_status=quality_status,
                quality_flags=quality_flags,
            )
            rel_path = str(out_path.relative_to(dataset_root))
            records.append({
                "global_id": global_id,
                "sample_id": sample_id,
                "relative_path": rel_path,
                "scene_id": scene.scene_id,
                "scene_path": str(scene.scene_path),
                "start_id": start_id,
                "step_id": step_id,
                "crop_type": "robot_centered",
                "crop_center_xyz": list(crop_center),
                "crop_origin_xyz": list(crop_origin),
                "crop_shape": list(cfg.dims),
                "voxel_size": cfg.voxel_size,
                "gt_type": GT_TYPE,
                "partial_3d_source": PARTIAL_SOURCE,
                "frontier_connectivity": FRONTIER_CONNECTIVITY,
                "quality_status": quality_status,
                "quality_flags": quality_flags,
                "observed_free_count": int(observed_free.sum()),
                "observed_occupied_count": int(observed_occupied.sum()),
                "unknown_count": int(unknown_mask.sum()),
                "frontier_count": int(frontier_mask.sum()),
                "full_occupancy_occupied_count": int(full_crop.sum()),
                "valid_voxel_count": int(valid_mask.sum()),
                "gt_observed_conflict_ratio": conflict,
            })
            global_id += 1

        scene_records = records[scene_record_start:]
        scene_summaries.append({
            "scene_id": scene.scene_id,
            "status": "processed",
            "sample_count": len(scene_records),
            "rollout_dir": str(scene.rollout_dir),
            "gt_path": str(scene.gt_path),
        })

    quality_summary = summarize_records(records)
    manifest = local_voxel_dataset_manifest(
        dataset_name=cfg.name,
        gt_type=GT_TYPE,
        scenes=scenes_processed,
        voxel_shape=cfg.dims,
        voxel_size=cfg.voxel_size,
        sample_count=quality_summary["sample_count"],
        pass_count=quality_summary["pass_count"],
        warning_count=quality_summary["warning_count"],
        reject_count=quality_summary["reject_count"],
        partial_3d_source=PARTIAL_SOURCE,
    )
    manifest.update({
        "dataset_path": str(dataset_root),
        "crop_type": "robot_centered",
        "frontier_mask_method": "observed_free_and_adjacent_unknown",
        "frontier_connectivity": FRONTIER_CONNECTIVITY,
        "source_gt_is_perfect_ground_truth": False,
        "dense_scan_pseudo_gt_not_perfect_gt": True,
        "sample_index_file": "sample_index.jsonl",
    })
    dataset_root.mkdir(parents=True, exist_ok=True)
    (dataset_root / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    with (dataset_root / "sample_index.jsonl").open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True) + "\n")
    split_summary = write_splits(dataset_root, records)
    quality_summary["split_summary"] = split_summary
    (dataset_root / "quality_summary.json").write_text(json.dumps(quality_summary, indent=2, sort_keys=True), encoding="utf-8")

    run_dataset_dir = run_dir / "dataset" / cfg.name
    run_dataset_dir.mkdir(parents=True, exist_ok=True)
    (run_dataset_dir / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (run_dataset_dir / "quality_summary.json").write_text(json.dumps(quality_summary, indent=2, sort_keys=True), encoding="utf-8")
    (run_dataset_dir / "split_summary.json").write_text(json.dumps(split_summary, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "config": {
            "name": cfg.name,
            "dims": list(cfg.dims),
            "voxel_size": cfg.voxel_size,
            "max_samples_per_scene": cfg.max_samples_per_scene,
        },
        "dataset_root": str(dataset_root),
        "manifest": manifest,
        "quality_summary": quality_summary,
        "split_summary": split_summary,
        "scene_summaries": scene_summaries,
        "records": records,
    }


def make_plots(main_result: dict[str, Any], run_dir: Path) -> list[str]:
    plot_paths: list[str] = []
    dataset_root = Path(main_result["dataset_root"])
    records_by_scene: dict[str, dict[str, Any]] = {}
    for record in main_result["records"]:
        records_by_scene.setdefault(record["scene_id"], record)
    for scene_id, record in records_by_scene.items():
        sample_path = dataset_root / record["relative_path"]
        z = np.load(sample_path, allow_pickle=True)
        arrays = {
            "observed_free": z["observed_free"],
            "observed_occupied": z["observed_occupied"],
            "unknown": z["unknown_mask"],
            "frontier": z["frontier_mask"],
            "full_occupancy": z["full_occupancy"],
        }
        for name, arr in arrays.items():
            bev = arr.max(axis=0)
            out = run_dir / "plots" / scene_id / f"sample_bev_{name}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            plt.figure(figsize=(5, 5))
            plt.imshow(bev, origin="lower", cmap="viridis")
            plt.title(f"{scene_id} {name}")
            plt.tight_layout()
            plt.savefig(out, dpi=120)
            plt.close()
            plot_paths.append(str(out))

        out = run_dir / "plots" / scene_id / "sample_z_slices.png"
        fig, axes = plt.subplots(2, 4, figsize=(10, 5))
        full = z["full_occupancy"]
        obs = z["observed_free"] + 2 * z["observed_occupied"]
        indices = np.linspace(0, full.shape[0] - 1, 4, dtype=int)
        for col, idx in enumerate(indices):
            axes[0, col].imshow(full[idx], origin="lower", cmap="magma")
            axes[0, col].set_title(f"GT z={idx}")
            axes[1, col].imshow(obs[idx], origin="lower", cmap="viridis")
            axes[1, col].set_title(f"obs z={idx}")
            axes[0, col].axis("off")
            axes[1, col].axis("off")
        plt.tight_layout()
        plt.savefig(out, dpi=120)
        plt.close(fig)
        plot_paths.append(str(out))
    return plot_paths


def write_report(
    run_dir: Path,
    smoke_result: dict[str, Any],
    main_result: dict[str, Any],
    plot_paths: list[str],
) -> str:
    main_q = main_result["quality_summary"]
    smoke_q = smoke_result["quality_summary"]
    split = main_result["split_summary"]
    scene_lines = []
    for scene in SCENES:
        scene_lines.append(f"- {scene.scene_id}: {scene.scene_path}")
    source_rollouts = []
    for scene in SCENES:
        source_rollouts.append(f"- {scene.scene_id}: {scene.rollout_dir}")
    limitations = [
        "dense_scan_pseudo_gt is pseudo GT generated from multi-view Isaac depth; it is not perfect ground truth.",
        "Raw per-step 3D pointcloud arrays were not saved in the rollout directories.",
        "observed_free/observed_occupied are limited metadata reconstructions from rollout poses and map stats.",
        "The local voxel crop dataset is for engineering validation and human review before any training.",
    ]
    safe_to_train = (
        main_q["reject_count"] == 0
        and main_q["sample_count"] > 0
        and "partial_3d_source_limited" not in main_q["quality_flag_counts"]
    )
    report = f"""# MapPredict Phase 2 Local Voxel Dataset Report

phase: MapPredict Phase 2
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
source_GT: dense_scan_pseudo_gt
source GT: dense_scan_pseudo_gt
dense_scan_pseudo_gt_is_perfect_ground_truth: false
training_ready: false
requires_review: true
training_started: false
map_predict_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false

## Source Scenes

{chr(10).join(scene_lines)}

## Source Rollout Dirs

{chr(10).join(source_rollouts)}

## Dataset Outputs

dataset_version: {main_result['manifest']['dataset_name']}
dataset_path: {main_result['dataset_root']}
smoke_dataset_version: {smoke_result['manifest']['dataset_name']}
smoke_dataset_path: {smoke_result['dataset_root']}
voxel_shape: {main_result['manifest']['voxel_shape']}
smoke_voxel_shape: {smoke_result['manifest']['voxel_shape']}
voxel_size: {main_result['manifest']['voxel_size']}
crop_type: robot_centered
partial_3d_source: {PARTIAL_SOURCE}
frontier_mask_generation_method: observed_free voxel adjacent to unknown voxel
frontier_connectivity: {FRONTIER_CONNECTIVITY}

## Main Dataset Quality

sample_count: {main_q['sample_count']}
pass_count: {main_q['pass_count']}
warning_count: {main_q['warning_count']}
reject_count: {main_q['reject_count']}
observed_free_count_distribution: {json.dumps(main_q['observed_free_count'], sort_keys=True)}
observed_occupied_count_distribution: {json.dumps(main_q['observed_occupied_count'], sort_keys=True)}
unknown_count_distribution: {json.dumps(main_q['unknown_count'], sort_keys=True)}
frontier_count_distribution: {json.dumps(main_q['frontier_count'], sort_keys=True)}
full_occupancy_occupied_count_distribution: {json.dumps(main_q['full_occupancy_occupied_count'], sort_keys=True)}
gt_observed_conflict_ratio_distribution: {json.dumps(main_q['gt_observed_conflict_ratio'], sort_keys=True)}
empty_crop_count: {main_q['empty_crop_count']}
frontier_empty_count: {main_q['frontier_empty_count']}
unknown_empty_count: {main_q['unknown_empty_count']}
quality_flag_counts: {json.dumps(main_q['quality_flag_counts'], sort_keys=True)}

## Smoke Dataset Quality

sample_count: {smoke_q['sample_count']}
pass_count: {smoke_q['pass_count']}
warning_count: {smoke_q['warning_count']}
reject_count: {smoke_q['reject_count']}

## Split Summary

split_method: {split['split_method']}
train_count: {split['train_count']}
val_count: {split['val_count']}
test_count: {split['test_count']}
train_group_count: {split['train_group_count']}
val_group_count: {split['val_group_count']}
test_group_count: {split['test_group_count']}
group_overlap: {str(split['group_overlap']).lower()}

## Visualization Paths

{chr(10).join(f'- {p}' for p in plot_paths)}

## Limitations

{chr(10).join(f'- {item}' for item in limitations)}

## Safety Decision

safe_to_train_3d_unet_baseline: {str(safe_to_train).lower()}
safe_to_continue_phase3_engineering: {str(main_q['reject_count'] == 0 and main_q['sample_count'] > 0).lower()}
next_phase: MapPredict Phase 3 3D U-Net occupancy completion baseline, only if Phase 2 quality passes and user explicitly approves training.
"""
    top_report = WORKSPACE / "runs/MAP_PREDICT_PHASE2_LOCAL_VOXEL_DATASET_REPORT.md"
    top_report.write_text(report, encoding="utf-8")
    (run_dir / "reports/MAP_PREDICT_PHASE2_LOCAL_VOXEL_DATASET_REPORT.md").write_text(report, encoding="utf-8")
    return str(top_report)


def write_status_files(run_dir: Path, main_result: dict[str, Any], report_path: str) -> None:
    status = f"""<!-- map_predict_phase2_status:start -->
## MapPredict Phase 2 Local Voxel Dataset Status

current_phase: MapPredict Phase 2 local voxel crop dataset generation
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
map_predict_goal: SceneSense-style partial occupancy completion and uncertainty feature provider
dataset_version: {main_result['manifest']['dataset_name']}
dataset_path: {main_result['dataset_root']}
source_GT: dense_scan_pseudo_gt
dense_scan_pseudo_gt_is_perfect_ground_truth: false
partial_3d_source: {PARTIAL_SOURCE}
voxel_shape: {main_result['manifest']['voxel_shape']}
voxel_size: {main_result['manifest']['voxel_size']}
sample_count: {main_result['quality_summary']['sample_count']}
pass_count: {main_result['quality_summary']['pass_count']}
warning_count: {main_result['quality_summary']['warning_count']}
reject_count: {main_result['quality_summary']['reject_count']}
training_started: false
map_predict_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false
requires_review: true
training_ready: false
safe_to_train_3d_unet_baseline: false
run_dir: {run_dir}
report: {report_path}
next_phase: MapPredict Phase 3 3D U-Net occupancy completion baseline, only if Phase 2 quality passes
<!-- map_predict_phase2_status:end -->
"""
    targets = [
        WORKSPACE / "runs/ACTIVE_TASK_BOARD.md",
        WORKSPACE / "runs/WEBGPT_BRIEF.md",
        WORKSPACE / "runs/CRITIC_REPORT.md",
        WORKSPACE / "runs/MAP_PREDICT_PLAN.md",
        WORKSPACE / "runs/MAP_PREDICT_DATASET_SPEC.md",
        WORKSPACE / "runs/MAP_PREDICT_INTERFACE_SPEC.md",
    ]
    pattern = re.compile(r"<!-- map_predict_phase2_status:start -->.*?<!-- map_predict_phase2_status:end -->\n?", re.S)
    for target in targets:
        text = target.read_text(encoding="utf-8") if target.exists() else ""
        if pattern.search(text):
            text = pattern.sub(status + "\n", text)
        else:
            text = status + "\n" + text
        target.write_text(text, encoding="utf-8")


def main() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = WORKSPACE / f"runs/map_predict_phase2_local_voxel_dataset_{timestamp}"
    for sub in ("logs", "dataset", "reports", "summary", "plots", "debug"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    out_base = WORKSPACE / "data/map_predict/local_voxel_dataset"

    configs = [
        DatasetConfig(DATASET_SMOKE, (16, 32, 32), 0.2, 8),
        DatasetConfig(DATASET_MAIN, (24, 64, 64), 0.2, None),
    ]
    smoke_result = build_dataset_version(configs[0], out_base, run_dir)
    main_result = build_dataset_version(configs[1], out_base, run_dir)
    plot_paths = make_plots(main_result, run_dir)
    report_path = write_report(run_dir, smoke_result, main_result, plot_paths)
    write_status_files(run_dir, main_result, report_path)

    phase_summary = {
        "phase": "MapPredict Phase 2 local voxel crop dataset generation",
        "run_dir": str(run_dir),
        "report_path": report_path,
        "training_started": False,
        "rollout_started": False,
        "datasets": {
            "smoke": {
                "dataset_root": smoke_result["dataset_root"],
                "quality_summary": smoke_result["quality_summary"],
                "split_summary": smoke_result["split_summary"],
            },
            "main": {
                "dataset_root": main_result["dataset_root"],
                "quality_summary": main_result["quality_summary"],
                "split_summary": main_result["split_summary"],
            },
        },
    }
    (run_dir / "summary/phase2_summary.json").write_text(json.dumps(phase_summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(phase_summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
