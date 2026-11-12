"""Frozen sweep expert from reset in the takeover runtime, with demonstration mid-way own states (sft-v1/QLM-SIM-003).

For each sweep train EvalCase: ``takeover.RuntimeCache`` runtime (trace-only NativeCPU, EvalCase overlay), ``suite.reconstruct``,
``sweep_takeover.make`` (frozen production expert), then one command per 50 Hz tick to the terminal. Along the way RL-v3 own states
are saved at chunk boundaries (tick % 160 == 0) of the demonstration:
  * ``fl_contact``: the last chunk boundary at or before the first FL/block contact of the production trace;
  * ``half``: the last chunk boundary at or before half of the production episode length;
  * ``approach`` (6.08 s) and ``align`` (12.16 s): fixed boundaries inside the approach and the slow entry alignment, extra coverage
    for the E0 entry rule.
Every requested native9 command is compared with the production ``commands.jsonl`` of the same scene (exact equality), so this also
checks that the EvalCase/takeover runtime path reproduces production. Production files are only read.

Run: envs/qlm-mujoco-py312-v1/bin/python scripts/sft_v1/sweep_demo_states.py --run <run> --ids 001 ... [--workers 2]
(PYTHONPATH=<QLM sft-v1>/src). Needs <run>/cases-index.json from sweep_cases.py. Writes <run>/demo-states/<case>/<case>-<point>.pt
(+ .json, .own.json), <run>/demo-states/<case>.json (comparison and points), and the trace <run>/demo-states/<case>-reset.{npz,json}.
"""
import argparse
import contextlib
import gzip
import json
import os
from pathlib import Path
import sys

import numpy as np

CHUNK = 160


def targets(trace_dir):
    t = json.load(gzip.open(Path(trace_dir) / 'telemetry.json.gz', 'rt'))
    fl = next(int(b['physics_step']) for b in t['boundaries'] if b['contact']['fl_object'])
    end = int(t['boundaries'][-1]['physics_step'])
    return {'approach': 3040, 'align': 6080, 'half': (end // 2) // CHUNK * CHUNK, 'fl_contact': fl // CHUNK * CHUNK}, fl, end


def run_one(args):
    row, run, controller = args
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    from qlm_bench.backends.mujoco.suite import reconstruct
    from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
    from qlm_bench.rl_v3 import own_state, privileged
    from qlm_bench.sft_v1 import sweep_takeover as st, takeover as tk
    import numpy as np
    cid = row['case_id']
    out = Path(run) / 'demo-states'
    done = out / f'{cid}.json'
    if done.exists():
        return json.loads(done.read_text())
    case = Path(run) / 'cases' / f'{cid}.json'
    trace = Path(row['production_trace'])
    production = [json.loads(x)['requested'] for x in (trace / 'commands.jsonl').read_text().splitlines()]
    want, fl_tick, end_tick = targets(trace)
    cache = tk.RuntimeCache(controller)
    rt, ec, binding = cache.get(case, row['model_path'])
    try:
        reconstruct(rt, ec)
        expert, config = st.make(rt, ec)
        saved, mismatch, i = {}, None, 0
        requested = []
        with contextlib.redirect_stdout(open(os.devnull, 'w')):
            while rt.terminal is None:
                tick = int(rt.physics.ticks[0])
                for name, target in want.items():
                    if tick == target and name not in saved:
                        path = out / cid / f'{cid}-{name}.pt'
                        path.parent.mkdir(parents=True, exist_ok=True)
                        rec = own_state.save(rt, path, origin={'event': 'demo_midway', 'point': name, 'work': 'sft-v1/QLM-SIM-003',
                                                               'expert': 'frozen production sweep', 'production_trace': str(trace)},
                                             binding_sha256=binding, privileged_row=privileged.row(rt))
                        saved[name] = {'path': str(path), 'tick': tick, 't_s': tick * .002, 'snapshot_sha256': rec['snapshot_sha256']}
                values, diag = expert.command()
                prepared = prepare_command(values, f'{cid}:{i}', tick)
                requested.append([float(x) for x in prepared['requested']])
                if mismatch is None and (i >= len(production) or requested[-1] != production[i]):
                    mismatch = i
                rt.step(prepared)
                i += 1
        outcome = {'terminal': rt.terminal and {k: v for k, v in rt.terminal.items() if k != 'physical_snapshot'}, 'commands': i,
                   'end_tick': int(rt.physics.ticks[0])}
    finally:
        cache.close()
    result = {'case_id': cid, 'production_trace': str(trace), 'production_commands': len(production), 'commands': i,
              'first_requested_mismatch': mismatch, 'identical_requested_native9': mismatch is None and i == len(production),
              'success': bool(outcome['terminal'] and outcome['terminal'].get('success')), 'outcome': outcome,
              'production_first_fl_contact_tick': fl_tick, 'production_end_tick': end_tick, 'targets': want, 'states': saved,
              'frozen_expert_manifest_sha256': config['frozen_expert']['manifest_sha256']}
    done.parent.mkdir(parents=True, exist_ok=True)
    done.write_text(json.dumps(result, indent=1, default=str) + '\n')
    print(json.dumps({'case': cid, 'identical': result['identical_requested_native9'], 'success': result['success'], 'states': sorted(saved)}), flush=True)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--ids', nargs='+', required=True)
    p.add_argument('--workers', type=int, default=2)
    a = p.parse_args()
    index = json.loads((a.run / 'cases-index.json').read_text())
    rows = {c['case_id'][-3:]: c for c in index['cases']}
    jobs = [(rows[f'{int(s):03d}'], str(a.run), index['controller_checkpoint']) for s in a.ids]
    if any(j[0]['split'] != 'train' for j in jobs):
        raise ValueError('Only train scenes')
    if a.workers <= 1:
        res = [run_one(j) for j in jobs]
    else:
        import multiprocessing as mp
        with mp.get_context('spawn').Pool(a.workers, maxtasksperchild=1) as pool:
            res = pool.map(run_one, jobs)
    print(json.dumps({'runs': len(res), 'identical': sum(r['identical_requested_native9'] for r in res), 'success': sum(r['success'] for r in res)}))


if __name__ == '__main__':
    sys.exit(main())
