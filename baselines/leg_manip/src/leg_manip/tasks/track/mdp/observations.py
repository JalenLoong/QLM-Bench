"""Observation terms of the low-level controller."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from leg_manip.traj import rotate_yaw

if TYPE_CHECKING:
    from mjlab.envs import ManagerBasedRlEnv

    from leg_manip.tasks.track.mdp.commands import FootTrajectoryCommand


def _cmd(env: ManagerBasedRlEnv, command_name: str) -> FootTrajectoryCommand:
    return env.command_manager.get_term(command_name)  # type: ignore[return-value]


def ee_pos_heading(env: ManagerBasedRlEnv, command_name: str) -> torch.Tensor:
    """Manipulating foot position in the robot heading frame (estimator target)."""
    cmd = _cmd(env, command_name)
    return cmd.to_heading(cmd.ee_pos_w())


def ee_dir_heading(env: ManagerBasedRlEnv, command_name: str) -> torch.Tensor:
    """Manipulating calf direction in the robot heading frame."""
    cmd = _cmd(env, command_name)
    return rotate_yaw(cmd.ee_dir_w(), -cmd.base_yaw())


def ee_pos_error_heading(env: ManagerBasedRlEnv, command_name: str) -> torch.Tensor:
    """Target minus current foot position, heading frame (privileged, critic only)."""
    cmd = _cmd(env, command_name)
    return cmd.to_heading(cmd.target_pos_w) - cmd.to_heading(cmd.ee_pos_w())


def traj_phase(env: ManagerBasedRlEnv, command_name: str) -> torch.Tensor:
    return _cmd(env, command_name).phase.unsqueeze(-1)
