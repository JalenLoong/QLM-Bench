"""Re-generate one demonstration physics trace with the approved executor of an articulated task.

A Standard100 scene (downloaded with ``python -m qlm_bench.benchmark fetch``) serves as the candidate scene.
The approved executor of the task drives the RAMBO controller in MuJoCo (native CPU, physics only) for the
horizon recorded in the approved binding; a successful trace is written to <output> (manifest, telemetry,
commands, terminal, snapshots) and then audited offline (every boundary reconstructed, success re-checked).

    python scripts/synthesis/example_one_demonstration.py <resource_root> turn_valve-20261016-091 <new output dir>
"""
import json
import sys
import time
from pathlib import Path

import torch

from qlm_bench.backends.factory import create_runtime
from qlm_bench.backends.mujoco.articulated_tasks import TASKS
from qlm_bench.benchmark import suite
from qlm_bench.synthesis.approved_executor import ApprovedExpert
from qlm_bench.synthesis.audit import audit_articulated_trace
from qlm_bench.synthesis.bindings import binding
from qlm_bench.synthesis.trace import collect_trace


def main():
    torch.set_num_threads(1)
    res, case_id, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    bench = res / 'benchmarks' / suite.RELEASE
    case = json.loads((bench / 'cases' / f'{case_id}.json').read_text())
    if case['task_id'] not in TASKS:
        raise SystemExit(f'{case_id} is not an articulated-task case ({", ".join(TASKS)})')
    horizon = binding(case['task_id'])['horizon_s']
    reg = suite.read(bench / 'resource_registry_snapshot.json')
    model = suite.resource(res, reg['resources'][case['scene']['resource_identity']])
    ckpt = suite.resource(res, reg['controller'])
    initial = {'schema': 'qlm-mujoco-initial-state-v1', 'model_identity': case['scene']['resource_identity'],
               'qpos': case['initial_state']['qpos'], 'qvel': case['initial_state']['qvel']}
    scene = {'candidate_id': case_id, 'task_id': case['task_id'], 'model': str(model),
             'model_identity': case['scene']['resource_identity'], 'initial_state': initial, 'seed': case['seed'],
             'difficulty': case['scene']['difficulty']}
    rt = create_runtime(case['task_id'], 'native', model_path=model, checkpoint=ckpt, seed=case['seed'],
                        horizon_s=horizon, trace_only=True)
    started = time.monotonic()
    try:
        if rt.profile['horizon_s'] != horizon:
            raise RuntimeError('Runtime horizon differs from the approved binding')
        collect_trace(rt, ApprovedExpert(case['task_id']), scene, out,
                      batch_identity={'native_trace_profile': 'native-cpu-original-rambo-v1'},
                      quality_policy='evidence-review-v1')
    finally:
        rt.close()
    audit = audit_articulated_trace(out)
    print(json.dumps({'task': case['task_id'], 'horizon_s': horizon, 'standard100_horizon_s': case['scene']['horizon_s'],
                      'success': True, 'n_actions': audit['n_actions'], 'audit_quality': audit['quality'],
                      'elapsed_s': round(time.monotonic() - started, 1)}, indent=2))


if __name__ == '__main__':
    main()
