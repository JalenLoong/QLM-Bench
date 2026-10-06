"""Live physical RGB envelope around byte-preserved contracts_v2 messages.

Compatibility camera paths are logical frame IDs, not files to open. Their digest
identifies the raw RGB bytes carried in this envelope (explicitly labelled in the
frame extensions); no resize, compression, latent or model tensor is introduced.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import math

from qlm_bench.compatibility.contracts_v2.validation import (
    BUNDLE, CAMERAS, PROFILE_HASHES, VERSION, validate_frame, validate_profiles, validate_record,
)
from qlm_bench.policy_interface.physical import ROOT_FIELDS

PHYSICS_STEP_NS = 2_000_000
GROUP_COMMANDS = 16
GROUP_TICKS = 160
SAMPLE_TICKS = 40
OBSERVATION_SCHEMA = 'qlm-live-observation-v1'
STATE_SEMANTICS = {'reference': 'root_link', 'quaternion': 'xyzw', 'velocity_frame': 'world',
                   'projected_gravity_frame': 'body'}


def make_message(kind, body, *, session_id, episode_id, reset_epoch, message_id, extensions=None):
    message = dict(protocol_version=VERSION, type=kind, session_id=session_id, episode_id=episode_id,
                   reset_epoch=reset_epoch, message_id=message_id, profiles=deepcopy(PROFILE_HASHES),
                   extensions={} if extensions is None else deepcopy(extensions), body=deepcopy(body))
    validate_record(kind, message)
    return message


def _root_state(value):
    if not isinstance(value, dict) or set(value) != set(ROOT_FIELDS):
        raise ValueError('Complete root-link fields required; private task state is forbidden')
    for key, values in value.items():
        width = 4 if key.endswith('orientation') else 3
        if not isinstance(values, (list, tuple)) or len(values) != width or \
                any(type(x) not in (float, int) or not math.isfinite(x) for x in values):
            raise ValueError('Malformed physical root state')
    quaternion = value['observation.state.base.orientation']
    if abs(math.sqrt(sum(x*x for x in quaternion)) - 1) > 1e-5:
        raise ValueError('Root quaternion must be normalized xyzw')


def validate_live_observation(packet, *, origin_ns=0, expected_capture_ticks=None, require_root_state=False):
    if not isinstance(packet, dict) or set(packet) != {'schema', 'observation', 'samples', 'state_semantics'} or \
            packet['schema'] != OBSERVATION_SCHEMA:
        raise ValueError('Unsupported live observation envelope')
    message = packet['observation']
    validate_record('Observation', message)
    validate_profiles(message['profiles'])
    samples = packet['samples']
    if not isinstance(samples, list) or len(samples) not in (1, 4):
        raise ValueError('Cold start is one real sample; ordinary feedback is four real samples')
    ticks = [sample.get('capture_tick') for sample in samples]
    if len(samples) == 1 and ticks != [0] or len(samples) == 4 and \
            (ticks[0] <= 0 or any(b-a != SAMPLE_TICKS for a, b in zip(ticks, ticks[1:]))):
        raise ValueError('Invalid cold-start or ordinary feedback timeline')
    if expected_capture_ticks is not None and ticks != list(expected_capture_ticks):
        raise ValueError('Feedback samples differ from the pending execution schedule')
    if ticks[-1] != message['body']['tick']:
        raise ValueError('Observation end differs from the last physical capture')
    frame_map = {}
    for frame in message['body']['rgb']:
        validate_frame(frame, epoch=message['reset_epoch'], origin_ns=origin_ns,
                       last_tick=message['body']['tick'])
        key = (frame['capture_tick'], frame['camera_id'])
        if key in frame_map:
            raise ValueError('Duplicate frame identity')
        frame_map[key] = frame
    if len(frame_map) != 2 * len(samples):
        raise ValueError('Exactly two physical RGB views per sample required')
    root_present = any(sample.get('root_state') for sample in samples)
    semantics = packet['state_semantics']
    if root_present or require_root_state:
        if not isinstance(semantics, dict) or set(semantics) != set(STATE_SEMANTICS) | {'ground_z', 'ground_reference'} or \
                any(semantics.get(k) != v for k, v in STATE_SEMANTICS.items()) or \
                type(semantics.get('ground_z')) not in (float, int) or not math.isfinite(semantics['ground_z']) or \
                not isinstance(semantics.get('ground_reference'), str) or not semantics['ground_reference']:
            raise ValueError('Explicit root-link, xyzw, world-velocity and ground identity required')
    elif semantics:
        raise ValueError('State semantics must be empty when no state is provided')
    last_ids = {}
    for sample in samples:
        if set(sample) != {'capture_tick', 'capture_sim_ns', 'rgb', 'sensor_frame_ids', 'root_state'}:
            raise ValueError('Unknown live sample fields; private channels cannot enter policy input')
        tick = sample['capture_tick']
        if type(tick) is not int or sample['capture_sim_ns'] != origin_ns + tick*PHYSICS_STEP_NS or \
                set(sample['rgb']) != set(CAMERAS) or set(sample['sensor_frame_ids']) != set(CAMERAS):
            raise ValueError('Physical sample timing or camera identity mismatch')
        if root_present or require_root_state:
            _root_state(sample['root_state'])
        elif sample['root_state'] != {}:
            raise ValueError('Malformed absent state')
        for camera, image in sample['rgb'].items():
            frame = frame_map[(tick, camera)]
            profile = BUNDLE[camera]
            if str(getattr(image, 'dtype', None)) != 'uint8' or \
                    tuple(getattr(image, 'shape', ())) != (profile['height'], profile['width'], 3):
                raise ValueError('Live RGB must retain the physical full-resolution uint8 HWC profile')
            if frame['sha256'] != hashlib.sha256(image.tobytes(order='C')).hexdigest() or \
                    frame['extensions'].get('payload_encoding') != 'raw-rgb8':
                raise ValueError('Lossless RGB payload does not match frame identity')
            current_id = sample['sensor_frame_ids'][camera]
            if type(current_id) is not int or current_id != frame['sensor_frame_id'] or \
                    current_id <= last_ids.get(camera, -1):
                raise ValueError('Sensor frame identity is stale or inconsistent')
            last_ids[camera] = current_id
    return packet


def _multiply(a, b):
    x,y,z,w = a
    X,Y,Z,W = b
    return [w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X,
            w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z]


def _camera_pose(root, camera):
    q = root['observation.state.base.orientation']
    p = root['observation.state.base.position']
    config = BUNDLE[camera]
    v = _multiply(_multiply(q, config['mount_position_m'] + [0.]), [-q[0],-q[1],-q[2],q[3]])[:3]
    return [a+b for a,b in zip(p,v)], _multiply(q, config['mount_quaternion_xyzw'])


def make_observation(samples, *, session_id, episode_id, reset_epoch, message_id,
                     instruction, executed_history, state_semantics, origin_ns=0):
    """Create one live packet from owned runtime snapshots at exact sample boundaries."""
    frames = []
    public_samples = []
    aliases = dict(zip(CAMERAS, ('ego', 'task_centric')))
    for snapshot in samples:
        tick = snapshot['physics_step']
        if snapshot['simulation_time_ns'] != origin_ns + tick*PHYSICS_STEP_NS or \
                snapshot['reset_epoch'] != reset_epoch:
            raise ValueError('Runtime snapshot time/reset differs from live episode')
        root = {key: list(snapshot['state'][key]) for key in ROOT_FIELDS}
        _root_state(root)
        rgb, sensor_ids = {}, {}
        for camera, alias in aliases.items():
            image = snapshot['rgb'][alias].copy()
            image.setflags(write=False)
            rgb[camera] = image
            sensor_ids[camera] = snapshot['sensor_frame_ids'][alias]
            position, quaternion = _camera_pose(root, camera)
            frames.append(dict(camera_id=camera, profile_hash=BUNDLE['cameras']['cameras'][camera],
                               sensor_frame_id=sensor_ids[camera], capture_tick=tick,
                               timestamp_ns=snapshot['simulation_time_ns'],
                               path=f'rgb/{camera}/{reset_epoch}-{tick}.rgb',
                               sha256=hashlib.sha256(image.tobytes(order='C')).hexdigest(),
                               intrinsics=deepcopy(BUNDLE[camera]['intrinsics']), world_position=position,
                               world_quaternion_xyzw=quaternion, reset_epoch=reset_epoch,
                               extensions={'payload_encoding': 'raw-rgb8',
                                           'camera_pose_source': 'measured_root_link_and_fixed_profile_mount'}))
        public_samples.append(dict(capture_tick=tick, capture_sim_ns=snapshot['simulation_time_ns'],
                                   rgb=rgb, sensor_frame_ids=sensor_ids,
                                   root_state=root if state_semantics else {}))
    message = make_message('Observation', dict(tick=samples[-1]['physics_step'], rgb=frames,
                            executed_history=deepcopy(executed_history), instruction=instruction),
                           session_id=session_id, episode_id=episode_id, reset_epoch=reset_epoch,
                           message_id=message_id)
    packet = dict(schema=OBSERVATION_SCHEMA, observation=message, samples=public_samples,
                  state_semantics=deepcopy(state_semantics))
    return validate_live_observation(packet, origin_ns=origin_ns)
