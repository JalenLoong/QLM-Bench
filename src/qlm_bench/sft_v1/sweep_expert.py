"""Frozen production sweep_block_to_zone scripted expert (sft-v1/QLM-SIM-003).

The production expert (remaining-six production QLM-DATA-040) is not in any ``experts/`` folder: it is the class ``Sweep`` of
``runs/audit/sweep-task-success-scope-20261016-v1/geometry-entry-v3/entry_escape_executor.py`` in the workspace, at the end
of a 16-class inheritance chain spread over four audit directories, configured by ``sweep-recipe-v9.json``. This module loads a
byte-identical copy of that chain (``sweep_frozen/workspace/<workspace-relative path>``, listed with source path and sha256 in
``sweep_frozen/MANIFEST.json``) without reading the audit directories.

Load transform (the only one): four files hard-code ``R=Path('/home/jalen/workspace/WAM-Policy')`` and build their parent's
path from it. At exec time that literal is replaced by the mirror root, so every ``importlib.util.spec_from_file_location``
the chain performs resolves inside the mirror; the stored bytes are unchanged and verified against the manifest before
compilation. A spec outside the mirror, an unknown file or a hash mismatch raises. ``shared_executor`` (imported by name from
``sys.path`` in production) is loaded from the mirror into ``sys.modules`` under the same name.

Interface of the expert (production ``collect_trace`` convention, not ``ExpertAdapter``):
``expert = build(); expert.reset(runtime, scene)``, then one ``values, diag = expert.command()`` per completed 50 Hz command.
``scene`` needs ``initial_state.qpos`` (``fixed_base_y`` is read from qpos[1]).
"""
import contextlib
import copy
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import types

HERE = Path(__file__).resolve().parent
FROZEN = HERE / 'sweep_frozen'
MIRROR = FROZEN / 'workspace'
MANIFEST_PATH = FROZEN / 'MANIFEST.json'
ORIGINAL_ROOT = b"Path('/home/jalen/workspace/WAM-Policy')"
VERSION = 'sweep-production-frozen-v1'


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def manifest():
    return json.loads(MANIFEST_PATH.read_text())


def _expected():
    return {str((MIRROR / row['path']).resolve()): row for row in manifest()['files']}


def verify():
    """sha256 of every frozen file against the manifest; returns the identity record used in provenance."""
    rows = manifest()['files']
    for row in rows:
        data = (MIRROR / row['path']).read_bytes()
        if _sha(data) != row['sha256'] or len(data) != row['size_bytes']:
            raise ValueError('Frozen sweep expert file changed: ' + row['path'])
    return {'version': VERSION, 'manifest_sha256': _sha(MANIFEST_PATH.read_bytes()),
            'entry': manifest()['entry'], 'files': {row['path']: row['sha256'] for row in rows}}


class _FrozenLoader(importlib.machinery.SourceFileLoader):
    """Exec a mirror file after the hash check and the documented root substitution; never writes bytecode."""

    def __init__(self, fullname, path, expected):
        super().__init__(fullname, path)
        self.expected = expected

    def get_data(self, path):
        resolved = str(Path(path).resolve())
        if resolved not in self.expected:
            raise ImportError('Frozen sweep loader refuses a file outside the manifest: ' + str(path))
        data = Path(resolved).read_bytes()
        if _sha(data) != self.expected[resolved]['sha256']:
            raise ImportError('Frozen sweep file hash mismatch: ' + str(path))
        return data.replace(ORIGINAL_ROOT, ("Path(%r)" % str(MIRROR)).encode())

    def path_stats(self, path):  # No bytecode cache: always compile from the verified source.
        raise OSError

    def set_data(self, *args, **kwargs):
        return None


@contextlib.contextmanager
def _redirected_specs(expected):
    original = importlib.util.spec_from_file_location

    def spec(name, location=None, *args, **kwargs):
        resolved = str(Path(location).resolve())
        if resolved not in expected:
            raise ImportError(f'Frozen sweep chain asked for {location}, which is not in the frozen mirror')
        loader = _FrozenLoader(name, resolved, expected)
        return original(name, resolved, loader=loader)
    importlib.util.spec_from_file_location = spec
    try:
        yield
    finally:
        importlib.util.spec_from_file_location = original


_MODULE = None


def module():
    """The frozen entry module (loaded once per process)."""
    global _MODULE
    if _MODULE is not None:
        return _MODULE
    verify()
    expected = _expected()
    shared = MIRROR / 'runs/audit/remaining-six-reference-20261016-v1/shared_executor.py'
    current = sys.modules.get('shared_executor')
    if current is not None and str(Path(getattr(current, '__file__', '')).resolve()) != str(shared.resolve()):
        raise ImportError('A different shared_executor is already imported: ' + str(getattr(current, '__file__', None)))
    entry = MIRROR / manifest()['entry']['path']
    with _redirected_specs(expected):
        if current is None:
            spec = importlib.util.spec_from_file_location('shared_executor', shared)
            mod = importlib.util.module_from_spec(spec)
            sys.modules['shared_executor'] = mod
            spec.loader.exec_module(mod)
        spec = importlib.util.spec_from_file_location('approved_production_sweep_block_to_zone', entry)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    _MODULE = mod
    return mod


def recipe():
    return copy.deepcopy(json.loads((MIRROR / manifest()['recipe']).read_text()))


def build(config=None):
    """A new production Sweep expert with the frozen recipe (or an explicit config, recorded by the caller)."""
    cls = getattr(module(), manifest()['entry']['class'])
    return cls(recipe() if config is None else copy.deepcopy(config))


def chain():
    """Class MRO of the frozen expert with the file each class was compiled from."""
    out = []
    for c in getattr(module(), 'Sweep').__mro__:
        files = sorted({v.__code__.co_filename for v in c.__dict__.values() if isinstance(v, types.FunctionType)})
        out.append({'module': c.__module__, 'class': c.__qualname__, 'files': files})
    return out
