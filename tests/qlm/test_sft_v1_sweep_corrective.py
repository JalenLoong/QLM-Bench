"""sft-v1/QLM-DATA-002: physical trace of a corrective sweep_block_to_zone segment (takeover point B) on the episode clock.

Real test on one sweep train scene (049): its EvalCase, the student own state at point B and the frozen sweep recovery routine;
NativeCPU, no rendering. Held-out scenes are not read.
"""
import json
from pathlib import Path

import numpy as np
import pytest

from qlm_bench.sft_v1 import corrective_trace, sweep_recovery as SR, takeover as T

WORKSPACE = Path(__file__).resolve().parents[4]
RUN = WORKSPACE / 'runs/audit/tsft-sweep-prep-20261112-v1'
POINTS = WORKSPACE / 'runs/audit/tsft-sweep-gate-20261112-v1/points-exploration.json'
CASE_ID = 'sweep_block_to_zone-20261016-049'
REAL = pytest.mark.skipif(not (RUN / 'cases-index.json').exists() or not POINTS.exists(), reason='sweep prep cases and takeover points required')


@REAL
def test_sweep_corrective_trace_replays_the_takeover_on_the_episode_clock(tmp_path):
    from qlm_bench.backends.mujoco.rendition import audit_trace
    from qlm_bench.backends.mujoco.trace import verify_trace
    index = json.loads((RUN / 'cases-index.json').read_text())
    case = next(c for c in index['cases'] if c['case_id'] == CASE_ID)
    assert case['split'] == 'train'
    point = next(f for f in json.loads(POINTS.read_text())['failures'] if f['case_id'] == CASE_ID)['B']
    case_path = str(RUN / 'cases' / f'{CASE_ID}.json')
    cache = T.RuntimeCache(index['controller_checkpoint'])
    try:
        job = {'id': 'seg', 'kind': SR.KIND, 'case': case_path, 'model': case['model_path'], 'state': point['state']}
        arrays, summary = T.run_job(cache, job)
        T.save(tmp_path / 'seg', arrays, summary)
        segment = {'segment_id': 'seg', 'case_id': CASE_ID, 'case': case_path, 'point': 'B', 'takeover_tick': point['tick'], 'state': point['state'],
                   'state_sha256': point['state_sha256'], 'at_takeover': {'foot_lateral_cm': point['foot_lateral_cm']}, 'difficulty': case['difficulty']}
        identity = {'work_id': 'sft-v1/QLM-DATA-002', 'source_commit': '0' * 40, 'native_trace_profile': 'native-cpu-original-rambo-v1'}
        result = corrective_trace.record_segment(cache, segment, tmp_path / 'seg', tmp_path / 'trace', batch_identity=identity, uid='uid-B', reset_first=True)
    finally:
        cache.close()
    n, t0 = len(arrays['requested']), point['tick']
    assert summary['outcome']['success'] and result['passed'] and result['n_actions'] == n and result['takeover_tick'] == t0 and result['end_tick'] == t0 + 10 * n
    manifest, snapshots, telemetry, commands, terminal = verify_trace(tmp_path / 'trace')   # the production chain's own check, unchanged
    assert audit_trace(tmp_path / 'trace')['n_actions'] == n
    assert np.array_equal(snapshots['physics_step'], np.arange(n + 1) * 10)
    assert np.array_equal(snapshots['absolute_physics_step'], t0 + np.arange(n + 1) * 10)
    assert [b['physics_step'] for b in telemetry['boundaries']] == [i * 10 for i in range(n + 1)]
    assert terminal['physics_step'] == 10 * n and terminal['absolute_physics_step'] == t0 + 10 * n and terminal['success']
    assert np.array_equal(np.asarray([c['requested'] for c in commands]), arrays['requested'])
    assert [c['extensions']['expert']['phase'] for c in commands] == list(arrays['phase'])
    assert commands[0]['extensions']['expert']['routine'] == SR.VERSION
    scene = manifest['scene']
    assert scene['takeover']['absolute_tick'] == t0 and scene['takeover']['own_state_sha256'] == point['state_sha256'] and scene['split'] == 'train'
    assert manifest['profile']['task_id'] == 'sweep_block_to_zone' and manifest['profile']['instruction'] == 'Sweep the block into the outlined area.'
    assert manifest['backend']['physics'] == 'native' and manifest['demonstration_eligibility'] == corrective_trace.ELIGIBILITY
    assert abs(telemetry['boundaries'][0]['state']['task.progress'][0]) < 1e-9   # at B the student has not touched the block
