"""Schemas for map_predict-enhanced frontier features.

These helpers define the feature contract between map_predict, an exploration
frontier selector, and VLA dataset builders. They do not run planners, rollouts,
or training.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import math


REQUIRED_FRONTIER_FEATURE_FIELDS = (
    "sample_id",
    "frontier_id",
    "predicted_free_volume",
    "predicted_occupied_risk",
    "mean_uncertainty",
    "max_uncertainty",
    "uncertainty_volume",
    "expected_information_gain_proxy",
    "path_cost_proxy",
    "reachability_proxy",
)


ENHANCED_VLA_SAMPLE_REQUIRED_FIELDS = (
    "sample_id",
    "robot_platform",
    "sensor_method",
    "images",
    "candidate_table",
    "map_predict_frontier_features",
    "prompt",
    "action_type",
    "target_action",
    "selected_candidate_id",
    "training",
)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_float(value: Any, default: float = math.nan) -> float:
    if value is None:
        return default
    if isinstance(value, str) and value.strip() == "":
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed


def is_finite_number(value: Any) -> bool:
    return math.isfinite(parse_float(value))


@dataclass(frozen=True)
class MapPredictFrontierFeature:
    sample_id: str
    frontier_id: int
    predicted_free_volume: float
    predicted_occupied_risk: float
    mean_uncertainty: float
    max_uncertainty: float
    uncertainty_volume: float
    expected_information_gain_proxy: float
    path_cost_proxy: float
    reachability_proxy: bool
    score: float | None = None
    selected_by_map_predict_score: bool = False

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "MapPredictFrontierFeature":
        return cls(
            sample_id=str(row.get("sample_id", "")),
            frontier_id=int(parse_float(row.get("frontier_id"), 0.0)),
            predicted_free_volume=parse_float(row.get("predicted_free_volume"), 0.0),
            predicted_occupied_risk=parse_float(row.get("predicted_occupied_risk"), 0.0),
            mean_uncertainty=parse_float(row.get("mean_uncertainty"), 0.0),
            max_uncertainty=parse_float(row.get("max_uncertainty"), 0.0),
            uncertainty_volume=parse_float(row.get("uncertainty_volume"), 0.0),
            expected_information_gain_proxy=parse_float(row.get("expected_information_gain_proxy"), 0.0),
            path_cost_proxy=parse_float(row.get("path_cost_proxy"), 0.0),
            reachability_proxy=parse_bool(row.get("reachability_proxy")),
            score=parse_float(row.get("score")) if "score" in row else None,
            selected_by_map_predict_score=parse_bool(row.get("selected_by_map_predict_score")),
        )

    def to_vla_feature(self) -> dict[str, Any]:
        return {
            "frontier_id": self.frontier_id,
            "predicted_free_volume": self.predicted_free_volume,
            "predicted_occupied_risk": self.predicted_occupied_risk,
            "mean_uncertainty": self.mean_uncertainty,
            "max_uncertainty": self.max_uncertainty,
            "uncertainty_volume": self.uncertainty_volume,
            "path_cost_proxy": self.path_cost_proxy,
            "map_predict_score": self.score,
        }


def validate_frontier_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FRONTIER_FEATURE_FIELDS:
        if field not in row:
            errors.append(f"missing field: {field}")
    for field in (
        "frontier_id",
        "predicted_free_volume",
        "predicted_occupied_risk",
        "mean_uncertainty",
        "max_uncertainty",
        "uncertainty_volume",
        "expected_information_gain_proxy",
        "path_cost_proxy",
    ):
        if field in row and not is_finite_number(row[field]):
            errors.append(f"non-finite field: {field}")
    return errors


def validate_enhanced_vla_sample(sample: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ENHANCED_VLA_SAMPLE_REQUIRED_FIELDS:
        if field not in sample:
            errors.append(f"missing field: {field}")
    if sample.get("action_type") != "high_level_candidate_action":
        errors.append("action_type must be high_level_candidate_action")
    if sample.get("training") is not False:
        errors.append("training must be false for preview samples")
    if not isinstance(sample.get("map_predict_frontier_features"), list):
        errors.append("map_predict_frontier_features must be a list")
    return errors
