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
    """Convert world xyz points to zyx indices for [D, H, W] arrays."""

    points = np.asarray(points_xyz, dtype=np.float32)
    origin = np.asarray(spec.origin, dtype=np.float32)
    xyz = np.floor((points - origin) / float(spec.voxel_size)).astype(np.int32)
    return xyz[:, [2, 1, 0]]


def voxelize_points(points_xyz: np.ndarray, spec: VoxelGridSpec) -> np.ndarray:
    """Convert points into a boolean occupied grid with shape [D, H, W]."""

    occupied = np.zeros(spec.dims, dtype=bool)
    if points_xyz is None or len(points_xyz) == 0:
        return occupied
    zyx = world_to_grid(points_xyz, spec)
    d, h, w = spec.dims
    mask = (
        (zyx[:, 0] >= 0)
        & (zyx[:, 0] < d)
        & (zyx[:, 1] >= 0)
        & (zyx[:, 1] < h)
        & (zyx[:, 2] >= 0)
        & (zyx[:, 2] < w)
    )
    valid = zyx[mask]
    occupied[valid[:, 0], valid[:, 1], valid[:, 2]] = True
    return occupied


def point_to_grid_index(point_xyz: np.ndarray, spec: VoxelGridSpec) -> tuple[int, int, int] | None:
    """Return one zyx index for a world point, or None if it is outside."""

    point = np.asarray(point_xyz, dtype=np.float32).reshape(1, 3)
    zyx = world_to_grid(point, spec)[0]
    d, h, w = spec.dims
    if 0 <= zyx[0] < d and 0 <= zyx[1] < h and 0 <= zyx[2] < w:
        return int(zyx[0]), int(zyx[1]), int(zyx[2])
    return None


def raycast_points_to_occupancy(
    camera_origin_xyz: tuple[float, float, float] | np.ndarray,
    hit_points_xyz: np.ndarray,
    spec: VoxelGridSpec,
    *,
    max_points: int = 2400,
    ray_step_fraction: float = 0.5,
    min_range: float = 0.05,
    max_range: float = 15.0,
) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    """Build local partial occupancy by ray carving depth endpoints.

    Rays mark voxels before a hit as free and the endpoint voxel as occupied.
    The function accepts world-frame hit points and returns [D, H, W] boolean
    arrays. It is intentionally label-free and does not look at full occupancy.
    """

    free = np.zeros(spec.dims, dtype=bool)
    occupied = np.zeros(spec.dims, dtype=bool)
    pts = np.asarray(hit_points_xyz, dtype=np.float32).reshape(-1, 3)
    if pts.size == 0:
        return free, occupied, {"input_point_count": 0, "used_point_count": 0, "endpoint_inside_count": 0}
    finite = np.isfinite(pts).all(axis=1)
    pts = pts[finite]
    if pts.shape[0] > max_points:
        pts = pts[:: max(1, int(np.ceil(pts.shape[0] / max_points)))]

    eye = np.asarray(camera_origin_xyz, dtype=np.float32)
    step_size = max(1e-6, float(spec.voxel_size) * float(ray_step_fraction))
    used = 0
    endpoint_inside = 0

    for point in pts:
        vec = point - eye
        dist = float(np.linalg.norm(vec))
        if not np.isfinite(dist) or dist < min_range or dist > max_range:
            continue
        used += 1
        steps = max(2, int(np.ceil(dist / step_size)))
        # Keep the endpoint for occupied and carve only preceding samples.
        for step in range(steps - 1):
            t = step / steps
            idx = point_to_grid_index(eye + vec * t, spec)
            if idx is not None:
                free[idx] = True
        endpoint_idx = point_to_grid_index(point, spec)
        if endpoint_idx is not None:
            occupied[endpoint_idx] = True
            endpoint_inside += 1

    free &= ~occupied
    return free, occupied, {
        "input_point_count": int(hit_points_xyz.shape[0] if hasattr(hit_points_xyz, "shape") else 0),
        "used_point_count": int(used),
        "endpoint_inside_count": int(endpoint_inside),
    }


def unknown_from_observed(observed_free: np.ndarray, observed_occupied: np.ndarray) -> np.ndarray:
    return ~(np.asarray(observed_free, dtype=bool) | np.asarray(observed_occupied, dtype=bool))


def frontier_from_free_unknown(
    observed_free: np.ndarray,
    unknown_mask: np.ndarray,
    connectivity: int = 6,
) -> np.ndarray:
    """Return frontier voxels: observed free adjacent to unknown."""

    if connectivity not in (6, 26):
        raise ValueError("frontier connectivity must be 6 or 26")
    free = np.asarray(observed_free, dtype=bool)
    unknown = np.asarray(unknown_mask, dtype=bool)
    adjacent_unknown = np.zeros_like(unknown, dtype=bool)
    offsets = []
    for dz in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dz == dy == dx == 0:
                    continue
                if connectivity == 6 and abs(dz) + abs(dy) + abs(dx) != 1:
                    continue
                offsets.append((dz, dy, dx))
    for dz, dy, dx in offsets:
        shifted = np.zeros_like(unknown, dtype=bool)
        src_z = slice(max(0, -dz), unknown.shape[0] - max(0, dz))
        src_y = slice(max(0, -dy), unknown.shape[1] - max(0, dy))
        src_x = slice(max(0, -dx), unknown.shape[2] - max(0, dx))
        dst_z = slice(max(0, dz), unknown.shape[0] - max(0, -dz))
        dst_y = slice(max(0, dy), unknown.shape[1] - max(0, -dy))
        dst_x = slice(max(0, dx), unknown.shape[2] - max(0, -dx))
        shifted[dst_z, dst_y, dst_x] = unknown[src_z, src_y, src_x]
        adjacent_unknown |= shifted
    return free & adjacent_unknown
