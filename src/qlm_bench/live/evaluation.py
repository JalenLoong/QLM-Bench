"""Explicit local trial protocol and empirical metrics over QLM task outcomes."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import statistics

from qlm_bench.evaluation import EvaluationProtocol, TrialSpec, write_result
from qlm_bench.policy_interface.physical import ACTION_SCHEMA, COMMAND_INTERVAL_NS


def load_protocol(path):
    record = json.loads(Path(path).read_text())
    if record.get('schema') != 'qlm-local-live-evaluation-v1' or record.get('task_id') != 'push_box':
        raise ValueError('Explicit local Push Box evaluation protocol required')
    horizon = record['horizon_simulation_s']
    if not isinstance(horizon, (int, float)) or not math.isfinite(horizon) or horizon <= 0 or \
            not math.isclose(horizon * 50, record['max_commands']) or record['max_commands'] % 16:
        raise ValueError('Explicit whole command/group horizon required')
    trials = record['trials']
    if not trials or len({row['trial_id'] for row in trials}) != len(trials):
        raise ValueError('Unique scheduled trial membership required')
    for row in trials:
        for key in ('environment_seed', 'policy_seed'):
            if type(row[key]) is not int or row[key] < 0:
                raise ValueError('Explicit nonnegative trial seeds required')
    if record.get('error_policy') != 'count_as_failure' or record.get('retry_selection') != 'first_attempt':
        raise ValueError('This user trial batch retains failures and does not selectively retry')
    return record


def empirical_metrics(protocol, outcomes):
    expected = [row['trial_id'] for row in protocol['trials']]
    indexed = {row['trial_id']: row for row in outcomes}
    if len(indexed) != len(outcomes) or set(indexed) != set(expected):
        raise ValueError('Metrics require exactly one outcome per scheduled trial')
    counts = Counter(row['outcome'] for row in outcomes)
    complete = counts['not_run'] == 0
    actual = [row for row in outcomes if row['outcome'] != 'not_run']
    successes = [row for row in actual if row['outcome'] == 'success']
    def average(key, selected=actual):
        values = [row[key] for row in selected if row.get(key) is not None]
        return statistics.mean(values) if values else None
    return {'schema': 'qlm-local-empirical-metrics-v1',
        'status': 'complete' if complete else 'incomplete', 'task': 'push_box',
        'scheduled_trials': len(expected), 'attempted_trials': len(actual),
        'counts': {key: counts[key] for key in ('success', 'failure', 'timeout', 'error', 'not_run')},
        'success_rate': counts['success'] / len(expected) if complete else None,
        'fall_rate': sum(row['termination_reason'] == 'fall' for row in outcomes) / len(expected) if complete else None,
        'timeout_rate': counts['timeout'] / len(expected) if complete else None,
        'error_rate': counts['error'] / len(expected) if complete else None,
        'mean_simulation_duration_s': average('simulation_time_ns') / 1e9 if actual else None,
        'mean_success_time_s': average('simulation_time_ns', successes) / 1e9 if successes else None,
        'mean_wall_duration_s': average('wall_time_s'),
        'mean_completed_commands': average('executed_commands'),
        'diagnostics': {'mean_terminal_box_progress_x_m': average('box_progress_x_m'),
                        'mean_max_box_progress_x_m': average('max_box_progress_x_m')},
        'horizon_simulation_s': protocol['horizon_simulation_s'],
        'denominator': 'all scheduled first attempts; errors count as unsuccessful',
        'formal_benchmark_score': None,
        'scope': 'user-requested local nominal-Box05 trial evaluation; not an accepted public benchmark release'}


def outcome_row(trial, result, wall_s, *, media=None, error=None):
    terminal = result.get('terminal', {}) if result else {}
    reason = terminal.get('reason', 'execution_error' if error else 'not_run')
    if error:
        outcome = 'error'
    elif terminal.get('success'):
        outcome = 'success'
    elif terminal.get('fallen'):
        outcome = 'failure'
    elif terminal.get('timed_out'):
        outcome = 'timeout'
    elif result:
        outcome = 'error'
    else:
        outcome = 'not_run'
    evidence = None
    if terminal and 'reason' in terminal:
        camera_map = {'ego': 'go2_ego', 'task_centric': 'd435i_rgb_task'}
        evidence = {'evaluator_state': {'state': terminal['state'], 'task_review': terminal.get('task_review', {})},
                    'rgb': {camera_map[key]: value for key, value in terminal['rgb'].items()}}
    progress = terminal.get('state', {}).get('task.progress')
    return {'trial_id': trial['trial_id'], 'attempt_id': trial['trial_id'] + ':first-attempt',
        'case_id': trial['case_id'], 'task_id': 'push_box', 'policy_seed': trial['policy_seed'],
        'environment_seed': trial['environment_seed'], 'outcome': outcome,
        'termination_reason': reason, 'simulation_time_ns': result.get('simulation_time_ns', 0) if result else 0,
        'wall_time_s': wall_s, 'executed_commands': result.get('completed_commands', 0) if result else 0,
        'retry_of': None, 'terminal_before_reset': evidence is not None,
        'terminal_evidence': evidence, 'error': error,
        'box_progress_x_m': progress[0] if progress else None,
        'max_box_progress_x_m': media.get('max_box_progress_x_m') if media else None,
        'groups': result.get('groups', 0) if result else 0,
        'media_manifest': str(Path(media['videos']['ego']['path']).parent / 'media.json') if media else None}


def result_bundle(output, protocol, rows, cases, *, source, policy_identity, version, resources):
    expected = tuple(TrialSpec(row['trial_id'], row['case_id'], 'push_box', row['policy_seed'])
                     for row in protocol['trials'])
    specification = json.dumps(protocol, sort_keys=True, separators=(',', ':')).encode()
    qlm_protocol = EvaluationProtocol(protocol['protocol_id'], protocol['suite_id'], protocol['case_set_id'],
        protocol['runtime_profile'], protocol['controller_profile'], protocol['max_commands'],
        protocol['error_policy'], protocol['retry_selection'], 'engineering_diagnostic', 'draft', expected,
        {'source_commit': source['source_commit'], 'spec_sha256': hashlib.sha256(specification).hexdigest()})
    observation_profile = 'wam-v3-dual-rgb-measured-root-link' if version == 'v3' else 'wam-v2-dual-rgb'
    identities = {}
    for trial in protocol['trials']:
        reset = cases.get(trial['case_id'])
        identities[trial['case_id']] = {'task_id': 'push_box', 'task_version': protocol['task_version'],
            'assets': {v['asset_id']: v['version'] for v in resources.values()},
            'seed': trial['environment_seed'], 'runtime_profile': protocol['runtime_profile'],
            'controller_profile': protocol['controller_profile'], 'observation_profile': observation_profile,
            'camera_keys': ['go2_ego', 'd435i_rgb_task'],
            'provenance': {'evidence_kind': 'actual_runtime' if reset else 'not_run',
                           'initial_state': deepcopy(reset), 'reset_reconstruction_passed': False,
                           'source': source, 'resources': resources}}
    manifest = {'schema': 'qlm-evaluation-result-v1', 'scope': qlm_protocol.scope,
        'submission_id': version + ':' + protocol['protocol_id'], 'source_commit': source['source_commit'],
        'source': source, 'evidence_kind': 'actual_runtime', 'publication_status': 'local_only',
        'policy_identity': {'code': 'formal-first-SFT-step1000', 'adapter': 'qlm-live-v1',
                            'observation_profile': observation_profile, 'deployment': policy_identity},
        'protocol': qlm_protocol.record(), 'expected_trials': qlm_protocol.record()['expected_trials'],
        'case_identity': identities, 'case_validation': {key: 'draft' for key in identities},
        'action_scheduling': {'schema': ACTION_SCHEMA, 'command_interval_ns': COMMAND_INTERVAL_NS,
                             'mode': 'synchronous_single_command', 'desired_force': 'zero'},
        'policy_replanning': {'commands_per_group': 16, 'simulation_time_pauses_during_RPC': True},
        'not_run': ['official_benchmark_aggregate', 'new_training', 'new_demonstrations']}
    validation = write_result(output, manifest, rows)
    empirical = empirical_metrics(protocol, rows)
    Path(output, 'empirical_metrics.json').write_text(json.dumps(empirical, indent=2, allow_nan=False) + '\n')
    Path(output, 'validation.json').write_text(json.dumps(validation, indent=2, allow_nan=False) + '\n')
    return empirical, validation
