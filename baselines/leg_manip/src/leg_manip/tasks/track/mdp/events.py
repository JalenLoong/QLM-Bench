"""External toe loads for low-level manipulation training."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from mjlab.envs import ManagerBasedRlEnv
    from mjlab.managers.event_manager import EventTermCfg
    from mjlab.managers.scene_entity_config import SceneEntityCfg

    from leg_manip.tasks.track.mdp.commands import FootTrajectoryCommand


class apply_manip_foot_force:
    """Hold a sampled world force at the selected toe for a sampled duration.

    Use with ``mode="step"`` and calf bodies ordered FL, FR. This term owns their
    external wrench slots, clearing the other calf on every update. The moment
    about the current COM is refreshed each policy step as the leg moves.
    """

    def __init__(self, cfg: EventTermCfg, env: ManagerBasedRlEnv):
        asset_cfg = cfg.params["asset_cfg"]
        self._robot = env.scene[asset_cfg.name]
        self._body_ids = asset_cfg.body_ids
        self._body_index = torch.tensor(self._body_ids, device=env.device)
        self._ids = torch.arange(env.num_envs, device=env.device)
        self._dt = env.step_dt
        self._cooldown_s = cfg.params["cooldown_s"]
        self._force = torch.zeros(env.num_envs, 3, device=env.device)
        self._remaining = torch.zeros(env.num_envs, device=env.device)
        self._cooldown = torch.empty(env.num_envs, device=env.device).uniform_(
            *self._cooldown_s
        )
        # The event manager is built before commands; resolve the command at call time.

    def __call__(
        self,
        env: ManagerBasedRlEnv,
        env_ids: torch.Tensor | None,
        command_name: str,
        asset_cfg: SceneEntityCfg,
        force_range: tuple[float, float],
        duration_s: tuple[float, float],
        cooldown_s: tuple[float, float],
    ) -> None:
        del env_ids, asset_cfg, cooldown_s  # Step events update all environments.
        active = self._remaining > 0
        self._remaining[active] -= self._dt
        self._cooldown[~active] -= self._dt
        expired = active & (self._remaining <= 0)
        expired_ids = self._ids[expired]
        self._force[expired_ids] = 0.0
        self._cooldown[expired_ids] = torch.empty_like(
            expired_ids, dtype=torch.float
        ).uniform_(*self._cooldown_s)
        trigger = (self._remaining <= 0) & (self._cooldown <= 0)
        trigger_ids = self._ids[trigger]
        self._force[trigger_ids] = torch.empty_like(self._force[trigger_ids]).uniform_(
            *force_range
        )
        self._remaining[trigger_ids] = torch.empty_like(
            self._remaining[trigger_ids]
        ).uniform_(*duration_s)

        cmd: FootTrajectoryCommand = env.command_manager.get_term(command_name)
        flag = cmd.flag_index
        com = self._robot.data.body_com_pos_w[self._ids, self._body_index[flag]]
        moment = torch.cross(cmd.ee_pos_w() - com, self._force, dim=-1)
        forces = torch.zeros(len(self._ids), 2, 3, device=self._force.device)
        torques = torch.zeros_like(forces)
        forces[self._ids, flag] = self._force
        torques[self._ids, flag] = moment
        self._robot.write_external_wrench_to_sim(
            forces, torques, body_ids=self._body_ids
        )

    def reset(self, env_ids: torch.Tensor | slice | None = None) -> None:
        ids = self._ids if env_ids is None else self._ids[env_ids]
        self._remaining[ids] = 0.0
        self._force[ids] = 0.0
        self._cooldown[ids] = torch.empty_like(self._cooldown[ids]).uniform_(
            *self._cooldown_s
        )
        zeros = torch.zeros(len(ids), 2, 3, device=self._force.device)
        self._robot.write_external_wrench_to_sim(
            zeros, zeros, env_ids=ids, body_ids=self._body_ids
        )
