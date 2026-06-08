#!/usr/bin/env python3
"""MapPredict Phase 2.6 pseudo-GT alignment diagnostics.

This script diagnoses Phase 2.5 real partial 3D samples against Phase 1
dense_scan_pseudo_gt masks, fixes the conflict metric so GT unknown is not
treated as a contradiction, applies a conservative endpoint margin to observed
free voxels, and writes a corrected local voxel dataset v2.

It does not train, run rollout, open Isaac, mutate USD, or write raw RGB-D /
pointcloud dumps.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
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
    from .crop import crop_3d_from_origin, world_xyz_to_zyx
    from .metrics import (
        binary_dilation_3d,
        count_distribution,
        observed_gt_conflict_ratio,
        overlap_count,
        remove_endpoint_margin_from_free,
        true_observed_gt_conflict_stats,
        zero_rate,
    )
    from .voxelize import frontier_from_free_unknown, unknown_from_observed
except ImportError:
    from crop import crop_3d_from_origin, world_xyz_to_zyx
    from metrics import (
        binary_dilation_3d,
        count_distribution,
        observed_gt_conflict_ratio,
        overlap_count,
        remove_endpoint_margin_from_free,
        true_observed_gt_conflict_stats,
        zero_rate,
    )
    from voxelize import frontier_from_free_unknown, unknown_from_observed


WORKSPACE = Path("/home/ubuntu22/VLA")
RUNS_DIR = WORKSPACE / "runs"
DATA_ROOT = WORKSPACE / "data/map_predict/local_voxel_dataset"
SOURCE_DATASET_NAME = "local_voxel_v1_real_partial_3d"
CORRECTED_DATASET_NAME = "local_voxel_v2_aligned_real_partial_3d"
GT_TYPE = "dense_scan_pseudo_gt"
PARTIAL_SOURCE = "real_depth_backprojection_raycast"
AXIS_ORDER = "D=Z,H=Y,W=X"
FRONTIER_CONNECTIVITY = 6
ENDPOINT_MARGIN_VOX = 1
DILATION_RADIUS_VOX = 0
TOP_REPORT = RUNS_DIR / "MAP_PREDICT_PHASE26_ALIGNMENT_DEBUG_REPORT.md"
PHASE = "MapPredict Phase 2.6 pseudo-GT alignment conflict resolution"
PROJECT = "A1-VLM-LA Explorer"
GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"


@dataclass(frozen=True)
class SceneGT:
    scene_id: str
    gt_path: Path
    origin_xyz: tuple[float, float, float]
    voxel_size: float
    occupied_mask: np.ndarray
    free_mask: np.ndarray
    unknown_mask: np.ndarray
    observed_mask: np.ndarray


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_gt(scene_id: str) -> SceneGT:
    gt_path = WORKSPACE / "data/map_predict/full_occupancy_gt" / scene_id / "full_occupancy_dense_scan.npz"
    z = np.load(gt_path, allow_pickle=True)
    return SceneGT(
        scene_id=scene_id,
        gt_path=gt_path,
        origin_xyz=tuple(float(x) for x in z["origin_xyz"]),
        voxel_size=float(z["voxel_size"]),
        occupied_mask=z["occupied_mask"].astype(np.uint8),
        free_mask=z["free_mask"].astype(np.uint8),
        unknown_mask=z["unknown_mask"].astype(np.uint8),
        observed_mask=z["observed_mask"].astype(np.uint8),
    )


def load_v1_manifest(source_root: Path) -> dict[str, Any]:
    path = source_root / "dataset_manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def sample_paths(source_root: Path) -> list[Path]:
    return sorted(source_root.glob("*/*.npz"))


def scalar(value: np.ndarray | Any) -> Any:
    if isinstance(value, np.ndarray) and value.shape == ():
        return value.item()
    return value


def crop_gt_masks(sample: np.lib.npyio.NpzFile, gt: SceneGT) -> dict[str, np.ndarray]:
    dims = tuple(int(v) for v in sample["observed_free"].shape)
    voxel_size = float(sample["voxel_size"])
    crop_origin = tuple(float(x) for x in sample["crop_origin_xyz"])
    occupied, valid = crop_3d_from_origin(gt.occupied_mask, gt.origin_xyz, crop_origin, dims, voxel_size, fill_value=0)
    free, _ = crop_3d_from_origin(gt.free_mask, gt.origin_xyz, crop_origin, dims, voxel_size, fill_value=0)
    unknown, _ = crop_3d_from_origin(gt.unknown_mask, gt.origin_xyz, crop_origin, dims, voxel_size, fill_value=1)
    observed, _ = crop_3d_from_origin(gt.observed_mask, gt.origin_xyz, crop_origin, dims, voxel_size, fill_value=0)
    return {
        "gt_occupied": occupied.astype(np.uint8),
        "gt_free": free.astype(np.uint8),
        "gt_unknown": unknown.astype(np.uint8),
        "gt_observed": observed.astype(np.uint8),
        "valid_mask_from_gt": valid.astype(np.uint8),
    }


def round_trip_errors(sample: np.lib.npyio.NpzFile) -> list[float]:
    dims = tuple(int(v) for v in sample["observed_free"].shape)
    voxel_size = float(sample["voxel_size"])
    crop_origin = np.asarray(sample["crop_origin_xyz"], dtype=np.float32)
    zs = sorted({0, dims[0] // 2, dims[0] - 1})
    ys = sorted({0, dims[1] // 2, dims[1] - 1})
    xs = sorted({0, dims[2] // 2, dims[2] - 1})
    errors: list[float] = []
    for z, y, x in [(z, y, x) for z in zs for y in ys for x in xs]:
        xyz = crop_origin + np.asarray(
            [(x + 0.5) * voxel_size, (y + 0.5) * voxel_size, (z + 0.5) * voxel_size],
            dtype=np.float32,
        )
        zyx = world_xyz_to_zyx(xyz.reshape(1, 3), tuple(float(v) for v in crop_origin), voxel_size)[0]
        center = crop_origin + np.asarray(
            [(zyx[2] + 0.5) * voxel_size, (zyx[1] + 0.5) * voxel_size, (zyx[0] + 0.5) * voxel_size],
            dtype=np.float32,
        )
        errors.append(float(np.linalg.norm(center - xyz)))
    return errors


def true_conflict_with_options(
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
    gt_free: np.ndarray,
    gt_occupied: np.ndarray,
    gt_unknown: np.ndarray,
    *,
    dilation_radius_vox: int,
    endpoint_margin_vox: int,
) -> dict[str, float | int]:
    free = np.asarray(observed_free, dtype=bool)
    occupied = np.asarray(observed_occupied, dtype=bool)
    if endpoint_margin_vox > 0:
        free = remove_endpoint_margin_from_free(free, occupied, endpoint_margin_vox)
    gt_occ = binary_dilation_3d(gt_occupied, dilation_radius_vox, connectivity=26)
    gt_free_eff = np.asarray(gt_free, dtype=bool) & ~gt_occ
    return true_observed_gt_conflict_stats(free, occupied, gt_free_eff, gt_occ, gt_unknown)


def corrected_arrays(sample: np.lib.npyio.NpzFile) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    observed_occupied = sample["observed_occupied"].astype(bool)
    observed_free = remove_endpoint_margin_from_free(sample["observed_free"], observed_occupied, ENDPOINT_MARGIN_VOX)
    observed_free &= ~observed_occupied
    unknown_mask = unknown_from_observed(observed_free, observed_occupied)
    frontier_mask = frontier_from_free_unknown(observed_free, unknown_mask, FRONTIER_CONNECTIVITY)
    return (
        observed_free.astype(np.uint8),
        observed_occupied.astype(np.uint8),
        unknown_mask.astype(np.uint8),
        frontier_mask.astype(np.uint8),
    )


def evaluate_corrected_quality(
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
    unknown_mask: np.ndarray,
    frontier_mask: np.ndarray,
    full_occupancy: np.ndarray,
    gt_masks: dict[str, np.ndarray],
    partial_source: str,
) -> tuple[str, list[str], dict[str, float | int]]:
    flags: list[str] = []
    status = "pass"
    expected_shape = full_occupancy.shape
    for name, arr in [
        ("observed_free", observed_free),
        ("observed_occupied", observed_occupied),
        ("unknown_mask", unknown_mask),
        ("frontier_mask", frontier_mask),
        ("gt_free", gt_masks["gt_free"]),
        ("gt_occupied", gt_masks["gt_occupied"]),
        ("gt_unknown", gt_masks["gt_unknown"]),
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
    if full_occupancy.sum() == 0:
        flags.append("full_occupancy_occupied_count_zero")
        if status != "reject":
            status = "warning"
    if overlap_count(observed_free, observed_occupied) > 0:
        flags.append("observed_free_overlaps_observed_occupied")
        status = "reject"
    if partial_source != PARTIAL_SOURCE:
        flags.append("partial_3d_source_not_real_depth_raycast")
        status = "reject"
    if frontier_mask.sum() == 0:
        flags.append("frontier_mask_all_zero")
        if status != "reject":
            status = "warning"
    if observed_occupied.sum() == 0:
        flags.append("observed_occupied_count_zero")
        if status != "reject":
            status = "warning"
    if observed_free.sum() < 64:
        flags.append("low_observed_free_count")
        if status != "reject":
            status = "warning"

    stats = true_conflict_with_options(
        observed_free,
        observed_occupied,
        gt_masks["gt_free"],
        gt_masks["gt_occupied"],
        gt_masks["gt_unknown"],
        dilation_radius_vox=DILATION_RADIUS_VOX,
        endpoint_margin_vox=0,
    )
    if float(stats["true_conflict_ratio"]) > 0.2:
        flags.append("severe_true_gt_observed_conflict_ratio")
        status = "reject"
    elif float(stats["true_conflict_ratio"]) > 0.1 and status != "reject":
        flags.append("true_gt_observed_conflict_ratio_warning")
        status = "warning"
    return status, flags, stats


def diagnostic_option_grid(records: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for dilation in (0, 1, 2):
        for margin in (0, 1, 2):
            key = f"dilation_{dilation}_endpoint_margin_{margin}"
            vals = [r[f"true_conflict_d{dilation}_m{margin}"] for r in records]
            out[key] = {
                "true_conflict_ratio": count_distribution(vals),
                "reject_count_at_0_2": int(sum(float(v) > 0.2 for v in vals)),
            }
    return out


def select_debug_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_sample: dict[str, dict[str, Any]] = {}
    for rec in sorted(records, key=lambda r: float(r["old_conflict_ratio"]), reverse=True)[:20]:
        by_sample[rec["sample_id"]] = rec
    for rec in sorted(records, key=lambda r: float(r["old_conflict_ratio"]))[:10]:
        by_sample[rec["sample_id"]] = rec
    for scene_id in sorted({r["scene_id"] for r in records}):
        scene_records = [r for r in records if r["scene_id"] == scene_id]
        for rec in sorted(scene_records, key=lambda r: float(r["true_conflict_ratio_after"]), reverse=True)[:4]:
            by_sample[rec["sample_id"]] = rec
    return list(by_sample.values())


def save_debug_images(
    sample_path: Path,
    gt_masks: dict[str, np.ndarray],
    record: dict[str, Any],
    out_dir: Path,
) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    z = np.load(sample_path, allow_pickle=True)
    observed_free, observed_occupied, _unknown, _frontier = corrected_arrays(z)
    gt_occ = gt_masks["gt_occupied"].astype(bool)
    gt_free = gt_masks["gt_free"].astype(bool)
    occ_conflict = observed_occupied.astype(bool) & gt_free
    free_conflict = observed_free.astype(bool) & gt_occ
    conflict = occ_conflict.astype(np.uint8) + free_conflict.astype(np.uint8) * 2
    basename = str(record["sample_id"])

    panels = [
        ("observed_occupied", observed_occupied.max(axis=0), "magma"),
        ("observed_free", observed_free.max(axis=0), "viridis"),
        ("full_occupancy", gt_occ.max(axis=0), "gray_r"),
        ("true_conflict_map", conflict.max(axis=0), "plasma"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(9, 8))
    for ax, (name, image, cmap) in zip(axes.ravel(), panels):
        ax.imshow(image, origin="lower", cmap=cmap)
        ax.set_title(name)
        ax.axis("off")
    fig.suptitle(f"{basename} conflict={record['true_conflict_ratio_after']:.4f}")
    fig.tight_layout()
    path = out_dir / f"{basename}_bev_overlay.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    paths.append(str(path))

    z_indices = sorted({0, observed_occupied.shape[0] // 3, (2 * observed_occupied.shape[0]) // 3, observed_occupied.shape[0] - 1})
    fig, axes = plt.subplots(3, len(z_indices), figsize=(4 * len(z_indices), 9))
    if len(z_indices) == 1:
        axes = np.asarray(axes).reshape(3, 1)
    for idx, zidx in enumerate(z_indices):
        axes[0, idx].imshow(observed_occupied[zidx], origin="lower", cmap="magma")
        axes[0, idx].set_title(f"obs_occ z={zidx}")
        axes[0, idx].axis("off")
        axes[1, idx].imshow(gt_occ[zidx], origin="lower", cmap="gray_r")
        axes[1, idx].set_title(f"gt_occ z={zidx}")
        axes[1, idx].axis("off")
        axes[2, idx].imshow(conflict[zidx], origin="lower", cmap="plasma")
        axes[2, idx].set_title(f"conflict z={zidx}")
        axes[2, idx].axis("off")
    fig.tight_layout()
    z_path = out_dir / f"{basename}_z_slice_overlays.png"
    fig.savefig(z_path, dpi=120)
    plt.close(fig)
    paths.append(str(z_path))
    return paths


def split_samples(records: list[dict[str, Any]]) -> tuple[dict[str, list[str]], dict[str, Any]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for rec in records:
        groups[f"{rec['scene_id']}::start_{int(rec['start_id']):03d}"].append(rec["relative_path"])
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


def clear_output_dataset(dataset_root: Path) -> None:
    if DATA_ROOT not in dataset_root.parents:
        raise ValueError(f"refusing to remove unexpected dataset path: {dataset_root}")
    if dataset_root.exists():
        shutil.rmtree(dataset_root)
    dataset_root.mkdir(parents=True, exist_ok=True)


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(r["quality_status"] for r in records)
    flags = Counter(flag for r in records for flag in r["quality_flags"])
    return {
        "sample_count": len(records),
        "pass_count": int(status_counts.get("pass", 0)),
        "warning_count": int(status_counts.get("warning", 0)),
        "reject_count": int(status_counts.get("reject", 0)),
        "quality_flag_counts": dict(sorted(flags.items())),
        "observed_occupied_zero_rate": round(zero_rate(r["observed_occupied_count"] for r in records), 6),
        "frontier_empty_rate": round(zero_rate(r["frontier_count"] for r in records), 6),
        "observed_free_count": count_distribution(r["observed_free_count"] for r in records),
        "observed_occupied_count": count_distribution(r["observed_occupied_count"] for r in records),
        "unknown_count": count_distribution(r["unknown_count"] for r in records),
        "frontier_count": count_distribution(r["frontier_count"] for r in records),
        "full_occupancy_occupied_count": count_distribution(r["full_occupancy_occupied_count"] for r in records),
        "old_conflict_ratio": count_distribution(r["old_conflict_ratio"] for r in records),
        "true_conflict_ratio_before": count_distribution(r["true_conflict_ratio_before"] for r in records),
        "true_conflict_ratio_after": count_distribution(r["true_conflict_ratio_after"] for r in records),
        "observed_occ_in_gt_unknown_ratio": count_distribution(r["observed_occ_in_gt_unknown_ratio"] for r in records),
        "observed_free_overlaps_occupied": int(sum(r["observed_free_overlaps_occupied"] for r in records)),
    }


def save_corrected_npz(
    source_path: Path,
    out_path: Path,
    arrays: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
    gt_masks: dict[str, np.ndarray],
    quality_status: str,
    quality_flags: list[str],
    record: dict[str, Any],
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    z = np.load(source_path, allow_pickle=True)
    payload: dict[str, Any] = {key: z[key] for key in z.files}
    observed_free, observed_occupied, unknown_mask, frontier_mask = arrays
    payload.update(
        {
            "observed_free": observed_free.astype(np.uint8),
            "observed_occupied": observed_occupied.astype(np.uint8),
            "unknown_mask": unknown_mask.astype(np.uint8),
            "frontier_mask": frontier_mask.astype(np.uint8),
            "gt_free_mask": gt_masks["gt_free"].astype(np.uint8),
            "gt_unknown_mask": gt_masks["gt_unknown"].astype(np.uint8),
            "gt_observed_mask": gt_masks["gt_observed"].astype(np.uint8),
            "quality_status": np.asarray(quality_status),
            "quality_flags": np.asarray(json.dumps(quality_flags, sort_keys=True)),
            "source_dataset": np.asarray(SOURCE_DATASET_NAME),
            "source_sample_path": np.asarray(str(source_path)),
            "dataset_version": np.asarray(CORRECTED_DATASET_NAME),
            "axis_order_convention": np.asarray(AXIS_ORDER),
            "dilation_radius_vox": np.asarray(DILATION_RADIUS_VOX, dtype=np.int32),
            "endpoint_margin_vox": np.asarray(ENDPOINT_MARGIN_VOX, dtype=np.int32),
            "old_conflict_ratio": np.asarray(record["old_conflict_ratio"], dtype=np.float32),
            "true_conflict_ratio": np.asarray(record["true_conflict_ratio_after"], dtype=np.float32),
            "observed_occ_in_gt_unknown_ratio": np.asarray(record["observed_occ_in_gt_unknown_ratio"], dtype=np.float32),
        }
    )
    np.savez_compressed(out_path, **payload)


def write_csv_summary(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "scene_id",
        "relative_path",
        "start_id",
        "step_id",
        "quality_status",
        "quality_flags_text",
        "old_conflict_ratio",
        "true_conflict_ratio_before",
        "true_conflict_ratio_after",
        "observed_occ_in_gt_free_ratio",
        "observed_occ_in_gt_unknown_ratio",
        "observed_free_in_gt_occ_ratio",
        "observed_occupied_count",
        "observed_free_count",
        "unknown_count",
        "frontier_count",
        "full_occupancy_occupied_count",
        "gt_unknown_ratio_in_crop",
        "crop_origin_x",
        "crop_origin_y",
        "crop_origin_z",
        "crop_center_x",
        "crop_center_y",
        "crop_center_z",
        "voxel_size",
        "shape",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            row = dict(rec)
            row["quality_flags_text"] = ";".join(rec["quality_flags"])
            row["shape"] = "x".join(str(v) for v in rec["shape"])
            writer.writerow(row)


def write_report(summary: dict[str, Any]) -> None:
    q = summary["corrected_quality_summary"]
    lines = [
        "# MapPredict Phase 2.6 Alignment Debug Report",
        "",
        "phase: MapPredict Phase 2.6",
        "purpose: diagnose and fix real partial 3D vs dense_scan_pseudo_gt alignment conflicts",
        f"workspace: {summary['workspace']}",
        f"project_name: {summary['project_name']}",
        f"main_goal: {summary['main_goal']}",
        "map_predict_role: feature_provider",
        "planner: false",
        "VLA: false",
        "training_started: false",
        "map_predict_training_started: false",
        "VLA_training_started: false",
        "SFT_started: false",
        "GDPO_started: false",
        "RL_started: false",
        "",
        "## Phase 2.5 Issue Summary",
        "",
        f"source_dataset: {summary['source_dataset']}",
        f"phase25_sample_count: {summary['phase25_sample_count']}",
        f"phase25_observed_occupied_zero_rate: {summary['phase25_observed_occupied_zero_rate']}",
        f"phase25_reject_count: {summary['phase25_reject_count']}",
        f"phase25_main_reject_reason: {summary['phase25_main_reject_reason']}",
        "",
        "## Diagnostics",
        "",
        f"diagnostic_sample_count: {summary['diagnostic_sample_count']}",
        f"axis_order_convention: {summary['axis_order_convention']}",
        f"round_trip_error_mean: {summary['round_trip_error_mean']}",
        f"round_trip_error_max: {summary['round_trip_error_max']}",
        f"voxel_size_check: {summary['voxel_size_check']}",
        f"gt_voxel_sizes: {summary['gt_voxel_sizes']}",
        f"sample_voxel_sizes: {summary['sample_voxel_sizes']}",
        f"gt_coverage_summary: {summary['gt_coverage_summary']}",
        "",
        "## Conflict Metric Before / After",
        "",
        f"old_conflict_ratio: {q['old_conflict_ratio']}",
        f"true_conflict_ratio_before: {q['true_conflict_ratio_before']}",
        f"true_conflict_ratio_after: {q['true_conflict_ratio_after']}",
        f"observed_occ_in_gt_unknown_ratio: {q['observed_occ_in_gt_unknown_ratio']}",
        f"observed_occupied_zero_rate_before: {summary['phase25_observed_occupied_zero_rate']}",
        f"observed_occupied_zero_rate_after: {q['observed_occupied_zero_rate']}",
        f"reject_count_before: {summary['phase25_reject_count']}",
        f"reject_count_after: {q['reject_count']}",
        "",
        "## Main Conflict Cause",
        "",
        "main_conflict_cause: Phase 2.5 treated dense_scan_pseudo_gt unknown voxels as negative evidence.",
        "true_conflict_definition: observed_occupied & gt_free OR observed_free & gt_occupied",
        "not_conflict: observed_occupied in gt_unknown; observed_free in gt_unknown",
        "",
        "## Fixes Applied",
        "",
        "fix_a_conflict_metric: true",
        "fix_b_axis_transform: no_change_needed",
        f"fix_c_occupied_dilation_radius_vox: {summary['dilation_radius_vox']}",
        f"fix_d_endpoint_margin_vox: {summary['endpoint_margin_vox']}",
        "fix_e_rebuild_dense_scan_gt: not_needed_for_phase26",
        "",
        "## Corrected Dataset",
        "",
        f"corrected_dataset_version: {summary['corrected_dataset_version']}",
        f"corrected_dataset_path: {summary['corrected_dataset_path']}",
        f"sample_count: {q['sample_count']}",
        f"pass_count: {q['pass_count']}",
        f"warning_count: {q['warning_count']}",
        f"reject_count: {q['reject_count']}",
        f"observed_occupied_zero_rate: {q['observed_occupied_zero_rate']}",
        f"gt_observed_conflict_ratio_mean: {summary['gt_observed_conflict_ratio_mean']}",
        f"gt_observed_conflict_ratio_p95: {summary['gt_observed_conflict_ratio_p95']}",
        f"quality_flag_counts: {q['quality_flag_counts']}",
        f"split_summary: {summary['split_summary']}",
        "",
        "## Visualization Paths",
        "",
    ]
    if summary["visualization_paths"]:
        lines.extend(f"* {path}" for path in summary["visualization_paths"][:80])
    else:
        lines.append("* none")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"safe_to_train_3d_unet_baseline: {bool_text(summary['safe_to_train_3d_unet_baseline'])}",
            "training_ready: false",
            "requires_review: true",
            f"next_phase: {summary['next_phase']}",
            "",
            "## Notes",
            "",
            "* dense_scan_pseudo_gt remains pseudo GT, not perfect ground truth.",
            "* v2 does not overwrite v1.",
            "* corrected samples and debug images are kept in ignored paths.",
            "* no model training, SFT, GDPO, RL, rollout, or USD mutation was performed.",
        ]
    )
    TOP_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run_report = Path(summary["run_dir"]) / "reports" / TOP_REPORT.name
    run_report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--source-dataset", default=SOURCE_DATASET_NAME)
    parser.add_argument("--corrected-dataset", default=CORRECTED_DATASET_NAME)
    parser.add_argument("--max-debug-images", type=int, default=40)
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.run_dir) if args.run_dir else RUNS_DIR / f"map_predict_phase26_alignment_debug_{timestamp}"
    for rel in ["logs", "diagnostics", "reports", "summary", "plots", "debug_samples", "overlays"]:
        (run_dir / rel).mkdir(parents=True, exist_ok=True)

    source_root = DATA_ROOT / args.source_dataset
    corrected_root = DATA_ROOT / args.corrected_dataset
    clear_output_dataset(corrected_root)
    source_manifest = load_v1_manifest(source_root)
    paths = sample_paths(source_root)
    scenes = sorted({path.parent.name for path in paths})
    gts = {scene_id: load_gt(scene_id) for scene_id in scenes}

    records: list[dict[str, Any]] = []
    round_trip: list[float] = []
    sample_voxel_sizes: list[float] = []
    gt_voxel_sizes = sorted({round(gt.voxel_size, 8) for gt in gts.values()})

    for source_path in paths:
        sample = np.load(source_path, allow_pickle=True)
        scene_id = str(sample["scene_id"].item())
        gt = gts[scene_id]
        gt_masks = crop_gt_masks(sample, gt)
        observed_free_raw = sample["observed_free"].astype(np.uint8)
        observed_occupied = sample["observed_occupied"].astype(np.uint8)
        old_conflict = observed_gt_conflict_ratio(observed_occupied, sample["full_occupancy"])
        before = true_conflict_with_options(
            observed_free_raw,
            observed_occupied,
            gt_masks["gt_free"],
            gt_masks["gt_occupied"],
            gt_masks["gt_unknown"],
            dilation_radius_vox=0,
            endpoint_margin_vox=0,
        )
        option_values: dict[str, float] = {}
        for dilation in (0, 1, 2):
            for margin in (0, 1, 2):
                option = true_conflict_with_options(
                    observed_free_raw,
                    observed_occupied,
                    gt_masks["gt_free"],
                    gt_masks["gt_occupied"],
                    gt_masks["gt_unknown"],
                    dilation_radius_vox=dilation,
                    endpoint_margin_vox=margin,
                )
                option_values[f"true_conflict_d{dilation}_m{margin}"] = float(option["true_conflict_ratio"])

        arrays = corrected_arrays(sample)
        quality_status, quality_flags, after = evaluate_corrected_quality(
            arrays[0],
            arrays[1],
            arrays[2],
            arrays[3],
            sample["full_occupancy"],
            gt_masks,
            str(sample["partial_3d_source"].item()),
        )
        rel_path = Path(scene_id) / source_path.name
        crop_origin = [float(x) for x in sample["crop_origin_xyz"]]
        crop_center = [float(x) for x in sample["crop_center_xyz"]]
        record = {
            "sample_id": str(sample["sample_id"].item()),
            "scene_id": scene_id,
            "relative_path": str(rel_path),
            "source_sample_path": str(source_path),
            "start_id": int(sample["start_id"]),
            "step_id": int(sample["step_id"]),
            "quality_status": quality_status,
            "quality_flags": quality_flags,
            "old_conflict_ratio": float(old_conflict),
            "true_conflict_ratio_before": float(before["true_conflict_ratio"]),
            "true_conflict_ratio_after": float(after["true_conflict_ratio"]),
            "observed_occ_in_gt_free_ratio": float(after["observed_occ_in_gt_free_ratio"]),
            "observed_occ_in_gt_unknown_ratio": float(after["observed_occ_in_gt_unknown_ratio"]),
            "observed_free_in_gt_occ_ratio": float(after["observed_free_in_gt_occ_ratio"]),
            "observed_occupied_count": int(arrays[1].sum()),
            "observed_free_count": int(arrays[0].sum()),
            "unknown_count": int(arrays[2].sum()),
            "frontier_count": int(arrays[3].sum()),
            "full_occupancy_occupied_count": int(sample["full_occupancy"].sum()),
            "gt_unknown_ratio_in_crop": float(gt_masks["gt_unknown"].sum() / gt_masks["gt_unknown"].size),
            "observed_free_overlaps_occupied": overlap_count(arrays[0], arrays[1]),
            "crop_origin_x": crop_origin[0],
            "crop_origin_y": crop_origin[1],
            "crop_origin_z": crop_origin[2],
            "crop_center_x": crop_center[0],
            "crop_center_y": crop_center[1],
            "crop_center_z": crop_center[2],
            "voxel_size": float(sample["voxel_size"]),
            "shape": list(arrays[0].shape),
            **option_values,
        }
        out_path = corrected_root / rel_path
        save_corrected_npz(source_path, out_path, arrays, gt_masks, quality_status, quality_flags, record)
        records.append(record)
        sample_voxel_sizes.append(round(float(sample["voxel_size"]), 8))
        round_trip.extend(round_trip_errors(sample))

    split_summary = write_splits(corrected_root, records)
    quality_summary = summarize_records(records)
    option_summary = diagnostic_option_grid(records)
    selected = select_debug_records(records)
    visualization_paths: list[str] = []
    selected_by_id = {rec["sample_id"]: rec for rec in selected[: int(args.max_debug_images)]}
    for record in selected_by_id.values():
        source_path = Path(record["source_sample_path"])
        sample = np.load(source_path, allow_pickle=True)
        gt_masks = crop_gt_masks(sample, gts[record["scene_id"]])
        visualization_paths.extend(
            save_debug_images(source_path, gt_masks, record, run_dir / "overlays" / record["scene_id"])
        )

    diagnostics_csv = run_dir / "diagnostics/alignment_conflict_summary.csv"
    diagnostics_json = run_dir / "diagnostics/alignment_conflict_summary.json"
    write_csv_summary(diagnostics_csv, records)
    write_json(diagnostics_json, {"records": records, "option_summary": option_summary})
    write_json(run_dir / "summary/debug_selected_samples.json", {"selected_samples": selected})

    conflict_after = quality_summary["true_conflict_ratio_after"]
    phase25_reject_count = int(source_manifest.get("reject_count") or source_manifest.get("quality_summary", {}).get("reject_count") or 0)
    observed_zero_after = float(quality_summary["observed_occupied_zero_rate"])
    reject_count_after = int(quality_summary["reject_count"])
    sample_count = int(quality_summary["sample_count"])
    round_trip_mean = float(np.mean(round_trip)) if round_trip else 0.0
    round_trip_max = float(np.max(round_trip)) if round_trip else 0.0
    voxel_size_check = "pass" if len(set(sample_voxel_sizes)) == 1 and len(gt_voxel_sizes) == 1 and abs(sample_voxel_sizes[0] - gt_voxel_sizes[0]) < 1e-5 else "mismatch"
    safe_to_train = bool(
        sample_count > 0
        and reject_count_after / sample_count < 0.2
        and observed_zero_after <= 0.05
        and round_trip_max <= max(1e-6, sample_voxel_sizes[0] * 0.5 + 1e-6)
        and float(conflict_after["mean"] or 1.0) < 0.08
        and float(conflict_after["p95"] or 1.0) < 0.15
        and quality_summary["observed_free_overlaps_occupied"] == 0
    )
    next_phase = (
        "MapPredict Phase 3 3D U-Net occupancy completion baseline"
        if safe_to_train
        else "MapPredict Phase 1.5 rebuild dense_scan_pseudo_gt with higher coverage"
    )

    manifest = {
        "dataset_name": args.corrected_dataset,
        "source_dataset": args.source_dataset,
        "gt_type": GT_TYPE,
        "partial_3d_source": PARTIAL_SOURCE,
        "axis_order_convention": AXIS_ORDER,
        "voxel_size": float(sample_voxel_sizes[0]) if sample_voxel_sizes else 0.0,
        "sample_count": sample_count,
        "pass_count": int(quality_summary["pass_count"]),
        "warning_count": int(quality_summary["warning_count"]),
        "reject_count": reject_count_after,
        "observed_occupied_zero_rate": observed_zero_after,
        "gt_observed_conflict_ratio_mean": float(conflict_after["mean"] or 0.0),
        "gt_observed_conflict_ratio_p95": float(conflict_after["p95"] or 0.0),
        "dilation_radius_vox": DILATION_RADIUS_VOX,
        "endpoint_margin_vox": ENDPOINT_MARGIN_VOX,
        "training_ready": False,
        "requires_review": True,
        "safe_to_train_3d_unet_baseline": safe_to_train,
        "quality_summary": quality_summary,
        "split_summary": split_summary,
    }
    write_json(corrected_root / "dataset_manifest.json", manifest)
    write_json(corrected_root / "quality_summary.json", quality_summary)
    with (corrected_root / "sample_index.jsonl").open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True) + "\n")

    gt_coverage = {}
    for scene_id, gt in gts.items():
        total = int(gt.occupied_mask.size)
        gt_coverage[scene_id] = {
            "occupied_count": int(gt.occupied_mask.sum()),
            "free_count": int(gt.free_mask.sum()),
            "unknown_count": int(gt.unknown_mask.sum()),
            "observed_mask_coverage": float(gt.observed_mask.sum() / total) if total else 0.0,
        }

    summary = {
        "phase": PHASE,
        "workspace": str(WORKSPACE),
        "project_name": PROJECT,
        "main_goal": GOAL,
        "run_dir": str(run_dir),
        "source_dataset": args.source_dataset,
        "source_dataset_path": str(source_root),
        "corrected_dataset_version": args.corrected_dataset,
        "corrected_dataset_path": str(corrected_root),
        "phase25_sample_count": int(source_manifest.get("sample_count") or source_manifest.get("quality_summary", {}).get("sample_count") or 0),
        "phase25_observed_occupied_zero_rate": float(source_manifest.get("observed_occupied_zero_rate") or source_manifest.get("quality_summary", {}).get("observed_occupied_zero_rate") or 0.0),
        "phase25_reject_count": phase25_reject_count,
        "phase25_main_reject_reason": "severe_gt_observed_conflict_ratio",
        "diagnostic_sample_count": len(selected),
        "axis_order_convention": AXIS_ORDER,
        "round_trip_error_mean": round_trip_mean,
        "round_trip_error_max": round_trip_max,
        "voxel_size_check": voxel_size_check,
        "gt_voxel_sizes": gt_voxel_sizes,
        "sample_voxel_sizes": sorted(set(sample_voxel_sizes)),
        "gt_coverage_summary": gt_coverage,
        "option_summary": option_summary,
        "dilation_radius_vox": DILATION_RADIUS_VOX,
        "endpoint_margin_vox": ENDPOINT_MARGIN_VOX,
        "corrected_quality_summary": quality_summary,
        "gt_observed_conflict_ratio_mean": float(conflict_after["mean"] or 0.0),
        "gt_observed_conflict_ratio_p95": float(conflict_after["p95"] or 0.0),
        "split_summary": split_summary,
        "visualization_paths": visualization_paths,
        "diagnostics_csv": str(diagnostics_csv),
        "diagnostics_json": str(diagnostics_json),
        "training_started": False,
        "map_predict_training_started": False,
        "VLA_training_started": False,
        "SFT_started": False,
        "GDPO_started": False,
        "RL_started": False,
        "safe_to_train_3d_unet_baseline": safe_to_train,
        "training_ready": False,
        "requires_review": True,
        "next_phase": next_phase,
    }
    write_json(run_dir / "summary/phase26_alignment_debug_summary.json", summary)
    write_json(run_dir / "summary/local_voxel_v2_aligned_manifest.json", manifest)
    write_report(summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if safe_to_train else 2


if __name__ == "__main__":
    raise SystemExit(main())
