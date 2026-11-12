"""sft-v1/QLM-SIM-003: frozen production sweep_block_to_zone expert, its runs from reset and the mid-way takeover E0.

The freeze tests need only this checkout. The simulator tests use the sweep train EvalCases and demonstration own states written by
``scripts/sft_v1/sweep_cases.py`` / ``sweep_demo_states.py`` under workspace ``runs/audit/tsft-sweep-prep-20261112-v1`` (scene 001,
a train scene) and the production trace of that scene (read only); they run NativeCPU without rendering.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from qlm_bench.sft_v1 import sweep_expert, sweep_takeover as ST, takeover as T

WORKSPACE = Path(__file__).resolve().parents[4]
RUN = WORKSPACE / 'runs/audit/tsft-sweep-prep-20261112-v1'
CASE_ID = 'sweep_block_to_zone-20261016-001'
PRODUCTION = WORKSPACE / 'runs/audit/remaining-six-production-20261016-v1/sweep_block_to_zone/traces' / f'{CASE_ID}-c01'
REAL = pytest.mark.skipif(not (RUN / 'cases-index.json').exists() or not (RUN / f'demo-states/{CASE_ID}/{CASE_ID}-half.pt').exists()
                          or not (PRODUCTION / 'commands.jsonl').exists(), reason='sweep prep cases, demonstration own states and production trace required')


def test_frozen_copy_matches_manifest_and_sources_are_not_needed():
    identity = sweep_expert.verify()
    manifest = sweep_expert.manifest()
    assert len(manifest['files']) == 22 and identity['version'] == sweep_expert.VERSION
    for row in manifest['files']:
        data = (sweep_expert.MIRROR / row['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['sha256']
        source = Path(row['source'])
        if source.exists():  # The audit copy is the origin; when present it must still be byte-identical.
            assert hashlib.sha256(source.read_bytes()).hexdigest() == row['sha256']
    assert manifest['production_campaign']['recipe_equals_binding_recipe']
    deps = manifest['in_repo_dependencies']
    assert all(v['sha256'] == v['production_frozen_source_sha256'] for v in deps.values())


def test_chain_loads_only_from_the_mirror():
    chain = sweep_expert.chain()
    assert [c['class'] for c in chain][:6] == ['Sweep'] * 5 + ['SweepExecutor']
    assert len(chain) == 18  # 16 audit classes, SmoothPressExecutor (in repo), object
    for c in chain:
        for f in c['files']:
            assert str(sweep_expert.MIRROR) in f or f.endswith('backends/mujoco/press_reference_smooth.py')
    e = sweep_expert.build()
    assert e.config['recipe_id'] == 'sweep-a09-original-entry-hold-after-interaction-v9'
    # No diagnostic file keys: the chain's optional file writers stay disabled.
    assert not any(k.endswith('diagnostic_file') for k in e.config)


def test_loader_refuses_files_outside_the_manifest(tmp_path):
    expected = sweep_expert._expected()
    outside = tmp_path / 'other.py'
    outside.write_text('x = 1\n')
    with pytest.raises(ImportError):
        with sweep_expert._redirected_specs(expected):
            importlib.util.spec_from_file_location('other', outside)
    loader = sweep_expert._FrozenLoader('x', str(outside), expected)
    with pytest.raises(ImportError):
        loader.get_data(str(outside))


def scene():
    index = json.loads((RUN / 'cases-index.json').read_text())
    case = next(c for c in index['cases'] if c['case_id'] == CASE_ID)
    assert case['split'] == 'train'
    return dict(case=str(RUN / 'cases' / f'{CASE_ID}.json'), model=case['model_path']), index['controller_checkpoint']


@pytest.fixture(scope='module')
def cache():
    where, controller = scene()
    c = T.RuntimeCache(controller)
    yield where, c
    c.close()


@REAL
def test_from_reset_prefix_equals_production(cache):
    where, c = cache
    arrays, summary = ST.from_reset(c, max_seconds=4.0, **where)
    production = [json.loads(x)['requested'] for x in (PRODUCTION / 'commands.jsonl').read_text().splitlines()]
    n = len(arrays['requested'])
    assert n == 200
    assert arrays['requested'].tolist() == production[:n]
    assert summary['expert']['kind'] == 'sweep_expert'


@REAL
def test_e0_decisions_on_demonstration_states(cache):
    where, c = cache
    expected = {'approach': 'approach_base', 'align': 'interaction_raise', 'half': 'interaction_sweep', 'fl_contact': 'interaction_sweep'}
    for point, decision in expected.items():
        state = RUN / f'demo-states/{CASE_ID}/{CASE_ID}-{point}.pt'
        _, summary = ST.takeover(c, state=str(state), max_seconds=0.2, **where)
        assert summary['expert']['entry']['decision'] == decision, point
        assert summary['expert']['e0_params']['version'] == ST.E0_VERSION


@REAL
def test_e0_takeover_is_reproducible_and_batch_dispatches(cache, tmp_path):
    where, c = cache
    state = str(RUN / f'demo-states/{CASE_ID}/{CASE_ID}-half.pt')
    first, s1 = ST.takeover(c, state=state, max_seconds=0.64, **where)
    ST.from_reset(c, max_seconds=0.4, **where)  # Something else on the same runtime in between.
    second, s2 = T.run_job(c, {'id': 'x', 'kind': 'sweep_e0', 'state': state, 'max_seconds': 0.64, **where})
    for key in first:
        assert np.array_equal(first[key], second[key], equal_nan=first[key].dtype.kind == 'f'), key
    assert s1['expert']['entry'] == s2['expert']['entry']
    with pytest.raises(ValueError):
        T.run_job(c, {'id': 'y', 'kind': 'sweep_e0', **where})
