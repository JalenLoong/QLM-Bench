"""sft-v1/QLM-SIM-001: expert takeover from RL-v3 own states, expert runs from reset, E0 and the E* skeleton.

Real tests use the read-only RL-v3 train-scene demonstration own states (runs/audit/rl-v3-student-base-20261110-v1,
case push100-20261014-011, a train scene) and the RAMBO model_2000 controller; they run NativeCPU without rendering.
"""
import json
from pathlib import Path

import numpy as np
import pytest

from qlm_bench.sft_v1 import push_box_recovery, takeover as T

WORKSPACE = Path(__file__).resolve().parents[4]
RUN = WORKSPACE / 'runs/audit/rl-v3-student-base-20261110-v1'
CASE_ID = 'push100-20261014-011'
REAL = pytest.mark.skipif(not (RUN / 'cases-index.json').exists() or not (RUN / f'own-states/demo-{CASE_ID}-fl_contact.pt').exists(),
                          reason='RL-v3 train-scene cases and demonstration own states required')


def scene():
    index = json.loads((RUN / 'cases-index.json').read_text())
    case = next(c for c in index['cases'] if c['case_id'] == CASE_ID)
    assert case['split'] == 'train'
    return dict(case=str(RUN / 'cases' / f'{CASE_ID}.json'), model=case['model_path']), index['controller_checkpoint']


def state(event):
    return str(RUN / f'own-states/demo-{CASE_ID}-{event}.pt')


def same(a, b):
    assert set(a) == set(b)
    for key in a:
        if a[key].dtype.kind == 'f':
            assert np.array_equal(a[key], b[key], equal_nan=True), key
        else:
            assert np.array_equal(a[key], b[key]), key


@pytest.fixture(scope='module')
def cache():
    where, controller = scene()
    c = T.RuntimeCache(controller)
    yield where, c
    c.close()


@REAL
def test_takeover_twice_from_one_snapshot_is_bitwise_identical(cache):
    where, c = cache
    first, s1 = T.takeover(c, state=state('fl_contact'), kind='e0', **where)
    T.takeover(c, state=state('half'), kind='push_box_expert', **where)  # Something else in between on the same runtime.
    second, s2 = T.takeover(c, state=state('fl_contact'), kind='e0', **where)
    same(first, second)
    assert s1['outcome'] == s2['outcome']
    fresh = T.RuntimeCache(c.controller)
    try:
        third, _ = T.takeover(fresh, state=state('fl_contact'), kind='e0', **where)
    finally:
        fresh.close()
    same(first, third)


@REAL
def test_e0_completes_from_a_demonstration_mid_state(cache):
    where, c = cache
    arrays, summary = T.takeover(c, state=state('fl_contact'), kind='e0', **where)
    o = summary['outcome']
    assert o['success'] and not o['fallen'] and o['terminal']['reason'] == 'task_success'
    assert o['start_tick'] % T.CHUNK_TICKS == 0 and o['start_tick'] > 0 and o['end_tick'] * T.TICK_SECONDS < 24
    assert summary['expert']['overrides'] == T.E0_OVERRIDES and set(o['phases']) <= {'straight_push', 'corner_brake', 'corner_sidestep',
                                                                                      'corner_reposition', 'corner_lower', 'corner_nudge'}
    # Records: one command row per tick, privileged rows at start and after every command, chunk subset on 160-tick boundaries.
    n = o['commands']
    assert arrays['requested'].shape == arrays['executed'].shape == (n, 9) and arrays['privileged'].shape[0] == n + 1
    assert np.array_equal(arrays['requested'][:, [2, 6, 7, 8]], np.zeros((n, 4)))
    ticks = arrays['privileged'][:, 0]
    assert np.all(ticks[arrays['chunk_index']] % 160 == 0) and arrays['chunk_index'][0] == 0
    assert list(arrays['columns'][:2]) == ['tick', 'completed']


@REAL
def test_unmodified_push_box_expert_completes_a_train_scene_from_reset(cache):
    where, c = cache
    arrays, summary = T.from_reset(c, kind='push_box_expert', **where)
    o = summary['outcome']
    assert o['success'] and not o['fallen'] and o['start_tick'] == 0
    assert 'lateral_tracking_gain' not in summary['expert']['effective_expert_profile']
    assert summary['expert']['effective_expert_profile'] == summary['expert']['scene_expert_profile']
    assert {'settle', 'base_approach', 'normal_approach', 'straight_push'} <= set(o['phases'])


@REAL
def test_recovery_skeleton_regular_push_equals_e0(cache):
    """E* with steering and overshoot disabled is push_box_expert under the E0 options, bit for bit (mid-way and from reset)."""
    where, c = cache
    e0, _ = T.takeover(c, state=state('fl_contact'), kind='e0', **where)
    es, summary = T.takeover(c, state=state('fl_contact'), kind='recovery', **where)
    assert summary['expert']['recovery_params']['version'] == push_box_recovery.VERSION
    same(e0, es)
    e0r, _ = T.from_reset(c, kind='e0', max_seconds=6.0, **where)
    esr, _ = T.from_reset(c, kind='recovery', max_seconds=6.0, **where)
    assert 'straight_push' in set(esr['phase'])
    same(e0r, esr)


def test_recovery_parameters_are_versioned_and_strict():
    p = push_box_recovery.merged_params({'regular': {'corner_recovery': False}, 'version': 'x'})
    assert p['version'] == 'x' and p['regular']['corner_recovery'] is False and p['regular']['lateral_tracking_gain'] == 2.0
    with pytest.raises(ValueError):
        push_box_recovery.merged_params({'regular': {'unknown': 1}})
    with pytest.raises(ValueError):
        push_box_recovery.merged_params({'other': {}})
    assert push_box_recovery.DEFAULT_PARAMS['steering']['enabled'] is False


def test_unimplemented_hooks_refuse_when_enabled():
    class Env:
        _recovery_params = push_box_recovery.merged_params({'steering': {'enabled': True}, 'overshoot': {'enabled': True}})
    with pytest.raises(NotImplementedError):
        push_box_recovery.steer(Env(), 0., None, None, None, None, 0., 0., 'straight_push')
    with pytest.raises(NotImplementedError):
        push_box_recovery.overshoot_guard(Env(), 0., None, None, None, 0., 0., 'straight_push')


def test_new_modules_are_outside_the_hashed_source_identity():
    from qlm_bench.backends.mujoco.rl_v2 import storage
    import inspect
    source = inspect.getsource(storage.execution_source_identity)
    assert 'sft_v1' not in source and "'backends/mujoco'" in source
    assert Path(T.__file__).parent.name == 'sft_v1' and Path(push_box_recovery.__file__).parent.name == 'sft_v1'
