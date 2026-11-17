"""Per-environment behavior gates shared by the lift and track acceptance tools."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import torch


@dataclass(frozen=True)
class GateLimits:
    position_m: float
    """Maximum mean 3D foot error of a successful environment."""
    z_m: float
    """Maximum mean foot height error of a successful environment."""
    contact_fraction: float
    """Maximum share of counted samples with the manipulating foot on the ground."""
    success_rate: Fraction
    """Minimum share of successful environments."""
    fall_rate: Fraction
    """Maximum share of early-terminated environments."""


LIFT_LIMITS = GateLimits(0.05, 0.03, 0.10, Fraction(9, 10), Fraction(1, 20))
TRACK_LIMITS = GateLimits(0.10, 0.05, 0.10, Fraction(4, 5), Fraction(1, 20))


def summarize_gate(
    position_error: torch.Tensor,
    z_error: torch.Tensor,
    ground_contact: torch.Tensor,
    fell: torch.Tensor,
    limits: GateLimits,
    contact_mask: torch.Tensor | None = None,
) -> dict:
    """Judge (T,N) samples of N environments against `limits`.

    Contact only counts where `contact_mask` is set (default: every sample).
    Early-terminated environments fail; any nonfinite or negative error value
    fails the whole gate.
    """
    if (
        position_error.ndim != 2
        or min(position_error.shape) == 0
        or z_error.shape != position_error.shape
        or ground_contact.shape != position_error.shape
        or fell.shape != position_error.shape[1:]
        or (contact_mask is not None and contact_mask.shape != position_error.shape)
    ):
        raise ValueError("Expected nonempty matching (T,N) data and (N,) falls")
    if contact_mask is None:
        contact_mask = torch.ones_like(ground_contact, dtype=torch.bool)
    finite = torch.isfinite(position_error).all(0) & torch.isfinite(z_error).all(0)
    valid = finite & (position_error >= 0).all(0) & (z_error >= 0).all(0)
    pos = position_error.mean(0)
    z = z_error.mean(0)
    counted = contact_mask.sum(0)
    contact = (ground_contact & contact_mask).sum(0) / counted.clamp(min=1)
    success = (
        valid
        & ~fell
        & (pos <= limits.position_m)
        & (z <= limits.z_m)
        & (contact <= limits.contact_fraction)
    )
    n = fell.numel()
    successful_envs = int(success.sum())
    fall_count = int(fell.sum())
    # Integer ratios avoid rejecting a boundary rate through float32 rounding.
    rate = limits.success_rate
    enough_success = successful_envs * rate.denominator >= rate.numerator * n
    rate = limits.fall_rate
    few_falls = fall_count * rate.denominator <= rate.numerator * n
    surviving = valid & ~fell

    def mean_of_survivors(values):
        return float(values[surviving].mean()) if bool(surviving.any()) else None

    return {
        "passed": bool(valid.all()) and enough_success and few_falls,
        "environments": n,
        "successful_envs": successful_envs,
        "success_rate": successful_envs / n,
        "fall_rate": fall_count / n,
        "nonfinite_envs": int((~finite).sum()),
        "error_statistics_scope": "original episodes without early termination",
        "mean_position_error_m": mean_of_survivors(pos),
        "mean_z_error_m": mean_of_survivors(z),
        "manip_ground_contact_fraction": mean_of_survivors(contact),
    }
