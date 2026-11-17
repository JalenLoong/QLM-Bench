"""Foot trajectory command: turns trajectory parameters p into the controller command.

The command term owns the current trajectory parameters of every env (world frame),
advances the phase and produces the 16-dim command of the paper:

    [flag (1) | x_t (3) | x_{t+0.3s}, x_{t+0.6s}, x_{t+0.9s} (9) | calf dir_t (3)]

with points and direction expressed in the robot heading frame (base x/y, base yaw,
height above the environment origin). For training it samples curves; experts override
:meth:`FootTrajectoryCommand._sample_params`, and planner rollouts push parameters in
with :meth:`FootTrajectoryCommand.set_params`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import torch
from mjlab.managers.command_manager import CommandTerm, CommandTermCfg

from leg_manip.assets.go2 import MANIP_CALF_BODIES, MANIP_FOOT_SITES
from leg_manip.traj import (
    TrajParams,
    inverse_yaw_transform,
    quat_to_yaw,
    rotate_yaw,
    slerp_unit,
)

if TYPE_CHECKING:
    from mjlab.entity import Entity
    from mjlab.envs import ManagerBasedRlEnv
    from mjlab.viewer.debug_visualizer import DebugVisualizer


@dataclass(kw_only=True)
class FootTrajectoryCommandCfg(CommandTermCfg):
    entity_name: str = "robot"
    foot_site_names: tuple[str, str] = MANIP_FOOT_SITES
    calf_body_names: tuple[str, str] = MANIP_CALF_BODIES
    num_ctrl: int = 6
    future_offsets_s: tuple[float, ...] = (0.3, 0.6, 0.9)
    sample_on_reset: bool = True
    """Sample parameters on resample (random curves here, expert curves in task
    subclasses). False: keep the parameters pushed in with set_params (planner)."""
    foot_rest_height: float = 0.022
    """Foot site height above flat ground when standing (Go2 foot sphere radius)."""

    @dataclass
    class Ranges:
        # Control points, in the robot heading frame at sampling time (paper: 4 m x
        # 4 m area, z in [0.01, 1.2] m for Aliengo; scaled down for Go2).
        ctrl_x: tuple[float, float] = (-1.5, 1.5)
        ctrl_y: tuple[float, float] = (-1.5, 1.5)
        ctrl_z: tuple[float, float] = (0.02, 0.6)
        weight: tuple[float, float] = (1.0, 2000.0)
        weight_log_uniform: bool = True
        duration_s: tuple[float, float] = (8.0, 20.0)
        # Calf directions: uniform on the cap cos(angle to axis) in dir_cos.
        dir_axis: tuple[float, float, float] = (1.0, 0.0, -1.0)
        dir_cos: tuple[float, float] = (0.0, 1.0)
        start_at_foot_prob: float = 0.5
        """Probability that the curve starts at the current foot position."""
        fr_prob: float = 0.5
        """Probability of using the front right leg (flag = 1)."""

    ranges: Ranges = field(default_factory=Ranges)

    @dataclass
    class VizCfg:
        num_curve_points: int = 20
        curve_color: tuple[float, float, float, float] = (0.2, 0.5, 1.0, 0.6)
        target_color: tuple[float, float, float, float] = (1.0, 0.8, 0.0, 0.9)

    viz: VizCfg = field(default_factory=VizCfg)

    def build(self, env: ManagerBasedRlEnv) -> FootTrajectoryCommand:
        return FootTrajectoryCommand(self, env)


class FootTrajectoryCommand(CommandTerm):
    cfg: FootTrajectoryCommandCfg

    def __init__(self, cfg: FootTrajectoryCommandCfg, env: ManagerBasedRlEnv):
        super().__init__(cfg, env)
        self.robot: Entity = env.scene[cfg.entity_name]
        site_ids, _ = self.robot.find_sites(cfg.foot_site_names, preserve_order=True)
        body_ids, _ = self.robot.find_bodies(cfg.calf_body_names, preserve_order=True)
        self._foot_site_ids = torch.tensor(site_ids, device=self.device)
        self._calf_body_ids = torch.tensor(body_ids, device=self.device)
        self._arange = torch.arange(self.num_envs, device=self.device)

        n, k, d = self.num_envs, cfg.num_ctrl, self.device
        self.params = TrajParams(
            flag=torch.zeros(n, device=d),
            ctrl=torch.zeros(n, k, 3, device=d),
            log_w=torch.zeros(n, k, device=d),
            dir0=torch.tensor([0.0, 0.0, -1.0], device=d).repeat(n, 1),
            dir1=torch.tensor([0.0, 0.0, -1.0], device=d).repeat(n, 1),
        )
        self.duration = torch.full((n,), 10.0, device=d)
        self.phase_time = torch.zeros(n, device=d)
        self._future = torch.tensor(cfg.future_offsets_s, device=d)
        self.target_pos_w = torch.zeros(n, 3, device=d)
        self.target_dir_w = torch.zeros(n, 3, device=d)
        self.future_pos_w = torch.zeros(n, len(cfg.future_offsets_s), 3, device=d)
        self._command = torch.zeros(
            n, 1 + 3 * (2 + len(cfg.future_offsets_s)), device=d
        )
        self._max_steps = env.max_episode_length

        # Envs whose parameters must be (re)sampled. Sampling is deferred to the next
        # _update_command, which runs after mj_forward: during a reset the derived
        # kinematics (base and foot poses) are still those of the previous episode.
        self._pending = torch.zeros(n, dtype=torch.bool, device=d)

        self.metrics["ee_pos_error"] = torch.zeros(n, device=d)
        self.metrics["ee_dir_error"] = torch.zeros(n, device=d)

    # Quantities of the manipulating leg.

    @property
    def flag_index(self) -> torch.Tensor:
        return self.params.flag.long()

    def ee_pos_w(self) -> torch.Tensor:
        sites = self._foot_site_ids[self.flag_index]
        return self.robot.data.site_pos_w[self._arange, sites]

    def ee_vel_w(self) -> torch.Tensor:
        sites = self._foot_site_ids[self.flag_index]
        return self.robot.data.site_lin_vel_w[self._arange, sites]

    def ee_dir_w(self) -> torch.Tensor:
        knee = self.robot.data.body_link_pos_w[
            self._arange, self._calf_body_ids[self.flag_index]
        ]
        return torch.nn.functional.normalize(self.ee_pos_w() - knee, dim=-1)

    def base_yaw(self) -> torch.Tensor:
        return quat_to_yaw(self.robot.data.root_link_quat_w)

    def _heading_origin(self) -> torch.Tensor:
        """Translate x/y with the base, keeping z relative to the environment."""
        origin = self.robot.data.root_link_pos_w.clone()
        origin[:, 2] = self._env.scene.env_origins[:, 2]
        return origin

    def to_heading(self, points_w: torch.Tensor) -> torch.Tensor:
        """World points -> heading frame, with environment-absolute heights."""
        return inverse_yaw_transform(points_w, self.base_yaw(), self._heading_origin())

    @property
    def phase(self) -> torch.Tensor:
        return (self.phase_time / self.duration).clamp(0.0, 1.0)

    # External control (expert data collection and planner rollouts).

    def set_params(
        self,
        params_w: TrajParams,
        env_ids: torch.Tensor | None = None,
        duration: torch.Tensor | float | None = None,
        reset_phase: bool = False,
    ) -> None:
        """Overwrite the world-frame trajectory parameters of some envs."""
        if env_ids is None:
            env_ids = self._arange
        self.params.flag[env_ids] = params_w.flag
        self.params.ctrl[env_ids] = params_w.ctrl
        self.params.log_w[env_ids] = params_w.log_w
        self.params.dir0[env_ids] = params_w.dir0
        self.params.dir1[env_ids] = params_w.dir1
        if duration is not None:
            self.duration[env_ids] = torch.as_tensor(
                duration, device=self.device, dtype=torch.float
            )
        if reset_phase:
            self.phase_time[env_ids] = 0.0
        self._update_command(env_ids)

    # CommandTerm interface.

    @property
    def command(self) -> torch.Tensor:
        return self._command

    def compute(self, dt, env_ids: torch.Tensor | None = None) -> None:
        if env_ids is None:
            self.phase_time += dt
        else:
            self.phase_time[env_ids] += dt
        super().compute(dt, env_ids)

    def _update_metrics(self) -> None:
        pos_err = torch.norm(self.ee_pos_w() - self.target_pos_w, dim=-1)
        cos = (self.ee_dir_w() * self.target_dir_w).sum(-1).clamp(-1.0, 1.0)
        valid = (~self._pending).float()
        self.metrics["ee_pos_error"] += valid * pos_err / self._max_steps
        self.metrics["ee_dir_error"] += valid * torch.acos(cos) / self._max_steps

    def _resample_command(self, env_ids: torch.Tensor) -> None:
        self.phase_time[env_ids] = 0.0
        if self.cfg.sample_on_reset:
            self._pending[env_ids] = True

    def _sample_params(self, env_ids: torch.Tensor) -> tuple[TrajParams, torch.Tensor]:
        """World-frame parameters and durations for env_ids. Called with fresh
        kinematics. Subclasses (expert tasks) override this."""
        return self._sample_random(env_ids)

    def _sample_random(self, env_ids: torch.Tensor) -> tuple[TrajParams, torch.Tensor]:
        r = self.cfg.ranges
        n, k, d = len(env_ids), self.cfg.num_ctrl, self.device

        def u(lo_hi, *shape):
            return torch.empty(*shape, device=d).uniform_(*lo_hi)

        ctrl = torch.stack(
            [u(r.ctrl_x, n, k), u(r.ctrl_y, n, k), u(r.ctrl_z, n, k)], dim=-1
        )
        if r.weight_log_uniform:
            log_w = u((math.log(r.weight[0]), math.log(r.weight[1])), n, k)
        else:
            log_w = u(r.weight, n, k).log()
        axis = torch.nn.functional.normalize(torch.tensor(r.dir_axis, device=d), dim=0)
        dirs = _sample_cap(axis, r.dir_cos, 2 * n).view(n, 2, 3)
        flag = (torch.rand(n, device=d) < r.fr_prob).float()
        local = TrajParams(flag, ctrl, log_w, dirs[:, 0], dirs[:, 1])

        # Heading frame -> world. Heights are absolute above each env origin.
        yaw = self.base_yaw()[env_ids]
        origin = self._heading_origin()[env_ids]
        params_w = local.to_parent(yaw, origin)

        start_here = torch.rand(n, device=d) < r.start_at_foot_prob
        sites = self._foot_site_ids[flag.long()]
        foot_w = self.robot.data.site_pos_w[env_ids, sites].clone()
        # Resets spawn the base about 8 cm above its standing height, so the fresh
        # foot is still airborne. Start on the ground below it.
        foot_w[:, 2] = origin[:, 2] + self.cfg.foot_rest_height
        params_w.ctrl[:, 0] = torch.where(
            start_here.unsqueeze(-1), foot_w, params_w.ctrl[:, 0]
        )
        return params_w, u(r.duration_s, n)

    def _update_command(self, env_ids: torch.Tensor | None) -> None:
        pending = self._pending.nonzero().flatten()
        if len(pending) > 0:
            self._pending[pending] = False
            params, duration = self._sample_params(pending)
            self.set_params(params, pending, duration)
        idx = self._arange if env_ids is None else env_ids
        p = self.params.index(idx)
        dur = self.duration[idx]
        t = self.phase[idx]
        self.target_pos_w[idx] = p.position(t)
        self.target_dir_w[idx] = slerp_unit(p.dir0, p.dir1, t)
        t_fut = (t.unsqueeze(-1) + self._future / dur.unsqueeze(-1)).clamp(max=1.0)
        fut = torch.stack([p.position(t_fut[:, j]) for j in range(t_fut.shape[1])], 1)
        self.future_pos_w[idx] = fut

        yaw = self.base_yaw()[idx]
        origin = self._heading_origin()[idx]
        tgt_h = inverse_yaw_transform(self.target_pos_w[idx], yaw, origin)
        fut_h = inverse_yaw_transform(fut, yaw, origin)
        dir_h = rotate_yaw(self.target_dir_w[idx], -yaw)
        self._command[idx] = torch.cat(
            [p.flag.unsqueeze(-1), tgt_h, fut_h.flatten(1), dir_h], dim=-1
        )

    def _debug_vis_impl(self, visualizer: DebugVisualizer) -> None:
        env_indices = visualizer.get_env_indices(self.num_envs)
        ts = torch.linspace(0, 1, self.cfg.viz.num_curve_points, device=self.device)
        for b in env_indices:
            p = self.params.index(b)
            curve = _curve_points(p, ts)
            for i, pt in enumerate(curve.cpu().numpy()):
                visualizer.add_sphere(
                    center=pt,
                    radius=0.012,
                    color=self.cfg.viz.curve_color,
                    label=f"curve_{b}_{i}",
                )
            visualizer.add_sphere(
                center=self.target_pos_w[b].cpu().numpy(),
                radius=0.03,
                color=self.cfg.viz.target_color,
                label=f"foot_target_{b}",
            )
            start = self.target_pos_w[b].cpu().numpy()
            visualizer.add_arrow(
                start=start,
                end=start + 0.15 * self.target_dir_w[b].cpu().numpy(),
                color=self.cfg.viz.target_color,
                width=0.01,
                label=f"foot_dir_{b}",
            )


def _curve_points(p: TrajParams, ts: torch.Tensor) -> torch.Tensor:
    """Sample one env's curve at phases ts (M,) -> (M, 3)."""
    m = ts.shape[0]
    ctrl = p.ctrl.unsqueeze(0).expand(m, -1, -1)
    log_w = p.log_w.unsqueeze(0).expand(m, -1)
    single = TrajParams(p.flag.expand(m), ctrl, log_w, p.dir0, p.dir1)
    return single.position(ts)


def _sample_cap(
    axis: torch.Tensor, cos_range: tuple[float, float], n: int
) -> torch.Tensor:
    """Uniform unit vectors whose cosine to `axis` lies in cos_range, shape (n, 3)."""
    cos = torch.empty(n, device=axis.device).uniform_(*cos_range)
    sin = torch.sqrt((1 - cos * cos).clamp(min=0.0))
    phi = torch.empty(n, device=axis.device).uniform_(0, 2 * math.pi)
    helper = torch.tensor([0.0, 0.0, 1.0], device=axis.device)
    if torch.abs(axis @ helper) > 0.9:
        helper = torch.tensor([0.0, 1.0, 0.0], device=axis.device)
    e1 = torch.nn.functional.normalize(torch.linalg.cross(axis, helper), dim=0)
    e2 = torch.linalg.cross(axis, e1)
    return cos.unsqueeze(-1) * axis + sin.unsqueeze(-1) * (
        torch.cos(phi).unsqueeze(-1) * e1 + torch.sin(phi).unsqueeze(-1) * e2
    )
