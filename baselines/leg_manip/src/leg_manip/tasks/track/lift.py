"""Isolated near-foot skill stage; passing it does not qualify a task expert."""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from mjlab.envs import ManagerBasedRlEnvCfg

from leg_manip.tasks.track.env_cfg import CMD, make_track_env_cfg
from leg_manip.tasks.track.mdp.commands import (
    FootTrajectoryCommand,
    FootTrajectoryCommandCfg,
)
from leg_manip.tasks.track.rl_cfg import TrackRunnerCfg, track_go2_runner_cfg
from leg_manip.traj import TrajParams


@dataclass(kw_only=True)
class LiftTrajectoryCommandCfg(FootTrajectoryCommandCfg):
    lift_range: tuple[float, float] = (0.06, 0.12)
    duration_s: float = 3.0
    forced_leg: int | None = None
    """None samples both forelegs; 0/1 isolates FL/FR during acceptance."""

    def build(self, env) -> LiftTrajectoryCommand:
        if self.forced_leg not in (None, 0, 1):
            raise ValueError("forced_leg must be None, 0 or 1")
        if not (
            0 < self.lift_range[0] <= self.lift_range[1]
            and all(math.isfinite(x) for x in self.lift_range)
            and math.isfinite(self.duration_s)
            and self.duration_s > 0
        ):
            raise ValueError("lift range and duration must be positive and finite")
        return LiftTrajectoryCommand(self, env)


class LiftTrajectoryCommand(FootTrajectoryCommand):
    cfg: LiftTrajectoryCommandCfg

    def _sample_params(self, env_ids: torch.Tensor):
        # Called after mj_forward by the base command's deferred reset path.
        n = len(env_ids)
        if self.cfg.forced_leg is None:
            flag = torch.randint(0, 2, (n,), device=self.device)
        else:
            flag = torch.full((n,), self.cfg.forced_leg, device=self.device)
        start = self.robot.data.site_pos_w[env_ids, self._foot_site_ids[flag]].clone()
        knee = self.robot.data.body_link_pos_w[env_ids, self._calf_body_ids[flag]]
        direction = torch.nn.functional.normalize(start - knee, dim=-1)
        # Resets spawn the base about 8 cm above its standing height, so the fresh
        # foot is still airborne. Start the lift on the ground below it.
        origin_z = self._env.scene.env_origins[env_ids, 2]
        start[:, 2] = origin_z + self.cfg.foot_rest_height
        end = start.clone()
        end[:, 2] += torch.empty(n, device=self.device).uniform_(*self.cfg.lift_range)
        phase = torch.linspace(0, 1, self.cfg.num_ctrl, device=self.device)
        ctrl = start[:, None] + phase[None, :, None] * (end - start)[:, None]
        params = TrajParams(
            flag.float(),
            ctrl,
            torch.zeros(n, self.cfg.num_ctrl, device=self.device),
            direction,
            direction.clone(),
        )
        return params, torch.full((n,), self.cfg.duration_s, device=self.device)


def make_lift_env_cfg(
    play: bool = False, forced_leg: int | None = None
) -> ManagerBasedRlEnvCfg:
    cfg = make_track_env_cfg(play=play)
    cfg.commands[CMD] = LiftTrajectoryCommandCfg(
        forced_leg=forced_leg, resampling_time_range=(1e9, 1e9)
    )
    # First verify the requested leg in simple physics, before robustness or
    # locomotion training. Keep randomized reset pose/joints and actor noise.
    cfg.events = {
        name: term
        for name, term in cfg.events.items()
        if name in ("reset_base", "reset_robot_joints")
    }
    cfg.episode_length_s = 10.0
    return cfg


def lift_go2_runner_cfg() -> TrackRunnerCfg:
    cfg = track_go2_runner_cfg()
    cfg.experiment_name = "legmanip_lift_go2"
    cfg.max_iterations = 2000
    cfg.save_interval = 250
    cfg.wandb_project = "WAM-Policy"
    return cfg
