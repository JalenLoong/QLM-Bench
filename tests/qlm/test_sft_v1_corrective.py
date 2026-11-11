"""sft-v1/QLM-DATA-001: physical trace of a corrective takeover segment on the episode clock.

Real test on an exploration-set scene (push100-20261014-013, takeover point B); NativeCPU, no rendering. The gate set is not run here.
"""
import gzip
import json
from pathlib import Path

import numpy as np
import pytest

from qlm_bench.sft_v1 import corrective_trace, takeover as T

WORKSPACE = Path(__file__).resolve().parents[4]
GATE = WORKSPACE / 'runs/audit/tsft-push-gate-20261111-v1'
CASE_ID = 'push100-20261014-013'
STATE = GATE / f'g1/states/{CASE_ID}/{CASE_ID}-k18.pt'
REAL = pytest.mark.skipif(not STATE.exists(), reason='G1 exploration-set own state required')


@REAL
def test_corrective_trace_replays_the_takeover_on_the_episode_clock(tmp_path):
    from qlm_bench.backends.mujoco.rendition import audit_trace
    from qlm_bench.backends.mujoco.trace import verify_trace
    assert CASE_ID in json.loads((GATE / 'split.json').read_text())['exploration']
    index = json.loads((GATE / 'cases-index.json').read_text())
    case = next(c for c in index['cases'] if c['case_id'] == CASE_ID)
    point = next(f for f in json.loads((GATE / 'g2/points.json').read_text())['failures'] if f['case_id'] == CASE_ID)['B']
    case_path = str(GATE / 'cases' / f'{CASE_ID}.json')
    cache = T.RuntimeCache(index['controller_checkpoint'])
    try:
        arrays, summary = T.takeover(cache, case=case_path, model=case['model_path'], state=str(STATE), kind='recovery', name='seg')
        T.save(tmp_path / 'seg', arrays, summary)
        segment = {'segment_id': 'seg', 'case_id': CASE_ID, 'case': case_path, 'point': 'B', 'takeover_tick': point['tick'], 'state': str(STATE),
                   'state_sha256': point['state_sha256'], 'at_takeover': {'D': point['D']}, 'difficulty': case['difficulty']}
        identity = {'work_id': corrective_trace.WORK_ID, 'source_commit': '0' * 40, 'native_trace_profile': 'native-cpu-original-rambo-v1'}
        result = corrective_trace.record_segment(cache, segment, tmp_path / 'seg', tmp_path / 'trace', batch_identity=identity, uid='uid-B')
        with pytest.raises(FileExistsError):
            corrective_trace.record_segment(cache, segment, tmp_path / 'seg', tmp_path / 'trace', batch_identity=identity, uid='uid-B')
        with pytest.raises(ValueError):   # a different own state than the takeover used
            corrective_trace.record_segment(cache, {**segment, 'state_sha256': '0' * 64}, tmp_path / 'seg', tmp_path / 'other', batch_identity=identity, uid='uid-B')
    finally:
        cache.close()
    n, t0 = len(arrays['requested']), point['tick']
    assert result['passed'] and result['n_actions'] == n and result['takeover_tick'] == t0 == 3040 and result['end_tick'] == t0 + 10 * n
    manifest, snapshots, telemetry, commands, terminal = verify_trace(tmp_path / 'trace')   # the production chain's own check, unchanged
    assert audit_trace(tmp_path / 'trace')['n_actions'] == n
    # Episode clock: the takeover boundary is tick 0 in every stream; the absolute tick is kept beside it.
    assert np.array_equal(snapshots['physics_step'], np.arange(n + 1) * 10)
    assert np.array_equal(snapshots['absolute_physics_step'], t0 + np.arange(n + 1) * 10)
    assert np.isclose(snapshots['time'][0], t0 * 0.002)
    assert [b['physics_step'] for b in telemetry['boundaries']] == [i * 10 for i in range(n + 1)]
    assert [p['physics_step'] for p in telemetry['physics']] == list(range(10 * n + 1))
    assert [c['controller_tick'] for c in telemetry['controller']] == list(range(2 * n))
    assert telemetry['controller'][0]['fl_ik_command_id'] is None and telemetry['controller'][2]['fl_ik_command_id'] == 'uid-B:0'
    assert terminal['physics_step'] == 10 * n and terminal['absolute_physics_step'] == t0 + 10 * n and terminal['success']
    assert len(terminal['executed_history']) == n
    # The commands are the ones the routine requested during the takeover, with its phases.
    assert np.array_equal(np.asarray([c['requested'] for c in commands]), arrays['requested'])
    assert [c['extensions']['expert']['phase'] for c in commands] == list(arrays['phase'])
    scene = manifest['scene']
    assert scene['takeover']['absolute_tick'] == t0 and scene['takeover']['own_state_sha256'] == point['state_sha256'] and scene['split'] == 'train'
    assert manifest['backend']['physics'] == 'native' and manifest['demonstration_eligibility'] == corrective_trace.ELIGIBILITY
    assert 'src/qlm_bench/sft_v1/corrective_trace.py' in manifest['batch_identity']['implementation']
    with gzip.open(tmp_path / 'trace/telemetry.json.gz', 'rt') as f:
        assert json.load(f)['boundaries'][0]['state']['task.progress'][0] > 0.05   # progress stays relative to the reset
