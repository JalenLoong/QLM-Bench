"""Download the Standard100 suite and its scene/controller packs from the QLM-Bench Hugging Face dataset."""
import json
from pathlib import Path

from qlm_bench.benchmark.suite import RELEASE


def fetch(output, *, case_ids=None, repo_id=None, revision=None):
    """Suite metadata plus the scene packs of the selected cases (default: all 100) and the RAMBO controller.

    The result is a resource root with the dataset layout: ``benchmarks/<RELEASE>/`` and ``assets/``."""
    from huggingface_hub import snapshot_download
    from qlm_bench.config import dataset_repo_id, dataset_revision
    repo, rev, output = dataset_repo_id(repo_id), dataset_revision(revision), Path(output)
    prefix = f'benchmarks/{RELEASE}'
    get = lambda patterns: snapshot_download(repo, repo_type='dataset', revision=rev, local_dir=str(output),
                                             allow_patterns=patterns)
    get([f'{prefix}/manifest.json', f'{prefix}/protocol_snapshot.json', f'{prefix}/resource_registry_snapshot.json',
         f'{prefix}/cases/*.json'])
    bench = output / prefix
    manifest = json.loads((bench / 'manifest.json').read_text())
    selected = manifest['case_ids'] if not case_ids else list(case_ids)
    unknown = set(selected) - set(manifest['case_ids'])
    if unknown:
        raise ValueError(f'Unknown Standard100 cases: {sorted(unknown)}')
    registry = json.loads((bench / 'resource_registry_snapshot.json').read_text())
    identities = {json.loads((bench / 'cases' / f'{c}.json').read_text())['scene']['resource_identity'] for c in selected}
    rows = [registry['resources'][i] for i in sorted(identities)] + [registry['controller']]
    get([str(Path(row['manifest']).parent) + '/**' for row in rows])
    return {'resource_root': str(output.resolve()), 'suite': str(bench.resolve()), 'repo_id': repo, 'revision': rev,
            'cases': len(selected), 'scene_packs': len(identities)}
