"""Frontier and candidate feature extraction from predicted occupancy."""

from __future__ import annotations

from typing import Any

import numpy as np


def frontier_mask_2d(known_free: np.ndarray, unknown: np.ndarray) -> np.ndarray:
    free = np.asarray(known_free, dtype=bool)
    unk = np.asarray(unknown, dtype=bool)
    frontier = np.zeros_like(free, dtype=bool)
    shifts = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dy, dx in shifts:
        shifted = np.zeros_like(unk, dtype=bool)
        src_y = slice(max(0, -dy), unk.shape[0] - max(0, dy))
        src_x = slice(max(0, -dx), unk.shape[1] - max(0, dx))
        dst_y = slice(max(0, dy), unk.shape[0] - max(0, -dy))
        dst_x = slice(max(0, dx), unk.shape[1] - max(0, -dx))
        shifted[dst_y, dst_x] = unk[src_y, src_x]
        frontier |= free & shifted
    return frontier


def frontier_mask_from_3d(observed_free: np.ndarray, unknown_mask: np.ndarray) -> np.ndarray:
    """Derive a 3D frontier mask from free voxels adjacent to unknown voxels."""

    free = np.asarray(observed_free, dtype=bool)
    unknown = np.asarray(unknown_mask, dtype=bool)
    frontier = np.zeros_like(free, dtype=bool)
    shifts = [
        (-1, 0, 0),
        (1, 0, 0),
        (0, -1, 0),
        (0, 1, 0),
        (0, 0, -1),
        (0, 0, 1),
    ]
    for dz, dy, dx in shifts:
        shifted = np.zeros_like(unknown, dtype=bool)
        src_z = slice(max(0, -dz), unknown.shape[0] - max(0, dz))
        src_y = slice(max(0, -dy), unknown.shape[1] - max(0, dy))
        src_x = slice(max(0, -dx), unknown.shape[2] - max(0, dx))
        dst_z = slice(max(0, dz), unknown.shape[0] - max(0, -dz))
        dst_y = slice(max(0, dy), unknown.shape[1] - max(0, -dy))
        dst_x = slice(max(0, dx), unknown.shape[2] - max(0, -dx))
        shifted[dst_z, dst_y, dst_x] = unknown[src_z, src_y, src_x]
        frontier |= free & shifted
    return frontier


def connected_components_2d(mask: np.ndarray) -> list[np.ndarray]:
    """Return 4-connected BEV component masks."""

    source = np.asarray(mask, dtype=bool)
    visited = np.zeros_like(source, dtype=bool)
    components: list[np.ndarray] = []
    h, w = source.shape
    for y in range(h):
        for x in range(w):
            if visited[y, x] or not source[y, x]:
                continue
            component = np.zeros_like(source, dtype=bool)
            stack = [(y, x)]
            visited[y, x] = True
            while stack:
                cy, cx = stack.pop()
                component[cy, cx] = True
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and source[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((ny, nx))
            components.append(component)
    return components


def frontier_feature_rows(
    *,
    sample_id: str,
    scene_id: str | None = None,
    frontier_mask: np.ndarray,
    unknown_mask: np.ndarray | None = None,
    pred_occ_prob: np.ndarray,
    uncertainty: np.ndarray,
    bev_pred_occ: np.ndarray,
    bev_uncertainty: np.ndarray,
    robot_pose: np.ndarray | None = None,
    crop_origin_xyz: np.ndarray | None = None,
    voxel_size: float | None = None,
    max_components: int | None = None,
) -> list[dict[str, Any]]:
    """Summarize each BEV frontier connected component."""

    frontier_3d = np.asarray(frontier_mask, dtype=bool)
    if frontier_3d.ndim != 3:
        raise ValueError(f"frontier_mask must be [D,H,W], got {frontier_3d.shape}")
    pred = np.asarray(pred_occ_prob, dtype=np.float32)
    unc = np.asarray(uncertainty, dtype=np.float32)
    unknown = np.asarray(unknown_mask, dtype=bool) if unknown_mask is not None else np.zeros_like(frontier_3d, dtype=bool)
    bev_frontier = frontier_3d.any(axis=0)
    components = connected_components_2d(bev_frontier)
    if max_components is not None:
        components = components[: int(max_components)]
    rows: list[dict[str, Any]] = []
    for frontier_id, component_2d in enumerate(components):
        component_3d = frontier_3d & component_2d[None, :, :]
        if not component_3d.any():
            continue
        feature_3d = unknown & component_2d[None, :, :]
        if not feature_3d.any():
            feature_3d = component_3d
        pred_values = pred[feature_3d]
        unc_values = unc[feature_3d]
        bev_unc_values = np.asarray(bev_uncertainty, dtype=np.float32)[component_2d]
        yy, xx = np.nonzero(component_2d)
        centroid_y = float(yy.mean()) if yy.size else 0.0
        centroid_x = float(xx.mean()) if xx.size else 0.0
        centroid_world_x = None
        centroid_world_y = None
        robot_world_x = None
        robot_world_y = None
        robot_to_frontier_distance = None
        if crop_origin_xyz is not None and voxel_size is not None:
            origin = np.asarray(crop_origin_xyz, dtype=np.float32).reshape(-1)
            if origin.size >= 2:
                centroid_world_x = float(origin[0] + (centroid_x + 0.5) * float(voxel_size))
                centroid_world_y = float(origin[1] + (centroid_y + 0.5) * float(voxel_size))
        if robot_pose is not None:
            pose = np.asarray(robot_pose, dtype=np.float32).reshape(-1)
            if pose.size >= 2:
                robot_world_x = float(pose[0])
                robot_world_y = float(pose[1])
        if centroid_world_x is not None and centroid_world_y is not None and robot_world_x is not None and robot_world_y is not None:
            robot_to_frontier_distance = float(
                np.hypot(centroid_world_x - robot_world_x, centroid_world_y - robot_world_y)
            )
        rows.append(
            {
                "sample_id": sample_id,
                "scene_id": scene_id or "",
                "frontier_id": int(frontier_id),
                "frontier_voxel_count": int(component_3d.sum()),
                "frontier_bev_cell_count": int(component_2d.sum()),
                "frontier_centroid_y": centroid_y,
                "frontier_centroid_x": centroid_x,
                "frontier_centroid_world_x": centroid_world_x,
                "frontier_centroid_world_y": centroid_world_y,
                "robot_world_x": robot_world_x,
                "robot_world_y": robot_world_y,
                "robot_to_frontier_distance": robot_to_frontier_distance,
                "predicted_free_volume": float((1.0 - pred_values).sum()),
                "predicted_occupied_risk": float(pred_values.mean()) if pred_values.size else 0.0,
                "mean_uncertainty": float(unc_values.mean()) if unc_values.size else 0.0,
                "max_uncertainty": float(unc_values.max()) if unc_values.size else 0.0,
                "uncertainty_volume": float(unc_values.sum()) if unc_values.size else 0.0,
                "expected_information_gain_proxy": float(
                    (1.0 - pred_values).sum() * (bev_unc_values.mean() if bev_unc_values.size else 0.0)
                ),
                "bev_pred_occ_mean": float(np.asarray(bev_pred_occ, dtype=np.float32)[component_2d].mean())
                if component_2d.any()
                else 0.0,
            }
        )
    return rows


def frontier_feature_nan_count(rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        for value in row.values():
            if isinstance(value, float) and not np.isfinite(value):
                count += 1
    return count


def summarize_candidate_uncertainty(
    candidates: list[dict[str, Any]],
    uncertainty_bev: np.ndarray,
    world_to_pixel,
    radius_px: int = 3,
) -> list[dict[str, Any]]:
    """Attach local uncertainty statistics to candidate dictionaries."""

    out: list[dict[str, Any]] = []
    h, w = uncertainty_bev.shape
    for candidate in candidates:
        x, y = world_to_pixel(candidate["x"], candidate["y"])
        x = int(round(x))
        y = int(round(y))
        y0, y1 = max(0, y - radius_px), min(h, y + radius_px + 1)
        x0, x1 = max(0, x - radius_px), min(w, x + radius_px + 1)
        patch = uncertainty_bev[y0:y1, x0:x1]
        enriched = dict(candidate)
        enriched["map_predict_uncertainty_mean"] = float(patch.mean()) if patch.size else None
        enriched["map_predict_uncertainty_max"] = float(patch.max()) if patch.size else None
        out.append(enriched)
    return out
