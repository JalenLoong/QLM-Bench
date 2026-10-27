"""Planner inference wrapper with the n_obs_steps observation history."""

from __future__ import annotations

from pathlib import Path

import torch

from leg_manip.planner.model import load_checkpoint


class PlannerPolicy:
    def __init__(self, ckpt_dir: str | Path, device: str = "cuda") -> None:
        self.policy, self.meta = load_checkpoint(ckpt_dir, device)
        self.n_obs_steps = self.policy.n_obs_steps
        self.device = device
        self._clouds: torch.Tensor | None = None
        self._states: torch.Tensor | None = None

    @torch.no_grad()
    def __call__(
        self, point_cloud: torch.Tensor, state: torch.Tensor, first: bool
    ) -> torch.Tensor:
        """(N, P, 3), (N, 17) -> trajectory parameter vectors (N, 31), env frame.

        On the first call of an episode the history is filled with the current
        observation (same as edge padding during training).
        """
        cloud = point_cloud.to(self.device, torch.float32).unsqueeze(1)
        st = state.to(self.device, torch.float32).unsqueeze(1)
        if first or self._clouds is None:
            self._clouds = cloud.repeat(1, self.n_obs_steps, 1, 1)
            self._states = st.repeat(1, self.n_obs_steps, 1)
        else:
            self._clouds = torch.cat([self._clouds[:, 1:], cloud], 1)
            self._states = torch.cat([self._states[:, 1:], st], 1)
        out = self.policy.predict_action(
            {"point_cloud": self._clouds, "agent_pos": self._states}
        )
        return out["action"][:, 0]
