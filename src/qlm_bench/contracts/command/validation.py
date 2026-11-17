"""Versioned offline contracts. No simulator, model, or publication side effects.

The WAM consumer maintains its own installed copy of this portable validator;
only declarative specifications/fixtures are exchanged between repositories.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile
import numpy as np
from PIL import Image

SPEC = Path(__file__).with_name('spec')
VERSION = '2.0.0'
CAMERAS = ('go2_ego', 'd435i_rgb_task')


class ContractError(ValueError):
    def __init__(self, code, detail):
        self.code, self.detail = code, str(detail)
        super().__init__(f'{code}: {detail}')


def require(condition, code, detail):
    if not condition:
        raise ContractError(code, detail)


def canonical_bytes(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                          allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError) as error:
        raise ContractError('json', error) from error


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'json', f'duplicate key {key}')
        result[key] = value
    return result


def read_json(path):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=_pairs,
                           parse_constant=lambda x: (_ for _ in ()).throw(ContractError('json', x)))
        canonical_bytes(value)
        return value
    except (OSError, UnicodeError, ValueError) as error:
        raise ContractError('json', f'{path}: {error}') from error


def read_jsonl(path):
    try:
        lines = Path(path).read_text(encoding='utf-8').splitlines()
        require(all(line.strip() for line in lines), 'json', 'blank JSONL row')
        result = [json.loads(line, object_pairs_hook=_pairs) for line in lines]
        canonical_bytes(result)
        return result
    except (OSError, UnicodeError, ValueError) as error:
        raise ContractError('json', error) from error


def safe_path(root, name):
    require(isinstance(name, str) and name and '\\' not in name, 'path', name)
    path = Path(name)
    require(not path.is_absolute() and '..' not in path.parts and name == path.as_posix(), 'path', name)
    root = Path(root).resolve()
    target = root / path
    require(all(not (root / Path(*path.parts[:i])).is_symlink() for i in range(1, len(path.parts)+1)), 'path', 'symlink')
    require(target.resolve().is_relative_to(root) and target.is_file(), 'path', name)
    return target


def load_bundle():
    """The command/timing/camera specification files listed in spec/lock.json (structure is checked by _check)."""
    lock = read_json(SPEC / 'lock.json')
    data = {name[:-5]: read_json(SPEC / name) for name in lock['files']}
    return lock, data


LOCK, BUNDLE = load_bundle()
PROFILE_HASHES = LOCK['profile_hashes']
from qlm_bench.contracts.rgb_profiles import camera_bundle, resolve_camera, RGB_HW, RGB_360
RGB_360_BUNDLE = camera_bundle(BUNDLE, RGB_360)
RGB_360_PROFILE_HASHES = {**PROFILE_HASHES, 'cameras': digest(RGB_360_BUNDLE['cameras'])}


def _check(value, schema, path, definitions):
    if '$ref' in schema:
        return _check(value, definitions[schema['$ref'].split('/')[-1]], path, definitions)
    if 'anyOf' in schema:
        for choice in schema['anyOf']:
            try:
                _check(value, choice, path, definitions)
                return
            except ContractError:
                pass
        raise ContractError('schema', f'{path}: no matching type')
    if 'const' in schema:
        require(type(value) is type(schema['const']) and value == schema['const'], 'schema', path)
    if 'enum' in schema:
        require(any(type(value) is type(x) and value == x for x in schema['enum']), 'schema', path)
    t = schema.get('type')
    types = {'object':dict, 'array':list, 'string':str, 'integer':int, 'boolean':bool, 'null':type(None)}
    if t == 'number':
        require(type(value) in (int, float) and math.isfinite(value), 'schema', path)
    elif t:
        require(type(value) is types[t], 'schema', f'{path}: expected {t}')
    if t in ('number', 'integer'):
        for key, passed in [('minimum', value >= schema.get('minimum', -math.inf)),
                            ('maximum', value <= schema.get('maximum', math.inf)),
                            ('exclusiveMinimum', value > schema.get('exclusiveMinimum', -math.inf))]:
            require(passed, 'schema', f'{path}: {key}')
    if t == 'string':
        require(len(value) >= schema.get('minLength', 0), 'schema', path)
        if 'pattern' in schema:
            require(re.fullmatch(schema['pattern'], value) is not None, 'schema', path)
    if t == 'array':
        require(schema.get('minItems', 0) <= len(value) <= schema.get('maxItems', math.inf), 'schema', path)
        for i, item in enumerate(value):
            _check(item, schema['items'], f'{path}[{i}]', definitions)
    if t == 'object':
        props = schema.get('properties', {})
        require(set(schema.get('required', [])) <= value.keys(), 'schema', f'{path}: missing fields')
        for key, item in value.items():
            sub = props.get(key, schema.get('additionalProperties', True))
            require(sub is not False, 'schema', f'{path}: unknown {key}')
            if isinstance(sub, dict):
                _check(item, sub, f'{path}.{key}', definitions)


def validate_record(kind, value):
    canonical_bytes(value)
    defs = BUNDLE['schemas']['$defs']
    require(kind in defs, 'schema', f'unknown record kind {kind}')
    _check(value, defs[kind], kind, defs)
    return copy.deepcopy(value)


def validate_profiles(profiles):
    require(profiles in (PROFILE_HASHES, RGB_360_PROFILE_HASHES), 'profile', 'unrecognized profile hashes')


def validate_command(row):
    validate_record('command', row)
    start, end, until = row['start_tick'], row['end_tick'], row['executed_until_tick']
    require(start % 10 == 0 and end == start + 10 and start <= until <= end, 'timing', 'command interval')
    requested = np.asarray(row['requested'], dtype=np.float64)
    require(np.max(np.abs(requested))<=np.finfo(np.float32).max, 'action', 'not representable as float32')
    expected = requested.astype(np.float32).astype(np.float64); expected[6:] = 0
    require(np.array_equal(row['transformed'], expected) and np.array_equal(row['filtered'], expected), 'action', 'unrecorded transform/filter')
    require(row['force_overridden'] == bool(np.any(requested[6:] != 0)), 'action', 'force override flag')
    status = row['status']
    if status == 'completed':
        require(until == end and row['executed'] is not None and np.array_equal(row['executed'], expected), 'execution', 'unconfirmed or changed execution')
    elif status == 'partial':
        require(start < until < end and row['executed'] is None, 'execution', 'partial must not become a full label')
    else:
        require(until == start and row['executed'] is None, 'execution', 'not executed')
    return row


def _rotation(q):
    x,y,z,w = q
    return np.asarray([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                       [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                       [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


def validate_frame(row, *, epoch, origin_ns, last_tick):
    validate_record('camera_frame', row)
    camera = row['camera_id']
    try: profile, _ = resolve_camera(BUNDLE, camera, row['profile_hash'])
    except ValueError as error: raise ContractError('profile', str(error)) from error
    path=Path(row['path'])
    require(not path.is_absolute() and '..' not in path.parts and '\\' not in row['path'] and row['path']==path.as_posix() and row['path'].startswith(f'rgb/{camera}/'), 'path', 'camera relative path')
    tick = row['capture_tick']
    require(row['reset_epoch'] == epoch, 'epoch', 'camera epoch')
    require(tick % 40 == 0 and tick <= last_tick, 'timing', 'camera tick')
    require(row['timestamp_ns'] == origin_ns + tick * 2_000_000 and row['timestamp_ns'] <= 2**63-1, 'timing', 'capture timestamp')
    require(np.allclose(row['intrinsics'], profile['intrinsics'], rtol=0, atol=1e-3), 'camera', 'intrinsics')
    require(abs(np.linalg.norm(row['world_quaternion_xyzw']) - 1) < 1e-5, 'camera', 'quaternion')
