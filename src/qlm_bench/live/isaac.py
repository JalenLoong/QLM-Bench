"""Explicit single-env physical client for the separately launched policy service."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--profile', type=Path, required=True)
    result.add_argument('--resource-root', type=Path, required=True)
    result.add_argument('--output-dir', type=Path, required=True)
    result.add_argument('--host', default='127.0.0.1')
    result.add_argument('--port', type=int, default=8765)
    result.add_argument('--timeout-s', type=float, default=600.)
    result.add_argument('--retries', type=int, default=1)
    result.add_argument('--instruction', required=True)
    result.add_argument('--session-id', required=True)
    result.add_argument('--episodes', type=int, required=True)
    result.add_argument('--max-groups', type=int, required=True,
                        help='Explicit engineering bound, never a benchmark preset')
    result.add_argument('--episode-length-s', type=float, required=True)
    result.add_argument('--seed', type=int, required=True)
    result.add_argument('--policy-seed', type=int, required=True)
    result.add_argument('--include-root-state', action='store_true')
    result.add_argument('--ground-z', type=float, default=0.)
    result.add_argument('--ground-reference', default='task-ground-plane')
    result.add_argument('--evaluation-protocol', type=Path,
                        help='Explicit local trial membership/horizon; records every outcome and three RGB views')
    result.add_argument('--policy-version', choices=('v2', 'v3'))
    result.add_argument('--ffmpeg', default='ffmpeg')
    result.add_argument('--ffprobe', default='ffprobe')
    result.add_argument('--results-python', type=Path,
                        help='Separate CPU data interpreter with PyArrow; required for evaluation result writing')
    return result


def main(argv=None):
    raw = list(sys.argv[1:] if argv is None else argv)
    command_parser = parser()
    if '--help' in raw or '-h' in raw:
        command_parser.add_argument('--viz', choices=('none', 'kit'), required=True)
        command_parser.print_help()
        return 0
    preliminary, _ = command_parser.parse_known_args(raw)
    from qlm_bench.collection.isaac import _resources, TASK_IDS
    profile = json.loads(preliminary.profile.read_text())
    evaluation = None
    if preliminary.evaluation_protocol:
        from .evaluation import load_protocol
        evaluation = load_protocol(preliminary.evaluation_protocol)
        if preliminary.policy_version is None or preliminary.results_python is None or preliminary.episodes != len(evaluation['trials']) or \
                preliminary.episode_length_s != evaluation['horizon_simulation_s'] or \
                preliminary.max_groups * 16 != evaluation['max_commands'] or \
                profile['task_profile_version'] != evaluation['task_version']:
            command_parser.error('Version, trial count, profile and bounds must match the evaluation protocol')
    if preliminary.output_dir.exists():
        raise FileExistsError('Keep actual attempts immutable; select a fresh output directory')
    if preliminary.episodes < 1 or preliminary.max_groups < 1 or preliminary.episode_length_s <= 0:
        command_parser.error('Positive episode and group bounds required')
    resources = _resources(profile, preliminary.resource_root, task='push_box')
    from isaaclab.app import AppLauncher
    from rambo.utils.physx import assert_physx_environment, validate_rambo_visualizer_args
    AppLauncher.add_app_launcher_args(command_parser)
    args = command_parser.parse_args(raw)
    validate_rambo_visualizer_args(command_parser, args, raw)
    args.enable_cameras = True
    args.output_dir.mkdir(parents=True, exist_ok=False)
    from qlm_bench.collection.orchestrator import source_identity
    from .protocol import STATE_SEMANTICS
    from .runner import SynchronousDriver
    from .transport import RPCClient
    started = time.time()
    manifest = dict(schema='qlm-live-attempt-v1', work_id='EVAL-002' if evaluation else 'INFER-001', source=source_identity(),
                    arguments={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
                    resources=resources, evidence_kind='actual_runtime', publication_status='local_only',
                    status='running', started_unix=started,
                    not_run=['formal_benchmark_score', 'training', 'new_demonstrations'])
    if evaluation:
        manifest.update(evaluation_protocol=evaluation, policy_version=args.policy_version,
                        policy_work_id='v3/EVAL-001' if args.policy_version == 'v3' else 'shared-v2/EVAL-002')
    manifest_path = args.output_dir/'attempt.json'
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    app = runtime = video_recorder = None
    observer_handles = None
    cases, trial_rows, policy_identity = {}, [], None
    current_trial = None
    code = 1
    events = (args.output_dir/'events.jsonl').open('x')
    def record(kind, payload):
        events.write(json.dumps({'event':kind, 'payload':payload}, allow_nan=False)+'\n')
        events.flush()
        if evaluation and kind == 'reset' and current_trial is not None:
            cases[current_trial['case_id']] = payload['snapshot']
        if evaluation and kind == 'policy_reset':
            nonlocal policy_identity
            policy_identity = payload['response'].get('model_identity', payload['response'].get('identity', {}))
    try:
        app = AppLauncher(args)
        from rambo.tasks.common.controller_runtime import ControllerRuntime
        def attach_media(created_runtime):
            nonlocal video_recorder, observer_handles
            from rambo.recording_evaluation import EvaluationVideoRecorder, create_observer
            observer, observer_handles = create_observer(profile)
            video_recorder = EvaluationVideoRecorder(created_runtime.base_env, observer,
                args.output_dir / 'videos', args.ffmpeg, args.ffprobe)
            created_runtime.base_env._v2_recorder = video_recorder
        runtime = ControllerRuntime(TASK_IDS['push_box'], profile=profile,
                   resource_root=args.resource_root, asset_id=resources['task_asset']['asset_id'],
                   seed=args.seed, episode_length_s=args.episode_length_s,
                   device=getattr(args,'device','cuda:0'),
                   on_environment_ready=attach_media if evaluation else None)
        manifest['runtime'] = assert_physx_environment(runtime.env)
        client = RPCClient(args.host,args.port,timeout_s=args.timeout_s,retries=args.retries)
        semantics = dict(STATE_SEMANTICS,ground_z=args.ground_z,ground_reference=args.ground_reference) \
                    if args.include_root_state else {}
        driver = SynchronousDriver(runtime,client,session_id=args.session_id,
                 instruction=args.instruction,task_version=profile['task_profile_version'],
                 timeout_s=args.timeout_s,state_semantics=semantics,on_event=record,max_groups=args.max_groups)
        outcomes = []
        for index in range(args.episodes):
            if not evaluation:
                driver.reset_episode(f'{args.session_id}:episode-{index:04}',policy_seed=args.policy_seed+index)
                outcomes.append(driver.run_episode())
                continue
            import torch
            from .evaluation import outcome_row
            current_trial = evaluation['trials'][index]
            torch.manual_seed(current_trial['environment_seed'])
            trial_start = time.monotonic()
            result = media = error = None
            print(json.dumps({'event': 'evaluation_trial_start', 'version': args.policy_version,
                              **current_trial}), flush=True)
            try:
                driver.reset_episode(args.session_id + ':' + current_trial['trial_id'],
                                     policy_seed=current_trial['policy_seed'])
                video_recorder.begin(current_trial['trial_id'])
                result = driver.run_episode()
                outcomes.append(result)
            except Exception as caught:
                error = type(caught).__name__ + ': ' + str(caught)
                print('Evaluation trial failed: ' + error, file=sys.stderr, flush=True)
                if driver.identity is not None and driver.history is not None:
                    result = {'completed_commands': len(driver.history.completed),
                              'simulation_time_ns': driver.last_snapshot['simulation_time_ns'],
                              'groups': 0, 'terminal': {}}
            finally:
                if video_recorder.sinks:
                    try:
                        media = video_recorder.close_trial(error=error)
                    except Exception as caught:
                        error = (error + '; ' if error else '') + 'media: ' + str(caught)
                row = outcome_row(current_trial, result, time.monotonic() - trial_start, media=media, error=error)
                trial_rows.append(row)
                (args.output_dir / 'trial_outcomes.json').write_text(json.dumps(trial_rows, indent=2, allow_nan=False) + '\n')
                print(json.dumps({'event': 'evaluation_trial_end', 'version': args.policy_version,
                    'trial_id': current_trial['trial_id'], 'outcome': row['outcome'],
                    'reason': row['termination_reason'], 'simulation_s': row['simulation_time_ns'] / 1e9,
                    'commands': row['executed_commands'], 'wall_s': row['wall_time_s']}), flush=True)
            if error and ('RGB' in error or 'observer lost' in error or 'CUDA' in error):
                for pending in evaluation['trials'][index + 1:]:
                    trial_rows.append(outcome_row(pending, None, 0))
                (args.output_dir / 'trial_outcomes.json').write_text(json.dumps(trial_rows, indent=2, allow_nan=False) + '\n')
                raise RuntimeError('Infrastructure gate failed; remaining declared trials are not_run: ' + error)
        manifest.update(status='completed',outcomes=outcomes)
        if evaluation:
            import os
            import subprocess
            request_path = args.output_dir / 'result_request.json'
            request_path.write_text(json.dumps({'output': str(args.output_dir / 'results'),
                'protocol': evaluation, 'rows': trial_rows, 'cases': cases, 'source': manifest['source'],
                'policy_identity': policy_identity, 'version': args.policy_version, 'resources': resources},
                indent=2, allow_nan=False) + '\n')
            script = ('import json,sys; from qlm_bench.live.evaluation import result_bundle; '
                      'd=json.load(open(sys.argv[1])); '
                      'metrics,validation=result_bundle(**d); '
                      'json.dump({"metrics":metrics,"validation":validation},open(sys.argv[2],"w"),indent=2)')
            response_path = args.output_dir / 'result_response.json'
            cpu_env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2]))
            subprocess.run([str(args.results_python), '-c', script, str(request_path), str(response_path)],
                           env=cpu_env, check=True)
            response = json.loads(response_path.read_text())
            metrics, validation = response['metrics'], response['validation']
            manifest.update(trial_outcomes=trial_rows, metrics=metrics, result_validation=validation)
            print(json.dumps({'event': 'evaluation_complete', 'version': args.policy_version, 'metrics': metrics}), flush=True)
        code = 0
    except (Exception, KeyboardInterrupt) as error:
        manifest.update(status='failed',error_type=type(error).__name__,error=str(error))
        print(f'Live inference failed: {type(error).__name__}: {error}',file=sys.stderr)
    finally:
        if runtime is not None:
            try: runtime.close()
            except Exception as error:
                manifest.update(status='failed',close_error=str(error));code=1
        manifest['ended_unix'] = time.time()
        manifest['wall_time_s'] = manifest['ended_unix']-started
        manifest_path.write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
        events.close()
        if app is not None:
            app.app.close(exit_code=code)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
