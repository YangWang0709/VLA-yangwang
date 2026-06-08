"""Spatial crop utilities for map_predict samples."""

from __future__ import annotations

import numpy as np


def crop_origin_from_center(
    center_xyz: tuple[float, float, float],
    dims: tuple[int, int, int],
    voxel_size: float,
) -> tuple[float, float, float]:
    extent = np.asarray(dims, dtype=np.float32) * float(voxel_size)
    center = np.asarray(center_xyz, dtype=np.float32)
    origin = center - 0.5 * extent
    return tuple(float(x) for x in origin)


def centered_crop_3d(array: np.ndarray, center_zyx: tuple[int, int, int], dims: tuple[int, int, int]) -> np.ndarray:
    """Return a zero-padded centered crop with shape [D, H, W]."""

    src = np.asarray(array)
    out = np.zeros(dims, dtype=src.dtype)
    slices_src = []
    slices_dst = []
    for axis, (center, size, max_size) in enumerate(zip(center_zyx, dims, src.shape)):
        start = int(center) - size // 2
        end = start + size
        src_start = max(0, start)
        src_end = min(max_size, end)
        dst_start = max(0, -start)
        dst_end = dst_start + max(0, src_end - src_start)
        slices_src.append(slice(src_start, src_end))
        slices_dst.append(slice(dst_start, dst_end))
    out[tuple(slices_dst)] = src[tuple(slices_src)]
    return out
