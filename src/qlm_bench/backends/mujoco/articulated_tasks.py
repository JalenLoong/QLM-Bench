"""Task state for the six authored-scene tasks (sweep, fridge, oven, valve, drawer, door).

Success = the task condition holds for three consecutive 50 Hz policy ticks after the 2.1 s
start-up window, with the robot not fallen.
"""
import copy
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

from qlm_bench.tasks.registration import ARTICULATED_TASKS
from qlm_bench.tasks.success import PolicySuccessHold
from qlm_bench.tasks.predicates import push_goal_condition

TASKS = ARTICULATED_TASKS
PREDICATES = {t: t + '_three_ticks' for t in TASKS}


class ArticulatedTaskState:
    """Three-tick 50 Hz success condition with the 2.1 s start-up gate."""
    def __init__(self, physics, profile):
        self.physics, self.profile, self.task = physics, profile, profile['task_id']
        if self.task not in TASKS or profile['success_hold_commands'] != 3:
            raise ValueError('Three-tick articulated task profile required')
        self.body = physics.model.body('primary').id
        self.success_holds = [PolicySuccessHold(3) for _ in range(physics.count)]
        self.hold = np.zeros(physics.count, dtype=int)
        self.criteria = None
        if self.task == 'open_room_door':
            from qlm_bench.backends.mujoco import door_socket as adapter
            if profile.get('task_success_profile') != adapter.PROFILE_ID:
                raise ValueError('Door requires the geometric socket-exit profile')
            self.criteria = [adapter.DoorSocketExit(physics.model, profile) for _ in range(physics.count)]
        self.reset()

    def reset(self, indices=None):
        if not hasattr(self, 'unlocked'):
            self.unlocked = np.zeros(self.physics.count, dtype=bool)
        for i in range(self.physics.count) if indices is None else indices:
            self.success_holds[i].reset()
            self.hold[i] = 0
            self.unlocked[i] = False
            if self.criteria is not None:
                self.criteria[i].reset()

    def joint(self, index, name):
        return float(self.physics.data[index].qpos[int(self.physics.model.joint(name).qposadr[0])])

    def geometry(self, index):
        d, m = self.physics.data[index], self.physics.model
        p, r = d.xpos[self.body], d.xmat[self.body].reshape(3, 3)
        corners = np.asarray([p])
        if self.task == 'sweep_block_to_zone':
            gid = m.geom('sw_block').id
            local = np.asarray(list(itertools.product(*[[-v, v] for v in m.geom_size[gid]])))
            corners = local @ d.geom_xmat[gid].reshape(3, 3).T + d.geom_xpos[gid]
        return p, r, corners

    def geometric_center(self, index):
        d = self.physics.data[index]
        if self.task == 'sweep_block_to_zone':
            return d.geom_xpos[self.physics.model.geom('sw_block').id].copy()
        return d.xpos[self.body].copy()

    def progress(self, index):
        if self.task == 'sweep_block_to_zone':
            return float(np.dot(self.geometric_center(index)[:2] - self.profile['initial_center_xy'],
                                self.profile['sweep_direction_xy']))
        return self.joint(index, self.profile['primary_joint'])

    def condition(self, index):
        p, q = self.profile, self.progress(index)
        if self.task == 'sweep_block_to_zone':
            return push_goal_condition(self.geometry(index)[2][:, :2], p['goal_x'], p['goal_y'])
        if self.task in ('close_fridge_door', 'close_oven_door'):
            return abs(q) <= p['closed_tolerance_rad']
        if self.task == 'turn_valve':
            return q >= p['target_min_rad']
        if self.task == 'pull_open_drawer':
            return q >= p['target_extension_m']
        observation = self.criteria[index].observe(self.physics.data[index])
        self.unlocked[index] = observation['unlocked_history']
        return observation['condition']

    def evaluate(self, index, core):
        fallen = bool(core.base_height[index] < .1 or np.linalg.norm(
            core.projected_gravity_b[index].cpu().numpy() - [0, 0, -1]) > .75)
        condition = self.condition(index) and self.physics.ticks[index] >= 1050
        success = self.success_holds[index].update(int(self.physics.ticks[index]), condition, not fallen)
        self.hold[index] = self.success_holds[index].count
        return dict(success=bool(success), fallen=fallen, progress=self.progress(index),
                    timed_out=bool(self.physics.ticks[index] * .002 >= self.profile['horizon_s']))


def articulated_runtime(model_path, checkpoint, *, seed=42, horizon_s=None, **kwargs):
    """MuJoCoRuntime with the articulated task state (native CPU physics and RAMBO only)."""
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    if kwargs.pop('backend', 'native') != 'native' or kwargs.pop('device', 'cpu') != 'cpu':
        raise ValueError('The articulated tasks run on native MuJoCo CPU with RAMBO on CPU')
    overlay = dict(kwargs.pop('profile_override', {}) or {})
    if horizon_s is not None:
        overlay['horizon_s'] = horizon_s
    return MuJoCoRuntime(model_path, checkpoint, seed=seed, backend='native', device='cpu',
                         trace_only=kwargs.pop('trace_only', True), task_state_factory=ArticulatedTaskState,
                         profile_override=overlay or None, **kwargs)
