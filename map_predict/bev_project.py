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
    raise ValueError(f"unsupported BEV projection mode: {mode}")


def uncertainty_to_bev(uncertainty: np.ndarray) -> np.ndarray:
    return occupancy_to_bev(uncertainty, mode="mean")
