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


def observed_gt_conflict_ratio(observed_occupied: np.ndarray, full_occupancy: np.ndarray) -> float:
    """Return fraction of observed occupied voxels absent from full occupancy."""

    observed = np.asarray(observed_occupied, dtype=bool)
    if observed.sum() == 0:
        return 0.0
    full = np.asarray(full_occupancy, dtype=bool)
    return float(np.logical_and(observed, ~full).sum() / observed.sum())


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
    }
