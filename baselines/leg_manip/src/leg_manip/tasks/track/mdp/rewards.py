"""Reward terms of the low-level controller (paper Table I plus the stability terms
left commented out in the paper's LaTeX source)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from leg_manip.traj import quat_to_yaw

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


def track_ee_pos_fine(
    env: ManagerBasedRlEnv, command_name: str, std: float
) -> torch.Tensor:
    """Narrow 3D Gaussian for centimetre-level placement near the target."""
    cmd = _cmd(env, command_name)
    err = cmd.ee_pos_w() - cmd.target_pos_w
    return torch.exp(-err.square().sum(-1) / std**2)


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
    env: ManagerBasedRlEnv,
    command_name: str,
    sensor_name: str,
    lift_height: float = 0.05,
) -> torch.Tensor:
    """Reward support with the requested manipulating leg clear of the ground.

    All three supporting feet may stay down for a stationary manipulation. A
    raised hind leg cannot substitute for the commanded foreleg. Low targets
    still allow ground interaction. Sensor primaries are FL, FR, RL, RR.
    """
    cmd = _cmd(env, command_name)
    sensor: ContactSensor = env.scene[sensor_name]
    assert sensor.data.found is not None
    contact = sensor.data.found > 0  # (N, 4)
    manip = torch.nn.functional.one_hot(cmd.flag_index, num_classes=4).bool()
    n_support = (contact & ~manip).sum(-1)
    manipulating_contact = (contact & manip).any(-1)
    needs_lift = _needs_lift(env, cmd, lift_height)
    return ((n_support > 0) & (~needs_lift | ~manipulating_contact)).float()


def _needs_lift(
    env: ManagerBasedRlEnv, cmd: FootTrajectoryCommand, lift_height: float
) -> torch.Tensor:
    target_height = cmd.target_pos_w[:, 2] - env.scene.env_origins[:, 2]
    return target_height > lift_height


def manip_foot_ground_contact(
    env: ManagerBasedRlEnv,
    command_name: str,
    sensor_name: str,
    lift_height: float = 0.05,
) -> torch.Tensor:
    """Penalize manipulating-foot ground contact only for airborne targets."""
    cmd = _cmd(env, command_name)
    sensor: ContactSensor = env.scene[sensor_name]
    assert sensor.data.found is not None
    contact = sensor.data.found > 0
    selected = contact.gather(1, cmd.flag_index.unsqueeze(-1)).squeeze(-1)
    return (selected & _needs_lift(env, cmd, lift_height)).float()


def manip_foot_load_share(
    env: ManagerBasedRlEnv,
    command_name: str,
    sensor_name: str,
    lift_height: float = 0.05,
) -> torch.Tensor:
    """Manipulating foot's share of the vertical ground reaction, for raised targets.

    The contact terms only change once the foot is fully unloaded, which needs a
    whole-body weight shift first. This dense term rewards that shift as it
    happens. Sensor primaries are FL, FR, RL, RR with net forces from the terrain.
    """
    cmd = _cmd(env, command_name)
    sensor: ContactSensor = env.scene[sensor_name]
    assert sensor.data.force is not None
    load = sensor.data.force[..., 2].abs()  # (N, 4)
    selected = load.gather(1, cmd.flag_index.unsqueeze(-1)).squeeze(-1)
    share = selected / load.sum(-1).clamp(min=1.0)
    return share * _needs_lift(env, cmd, lift_height).float()


def base_approach_velocity(
    env: ManagerBasedRlEnv, command_name: str, speed: float, reach: float
) -> torch.Tensor:
    """Base speed toward the target (capped at `speed`, normalized) while the target
    is farther than `reach` from the manipulating foot in xy; 1 within reach.

    The xy Gaussian is nearly flat about 1 m from the target and a standing tripod
    already earns the support reward, so walking toward far targets had no signal.
    """
    cmd = _cmd(env, command_name)
    offset = (cmd.target_pos_w - cmd.ee_pos_w())[:, :2]
    dist = offset.norm(dim=-1)
    direction = offset / dist.clamp(min=1e-6).unsqueeze(-1)
    vel = cmd.robot.data.root_link_lin_vel_w[:, :2]
    toward = ((vel * direction).sum(-1) / speed).clamp(0.0, 1.0)
    return torch.where(dist <= reach, torch.ones_like(toward), toward)


def base_heading_to_target(
    env: ManagerBasedRlEnv,
    command_name: str,
    reference: tuple[float, float],
    std: float,
    blend_dist: float,
) -> torch.Tensor:
    """Gaussian in the target's bearing, seen from the manipulating foot's rest point.

    Nothing else ties the base yaw to the target: the full-range pilots turned
    side-on, held the foot beside the trunk and kicked sideways, so the head camera
    (+-43.5 deg) lost the object within a second. `reference` is the FL rest point
    (x, y) in the heading frame (mirrored for FR), so targets ahead of that leg count
    as aligned. The bearing term fades out linearly within `blend_dist` of it,
    where the bearing is undefined (e.g. lifting the foot in place).
    """
    cmd = _cmd(env, command_name)
    yaw = quat_to_yaw(cmd.robot.data.root_link_quat_w)
    offset = (cmd.target_pos_w - cmd.robot.data.root_link_pos_w)[:, :2]
    cos, sin = torch.cos(yaw), torch.sin(yaw)
    side = 1.0 - 2.0 * cmd.flag_index.float()  # FL is on +y, FR on -y
    x = cos * offset[:, 0] + sin * offset[:, 1] - reference[0]
    y = -sin * offset[:, 0] + cos * offset[:, 1] - side * reference[1]
    aligned = torch.exp(-torch.atan2(y, x).square() / std**2)
    blend = (torch.hypot(x, y) / blend_dist).clamp(max=1.0)
    return 1.0 - blend * (1.0 - aligned)


def base_heading_along_dir(
    env: ManagerBasedRlEnv,
    command_name: str,
    std: float,
    reach: float,
    min_horizontal: float,
) -> torch.Tensor:
    """Gaussian in the angle between the base heading and the commanded calf
    direction's xy part, paid only while the foot is within `reach` (xy) of the
    target; 0 farther out, where the bearing term above steers the base.

    That bearing term fades out once the foot is on the target, so slow contact
    and hold phases left the yaw free: closing the dishwasher, the heading pilots
    stood side-on with the door 56-73 deg off the camera axis. Both expert calf
    directions point into the object. The angle fades out linearly as the
    direction's xy norm drops below `min_horizontal` (calf pointing straight down).
    """
    cmd = _cmd(env, command_name)
    yaw = quat_to_yaw(cmd.robot.data.root_link_quat_w)
    d = cmd.target_dir_w[:, :2]
    angle = torch.atan2(d[:, 1], d[:, 0]) - yaw
    angle = torch.atan2(torch.sin(angle), torch.cos(angle))
    aligned = torch.exp(-angle.square() / std**2)
    blend = (d.norm(dim=-1) / min_horizontal).clamp(max=1.0)
    near = (cmd.ee_pos_w() - cmd.target_pos_w)[:, :2].norm(dim=-1) <= reach
    return near.float() * (1.0 - blend * (1.0 - aligned))


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
