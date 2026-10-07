"""Bounded actual PhysX/controller reset regression; never a demonstration batch."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time


def main(argv=None):
    raw = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', choices=('push_box', 'lift_basket', 'press_button'), required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--resource-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--ffmpeg', required=True)
    parser.add_argument('--cycles', type=int, default=3)
    parser.add_argument('--disable-repair', action='store_true', help='Explicit negative-control diagnostic')
    from isaaclab.app import AppLauncher
    from rambo.utils.physx import validate_rambo_visualizer_args, assert_physx_environment
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args(raw)
    validate_rambo_visualizer_args(parser, args, raw)
    if not 1 <= args.cycles <= 10:
        parser.error('Reset regression is bounded to 1..10 cycles')
    args.enable_cameras = True
    args.output_dir.mkdir(parents=True, exist_ok=False)
    profile = json.loads(args.profile.read_text())
    from qlm_bench.collection.orchestrator import source_identity
    report = dict(schema='qlm-reset-freshness-regression-v1', work_id='SIM-003',
                  task=args.task, source=source_identity(), profile=profile,
                  diagnostic_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  profile_sha256=hashlib.sha256(args.profile.read_bytes()).hexdigest(),
                  repair_enabled=not args.disable_repair, cycles=args.cycles,
                  evidence_kind='actual_runtime', publication_status='local_only',
                  status='running', checks=[], terminals=[],
                  not_run=['demonstration_collection', 'SFT_model_rollout', 'training',
                           'historical_data_repair', 'formal_benchmark', 'remote_publication'])
    path = args.output_dir / 'report.json'
    def save():
        path.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    save()
    started = time.monotonic()
    app = runtime = recorder = None
    recorder_closed = False
    code = 1
    try:
        app = AppLauncher(args)
        import numpy as np
        import torch
        import warp as wp
        from PIL import Image
        from isaaclab.utils.math import quat_apply, quat_apply_inverse
        from qlm_bench.collection.isaac import TASK_IDS
        from rambo.contracts_v2.runtime import prepare_command
        from rambo.recording_v2 import Recorder
        from rambo.recording_evaluation import create_observer
        from rambo.tasks.common.controller_runtime import ControllerRuntime
        if args.disable_repair:
            from rambo.tasks.direct.rambo_quadruped import qp_env
            qp_env.invalidate_reset_root_link_velocity = lambda _robot: None

        def attach(created):
            nonlocal recorder
            observer, _handles = create_observer(profile)
            recorder = Recorder(created.base_env, args.output_dir / 'raw' / 'diagnostic', args.ffmpeg, observer)
            created.base_env._v2_recorder = recorder
        runtime = ControllerRuntime(TASK_IDS[args.task], profile=profile,
                                    resource_root=args.resource_root, seed=42,
                                    episode_length_s=0.32, on_environment_ready=attach)
        env = runtime.base_env
        report['runtime'] = assert_physx_environment(runtime.env)
        report['controller_sha256'] = runtime.contract.sha256

        def clock():
            return [int(env._sim_step_counter), float(env._robot.data._sim_timestamp),
                    int(env.common_step_counter)]

        def check(label, snapshot, *, previous_clock=None):
            robot = env._robot
            # Direct backend readback, independent of the derived data cache.
            com = wp.to_torch(robot.root_view.get_root_velocities()).reshape(1, 6).clone()
            pose = wp.to_torch(robot.root_view.get_root_transforms()).reshape(1, 7).clone()
            offset = quat_apply(pose[:, 3:], robot.data.body_com_pos_b.torch[:, 0])
            reference = com.clone()
            reference[:, :3] -= torch.linalg.cross(com[:, 3:], offset, dim=-1)
            body_linear = quat_apply_inverse(pose[:, 3:], reference[:, :3])
            body_angular = quat_apply_inverse(pose[:, 3:], reference[:, 3:])
            state = snapshot['state']
            public = torch.tensor([state['observation.state.base.linear_velocity'] +
                                   state['observation.state.base.angular_velocity']], device=env.device)
            observations = runtime.observations.reshape(1, env.cfg.history_length, -1)[0, -1]
            expected_obs = torch.cat((body_linear, body_angular), dim=-1)[0]
            public_error = float((public - reference).abs().max().item())
            controller_error = float((observations[4:10] - expected_obs).abs().max().item())
            row = dict(label=label, snapshot={k:copy.deepcopy(snapshot[k]) for k in
                        ('simulation_time_ns', 'physics_step', 'reset_epoch', 'state', 'rgb_hashes', 'sensor_frame_ids')},
                       direct_com_twist=com[0].cpu().tolist(), reference_root_link_twist=reference[0].cpu().tolist(),
                       controller_velocity=observations[4:10].cpu().tolist(),
                       controller_reference=expected_obs.cpu().tolist(),
                       public_max_abs_error=public_error, controller_max_abs_error=controller_error,
                       global_clock=clock(), physics_not_advanced=previous_clock is None or previous_clock == clock(),
                       reset_origin=snapshot['physics_step'] == 0 and snapshot['simulation_time_ns'] == 0,
                       direct_reset_velocity_max_abs=float(com.abs().max().item()), rgb={})
            for role, pixels in snapshot['rgb'].items():
                values = np.asarray(pixels)[:, :, :3]
                metrics = dict(std=float(values.std()), distinct_scalar_values=int(np.unique(values).size),
                               sha256=hashlib.sha256(values.tobytes()).hexdigest())
                metrics['scene_valid'] = metrics['std'] > 3 and metrics['distinct_scalar_values'] > 16
                row['rgb'][role] = metrics
                if label in ('startup', 'manual-0', 'automatic-0'):
                    Image.fromarray(values).save(args.output_dir / f'{label}-{role}.png')
            row['passed'] = public_error < 1e-5 and controller_error < 1e-5 and \
                row['direct_reset_velocity_max_abs'] < 1e-5 and row['reset_origin'] and \
                row['physics_not_advanced'] and all(m['scene_valid'] for m in row['rgb'].values())
            report['checks'].append(row)
            save()
            print(json.dumps({'reset_check': label, 'passed': row['passed'],
                              'public_error': public_error, 'controller_error': controller_error}), flush=True)

        def execute(count, prefix):
            terminal = None
            for index in range(count):
                request, expert = runtime.expert_command()
                prepared = prepare_command(request, f'{prefix}:{index}', env.episode_tick)
                prepared['extensions']['expert'] = expert
                if recorder.active:
                    recorder.submit(prepared)
                result = runtime.step(prepared)
                if result['terminal'] is not None:
                    terminal = result['terminal']
                    break
                if recorder.active:
                    # The collector owns the 50 Hz boundary capture; the fixed
                    # controller only records physics/control and the terminal.
                    recorder.capture_boundary()
            return terminal

        with torch.inference_mode():
            check('startup', runtime.state())
            for cycle in range(args.cycles):
                if execute(4, f'pre-reset-{cycle}') is not None:
                    raise ValueError('Unexpected terminal before the manual reset')
                dirty = runtime.state()
                before = clock()
                check(f'manual-{cycle}', runtime.reset(), previous_clock=before)
                report['checks'][-1]['previous_velocity'] = dirty['state']['observation.state.base.linear_velocity'] + \
                    dirty['state']['observation.state.base.angular_velocity']
                if cycle == 0:
                    recorder.begin()
                    recorded = recorder.boundaries[0]['state']
                    public = report['checks'][-1]['snapshot']['state']
                    # PhysX forward kinematics can round the reset pose by a few
                    # float32 ulps without stepping; compare physical values.
                    report['recorder_initial_field_errors'] = {
                        key: float(np.max(np.abs(np.asarray(recorded[key], dtype=float) -
                                                 np.asarray(public[key], dtype=float))))
                        for key in public}
                    report['recorder_initial_matches_public'] = set(recorded) == set(public) and \
                        all(error < 1e-5 for error in report['recorder_initial_field_errors'].values())
                terminal = execute(16, f'timeout-{cycle}')
                if terminal is None:
                    raise ValueError('Bounded episode did not reach its declared terminal')
                owned = {k:copy.deepcopy(terminal[k]) for k in
                         ('simulation_time_ns', 'physics_step', 'reset_epoch', 'state', 'rgb_hashes', 'reason')}
                report['terminals'].append(owned)
                check(f'automatic-{cycle}', runtime.state())
                if cycle == 0:
                    report['terminal_before_reset'] = recorder.terminal['state'] == terminal['state'] and \
                        recorder.terminal['rgb_hashes'] == terminal['rgb_hashes']
                    recorder.close(dict(work_id='SIM-003', scenario='reset-freshness-diagnostic',
                        mode='diagnostic', diagnostic_only=True, profile=profile,
                        implementation=report['source'], checkpoint_sha256=runtime.contract.sha256,
                        source_commit=report['source']['source_commit'],
                        status='success' if terminal['success'] else 'failure',
                        task_text=profile.get('task_text', 'Push the box into the target area.'),
                        initial_geometry=copy.deepcopy(recorder.boundaries[0]['task_review']),
                        post_reset_state=runtime.state()['state']))
                    recorder_closed = True
                    env._v2_recorder = None
                    report['recorded_commands'] = len(recorder.commands)
                    report['recorded_boundaries'] = len(recorder.boundaries)
                if env.episode_tick != 0 or runtime.state()['reset_epoch'] <= terminal['reset_epoch']:
                    raise ValueError('Terminal was not owned before a new reset epoch')
        report['passed'] = all(row['passed'] for row in report['checks']) and \
            report['recorder_initial_matches_public'] and report['terminal_before_reset'] and \
            report['recorded_boundaries'] == report['recorded_commands'] + 1
        report['status'] = 'passed' if report['passed'] else 'failed'
        code = 0 if report['passed'] else 1
    except Exception as error:
        report.update(status='error', passed=False, error={'type': type(error).__name__, 'message': str(error)})
        import traceback
        traceback.print_exc()
    finally:
        if recorder is not None and not recorder_closed:
            recorder.close(dict(work_id='SIM-003', diagnostic_only=True, invalid=True))
        if runtime is not None:
            runtime.close()
        report['wall_seconds'] = time.monotonic() - started
        save()
        if report.get('passed'):
            (args.output_dir / 'raw' / 'diagnostic' / 'summary.json').write_text(
                json.dumps({'passed': True, 'terminal_before_reset': report['terminal_before_reset'],
                            'diagnostic_only': True, 'work_id': 'SIM-003',
                            'source_report': str(path.resolve()),
                            'source_report_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}, indent=2) + '\n')
        if app is not None:
            app.app.close()
    return code


if __name__ == '__main__':
    raise SystemExit(main())
