"""Reward terms of the low-level controller (paper Table I plus the stability terms
left commented out in the paper's LaTeX source)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from mjlab.entity import Entity
    from mjlab.envs import ManagerBasedRlEnv
    from mjlab.managers.reward_manager import RewardTermCfg
    from mjlab.sensor import ContactSensor

    from leg_manip.tasks.track.mdp.commands import FootTrajectoryCommand


def _cmd(env: ManagerBasedRlEnv, command_name: str) -> FootTrajectoryCommand:
    return env.command_manager.get_term(command_name)  # type: ignore[return-value]


def track_ee_pos_xy(
    env: ManagerBasedRlEnv, command_name: str, std: float
) -> torch.Tensor:
    cmd = _cmd(env, command_name)
    err = (cmd.ee_pos_w() - cmd.target_pos_w)[:, :2]
    return torch.exp(-err.square().sum(-1) / std**2)


def track_ee_pos_z(
    env: ManagerBasedRlEnv, command_name: str, std: float, z_scale: float = 5.0
) -> torch.Tensor:
    """z error amplified by z_scale ("fivefold to promote leg lifting")."""
    cmd = _cmd(env, command_name)
    err = z_scale * (cmd.ee_pos_w() - cmd.target_pos_w)[:, 2]
    return torch.exp(-err.square() / std**2)


def track_ee_dir(
    env: ManagerBasedRlEnv, command_name: str, sigma: float
) -> torch.Tensor:
    """exp(-(1 - theta . theta_d) / sigma)."""
    cmd = _cmd(env, command_name)
    dot = (cmd.ee_dir_w() * cmd.target_dir_w).sum(-1)
    return torch.exp(-(1.0 - dot) / sigma)


class ee_velocity_change:
    """Squared change of the manipulating foot velocity per policy step.

    The paper penalizes |x_ee_ddot|^2 with weight -5. With mjlab's dt-scaled rewards
    a true acceleration would dwarf the tracking terms, so the velocity change per
    step (acceleration * dt) is used instead.
    """

    def __init__(self, cfg: RewardTermCfg, env: ManagerBasedRlEnv):
        self._cmd = _cmd(env, cfg.params["command_name"])
        self._prev = torch.zeros(env.num_envs, 3, device=env.device)
        self._fresh = torch.ones(env.num_envs, dtype=torch.bool, device=env.device)

    def reset(self, env_ids: torch.Tensor | slice | None = None) -> None:
        self._fresh[env_ids] = True

    def __call__(self, env: ManagerBasedRlEnv, command_name: str) -> torch.Tensor:
        del env, command_name
        vel = self._cmd.ee_vel_w()
        out = (vel - self._prev).square().sum(-1) * (~self._fresh).float()
        self._prev = vel.clone()
        self._fresh[:] = False
        return out


class base_velocity_change:
    """Squared change of the base linear velocity per policy step (see above)."""

    def __init__(self, cfg: RewardTermCfg, env: ManagerBasedRlEnv):
        self._robot: Entity = env.scene[cfg.params.get("entity_name", "robot")]
        self._prev = torch.zeros(env.num_envs, 3, device=env.device)
        self._fresh = torch.ones(env.num_envs, dtype=torch.bool, device=env.device)

    def reset(self, env_ids: torch.Tensor | slice | None = None) -> None:
        self._fresh[env_ids] = True

    def __call__(
        self, env: ManagerBasedRlEnv, entity_name: str = "robot"
    ) -> torch.Tensor:
        del env, entity_name
        vel = self._robot.data.root_link_lin_vel_w
        out = (vel - self._prev).square().sum(-1) * (~self._fresh).float()
        self._prev = vel.clone()
        self._fresh[:] = False
        return out


def free_gait(
    env: ManagerBasedRlEnv, command_name: str, sensor_name: str
) -> torch.Tensor:
    """1 if 0 < (support feet in contact) < 3. Support feet are the three feet other
    than the manipulating one; the sensor's primaries are ordered FL, FR, RL, RR."""
    cmd = _cmd(env, command_name)
    sensor: ContactSensor = env.scene[sensor_name]
    assert sensor.data.found is not None
    contact = sensor.data.found > 0  # (N, 4)
    manip = torch.nn.functional.one_hot(cmd.flag_index, num_classes=4).bool()
    n_support = (contact & ~manip).sum(-1)
    return ((n_support > 0) & (n_support < 3)).float()


def manip_foot_ground_contact(
    env: ManagerBasedRlEnv, command_name: str, sensor_name: str
) -> torch.Tensor:
    """1 while the manipulating foot touches the ground."""
    cmd = _cmd(env, command_name)
    sensor: ContactSensor = env.scene[sensor_name]
    assert sensor.data.found is not None
    contact = sensor.data.found > 0
    return contact.gather(1, cmd.flag_index.unsqueeze(-1)).squeeze(-1).float()


def joint_deviation_l2(
    env: ManagerBasedRlEnv, entity_name: str = "robot"
) -> torch.Tensor:
    robot: Entity = env.scene[entity_name]
    return (robot.data.joint_pos - robot.data.default_joint_pos).square().sum(-1)


def torque_limit_violation(
    env: ManagerBasedRlEnv, ratio: float = 0.95, entity_name: str = "robot"
) -> torch.Tensor:
    """Number of actuators above `ratio` of their effort limit."""
    robot: Entity = env.scene[entity_name]
    force = robot.data.actuator_force.abs()
    limit = torch.cat(
        [
            torch.full((len(a.target_ids),), a.cfg.effort_limit, device=env.device)
            for a in robot.actuators
        ]
    )
    return (force > ratio * limit).float().sum(-1)
