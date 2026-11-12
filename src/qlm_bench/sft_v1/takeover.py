"""Expert-in-the-loop takeover from a saved chunk boundary, and expert runs from reset (sft-v1/QLM-SIM-001).

The RL-v3 scene worker only executes external command chunks. Scripted experts are called once per 50 Hz command
inside the process through ``ExpertAdapter`` (as ``backends/mujoco/recording.py`` does). This module puts the two
together without changing any existing operation:

* ``open_runtime``: the scene worker's runtime (same ``create_runtime`` call, EvalCase goal/horizon overlay, NativeCPU,
  RAMBO CPU, rgb profile ``dual-rgb-360p-v1``) but ``trace_only=True``: no renderer, the same numeric
  observation/refresh path. The snapshot identity does not include the renderer, so RL-v3 own states captured by the
  hardware-EGL worker restore here unchanged.
* ``takeover``: ``own_state.load`` + ``snapshot.restore`` (the worker's restore path), a fresh ``ExpertAdapter``, the
  chosen expert entered mid-way, then one expert command per 50 Hz tick until the runtime's own terminal: task
  success (original predicate and hold), robot fall, or timeout at the case horizon on the restored absolute clock
  (24 s for push_box), or a physics-instability stop.
* ``from_reset``: ``suite.reconstruct`` (the Standard100 reset) and the same loop from t=0 (ideal trajectories, E*
  consistency runs).

Experts (``EXPERTS``):
    push_box_expert  the unmodified expert with the scene's own expert profile (source_profile = push100 provenance
                     task_profile.expert); optional ``overrides`` of the three regular-push options.
    e0               reference arm E0: push_box_expert entered mid-way at straight_push with lateral tracking
                     (gain 2.0, limit 0.015 m) and corner_recovery on, no steering (design section 6, G4).
    recovery         E* (``push_box_recovery``) with a versioned parameter set.

Records per run (``save``): every command requested by the expert and executed by the runtime (native9), the expert
phase, commanded contact point and world base velocity, one RL-v3 privileged row (``rl_v3.privileged`` columns:
8 box corners, goal rectangle, box centre and quaternion, progress, FL/body contact, hold, base pose, FL foot, fallen,
success, terminal code) at the start and after every command, and the chunk-boundary subset (absolute tick % 160 == 0).

CLI: ``python -m qlm_bench.sft_v1.takeover batch --jobs jobs.json --out DIR --controller model_2000.pt --workers 8``.
A job is {id, case, model, kind, state?, params?, overrides?, max_seconds?}; a job with ``state`` is a takeover, one
without is a run from reset. Kinds ``sweep_expert`` (from reset) and ``sweep_e0`` (takeover) dispatch to
``sft_v1.sweep_takeover`` (frozen production sweep expert, sft-v1/QLM-SIM-003); kind ``sweep_recovery`` (either) dispatches to
``sft_v1.sweep_recovery`` (E* for sweep_block_to_zone). Finished jobs (``<out>/<id>.json``) are skipped on rerun.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time as wall

import numpy as np

SCHEMA = 'qlm-sft-v1-takeover-v1'
COMMAND_TICKS = 10
CHUNK_TICKS = 160
TICK_SECONDS = 0.002
E0_OVERRIDES = {'lateral_tracking_gain': 2.0, 'lateral_tracking_limit_m': 0.015, 'corner_recovery': True}
OVERRIDE_KEYS = tuple(E0_OVERRIDES)
EXPERTS = ('push_box_expert', 'e0', 'recovery', 'sweep_expert', 'sweep_e0', 'sweep_recovery')  # sweep_*: sft_v1.sweep_takeover / sweep_recovery


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_identity():
    """Hashes of this tool and the recovery routine plus the hashed simulator source identity."""
    from qlm_bench.backends.mujoco.rl_v2.storage import execution_source_identity
    here = Path(__file__).resolve().parent
    return {'execution_source_identity': execution_source_identity(),
            'files': {p.name: _sha(p) for p in sorted(here.glob('*.py'))},
            'push_box_expert': _sha(here.parent / 'backends/mujoco/experts/push_box_expert.py'),
            'push_box_corner_recovery': _sha(here.parent / 'backends/mujoco/experts/push_box_corner_recovery.py')}


# ------------------------------------------------------------------ runtime

def open_runtime(case_path, model_path, controller):
    """Trace-only NativeCPU runtime bound to an EvalCase scene, as the RL-v3 scene worker builds it (minus rendering)."""
    import torch
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.evaluation import EvalCase
    torch.set_num_threads(1)
    case = EvalCase.from_record(json.loads(Path(case_path).read_text()))
    overlay = {**case.scene.get('goal_overlay', {}), 'horizon_s': case.scene['horizon_s']}
    rt = create_runtime(case.task_id, 'native', model_path=str(model_path), checkpoint=str(controller), seed=case.seed,
                        device='cpu', trace_only=True, rgb_profile='dual-rgb-360p-v1', profile_override=overlay)
    return rt, case, _sha(case_path)


class RuntimeCache:
    """One runtime per scene for a worker process; a runtime left without a terminal is rebuilt."""

    def __init__(self, controller):
        self.controller = str(controller)
        self.key = self.rt = self.case = self.binding = None

    def get(self, case_path, model_path):
        key = (str(case_path), str(model_path))
        if self.rt is not None and (key != self.key or (self.rt.current is not None and self.rt.terminal is None)):
            self.close()
        if self.rt is None:
            self.rt, self.case, self.binding = open_runtime(case_path, model_path, self.controller)
            self.key = key
        return self.rt, self.case, self.binding

    def close(self):
        if self.rt is not None:
            self.rt.close()
        self.key = self.rt = self.case = self.binding = None


# ------------------------------------------------------------------ experts

def make_expert(rt, kind, *, params=None, overrides=None):
    """Fresh ExpertAdapter, command function, mid-way entry and the effective configuration record."""
    from qlm_bench.backends.mujoco.expert_adapter import ExpertAdapter
    from qlm_bench.backends.mujoco.experts import push_box_expert
    if rt.task.task != 'push_box':
        raise ValueError('The takeover tool is implemented for push_box only')
    adapter = ExpertAdapter(rt.physics, rt.core, rt.task)
    expert = adapter.cfg.approved_profile['expert']
    config = {'kind': kind, 'scene_expert_profile': copy.deepcopy(expert)}
    if kind in ('push_box_expert', 'e0'):
        if params is not None:
            raise ValueError(f'{kind} takes overrides, not recovery params')
        chosen = copy.deepcopy(E0_OVERRIDES) if kind == 'e0' else {}
        chosen.update(copy.deepcopy(overrides or {}))
        if set(chosen) - set(OVERRIDE_KEYS):
            raise ValueError(f'Only {OVERRIDE_KEYS} may be overridden')
        # ExpertAdapter.apply_profile_override refuses keys absent from the source profile; these three options are read
        # by push_box_expert / corner_reference directly from the profile, so they are set there explicitly and recorded.
        expert.update(chosen)
        config['overrides'] = chosen

        def entry(env, t):
            env._expert_stage = 'straight_push'
            env._expert_push_start = float(t)
        fn = push_box_expert.command
    elif kind == 'recovery':
        if overrides:
            raise ValueError('recovery takes params, not overrides')
        from qlm_bench.sft_v1 import push_box_recovery
        config['recovery_params'] = push_box_recovery.configure(adapter, params)
        entry, fn = push_box_recovery.enter_midway, push_box_recovery.command
    else:
        raise ValueError(f'Unknown expert {kind}')
    config['effective_expert_profile'] = copy.deepcopy(expert)
    return adapter, fn, entry, config


# ------------------------------------------------------------------ loop

def _vector(value, n):
    return [math.nan] * n if value is None else [float(x) for x in value]


def run_loop(rt, adapter, fn, *, name, max_seconds=None):
    """Expert commands until the runtime's terminal (or a physics-instability stop / optional local cap for tests)."""
    from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
    from qlm_bench.rl_v3 import privileged
    start = int(rt.physics.ticks[0])
    if start % COMMAND_TICKS:
        raise ValueError('Expert loop must start on a command boundary')
    cap = None if max_seconds is None else start + int(round(max_seconds / TICK_SECONDS))
    requested, executed, phases, contact_points, base_velocity = [], [], [], [], []
    rows = [privileged.row(rt)]
    terminal, i = None, 0
    while rt.terminal is None:
        tick = int(rt.physics.ticks[0])
        if cap is not None and tick >= cap:
            break
        values, diag = fn(adapter, tick * TICK_SECONDS)
        prepared = prepare_command(values, f'{name}:{i}', tick)
        try:
            outcome = rt.step(prepared)
        except FloatingPointError as exc:
            terminal = {'reason': 'physics_instability', 'tick': int(rt.physics.ticks[0]), 'success': False, 'fallen': False,
                        'timed_out': False, 'detail': str(exc)}
            break
        command = outcome['command']
        requested.append([float(x) for x in prepared['requested']])
        executed.append(_vector(command['executed'], 9))
        phases.append(str(diag.get('phase')))
        contact_points.append(_vector(diag.get('commanded_contact_point'), 3))
        base_velocity.append(_vector(diag.get('commanded_world_base_velocity'), 3))
        reason = None if outcome['terminal'] is None else outcome['terminal']['reason']
        rows.append(privileged.row(rt, completed=command['status'] == 'completed', terminal_reason=reason))
        i += 1
        if outcome['terminal'] is not None:
            t = outcome['terminal']
            terminal = {'reason': reason, 'tick': int(rt.physics.ticks[0]), 'success': bool(t.get('success', False)),
                        'fallen': bool(t.get('fallen', False)), 'timed_out': bool(t.get('timed_out', False))}
    columns = privileged.columns(rt)
    arrays = {'requested': np.asarray(requested, np.float64).reshape(-1, 9), 'executed': np.asarray(executed, np.float64).reshape(-1, 9),
              'phase': np.asarray(phases, dtype='U32'), 'commanded_contact_point': np.asarray(contact_points, np.float64).reshape(-1, 3),
              'commanded_world_base_velocity': np.asarray(base_velocity, np.float64).reshape(-1, 3),
              'privileged': np.asarray(rows, np.float64), 'columns': np.asarray(columns)}
    ticks = arrays['privileged'][:, 0].astype(np.int64)
    arrays['chunk_index'] = np.flatnonzero(ticks % CHUNK_TICKS == 0)
    end = int(rt.physics.ticks[0])
    horizon_ticks = int(round(rt.profile['horizon_s'] / TICK_SECONDS))
    outcome = {'terminal': terminal, 'success': bool(terminal and terminal['success']), 'fallen': bool(terminal and terminal['fallen']),
               'stopped_by_cap': terminal is None, 'start_tick': start, 'end_tick': end, 'commands': i,
               'start_s': start * TICK_SECONDS, 'end_s': end * TICK_SECONDS, 'elapsed_s': (end - start) * TICK_SECONDS,
               'horizon_s': float(rt.profile['horizon_s']), 'horizon_margin_s': (horizon_ticks - end) * TICK_SECONDS,
               'phases': sorted(set(phases))}
    return arrays, outcome


def takeover(cache, *, case, model, state, kind, params=None, overrides=None, name='takeover', max_seconds=None):
    """Restore an RL-v3 own state and let the expert finish the episode from that boundary."""
    from qlm_bench.backends.mujoco.rl_v2 import snapshot as snap
    from qlm_bench.rl_v3 import own_state
    rt, ec, binding = cache.get(case, model)
    stored, record = own_state.load(Path(state), binding_sha256=binding)
    snap.restore(rt, stored)
    adapter, fn, entry, config = make_expert(rt, kind, params=params, overrides=overrides)
    t0 = int(rt.physics.ticks[0]) * TICK_SECONDS
    entry(adapter, t0)
    started = wall.monotonic()
    arrays, outcome = run_loop(rt, adapter, fn, name=name, max_seconds=max_seconds)
    start = {'mode': 'takeover', 'state': str(Path(state).resolve()), 'state_sha256': record['snapshot_sha256'],
             'absolute_tick': record['absolute_tick'], 'origin': record['origin']}
    return arrays, _summary(ec, case, model, cache.controller, start, config, outcome, wall.monotonic() - started)


def from_reset(cache, *, case, model, kind, params=None, overrides=None, name='reset', max_seconds=None):
    """Standard100 reset of the case, then the expert from t=0 (settle, approach, push)."""
    from qlm_bench.backends.mujoco.suite import reconstruct
    rt, ec, binding = cache.get(case, model)
    reconstruct(rt, ec)
    adapter, fn, _, config = make_expert(rt, kind, params=params, overrides=overrides)
    started = wall.monotonic()
    arrays, outcome = run_loop(rt, adapter, fn, name=name, max_seconds=max_seconds)
    start = {'mode': 'reset', 'case_seed': ec.seed}
    return arrays, _summary(ec, case, model, cache.controller, start, config, outcome, wall.monotonic() - started)


def _summary(ec, case, model, controller, start, config, outcome, seconds):
    return {'schema': SCHEMA, 'case_id': ec.case_id, 'case': str(Path(case).resolve()), 'case_sha256': _sha(case), 'model': str(model),
            'controller': str(controller), 'controller_sha256': _sha(controller), 'start': start, 'expert': config,
            'outcome': outcome, 'wall_s': seconds, 'code': code_identity()}


def save(stem, arrays, summary):
    """<stem>.npz (arrays) then <stem>.json (summary with the npz hash); the json marks the job complete."""
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    npz = stem.with_suffix('.npz')
    partial = stem.with_name(stem.name + '.partial.npz')
    np.savez_compressed(partial, **arrays)
    partial.replace(npz)
    summary = {**summary, 'arrays': npz.name, 'arrays_sha256': _sha(npz)}
    tmp = stem.with_name(stem.name + '.json.partial')
    tmp.write_text(json.dumps(summary, indent=1, allow_nan=False) + '\n')
    tmp.replace(stem.with_suffix('.json'))
    return summary


# ------------------------------------------------------------------ batch

def run_job(cache, job):
    if job['kind'] == 'sweep_recovery':  # E* for sweep_block_to_zone: a takeover with ``state``, a run from reset without.
        from qlm_bench.sft_v1 import sweep_recovery
        if job.get('overrides'):
            raise ValueError('sweep_recovery takes params, not overrides')
        common = dict(case=job['case'], model=job['model'], params=job.get('params'), name=job['id'], max_seconds=job.get('max_seconds'))
        if job.get('state'):
            return sweep_recovery.takeover(cache, state=job['state'], **common)
        return sweep_recovery.from_reset(cache, **common)
    if job['kind'] in ('sweep_expert', 'sweep_e0'):
        from qlm_bench.sft_v1 import sweep_takeover
        if bool(job.get('state')) != (job['kind'] == 'sweep_e0') or job.get('overrides'):
            raise ValueError('sweep_e0 needs a state, sweep_expert runs from reset; neither takes overrides')
        common = dict(case=job['case'], model=job['model'], name=job['id'], max_seconds=job.get('max_seconds'))
        if job.get('state'):
            return sweep_takeover.takeover(cache, state=job['state'], params=job.get('params'), **common)
        return sweep_takeover.from_reset(cache, **common)
    common = dict(case=job['case'], model=job['model'], kind=job['kind'], params=job.get('params'), overrides=job.get('overrides'),
                  name=job['id'], max_seconds=job.get('max_seconds'))
    if job.get('state'):
        return takeover(cache, state=job['state'], **common)
    return from_reset(cache, **common)


def _worker(args):
    jobs, out, controller = args
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    cache = RuntimeCache(controller)
    done = []
    try:
        for job in jobs:
            arrays, summary = run_job(cache, job)
            summary['job'] = job
            summary = save(Path(out) / job['id'], arrays, summary)
            o = summary['outcome']
            print(json.dumps({'id': job['id'], 'success': o['success'], 'terminal': o['terminal'] and o['terminal']['reason'],
                              'elapsed_s': round(o['elapsed_s'], 2), 'wall_s': round(summary['wall_s'], 1)}), flush=True)
            done.append(job['id'])
    finally:
        cache.close()
    return done


def batch(jobs, out, controller, workers=1):
    out = Path(out)
    ids = [j['id'] for j in jobs]
    if len(set(ids)) != len(ids):
        raise ValueError('Job ids must be unique')
    pending = [j for j in jobs if not (out / f"{j['id']}.json").exists()]
    print(f'{len(jobs)} jobs, {len(jobs) - len(pending)} done, {len(pending)} pending, {workers} workers', flush=True)
    groups = {}
    for job in pending:  # One scene per group keeps the runtime of a worker process.
        groups.setdefault((job['case'], job['model']), []).append(job)
    tasks = [(g, str(out), str(controller)) for g in groups.values()]
    if workers <= 1:
        return [x for t in tasks for x in _worker(t)]
    import multiprocessing as mp
    with mp.get_context('spawn').Pool(workers, maxtasksperchild=4) as pool:
        return [x for r in pool.imap_unordered(_worker, tasks) for x in r]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='command', required=True)
    b = sub.add_parser('batch')
    b.add_argument('--jobs', type=Path, required=True)
    b.add_argument('--out', type=Path, required=True)
    b.add_argument('--controller', type=Path, required=True)
    b.add_argument('--workers', type=int, default=1)
    a = p.parse_args()
    jobs = json.loads(a.jobs.read_text())
    jobs = jobs['jobs'] if isinstance(jobs, dict) else jobs
    batch(jobs, a.out, a.controller, a.workers)


if __name__ == '__main__':
    sys.exit(main())
