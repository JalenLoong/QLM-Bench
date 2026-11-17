"""Capture physical object joints before mjlab overwrites terminal states."""

from __future__ import annotations

import torch
from mjlab.envs import ManagerBasedRlEnv
from mjlab.managers.recorder_manager import RecorderTerm, RecorderTermCfg

from leg_manip.tasks.manip.mdp import object_joint_pos

OBJECT_JOINT_RECORDER = "object_joint"


class ObjectJointRecorder(RecorderTerm):
    """One post-action joint sample per env, including auto-reset transitions."""

    def __init__(self, cfg: RecorderTermCfg, env: ManagerBasedRlEnv):
        super().__init__(cfg, env)
        self.joint = torch.zeros(self.num_envs, device=self.device)
        self._terminal_joint = torch.zeros_like(self.joint)

    def record_pre_reset(self, env_ids: torch.Tensor) -> None:
        # qpos is already integrated even though derived kinematics await forward().
        self._terminal_joint[env_ids] = object_joint_pos(self._env)[env_ids]

    def record_post_step(self) -> None:
        self.joint = torch.where(
            self._env.reset_buf & self._env.cfg.auto_reset,
            self._terminal_joint,
            object_joint_pos(self._env),
        )
