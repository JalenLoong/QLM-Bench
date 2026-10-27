"""Yaw-only rigid transforms between object, world and robot heading frames.

The paper expresses trajectory parameters in three frames: the object frame for
hand-designed expert trajectories, the world frame for the planner, and the robot
frame for the controller. The controller uses a gravity-aligned heading frame
(base x/y, environment-origin z, base yaw), preserving environment-absolute height.
These generic helpers apply the full supplied origin; callers choose that origin.
"""

from __future__ import annotations

import torch


def yaw_matrix(yaw: torch.Tensor) -> torch.Tensor:
    """Rotation matrices about +z, shape (..., 3, 3)."""
    c, s = torch.cos(yaw), torch.sin(yaw)
    zero, one = torch.zeros_like(yaw), torch.ones_like(yaw)
    rows = (
        torch.stack([c, -s, zero], -1),
        torch.stack([s, c, zero], -1),
        torch.stack([zero, zero, one], -1),
    )
    return torch.stack(rows, -2)


def quat_to_yaw(quat_wxyz: torch.Tensor) -> torch.Tensor:
    """Heading angle of (w, x, y, z) quaternions, shape (...)."""
    w, x, y, z = quat_wxyz.unbind(-1)
    return torch.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def apply_yaw_transform(
    points: torch.Tensor, yaw: torch.Tensor, origin: torch.Tensor
) -> torch.Tensor:
    """Map points from a local yaw frame to its parent: R(yaw) p + origin.

    Args:
        points: Shape (..., N, 3) or (..., 3).
        yaw: Shape (...).
        origin: Shape (..., 3).
    """
    rot = yaw_matrix(yaw)
    if points.dim() == origin.dim():
        return (rot @ points.unsqueeze(-1)).squeeze(-1) + origin
    return points @ rot.transpose(-1, -2) + origin.unsqueeze(-2)


def inverse_yaw_transform(
    points: torch.Tensor, yaw: torch.Tensor, origin: torch.Tensor
) -> torch.Tensor:
    """Map points from a parent frame into a local yaw frame: R(yaw)^T (p - origin)."""
    rot_t = yaw_matrix(yaw).transpose(-1, -2)
    if points.dim() == origin.dim():
        return (rot_t @ (points - origin).unsqueeze(-1)).squeeze(-1)
    return (points - origin.unsqueeze(-2)) @ rot_t.transpose(-1, -2)


def rotate_yaw(vectors: torch.Tensor, yaw: torch.Tensor) -> torch.Tensor:
    """Rotate direction vectors (..., 3) by yaw (...)."""
    return (yaw_matrix(yaw) @ vectors.unsqueeze(-1)).squeeze(-1)
