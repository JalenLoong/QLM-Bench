"""Portable foundation snapshots and explicit per-worktree source bindings."""
from __future__ import annotations
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile


def verify_bindings(source_root):
    root = Path(source_root).resolve()
    result = {}
    for package, relative in [('qlm_bench', 'src/qlm_bench'), ('rambo', 'source/rambo/rambo'), ('crl2', 'source/crl2/crl2')]:
        spec = importlib.util.find_spec(package)
        if spec is None or not spec.origin or not Path(spec.origin).resolve().is_relative_to(root / relative):
            raise ValueError('Wrong worktree import source: ' + package)
        result[package] = spec.origin
    return {'passed': True, 'source_root': str(root), 'imports': result}


def freeze_snapshot(root, output):
    root, out = Path(root).resolve(), Path(output).resolve()
    if out.exists() or out == root or out.is_relative_to(root):
        raise ValueError('New snapshot directory outside checkout required')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args])
    base = git('rev-parse', 'HEAD').decode().strip()
    tracked = [x for x in git('ls-files', '-z').decode().split('\0') if x]
    untracked = [x for x in git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\0') if x]
    out.mkdir(parents=True)
    patch = git('diff', '--binary', 'HEAD')
    (out / 'tracked.patch').write_bytes(patch)
    with tarfile.open(out / 'new-files.tar', 'w') as archive:
        for name in sorted(untracked):
            if (root / name).is_symlink():
                raise ValueError('Snapshot refuses source symlinks')
            archive.add(root / name, arcname=name)
    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
              for name in sorted(set(tracked + untracked)) if (root / name).is_file()}
    result = {'schema': 'qlm-foundation-snapshot-v1', 'base_commit': base,
              'tracked_patch_sha256': hashlib.sha256(patch).hexdigest(),
              'new_files_tar_sha256': hashlib.sha256((out / 'new-files.tar').read_bytes()).hexdigest(),
              'files': hashes, 'source_committed_or_pushed': False}
    (out / 'snapshot.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def apply_snapshot(root, snapshot):
    root, snapshot = Path(root).resolve(), Path(snapshot).resolve()
    record = json.loads((snapshot / 'snapshot.json').read_text())
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args])
    if git('rev-parse', 'HEAD').decode().strip() != record['base_commit'] or git('status', '--porcelain'):
        raise ValueError('Clean checkout at exact snapshot base required')
    for file, field in [('tracked.patch', 'tracked_patch_sha256'), ('new-files.tar', 'new_files_tar_sha256')]:
        if hashlib.sha256((snapshot / file).read_bytes()).hexdigest() != record[field]:
            raise ValueError('Foundation snapshot checksum mismatch')
    if (snapshot / 'tracked.patch').stat().st_size:
        subprocess.run(['git', '-C', str(root), 'apply', '--check', str(snapshot / 'tracked.patch')], check=True)
        subprocess.run(['git', '-C', str(root), 'apply', str(snapshot / 'tracked.patch')], check=True)
    with tarfile.open(snapshot / 'new-files.tar') as archive:
        for member in archive.getmembers():
            dest = (root / member.name).resolve()
            if not dest.is_relative_to(root) or not member.isfile() or dest.exists():
                raise ValueError('Unsafe or existing snapshot destination')
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(archive.extractfile(member).read())
            dest.chmod(member.mode & 0o777)
    for name, digest in record['files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Applied source differs from frozen foundation: ' + name)
    return {'passed': True, 'source_root': str(root), 'base_commit': record['base_commit']}
