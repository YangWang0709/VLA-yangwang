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
