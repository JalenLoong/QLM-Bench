"""Run Standard100 against a policy server that speaks qlm-live-v1 (QLM-Bench is the RPC client).

The paper reports 300 episodes per policy: the Standard100 protocol at policy seed 42 plus two repeats at
seeds 43 and 44 (same 100 cases, resets, budgets and success criteria; trial ids ``<base>-repeat02`` and
``<base>-repeat03``). Run one process per seed; ``--cases`` restricts a run to some cases (a selection
aid for parallel clients, not a Standard100 success rate).

Every attempt of every trial gets its own transport session
(``evaluation-<task>/<case_id>/<trial_id>/attempt-NNN``) and a fresh simulator, so one policy server can serve
all three seeds, resumed runs and parallel clients; after a case its driver is released and memory is trimmed. Outputs in ``--output``: ``result.json`` and ``result/``
(manifest, episodes.parquet, summary.json), ``progress/<trial>.json``, ``durable-outcomes/<attempt>.json``,
``events.jsonl``, ``memory.jsonl`` and, with ``--record-video``, ``<case>/actual_media/``.
"""
from copy import deepcopy
import ctypes
import gc
import hashlib
import json
import math
from pathlib import Path
import time

from qlm_bench.benchmark.cases import EvaluationProtocol, TrialSpec
from qlm_bench.benchmark.results import write_result
from qlm_bench.benchmark.runner import EvaluationRunner
from qlm_bench.benchmark import suite

POLICY_SEEDS = (42, 43, 44)
VALID = ('success', 'failure', 'timeout')


def trials_for_seed(spec, seed):
    """Expected trials of one policy-seed repeat of the 300-episode protocol (seed 42 = Standard100 itself)."""
    if seed not in POLICY_SEEDS:
        raise ValueError(f'Policy seed must be one of {POLICY_SEEDS}')
    base = [t for t in spec['expected_trials'] if t['policy_seed'] == 42]
    if seed == 42:
        return base
    repeat = POLICY_SEEDS.index(seed) + 1
    return [{**t, 'trial_id': f"{t['trial_id']}-repeat{repeat:02d}", 'policy_seed': seed} for t in base]


def load_protocol(bench, cases, *, policy_seed=42, selected=None):
    path = Path(bench) / 'protocol_snapshot.json'
    spec = deepcopy(suite.read(path)['spec']) if path.is_file() else suite.protocol(cases).record()
    spec['expected_trials'] = trials_for_seed(spec, policy_seed)
    if selected is not None:
        spec['expected_trials'] = [t for t in spec['expected_trials'] if t['case_id'] in selected]
        tasks = {t['task_id'] for t in spec['expected_trials']}
        spec['task_command_budgets'] = {k: v for k, v in spec.get('task_command_budgets', {}).items() if k in tasks}
    if policy_seed != 42:
        spec['protocol_id'] = f"{spec['protocol_id']}-seed{policy_seed}"
    spec['expected_trials'] = tuple(TrialSpec(**t) for t in spec['expected_trials'])
    protocol = EvaluationProtocol(**spec)
    if {t.case_id for t in protocol.expected_trials} != {c.case_id for c in cases}:
        raise ValueError('Protocol trials and suite cases differ')
    if any(protocol.command_budget(c.task_id) != round(c.scene['horizon_s'] * 50) for c in cases):
        raise ValueError('Protocol command budget differs from the case horizon')
    return protocol


def _atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.partial')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def _trimmed_rss():
    """Collect garbage of retired cases, return freed heap to the OS, and report the resident size."""
    gc.collect()
    try:
        ctypes.CDLL(None).malloc_trim(0)
    except (AttributeError, OSError):
        pass
    try:
        return int(next(line.split()[1] for line in Path('/proc/self/status').read_text().splitlines()
                        if line.startswith('VmRSS:'))) * 1024
    except (OSError, StopIteration):
        return None


def _normalize(x):
    if hasattr(x, 'tobytes'):
        return {'shape': list(x.shape), 'dtype': str(x.dtype), 'sha256': hashlib.sha256(x.tobytes()).hexdigest()}
    if isinstance(x, dict):
        return {k: _normalize(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)):
        return [_normalize(v) for v in x]
    return x


class LiveExecutor:
    """Episode strategy for EvaluationRunner: chunk-16 closed loop through SynchronousDriver over RPC."""
    def __init__(self, client, *, on_event=None, progress_dir=None):
        self.client = client
        self.on_event = on_event or (lambda *a: None)
        self.progress_dir = None if progress_dir is None else Path(progress_dir)
        self.drivers = {}
        self.last_history = None
        self.last_evidence = {}

    def __call__(self, adapter, case, trial, budget):
        started = time.monotonic()
        key = id(adapter.runtime)
        try:
            result = self._episode(adapter, case, trial, budget)
            terminal = result['terminal']
            self._progress(trial, {'status': 'terminal', 'trial_id': trial.trial_id, 'case_id': case.case_id,
                                   'task_id': case.task_id, 'policy_seed': trial.policy_seed,
                                   'outcome': terminal.outcome, 'termination_reason': terminal.termination_reason,
                                   'simulation_time_s': terminal.simulation_time_ns / 1e9,
                                   'executed_commands': len(result['history'].completed),
                                   'inference_calls': result['inference_calls'], 'feedback_calls': result['feedback_calls'],
                                   'all_waits_frozen': result['all_waits_frozen'],
                                   'wall_executor_s': time.monotonic() - started})
            return result
        except BaseException as exc:
            self._progress(trial, {'status': 'infrastructure_error', 'trial_id': trial.trial_id, 'case_id': case.case_id,
                                   'task_id': case.task_id, 'error_type': type(exc).__name__, 'error_message': str(exc)})
            raise
        finally:
            # A finished case must not keep its closed MuJoCo model, RAMBO weights and history alive.
            self.drivers.pop(key, None)

    def _progress(self, trial, row):
        print(json.dumps(row), flush=True)
        if self.progress_dir is not None:
            _atomic_json(self.progress_dir / (trial.trial_id + '.json'), row)

    def _episode(self, adapter, case, trial, budget):
        from qlm_bench.live import SynchronousDriver
        self.last_history = None
        self.last_evidence = {}
        key = id(adapter.runtime)
        counts = {'predict': 0, 'feedback': 0, 'wait': 0, 'partial_intervals': 0, 'requested_executed_differences': 0}
        frozen = [True]

        def event(kind, payload):
            if kind == 'execution':
                for command in payload['ack']['body']['commands']:
                    counts['partial_intervals'] += int(command['status'] == 'partial')
                    counts['requested_executed_differences'] += int(command['status'] == 'completed' and
                                                                    command['requested'] != command['executed'])
            if kind == 'wait':
                counts['wait'] += 1
                frozen[0] &= bool(payload['simulation_frozen'])
                if payload['method'] in counts:
                    counts[payload['method']] += 1
            self.on_event(kind, payload)
        driver = self.drivers.get(key)
        if driver is None:
            # One transport session per (trial, attempt): seeds, retries and resumed runs never reuse a session.
            attempt = getattr(self, 'attempt_id', None) or f'{trial.trial_id}/attempt-001'
            driver = SynchronousDriver(adapter.runtime, self.client, session_id=f'evaluation-{case.task_id}/{case.case_id}/{attempt}',
                                       instruction=case.instruction, task_id=case.task_id, task_version=case.task_version,
                                       state_semantics=suite.SEMANTICS, on_event=event, max_groups=math.ceil(budget / 16))
            self.drivers[key] = driver
        driver.on_event = event
        driver.max_groups = math.ceil(budget / 16)
        observed = adapter.observe()
        try:
            driver.reset_episode(observed.episode_uid, policy_seed=trial.policy_seed, initial_snapshot=adapter.runtime.state())
            result = driver.run_episode()
        except BaseException:
            self.last_history = driver.history
            self.last_evidence = {'inference_calls': counts['predict'], 'feedback_calls': counts['feedback'],
                                  'rpc_waits': counts['wait'], 'all_waits_frozen': frozen[0],
                                  'partial_intervals': counts['partial_intervals'],
                                  'requested_executed_differences': counts['requested_executed_differences'],
                                  'simulation_time_ns': adapter.runtime.state()['simulation_time_ns'],
                                  'closed_loop_status': 'PARTIAL_CLOSED_LOOP' if driver.history and driver.history.completed else 'NOT_RUN'}
            self.on_event('partial_execution', {'trial_id': trial.trial_id, 'counts': counts,
                                                'completed_commands': len(driver.history.completed) if driver.history else 0})
            raise
        adapter._terminal = deepcopy(adapter.runtime.terminal)
        terminal = adapter.terminal()
        closed = counts['predict'] >= 2 and counts['feedback'] >= 2 and frozen[0] and result['task_terminal']
        return {'terminal': terminal, 'history': driver.history, 'simulation_time_ns': result['simulation_time_ns'],
                'inference_calls': counts['predict'], 'feedback_calls': counts['feedback'], 'rpc_waits': counts['wait'],
                'all_waits_frozen': frozen[0], 'partial_intervals': counts['partial_intervals'],
                'requested_executed_differences': counts['requested_executed_differences'],
                'closed_loop_status': 'PASS_CLOSED_LOOP' if closed else 'PARTIAL_CLOSED_LOOP'}


def run(resource_root, output, *, policy_port, policy_seed=42, suite_dir=None, cases=None, policy_name='policy',
        record_video=False, ffmpeg='ffmpeg', ffprobe='ffprobe', previous_outcomes=(), rpc_timeout_s=600.):
    """Evaluate one policy seed of the Standard100 protocol; returns the result dict written to result.json."""
    import os
    os.environ.setdefault('MUJOCO_GL', 'egl')   # Standard100 renders with hardware EGL
    import torch
    torch.set_num_threads(1)                    # RAMBO and the QP run single-threaded, as in the paper evaluation
    from qlm_bench.live import RPCClient
    from qlm_bench.live.media import ActualRGBRecorder
    resource_root = Path(resource_root)
    bench = Path(suite_dir) if suite_dir else resource_root / 'benchmarks' / suite.RELEASE
    _, all_cases = suite.load_suite(bench)
    selected = None if cases is None else set(cases)
    if selected is not None:
        unknown = selected - {c.case_id for c in all_cases}
        if unknown:
            raise ValueError(f'Unknown Standard100 cases: {sorted(unknown)}')
        all_cases = [c for c in all_cases if c.case_id in selected]
    protocol = load_protocol(bench, all_cases, policy_seed=policy_seed, selected=selected)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    media = {}

    class TrialRecorder(ActualRGBRecorder):
        """Close each episode's video at its terminal; per-boundary records are already on disk."""
        def seal_terminal(self, snapshot):
            super().seal_terminal(snapshot)
            if not self.closed:
                self.close()
                self.frames = []

    def event(kind, payload):
        with (output / 'events.jsonl').open('a') as f:
            f.write(json.dumps({'event': kind, **_normalize(payload)}, allow_nan=False) + '\n')

    def factory(case):
        rss = _trimmed_rss()
        with (output / 'memory.jsonl').open('a') as f:
            f.write(json.dumps({'event': 'before_new_case', 'case_id': case.case_id, 'rss_bytes': rss,
                                'wall_unix_s': time.time()}) + '\n')
        adapter = suite.runtime_for(resource_root, bench, case)
        if record_video:
            recorder = TrialRecorder(output / case.case_id / 'actual_media', ffmpeg=ffmpeg, ffprobe=ffprobe,
                                     identity={'case_id': case.case_id, 'scope': protocol.scope},
                                     observer=adapter.runtime.renderer.observer_clip is not None)
            adapter.runtime.on_observation = recorder.observe
            adapter.runtime.on_terminal = recorder.seal_terminal
            media[case.case_id] = recorder
        return adapter

    def durable(row):
        _atomic_json(output / 'durable-outcomes' / (row['attempt_id'].replace('/', '__') + '.json'), row)

    executor = LiveExecutor(RPCClient(port=policy_port, timeout_s=rpc_timeout_s), on_event=event,
                            progress_dir=output / 'progress')
    runner = EvaluationRunner(protocol, {c.case_id: c for c in all_cases}, runtime_factory=factory,
                              policy_name=policy_name, episode_executor=executor, on_outcome=durable)
    try:
        result = runner.run(submission_id=output.name, benchmark_release=suite.RELEASE, previous_outcomes=previous_outcomes)
        result['run_manifest'].update(policy_seed=policy_seed, case_subset=sorted(selected) if selected else None)
        write_result(output / 'result', result['run_manifest'], result['outcomes'])
        suite.write(output / 'result.json', result)
    finally:
        for recorder in media.values():
            recorder.close()
    return result


def complete(result):
    """True when every expected trial has a task outcome (success / failure / timeout)."""
    done = {r['trial_id'] for r in result['outcomes'] if r['outcome'] in VALID}
    return done == {t['trial_id'] for t in result['run_manifest']['expected_trials']}
