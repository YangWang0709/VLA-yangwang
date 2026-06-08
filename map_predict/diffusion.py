"""Diffusion schedule draft for occupancy completion experiments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DiffusionSchedule:
    timesteps: int = 100
    beta_start: float = 1e-4
    beta_end: float = 2e-2

    def betas(self) -> np.ndarray:
        return np.linspace(self.beta_start, self.beta_end, self.timesteps, dtype=np.float32)

    def alpha_bars(self) -> np.ndarray:
        betas = self.betas()
        return np.cumprod(1.0 - betas)


def add_noise_numpy(x0: np.ndarray, noise: np.ndarray, timestep: int, schedule: DiffusionSchedule) -> np.ndarray:
    alpha_bar = float(schedule.alpha_bars()[timestep])
    return np.sqrt(alpha_bar) * x0 + np.sqrt(1.0 - alpha_bar) * noise
