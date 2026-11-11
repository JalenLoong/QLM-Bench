"""Corrective push_box demonstrations: physical traces, offline rendering, release (sft-v1/QLM-DATA-001, design 4.4).

Stages (each resumable; finished items are skipped):

  trace    for every accepted takeover segment: ``sft_v1.corrective_trace.record_segment`` (replay from the own state on the
           episode clock, bit-equal to the takeover record) -> RUN/traces/<uid>/, then the production ``audit_trace``.
  render   the unchanged production worker ``scripts/mujoco/synthesis/render_trace.py --formal-pilot`` (offline state replay,
           OSMesa, ego + task-centric 640x360 at 50 FPS; Raw + single-episode Canonical wam-quadruped-v2.1.0) ->
           RUN/episodes/<uid>/, then the comparisons of the production ``validate_output`` that need no rendition profile.
  package  hold out 8 scenes (fixed seed) as the corrective validation split, ``dataset_v2.merge`` -> RELEASE/canonical,
           RELEASE/raw/<uid> (hard links), RELEASE/pre_takeover (sidecars, not episodes), RELEASE/release.json; validates
           every Raw episode and the merged Canonical collection and asserts that no held-out scene is present.

Usage:
  corrective_release.py trace   --run RUN --gate GATE [--workers N]
  corrective_release.py render  --run RUN [--workers N]
  corrective_release.py package --run RUN --gate GATE --release DATA_ROOT/NAME
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[4]
QLM = Path(__file__).resolve().parents[2]
RELEASE_NAME = 'mujoco-push-corrective-r1-20261111-v1'
VALIDATION_SEED = 2026111101
VALIDATION_SCENES = 8
ROUTINE_COMMIT = 'a3785cbf408c8120c3cc77e42942ed3f26d3dba5'
PUSH100 = WORKSPACE / 'data/qlm_bench/push100-20261014-v1/canonical'
FFMPEG, FFPROBE = WORKSPACE / 'cache/tools/bin/ffmpeg', WORKSPACE / 'cache/tools/bin/ffprobe'
RENDER_ENVIRONMENT = {'MUJOCO_GL': 'osmesa', 'LD_LIBRARY_PATH': str(WORKSPACE / 'assets/mujoco/p0-v1/osmesa/root/usr/lib/x86_64-linux-gnu'),
                      'MESA_SHADER_CACHE_DIR': str(WORKSPACE / 'cache/mesa'), 'OMP_NUM_THREADS': '4', 'PYTHONPATH': str(QLM / 'src')}
# SFT5000 action normalizer (export provenance data.action_normalizer): q01 = offset - scale, q99 = offset + scale.
NORMALIZER_OFFSET = np.array([0.058469385951757366, -0.014171185027807964, -0.04378169694915417, 0.349012840911746, 0.11562707189470528, 0.17840446569025514])
NORMALIZER_SCALE = np.array([0.08413853824138635, 0.048443782050162545, 0.08683070188388227, 0.19649447090923786, 0.08942297752946615, 0.16226205222308632])


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path);path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.writing')
    tmp.write_text(json.dumps(value, indent=1, ensure_ascii=False, allow_nan=False) + '\n');tmp.replace(path)


def uid_of(segment):
    return f"{segment['case_id']}-corr-r1-{segment['point'].replace('=', '')}"


def load_segments(run):
    record = json.loads((run / 'takeover/segments.json').read_text())
    return record, record['segments']


def source_commit():
    dirty = subprocess.run(['git', '-C', str(QLM), 'status', '--porcelain', '--', 'src', 'scripts'], capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        raise SystemExit('Commit the source before producing release traces:\n' + dirty)
    return subprocess.run(['git', '-C', str(QLM), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ trace

def batch_identity(record, segment, gate, commit):
    from qlm_bench.sft_v1 import push_box_recovery
    source = json.loads((gate / 'g1/run-config.json').read_text())
    summary = json.loads((Path(record['_run']) / 'takeover/results' / f"{segment['segment_id']}.json").read_text())
    params = summary['expert']['recovery_params']
    params_sha = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
    if params != push_box_recovery.DEFAULT_PARAMS or summary['code']['files']['push_box_recovery.py'] != sha(Path(push_box_recovery.__file__)):
        raise SystemExit('Takeover was not produced by the frozen routine')
    return {'work_id': 'sft-v1/QLM-DATA-001', 'source_commit': commit, 'native_trace_profile': 'native-cpu-original-rambo-v1',
            'checkpoint_sha256': record['controller_sha256'],
            'corrective': {
                'release': RELEASE_NAME, 'round': 'r1', 'design': 'workspace docs/current/task-specific-sft-design-20261110.md section 4.4',
                'content': 'expert segment after the takeover only; the student half before the takeover is a sidecar and not an episode',
                'source_model': {'name': source['model'], 'method': 'streaming_with_anchor (quadruped OPD-v5.0), S900 EMA', 'nfe': '1/2',
                                 'seed': source['seed'], 'residual': source['residual'], 'inference_sha256': source['inference_sha256'],
                                 'student_manifest_sha256': source['student']['manifest_sha256'], 'student_adapter_sha256': source['student']['adapter_sha256'],
                                 'successful_updates': source['student']['successful_updates'], 'variant': source['student']['variant']},
                'scene': {'case_id': segment['case_id'], 'base_release_split': 'train', 'canonical_episode_index': segment['canonical_episode_index']},
                'takeover': {'point': segment['point'], 'absolute_tick': segment['takeover_tick'], 'absolute_time_s': segment['takeover_s'],
                             'rule': record['rule'], 'points_sha256': record['points_sha256'], 'split_sha256': record['split_sha256'],
                             'own_state_sha256': segment['state_sha256'], 'at_takeover': segment['at_takeover'], 'gate_run': record['gate_run']},
                'routine': {'module': 'qlm_bench.sft_v1.push_box_recovery', 'version': params['version'], 'commit': ROUTINE_COMMIT,
                            'params_sha256': params_sha, 'file_sha256': summary['code']['files']['push_box_recovery.py']},
                'physics': 'native MuJoCo CPU, float64', 'controller': 'original RAMBO model_2000', 'controller_sha256': record['controller_sha256'],
                'pre_takeover_sidecar': f"pre_takeover/{segment['case_id']}.json"}}


def _trace_worker(args):
    jobs, run, gate, commit = args
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    from qlm_bench.backends.mujoco.rendition import audit_trace
    from qlm_bench.sft_v1 import corrective_trace, takeover
    run, gate = Path(run), Path(gate)
    record, _ = load_segments(run);record['_run'] = str(run)
    cache = takeover.RuntimeCache(record['controller_checkpoint'])
    done = []
    try:
        for segment in jobs:
            uid = uid_of(segment)
            segment = {**segment, 'case': str(gate / 'cases' / f"{segment['case_id']}.json")}
            result = corrective_trace.record_segment(cache, segment, run / 'takeover/results' / segment['segment_id'], run / 'traces' / uid,
                                                     batch_identity=batch_identity(record, segment, gate, commit), uid=uid)
            audit = audit_trace(run / 'traces' / uid)
            result['audit'] = {k: audit[k] for k in ('manifest_sha256', 'trajectory_sha256', 'source_identity_sha256', 'quality', 'n_actions')}
            write_json(run / 'trace-results' / f'{uid}.json', result)
            print(json.dumps({'uid': uid, 'n_actions': result['n_actions'], 'wall_s': round(result['wall_s'], 1)}), flush=True)
            done.append(uid)
    finally:
        cache.close()
    return done


def stage_trace(a):
    run, gate = a.run.resolve(), a.gate.resolve()
    commit = source_commit()
    _, segments = load_segments(run)
    pending = [s for s in segments if not (run / 'trace-results' / f'{uid_of(s)}.json').exists()]
    for s in pending:  # A trace directory without a result is an interrupted attempt.
        if (run / 'traces' / uid_of(s)).exists():
            raise SystemExit(f'Unfinished trace directory present: {uid_of(s)}')
    groups = {}
    for s in pending:
        groups.setdefault(s['case_id'], []).append(s)
    print(f'{len(segments)} segments, {len(pending)} to trace, source {commit[:12]}', flush=True)
    tasks = [(g, str(run), str(gate), commit) for g in groups.values()]
    if a.workers <= 1:
        for t in tasks:
            _trace_worker(t)
    else:
        import multiprocessing as mp
        with mp.get_context('spawn').Pool(a.workers, maxtasksperchild=6) as pool:
            for _ in pool.imap_unordered(_trace_worker, tasks):
                pass


# ------------------------------------------------------------------ render

def formal_metadata(segment, uid):
    """The base release's admitted metadata of the scene (asset, appearance, seed, condition ids), for this episode."""
    base = json.loads((PUSH100 / 'metadata' / segment['case_id'] / 'provenance.json').read_text())['formal_metadata']
    if base['episode_uid'] != segment['case_id'] or base['split'] != 'train' or base['task_id'] != 'push_box':
        raise SystemExit(f"{segment['case_id']} is not a train scene of the base release")
    return {**base, 'episode_uid': uid}


def check_episode(run, segment, uid):
    """What the production validate_output compares, without a rendition profile: render-only producer, Raw/Canonical lineage,
    and actions / states / terminal equal to the physical trace; plus actions equal to the takeover record."""
    import pyarrow.parquet as pq
    from qlm_bench.backends.mujoco.trace import verify_trace
    from qlm_bench.compatibility.dataset_v2.validation import COLUMNS
    output = run / 'episodes' / uid
    result = json.loads((output / 'result.json').read_text());producer = json.loads((output / 'producer.json').read_text())
    if not (result.get('passed') is True and producer.get('passed') is True and result.get('physics_reexecuted') is False
            and not result.get('controller_loaded') and not result.get('WAM_loaded') and not result.get('physics_owner_loaded')):
        raise ValueError('Incomplete/invalid render-only producer')
    raw_prov = json.loads((output / 'raw' / uid / 'metadata/provenance.json').read_text())
    canon_prov = json.loads((output / 'canonical/metadata/provenance.json').read_text())
    if raw_prov != canon_prov:
        raise ValueError('Raw/Canonical lineage differs')
    manifest, _, telemetry, commands, terminal = verify_trace(run / 'traces' / uid)
    table = pq.read_table(output / 'canonical/data/chunk-000/episode_000000.parquet')
    action = np.asarray(table['action'].to_pylist(), np.float32)
    np.testing.assert_array_equal(action, np.asarray([c['executed'] for c in commands], np.float32))
    with np.load(run / 'takeover/results' / f"{segment['segment_id']}.npz") as z:
        np.testing.assert_array_equal(action, z['requested'].astype(np.float32))
    for key, spec in COLUMNS.items():
        if not key.startswith(('observation.state.', 'task.')):
            continue
        expected = np.asarray([b['state'][key] for b in telemetry['boundaries'][:-1]], dtype=spec['dtype'])
        observed = np.asarray(table[key].to_pylist(), dtype=spec['dtype']).reshape(expected.shape)
        np.testing.assert_array_equal(observed, expected, err_msg='Physical state altered: ' + key)
    contract = json.loads((output / 'canonical/meta/contract.json').read_text())
    episode = contract['episodes'][0]
    if episode['terminal']['state'] != terminal['state'] or episode['length'] != manifest['n_actions'] or episode['status'] != 'success':
        raise ValueError('Terminal state or length changed')
    corrective = canon_prov['source_identity']['corrective']
    if (corrective['takeover']['own_state_sha256'] != segment['state_sha256'] or corrective['scene']['case_id'] != segment['case_id']
            or canon_prov['formal_metadata']['split'] != 'train' or canon_prov['backend']['physics'] != 'native'):
        raise ValueError('Provenance does not describe this segment')
    oor = (action[:, :6] < NORMALIZER_OFFSET - NORMALIZER_SCALE) | (action[:, :6] > NORMALIZER_OFFSET + NORMALIZER_SCALE)
    return {'uid': uid, 'segment_id': segment['segment_id'], 'case_id': segment['case_id'], 'point': segment['point'], 'passed': True,
            'rows': int(len(action)), 'duration_s': len(action) * 0.02, 'takeover_s': segment['takeover_s'],
            'end_absolute_s': segment['takeover_s'] + len(action) * 0.02, 'horizon_s': 24.0,
            'out_of_range_by_dim': oor.sum(0).tolist(), 'out_of_range_elements': int(oor.sum()),
            'raw_validation': json.loads((output / 'raw' / uid / 'raw-validation.json').read_text())['contract_valid'],
            'canonical_validation': json.loads((output / 'canonical-validation.json').read_text())['contract_valid'],
            'gl': result['GL'], 'render_wall_s': result['wall_s'], 'trace_manifest_sha256': sha(run / 'traces' / uid / 'manifest.json'),
            'canonical_inventory_sha256': sha(output / 'canonical/meta/checksums.json'), 'original_numerical_states_actions_terminal_preserved': True}


def _render_one(run, segment):
    uid = uid_of(segment)
    accepted = run / 'episode-results' / f'{uid}.json'
    if accepted.exists():
        return uid, 'skipped'
    output = run / 'episodes' / uid
    if output.exists():   # an interrupted attempt of this stage; set aside, never deleted
        aside = run / 'superseded' / uid
        k = 0
        while (aside.parent / f'{aside.name}-{k}').exists():
            k += 1
        aside.parent.mkdir(parents=True, exist_ok=True);output.rename(aside.parent / f'{aside.name}-{k}')
    meta = run / 'render-inputs' / f'{uid}.json'
    write_json(meta, formal_metadata(segment, uid))
    manifest = json.loads((run / 'traces' / uid / 'manifest.json').read_text())
    log = run / 'logs' / f'render-{uid}.log';log.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(QLM / 'scripts/mujoco/synthesis/render_trace.py'), '--trace', str(run / 'traces' / uid),
               '--model', manifest['scene']['model'], '--output', str(output), '--episode-uid', uid,
               '--ffmpeg', str(FFMPEG), '--ffprobe', str(FFPROBE), '--formal-pilot', '--metadata', str(meta)]
    env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'MUJOCO_GL', 'PYOPENGL_PLATFORM')}
    env.update(RENDER_ENVIRONMENT)
    with log.open('w') as f:
        code = subprocess.run(command, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
    if code:
        return uid, f'render failed ({code}), see {log}'
    write_json(accepted, check_episode(run, segment, uid))
    return uid, 'ok'


def stage_render(a):
    run = a.run.resolve()
    _, segments = load_segments(run)
    missing = [uid_of(s) for s in segments if not (run / 'trace-results' / f'{uid_of(s)}.json').exists()]
    if missing:
        raise SystemExit(f'{len(missing)} traces missing')
    from concurrent.futures import ThreadPoolExecutor
    failed = []
    with ThreadPoolExecutor(a.workers) as pool:
        for uid, status in pool.map(lambda s: _render_one(run, s), segments):
            print(uid, status, flush=True)
            if status not in ('ok', 'skipped'):
                failed.append(uid)
    if failed:
        raise SystemExit(f'{len(failed)} episodes failed: {failed}')


# ------------------------------------------------------------------ package

def stage_package(a):
    from qlm_bench.compatibility.dataset_v2.media import MediaTools
    from qlm_bench.compatibility.dataset_v2.merge import merge
    from qlm_bench.compatibility.dataset_v2.validation import validate_canonical, validate_raw
    run, gate, release = a.run.resolve(), a.gate.resolve(), a.release.resolve()
    if release.name != RELEASE_NAME or release.exists():
        raise SystemExit('Release directory must be new and carry the release name')
    record, segments = load_segments(run)
    results = {uid_of(s): json.loads((run / 'episode-results' / f'{uid_of(s)}.json').read_text()) for s in segments}
    if not all(r['passed'] for r in results.values()):
        raise SystemExit('Unaccepted episode present')
    base_split = json.loads((PUSH100 / 'meta/split.json').read_text())['episodes']
    train_scenes, held_out = set(base_split['train']), set(base_split['validation']) | set(base_split['test'])
    gate_split = json.loads((gate / 'split.json').read_text())
    if held_out != set(gate_split['held_out_excluded']) or len(train_scenes) != 80:
        raise SystemExit('Base release split differs from the gate run')
    scenes = sorted({s['case_id'] for s in segments})
    if not set(scenes) <= train_scenes or set(scenes) & held_out:
        raise SystemExit('A segment comes from a scene outside the 80 train scenes')
    validation = sorted(random.Random(VALIDATION_SEED).sample(scenes, VALIDATION_SCENES))
    order = sorted(segments, key=lambda s: (s['case_id'] in validation, s['case_id'], s['point']))
    entries = [{'canonical': str(run / 'episodes' / uid_of(s) / 'canonical'), 'split': 'validation' if s['case_id'] in validation else 'train'} for s in order]
    tools = MediaTools(str(FFMPEG), str(FFPROBE))
    partial = release.with_name(release.name + '.writing')
    if partial.exists():
        raise SystemExit(f'Unfinished release attempt present: {partial}')
    partial.mkdir(parents=True)
    merged = merge(entries, partial / 'canonical', tools, 'sft-v1/QLM-DATA-001')
    raw_reports = {}
    for s in order:   # Raw views: hard links of the rendered Raw episodes, as the base release does.
        uid = uid_of(s);source = run / 'episodes' / uid / 'raw' / uid
        for f in sorted(p for p in source.rglob('*') if p.is_file()):
            target = partial / 'raw' / uid / f.relative_to(source);target.parent.mkdir(parents=True, exist_ok=True)
            os.link(f, target)
        raw_reports[uid] = validate_raw(partial / 'raw' / uid, tools=tools)
    shutil.copytree(run / 'pre-takeover', partial / 'pre_takeover')
    sidecars = json.loads((partial / 'pre_takeover/index.json').read_text())
    for entry in sidecars['cases']:
        if sha(partial / 'pre_takeover' / entry['json']) != entry['json_sha256'] or sha(partial / 'pre_takeover' / f"{entry['case_id']}.npz") != entry['arrays_sha256']:
            raise SystemExit('Sidecar copy differs')
    if sorted(e['case_id'] for e in sidecars['cases']) != scenes:
        raise SystemExit('Sidecars do not cover the source rollouts')
    # ---- nothing from a held-out scene anywhere in the release
    split = json.loads((partial / 'canonical/meta/split.json').read_text())['episodes']
    contract = json.loads((partial / 'canonical/meta/contract.json').read_text())
    uids = [e['episode_uid'] for e in contract['episodes']]
    by_uid = {uid_of(s): s for s in segments}
    names = [p.name for p in partial.rglob('*')]
    held_tokens = [f'push100-20261014-{i:03d}' for i in range(81, 101)]
    if sorted(held_tokens) != sorted(held_out):
        raise SystemExit('Held-out scene ids are not 081-100')
    leaks = [n for n in names if any(t in n for t in held_tokens)]
    for uid in uids:
        prov = json.loads((partial / 'canonical/metadata' / uid / 'provenance.json').read_text())
        scene = prov['source_identity']['corrective']['scene']['case_id']
        if scene != by_uid[uid]['case_id'] or scene not in train_scenes or scene in held_out or prov['formal_metadata']['split'] != 'train':
            leaks.append(uid)
    if leaks or set(uids) != set(by_uid) or set(split['train']) | set(split['validation']) != set(uids) or set(split['train']) & set(split['validation']):
        raise SystemExit(f'Held-out or inconsistent content: {leaks[:5]}')
    if {by_uid[u]['case_id'] for u in split['validation']} != set(validation) or {by_uid[u]['case_id'] for u in split['train']} & set(validation):
        raise SystemExit('Validation split is not whole scenes')
    recheck = validate_canonical(partial / 'canonical', tools=tools)
    info = json.loads((partial / 'canonical/meta/info.json').read_text())
    rows = np.array([results[u]['rows'] for u in uids]);oor = np.array([results[u]['out_of_range_by_dim'] for u in uids]).sum(0)
    takeover = np.array([by_uid[u]['takeover_s'] for u in uids])
    summary = {
        'schema': 'qlm-sft-v1-corrective-release-v1', 'release': RELEASE_NAME, 'work_id': 'sft-v1/QLM-DATA-001', 'dataset_schema_version': recheck['dataset_schema_version'],
        'design': 'workspace docs/current/task-specific-sft-design-20261110.md section 4.4', 'source_commit': contract['episodes'][0]['source_commit'],
        'task_text': contract['episodes'][0]['task_text'], 'episodes': len(uids), 'frames': int(info['total_frames']), 'splits': info['splits'],
        'source_rollouts': len(scenes), 'points': {p: sum(by_uid[u]['point'] == p for u in uids) for p in ('A', 'B', 'A=B')},
        'validation': {'unit': 'scene', 'seed': VALIDATION_SEED, 'method': f'random.Random({VALIDATION_SEED}).sample(sorted scenes with corrective segments, {VALIDATION_SCENES})',
                       'scenes': validation, 'episodes': split['validation']},
        'train_scenes': sorted(set(scenes) - set(validation)),
        'episode_rows': {'median': float(np.median(rows)), 'min': int(rows.min()), 'max': int(rows.max()), 'duration_s_median': float(np.median(rows) * 0.02)},
        'takeover_time_s': {'median': float(np.median(takeover)), 'min': float(takeover.min()), 'max': float(takeover.max())},
        'action_out_of_range': {'normalizer': 'SFT5000 export provenance data.action_normalizer, q01-q99, first 6 native9 dims',
                                'by_dim': {k: int(v) for k, v in zip(('vx', 'vy', 'yaw_rate', 'fl_x', 'fl_y', 'fl_z'), oor)},
                                'commands': int(rows.sum()), 'element_share': float(oor.sum() / (6 * rows.sum()))},
        'held_out': {'scenes_excluded': sorted(held_out), 'present': False, 'base_release': str(PUSH100), 'base_split_sha256': sha(PUSH100 / 'meta/split.json')},
        'routine': json.loads((partial / 'canonical/metadata' / uids[0] / 'provenance.json').read_text())['source_identity']['corrective']['routine'],
        'source_model': json.loads((partial / 'canonical/metadata' / uids[0] / 'provenance.json').read_text())['source_identity']['corrective']['source_model'],
        'render': {'mode': 'offline_state_replay', 'backend': 'osmesa', 'gl': results[uids[0]]['gl'], 'views': ['ego', 'task_centric'], 'size': [640, 360], 'fps': 50},
        'gate': {'run': str(gate), 'split_sha256': record['split_sha256'], 'points_sha256': record['points_sha256']},
        'validation_results': {'canonical': recheck['contract_valid'], 'canonical_video': recheck['video_validation'], 'merge': merged['contract_valid'],
                               'raw_episodes_valid': sum(r['contract_valid'] for r in raw_reports.values()), 'raw_episodes': len(raw_reports)},
        'canonical_inventory_sha256': sha(partial / 'canonical/meta/checksums.json'),
        'pre_takeover': {'path': 'pre_takeover/', 'cases': len(sidecars['cases']), 'index_sha256': sha(partial / 'pre_takeover/index.json'), 'in_sft_pool': False},
        'episodes_table': [{'episode_index': i, 'episode_uid': u, 'split': 'validation' if u in split['validation'] else 'train', 'scene': by_uid[u]['case_id'],
                            'point': by_uid[u]['point'], 'takeover_s': by_uid[u]['takeover_s'], 'rows': results[u]['rows'],
                            'out_of_range_elements': results[u]['out_of_range_elements']} for i, u in enumerate(uids)],
        'published': False}
    write_json(partial / 'release.json', summary)
    partial.rename(release)
    print(json.dumps({k: summary[k] for k in ('release', 'episodes', 'frames', 'splits', 'validation_results')}, ensure_ascii=False), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='stage', required=True)
    for name in ('trace', 'render', 'package'):
        s = sub.add_parser(name);s.add_argument('--run', type=Path, required=True)
        if name != 'render':
            s.add_argument('--gate', type=Path, required=True)
        if name != 'package':
            s.add_argument('--workers', type=int, default=1)
        else:
            s.add_argument('--release', type=Path, required=True)
    a = p.parse_args()
    {'trace': stage_trace, 'render': stage_render, 'package': stage_package}[a.stage](a)


if __name__ == '__main__':
    main()
