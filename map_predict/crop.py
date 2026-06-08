"""Spatial crop utilities for map_predict samples."""

from __future__ import annotations

import numpy as np


def crop_origin_from_center(
    center_xyz: tuple[float, float, float],
    dims: tuple[int, int, int],
    voxel_size: float,
) -> tuple[float, float, float]:
    """Return crop origin in xyz for a [D, H, W] grid.

    Axis convention is D=z, H=y, W=x.
    """

    d, h, w = dims
    extent_xyz = np.asarray((w, h, d), dtype=np.float32) * float(voxel_size)
    center = np.asarray(center_xyz, dtype=np.float32)
    origin = center - 0.5 * extent_xyz
    return tuple(float(x) for x in origin)


def world_xyz_to_zyx(
    xyz: np.ndarray,
    origin_xyz: tuple[float, float, float],
    voxel_size: float,
) -> np.ndarray:
    """Convert world xyz points to integer zyx indices for [D, H, W] arrays."""

    pts = np.asarray(xyz, dtype=np.float32)
    origin = np.asarray(origin_xyz, dtype=np.float32)
    ijk_xyz = np.floor((pts - origin) / float(voxel_size)).astype(np.int32)
    return ijk_xyz[:, [2, 1, 0]]


def grid_centers_xyz(
    dims: tuple[int, int, int],
    origin_xyz: tuple[float, float, float],
    voxel_size: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return dense xyz coordinate arrays with shape [D, H, W]."""

    d, h, w = dims
    origin = np.asarray(origin_xyz, dtype=np.float32)
    xs = origin[0] + (np.arange(w, dtype=np.float32) + 0.5) * float(voxel_size)
    ys = origin[1] + (np.arange(h, dtype=np.float32) + 0.5) * float(voxel_size)
    zs = origin[2] + (np.arange(d, dtype=np.float32) + 0.5) * float(voxel_size)
    zz, yy, xx = np.meshgrid(zs, ys, xs, indexing="ij")
    return xx, yy, zz


def crop_3d_from_origin(
    array: np.ndarray,
    source_origin_xyz: tuple[float, float, float],
    crop_origin_xyz: tuple[float, float, float],
    dims: tuple[int, int, int],
    voxel_size: float,
    fill_value: int | float = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Return a zero-padded crop and valid mask using xyz origins.

    Source and destination arrays use [D, H, W] where D=z, H=y, W=x.
    """

    src = np.asarray(array)
    out = np.full(dims, fill_value, dtype=src.dtype)
    valid = np.zeros(dims, dtype=bool)

    xx, yy, zz = grid_centers_xyz(dims, crop_origin_xyz, voxel_size)
    pts = np.stack([xx.ravel(), yy.ravel(), zz.ravel()], axis=1)
    zyx = world_xyz_to_zyx(pts, source_origin_xyz, voxel_size)
    d_src, h_src, w_src = src.shape
    inside = (
        (zyx[:, 0] >= 0)
        & (zyx[:, 0] < d_src)
        & (zyx[:, 1] >= 0)
        & (zyx[:, 1] < h_src)
        & (zyx[:, 2] >= 0)
        & (zyx[:, 2] < w_src)
    )
    out_flat = out.reshape(-1)
    valid_flat = valid.reshape(-1)
    valid_indices = np.flatnonzero(inside)
    src_zyx = zyx[inside]
    out_flat[valid_indices] = src[src_zyx[:, 0], src_zyx[:, 1], src_zyx[:, 2]]
    valid_flat[valid_indices] = True
    return out, valid


def centered_crop_3d(
    array: np.ndarray,
    center_zyx: tuple[int, int, int],
    dims: tuple[int, int, int],
) -> np.ndarray:
    """Return a zero-padded centered crop with shape [D, H, W]."""

    src = np.asarray(array)
    out = np.zeros(dims, dtype=src.dtype)
    slices_src = []
    slices_dst = []
    for center, size, max_size in zip(center_zyx, dims, src.shape):
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
