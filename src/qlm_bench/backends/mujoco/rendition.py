"""Ten-slot render-only recovery of immutable successful physical trajectories."""
import copy
import fcntl
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import time

import numpy as np

from .trace import verify_trace, sha, write_json
from .template import quat_matrix
from .resources import resource_closure
from qlm_bench.compatibility.dataset_v2.pilot_rendition import load_profile, slot_for, validate_formal_pilot
from qlm_bench.compatibility.dataset_v2.validation import digest, validate_raw, COLUMNS
from qlm_bench.compatibility.dataset_v2.media import MediaTools


class RecordingIntegrityError(ValueError):
    """Identity/integrity errors must not be retried as temporary encoder failures."""


def audit_trace(path):
    m, arrays, telemetry, commands, terminal = verify_trace(path)
    from .remaining_tasks import TASKS
    if m['profile']['task_id'] in TASKS:
        from .remaining_tasks import audit_remaining_trace
        return audit_remaining_trace(path)
    task_id = m['profile']['task_id']
    if task_id not in ('push_box', 'press_button', 'lift_basket', 'kick_ball_to_goal') or not m['terminal_before_reset']:
        raise RecordingIntegrityError('Expected supported successful pre-reset task trace')
    contact = [b['contact'] for b in telemetry['boundaries']]
    policy = m.get('quality_policy', 'legacy-fl-contact-v1')
    from .quality import contact_evidence
    evidence = contact_evidence(telemetry['boundaries'])
    quality = {k: evidence[k] for k in ('fl_contact_boundaries', 'body_contact_boundaries')}
    if quality != m['quality']:
        raise RecordingIntegrityError('Captured contact evidence differs from manifest')
    if policy == 'legacy-fl-contact-v1':
        if evidence['status'] != 'measured' or quality['fl_contact_boundaries'] < 1 or quality['body_contact_boundaries']:
            raise RecordingIntegrityError('Legacy FL-only demonstration quality mismatch')
    elif policy != 'evidence-review-v1':
        raise RecordingIntegrityError('Unknown quality policy')
    if task_id == 'push_box':
        bounds = m['profile']['bounds_local']
        local = np.asarray(list(itertools.product(*zip(*bounds))))
    elif task_id == 'press_button':
        if m['profile']['threshold_m'] != .012 or m['profile']['success_hold_commands'] != 3:
            raise RecordingIntegrityError('Frozen Press displacement/hold contract differs')
    elif task_id == 'kick_ball_to_goal':
        from .kick_goal import GoalEntry
        if m['profile']['success_hold_commands'] != 3 or m['profile']['ball_radius_m'] != .1:
            raise RecordingIntegrityError('Frozen Kick whole-ball/hold contract differs')
        entry = GoalEntry(m['profile']['goal_geometry'], m['profile']['ball_radius_m'])
        boundaries = telemetry['boundaries']
        entry.reset(boundaries[0]['state']['task.object.position'])
        goal_conditions = [False] + [entry.update(i * 10, b['state']['task.object.position'])
                                     for i, b in enumerate(boundaries[1:], start=1)]
    else:
        if m['profile']['minimum_clearance_m'] != .02 or m['profile']['success_hold_commands'] != 3 or m['profile']['floor_z_m'] != 0. or m['profile'].get('success_enable_after_s',2.1)!=2.1:
            raise RecordingIntegrityError('Frozen Lift whole-geometry clearance/hold contract differs')
        local = np.asarray(m['profile']['support_vertices_local'],dtype=float)
        if local.ndim != 2 or local.shape[1] != 3 or len(local)<4 or not np.isfinite(local).all():
            raise RecordingIntegrityError('Complete Lift geometry support required')
    hold = []
    for last_index,b in enumerate(telemetry['boundaries'][-3:]):
        s = b['state']
        if task_id == 'push_box':
            corners = local @ quat_matrix(s['task.object.orientation']).T + s['task.object.position']
            x, y = m['profile']['goal_x'], m['profile']['goal_y']
            inside = bool(np.all(corners[:, 0] >= x[0]) and np.all(corners[:, 0] <= x[1]) and
                          np.all(corners[:, 1] >= y[0]) and np.all(corners[:, 1] <= y[1]))
        elif task_id == 'press_button':
            inside = bool(s['task.progress'][0] >= m['profile']['threshold_m'])
        elif task_id == 'kick_ball_to_goal':
            inside = goal_conditions[len(goal_conditions)-3+last_index]
        else:
            corners = local @ quat_matrix(s['task.object.orientation']).T + s['task.object.position']
            actual = float(corners[:,2].min()-m['profile']['floor_z_m'])
            if abs(actual-s['task.progress'][0])>2e-6:
                raise RecordingIntegrityError('Lift progress differs from full geometry')
            from qlm_bench.tasks.predicates import physical_condition
            inside,_ = physical_condition('lift_basket',m['profile'],corners_world=corners,
                time_s=float(arrays['simulation_time_ns'][-3+last_index])*1e-9)
        not_fallen = bool(s['observation.state.base.position'][2] >= .1 and
                         np.linalg.norm(np.asarray(s['observation.state.projected_gravity']) - [0, 0, -1]) <= .75)
        hold.append(inside and not_fallen)
    predicate = {'push_box':'full_footprint_three_ticks','press_button':'button_displacement_three_ticks',
                 'lift_basket':'whole_basket_clearance_three_ticks', 'kick_ball_to_goal':'front_whole_ball_goal_three_ticks'}[task_id]
    consecutive = len(hold) == 3 and np.array_equal(np.diff(arrays['simulation_time_ns'][-3:]), [20_000_000, 20_000_000])
    quality.update({predicate: bool(all(hold) and consecutive), 'not_fallen': terminal['fallen'] is False})
    if not quality[predicate] or not quality['not_fallen'] or terminal.get('success') is not True:
        raise RecordingIntegrityError('Original task predicate/not-fallen3tick gate failed')
    h = hashlib.sha256()
    for k in ('qpos', 'qvel', 'simulation_time_ns'):
        h.update(k.encode()); h.update(arrays[k].tobytes())
    h.update(np.asarray([c['executed'] for c in commands], np.float32).tobytes())
    return {'manifest_sha256': sha(Path(path) / 'manifest.json'), 'trajectory_sha256': h.hexdigest(),
            'model_identity': m['model_identity'], 'source_identity_sha256': digest(m['batch_identity']),
            'quality': quality, 'n_actions': m['n_actions'], 'n_boundaries': m['n_boundaries'],
            'task_id': task_id, 'physical_source': copy.deepcopy(m['batch_identity']), 'scene': copy.deepcopy(m['scene'])}


def validate_slot_inputs(profile, uid):
    slot = slot_for(profile, uid)
    if profile['schema'] == 'qlm-approved-six-production-rendition-v1':
        from .remaining_production import validate_recording_inputs
        return validate_recording_inputs(profile, slot)
    actual = audit_trace(slot['trace'])
    if actual['task_id'] != profile['task_id'] or actual['task_id'] != slot['task_id']:
        raise RecordingIntegrityError('Physical task differs from frozen rendition membership')
    for a, b in [('manifest_sha256', 'trace_manifest_sha256'), ('trajectory_sha256', 'physical_trajectory_sha256'),
                 ('source_identity_sha256', 'physical_source_sha256'), ('model_identity', 'model_identity'),
                 ('quality', 'quality')]:
        if actual[a] != slot[b]:
            raise RecordingIntegrityError('Frozen trace identity/quality changed: ' + b)
    if resource_closure(slot['model'], require_portable=True)['identity'] != slot['model_identity']:
        raise RecordingIntegrityError('Frozen scene resource changed')
    if actual['task_id'] == 'press_button':
        import mujoco
        model = mujoco.MjModel.from_xml_path(slot['model'])
        joint = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'button_slide')
        if joint < 0: raise RecordingIntegrityError('Actual passive button articulation missing')
        _, arrays, telemetry, _, _ = verify_trace(slot['trace'])
        displacement = arrays['qpos'][:, int(model.jnt_qposadr[joint])]
        reported = np.asarray([b['state']['task.progress'][0] for b in telemetry['boundaries']])
        if not np.allclose(displacement, reported, rtol=0, atol=1e-8):
            raise RecordingIntegrityError('Button progress differs from actual physical articulation snapshot')
    elif actual['task_id'] == 'kick_ball_to_goal':
        import mujoco
        model = mujoco.MjModel.from_xml_path(slot['model'])
        source_profile = json.loads(Path(slot['model']).with_suffix('.task.json').read_text())
        manifest, arrays, telemetry, _, _ = verify_trace(slot['trace'])
        if any(manifest['profile'][key] != source_profile[key] for key in
               ('goal_geometry', 'ball_radius_m', 'canonical_goal_position', 'success_hold_commands')):
            raise RecordingIntegrityError('Kick goal geometry differs from actual source profile')
        adr = int(model.joint('object_free').qposadr[0])
        if not np.allclose(model.body('goal').pos, source_profile['goal_geometry']['front_center_xyz_m'], rtol=0, atol=1e-12):
            raise RecordingIntegrityError('Kick physical goal differs from declared goal')
        for i, boundary in enumerate(telemetry['boundaries']):
            state = boundary['state']
            if not np.allclose(arrays['qpos'][i, adr:adr+3], state['task.object.position'], rtol=0, atol=1e-8):
                raise RecordingIntegrityError('Kick ball pose differs from actual physical snapshot')
            if not np.allclose(state['task.goal.position'], source_profile['canonical_goal_position'], rtol=0, atol=1e-7):
                raise RecordingIntegrityError('Kick observed goal differs from actual physical goal')
    elif actual['task_id'] == 'lift_basket':
        import mujoco
        model = mujoco.MjModel.from_xml_path(slot['model'])
        source_profile=json.loads(Path(slot['model']).with_suffix('.task.json').read_text())
        _, arrays, telemetry, _, _=verify_trace(slot['trace'])
        adr=int(model.joint('object_free').qposadr[0])
        local=np.asarray(source_profile['support_vertices_local'])
        for i,b in enumerate(telemetry['boundaries']):
            position=arrays['qpos'][i,adr:adr+3]
            quaternion=arrays['qpos'][i,adr+3:adr+7][[1,2,3,0]]
            height=float((local@quat_matrix(quaternion).T+position)[:,2].min()-source_profile['floor_z_m'])
            if abs(height-b['state']['task.progress'][0])>2e-6:
                raise RecordingIntegrityError('Lift progress differs from actual complete physical snapshot')
            if not np.allclose(position,b['state']['task.object.position'],rtol=0,atol=1e-7):
                raise RecordingIntegrityError('Lift object pose differs from physical snapshot')
    source_root = Path(__file__).resolve().parents[4]
    for name, expected in profile['recording_source']['implementation'].items():
        part = Path(name)
        if part.is_absolute() or '..' in part.parts or sha(source_root / part) != expected:
            raise RecordingIntegrityError('Frozen recording source changed: ' + name)
    if sha(Path(profile['template_root']) / 'template.json') != profile['template_sha256']:
        raise RecordingIntegrityError('Original execution template changed')
    physical = actual['physical_source']
    if profile.get('quality_policy') == 'evidence-review-v1':
        from .quality import analyze_trace
        review, _ = analyze_trace(slot['trace'])
        if digest(review) != slot['quality_review_sha256']:
            raise RecordingIntegrityError('Frozen actual behavior evidence changed')
        if slot.get('behavior_review_resolution') is not None:
            resolution=slot['behavior_review_resolution']
            if resolution.get('accepted') is not True or resolution.get('trace_manifest_sha256')!=actual['manifest_sha256'] or resolution.get('quality_review_sha256')!=digest(review) or not resolution.get('evidence'):
                raise RecordingIntegrityError('Behavior review resolution mismatch')
            for evidence in resolution['evidence']:
                if sha(evidence['path'])!=evidence['sha256']:raise RecordingIntegrityError('Behavior review evidence changed')
        executor = {'press_button':'press-body-carry-v2','push_box':'cross-track-smooth-v3',
                    'lift_basket':'lift-body-lane-geometry-v2', 'kick_ball_to_goal':'kick-impulse-retract-v3-tucked-carry'}[profile['task_id']]
        if physical.get('approval_sha256') != digest(profile['approval']) or physical.get('executor_variant') != executor:
            raise RecordingIntegrityError('Physical execution lacks approved recipe/scope identity')
        press_campaign_key = 'production_campaign_sha256' if profile['schema'] in ('qlm-press-production-rendition-v1','qlm-lift-production-rendition-v1','qlm-kick-production-rendition-v1') else 'pilot_campaign_sha256'
        if profile['task_id'] in ('press_button','lift_basket','kick_ball_to_goal') and physical.get(press_campaign_key) != profile.get('campaign_sha256' if press_campaign_key=='production_campaign_sha256' else 'pilot_campaign_sha256'):
            raise RecordingIntegrityError('Physical execution differs from frozen Press pilot campaign')
        if slot.get('review_status') != ('approved_task_recipe_technical_quality' if profile['schema'] in ('qlm-push-production-rendition-v1','qlm-press-production-rendition-v1','qlm-lift-production-rendition-v1','qlm-kick-production-rendition-v1') else 'eligible_for_ten_pilot_user_review'):
            raise RecordingIntegrityError('Behavior review has not admitted this pilot')
    if physical.get('template_sha256') != profile['template_sha256'] or physical.get('template_id') != profile['template_id']:
        raise RecordingIntegrityError('Physical execution did not use the declared unchanged recipe')
    return actual


def validate_output(output, *, profile_path, tools, check_media=True):
    """Validate actual payloads and compare numerical training rows to source trace."""
    output = Path(output); profile = load_profile(profile_path)
    producer = json.loads((output / 'producer.json').read_text())
    slot = slot_for(profile, producer['episode_uid'])
    actual = validate_slot_inputs(profile, slot['episode_uid'])
    result = json.loads((output / 'result.json').read_text())
    if result.get('passed') is not True or producer.get('passed') is not True or \
            result.get('physics_reexecuted') is not False or result.get('controller_loaded') or result.get('WAM_loaded') or \
            result.get('physics_owner_loaded'):
        raise RecordingIntegrityError('Incomplete/invalid render-only producer')
    canonical = validate_formal_pilot(output / 'canonical', profile_path=profile_path, tools=tools, check_media=check_media)
    raw = validate_raw(output / 'raw' / slot['episode_uid'], tools=tools, check_media=check_media)
    raw_prov = json.loads((output / 'raw' / slot['episode_uid'] / 'metadata/provenance.json').read_text())
    canon_prov = json.loads((output / 'canonical/metadata/provenance.json').read_text())
    if raw_prov != canon_prov:
        raise RecordingIntegrityError('Raw/Canonical lineage differs')
    _, _, telemetry, commands, terminal = verify_trace(slot['trace'])
    import pyarrow.parquet as pq
    table = pq.read_table(output / 'canonical/data/chunk-000/episode_000000.parquet')
    np.testing.assert_array_equal(np.asarray(table['action'].to_pylist(), np.float32),
                                  np.asarray([c['executed'] for c in commands], np.float32))
    for key, spec in COLUMNS.items():
        if not key.startswith(('observation.state.', 'task.')): continue
        expected = np.asarray([b['state'][key] for b in telemetry['boundaries'][:-1]], dtype=spec['dtype'])
        observed = np.asarray(table[key].to_pylist(), dtype=spec['dtype']).reshape(expected.shape)
        np.testing.assert_array_equal(observed, expected, err_msg='Original physical state altered: ' + key)
    contract = json.loads((output / 'canonical/meta/contract.json').read_text())
    if contract['episodes'][0]['terminal']['state'] != terminal['state']:
        raise RecordingIntegrityError('Original terminal state changed')
    report = {'passed': True, 'episode_uid': slot['episode_uid'], 'rendition_id': slot['rendition_id'],
              'physical_demo_count': 1, 'trace': actual, 'raw': raw, 'canonical': canonical,
              'original_numerical_states_actions_terminal_preserved': True}
    # Preserve source identity in provenance, not a large repeated copy in acceptance.
    report['trace'] = {k: v for k, v in actual.items() if k not in ('physical_source', 'scene')}
    return report


class RenditionQueue:
    """No physical runner exists here: every slot is bound to a retained trace."""
    def __init__(self, root, profile_path, *, validator=None):
        self.root = Path(root); self.profile_path = Path(profile_path)
        self.profile = load_profile(profile_path)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / 'recording-queue.json'
        self.tools = MediaTools(self.profile['ffmpeg'], self.profile['ffprobe'])
        self.validator = validator or (lambda output: validate_output(output, profile_path=self.profile_path, tools=self.tools))
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
            if self.state['profile_sha256'] != self.profile['profile_sha256']:
                raise RecordingIntegrityError('Recording queue/profile conflict')
        else:
            self.state = {'schema': 'qlm-render-only-pilot-queue-v1', 'profile_sha256': self.profile['profile_sha256'],
                          'physical_executions': 0, 'slots': {s['episode_uid']: {'status': 'render_pending',
                          'render_attempts': 0, 'physical_trajectory_sha256': s['physical_trajectory_sha256']}
                          for s in self.profile['slots']}}
            self.save()

    def __enter__(self):
        self.lock = (self.root / 'recording-queue.lock').open('a')
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB); return self

    def __exit__(self, *_):
        fcntl.flock(self.lock, fcntl.LOCK_UN); self.lock.close()

    def save(self): write_json(self.path, self.state)

    def event(self, uid, event, **data):
        with (self.root / 'recording-attempts.jsonl').open('a') as f:
            f.write(json.dumps({'episode_uid': uid, 'event': event, **data}, allow_nan=False) + '\n'); f.flush()

    def accepted(self): return sum(s['status'] == 'accepted' for s in self.state['slots'].values())

    def run(self, worker, *, uids=None):
        selected = set(uids) if uids is not None else {s['episode_uid'] for s in self.profile['slots']}
        if not selected <= set(self.state['slots']): raise ValueError('Unknown recording slot')
        for slot in self.profile['slots']:
            uid = slot['episode_uid']
            if uid not in selected: continue
            validate_slot_inputs(self.profile, uid)
            row = self.state['slots'][uid]; output = self.root / 'episodes' / uid
            # Re-read real bytes even for previously accepted outputs. A stale counter is not data.
            if output.exists():
                try:
                    accepted = self.validator(output)
                    if accepted.get('episode_uid')!=uid:raise RecordingIntegrityError('Recording validator returned another slot')
                    row.update(status='accepted', acceptance=accepted); self.save(); continue
                except RecordingIntegrityError: raise
                except (OSError, ValueError, AssertionError) as error:
                    self.event(uid, 'output_incomplete', reason=str(error))
                    # Preserve failed render staging for this bounded phase, never touch a source trace.
                    dest = self.root / 'incomplete-recordings' / uid / f"attempt-{row['render_attempts']:03d}"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if dest.exists(): raise RecordingIntegrityError('Conflicting incomplete staging')
                    output.rename(dest)
            row['status'] = 'render_pending'; self.save()
            while row['status'] != 'accepted':
                if row['render_attempts'] >= self.profile['maximum_render_attempts']:
                    raise RuntimeError('Render retry budget exhausted; original trace retained')
                row.update(status='rendering', render_attempts=row['render_attempts'] + 1); self.save()
                self.event(uid, 'rendering', attempt=row['render_attempts'], physical_execution=False)
                try:
                    worker(slot, output, row['render_attempts'])
                    row['status'] = 'validating'; self.save()
                    accepted = self.validator(output)
                    if accepted.get('episode_uid')!=uid:raise RecordingIntegrityError('Recording validator returned another slot')
                    row.update(status='accepted', acceptance=accepted); self.save()
                    self.event(uid, 'accepted', rendition_id=slot['rendition_id'], physical_demo_count=1)
                except RecordingIntegrityError: raise
                except Exception as error:
                    row['status'] = 'render_pending'; self.save()
                    self.event(uid, 'render_failed', attempt=row['render_attempts'], reason=str(error))
                    if output.exists():
                        dest = self.root / 'incomplete-recordings' / uid / f"attempt-{row['render_attempts']:03d}"
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        if dest.exists(): raise RecordingIntegrityError('Conflicting render staging')
                        output.rename(dest)
            print(f'Recording accepted {uid}; unique physical demos {self.accepted()}/{len(self.profile["slots"])}', flush=True)
