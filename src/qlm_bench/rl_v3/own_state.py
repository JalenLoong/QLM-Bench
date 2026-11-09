"""Versioned own-rollout state files for RL-v3 resets (rl-v3/QLM-SIM-002).

Reuses ``backends/mujoco/rl_v2/snapshot.py`` unchanged: ``capture`` already accepts any nonterminal,
completed ``tick % 160 == 0`` boundary regardless of whether the trajectory came from a
demonstration or from the policy, and ``restore`` checks the model/profile/controller/source
identity. This module only adds a manifest that binds the payload to the worker scene and origin,
and confines every path to an explicit state root. The demo-anchor path is not touched.

Files written for ``<name>.pt``: the snapshot payload ``<name>.pt``, its rl-v2 inventory
``<name>.json`` (written by ``snapshot.save``) and the RL-v3 manifest ``<name>.own.json``.
"""
import json
from pathlib import Path

SCHEMA = 'qlm-rl-v3-own-state-v1'


def resolve(state_root, path):
    """Resolve ``path`` (absolute or relative to the root) strictly inside ``state_root``."""
    if state_root is None:
        raise ValueError('Own-state RPC disabled: worker started without --state-root')
    if not isinstance(path, str) or not path or '\x00' in path:
        raise ValueError('Explicit own-state path required')
    root = Path(state_root).resolve()
    target = Path(path) if Path(path).is_absolute() else root / path
    target = target.resolve()
    if root not in target.parents or target.suffix != '.pt':
        raise ValueError('Own-state path must be a .pt file inside the state root')
    return target


def manifest_path(path):
    return Path(path).with_suffix('.own.json')


def save(rt, path, *, origin, binding_sha256, privileged_row):
    """Capture the live runtime at a legal chunk boundary and write payload + manifests."""
    from qlm_bench.backends.mujoco.rl_v2 import snapshot
    return save_snapshot(snapshot.capture(rt), path, task_id=rt.task.task, origin=origin,
                         binding_sha256=binding_sha256, privileged_row=privileged_row)


def save_snapshot(snap, path, *, task_id, origin, binding_sha256, privileged_row):
    """Write an already captured snapshot (rl-v3/QLM-SIM-003 ring) with the same manifest as ``save``."""
    from qlm_bench.backends.mujoco.rl_v2 import snapshot
    from qlm_bench.backends.mujoco.rl_v2.storage import sha256, write_json
    path = Path(path)
    if manifest_path(path).exists():
        raise FileExistsError(manifest_path(path))
    snapshot.save(path, snap)
    record = {'schema': SCHEMA, 'snapshot_schema': snapshot.SCHEMA, 'snapshot': path.name,
              'snapshot_sha256': sha256(path), 'absolute_tick': snap['tick'],
              'simulation_time_ns': snap['tick'] * 2_000_000, 'identity': snap['identity'],
              'binding_sha256': binding_sha256, 'task_id': task_id, 'origin': origin,
              'privileged_row': privileged_row}
    write_json(manifest_path(path), record)
    return record


def load(path, *, binding_sha256):
    """Verified snapshot plus manifest; refuses another scene binding or a changed payload."""
    from qlm_bench.backends.mujoco.rl_v2 import snapshot
    from qlm_bench.backends.mujoco.rl_v2.storage import sha256
    path = Path(path)
    record = json.loads(manifest_path(path).read_text())
    if record.get('schema') != SCHEMA or record.get('snapshot') != path.name:
        raise ValueError('Not an RL-v3 own-state manifest')
    if record['snapshot_sha256'] != sha256(path):
        raise ValueError('Own-state payload hash mismatch')
    if record['binding_sha256'] != binding_sha256:
        raise ValueError('Own state belongs to another scene binding')
    snap = snapshot.load(path)
    if snap['tick'] != record['absolute_tick'] or snap['identity'] != record['identity']:
        raise ValueError('Own-state payload/manifest mismatch')
    return snap, record
