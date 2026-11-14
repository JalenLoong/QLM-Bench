"""File lists of the door inputs (rl-v4/QLM-DATA-002): ``bundle-small-files.txt`` (what make_workspace_archive.sh packs)
and ``scene-files.json`` (sha256 of every file the door run reads outside the checkouts and models). Small = every
non-mesh file of the 80 train scene packs (their resource-manifest.json entries plus the manifest itself), the 80 case
files and cases-index.json; the meshes (24 distinct sha256, the same set as the 10 Standard100 door test scenes) are
listed by sha256 only and are placed by sha (HF dataset or hard links from content already present).

    python3 scripts/rl_v4/open_room_door/make_lists.py <workspace root> <run dir with cases/ and cases-index.json, workspace-relative>
"""
import hashlib
import json
import sys
from pathlib import Path

LOCAL = '/home/jalen/workspace/WAM-Policy/'
ws, run = Path(sys.argv[1]).resolve(), sys.argv[2].rstrip('/')
here = Path(__file__).resolve().parent
ix = json.loads((ws / run / 'cases-index.json').read_text())
small, files, meshes = [f'{run}/cases-index.json'], {}, {}
for c in ix['cases']:
    d = Path(c['model_path']).parent
    rel = str(d)[len(LOCAL):]
    small.append(f"{run}/cases/{c['case_id']}.json")
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
            'workspace-files.tar.gz, meshes are placed by sha256 (mesh_sha256: the 24 distinct ones and their sizes)',
    'files': dict(sorted(files.items())), 'mesh_sha256': dict(sorted(meshes.items()))}, indent=0) + '\n')
print(len(set(small)), 'small files,', len(files) - len(set(small)), 'mesh references,', len(meshes), 'distinct meshes')
