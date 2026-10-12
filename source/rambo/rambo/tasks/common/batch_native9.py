"""Per-environment native9 ledgers; original QP controller/physics is shared."""
from __future__ import annotations
import copy
import torch
from .episode import EpisodeRuntime
from .snapshots import capture_state, capture_rgb


class BatchNative9Mixin:
    def __init__(self, cfg, *args, **kwargs):
        self.lanes = [EpisodeRuntime() for _ in range(cfg.scene.num_envs)]
        self.lane_active = [True] * cfg.scene.num_envs
        self.expert_lanes = [{} for _ in self.lanes]
        super().__init__(cfg, *args, **kwargs)

    def _setup_task_assets(self):
        if self.scene.cfg.num_envs < 1:
            raise ValueError('Positive environment count required')

    @property
    def episode_clock(self):
        return self.lanes[0].clock

    @property
    def task_outcome(self):
        return self.lanes[0].outcome

    def lane_tick(self, index):
        return self.lanes[index].clock.tick(int(self._sim_step_counter))

    def lane_snapshot(self, index):
        rgb, hashes, frames = capture_rgb(self, index)
        lane = self.lanes[index]
        return dict(env_index=index, simulation_time_ns=lane.clock.time_ns(int(self._sim_step_counter)),
                    physics_step=self.lane_tick(index), reset_epoch=lane.clock.reset_epoch,
                    state=capture_state(self, index), rgb=rgb, rgb_hashes=hashes,
                    sensor_frame_ids=frames, outcome=lane.outcome)

    def submit_native9_batch(self, commands):
        if len(commands) != self.num_envs:
            raise ValueError('One explicit command/idle marker per environment required')
        values = []
        for index, prepared in enumerate(commands):
            if prepared is None:
                if self.lane_active[index]:
                    raise ValueError('Active lane needs its own command')
                values.append([0., 0., 0., *self.cfg.ee_default_command, 0., 0., 0.])
            else:
                if not self.lane_active[index]:
                    raise ValueError('Inactive lane must be reset before command submission')
                self.lanes[index].submit(prepared, int(self._sim_step_counter))
                values.append(prepared['filtered'])
        cmds = torch.as_tensor(values, dtype=torch.float32, device=self.device)
        self.set_loco_manip_commands(cmds[:, :3], cmds[:, 3:6], cmds[:, 6:])

    def _validate_episode_command(self):
        for index, lane in enumerate(self.lanes):
            row = lane.current_command
            if row is None:
                continue
            held = torch.cat((self._velocity_commands[index], self._ee_pos_commands[index], self._ee_force_commands[index]))
            if not torch.equal(held, torch.as_tensor(row['filtered'], dtype=held.dtype, device=held.device)):
                raise ValueError('Per-lane native9 command differs from ledger')

    def _confirm_episode_control(self):
        for lane in self.lanes:
            lane.confirm_control(int(self._sim_step_counter))

    def capture_terminal_snapshot(self):
        for index in torch.nonzero(self.reset_buf, as_tuple=False).flatten().tolist():
            lane = self.lanes[index]
            snapshot = self.lane_snapshot(index)
            snapshot.update(lane.outcome)
            snapshot.update(reason=lane.outcome['termination_reason'],
                            command_confirmation=copy.deepcopy(lane.current_command),
                            executed_history=lane.history,
                            task_review=self.review_lane(index),
                            partial_interval=self.lane_tick(index) % 10 != 0)
            lane.seal_terminal(snapshot)
        return self.lanes[0].terminal

    def _reset_idx(self, env_ids):
        indices = list(range(self.num_envs)) if env_ids is None else torch.as_tensor(env_ids).flatten().tolist()
        auto = {i: self.lanes[i].outcome['terminated'] for i in indices}
        super()._reset_idx(env_ids)
        for index in indices:
            self.lanes[index].reset(int(self._sim_step_counter))
            self.expert_lanes[index] = {}
            self.lane_active[index] = not auto[index]
            if hasattr(self, '_success_holds'):
                self._success_holds[index].reset()

    def activate(self, indices):
        ids = torch.as_tensor(indices, dtype=torch.long, device=self.device)
        self._reset_idx(ids)
        for index in indices:
            self.lane_active[index] = True

    @property
    def task_metrics(self):
        return {}
