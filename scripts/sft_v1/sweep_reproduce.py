"""Reproduce production sweep_block_to_zone demonstrations from reset with the frozen expert (sft-v1/QLM-SIM-003).

For each production candidate: the same steps as the production ``remaining100.py physics`` entry (QLM-DATA-040, frozen
source of commit 7e7665b): ``create_runtime(task, 'native', model_path, checkpoint, seed, horizon_s=40)`` trace-only NativeCPU,
the expert's command wrapped with the same robot/asset contact diagnostic, ``collect_trace(..., reference=False,
quality_policy='evidence-review-v1')``. The only difference is the expert: ``qlm_bench.sft_v1.sweep_expert.build()`` (frozen
mirror) instead of ``ApprovedExpert`` reading the audit directories. The new trace is written under ``--out`` and then compared
value by value with the production trace: every ``commands.jsonl`` record (requested/executed native9 and the expert
diagnostic), every ``telemetry.json.gz`` row (boundaries, controller, 500 Hz physics, contact sensor), ``terminal.json`` and
every array of ``render_snapshots.npz``. Production files are only read.

Run: envs/qlm-mujoco-py312-v1/bin/python scripts/sft_v1/sweep_reproduce.py --out DIR --ids 001 017 ... [--workers 2]
with PYTHONPATH=<QLM sft-v1>/src. Writes DIR/traces/<candidate>/ and DIR/compare/<candidate>.json.
"""
import argparse
import contextlib
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

W = Path('/home/jalen/workspace/WAM-Policy')
PRODUCTION = W / 'runs/audit/remaining-six-production-20261016-v1/sweep_block_to_zone'
CHECKPOINT = W / 'assets/qlm/resources/20261003-refactor-v1/rambo-go2-controller/iteration-2000/runtime/model_2000.pt'
TASK = 'sweep_block_to_zone'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def candidate(short):
    return f'{TASK}-20261016-{int(short):03d}-c01'


def contact_wrapped(runtime, expert):
    """The production contact diagnostic wrapper (remaining100.py physics), unchanged."""
    import mujoco
    original = expert.command
    m = runtime.physics.model
    robot = {m.body('base').id}
    for body in range(m.nbody):
        if int(m.body_parentid[body]) in robot:
            robot.add(body)
    assets = set(range(1, m.nbody)) - robot

    def command():
        values, diag = original()
        d = runtime.physics.data[0]
        contacts = []
        for i, contact in enumerate(d.contact[:d.ncon]):
            g1, g2 = map(int, contact.geom)
            b1, b2 = map(int, m.geom_bodyid[[g1, g2]])
            if b1 in robot and b2 in assets:
                rb, ag = b1, g2
            elif b2 in robot and b1 in assets:
                rb, ag = b2, g1
            else:
                continue
            force = np.zeros(6)
            mujoco.mj_contactForce(m, d, i, force)
            contacts.append(dict(robot_body=m.body(rb).name, asset_geom=m.geom(ag).name, normal_force_N=float(force[0])))
        diag['actual_robot_asset_contacts'] = contacts
        return values, diag
    expert.command = command


def first_difference(a, b, path=''):
    """Path of the first value that differs (exact float equality), or None."""
    if type(a) is not type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool)):
        return f'{path}: type {type(a).__name__} vs {type(b).__name__}'
    if isinstance(a, dict):
        if set(a) != set(b):
            return f'{path}: keys {sorted(set(a) ^ set(b))}'
        for k in a:
            d = first_difference(a[k], b[k], f'{path}/{k}')
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f'{path}: length {len(a)} vs {len(b)}'
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_difference(x, y, f'{path}[{i}]')
            if d:
                return d
        return None
    return None if a == b else f'{path}: {a!r} vs {b!r}'


def compare(new, old):
    out = {}
    na = [json.loads(x) for x in (new / 'commands.jsonl').read_text().splitlines()]
    oa = [json.loads(x) for x in (old / 'commands.jsonl').read_text().splitlines()]
    native = [i for i, (x, y) in enumerate(zip(na, oa)) if x['requested'] != y['requested'] or x['executed'] != y['executed']]
    out['commands'] = {'new': len(na), 'production': len(oa), 'native9_mismatch_count': len(native),
                       'first_native9_mismatch': native[0] if native else None,
                       'first_any_difference': first_difference(na, oa), 'bytes_equal': (new / 'commands.jsonl').read_bytes() == (old / 'commands.jsonl').read_bytes()}
    nt = json.load(gzip.open(new / 'telemetry.json.gz', 'rt'))
    ot = json.load(gzip.open(old / 'telemetry.json.gz', 'rt'))
    out['telemetry'] = {k: {'rows_new': len(nt[k]), 'rows_production': len(ot[k]), 'first_difference': first_difference(nt[k], ot[k], k)}
                        for k in sorted(set(nt) | set(ot))}
    out['terminal'] = {'first_difference': first_difference(json.loads((new / 'terminal.json').read_text()), json.loads((old / 'terminal.json').read_text()))}
    with np.load(new / 'render_snapshots.npz') as a, np.load(old / 'render_snapshots.npz') as b:
        out['render_snapshots'] = {k: bool(k in b and a[k].shape == b[k].shape and np.array_equal(a[k], b[k])) for k in sorted(set(a.files) | set(b.files))}
    nm, om = json.loads((new / 'manifest.json').read_text()), json.loads((old / 'manifest.json').read_text())
    out['manifest'] = {k: nm.get(k) == om.get(k) for k in ('n_actions', 'n_boundaries', 'model_identity', 'model_parameters_identity', 'physical_success', 'quality')}
    out['manifest']['profile_first_difference'] = first_difference(nm['profile'], om['profile'], 'profile')
    out['identical'] = (not native and out['commands']['first_any_difference'] is None
                        and all(v['first_difference'] is None for v in out['telemetry'].values())
                        and out['terminal']['first_difference'] is None and all(out['render_snapshots'].values())
                        and all(v for k, v in out['manifest'].items() if k != 'profile_first_difference'))
    return out


def run_one(args):
    short, out = args
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    import torch
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.backends.mujoco.trace import collect_trace
    from qlm_bench.sft_v1 import sweep_expert
    torch.set_num_threads(1)
    cid = candidate(short)
    old = PRODUCTION / 'traces' / cid
    scene = json.loads((old / 'manifest.json').read_text())['scene']
    camp = json.loads((PRODUCTION / 'campaign.json').read_text())
    trace = Path(out) / 'traces' / cid
    result_path = Path(out) / 'compare' / f'{cid}.json'
    if result_path.exists():
        return json.loads(result_path.read_text())
    if trace.exists() or trace.with_name(trace.name + '.writing').exists():
        raise FileExistsError(f'{trace} exists without a comparison; inspect it, it is not overwritten')
    if sha(CHECKPOINT) != camp['source']['checkpoint_sha256']:
        raise ValueError('Controller checkpoint differs from production')
    identity = sweep_expert.verify()
    runtime = create_runtime(TASK, 'native', model_path=scene['model'], checkpoint=str(CHECKPOINT), seed=scene['seed'], horizon_s=camp['horizon_s'])
    try:
        expert = sweep_expert.build(camp['recipe'])
        contact_wrapped(runtime, expert)
        with contextlib.redirect_stdout(open(os.devnull, 'w')):  # the chain prints 1 Hz diagnostics
            result = collect_trace(runtime, expert, scene, trace, batch_identity={'native_trace_profile': camp['source']['native_trace_profile'], 'sft_v1_reproduction_of': str(old), 'frozen_expert': identity},
                                   reference=False, quality_policy='evidence-review-v1')
    finally:
        runtime.close()
    summary = {'candidate_id': cid, 'split': next(s['split'] for s in camp['slots'] if s['candidates'][0]['candidate_id'] == cid),
               'collect_trace_passed': bool(result.get('passed')), 'frozen_expert_manifest_sha256': identity['manifest_sha256']}
    if result.get('passed'):
        summary['comparison'] = compare(trace, old)
    else:
        summary['collect_trace_result'] = result
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps({'candidate': cid, 'identical': summary.get('comparison', {}).get('identical')}), flush=True)
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--ids', nargs='+', required=True)
    p.add_argument('--workers', type=int, default=2)
    a = p.parse_args()
    camp = json.loads((PRODUCTION / 'campaign.json').read_text())
    split = {s['candidates'][0]['candidate_id']: s['split'] for s in camp['slots']}
    for short in a.ids:
        if split[candidate(short)] != 'train':
            raise ValueError(f'{candidate(short)} is {split[candidate(short)]}; only train scenes are used')
    jobs = [(s, str(a.out)) for s in a.ids]
    if a.workers <= 1:
        rows = [run_one(j) for j in jobs]
    else:
        import multiprocessing as mp
        with mp.get_context('spawn').Pool(a.workers, maxtasksperchild=1) as pool:
            rows = pool.map(run_one, jobs)
    print(json.dumps({'runs': len(rows), 'identical': sum(bool(r.get('comparison', {}).get('identical')) for r in rows)}))


if __name__ == '__main__':
    sys.exit(main())
