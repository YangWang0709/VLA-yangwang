"""Uncertainty utilities for occupancy probability grids."""

from __future__ import annotations

import numpy as np


def binary_entropy(probability: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    p = np.clip(np.asarray(probability, dtype=np.float32), eps, 1.0 - eps)
    return -(p * np.log(p) + (1.0 - p) * np.log(1.0 - p))


def normalized_binary_entropy(probability: np.ndarray) -> np.ndarray:
    return binary_entropy(probability) / np.log(2.0)


def uncertainty_from_logits(logits: np.ndarray) -> np.ndarray:
    prob = 1.0 / (1.0 + np.exp(-np.asarray(logits, dtype=np.float32)))
    return normalized_binary_entropy(prob)
