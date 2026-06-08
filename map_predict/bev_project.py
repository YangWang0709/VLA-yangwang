"""Project 3D occupancy predictions into BEV feature maps."""

from __future__ import annotations

import numpy as np


def occupancy_to_bev(occupancy: np.ndarray, mode: str = "max") -> np.ndarray:
    grid = np.asarray(occupancy)
    if grid.ndim != 3:
        raise ValueError(f"occupancy must be [D, H, W], got {grid.shape}")
    if mode == "max":
        return grid.max(axis=0)
    if mode == "mean":
        return grid.mean(axis=0)
    if mode == "sum":
        return grid.sum(axis=0)
    if mode == "probabilistic_union":
        return 1.0 - np.prod(1.0 - np.clip(grid, 0.0, 1.0), axis=0)
    raise ValueError(f"unsupported BEV projection mode: {mode}")


def uncertainty_to_bev(
    uncertainty: np.ndarray,
    unknown_mask: np.ndarray | None = None,
    mode: str = "max",
) -> np.ndarray:
    grid = np.asarray(uncertainty, dtype=np.float32)
    if grid.ndim != 3:
        raise ValueError(f"uncertainty must be [D, H, W], got {grid.shape}")
    if mode == "max":
        return grid.max(axis=0)
    if mode == "mean":
        return grid.mean(axis=0)
    if mode == "mean_unknown_z":
        if unknown_mask is None:
            return grid.mean(axis=0)
        unknown = np.asarray(unknown_mask, dtype=bool)
        denom = unknown.sum(axis=0)
        weighted = (grid * unknown.astype(np.float32)).sum(axis=0)
        out = np.zeros_like(weighted, dtype=np.float32)
        np.divide(weighted, denom, out=out, where=denom > 0)
        return out
    raise ValueError(f"unsupported uncertainty BEV projection mode: {mode}")


def binary_to_bev(mask: np.ndarray, mode: str = "any") -> np.ndarray:
    grid = np.asarray(mask, dtype=bool)
    if grid.ndim != 3:
        raise ValueError(f"mask must be [D, H, W], got {grid.shape}")
    if mode == "any":
        return grid.any(axis=0)
    if mode == "all":
        return grid.all(axis=0)
    if mode == "count":
        return grid.sum(axis=0)
    raise ValueError(f"unsupported binary BEV projection mode: {mode}")


def project_prediction_to_bev(
    pred_occ_prob: np.ndarray,
    uncertainty: np.ndarray,
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
    unknown_mask: np.ndarray,
    *,
    occ_projection: str = "max",
    uncertainty_projection: str = "max",
) -> dict[str, np.ndarray]:
    """Project a 3D occupancy prediction and masks into BEV feature maps."""

    return {
        "bev_pred_occ": occupancy_to_bev(pred_occ_prob, mode=occ_projection).astype(np.float32),
        "bev_uncertainty": uncertainty_to_bev(uncertainty, unknown_mask, mode=uncertainty_projection).astype(np.float32),
        "bev_observed_free": binary_to_bev(observed_free, mode="any").astype(np.uint8),
        "bev_observed_occupied": binary_to_bev(observed_occupied, mode="any").astype(np.uint8),
        "bev_unknown": binary_to_bev(unknown_mask, mode="any").astype(np.uint8),
    }
