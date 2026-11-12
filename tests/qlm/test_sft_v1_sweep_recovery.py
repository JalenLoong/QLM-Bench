"""sft-v1/QLM-SIM-003: sweep_block_to_zone recovery routine E* (``sft_v1.sweep_recovery``).

The simulator tests use one exploration-set train scene (049) of workspace ``runs/audit/tsft-sweep-prep-20261112-v1``: its EvalCase,
the student own state at takeover point B listed in ``tsft-sweep-gate-20261112-v1/points-exploration.json`` and a demonstration
mid-way state. They run NativeCPU without rendering. No gate-set or held-out scene is read.
"""
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from qlm_bench.sft_v1 import sweep_expert, sweep_recovery as SR, sweep_takeover as ST, takeover as T

WORKSPACE = Path(__file__).resolve().parents[4]
RUN = WORKSPACE / 'runs/audit/tsft-sweep-prep-20261112-v1'
POINTS = WORKSPACE / 'runs/audit/tsft-sweep-gate-20261112-v1/points-exploration.json'
CASE_ID = 'sweep_block_to_zone-20261016-049'
HALF = RUN / f'demo-states/{CASE_ID}/{CASE_ID}-half.pt'
REAL = pytest.mark.skipif(not (RUN / 'cases-index.json').exists() or not POINTS.exists() or not HALF.exists(),
                          reason='sweep prep cases, exploration takeover points and demonstration own states required')
E0_PARAMS_SHA256 = 'f8dc8e1aa4c74531d9dafe2f62d95d30abcff1edb25d2b8c5a1d93773f9c173e'  # Preregistered E0 arm.


def off():
    """E* with every added term disabled: must be E0."""
    p = copy.deepcopy(SR.DEFAULT_PARAMS)
    p['entry'].update(base_x_floor=False, advance_at_once=False)
    for key in ('tracking', 'steering', 'base_follow'):
        p[key]['enabled'] = False
    return p


def test_params_are_versioned_and_keep_the_e0_entry_rule():
    p = SR.DEFAULT_PARAMS
    assert p['version'] == SR.VERSION and p['schema'] == 'qlm-sft-v1-sweep-recovery-params-v1'
    assert p['entry']['rule'] == ST.E0_PARAMS and ST.params_sha256(ST.E0_PARAMS) == E0_PARAMS_SHA256
    assert SR.params_sha256(p) == SR.params_sha256(json.loads(json.dumps(p)))
    assert SR.params_sha256(off()) != SR.params_sha256(p)
    assert SR.KIND in T.EXPERTS


def test_recovery_extends_the_frozen_expert_without_touching_it():
    before = sweep_expert.verify()
    cls = SR.recovery_class()
    frozen = getattr(sweep_expert.module(), 'Sweep')
    assert issubclass(cls, frozen) and cls is not frozen and cls is SR.recovery_class()
    assert sweep_expert.verify() == before
    expert = cls(sweep_expert.recipe(), None)
    assert expert.rec == SR.DEFAULT_PARAMS and expert.rec is not SR.DEFAULT_PARAMS
    assert expert.config == sweep_expert.build().config


def scene():
    index = json.loads((RUN / 'cases-index.json').read_text())
    case = next(c for c in index['cases'] if c['case_id'] == CASE_ID)
    assert case['split'] == 'train'
    point = next(f for f in json.loads(POINTS.read_text())['failures'] if f['case_id'] == CASE_ID)
    assert point['set'] == 'exploration'
    return dict(case=str(RUN / 'cases' / f'{CASE_ID}.json'), model=case['model_path']), index['controller_checkpoint'], point


@pytest.fixture(scope='module')
def cache():
    where, controller, point = scene()
    c = T.RuntimeCache(controller)
    yield where, c, point
    c.close()


def same(a, b):
    return np.array_equal(a, b, equal_nan=a.dtype.kind == 'f')


@REAL
def test_all_terms_off_is_e0_and_production(cache):
    where, c, point = cache
    state = point['B']['state']
    e0, s0 = ST.takeover(c, state=state, max_seconds=3.0, **where)
    mine, s1 = SR.takeover(c, state=state, params=off(), max_seconds=3.0, **where)
    for key in ('requested', 'executed', 'privileged', 'phase'):
        assert same(e0[key], mine[key]), key
    assert s1['expert']['entry']['decision'] == s0['expert']['entry']['decision'] and s1['expert']['entry']['base_x_floor'] is None
    production, _ = ST.from_reset(c, max_seconds=4.0, **where)
    reset, summary = SR.from_reset(c, params=off(), max_seconds=4.0, **where)
    assert same(production['requested'], reset['requested']) and same(production['privileged'], reset['privileged'])
    assert summary['expert']['kind'] == SR.KIND and summary['expert']['version'] == SR.VERSION


@REAL
def test_contact_point_sits_on_the_pushed_face(cache):
    from qlm_bench.backends.mujoco.suite import reconstruct
    where, c, _ = cache
    rt, ec, _ = c.get(where['case'], where['model'])
    reconstruct(rt, ec)
    expert, config = SR.make(rt, ec)
    assert config['recovery_params_sha256'] == SR.params_sha256(SR.DEFAULT_PARAMS)
    m, d = rt.physics.model, rt.physics.data[0]
    gid = m.geom('sw_block').id
    p, R, half = d.geom_xpos[gid], d.geom_xmat[gid].reshape(3, 3), m.geom_size[gid]
    normal = expert.rec_sign * R[:2, expert.rec_axis]
    tangent = expert.rec_tangent_sign * R[:2, 1 - expert.rec_axis]
    assert normal @ -np.asarray(expert.direction) > .99 and tangent[0] > .99  # The face that looks back along the sweep; tangent ~ +x.
    radius = float(m.geom_size[m.geom('FL').id, 0])
    depth = float(half[expert.rec_axis]) + radius - SR.DEFAULT_PARAMS['steering']['overlap_m']
    for offset in (0., .02, -.03):
        expert.rec_offset = offset
        q = expert.rec_contact() - p[:2]
        assert abs(q @ normal - depth) < 1e-12 and abs(q @ tangent - offset) < 1e-12
    _, yaw, lateral = expert.rec_measure()
    assert abs(lateral) < 1e-12 and abs(yaw) < np.deg2rad(8.)


@REAL
def test_takeover_from_student_state_recovers_and_batch_dispatches(cache, tmp_path):
    where, c, point = cache
    job = {'id': '049-B', 'kind': SR.KIND, 'state': point['B']['state'], **where}
    arrays, summary = T.run_job(c, job)
    o = summary['outcome']
    assert o['success'] and not o['fallen'] and o['terminal']['reason'] == 'task_success' and o['horizon_margin_s'] > 3.
    assert summary['start']['state_sha256'] == point['B']['state_sha256'] and summary['start']['absolute_tick'] == point['B']['tick']
    entry = summary['expert']['entry']
    assert entry['decision'] == 'interaction_raise' and entry['base_x_floor'] is not None
    log = arrays['recovery_log']
    assert log.shape == (o['commands'], len(SR.LOG_COLUMNS)) and list(arrays['recovery_log_columns']) == list(SR.LOG_COLUMNS)
    cols = {k: i for i, k in enumerate(SR.LOG_COLUMNS)}
    limit = SR.DEFAULT_PARAMS['tracking']['limit_m']
    assert np.all(np.abs(log[:, cols['tracking_bias_m']]) <= limit + 1e-12)
    names = {k: i for i, k in enumerate(arrays['columns'])}
    last = arrays['privileged'][-1]
    xs = [last[names[f'corner{i}_x']] for i in range(8)]
    assert last[names['goal_x0']] < min(xs) and max(xs) < last[names['goal_x1']]
    T.save(tmp_path / job['id'], arrays, {**summary, 'job': job})
    assert json.loads((tmp_path / '049-B.json').read_text())['expert']['recovery_params']['version'] == SR.VERSION
    with pytest.raises(ValueError):
        T.run_job(c, {**job, 'overrides': {'x': 1}})


@REAL
def test_takeover_is_reproducible_from_a_demonstration_state(cache):
    where, c, _ = cache
    first, s1 = SR.takeover(c, state=str(HALF), max_seconds=0.64, **where)
    SR.from_reset(c, max_seconds=0.4, **where)  # Something else on the same runtime in between.
    second, s2 = SR.takeover(c, state=str(HALF), max_seconds=0.64, **where)
    for key in first:
        assert same(first[key], second[key]), key
    assert s1['expert']['entry'] == s2['expert']['entry']
