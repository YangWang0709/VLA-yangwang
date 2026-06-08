"""Handcrafted frontier scoring baseline for MapPredict Phase 5."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class FrontierScoringConfig:
    alpha: float = 1.0
    beta: float = 0.5
    gamma: float = 1.0
    delta: float = 0.2
    uncertainty_threshold: float = 0.05
    path_cost_method: str = "euclidean_proxy"
    reachability_method: str = "bev_validity_proxy"
    risk_method: str = "mean_predicted_occupied_probability"
    occupied_risk_threshold: float = 0.5
    selection_method: str = "max_score_per_sample"


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    try:
        if any(ch in text for ch in (".", "e", "E")):
            return float(text)
        return int(text)
    except ValueError:
        return text


def load_scoring_config(path: str | Path) -> FrontierScoringConfig:
    """Load a tiny YAML-like key/value config without requiring PyYAML."""

    values: dict[str, Any] = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = _parse_scalar(value)
    return FrontierScoringConfig(**{k: values[k] for k in values if k in FrontierScoringConfig.__dataclass_fields__})


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, str) and value.strip() == "":
        return default
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if np.isfinite(out) else default


def row_nan_feature_count(row: dict[str, Any]) -> int:
    count = 0
    for value in row.values():
        if isinstance(value, float) and not np.isfinite(value):
            count += 1
        elif isinstance(value, str):
            try:
                parsed = float(value)
            except ValueError:
                continue
            if not np.isfinite(parsed):
                count += 1
    return count


def path_cost_proxy(row: dict[str, Any], config: FrontierScoringConfig) -> float:
    if config.path_cost_method != "euclidean_proxy":
        raise ValueError(f"unsupported path cost method: {config.path_cost_method}")
    direct = to_float(row.get("robot_to_frontier_distance"), default=np.nan)
    if np.isfinite(direct):
        return float(direct)
    robot_x = to_float(row.get("robot_world_x"), default=np.nan)
    robot_y = to_float(row.get("robot_world_y"), default=np.nan)
    frontier_x = to_float(row.get("frontier_centroid_world_x"), default=np.nan)
    frontier_y = to_float(row.get("frontier_centroid_world_y"), default=np.nan)
    if np.isfinite([robot_x, robot_y, frontier_x, frontier_y]).all():
        return float(np.hypot(frontier_x - robot_x, frontier_y - robot_y))
    # Deterministic fallback when only the Phase 4 prototype table is available.
    return float(np.sqrt(max(to_float(row.get("frontier_bev_cell_count")), 0.0)))


def reachability_proxy(row: dict[str, Any], config: FrontierScoringConfig) -> tuple[bool, str]:
    if config.reachability_method != "bev_validity_proxy":
        raise ValueError(f"unsupported reachability method: {config.reachability_method}")
    if to_float(row.get("frontier_bev_cell_count")) <= 0:
        return False, "empty_bev_frontier"
    if to_float(row.get("frontier_voxel_count")) <= 0:
        return False, "empty_voxel_frontier"
    risk = to_float(row.get("predicted_occupied_risk"))
    if risk >= float(config.occupied_risk_threshold):
        return False, "occupied_risk_above_threshold"
    return True, ""


def score_frontier_row(row: dict[str, Any], config: FrontierScoringConfig) -> dict[str, Any]:
    scored = dict(row)
    predicted_free_volume = to_float(row.get("predicted_free_volume"))
    uncertainty_volume = to_float(row.get("uncertainty_volume"))
    occupied_risk = to_float(row.get("predicted_occupied_risk"))
    path_cost = path_cost_proxy(row, config)
    reachable, failure_reason = reachability_proxy(row, config)
    score = (
        float(config.alpha) * predicted_free_volume
        + float(config.beta) * uncertainty_volume
        - float(config.gamma) * occupied_risk
        - float(config.delta) * path_cost
    )
    nan_feature_count = row_nan_feature_count(row)
    if nan_feature_count:
        reachable = False
        failure_reason = "nan_feature"
    scored.update(
        {
            "path_cost_proxy": float(path_cost),
            "reachability_proxy": bool(reachable),
            "invalid_flag": bool(not reachable),
            "failure_reason": failure_reason,
            "score": float(score) if np.isfinite(score) else np.nan,
            "selected_by_map_predict_score": False,
        }
    )
    return scored


def score_frontiers(rows: list[dict[str, Any]], config: FrontierScoringConfig) -> list[dict[str, Any]]:
    scored = [score_frontier_row(row, config) for row in rows]
    by_sample: dict[str, list[dict[str, Any]]] = {}
    for row in scored:
        by_sample.setdefault(str(row.get("sample_id", "")), []).append(row)
    for sample_rows in by_sample.values():
        candidates = [
            row
            for row in sample_rows
            if bool(row.get("reachability_proxy")) and np.isfinite(to_float(row.get("score"), default=np.nan))
        ]
        if not candidates:
            continue
        best = max(candidates, key=lambda row: to_float(row.get("score"), default=-np.inf))
        best["selected_by_map_predict_score"] = True
    return scored


def score_formula() -> str:
    return "alpha*predicted_free_volume + beta*uncertainty_volume - gamma*occupied_risk - delta*path_cost"
