from types import SimpleNamespace
import torch
from rambo.tasks.common.batch_native9 import BatchNative9Mixin
from rambo.contracts_v2.runtime import prepare_command


class Base:
    def __init__(self, cfg):
        self.num_envs = cfg.scene.num_envs
        self.cfg = cfg
        self.device = 'cpu'
        self._sim_step_counter = 0
        self._velocity_commands = torch.zeros(self.num_envs, 3)
        self._ee_pos_commands = torch.zeros(self.num_envs, 3)
        self._ee_force_commands = torch.zeros(self.num_envs, 3)

    def set_loco_manip_commands(self, velocity, position, force):
        self._velocity_commands[:] = velocity
        self._ee_pos_commands[:] = position
        self._ee_force_commands[:] = force

    def _reset_idx(self, ids):
        pass


class Batch(BatchNative9Mixin, Base):
    pass


def test_one_lane_reset_keeps_other_history_and_clock():
    cfg = SimpleNamespace(scene=SimpleNamespace(num_envs=2), ee_default_command=[.1934, .142, .05])
    batch = Batch(cfg)
    commands = [prepare_command([i, 0, 0, .2, .1, .05, 0, 0, 0], f'lane-{i}', 0) for i in range(2)]
    batch.submit_native9_batch(commands)
    batch._validate_episode_command()
    for step in (5, 10):
        batch._sim_step_counter = step
        batch._confirm_episode_control()
    batch._reset_idx(torch.tensor([1]))
    assert batch.lane_tick(0) == 10 and batch.lane_tick(1) == 0
    assert len(batch.lanes[0].history) == 1 and not batch.lanes[1].history
    assert batch.lanes[0].clock.reset_epoch != batch.lanes[1].clock.reset_epoch
    next_commands = [prepare_command([0, 0, 0, .2, .1, .05, 0, 0, 0], f'next-{i}', batch.lane_tick(i)) for i in range(2)]
    batch.submit_native9_batch(next_commands)
    batch._sim_step_counter = 15; batch._confirm_episode_control()
    batch._sim_step_counter = 20; batch._confirm_episode_control()
    assert batch.lanes[0].history[-1]['start_tick'] == 10
    assert batch.lanes[1].history[-1]['start_tick'] == 0


def test_indexed_recorder_uses_lane_time_and_owned_history():
    from rambo.recording_v2 import Recorder
    from rambo.tasks.common.episode import EpisodeRuntime
    lanes = [EpisodeRuntime(), EpisodeRuntime()]
    lanes[0].reset(0); lanes[1].reset(10)
    env = SimpleNamespace(lanes=lanes, lane_tick=lambda i: lanes[i].clock.tick(20))
    recorder = object.__new__(Recorder); recorder.env = env; recorder.env_index = 1
    assert recorder.tick == 10 and recorder.ns == 20_000_000 and recorder.clock.origin_tick == 10
