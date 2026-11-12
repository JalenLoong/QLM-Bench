"""Physics equivalence of the hardware-EGL RL-v3 scene worker and the trace-only takeover runtime (sft-v1/QLM-SIM-001).

G1 own states are captured by the rendering scene worker (observation_ticks 40, renderer on); takeovers run in the trace-only runtime of
``qlm_bench.sft_v1.takeover`` (no renderer, observation_ticks 10). For each given own state this script restores it in both, executes the
same fixed native9 commands (the first ``--chunks`` x 16 commands E0 requests from that state, computed once in the trace-only runtime and
then replayed open loop in both; for sweep_block_to_zone states E0 is ``sweep_takeover`` with the frozen production expert, sft-v1/QLM-SIM-003), and compares every privileged row (restore row plus one per command) and the final controller/physics
freeze token bit for bit. Run with MUJOCO_GL=egl (hardware renderer, as the worker requires), envs/qlm-mujoco-py312-v1,
PYTHONPATH=<QLM sft-v1>/src. Writes a JSON report.
"""
import argparse
import json
import os
from pathlib import Path
import uuid

import numpy as np


def worker_rows(worker, case, model, state, commands, chunks):
    session = f'eq:{uuid.uuid4().hex}'
    n = [0]

    def call(op, payload):
        n[0] += 1
        r = worker.handle({'schema': 'qlm-rl-v3-scene-ipc-v1', 'id': f'{session}:{n[0]}', 'operation': op, 'session': session, 'payload': payload})
        if not r['ok']:
            raise RuntimeError(r)
        return r['result']
    boundary = call('restore_state', {'case': case, 'model': model, 'path': state})
    rows, freeze, terminal = list(boundary['privileged']['rows']), None, None
    for k in range(chunks):
        r = call('execute', {'chunk': k, 'commands': commands[16 * k:16 * k + 16].tolist(), 'ring': False})
        rows += r['privileged']['rows']
        freeze, terminal = r['freeze'], r['terminal']
        if terminal is not None:
            break
    return np.asarray(rows, np.float64), freeze, boundary['renderer']


def trace_rows(cache, case, model, state, commands):
    from qlm_bench.backends.mujoco.rl_v2 import snapshot as snap
    from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
    from qlm_bench.rl_v3 import own_state, privileged
    rt, _, binding = cache.get(case, model)
    stored, _ = own_state.load(Path(state), binding_sha256=binding)
    snap.restore(rt, stored)
    rows = [privileged.row(rt)]
    for i, values in enumerate(commands):
        tick = int(rt.physics.ticks[0])
        out = rt.step(prepare_command(values.tolist(), f'eq:{i}', tick))
        reason = None if out['terminal'] is None else out['terminal']['reason']
        rows.append(privileged.row(rt, completed=out['command']['status'] == 'completed', terminal_reason=reason))
        if out['terminal'] is not None:
            break
    return np.asarray(rows, np.float64), rt.freeze_token()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cases', type=Path, required=True, help='directory with <case_id>.json EvalCases')
    p.add_argument('--index', type=Path, required=True, help='cases-index.json (model paths, controller)')
    p.add_argument('--state-root', type=Path, required=True)
    p.add_argument('--states', nargs='+', required=True, help='own-state file names under --state-root; case id parsed from the name')
    p.add_argument('--chunks', type=int, default=3)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.cases, a.state_root = a.cases.resolve(), a.state_root.resolve()
    if os.environ.get('MUJOCO_GL') != 'egl':
        raise SystemExit('MUJOCO_GL=egl required (hardware renderer, as in the RL-v3 scene worker)')
    from qlm_bench.rl_v3 import privileged
    from qlm_bench.rl_v3.scene_worker import SceneWorker
    from qlm_bench.sft_v1 import takeover as T
    index = json.loads(a.index.read_text())
    models = {c['case_id']: c['model_path'] for c in index['cases']}
    controller = index['controller_checkpoint']
    worker = SceneWorker(controller, a.state_root)
    cache = T.RuntimeCache(controller)
    report = {'schema': 'qlm-sft-v1-render-equivalence-v1', 'chunks': a.chunks, 'controller': controller, 'code': T.code_identity(), 'states': []}
    try:
        for name in a.states:
            case_id = next(cid for cid in models if cid in name)
            if models[case_id] is None or not any(c['case_id'] == case_id and c['split'] == 'train' for c in index['cases']):
                raise ValueError('train scenes only')
            case, model, state = str(a.cases / f'{case_id}.json'), models[case_id], str(a.state_root / name)
            # Fixed commands: what E0 requests from this state in the first chunks (trace-only run, then replayed open loop in both).
            task = json.loads(Path(case).read_text())['task_id']
            kind = 'sweep_e0' if task == 'sweep_block_to_zone' else 'e0'  # sweep: frozen production expert entered by E0 (sweep_takeover)
            arrays, _ = T.run_job(cache, {'id': f'eq-{name}', 'case': case, 'model': model, 'kind': kind, 'state': state,
                                          'max_seconds': a.chunks * 0.32})
            commands = arrays['requested'][:16 * a.chunks]
            reference, freeze_t = trace_rows(cache, case, model, state, commands)
            rendered, freeze_w, renderer = worker_rows(worker, case, model, state, commands, a.chunks)
            columns = privileged.columns(cache.rt)
            same = reference.shape == rendered.shape and np.array_equal(reference, rendered)
            entry = {'state': name, 'case_id': case_id, 'commands': int(len(commands)), 'rows': [int(reference.shape[0]), int(rendered.shape[0])],
                     'privileged_rows_bitwise_equal': bool(same), 'freeze_token_equal': freeze_t == freeze_w, 'renderer': renderer,
                     'trace_only_freeze': freeze_t, 'worker_freeze': freeze_w}
            if not same and reference.shape == rendered.shape:
                diff = np.abs(reference - rendered)
                first = int(np.argwhere(diff > 0)[0][0])
                entry.update(first_differing_row=first, max_abs_diff=float(diff.max()),
                             differing_columns=sorted({columns[j] for j in np.argwhere(diff > 0)[:, 1]}))
            report['states'].append(entry)
            print(json.dumps({k: entry[k] for k in ('state', 'commands', 'rows', 'privileged_rows_bitwise_equal', 'freeze_token_equal')}), flush=True)
    finally:
        worker.close()
        cache.close()
    report['all_equal'] = all(s['privileged_rows_bitwise_equal'] and s['freeze_token_equal'] for s in report['states'])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=1) + '\n')
    print('all_equal', report['all_equal'])


if __name__ == '__main__':
    main()
