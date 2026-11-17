"""MDP pieces shared by the manipulation tasks."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import torch

from leg_manip.tasks.track.mdp.commands import (
    FootTrajectoryCommand,
    FootTrajectoryCommandCfg,
)
from leg_manip.traj import NUM_CTRL, TrajParams, quat_to_yaw

if TYPE_CHECKING:
    from mjlab.entity import Entity
    from mjlab.envs import ManagerBasedRlEnv


@dataclass(kw_only=True)
class ExpertTrajectoryCommandCfg(FootTrajectoryCommandCfg):
    """Expert trajectory: fixed parameters in the object frame, mapped to the world
    with the object's pose at the start of each episode (paper Sec. IV-A)."""

    object_name: str = "object"
    expert_vector: tuple[float, ...] = ()
    duration_s: float = 10.0

    def build(self, env: ManagerBasedRlEnv) -> ExpertTrajectoryCommand:
        return ExpertTrajectoryCommand(self, env)


class ExpertTrajectoryCommand(FootTrajectoryCommand):
    cfg: ExpertTrajectoryCommandCfg

    def __init__(self, cfg: ExpertTrajectoryCommandCfg, env: ManagerBasedRlEnv):
        super().__init__(cfg, env)
        self.before_observation: Callable[[], None] | None = None
        self.object: Entity = env.scene[cfg.object_name]
        vec = torch.tensor(cfg.expert_vector, device=self.device, dtype=torch.float)
        self.expert_object_frame = TrajParams.from_vector(vec, cfg.num_ctrl)

    def object_pose(self, env_ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Object origin (on the ground) and yaw in the sim world frame."""
        pos = self.object.data.root_link_pos_w[env_ids]
        yaw = quat_to_yaw(self.object.data.root_link_quat_w[env_ids])
        return pos, yaw

    def _sample_params(self, env_ids: torch.Tensor) -> tuple[TrajParams, torch.Tensor]:
        n = len(env_ids)
        e = self.expert_object_frame
        batch = TrajParams(
            e.flag.expand(n).clone(),
            e.ctrl.expand(n, -1, -1).clone(),
            e.log_w.expand(n, -1).clone(),
            e.dir0.expand(n, -1).clone(),
            e.dir1.expand(n, -1).clone(),
        )
        pos, yaw = self.object_pose(env_ids)
        duration = torch.full((n,), self.cfg.duration_s, device=self.device)
        return batch.to_parent(yaw, pos), duration


def trajectory_command_observation(
    env: ManagerBasedRlEnv, command_name: str
) -> torch.Tensor:
    """Prepare a planner frame after sensing, before actor history is appended.

    The rollout temporarily supplies the callback. Other command observations
    (critic/estimator) then read the same updated trajectory without another push.
    """
    cmd: ExpertTrajectoryCommand = env.command_manager.get_term(command_name)
    if cmd.before_observation is not None:
        cmd.before_observation()
    return cmd.command


def reset_robot_and_object(
    env: ManagerBasedRlEnv,
    env_ids: torch.Tensor | None,
    robot_name: str = "robot",
    object_name: str = "object",
    robot_height: float = 0.30,
    robot_yaw_range: tuple[float, float] = (-math.pi, math.pi),
    distance_range: tuple[float, float] = (1.0, 1.8),
    bearing_range_deg: tuple[float, float] = (-20.0, 20.0),
    object_yaw_range_deg: tuple[float, float] = (-15.0, 15.0),
    object_joint_range: tuple[float, float] = (0.0, 0.0),
) -> None:
    """Place the robot at the env origin and the object in a sector in front of it.

    Paper evaluation: objects appear in a 40 deg sector up to 3 m in front of the
    robot (Aliengo). The object +x axis points away from the robot, so the robot
    faces the object's front face; object_yaw_range adds a misalignment.
    """
    if env_ids is None:
        env_ids = torch.arange(env.num_envs, device=env.device)
    n, d = len(env_ids), env.device
    robot: Entity = env.scene[robot_name]
    obj: Entity = env.scene[object_name]
    origins = env.scene.env_origins[env_ids]

    def u(lo_hi):
        return torch.empty(n, device=d).uniform_(*lo_hi)

    robot_yaw = u(robot_yaw_range)
    root = robot.data.default_root_state[env_ids].clone()
    root[:, 0:3] = origins
    root[:, 2] = robot_height
    root[:, 3:7] = _yaw_quat(robot_yaw)
    root[:, 7:] = 0.0
    robot.write_root_state_to_sim(root, env_ids=env_ids)

    dist = u(distance_range)
    bearing = robot_yaw + torch.deg2rad(u(bearing_range_deg))
    obj_pos = origins.clone()
    obj_pos[:, 0] += dist * torch.cos(bearing)
    obj_pos[:, 1] += dist * torch.sin(bearing)
    obj_pos[:, 2] = 0.0
    obj_yaw = bearing + torch.deg2rad(u(object_yaw_range_deg))
    obj.write_mocap_pose_to_sim(
        torch.cat([obj_pos, _yaw_quat(obj_yaw)], dim=-1), env_ids=env_ids
    )
    joint_pos = u(object_joint_range).unsqueeze(-1)
    obj.write_joint_state_to_sim(
        joint_pos, torch.zeros_like(joint_pos), env_ids=env_ids
    )


def _yaw_quat(yaw: torch.Tensor) -> torch.Tensor:
    zero = torch.zeros_like(yaw)
    return torch.stack([torch.cos(yaw / 2), zero, zero, torch.sin(yaw / 2)], dim=-1)


def object_joint_pos(
    env: ManagerBasedRlEnv, object_name: str = "object"
) -> torch.Tensor:
    obj: Entity = env.scene[object_name]
    return obj.data.joint_pos[:, 0]


def default_expert_vector(
    flag: int,
    ctrl: list[tuple[float, float, float]],
    weights: list[float],
    dir0: tuple[float, float, float],
    dir1: tuple[float, float, float],
) -> tuple[float, ...]:
    """Pack a hand-designed object-frame trajectory into the 31-dim vector."""
    assert len(ctrl) == NUM_CTRL and len(weights) == NUM_CTRL
    p = TrajParams(
        torch.tensor(float(flag)),
        torch.tensor(ctrl, dtype=torch.float),
        torch.log(torch.tensor(weights, dtype=torch.float)),
        torch.nn.functional.normalize(torch.tensor(dir0), dim=0),
        torch.nn.functional.normalize(torch.tensor(dir1), dim=0),
    )
    return tuple(p.to_vector().tolist())
