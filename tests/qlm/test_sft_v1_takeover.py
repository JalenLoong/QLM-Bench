"""sft-v1/QLM-SIM-001: expert takeover from RL-v3 own states, expert runs from reset, E0 and the E* skeleton;
sft-v1/QLM-SIM-002: the turning push and overshoot guard of E* (helpers, and one exploration-set scene).

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
SKELETON = {'regular': {'corner_recovery': True}, 'steering': {'enabled': False}, 'overshoot': {'enabled': False}}
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
    es, summary = T.takeover(c, state=state('fl_contact'), kind='recovery', params=SKELETON, **where)
    assert summary['expert']['recovery_params']['version'] == push_box_recovery.VERSION
    same(e0, es)
    e0r, _ = T.from_reset(c, kind='e0', max_seconds=6.0, **where)
    esr, _ = T.from_reset(c, kind='recovery', params=SKELETON, max_seconds=6.0, **where)
    assert 'straight_push' in set(esr['phase'])
    same(e0r, esr)


def test_recovery_parameters_are_versioned_and_strict():
    p = push_box_recovery.merged_params({'regular': {'corner_recovery': False}, 'version': 'x'})
    assert p['version'] == 'x' and p['regular']['corner_recovery'] is False and p['regular']['lateral_tracking_gain'] == 2.0
    with pytest.raises(ValueError):
        push_box_recovery.merged_params({'regular': {'unknown': 1}})
    with pytest.raises(ValueError):
        push_box_recovery.merged_params({'other': {}})
    d = push_box_recovery.DEFAULT_PARAMS
    assert d['version'] == push_box_recovery.VERSION and d['steering']['enabled'] is True and d['overshoot']['enabled'] is True
    # The frozen routine replaces the fixed-stroke corner repair with its own guard.
    assert d['regular']['corner_recovery'] is False
    off = push_box_recovery.merged_params(SKELETON)
    assert off['steering']['enabled'] is False and off['overshoot']['enabled'] is False and off['steering']['theta_on_deg'] == d['steering']['theta_on_deg']


# ------------------------------------------------------------------ sft-v1/QLM-SIM-002: turning push and overshoot guard

class _Env:
    """Just what the geometry helpers read."""
    _box_geometry = {'dimensions': [0.32, 0.18, 0.2]}
    _recovery_params = push_box_recovery.merged_params()

    class cfg:
        approved_profile = {'goal_x': [1.0, 1.4], 'goal_y': [-0.25, 0.25]}


def _geom(yaw_deg, centre=(0.9, 0.0)):
    yaw = np.radians(yaw_deg);c, s = np.cos(yaw), np.sin(yaw)
    local = np.array([[x, y] for x in (-0.16, 0.16) for y in (-0.09, 0.09)])
    pts = local @ np.array([[c, s], [-s, c]]) + np.asarray(centre)
    lo, hi = pts.min(0), pts.max(0)
    return {'center': [centre[0], centre[1], 0.1], 'yaw_rad': float(yaw), 'projected_box_corners': pts.tolist(),
            'footprint_xy': [[lo[0], lo[1]], [hi[0], lo[1]], [hi[0], hi[1]], [lo[0], hi[1]]]}


def test_near_face_frame_follows_the_face_closest_to_the_robot():
    R = push_box_recovery
    short = R._box(_Env, _geom(20.));long_ = R._box(_Env, _geom(80.))
    assert np.isclose(np.degrees(short['yaw']), 20.) and np.isclose(short['depth'], 0.16) and np.isclose(short['width'], 0.09)
    # Past 45 deg the long face is the near face: yaw is measured from it and depth/width swap.
    assert np.isclose(np.degrees(long_['yaw']), -10.) and np.isclose(long_['depth'], 0.09) and np.isclose(long_['width'], 0.16)
    for box in (short, long_):
        for yl in (-0.05, 0., 0.06):
            assert np.isclose(R._face_coord(box, R._face_y(box, yl)), yl)
    # The +x ray through the centre meets the near face at depth * tan(yaw): the regular push is the yl = 0.058 point at 20 deg.
    assert np.isclose(R._face_coord(short, short['centre'][1]), 0.16 * np.tan(np.radians(20.)))


def test_turning_push_contact_point_stays_on_the_usable_near_face():
    R = push_box_recovery;p = _Env._recovery_params['steering']
    usable = 0.09 - p['face_margin_m']
    assert R._contact_offset(_Env, R._box(_Env, _geom(0.))) == 0.
    assert 0 < R._contact_offset(_Env, R._box(_Env, _geom(8.))) < usable                      # +yaw: toward the +y end
    assert np.isclose(R._contact_offset(_Env, R._box(_Env, _geom(35.))), usable)            # clipped, never past the corner
    assert np.isclose(R._contact_offset(_Env, R._box(_Env, _geom(-35.))), -usable)
    # At 35 deg that point is on the -y side of the box centre in the world: the centre ray would already be on the side face.
    box = R._box(_Env, _geom(35.))
    assert R._face_y(box, usable) < box['centre'][1] < R._face_y(box, 0.09) + 0.16 * np.sin(np.radians(35.))
    # A straight box close to the goal's +y edge is leaned to -yaw: the contact moves to the +y end although yaw is 0.
    near_edge = R._box(_Env, _geom(0., centre=(0.9, 0.12)))
    assert near_edge['over_hi'] > -p['margin_ref_m'] and R._contact_offset(_Env, near_edge) > 0
    assert R._contact_offset(_Env, R._box(_Env, _geom(0., centre=(0.9, -0.12)))) < 0


def test_left_boundary_of_a_turned_box():
    R = push_box_recovery
    y, x = R._left_boundary(_geom(0.), 0.9)
    assert np.isclose(y, 0.09) and x == 0.9
    g = _geom(30.)
    pts = np.asarray(g['projected_box_corners'])
    y, x = R._left_boundary(g, 0.9)
    assert pts[:, 1].min() < y < pts[:, 1].max() and np.isclose(y, 0.09 / np.cos(np.radians(30.)))
    assert R._left_boundary(g, 5.0)[1] < pts[:, 0].max()                                      # x clamped into the outline


EXPLORATION = WORKSPACE / 'runs/audit/tsft-push-gate-20261111-v1'
EXPLORATION_CASE = 'push100-20261014-013'   # exploration set (split.json); the gate set is never run here
EXPLORATION_STATE = EXPLORATION / f'g1/states/{EXPLORATION_CASE}/{EXPLORATION_CASE}-k18.pt'   # takeover point B, 6.08 s
REAL_EXPLORATION = pytest.mark.skipif(not EXPLORATION_STATE.exists() or not (RUN / f'own-states/demo-{EXPLORATION_CASE}-half.pt').exists(),
                                      reason='G1 exploration-set own state required')
Q01 = np.array([-0.0257, -0.0626, -0.1306, 0.1525, 0.0262, 0.0161])   # SFT5000 action normalizer, offset -/+ scale
Q99 = np.array([0.1426, 0.0343, 0.0430, 0.5455, 0.2051, 0.3407])


@pytest.fixture(scope='module')
def exploration():
    assert EXPLORATION_CASE in json.loads((EXPLORATION / 'split.json').read_text())['exploration']
    index = json.loads((EXPLORATION / 'cases-index.json').read_text())
    case = next(c for c in index['cases'] if c['case_id'] == EXPLORATION_CASE)
    c = T.RuntimeCache(index['controller_checkpoint'])
    yield dict(case=str(EXPLORATION / 'cases' / f'{EXPLORATION_CASE}.json'), model=case['model_path']), c
    c.close()


@REAL_EXPLORATION
def test_recovery_turns_a_deviated_box_back_and_stays_in_the_action_range(exploration):
    """From the student's own state at takeover point B (+21 deg, foot on the middle of the near face) the frozen routine re-plants the
    foot on the +y end of the face, turns the box back and finishes; E0 also finishes here, the difference is how (see the exploration record)."""
    where, c = exploration
    arrays, summary = T.takeover(c, state=str(EXPLORATION_STATE), kind='recovery', **where)
    o = summary['outcome']
    assert o['success'] and not o['fallen'] and o['end_s'] < 12.0
    assert summary['expert']['recovery_params'] == push_box_recovery.merged_params()
    phases = list(arrays['phase'])
    assert phases[0] == 'steer_replant' and 'steer_push' in phases and phases.index('steer_replant') < phases.index('steer_push')
    assert not any(p.startswith('corner_') for p in phases)
    req = arrays['requested']
    assert np.array_equal(req[:, [2, 6, 7, 8]], np.zeros((len(req), 4)))
    assert np.all(req[:, :6] >= Q01 - 1e-6) and np.all(req[:, :6] <= Q99 + 1e-6)
    cols = list(arrays['columns']);q = arrays['privileged'][:, [cols.index(f'object_q{a}') for a in 'xyzw']]
    yaw = np.degrees(np.arctan2(2 * (q[:, 3] * q[:, 2] + q[:, 0] * q[:, 1]), 1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2)))
    assert yaw[0] > 18 and yaw.min() > -15 and yaw.max() < yaw[0] + 5 and abs(yaw[-1]) < 15
    again, _ = T.takeover(c, state=str(EXPLORATION_STATE), kind='recovery', **where)
    same(arrays, again)


@REAL_EXPLORATION
def test_recovery_leaves_an_undeviated_push_alone(exploration):
    """From a demonstration mid-state of the same scene nothing triggers a re-plant or the guard, and the push completes."""
    where, c = exploration
    arrays, summary = T.takeover(c, state=str(RUN / f'own-states/demo-{EXPLORATION_CASE}-half.pt'), kind='recovery', **where)
    o = summary['outcome']
    assert o['success'] and not o['fallen']
    assert not any(p.startswith('guard_') for p in arrays['phase'])


def test_new_modules_are_outside_the_hashed_source_identity():
    from qlm_bench.backends.mujoco.rl_v2 import storage
    import inspect
    source = inspect.getsource(storage.execution_source_identity)
    assert 'sft_v1' not in source and "'backends/mujoco'" in source
    assert Path(T.__file__).parent.name == 'sft_v1' and Path(push_box_recovery.__file__).parent.name == 'sft_v1'
