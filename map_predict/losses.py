"""Losses for MapPredict occupancy completion baselines."""

from __future__ import annotations

try:
    import torch
    import torch.nn.functional as F
except Exception:  # pragma: no cover - torch may be unavailable in lint contexts.
    torch = None
    F = None


def _masked_bce_with_logits(logits, target, mask, pos_weight=None):
    selected_logits = logits[mask]
    selected_target = target[mask]
    if selected_logits.numel() == 0:
        return logits.sum() * 0.0
    return F.binary_cross_entropy_with_logits(selected_logits, selected_target, pos_weight=pos_weight)


def occupancy_completion_loss(
    pred_logits,
    batch: dict,
    *,
    lambda_obs: float = 0.1,
    unknown_pos_weight: float | None = None,
) -> dict:
    """Return Phase 3 unknown-region BCE plus observed consistency BCE."""

    if torch is None or F is None:
        raise ImportError("torch is required for occupancy_completion_loss")
    logits = pred_logits.squeeze(1)
    full_occupancy = batch["full_occupancy"].to(device=logits.device, dtype=torch.float32)
    unknown_mask = batch["unknown_mask"].to(device=logits.device).bool()
    observed_free = batch["observed_free"].to(device=logits.device).bool()
    observed_occupied = batch["observed_occupied"].to(device=logits.device).bool()
    known_mask = observed_free | observed_occupied
    observed_target = observed_occupied.to(dtype=torch.float32)
    pos_weight = None
    if unknown_pos_weight is not None:
        pos_weight = torch.tensor(float(unknown_pos_weight), device=logits.device, dtype=torch.float32)

    loss_unknown = _masked_bce_with_logits(logits, full_occupancy, unknown_mask, pos_weight=pos_weight)
    loss_observed = _masked_bce_with_logits(logits, observed_target, known_mask)
    loss = loss_unknown + float(lambda_obs) * loss_observed
    return {
        "loss": loss,
        "loss_unknown": loss_unknown.detach(),
        "loss_observed": loss_observed.detach(),
    }


def enforce_observed_consistency(pred_prob, observed_free, observed_occupied):
    """Clamp predicted occupancy probabilities in directly observed voxels."""

    pred = pred_prob.clone()
    pred[observed_free.bool()] = 0.0
    pred[observed_occupied.bool()] = 1.0
    return pred
