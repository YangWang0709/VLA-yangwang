"""Metrics for occupancy completion and feature-provider evaluation."""

from __future__ import annotations

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
