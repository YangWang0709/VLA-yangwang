"""Voxelization helpers for partial 3D occupancy observations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class VoxelGridSpec:
    dims: tuple[int, int, int]
    voxel_size: float
    origin: tuple[float, float, float]

    @property
    def d_hw(self) -> tuple[int, int, int]:
        return self.dims


def world_to_grid(points_xyz: np.ndarray, spec: VoxelGridSpec) -> np.ndarray:
    points = np.asarray(points_xyz, dtype=np.float32)
    origin = np.asarray(spec.origin, dtype=np.float32)
    return np.floor((points - origin) / float(spec.voxel_size)).astype(np.int32)


def voxelize_points(points_xyz: np.ndarray, spec: VoxelGridSpec) -> np.ndarray:
    """Convert points into a boolean occupied grid with shape [D, H, W]."""

    occupied = np.zeros(spec.dims, dtype=bool)
    if points_xyz is None or len(points_xyz) == 0:
        return occupied
    ijk = world_to_grid(points_xyz, spec)
    d, h, w = spec.dims
    mask = (
        (ijk[:, 0] >= 0)
        & (ijk[:, 0] < d)
        & (ijk[:, 1] >= 0)
        & (ijk[:, 1] < h)
        & (ijk[:, 2] >= 0)
        & (ijk[:, 2] < w)
    )
    valid = ijk[mask]
    occupied[valid[:, 0], valid[:, 1], valid[:, 2]] = True
    return occupied


def unknown_from_observed(observed_free: np.ndarray, observed_occupied: np.ndarray) -> np.ndarray:
    return ~(np.asarray(observed_free, dtype=bool) | np.asarray(observed_occupied, dtype=bool))
