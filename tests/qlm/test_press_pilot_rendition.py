"""Press admission must retain its own predicate and bounded pilot identity."""
import copy
import json
import numpy as np
import pytest

from qlm_bench.backends.mujoco import rendition
from qlm_bench.compatibility.dataset_v2.pilot_rendition import load_profile, PRESS_SCHEMA, SCHEMA
from qlm_bench.compatibility.dataset_v2.validation import digest


def save_profile(tmp_path, task='press_button', schema=PRESS_SCHEMA):
    profile = {'schema': schema, 'task_id': task, 'rgb_profile': 'dual-rgb-360p-v1',
        'pilot_campaign_sha256': 'frozen-campaign', 'pilot_target': 10,
        'maximum_render_attempts': 3, 'quality_policy': 'evidence-review-v1',
        'approval': {'reference_quality_approved': True, 'retarget_scope_approved': True, 'evidence_sha256': 'review'},
        'slots': [{'episode_uid': 'press-01', 'rendition_id': 'press-01@360p',
            'physical_trajectory_sha256': 'actual-trajectory', 'difficulty': 'clean', 'split': 'train',
            'task_id': task, 'appearance_preset': 'ap_00', 'quality_review_sha256': 'actual-behavior',
            'review_status': 'eligible_for_ten_pilot_user_review'}]}
    profile['profile_sha256'] = digest(profile)
    path = tmp_path / 'profile.json'; path.write_text(json.dumps(profile))
    return path


def test_press_slot_requires_approved_ten_pilot_campaign(tmp_path):
    path = save_profile(tmp_path); profile = load_profile(path)
    profile.pop('profile_sha256'); profile.pop('pilot_campaign_sha256')
    profile['profile_sha256'] = digest(profile); path.write_text(json.dumps(profile))
    with pytest.raises(ValueError, match='ten-slot'): load_profile(path)


@pytest.mark.parametrize('task,schema', [('push_box', PRESS_SCHEMA), ('press_button', SCHEMA), ('open_door', PRESS_SCHEMA)])
def test_task_schema_cannot_relabel_existing_or_unqualified_task(tmp_path, task, schema):
    with pytest.raises(ValueError, match='membership'): load_profile(save_profile(tmp_path, task, schema))


def trace_fixture(tmp_path, monkeypatch, progress=(.0121, .013, .014)):
    (tmp_path / 'manifest.json').write_text('{}')
    m = {'profile': {'task_id': 'press_button', 'threshold_m': .012, 'success_hold_commands': 3},
        'terminal_before_reset': True, 'quality_policy': 'evidence-review-v1',
        'quality': {'fl_contact_boundaries': 0, 'body_contact_boundaries': 0},
        'model_identity': 'actual-model', 'batch_identity': {}, 'n_actions': 2, 'n_boundaries': 3, 'scene': {}}
    arrays = {'qpos': np.zeros((3, 2)), 'qvel': np.zeros((3, 2)),
              'simulation_time_ns': np.array([0, 20_000_000, 40_000_000], np.int64)}
    states = [{'state': {'task.progress': [p], 'observation.state.base.position': [0, 0, .3],
              'observation.state.projected_gravity': [0, 0, -1]}, 'contact': {'status': 'unknown'}} for p in progress]
    commands = [{'executed': [0.] * 9} for _ in range(2)]
    terminal = {'success': True, 'fallen': False}
    monkeypatch.setattr(rendition, 'verify_trace', lambda _: (m, arrays, {'boundaries': states}, commands, terminal))
    return m, arrays, states, terminal


def test_press_uses_displacement_hold_and_unknown_contact_is_not_failure(tmp_path, monkeypatch):
    trace_fixture(tmp_path, monkeypatch)
    audit = rendition.audit_trace(tmp_path)
    assert audit['quality']['button_displacement_three_ticks'] is True
    assert 'full_footprint_three_ticks' not in audit['quality']
    assert audit['quality']['fl_contact_boundaries'] == 0


@pytest.mark.parametrize('mutation', ['below_threshold', 'fallen', 'time_gap', 'predicate_changed', 'terminal_failed'])
def test_press_rejects_false_success_or_changed_hold_contract(tmp_path, monkeypatch, mutation):
    m, arrays, states, terminal = trace_fixture(tmp_path, monkeypatch)
    if mutation == 'below_threshold': states[0]['state']['task.progress'] = [.0119]
    if mutation == 'fallen': states[-1]['state']['observation.state.base.position'][2] = .05
    if mutation == 'time_gap': arrays['simulation_time_ns'][-1] += 20_000_000
    if mutation == 'predicate_changed': m['profile']['threshold_m'] = .005
    if mutation == 'terminal_failed': terminal['success'] = False
    with pytest.raises(rendition.RecordingIntegrityError): rendition.audit_trace(tmp_path)
