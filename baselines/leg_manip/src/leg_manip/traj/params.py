"""Trajectory parameters p: the interface between planner and controller.

Layout of the flat vector (K control points, default K = 6, 31 dims):

    [flag (1) | ctrl points (3K) | log weights (K) | start dir (3) | end dir (3)]

- flag: manipulating forelimb, 0 = front left (FL), 1 = front right (FR).
- ctrl points / weights: rational Bézier curve of the foot (Eq. 1). Weights are
  stored as natural logs because the paper samples them over [1, 2000].
- start / end dir: unit vectors of the calf direction (knee -> foot), interpolated
  with SLERP (Eq. 2). The paper's orientation reward uses a dot product, so the
  "orientation" is a direction, not a full rotation.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from leg_manip.traj.bezier import rational_bezier, slerp_unit
from leg_manip.traj.frames import apply_yaw_transform, inverse_yaw_transform, rotate_yaw

NUM_CTRL = 6


def param_dim(num_ctrl: int = NUM_CTRL) -> int:
    return 1 + 3 * num_ctrl + num_ctrl + 6


@dataclass
class TrajParams:
    flag: torch.Tensor  # (...,)
    ctrl: torch.Tensor  # (..., K, 3)
    log_w: torch.Tensor  # (..., K)
    dir0: torch.Tensor  # (..., 3)
    dir1: torch.Tensor  # (..., 3)

    @property
    def num_ctrl(self) -> int:
        return self.ctrl.shape[-2]

    @property
    def batch_shape(self) -> torch.Size:
        return self.flag.shape

    def to_vector(self) -> torch.Tensor:
        return torch.cat(
            [
                self.flag.unsqueeze(-1),
                self.ctrl.flatten(-2),
                self.log_w,
                self.dir0,
                self.dir1,
            ],
            dim=-1,
        )

    @classmethod
    def from_vector(cls, vec: torch.Tensor, num_ctrl: int = NUM_CTRL) -> TrajParams:
        """Inverse of :meth:`to_vector`. Snaps the flag to {0, 1} and renormalizes
        directions, which matters for planner outputs."""
        assert vec.shape[-1] == param_dim(num_ctrl), vec.shape
        k = num_ctrl
        flag = (vec[..., 0] > 0.5).to(vec.dtype)
        ctrl = vec[..., 1 : 1 + 3 * k].unflatten(-1, (k, 3))
        log_w = vec[..., 1 + 3 * k : 1 + 4 * k]
        dir0 = torch.nn.functional.normalize(vec[..., 1 + 4 * k : 4 + 4 * k], dim=-1)
        dir1 = torch.nn.functional.normalize(vec[..., 4 + 4 * k : 7 + 4 * k], dim=-1)
        return cls(flag, ctrl, log_w, dir0, dir1)

    def position(self, t: torch.Tensor) -> torch.Tensor:
        """Foot target at phase t (...,) -> (..., 3)."""
        return rational_bezier(self.ctrl, self.log_w.exp(), t.clamp(0.0, 1.0))

    def direction(self, t: torch.Tensor) -> torch.Tensor:
        """Calf direction target at phase t (...,) -> (..., 3)."""
        return slerp_unit(self.dir0, self.dir1, t.clamp(0.0, 1.0))

    def to_parent(self, yaw: torch.Tensor, origin: torch.Tensor) -> TrajParams:
        """Express in the parent frame of a local yaw frame (e.g. object -> world)."""
        return TrajParams(
            self.flag,
            apply_yaw_transform(self.ctrl, yaw, origin),
            self.log_w,
            rotate_yaw(self.dir0, yaw),
            rotate_yaw(self.dir1, yaw),
        )

    def to_local(self, yaw: torch.Tensor, origin: torch.Tensor) -> TrajParams:
        """Express in a local yaw frame (e.g. world -> object)."""
        return TrajParams(
            self.flag,
            inverse_yaw_transform(self.ctrl, yaw, origin),
            self.log_w,
            rotate_yaw(self.dir0, -yaw),
            rotate_yaw(self.dir1, -yaw),
        )

    def index(self, idx) -> TrajParams:
        return TrajParams(
            self.flag[idx],
            self.ctrl[idx],
            self.log_w[idx],
            self.dir0[idx],
            self.dir1[idx],
        )
