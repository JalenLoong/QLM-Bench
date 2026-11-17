"""File lists of the door inputs: ``bundle-small-files.txt`` (what make_workspace_archive.sh
packs) and ``scene-files.json`` (sha256 of every file the door run reads outside the checkouts and models).

Small = every non-mesh file of the 80 train scene packs (their resource-manifest.json entries plus the manifest itself),
``v2-inference.json`` (model and prompt locators) and ``frozen-resources.json`` (the frozen base files), as push's archive
carries them; the case files and ``cases-index.json`` are files of this directory (``cases/``), not part of the archive.
The meshes (24 distinct sha256, the same set as the 10 Standard100 door test scenes) are listed by sha256 only and are
placed by sha (from the QLM-Bench HF dataset, or hard links from content already present).

    python3 inputs/task_rl/open_room_door/make_lists.py <data root holding task_rl/open_room_door/> [<recorded path prefix>]
"""
import hashlib
import json
import sys
from pathlib import Path

LOCAL = (sys.argv[2] if len(sys.argv) > 2 else '@WORKSPACE@').rstrip('/') + '/'   # prefix of the paths recorded in cases-index.json
ws = Path(sys.argv[1]).resolve()
here = Path(__file__).resolve().parent
ix = json.loads((here / 'cases-index.json').read_text())
small, files, meshes = [], {}, {}
for c in ix['cases']:
    d = Path(c['model_path']).parent
    rel = str(d)[len(LOCAL):]
    small.append(f'{rel}/resource-manifest.json')
    for f, v in json.loads((ws / rel / 'resource-manifest.json').read_text())['files'].items():
        files[f'{rel}/{f}'] = v['sha256']
        if f.startswith('meshes/'):
            meshes[v['sha256']] = v['size_bytes']
        else:
            small.append(f'{rel}/{f}')
for f in small:
    files[f] = hashlib.sha256((ws / f).read_bytes()).hexdigest()
for f, h in files.items():
    if f not in small and hashlib.sha256((ws / f).read_bytes()).hexdigest() != h:
        raise ValueError('mesh hash differs from its resource manifest: ' + f)
(here / 'bundle-small-files.txt').write_text('\n'.join(sorted(set(small))) + '\n')
(here / 'scene-files.json').write_text(json.dumps({
    'note': 'every file the door run reads outside the checkouts and models, by workspace-relative path; small files ship in '
            'workspace-files.tar.gz, meshes are placed by sha256 (mesh_sha256: the 24 distinct ones and their sizes); the case '
            'files are in cases/ of this directory (sha256 in cases-index.json)',
    'files': dict(sorted(files.items())), 'mesh_sha256': dict(sorted(meshes.items()))}, indent=0) + '\n')
print(len(set(small)), 'small files,', len(files) - len(set(small)), 'mesh references,', len(meshes), 'distinct meshes')
