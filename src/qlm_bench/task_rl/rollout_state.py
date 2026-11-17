"""Rollout-state files: a snapshot captured during a Task RL rollout plus a small manifest.

For ``<name>.pt`` three files are written: the snapshot payload ``<name>.pt``, its summary ``<name>.json``
(written by ``snapshot.save``) and the manifest ``<name>.own.json`` binding it to the worker's scene (the
sha256 of the case file) and its origin. All paths are confined to the worker's ``--state-root``.
"""
import json
from pathlib import Path

SCHEMA = 'qlm-task-rl-rollout-state-v1'


def resolve(state_root, path):
    """Resolve ``path`` (absolute or relative to the root) strictly inside ``state_root``."""
    if state_root is None:
        raise ValueError('Rollout-state operations need the worker --state-root')
    if not isinstance(path, str) or not path or '\x00' in path:
        raise ValueError('Explicit rollout-state path required')
    root = Path(state_root).resolve()
    target = Path(path) if Path(path).is_absolute() else root / path
    target = target.resolve()
    if root not in target.parents or target.suffix != '.pt':
        raise ValueError('Rollout-state path must be a .pt file inside the state root')
    return target


def manifest_path(path):
    return Path(path).with_suffix('.own.json')


def save(rt, path, *, origin, binding_sha256, privileged_row):
    """Capture the live runtime at a legal chunk boundary and write payload + manifests."""
    from qlm_bench.task_rl import open_room_door
    return save_snapshot(open_room_door.capture(rt), path, task_id=rt.task.task, origin=origin,
                         binding_sha256=binding_sha256, privileged_row=privileged_row)


def save_snapshot(snap, path, *, task_id, origin, binding_sha256, privileged_row):
    """Write an already captured snapshot (e.g. from the in-memory ring) with the same manifest as ``save``."""
    from qlm_bench.task_rl import snapshot
    path = Path(path)
    if manifest_path(path).exists():
        raise FileExistsError(manifest_path(path))
    snapshot.save(path, snap)
    record = {'schema': SCHEMA, 'snapshot_schema': snapshot.SCHEMA, 'snapshot': path.name,
              'snapshot_sha256': snapshot.sha256(path), 'absolute_tick': snap['tick'],
              'simulation_time_ns': snap['tick'] * 2_000_000, 'scene': snap['scene'],
              'binding_sha256': binding_sha256, 'task_id': task_id, 'origin': origin,
              'privileged_row': privileged_row}
    snapshot.write_json(manifest_path(path), record)
    return record


def load(path, *, binding_sha256):
    """Snapshot plus manifest; refuses a state captured on another case/scene."""
    from qlm_bench.task_rl import snapshot
    path = Path(path)
    record = json.loads(manifest_path(path).read_text())
    if record.get('schema') != SCHEMA or record.get('snapshot') != path.name:
        raise ValueError('Not a Task RL rollout-state manifest')
    if record['binding_sha256'] != binding_sha256:
        raise ValueError('Rollout state belongs to another case')
    snap = snapshot.load(path)
    if snap['tick'] != record['absolute_tick']:
        raise ValueError('Rollout-state payload/manifest tick mismatch')
    return snap, record
