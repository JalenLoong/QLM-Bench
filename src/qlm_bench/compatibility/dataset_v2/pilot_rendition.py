"""Portable formal-pilot rendition admission; no simulator/controller/model imports."""
import json
from pathlib import Path

from .validation import digest, file_hash, read_json, validate_canonical

SCHEMA = 'qlm-push-pilot-rendition-v1'
LINEAGE_SCHEMA = 'qlm-physical-recording-lineage-v1'
RGB_PROFILE = 'dual-rgb-360p-v1'


def load_profile(path):
    profile = read_json(Path(path))
    unsigned = {k: v for k, v in profile.items() if k != 'profile_sha256'}
    if profile.get('schema') != SCHEMA or digest(unsigned) != profile.get('profile_sha256'):
        raise ValueError('Invalid frozen pilot rendition profile')
    slots = profile.get('slots', [])
    if profile.get('task_id') != 'push_box' or profile.get('rgb_profile') != RGB_PROFILE or len(slots) != 10:
        raise ValueError('This profile admits ten360p Push pilots only')
    if (sum(s['difficulty'] == 'clean' for s in slots),
            sum(s['difficulty'] == 'randomized' for s in slots)) != (2, 8):
        raise ValueError('Expected2Clean/8Randomized')
    for key in ('episode_uid', 'rendition_id', 'physical_trajectory_sha256'):
        if len({s[key] for s in slots}) != 10:
            raise ValueError('Duplicate pilot physical/recording identity: ' + key)
    if any(s['task_id'] != 'push_box' or s['split'] != 'train' for s in slots):
        raise ValueError('Explicit all-train pilot membership required')
    if profile.get('maximum_render_attempts') != 3:
        raise ValueError('Frozen render retry budget must be initial+2 retries')
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
    for key in ('fl_contact_boundaries', 'body_contact_boundaries', 'full_footprint_three_ticks', 'not_fallen'):
        if physical.get('quality', {}).get(key) != slot['quality'][key]:
            raise ValueError('Physical quality provenance mismatch')
    if slot['quality']['fl_contact_boundaries'] < 1 or slot['quality']['body_contact_boundaries'] != 0 or \
            slot['quality']['full_footprint_three_ticks'] is not True or slot['quality']['not_fallen'] is not True:
        raise ValueError('FL/task demonstration quality gate failed')
    from ..rgb_profiles import resolve_dataset_profile, RGB_HW
    from .validation import PROFILE
    _, rgb_profile = resolve_dataset_profile(PROFILE, contract['profile_hash'])
    if rgb_profile != RGB_PROFILE:
        raise ValueError('Formal rendition must be360p')
    return {**report, 'formal_pilot_admitted': True, 'profile_sha256': profile['profile_sha256'],
            'episode_uid': ep['episode_uid'], 'rendition_id': slot['rendition_id'],
            'physical_trajectory_sha256': slot['physical_trajectory_sha256'],
            'rgb_hw': list(RGB_HW[rgb_profile]), 'physical_demo_count': 1,
            'physical_source_preserved': True, 'recording_source_separate': True,
            'canonical_inventory_sha256': file_hash(root / 'meta/checksums.json')}
