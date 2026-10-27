"""Rational Bézier curves and SLERP between unit vectors (paper Eq. 1 and 2)."""

from __future__ import annotations

import math

import torch


def bernstein_basis(t: torch.Tensor, num_ctrl: int) -> torch.Tensor:
    """Bernstein basis of degree ``num_ctrl - 1``.

    Args:
        t: Phase in [0, 1], shape (...).
        num_ctrl: Number of control points K.

    Returns:
        Basis values, shape (..., K).
    """
    n = num_ctrl - 1
    i = torch.arange(num_ctrl, device=t.device, dtype=t.dtype)
    binom = torch.tensor(
        [math.comb(n, k) for k in range(num_ctrl)], device=t.device, dtype=t.dtype
    )
    t = t.unsqueeze(-1)
    return binom * t.pow(i) * (1.0 - t).pow(n - i)


def rational_bezier(
    ctrl: torch.Tensor, weights: torch.Tensor, t: torch.Tensor
) -> torch.Tensor:
    """Evaluate a rational Bézier curve.

    Args:
        ctrl: Control points, shape (..., K, D).
        weights: Positive control point weights, shape (..., K).
        t: Phase in [0, 1], shape (...).

    Returns:
        Curve points, shape (..., D).
    """
    basis = bernstein_basis(t, ctrl.shape[-2]) * weights
    return (basis.unsqueeze(-1) * ctrl).sum(-2) / basis.sum(-1, keepdim=True)


def slerp_unit(v0: torch.Tensor, v1: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
    """Spherical linear interpolation between unit vectors.

    Args:
        v0: Start unit vectors, shape (..., 3).
        v1: End unit vectors, shape (..., 3).
        t: Phase in [0, 1], shape (...).

    Returns:
        Interpolated unit vectors, shape (..., 3).
    """
    t = t.unsqueeze(-1)
    v0, v1 = torch.broadcast_tensors(v0, v1)
    dot = (v0 * v1).sum(-1, keepdim=True).clamp(-1.0, 1.0)
    normal = torch.cross(v0, v1, dim=-1)
    sin_theta = normal.norm(dim=-1, keepdim=True)
    theta = torch.atan2(sin_theta, dot)
    # Cross products avoid cancellation in v1 - dot * v0 near the antipodes.
    tangent = torch.nn.functional.normalize(
        torch.cross(normal, v0, dim=-1), dim=-1, eps=torch.finfo(v0.dtype).tiny
    )
    # Only exactly collinear inputs need an arbitrary great-circle tangent.
    helper = torch.nn.functional.one_hot(v0.abs().argmin(-1), 3).to(v0.dtype)
    fallback = torch.nn.functional.normalize(torch.cross(v0, helper, dim=-1), dim=-1)
    tangent = torch.where(sin_theta > 0, tangent, fallback)
    out = torch.cos(t * theta) * v0 + torch.sin(t * theta) * tangent
    out = torch.nn.functional.normalize(out, dim=-1)
    # Preserve the supplied endpoints, including the exactly antipodal case.
    return torch.where(t == 0, v0, torch.where(t == 1, v1, out))
