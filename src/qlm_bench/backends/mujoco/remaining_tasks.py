"""Approved six-task state and independent snapshot audit. No controller imports.

The high-level recipes remain immutable external dependencies with explicit source
hashes; their historical executions never acquire the new production identity.
"""
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np

from qlm_bench.tasks.success import PolicySuccessHold
from qlm_bench.tasks.predicates import push_goal_condition

WORKSPACE = next((p for p in Path(__file__).resolve().parents if (p / 'workspace.env').is_file()), None)
BINDINGS = (WORKSPACE or Path('/unavailable-qlm-production-workspace')) / 'runs/audit/remaining-six-handoff-20261016-v1/approved-six-task-bindings.json'
TASKS = ('sweep_block_to_zone', 'close_fridge_door', 'close_oven_door',
         'turn_valve', 'pull_open_drawer', 'open_room_door')
PREDICATES = {t: t + '_three_ticks' for t in TASKS}


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def binding(task_id):
    if task_id not in TASKS:
        raise ValueError('Unknown approved remaining task')
    result = next(t for t in json.loads(BINDINGS.read_text())['tasks'] if t['task_id'] == task_id)
    if task_id == 'pull_open_drawer':
        # The handoff names the nominal class; qualification-v5 names the
        # already approved randomized-frame adapter. Preserve both identities.
        qualification = Path(result['scope_evidence'])
        evidence = json.loads(qualification.read_text())
        proposal = Path(evidence['proposal'])
        if hashlib.sha256(proposal.read_bytes()).hexdigest() != evidence['proposal_sha256']:
            raise ValueError('Drawer scope proposal changed')
        scope = json.loads(proposal.read_text())
        if not evidence['all16_actual_success']:
            raise ValueError('Drawer complete scope qualification required')
        result.update(scope_executor=scope['executor'], scope_class_name=scope['executor_class'],
                      scope_executor_sha256=scope['executor_sha256'],
                      scope_binding_files=[str(qualification), str(proposal)])
    return result


class RemainingTaskState:
    """Same approved 50Hz conditions and 2.1s startup gate as reference runtime."""
    def __init__(self, physics, profile):
        self.physics, self.profile, self.task = physics, profile, profile['task_id']
        if self.task not in TASKS or profile['success_hold_commands'] != 3:
            raise ValueError('Explicit approved three-tick task required')
        self.body = physics.model.body('primary').id
        self.success_holds = [PolicySuccessHold(3) for _ in range(physics.count)]
        self.hold = np.zeros(physics.count, dtype=int)
        self.criteria = None
        if self.task == 'open_room_door':
            from . import door_socket as adapter
            if profile.get('task_success_profile') != adapter.PROFILE_ID:
                raise ValueError('Door requires approved geometric socket-exit v3 profile')
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


def audit_remaining_trace(path):
    """Reconstruct every actual boundary; never step physics or load RAMBO."""
    import mujoco
    from types import SimpleNamespace
    from .trace import verify_trace, sha, SNAPSHOT_ARRAYS
    from .resources import resource_closure
    from .quality import contact_evidence
    from qlm_bench.compatibility.dataset_v2.validation import digest
    m, arrays, telemetry, commands, terminal = verify_trace(path)
    task = m['profile']['task_id']
    binding(task)
    model_path = m['scene']['model']
    if resource_closure(model_path, require_portable=True)['identity'] != m['model_identity']:
        raise ValueError('Physical model resource changed')
    model = mujoco.MjModel.from_xml_path(model_path)
    data = mujoco.MjData(model)
    profile = json.loads(Path(model_path).with_suffix('.task.json').read_text())
    # Horizon is explicitly selected at runtime; all task geometry remains exact.
    for key in ('primary_joint', 'canonical_goal_position', 'goal_x', 'goal_y', 'sweep_direction_xy',
                'initial_center_xy', 'closed_tolerance_rad', 'target_min_rad', 'target_extension_m',
                'task_success_profile', 'target_open_rad', 'bolt_joint', 'lever_joint', 'unlock_lever_max_rad'):
        if key in profile and m['profile'].get(key) != profile[key]:
            raise ValueError('Trace task geometry/profile differs: ' + key)
    physics = SimpleNamespace(model=model, data=[data], count=1, ticks=np.zeros(1, np.int64))
    state = RemainingTaskState(physics, m['profile'])
    base = model.body('base').id
    first = None
    hold = 0
    for k in ('qpos', 'qvel'):
        np.testing.assert_array_equal(arrays[k][0], m['scene']['initial_state'][k])
    for i, boundary in enumerate(telemetry['boundaries']):
        for key in SNAPSHOT_ARRAYS:
            getattr(data, key)[:] = arrays[key][i]
        data.time = float(arrays['time'][i])
        mujoco.mj_forward(model, data)
        physics.ticks[0] = i * 10
        observed = boundary['state']
        np.testing.assert_allclose(observed['task.object.position'], data.xpos[state.body], rtol=0, atol=1e-7)
        np.testing.assert_allclose(observed['task.object.orientation'], data.xquat[state.body][[1, 2, 3, 0]], rtol=0, atol=1e-7)
        np.testing.assert_allclose(observed['task.goal.position'], profile['canonical_goal_position'], rtol=0, atol=1e-7)
        np.testing.assert_allclose(observed['task.progress'], [state.progress(0)], rtol=0, atol=1e-7)
        inside = state.condition(0)
        notfallen = data.xpos[base, 2] >= .1 and np.linalg.norm(-data.xmat[base].reshape(3, 3)[2, :] - [0, 0, -1]) <= .75
        hold = hold + 1 if i >= 105 and inside and notfallen else 0
        if hold >= 3 and first is None:
            first = i
    if first != m['n_actions'] or terminal['success'] is not True or not m['terminal_before_reset']:
        raise ValueError('Original success predicate/first-success terminal mismatch')
    evidence = contact_evidence(telemetry['boundaries'])
    quality = {k: evidence[k] for k in ('fl_contact_boundaries', 'body_contact_boundaries')}
    if quality != m['quality']:
        raise ValueError('Captured contact counts differ')
    quality.update({PREDICATES[task]: True, 'not_fallen': True})
    h = hashlib.sha256()
    for k in ('qpos', 'qvel', 'simulation_time_ns'):
        h.update(k.encode()); h.update(arrays[k].tobytes())
    h.update(np.asarray([c['executed'] for c in commands], np.float32).tobytes())
    return dict(manifest_sha256=sha(Path(path) / 'manifest.json'), trajectory_sha256=h.hexdigest(),
                model_identity=m['model_identity'], source_identity_sha256=digest(m['batch_identity']),
                quality=quality, n_actions=m['n_actions'], n_boundaries=m['n_boundaries'],
                task_id=task, physical_source=copy.deepcopy(m['batch_identity']), scene=copy.deepcopy(m['scene']))
