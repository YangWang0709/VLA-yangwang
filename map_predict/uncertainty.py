"""Uncertainty utilities for occupancy probability grids."""

from __future__ import annotations

import numpy as np


def binary_entropy(probability: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    p = np.clip(np.asarray(probability, dtype=np.float32), eps, 1.0 - eps)
    return -(p * np.log(p) + (1.0 - p) * np.log(1.0 - p))


def normalized_binary_entropy(probability: np.ndarray) -> np.ndarray:
    return (binary_entropy(probability) / np.log(2.0)).astype(np.float32)


def uncertainty_from_logits(logits: np.ndarray) -> np.ndarray:
    prob = 1.0 / (1.0 + np.exp(-np.asarray(logits, dtype=np.float32)))
    return normalized_binary_entropy(prob)


def sigmoid(logits: np.ndarray) -> np.ndarray:
    logits = np.asarray(logits, dtype=np.float32)
    return (1.0 / (1.0 + np.exp(-logits))).astype(np.float32)


def probability_entropy_uncertainty(pred_occ_prob: np.ndarray) -> np.ndarray:
    """Return normalized entropy uncertainty in [0, 1]."""

    return normalized_binary_entropy(pred_occ_prob)


def preserve_observed_space(
    pred_occ_prob: np.ndarray,
    uncertainty: np.ndarray,
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Clamp known free/occupied voxels and zero their uncertainty."""

    prob = np.asarray(pred_occ_prob, dtype=np.float32).copy()
    unc = np.asarray(uncertainty, dtype=np.float32).copy()
    free = np.asarray(observed_free, dtype=bool)
    occupied = np.asarray(observed_occupied, dtype=bool)
    prob[free] = 0.0
    prob[occupied] = 1.0
    unc[free | occupied] = 0.0
    return prob, unc


def observed_uncertainty_gap(
    uncertainty: np.ndarray,
    unknown_mask: np.ndarray,
    observed_free: np.ndarray,
    observed_occupied: np.ndarray,
) -> dict[str, float]:
    unc = np.asarray(uncertainty, dtype=np.float32)
    unknown = np.asarray(unknown_mask, dtype=bool)
    observed = np.asarray(observed_free, dtype=bool) | np.asarray(observed_occupied, dtype=bool)
    mean_unknown = float(unc[unknown].mean()) if unknown.any() else 0.0
    mean_observed = float(unc[observed].mean()) if observed.any() else 0.0
    return {
        "uncertainty_mean_unknown": mean_unknown,
        "uncertainty_mean_observed": mean_observed,
        "uncertainty_observed_gap": mean_unknown - mean_observed,
    }


def has_dropout_module(model) -> bool:
    """Return true if a torch model contains any dropout layer."""

    try:
        import torch.nn as nn
    except Exception:  # pragma: no cover
        return False
    dropout_types = (
        nn.Dropout,
        nn.Dropout1d,
        nn.Dropout2d,
        nn.Dropout3d,
        nn.AlphaDropout,
    )
    return any(isinstance(module, dropout_types) for module in model.modules())
