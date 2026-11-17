"""Joint position action with a first-order low-pass filter (paper Sec. IV-B:
"passed through a low-pass filter followed by joint-level PD controller")."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import torch
from mjlab.envs.mdp.actions import JointPositionActionCfg
from mjlab.envs.mdp.actions.actions import JointPositionAction

if TYPE_CHECKING:
    from mjlab.envs import ManagerBasedRlEnv


@dataclass(kw_only=True)
class FilteredJointPositionActionCfg(JointPositionActionCfg):
    cutoff_hz: float = 10.0
    """Cutoff of the filter, applied at the physics rate. <= 0 disables it."""

    def build(self, env: ManagerBasedRlEnv) -> FilteredJointPositionAction:
        return FilteredJointPositionAction(self, env)


class FilteredJointPositionAction(JointPositionAction):
    cfg: FilteredJointPositionActionCfg

    def __init__(self, cfg: FilteredJointPositionActionCfg, env: ManagerBasedRlEnv):
        super().__init__(cfg, env)
        dt = env.physics_dt
        tau = 1.0 / (2 * math.pi * cfg.cutoff_hz) if cfg.cutoff_hz > 0 else 0.0
        self._alpha = dt / (dt + tau)
        self._filtered = self._entity.data.default_joint_pos[
            :, self._target_ids
        ].clone()

    def reset(self, env_ids: torch.Tensor | slice | None = None) -> None:
        super().reset(env_ids)
        default = self._entity.data.default_joint_pos[:, self._target_ids]
        self._filtered[env_ids] = default[env_ids]

    def apply_actions(self) -> None:
        self._filtered += self._alpha * (self._processed_actions - self._filtered)
        encoder_bias = self._entity.data.encoder_bias[:, self._target_ids]
        self._entity.set_joint_position_target(
            self._filtered - encoder_bias, joint_ids=self._target_ids
        )
