"""Inference/sample interface draft for map_predict."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MapPredictOutput:
    predicted_occupancy: Any
    occupancy_probability: Any
    uncertainty: Any
    metadata: dict


def format_feature_provider_output(predicted_occupancy: Any, occupancy_probability: Any, uncertainty: Any) -> MapPredictOutput:
    return MapPredictOutput(
        predicted_occupancy=predicted_occupancy,
        occupancy_probability=occupancy_probability,
        uncertainty=uncertainty,
        metadata={
            "module": "map_predict",
            "role": "feature_provider",
            "planner": False,
            "vla": False,
        },
    )
