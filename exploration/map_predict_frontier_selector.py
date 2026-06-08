"""MapPredict-enhanced frontier selector interface.

The selector is a deterministic feature consumer. It does not call a planner,
run rollout, train VLA, or emit low-level robot commands.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

from exploration.frontier_feature_schema import parse_bool, parse_float, validate_frontier_row


DEFAULT_WEIGHTS = {
    "alpha": 1.0,
    "beta": 0.5,
    "gamma": 1.0,
    "delta": 0.2,
}


def load_frontier_table(frontier_table: str | Path | Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(frontier_table, (str, Path)):
        with Path(frontier_table).open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    return [dict(row) for row in frontier_table]


def compute_map_predict_score(row: dict[str, Any], weights: dict[str, float] | None = None) -> float:
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    predicted_free_volume = parse_float(row.get("predicted_free_volume"), 0.0)
    uncertainty_volume = parse_float(row.get("uncertainty_volume"), 0.0)
    occupied_risk = parse_float(row.get("predicted_occupied_risk"), 0.0)
    path_cost_proxy = parse_float(row.get("path_cost_proxy"), 0.0)
    return (
        float(weights["alpha"]) * predicted_free_volume
        + float(weights["beta"]) * uncertainty_volume
        - float(weights["gamma"]) * occupied_risk
        - float(weights["delta"]) * path_cost_proxy
    )


def _row_is_valid(row: dict[str, Any], weights: dict[str, float] | None) -> tuple[bool, str, float]:
    errors = validate_frontier_row(row)
    if errors:
        return False, "; ".join(errors), float("nan")
    if not parse_bool(row.get("reachability_proxy")):
        return False, "unreachable_frontier", float("nan")
    if parse_bool(row.get("invalid_flag")):
        return False, str(row.get("failure_reason") or "invalid_frontier"), float("nan")
    score = parse_float(row.get("score"))
    if not (score == score):
        score = compute_map_predict_score(row, weights)
    if not (score == score):
        return False, "nan_score", float("nan")
    return True, "", score


def select_frontier_with_map_predict(
    frontier_table: str | Path | Iterable[dict[str, Any]],
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Select the highest-scoring valid frontier from a frontier table."""

    rows = load_frontier_table(frontier_table)
    best_row: dict[str, Any] | None = None
    best_score = float("-inf")
    invalid_count = 0
    for row in rows:
        valid, _, score = _row_is_valid(row, weights)
        if not valid:
            invalid_count += 1
            continue
        if score > best_score:
            best_score = score
            best_row = row
    if best_row is None:
        return {
            "selected_frontier_id": None,
            "score": None,
            "reason": {},
            "failure_reason": "no_valid_frontier",
            "valid_frontier_count": 0,
            "invalid_frontier_count": invalid_count,
        }

    selected_frontier_id = int(parse_float(best_row.get("frontier_id"), 0.0))
    return {
        "selected_frontier_id": selected_frontier_id,
        "score": float(best_score),
        "reason": {
            "predicted_free_volume": parse_float(best_row.get("predicted_free_volume"), 0.0),
            "uncertainty_volume": parse_float(best_row.get("uncertainty_volume"), 0.0),
            "occupied_risk": parse_float(best_row.get("predicted_occupied_risk"), 0.0),
            "path_cost_proxy": parse_float(best_row.get("path_cost_proxy"), 0.0),
        },
        "failure_reason": "",
        "valid_frontier_count": len(rows) - invalid_count,
        "invalid_frontier_count": invalid_count,
        "sample_id": best_row.get("sample_id"),
    }


def select_frontiers_by_sample(
    frontier_rows: Iterable[dict[str, Any]],
    weights: dict[str, float] | None = None,
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in frontier_rows:
        grouped.setdefault(str(row.get("sample_id", "")), []).append(dict(row))
    return {sample_id: select_frontier_with_map_predict(rows, weights) for sample_id, rows in grouped.items()}
