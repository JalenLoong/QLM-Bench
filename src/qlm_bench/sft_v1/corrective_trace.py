"""Physical traces of corrective takeover segments for the existing offline state-replay recorder (sft-v1/QLM-DATA-001).

The production chain records a ``qlm-physical-trace-v1`` trace first and renders it afterwards in a separate process
(``backends/mujoco/trace.collect_trace`` -> ``scripts/mujoco/synthesis/render_trace.py``). ``collect_trace`` always starts
from a reset. A corrective segment (design 4.4 of task-specific-sft-design-20261110) starts at a takeover boundary of the
student's own rollout, so this module writes the same trace format from a restored RL-v3 own state:

* restore the own state into the trace-only NativeCPU runtime of ``sft_v1.takeover`` (the path the takeover itself used);
* replay, open loop, the native9 commands the frozen recovery routine requested during the accepted takeover, with the
  recorder hooks of ``collect_trace`` attached (one boundary per command, 500 Hz physics rows, 100 Hz controller rows);
* require every privileged row of the replay to equal the takeover record bit for bit, and the same success terminal;
* write the trace on the **episode clock**: every tick and timestamp is re-based so the takeover boundary is tick 0 (the
  dataset contract has one clock that is 0 at the first frame). The absolute takeover tick, the own-state hash and the
  source rollout are recorded in ``scene.takeover`` and ``batch_identity.corrective``; ``render_snapshots.npz`` keeps the
  absolute tick of every boundary in ``absolute_physics_step`` and MuJoCo's own ``time`` untouched.

Nothing under the folders hashed by ``execution_source_identity`` is changed; ``verify_trace`` of the production chain is
run on the result unchanged.
"""
import copy
import gzip
import importlib.metadata
import json
from pathlib import Path
import shutil
import time

import numpy as np

SCHEMA = 'qlm-sft-v1-corrective-trace-v1'
WORK_ID = 'sft-v1/QLM-DATA-001'
# The contact evidence is recorded as in the evidence-review traces (the only non-legacy policy the production audit
# knows); eligibility is not a pending human review but the corrective acceptance rule below.
QUALITY_POLICY = 'evidence-review-v1'
ELIGIBILITY = 'corrective_takeover_accepted'
ACCEPTANCE = 'sft-v1-corrective-takeover-v1: frozen recovery routine, task_success terminal, no fall, within the case horizon'
TICK_NS = 2_000_000


def implementation_identity():
    """The file inventory ``collect_trace`` records (src/qlm_bench and scripts/mujoco/synthesis), plus scripts/sft_v1."""
    from qlm_bench.backends.mujoco.trace import sha
    root = Path(__file__).resolve().parents[3]
    return {str(p.relative_to(root)): sha(p) for folder in ('src/qlm_bench', 'scripts/mujoco/synthesis', 'scripts/sft_v1')
            for p in sorted((root / folder).rglob('*')) if p.suffix in ('.py', '.json')}


def record_segment(cache, segment, takeover_stem, output, *, batch_identity, uid):
    """Replay one accepted takeover from its own state and write ``output`` as a qlm-physical-trace-v1 directory.

    ``segment`` is one entry of takeover/segments.json, ``takeover_stem`` the path of its takeover result without suffix.
    """
    from qlm_bench.backends.mujoco.rl_v2 import snapshot as snap
    from qlm_bench.backends.mujoco.trace import SNAPSHOT_ARRAYS, sha, verify_trace, write_json
    from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
    from qlm_bench.rl_v3 import own_state, privileged
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    takeover_stem = Path(takeover_stem)
    summary = json.loads(takeover_stem.with_suffix('.json').read_text())
    npz = takeover_stem.with_suffix('.npz')
    if sha(npz) != summary['arrays_sha256']:
        raise ValueError('Takeover arrays differ from their summary')
    outcome = summary['outcome']
    accepted = (outcome['success'] and not outcome['fallen'] and outcome['terminal']['reason'] == 'task_success'
                and outcome['end_s'] <= outcome['horizon_s'])
    if not accepted or summary['expert']['kind'] != 'recovery' or summary['start']['state_sha256'] != segment['state_sha256']:
        raise ValueError('Only accepted recovery takeovers of the declared own state are recorded')
    with np.load(npz) as z:
        requested, executed, phases = z['requested'].copy(), z['executed'].copy(), z['phase'].copy()
        contact_points, base_velocity, reference_rows = z['commanded_contact_point'].copy(), z['commanded_world_base_velocity'].copy(), z['privileged'].copy()
    n = len(requested)
    if n != outcome['commands'] or len(reference_rows) != n + 1 or not np.array_equal(requested, executed):
        raise ValueError('Takeover record is incomplete')

    started = time.monotonic()
    rt, case, binding = cache.get(segment['case'], summary['model'])
    stored, record = own_state.load(Path(segment['state']), binding_sha256=binding)
    if record['snapshot_sha256'] != segment['state_sha256'] or record['absolute_tick'] != segment['takeover_tick']:
        raise ValueError('Own state differs from the takeover point record')
    boundaries, snapshots, physics, controls, contacts, commands = [], [], [], [], [], []

    def boundary(packet):
        state = copy.deepcopy(packet['state'])
        fl = state.get('task.contact.fl_object', [None])[0]
        body = state.get('task.contact.body_object', [None])[0]
        known = isinstance(fl, (bool, np.bool_)) and isinstance(body, (bool, np.bool_))
        boundaries.append({'simulation_time_ns': packet['simulation_time_ns'], 'physics_step': packet['physics_step'], 'state': state,
                           'contact': {'status': 'measured' if known else 'unknown', 'valid': known,
                                       'fl_object': bool(fl) if known else None, 'body_object': bool(body) if known else None},
                           'task_review': {'source': 'captured_physical_state', 'recording_mode': 'offline_state_replay'}})
        snapshots.append(copy.deepcopy(packet['physical_snapshot']))

    def physics_row(runtime, efforts):
        state = runtime.state_channels();tick = int(runtime.physics.ticks[0]);ns = tick * TICK_NS
        physics.append(dict(timestamp_ns=ns, physics_step=tick,
                            base_pose=state['observation.state.base.position'] + state['observation.state.base.orientation'],
                            base_twist=state['observation.state.base.linear_velocity'] + state['observation.state.base.angular_velocity'],
                            joint_position=state['observation.state.joint_position'], joint_velocity=state['observation.state.joint_velocity'],
                            joint_torque=np.asarray(efforts[0], np.float32).tolist(),
                            object_pose=state['task.object.position'] + state['task.object.orientation'],
                            object_velocity=state['task.object.linear_velocity'] + state['task.object.angular_velocity'],
                            external_force=[0., 0., 0.], external_torque=[0., 0., 0.], external_wrench_frame='world'))
        contacts.append(dict(measurement_timestamp_ns=ns, sensor_sequence_index=len(contacts),
                             force=state['observation.state.fl_contact_force'], torque=None, frame='world', force_kind='net_normal', valid=True))

    def control_row(runtime, residual):
        tick = int(runtime.physics.ticks[0])
        controls.append(dict(timestamp_ns=tick * TICK_NS, controller_tick=tick // 5,
                             high_level_command=runtime.current['filtered'], policy_residual=residual[0].cpu().tolist(),
                             reference_state=runtime.core._desired_joint_pos[0].cpu().tolist(),
                             residual_observation_command_id=runtime.controller_reference_command_id,
                             fl_ik_command_id=runtime.controller_reference_command_id, fl_ik_computed_tick=runtime.controller_reference_tick,
                             desired_joint_target=runtime.core.desired_pos[0].cpu().tolist(),
                             desired_joint_velocity=runtime.core.desired_vel[0].cpu().tolist(), desired_joint_torque=runtime.core.desired_tor[0].cpu().tolist(),
                             controller_mode='retained_quadruped_rambo', safety_flags=0))

    rows = []
    try:
        rt.on_observation = boundary
        snap.restore(rt, stored)
        t0 = int(rt.physics.ticks[0])
        if t0 != segment['takeover_tick'] or len(boundaries) != 1 or boundaries[0]['physics_step'] != t0:
            raise RuntimeError('Restore did not produce the takeover boundary')
        previous_reference = (rt.controller_reference_command_id, int(rt.controller_reference_tick))
        rt.on_physics = physics_row;rt.on_control = control_row
        physics_row(rt, np.zeros((1, 12), np.float32))
        rows.append(privileged.row(rt))
        for i in range(n):
            tick = int(rt.physics.ticks[0])
            result = rt.step(prepare_command(requested[i].tolist(), f'{uid}:{i}', tick))
            if not result['completed_interval']:
                raise RuntimeError('Replay left a partial command interval')
            command = copy.deepcopy(result['command'])
            command['extensions']['expert'] = {
                'phase': str(phases[i]), 'commanded_contact_point': [float(x) for x in contact_points[i]],
                'commanded_world_base_velocity': [float(x) for x in base_velocity[i]],
                'routine': summary['expert']['recovery_params']['version'], 'source': 'replayed accepted takeover command'}
            commands.append(command)
            reason = None if result['terminal'] is None else result['terminal']['reason']
            rows.append(privileged.row(rt, completed=command['status'] == 'completed', terminal_reason=reason))
            if (result['terminal'] is not None) != (i == n - 1):
                raise RuntimeError('Replay terminal does not coincide with the takeover record')
        rows = np.asarray(rows, np.float64)
        if not np.array_equal(rows, reference_rows):
            raise RuntimeError('Replay differs from the takeover record')
        terminal = rt.terminal
        if not (terminal and rt.outcome['success'] and not rt.outcome['fallen'] and terminal['reason'] == 'task_success'
                and not terminal['partial_interval'] and len(boundaries) == n + 1 and int(rt.physics.ticks[0]) == outcome['end_tick']):
            raise RuntimeError('Replay did not end in the recorded success terminal')
        rt.physics.assert_frozen_model(full=True)
        elapsed = time.monotonic() - started

        # ---- episode clock: the takeover boundary is tick 0 everywhere below.
        def shifted(tick):
            value = int(tick) - t0
            if value < 0:
                raise RuntimeError('Tick before the takeover boundary in the segment')
            return value
        own_ids = {c['command_id'] for c in commands}
        for b in boundaries:
            b['physics_step'] = shifted(b['physics_step']);b['simulation_time_ns'] = b['physics_step'] * TICK_NS
        for row in physics:
            row['physics_step'] = shifted(row['physics_step']);row['timestamp_ns'] = row['physics_step'] * TICK_NS
        for row in contacts:
            row['measurement_timestamp_ns'] = shifted(row['measurement_timestamp_ns'] // TICK_NS) * TICK_NS
        for row in controls:
            tick = shifted(row['timestamp_ns'] // TICK_NS)
            row.update(timestamp_ns=tick * TICK_NS, controller_tick=tick // 5, fl_ik_computed_tick=shifted(row['fl_ik_computed_tick']))
            for key in ('residual_observation_command_id', 'fl_ik_command_id'):
                # Before the first command of the segment completes, the controller reference is the student's last command;
                # as in a trace from reset there is no command of this episode yet (it is kept in scene.takeover).
                if row[key] not in own_ids:
                    row[key] = None
        for c in commands:
            for key in ('start_tick', 'end_tick', 'executed_until_tick'):
                c[key] = shifted(c[key])
        absolute = np.asarray([s['physics_step'] for s in snapshots], np.int64)
        terminal_record = {k: copy.deepcopy(v) for k, v in terminal.items() if k != 'physical_snapshot'}
        terminal_record.update(physics_step=shifted(terminal_record['physics_step']))
        terminal_record['simulation_time_ns'] = terminal_record['physics_step'] * TICK_NS
        terminal_record['executed_history'] = [copy.deepcopy(c) for c in commands]
        confirmation = terminal_record['command_confirmation']
        for key in ('start_tick', 'end_tick', 'executed_until_tick'):
            confirmation[key] = shifted(confirmation[key])
        terminal_record['absolute_physics_step'] = int(absolute[-1])

        quality = {'fl_contact_boundaries': sum(bool(b['contact']['fl_object']) for b in boundaries),
                   'body_contact_boundaries': sum(bool(b['contact']['body_object']) for b in boundaries)}
        partial = output.with_name(output.name + '.writing')
        if partial.exists():
            shutil.rmtree(partial)
        partial.mkdir(parents=True)
        arrays = {k: np.stack([s[k] for s in snapshots]) for k in SNAPSHOT_ARRAYS}
        arrays.update(time=np.asarray([s['time'] for s in snapshots]), physics_step=absolute - t0,
                      simulation_time_ns=(absolute - t0) * TICK_NS, absolute_physics_step=absolute)
        np.savez_compressed(partial / 'render_snapshots.npz', **arrays)
        with gzip.open(partial / 'telemetry.json.gz', 'wt') as f:
            json.dump({'boundaries': boundaries, 'controller': controls, 'physics': physics, 'contact_sensor': contacts}, f, allow_nan=False)
        with (partial / 'commands.jsonl').open('w') as f:
            for c in commands:
                f.write(json.dumps(c, allow_nan=False) + '\n')
        write_json(partial / 'terminal.json', terminal_record)
        profile = copy.deepcopy(rt.profile)
        takeover = {'schema': SCHEMA, 'segment_id': segment['segment_id'], 'source_case_id': segment['case_id'], 'point': segment['point'],
                    'absolute_tick': t0, 'absolute_simulation_time_ns': t0 * TICK_NS, 'episode_clock': 'tick 0 is the takeover boundary',
                    'own_state': segment['state'], 'own_state_sha256': segment['state_sha256'], 'own_state_origin': record['origin'],
                    'at_takeover': segment['at_takeover'], 'takeover_result': str(takeover_stem.with_suffix('.json')),
                    'takeover_result_sha256': sha(takeover_stem.with_suffix('.json')), 'takeover_arrays_sha256': summary['arrays_sha256'],
                    'replay': 'open loop from the own state; privileged rows equal the takeover record bit for bit',
                    'controller_reference_before_takeover': {'command_id': previous_reference[0], 'absolute_tick': previous_reference[1]},
                    'absolute_end_tick': int(absolute[-1]), 'horizon_s': float(rt.profile['horizon_s'])}
        scene = {'candidate_id': uid, 'seed': case.seed, 'case_id': case.case_id, 'case': str(Path(segment['case']).resolve()),
                 'case_sha256': binding, 'model': str(summary['model']), 'split': 'train', 'difficulty': segment['difficulty'],
                 'goal_x': profile['goal_x'], 'goal_y': profile['goal_y'], 'canonical_goal_position': profile['canonical_goal_position'],
                 'initial_state': {'source': 'rl-v3 own state at the takeover boundary', 'sha256': segment['state_sha256']}, 'takeover': takeover}
        identity = {**copy.deepcopy(batch_identity), 'implementation': implementation_identity()}
        environment = {}
        for name in ('mujoco', 'mujoco-warp', 'warp-lang', 'torch', 'qpth', 'numpy', 'av'):
            try:
                environment[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                environment[name] = None
        import resource
        manifest = {'schema': 'qlm-physical-trace-v1', 'passed': True, 'scene': scene, 'batch_identity': identity, 'reference': False,
                    'profile': profile, 'n_actions': n, 'n_boundaries': len(boundaries), 'model_identity': rt.physics.model_identity,
                    'model_parameters_identity': rt.physics.model_parameters_identity,
                    'world_id': snapshots[0]['world_id'], 'reset_epoch': snapshots[0]['reset_epoch'],
                    'quality': quality, 'quality_policy': QUALITY_POLICY, 'demonstration_eligibility': ELIGIBILITY,
                    'acceptance_policy': ACCEPTANCE, 'physical_success': True,
                    'telemetry_purpose': 'required_existing_Raw_streams_and_explicit_reference_diagnostics',
                    'terminal_before_reset': True, 'renderer_created': False, 'renderer_calls': 0,
                    'backend': {'physics': rt.physics.backend, 'controller': 'original model_2000', 'controller_device': str(rt.core.device),
                                'resources': rt.physics.resource_profile, 'asset_profile': copy.deepcopy(rt.profile),
                                'model_parameters_identity': rt.physics.model_parameters_identity,
                                'effective_physics_options': rt.physics.backend_options, 'case_seed': case.seed,
                                'random_streams': rt.core.case_rng.identity(), 'motor_lags_physics_ticks': rt.core.motor.lags.cpu().tolist(),
                                'environment': environment},
                    'performance': {'physics_capture_wall_s': elapsed, 'trace_write_s': time.monotonic() - started - elapsed,
                                    'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024, 'peak_torch_vram_bytes': 0},
                    'files': {p.name: sha(p) for p in partial.iterdir() if p.is_file()}}
        if len({s['reset_epoch'] for s in snapshots}) != 1:
            raise RuntimeError('Segment spans more than one runtime epoch')
        write_json(partial / 'manifest.json', manifest)
        verify_trace(partial)
        partial.rename(output)
        return {'passed': True, 'uid': uid, 'trace': str(output), 'trace_sha256': sha(output / 'manifest.json'), 'n_actions': n,
                'takeover_tick': t0, 'end_tick': int(absolute[-1]), 'quality': quality, 'wall_s': time.monotonic() - started}
    finally:
        rt.on_physics = None;rt.on_control = None;rt.on_observation = None
