"""Metrics for occupancy completion and feature-provider evaluation."""

from __future__ import annotations

from typing import Iterable

import numpy as np


def binary_iou(pred: np.ndarray, target: np.ndarray) -> float:
    p = np.asarray(pred, dtype=bool)
    t = np.asarray(target, dtype=bool)
    intersection = np.logical_and(p, t).sum()
    union = np.logical_or(p, t).sum()
    return float(intersection / union) if union else 1.0


def precision_recall(pred: np.ndarray, target: np.ndarray) -> tuple[float, float]:
    p = np.asarray(pred, dtype=bool)
    t = np.asarray(target, dtype=bool)
    tp = np.logical_and(p, t).sum()
    fp = np.logical_and(p, ~t).sum()
    fn = np.logical_and(~p, t).sum()
    precision = float(tp / (tp + fp)) if tp + fp else 1.0
    recall = float(tp / (tp + fn)) if tp + fn else 1.0
    return precision, recall


def unknown_region_iou(pred: np.ndarray, target: np.ndarray, unknown_mask: np.ndarray) -> float:
    mask = np.asarray(unknown_mask, dtype=bool)
    return binary_iou(np.asarray(pred)[mask], np.asarray(target)[mask])


def binary_cross_entropy_prob(prob: np.ndarray, target: np.ndarray, mask: np.ndarray | None = None) -> float:
    p = np.asarray(prob, dtype=np.float64)
    t = np.asarray(target, dtype=np.float64)
    if mask is not None:
        m = np.asarray(mask, dtype=bool)
        p = p[m]
        t = t[m]
    if p.size == 0:
        return 0.0
    p = np.clip(p, 1e-6, 1.0 - 1e-6)
    return float(np.mean(-(t * np.log(p) + (1.0 - t) * np.log(1.0 - p))))


def observed_consistency_error(
    pred_occ: np.ndarray,
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
) -> float:
    pred = np.asarray(pred_occ, dtype=bool)
    free = np.asarray(observed_free, dtype=bool)
    occupied = np.asarray(observed_occupied, dtype=bool)
    errors = 0
    total = int(free.sum() + occupied.sum())
    if total == 0:
        return 0.0
    errors += int(np.logical_and(pred, free).sum())
    errors += int(np.logical_and(~pred, occupied).sum())
    return float(errors / total)


def masked_binary_stats(pred_occ: np.ndarray, gt_occ: np.ndarray, mask: np.ndarray) -> dict[str, float]:
    m = np.asarray(mask, dtype=bool)
    if m.sum() == 0:
        return {"iou": 1.0, "precision": 1.0, "recall": 1.0}
    pred = np.asarray(pred_occ, dtype=bool)[m]
    gt = np.asarray(gt_occ, dtype=bool)[m]
    precision, recall = precision_recall(pred, gt)
    return {"iou": binary_iou(pred, gt), "precision": precision, "recall": recall}


def occupancy_completion_metrics(
    pred_prob: np.ndarray,
    full_occupancy: np.ndarray,
    unknown_mask: np.ndarray,
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
    *,
    threshold: float = 0.5,
) -> dict[str, float]:
    """Compute Phase 3 validation metrics for one sample."""

    prob = np.asarray(pred_prob, dtype=np.float32)
    gt = np.asarray(full_occupancy, dtype=bool)
    unknown = np.asarray(unknown_mask, dtype=bool)
    pred_occ = prob > float(threshold)
    unknown_stats = masked_binary_stats(pred_occ, gt, unknown)
    full_stats = masked_binary_stats(pred_occ, gt, np.ones_like(gt, dtype=bool))
    naive_free_prob = np.zeros_like(prob, dtype=np.float32)
    naive_occ_prob = np.ones_like(prob, dtype=np.float32)
    naive_free_occ = np.zeros_like(gt, dtype=bool)
    naive_occ_occ = np.ones_like(gt, dtype=bool)
    return {
        "unknown_region_bce": binary_cross_entropy_prob(prob, gt.astype(np.float32), unknown),
        "unknown_region_iou": unknown_stats["iou"],
        "unknown_region_precision": unknown_stats["precision"],
        "unknown_region_recall": unknown_stats["recall"],
        "observed_consistency_error": observed_consistency_error(pred_occ, observed_free, observed_occupied),
        "full_crop_iou": full_stats["iou"],
        "naive_all_free_iou": masked_binary_stats(naive_free_occ, gt, unknown)["iou"],
        "naive_all_occupied_iou": masked_binary_stats(naive_occ_occ, gt, unknown)["iou"],
        "naive_all_free_bce": binary_cross_entropy_prob(naive_free_prob, gt.astype(np.float32), unknown),
        "naive_all_occupied_bce": binary_cross_entropy_prob(naive_occ_prob, gt.astype(np.float32), unknown),
    }


def uncertainty_evaluation_metrics(
    uncertainty: np.ndarray,
    unknown_mask: np.ndarray,
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
    pred_prob: np.ndarray,
    full_occupancy: np.ndarray,
) -> dict[str, float]:
    """Compute Phase 4 uncertainty and basic entropy calibration metrics."""

    unc = np.asarray(uncertainty, dtype=np.float32)
    unknown = np.asarray(unknown_mask, dtype=bool)
    observed = np.asarray(observed_free, dtype=bool) | np.asarray(observed_occupied, dtype=bool)
    mean_unknown = float(unc[unknown].mean()) if unknown.any() else 0.0
    mean_observed = float(unc[observed].mean()) if observed.any() else 0.0
    pred_occ = np.asarray(pred_prob, dtype=np.float32) > 0.5
    gt_occ = np.asarray(full_occupancy, dtype=bool)
    error_unknown = np.logical_xor(pred_occ, gt_occ) & unknown
    correct_unknown = ~np.logical_xor(pred_occ, gt_occ) & unknown
    error_unc = float(unc[error_unknown].mean()) if error_unknown.any() else 0.0
    correct_unc = float(unc[correct_unknown].mean()) if correct_unknown.any() else 0.0
    return {
        "uncertainty_mean_unknown": mean_unknown,
        "uncertainty_mean_observed": mean_observed,
        "uncertainty_observed_gap": mean_unknown - mean_observed,
        "entropy_calibration_basic": error_unc - correct_unc,
        "uncertainty_mean_error_unknown": error_unc,
        "uncertainty_mean_correct_unknown": correct_unc,
    }


def observed_gt_conflict_ratio(observed_occupied: np.ndarray, full_occupancy: np.ndarray) -> float:
    """Return fraction of observed occupied voxels absent from full occupancy."""

    observed = np.asarray(observed_occupied, dtype=bool)
    if observed.sum() == 0:
        return 0.0
    full = np.asarray(full_occupancy, dtype=bool)
    return float(np.logical_and(observed, ~full).sum() / observed.sum())


def binary_dilation_3d(mask: np.ndarray, radius: int = 1, connectivity: int = 26) -> np.ndarray:
    """Return a small pure-numpy 3D binary dilation."""

    if connectivity not in (6, 26):
        raise ValueError("connectivity must be 6 or 26")
    out = np.asarray(mask, dtype=bool).copy()
    if radius <= 0:
        return out
    offsets: list[tuple[int, int, int]] = []
    for dz in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dz == dy == dx == 0:
                    continue
                if connectivity == 6 and abs(dz) + abs(dy) + abs(dx) != 1:
                    continue
                offsets.append((dz, dy, dx))
    for _ in range(radius):
        expanded = out.copy()
        for dz, dy, dx in offsets:
            shifted = np.zeros_like(out, dtype=bool)
            src_z = slice(max(0, -dz), out.shape[0] - max(0, dz))
            src_y = slice(max(0, -dy), out.shape[1] - max(0, dy))
            src_x = slice(max(0, -dx), out.shape[2] - max(0, dx))
            dst_z = slice(max(0, dz), out.shape[0] - max(0, -dz))
            dst_y = slice(max(0, dy), out.shape[1] - max(0, -dy))
            dst_x = slice(max(0, dx), out.shape[2] - max(0, -dx))
            shifted[dst_z, dst_y, dst_x] = out[src_z, src_y, src_x]
            expanded |= shifted
        out = expanded
    return out


def remove_endpoint_margin_from_free(
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
    endpoint_margin_vox: int = 1,
) -> np.ndarray:
    """Conservatively remove free voxels adjacent to occupied endpoints."""

    free = np.asarray(observed_free, dtype=bool)
    if endpoint_margin_vox <= 0:
        return free.copy()
    occupied_margin = binary_dilation_3d(observed_occupied, endpoint_margin_vox, connectivity=26)
    return free & ~occupied_margin


def true_observed_gt_conflict_stats(
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
    gt_free_mask: np.ndarray,
    gt_occupied_mask: np.ndarray,
    gt_unknown_mask: np.ndarray | None = None,
) -> dict[str, float | int]:
    """Compare partial observations only against known pseudo-GT evidence.

    Occupied observations in GT unknown space are not conflicts. Free
    observations in GT unknown space are not conflicts either. Conflicts are only
    observed occupied inside GT known free, or observed free inside GT occupied.
    """

    free = np.asarray(observed_free, dtype=bool)
    occupied = np.asarray(observed_occupied, dtype=bool)
    gt_free = np.asarray(gt_free_mask, dtype=bool)
    gt_occupied = np.asarray(gt_occupied_mask, dtype=bool)
    if gt_unknown_mask is None:
        gt_unknown = ~(gt_free | gt_occupied)
    else:
        gt_unknown = np.asarray(gt_unknown_mask, dtype=bool)
    occ_in_gt_free = np.logical_and(occupied, gt_free)
    free_in_gt_occ = np.logical_and(free, gt_occupied)
    occ_in_gt_unknown = np.logical_and(occupied, gt_unknown)
    free_in_gt_unknown = np.logical_and(free, gt_unknown)
    observed_total = int(free.sum() + occupied.sum())
    occupied_total = int(occupied.sum())
    free_total = int(free.sum())
    conflict_count = int(occ_in_gt_free.sum() + free_in_gt_occ.sum())
    return {
        "true_conflict_count": conflict_count,
        "true_conflict_ratio": float(conflict_count / observed_total) if observed_total else 0.0,
        "observed_total": observed_total,
        "observed_occupied_count": occupied_total,
        "observed_free_count": free_total,
        "observed_occ_in_gt_free_count": int(occ_in_gt_free.sum()),
        "observed_free_in_gt_occ_count": int(free_in_gt_occ.sum()),
        "observed_occ_in_gt_unknown_count": int(occ_in_gt_unknown.sum()),
        "observed_free_in_gt_unknown_count": int(free_in_gt_unknown.sum()),
        "observed_occ_in_gt_free_ratio": float(occ_in_gt_free.sum() / occupied_total) if occupied_total else 0.0,
        "observed_free_in_gt_occ_ratio": float(free_in_gt_occ.sum() / free_total) if free_total else 0.0,
        "observed_occ_in_gt_unknown_ratio": float(occ_in_gt_unknown.sum() / occupied_total) if occupied_total else 0.0,
    }


def overlap_count(left: np.ndarray, right: np.ndarray) -> int:
    """Return the number of voxels set in both binary arrays."""

    return int(np.logical_and(np.asarray(left, dtype=bool), np.asarray(right, dtype=bool)).sum())


def zero_rate(values: Iterable[int | float]) -> float:
    arr = np.asarray(list(values), dtype=np.float64)
    if arr.size == 0:
        return 0.0
    return float(np.count_nonzero(arr == 0) / arr.size)


def count_distribution(values: Iterable[int | float]) -> dict[str, float | int | None]:
    arr = np.asarray(list(values), dtype=np.float64)
    if arr.size == 0:
        return {"count": 0, "min": None, "max": None, "mean": None, "p50": None, "p90": None}
    return {
        "count": int(arr.size),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "mean": float(arr.mean()),
        "p50": float(np.percentile(arr, 50)),
        "p90": float(np.percentile(arr, 90)),
        "p95": float(np.percentile(arr, 95)),
    }
