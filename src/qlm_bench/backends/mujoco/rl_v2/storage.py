"""Versioned local artifacts; no publication or arbitrary-object deserialization."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


@lru_cache(maxsize=1)
def execution_source_identity():
    root = Path(__file__).resolve().parents[3]
    return digest({str(p.relative_to(root)): sha256(p) for folder in
                   ('controllers/rambo', 'contracts', 'tasks', 'compatibility/contracts_v2', 'backends/mujoco')
                   for p in sorted((root / folder).rglob('*'))
                   # equivalence.py registers these digests, so it cannot be part of them (fixed point).
                   if p.suffix in ('.py', '.json') and p.name != 'equivalence.py' and '__pycache__' not in p.parts})


def write_json(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.partial')
    with tmp.open('w') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(p)
