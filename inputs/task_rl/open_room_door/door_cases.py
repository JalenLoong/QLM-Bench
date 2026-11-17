"""EvalCase records for the 80 open_room_door train scenes used by Task RL.

Same recipe as the Standard100 preparation (``qlm_bench.benchmark.suite.prepare``): the published physical
snapshot bundle + source trace manifest of the door release in the demonstration catalogue give the initial
qpos/qvel, controller case seed, goal overlay, Standard100 horizon and policy camera geometry. As a recipe check
the 10 test scenes are rebuilt too and compared field by field (except provenance and validation status) with the
Standard100 case files; they are not written. Validation and test scenes never enter the output.

Maintainer tool, kept to document how the shipped cases were built. It reads each episode's scene path from the
dataset's source-trace manifests (recorded on the machine that produced the demonstrations) and checks the scene
against the original scene identity, so it only runs where the original scene packs are available; the released
cases (cases/, cases-index.json) were rebuilt from it and then moved to the neutral task_rl/ layout.

    python inputs/task_rl/open_room_door/door_cases.py --payload <dataset snapshot> \
        --standard100 <resource_root>/benchmarks/mujoco-standard-test100-v1 --out <dir>/cases
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

PAYLOAD = BENCH = None   # set from --payload / --standard100
TASK = 'open_room_door'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def build(entry, episode, frozen):
    from qlm_bench.benchmark.suite import HORIZONS, SEMANTICS, CONTROLLER, RUNTIME
    from qlm_bench.backends.mujoco.resources import resource_closure
    from qlm_bench.tasks.prompts import current_instruction_profile
    from qlm_bench.benchmark import EvalCase
    from qlm_bench.contracts.policy import ObservationProfile
    from qlm_bench.contracts.policy.physical import CAMERAS, ROOT_FIELDS
    ref = entry['ref']
    bpath = PAYLOAD / episode['snapshot_bundle']
    tpath = bpath.parent / 'source-trace-manifest.json'
    if sha(bpath) != episode['snapshot_bundle_sha256'] or sha(tpath) != episode['source_trace_manifest_sha256']:
        raise ValueError('Snapshot provenance changed: ' + episode['episode_uid'])
    bundle, trace = read(bpath), read(tpath)
    model = Path(trace['scene']['model'])
    closure = resource_closure(model, require_portable=True)
    if closure['identity'] != bundle['model_identity']:
        raise ValueError('Scene model identity differs from bundle: ' + episode['episode_uid'])
    p = current_instruction_profile(read(model.with_suffix('.task.json')))
    identity = closure['identity']
    observation = ObservationProfile('qlm-measured-root-link-dual-rgb-360p-v1', CAMERAS, ROOT_FIELDS, True, SEMANTICS)
    initial = deepcopy(trace['scene']['initial_state'])
    initial.pop('schema'); initial.pop('model_identity'); initial['simulation_time_ns'] = 0
    case = EvalCase(episode['episode_uid'], entry['task'], p['asset_profile'], entry['instruction'], observation,
                    {p['asset_id']: identity}, initial,
                    {'position': trace['scene'].get('canonical_goal_position', p['canonical_goal_position']), 'task_profile': p['asset_profile']},
                    {'resource_identity': identity, 'horizon_s': HORIZONS[entry['task']], 'render_backend': 'egl',
                     'goal_overlay': {k: trace['scene'][k] for k in ('goal_x', 'goal_y', 'canonical_goal_position') if k in trace['scene']},
                     'difficulty': episode['difficulty'], 'canonical_episode_index': episode['canonical_episode_index']},
                    frozen['policy_camera_geometry'], trace['scene']['seed'], CONTROLLER, RUNTIME,
                    {'kind': 'explicit_published_initial_state', 'physics_steps_during_reset': 0, 'clear_controller_history': True},
                    {'source_ref': ref, 'source_episode': episode['episode_uid'], 'source_trace_manifest_sha256': sha(tpath),
                     'snapshot_bundle_sha256': sha(bpath), 'evidence_kind': 'declared_not_verified'}, 'draft')
    return json.loads(json.dumps(case.record())), model, identity, trace


def main():
    from qlm_bench.contracts.rgb_profiles import dataset_profile, RGB_360
    from qlm_bench.data.lerobot.validation import PROFILE
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--payload', type=Path, required=True, help='Local snapshot of the QLM-Bench HF dataset (releases/, physical/)')
    p.add_argument('--standard100', type=Path, required=True, help='benchmarks/mujoco-standard-test100-v1 directory')
    a = p.parse_args()
    global PAYLOAD, BENCH
    PAYLOAD, BENCH = a.payload, a.standard100
    catalog = read(Path(__file__).resolve().parents[3] / 'src/qlm_bench/data/spec/catalog.json')
    entry = next(e for e in catalog['demonstrations'] if e['task'] == TASK)
    release_path = PAYLOAD / entry['ref']['manifest']
    release = read(release_path)
    frozen = dataset_profile(PROFILE, RGB_360)
    a.out.mkdir(parents=True, exist_ok=False)
    checks, index = [], []
    by_uid = {x['episode_uid']: x for x in release['episodes']}
    for uid in sorted(release['split']['test']):
        built, *_ = build(entry, by_uid[uid], frozen)
        frozen_case = read(BENCH / 'cases' / f'{uid}.json')
        diff = sorted(k for k in set(built) | set(frozen_case) if k not in ('provenance', 'validation_status') and built.get(k) != frozen_case.get(k))
        checks.append({'case_id': uid, 'rebuilt_equals_frozen_except_provenance': not diff, 'differing_fields': diff})
        if diff:
            raise ValueError(f'Recipe check failed for {uid}: {diff}')
    train = sorted((by_uid[u] for u in release['split']['train']), key=lambda x: x['canonical_episode_index'])
    if len(train) != 80:
        raise ValueError('Expected 80 train episodes')
    held_out = set(release['split']['validation']) | set(release['split']['test'])
    for episode in train:
        if episode['episode_uid'] in held_out or episode['split'] != 'train':
            raise ValueError('Held-out scene refused')
        record, model, identity, trace = build(entry, episode, frozen)
        path = a.out / f"{episode['episode_uid']}.json"
        path.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
        index.append({'case_id': episode['episode_uid'], 'task_id': TASK, 'split': 'train', 'difficulty': episode['difficulty'],
                      'canonical_episode_index': episode['canonical_episode_index'], 'model_path': str(model), 'resource_identity': identity,
                      'case_seed': record['seed'], 'horizon_s': record['scene']['horizon_s'], 'case_sha256': sha(path),
                      'production_trace': str(Path(trace['scene']['model']).parents[2] / 'traces' / (trace['scene']['candidate_id'])),
                      'source': 'built from published snapshot bundle (suite.prepare recipe)'})
    registry = read(BENCH / 'resource_registry_snapshot.json')
    controller = BENCH.parent.parent / registry['controller']['entrypoint']
    (a.out.parent / 'cases-index.json').write_text(json.dumps({'cases': index, 'recipe_checks_on_test_cases': checks,
        'held_out_never_written': sorted(held_out), 'release_manifest': str(release_path), 'release_manifest_sha256': sha(release_path),
        'controller_checkpoint': str(controller), 'controller_sha256': sha(controller), 'standard100_bench': str(BENCH)}, indent=1) + '\n')
    print(len(index), 'train cases;', sum(c['rebuilt_equals_frozen_except_provenance'] for c in checks), '/10 test recipe checks passed')


if __name__ == '__main__':
    main()
