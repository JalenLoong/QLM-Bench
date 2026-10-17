"""Portable formal-pilot rendition admission; no simulator/controller/model imports."""
import json
from pathlib import Path

from .validation import digest, file_hash, read_json, validate_canonical

SCHEMA = 'qlm-push-pilot-rendition-v1'
PRODUCTION_SCHEMA = 'qlm-push-production-rendition-v1'
PRESS_SCHEMA = 'qlm-press-pilot-slot-rendition-v1'
LIFT_SCHEMA = 'qlm-lift-pilot-slot-rendition-v1'
KICK_SCHEMA = 'qlm-kick-pilot-slot-rendition-v1'
KICK_PRODUCTION_SCHEMA = 'qlm-kick-production-rendition-v1'
LIFT_PRODUCTION_SCHEMA = 'qlm-lift-production-rendition-v1'
PRESS_PRODUCTION_SCHEMA = 'qlm-press-production-rendition-v1'
LINEAGE_SCHEMA = 'qlm-physical-recording-lineage-v1'
REMAINING_PRODUCTION_SCHEMA = 'qlm-approved-six-production-rendition-v1'
REMAINING_TASKS = ('sweep_block_to_zone','close_fridge_door','close_oven_door','turn_valve','pull_open_drawer','open_room_door')
RGB_PROFILE = 'dual-rgb-360p-v1'


def load_profile(path):
    profile = read_json(Path(path))
    if profile.get('schema') == REMAINING_PRODUCTION_SCHEMA:
        return load_remaining_profile(profile)
    unsigned = {k: v for k, v in profile.items() if k != 'profile_sha256'}
    if profile.get('schema') not in (SCHEMA, PRODUCTION_SCHEMA, PRESS_SCHEMA, PRESS_PRODUCTION_SCHEMA, LIFT_SCHEMA, LIFT_PRODUCTION_SCHEMA, KICK_SCHEMA, KICK_PRODUCTION_SCHEMA) or digest(unsigned) != profile.get('profile_sha256'):
        raise ValueError('Invalid frozen pilot rendition profile')
    slots = profile.get('slots', [])
    production = profile['schema'] in (PRODUCTION_SCHEMA, PRESS_PRODUCTION_SCHEMA, LIFT_PRODUCTION_SCHEMA, KICK_PRODUCTION_SCHEMA)
    press = profile['schema'] == PRESS_SCHEMA
    slot_pilot = profile['schema'] in (PRESS_SCHEMA, LIFT_SCHEMA, KICK_SCHEMA)
    task_id = 'kick_ball_to_goal' if profile['schema'] in (KICK_SCHEMA,KICK_PRODUCTION_SCHEMA) else 'lift_basket' if profile['schema'] in (LIFT_SCHEMA,LIFT_PRODUCTION_SCHEMA) else 'press_button' if profile['schema'] in (PRESS_SCHEMA, PRESS_PRODUCTION_SCHEMA) else 'push_box'
    expected = 1 if production or slot_pilot else 10
    if profile.get('task_id') != task_id or profile.get('rgb_profile') != RGB_PROFILE or len(slots) != expected:
        raise ValueError('Invalid explicit task rendition membership')
    if slot_pilot:
        if not profile.get('pilot_campaign_sha256') or profile.get('pilot_target') != 10 or profile.get('quality_policy') != 'evidence-review-v1':
            raise ValueError('Frozen ten-slot task pilot campaign required')
        if slots[0]['difficulty'] not in ('clean', 'randomized'):
            raise ValueError('Invalid Press pilot difficulty')
    if production:
        authorization = profile.get('production_authorization', {})
        if authorization.get('pilot_approved') is not True or authorization.get('target_accepted') != 100 or not profile.get('campaign_sha256'):
            raise ValueError('Approved100 campaign required')
        if slots[0]['difficulty'] not in ('clean', 'randomized') or slots[0]['split'] not in ('train', 'validation', 'test'):
            raise ValueError('Invalid production split/difficulty')
    elif not slot_pilot and (sum(s['difficulty'] == 'clean' for s in slots), sum(s['difficulty'] == 'randomized' for s in slots)) != (2, 8):
        raise ValueError('Expected2Clean/8Randomized')
    for key in ('episode_uid', 'rendition_id', 'physical_trajectory_sha256'):
        if len({s[key] for s in slots}) != expected:
            raise ValueError('Duplicate pilot physical/recording identity: ' + key)
    if any(s['task_id'] != task_id or (not production and s['split'] != 'train') for s in slots):
        raise ValueError('Explicit all-train pilot membership required')
    if profile.get('maximum_render_attempts') != 3:
        raise ValueError('Frozen render retry budget must be initial+2 retries')
    policy = profile.get('quality_policy', 'legacy-fl-contact-v1')
    if policy == 'evidence-review-v1':
        approval = profile.get('approval', {})
        if approval.get('reference_quality_approved') is not True or approval.get('retarget_scope_approved') is not True or not approval.get('evidence_sha256'):
            raise ValueError('Explicit reference/retarget approval required')
        for slot in slots:
            if slot['difficulty'] == 'clean' and slot.get('appearance_preset') != 'ap_00':
                raise ValueError('Clean pilot requires ap_00')
            if slot.get('review_status') != ('approved_task_recipe_technical_quality' if production else 'eligible_for_ten_pilot_user_review') or not slot.get('quality_review_sha256'):
                raise ValueError('Actual behavior evidence review required')
    elif policy != 'legacy-fl-contact-v1':
        raise ValueError('Unknown pilot quality policy')
    return profile


def load_remaining_profile(profile):
    """New production metadata; the frozen Raw/Canonical schema is unchanged."""
    unsigned = {k:v for k,v in profile.items() if k != 'profile_sha256'}
    slots = profile.get('slots', [])
    auth = profile.get('production_authorization', {})
    approval = profile.get('approval', {})
    if digest(unsigned) != profile.get('profile_sha256') or profile.get('task_id') not in REMAINING_TASKS:
        raise ValueError('Invalid approved-six production identity')
    if len(slots) != 1 or profile.get('rgb_profile') != RGB_PROFILE or profile.get('maximum_render_attempts') != 3:
        raise ValueError('One explicit360p production slot and bounded render retries required')
    if auth.get('remaining_six_approved') is not True or auth.get('target_accepted') != 100 or not profile.get('campaign_sha256'):
        raise ValueError('Explicit fresh100 authorization required')
    if not all(approval.get(k) is True for k in ('reference_quality_approved','retarget_scope_approved')) or not approval.get('evidence_sha256'):
        raise ValueError('Approved reference and scope required')
    slot = slots[0]
    if slot['task_id'] != profile['task_id'] or slot['difficulty'] not in ('clean','randomized') or slot['split'] not in ('train','validation','test'):
        raise ValueError('Invalid remaining-task membership')
    if slot['difficulty'] == 'clean' and slot['appearance_preset'] != 'ap_00':
        raise ValueError('Clean requires ap_00')
    if profile.get('quality_policy') != 'evidence-review-v1' or slot.get('review_status') != 'approved_task_recipe_technical_quality' or not slot.get('quality_review_sha256'):
        raise ValueError('Actual behavior evidence required')
    return profile


def slot_for(profile, uid):
    matches = [s for s in profile['slots'] if s['episode_uid'] == uid]
    if len(matches) != 1:
        raise ValueError('Episode is not an admitted pilot slot')
    return matches[0]


def validate_formal_pilot(root, *, profile_path, tools, check_media=True):
    root = Path(root)
    profile = load_profile(profile_path)
    report = validate_canonical(root, tools=tools, check_media=check_media)
    contract = read_json(root / 'meta/contract.json')
    if contract['diagnostic_only'] or len(contract['episodes']) != 1:
        raise ValueError('Exactly one formal pilot episode required')
    ep = contract['episodes'][0]
    slot = slot_for(profile, ep['episode_uid'])
    provenance = read_json(root / 'metadata/provenance.json')
    lineage = provenance.get('recording_lineage', {})
    physical = lineage.get('physical', {})
    recording = lineage.get('recording', {})
    if lineage.get('schema') != LINEAGE_SCHEMA or provenance.get('work_id') != profile['work_id']:
        raise ValueError('Explicit physical/recording lineage required')
    if physical.get('manifest_sha256') != slot['trace_manifest_sha256'] or \
            physical.get('trajectory_sha256') != slot['physical_trajectory_sha256'] or \
            physical.get('source_identity_sha256') != slot['physical_source_sha256'] or \
            physical.get('model_identity') != slot['model_identity']:
        raise ValueError('Pilot physical identity differs from frozen source')
    if digest(provenance['source_identity']) != slot['physical_source_sha256']:
        raise ValueError('Original physical source was relabeled')
    if recording.get('profile_sha256') != profile['profile_sha256'] or \
            recording.get('rendition_id') != slot['rendition_id'] or \
            recording.get('rgb_profile') != RGB_PROFILE or \
            recording.get('source_identity_sha256') != digest(profile['recording_source']) or \
            digest(recording.get('source_identity', {})) != digest(profile['recording_source']):
        raise ValueError('New recording identity/profile mismatch')
    if recording.get('physics_reexecuted') is not False or recording.get('controller_executed') is not False:
        raise ValueError('Rendition must not claim a new physical execution')
    meta = provenance.get('formal_metadata', {})
    if any(meta.get(k) != slot[k] for k in ('episode_uid', 'task_id', 'difficulty', 'split')):
        raise ValueError('Pilot metadata differs from frozen membership')
    if ep['status'] != 'success' or provenance.get('recording_mode') != 'offline_state_replay':
        raise ValueError('Successful actual state replay required')
    predicate = (profile['task_id'] + '_three_ticks') if profile['schema'] == REMAINING_PRODUCTION_SCHEMA else {'press_button':'button_displacement_three_ticks','push_box':'full_footprint_three_ticks',
                 'lift_basket':'whole_basket_clearance_three_ticks', 'kick_ball_to_goal':'front_whole_ball_goal_three_ticks'}[profile['task_id']]
    for key in ('fl_contact_boundaries', 'body_contact_boundaries', predicate, 'not_fallen'):
        if physical.get('quality', {}).get(key) != slot['quality'][key]:
            raise ValueError('Physical quality provenance mismatch')
    if slot['quality'][predicate] is not True or slot['quality']['not_fallen'] is not True:
        raise ValueError('Original task predicate failed')
    if profile.get('quality_policy', 'legacy-fl-contact-v1') == 'legacy-fl-contact-v1' and (slot['quality']['fl_contact_boundaries'] < 1 or slot['quality']['body_contact_boundaries'] != 0):
        raise ValueError('Legacy FL demonstration quality gate failed')
    from ..rgb_profiles import resolve_dataset_profile, RGB_HW
    from .validation import PROFILE
    _, rgb_profile = resolve_dataset_profile(PROFILE, contract['profile_hash'])
    if rgb_profile != RGB_PROFILE:
        raise ValueError('Formal rendition must be360p')
    return {**report, 'formal_pilot_admitted': profile['schema'] in (SCHEMA, PRESS_SCHEMA, LIFT_SCHEMA, KICK_SCHEMA), 'formal_production_admitted': profile['schema'] in (PRODUCTION_SCHEMA, PRESS_PRODUCTION_SCHEMA, LIFT_PRODUCTION_SCHEMA, KICK_PRODUCTION_SCHEMA, REMAINING_PRODUCTION_SCHEMA), 'profile_sha256': profile['profile_sha256'],
            'episode_uid': ep['episode_uid'], 'rendition_id': slot['rendition_id'],
            'physical_trajectory_sha256': slot['physical_trajectory_sha256'],
            'rgb_hw': list(RGB_HW[rgb_profile]), 'physical_demo_count': 1,
            'physical_source_preserved': True, 'recording_source_separate': True,
            'canonical_inventory_sha256': file_hash(root / 'meta/checksums.json')}
