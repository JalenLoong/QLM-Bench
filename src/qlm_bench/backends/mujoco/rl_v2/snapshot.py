"""Full CPU continuation at completed 16-command boundaries, not render snapshots."""
import copy
from pathlib import Path
import sys

import mujoco
import numpy as np
import torch

from .equivalence import EQUIVALENT_SOURCE_IDENTITIES
from .storage import digest, sha256, write_json

SCHEMA = 'qlm-rl-v2-anchor-snapshot-v1'
CORE_EXCLUDE = {'adapter', 'cfg', 'actor', 'robot', 'case_rng', 'motor',
                'contact_generator', 'joint_position_controller', 'torque_optimizer'}
TASK_EXCLUDE = {'physics', 'profile', 'success_holds', 'goal_entries', 'adapter'}


def _copy_fields(obj, excluded=()):
    result = {}
    for key, value in vars(obj).items():
        if key in excluded:
            continue
        if isinstance(value, (torch.Tensor, np.ndarray, str, int, float, bool, list, tuple, dict)) or value is None:
            result[key] = copy.deepcopy(value)
        else:
            raise TypeError(f'Unregistered continuation field: {type(obj).__name__}.{key}')
    return result


def identity(rt):
    if rt.physics.backend != 'native' or rt.core.device != 'cpu' or rt.physics.count != 1:
        raise ValueError('RL anchor requires one NativeCPU/RAMBOCPU world')
    from qlm_bench.controllers.rambo.core import CHECKPOINT_SHA256
    from .storage import execution_source_identity
    return {'schema': SCHEMA, 'model': rt.physics.model_identity,
            'model_parameters': rt.physics.full_model_identity, 'profile': digest(rt.profile),
            'controller': CHECKPOINT_SHA256, 'rgb_profile': rt.rgb_profile,
            'mujoco': mujoco.__version__, 'torch': torch.__version__ + '',
            'source': execution_source_identity()}


def capture(rt):
    binding = identity(rt)
    tick = int(rt.physics.ticks[0])
    if tick % 160 or rt.terminal is not None or (rt.current and rt.current['status'] != 'completed'):
        raise ValueError('Anchor requires nonterminal complete joint-chunk boundary')
    # state() establishes the same observation/read-cache boundary as ordinary execution.
    rt.state()
    spec = mujoco.mjtState.mjSTATE_INTEGRATION
    integration = np.empty(mujoco.mj_stateSize(rt.physics.model, spec))
    mujoco.mj_getState(rt.physics.model, rt.physics.data[0], integration, spec)
    core = rt.core
    parts = {'core': _copy_fields(core, CORE_EXCLUDE),
             'motor': _copy_fields(core.motor, {'random_streams'}),
             'contact': _copy_fields(core.contact_generator, {'_env'}),
             'position': _copy_fields(core.joint_position_controller, {'_env'}),
             'torque': _copy_fields(core.torque_optimizer, {'_env'}),
             'task': _copy_fields(rt.task, TASK_EXCLUDE)}
    holds = {key: [_copy_fields(x) for x in getattr(rt.task, key)]
             for key in ('success_holds', 'goal_entries') if hasattr(rt.task, key)}
    rng = {'seeds': list(core.case_rng.seeds), 'counts': copy.deepcopy(core.case_rng.counts),
           'streams': {k: [g.get_state().clone() for g in v] for k, v in core.case_rng.streams.items()}}
    return {'schema': SCHEMA, 'identity': binding, 'tick': tick, 'integration': integration,
            'parts': parts, 'task_holds': holds, 'rng': rng,
            'physics_aux': {'contact_history': rt.physics.contact_history.copy(),
                            'contact_history_tick': rt.physics.contact_history_tick.copy()},
            'lifecycle': {'clock': copy.deepcopy(vars(rt.lifecycle.clock)),
                          'fields': _copy_fields(rt.lifecycle, {'clock'})},
            'runtime': {k: copy.deepcopy(getattr(rt, k)) for k in
                        ('history', 'current', 'outcome', 'case_seed', '_next_case_seed',
                         'controller_reference_command_id', 'controller_reference_tick', 'capture_index')}}


def check_identity(stored, live):
    """Exact match, or a registered predecessor source whose successor set holds the live source (one WARNING)."""
    if not isinstance(stored, dict) or set(stored) != set(live) or \
            any(stored[key] != live[key] for key in live if key != 'source'):
        raise ValueError('Anchor source/resource/profile identity mismatch')
    if stored['source'] == live['source']:
        return None
    entry = EQUIVALENT_SOURCE_IDENTITIES.get(stored['source'])
    if entry is None or live['source'] not in entry['successors']:
        raise ValueError('Anchor source identity mismatch')
    print(f"WARNING: anchor source {stored['source'][:12]} accepted as registered equivalent of live source "
          f"{live['source'][:12]}: {entry['reason']}", file=sys.stderr, flush=True)
    return entry['reason']


def restore(rt, snapshot):
    if snapshot.get('schema') != SCHEMA:
        raise ValueError('Anchor source/resource/profile identity mismatch')
    check_identity(snapshot['identity'], identity(rt))
    tick = snapshot['tick']
    if type(tick) is not int or tick < 0 or tick % 160:
        raise ValueError('Invalid anchor boundary')
    spec = mujoco.mjtState.mjSTATE_INTEGRATION
    value = snapshot['integration']
    if value.shape != (mujoco.mj_stateSize(rt.physics.model, spec),) or not np.isfinite(value).all():
        raise ValueError('Invalid integration state')
    # New epoch permits backwards absolute time without weakening renderer freshness.
    epoch = int(rt.physics.epochs[0]) + 1
    d = rt.physics.data[0]
    mujoco.mj_resetData(rt.physics.model, d)
    mujoco.mj_setState(rt.physics.model, d, value, spec)
    mujoco.mj_forward(rt.physics.model, d)
    # Forward may alter warmstart; reapply the complete inputs after rebuilding derived state.
    mujoco.mj_setState(rt.physics.model, d, value, spec)
    rt.physics.ticks[:] = tick
    rt.physics.epochs[:] = epoch
    for k, v in snapshot['physics_aux'].items():
        setattr(rt.physics, k, v.copy())
    rt.physics._host_valid = False
    rt.physics._read_cache = {}
    core = rt.core
    objects = {'core': core, 'motor': core.motor, 'contact': core.contact_generator,
               'position': core.joint_position_controller, 'torque': core.torque_optimizer, 'task': rt.task}
    for name, fields in snapshot['parts'].items():
        vars(objects[name]).update(copy.deepcopy(fields))
    for name, states in snapshot['task_holds'].items():
        if len(states) != len(getattr(rt.task, name)):
            raise ValueError('Task state lane mismatch')
        for obj, fields in zip(getattr(rt.task, name), states):
            vars(obj).update(copy.deepcopy(fields))
    core.case_rng.seeds = list(snapshot['rng']['seeds'])
    core.case_rng.counts = copy.deepcopy(snapshot['rng']['counts'])
    for name, values in snapshot['rng']['streams'].items():
        for generator, value in zip(core.case_rng.streams[name], values):
            generator.set_state(value)
    vars(rt.lifecycle).update(copy.deepcopy(snapshot['lifecycle']['fields']))
    vars(rt.lifecycle.clock).update(snapshot['lifecycle']['clock'])
    rt.lifecycle.clock.reset_epoch = epoch
    rt.lifecycle._terminal = None
    for key, value in snapshot['runtime'].items():
        setattr(rt, key, copy.deepcopy(value))
    rt.cached = rt.terminal = None
    core.refresh()
    state = rt.state()
    return {'schema': 'qlm-rl-v2-restore-receipt-v1', 'absolute_tick': tick,
            'absolute_simulation_time_ns': tick * 2_000_000, 'relative_tick': 0,
            'restore_epoch': epoch, 'rng': core.case_rng.identity(), 'observation': state}


def _pack(value):
    if isinstance(value, np.ndarray):
        return {'__ndarray__': torch.from_numpy(value.copy())}
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {k: _pack(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_pack(v) for v in value)
    return value


def _unpack(value):
    if isinstance(value, dict):
        if set(value) == {'__ndarray__'}:
            return value['__ndarray__'].numpy().copy()
        return {k: _unpack(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_unpack(v) for v in value)
    return value


def save(path, snapshot):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.partial')
    torch.save(_pack(snapshot), tmp)
    tmp.replace(path)
    write_json(path.with_suffix('.json'), {'schema': SCHEMA, 'sha256': sha256(path),
                                          'identity': snapshot['identity'], 'tick': snapshot['tick']})


def load(path):
    import json
    path = Path(path)
    meta = json.loads(path.with_suffix('.json').read_text())
    if meta['schema'] != SCHEMA or sha256(path) != meta['sha256']:
        raise ValueError('Snapshot inventory/hash mismatch')
    result = _unpack(torch.load(path, map_location='cpu', weights_only=True))
    if result['identity'] != meta['identity'] or result['tick'] != meta['tick']:
        raise ValueError('Snapshot payload/manifest mismatch')
    return result
