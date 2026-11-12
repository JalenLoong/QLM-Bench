"""Corrective sweep_block_to_zone demonstrations from takeover point B: segments, traces, offline rendering, release (sft-v1/QLM-DATA-002).

Same chain as the corrective push_box release (``corrective_release.py``, sft-v1/QLM-DATA-001), for the frozen sweep recovery routine
``sweep_recovery-v1``. One segment per sweep train scene: the expert half after the takeover at point B of the student's rollout (foot
lowered at the pushing face, behind its centre, block not yet touched). Unrecoverable starts are dropped and recorded, nothing is tuned.

Stages (each resumable; finished items are skipped):

  segments  for the 80 train scenes: point B of GATE/points.json, the finished frozen-E* takeover of that state taken from the given
            result directories (hashes of the routine file, its parameters and the start state are checked against the frozen ones;
            success, no fall, within the horizon), copied to RUN/takeover/results/ -> RUN/takeover/segments.json (accepted and
            discarded, with the reason).
  trace     ``sft_v1.corrective_trace.record_segment`` (reset, restore the own state, open-loop replay on the episode clock,
            bit-equal to the takeover record) -> RUN/traces/<uid>/, then the production ``audit_trace``.
  render    the unchanged production worker ``scripts/mujoco/synthesis/render_trace.py --formal-pilot`` (offline state replay,
            OSMesa, ego + task-centric 640x360 at 50 FPS, observer only in Raw) -> RUN/episodes/<uid>/, then the comparisons of the
            production ``validate_output`` that need no rendition profile.
  package   hold out 8 scenes (fixed seed) as the corrective validation split, ``dataset_v2.merge`` -> RELEASE/canonical,
            RELEASE/raw/<uid> (hard links), RELEASE/pre_takeover (sidecars, not episodes), RELEASE/release.json; validates every Raw
            episode and the merged Canonical collection and asserts that no held-out scene is present.
  verify    the existing validation CLI on the released Canonical collection and every Raw episode, a text scan for held-out scene
            ids, provenance/action checks per episode and frame 0 against the student's frame at the takeover tick.

The pre-takeover sidecars are written by ``corrective_sidecar.py`` (unchanged) from RUN/takeover/segments.json.

Usage:
  sweep_corrective_release.py segments --run RUN --gate GATE --prep PREP --results DIR [DIR ...]
  sweep_corrective_release.py trace    --run RUN [--workers N]
  sweep_corrective_release.py render   --run RUN [--workers N]
  sweep_corrective_release.py package  --run RUN --release DATA_ROOT/NAME
  sweep_corrective_release.py verify   --run RUN --release DATA_ROOT/NAME
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corrective_release import FFMPEG, FFPROBE, NORMALIZER_OFFSET, NORMALIZER_SCALE, QLM, RENDER_ENVIRONMENT, WORKSPACE, sha, write_json  # noqa: E402

TASK = 'sweep_block_to_zone'
WORK_ID = 'sft-v1/QLM-DATA-002'
RELEASE_NAME = 'mujoco-sweep-corrective-r1-20261112-v1'
POINT = 'B'
VALIDATION_SEED = 2026111201
VALIDATION_SCENES = 8
ROUTINE_COMMIT = 'edd651eda7c1f602f8cd5cff474d15e054e9c4ce'
ROUTINE_FILE = 'src/qlm_bench/sft_v1/sweep_recovery.py'
BASE = WORKSPACE / 'data/qlm_bench/remaining-six-20261016-v1/sweep_block_to_zone/canonical'
HORIZON_S = 40.0
DESIGN = 'workspace docs/current/task-specific-sft-design-20261110.md sections 4.4 and 7; workspace docs/work/active/WS-TSFT-001/plan.md section 8'


def uid_of(segment):
    return f"{segment['case_id']}-corr-r1-{segment['point']}"


def load_segments(run):
    record = json.loads((run / 'takeover/segments.json').read_text())
    return record, record['segments']


def source_commit():
    dirty = subprocess.run(['git', '-C', str(QLM), 'status', '--porcelain', '--', 'src', 'scripts'], capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        raise SystemExit('Commit the source before producing release traces:\n' + dirty)
    return subprocess.run(['git', '-C', str(QLM), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()


def frozen_routine():
    """Version, parameters and file hash of the frozen routine; the file in the checkout must be the one of the frozen commit."""
    from qlm_bench.sft_v1 import sweep_recovery
    blob = subprocess.run(['git', '-C', str(QLM), 'show', f'{ROUTINE_COMMIT}:{ROUTINE_FILE}'], capture_output=True, check=True).stdout
    file_sha = hashlib.sha256(blob).hexdigest()
    if file_sha != sha(QLM / ROUTINE_FILE):
        raise SystemExit('sweep_recovery.py in the checkout differs from the frozen commit')
    return {'version': sweep_recovery.VERSION, 'params': sweep_recovery.DEFAULT_PARAMS,
            'params_sha256': sweep_recovery.params_sha256(sweep_recovery.DEFAULT_PARAMS), 'file_sha256': file_sha}


# ------------------------------------------------------------------ segments

def stage_segments(a):
    run, gate, prep = a.run.resolve(), a.gate.resolve(), a.prep.resolve()
    out = run / 'takeover'
    if (out / 'segments.json').exists():
        raise SystemExit('segments.json already written')
    frozen = frozen_routine()
    split = json.loads((gate / 'split.json').read_text())
    points = json.loads((gate / 'points.json').read_text())
    index = json.loads((prep / 'cases-index.json').read_text())
    cases = {c['case_id']: c for c in index['cases']}
    failures = {f['case_id']: f for f in points['failures']}
    held_out = set(split['held_out_excluded'])
    wanted = sorted(split['exploration'] + split['gate'])
    base_split = json.loads((BASE / 'meta/split.json').read_text())['episodes']
    if sorted(failures) != wanted or len(wanted) != 80 or sorted(base_split['train']) != wanted or held_out != set(base_split['validation']) | set(base_split['test']):
        raise SystemExit('points.json, split.json and the base release split do not describe the same 80 train scenes')
    segments, discarded = [], []
    for case_id in wanted:
        case = cases[case_id]
        if case['split'] != 'train' or case['task_id'] != TASK or case_id in held_out:
            raise SystemExit(f'{case_id} is not a sweep train scene')
        case_path = prep / 'cases' / f'{case_id}.json'
        if sha(case_path) != case['case_sha256']:
            raise SystemExit(f'{case_id}: EvalCase hash mismatch')
        pt = failures[case_id].get(POINT)
        sid = f'{case_id}-{POINT}'
        if pt is None:
            discarded.append({'segment_id': sid, 'case_id': case_id, 'reason': f'no point {POINT} in points.json'})
            continue
        if sha(pt['state']) != pt['state_sha256'] or pt['tick'] % 160 or pt['tick'] != (pt['chunk'] + 1) * 160:
            raise SystemExit(f'{case_id}: start state does not match points.json')
        short = f'{case_id[-3:]}-{POINT}'
        found = [d for d in a.results if (d / f'{short}.json').exists()]
        if not found:
            raise SystemExit(f'{case_id}: no takeover result; run the frozen routine from this state first')
        stem = found[0].resolve() / short
        summary = json.loads(stem.with_suffix('.json').read_text())
        expert, outcome, start = summary['expert'], summary['outcome'], summary['start']
        if not (expert['kind'] == 'sweep_recovery' and expert['version'] == frozen['version'] and expert['recovery_params'] == frozen['params']
                and expert['recovery_params_sha256'] == frozen['params_sha256'] and summary['code']['files']['sweep_recovery.py'] == frozen['file_sha256']
                and start['state_sha256'] == pt['state_sha256'] and start['absolute_tick'] == pt['tick'] and summary['case_sha256'] == case['case_sha256']
                and summary['controller_sha256'] == index['controller_sha256'] and sha(stem.with_suffix('.npz')) == summary['arrays_sha256']):
            raise SystemExit(f'{case_id}: the takeover result was not produced by the frozen routine from this start state')
        terminal = outcome['terminal'] or {}
        accepted = bool(outcome['success'] and not outcome['fallen'] and terminal.get('reason') == 'task_success' and outcome['end_s'] <= outcome['horizon_s'] == HORIZON_S)
        common = {'segment_id': sid, 'case_id': case_id, 'point': POINT, 'takeover_tick': pt['tick'], 'takeover_s': pt['boundary_s'],
                  'takeover_source': str(stem.with_suffix('.json')), 'takeover_source_sha256': sha(stem.with_suffix('.json')),
                  'at_takeover': {k: pt[k] for k in ('foot_lateral_cm', 'block_yaw_change_deg', 'base_offset_cm')},
                  'origin_set': 'exploration' if case_id in split['exploration'] else 'gate'}
        if not accepted:
            discarded.append({**common, 'reason': terminal.get('reason', 'no terminal'), 'fallen': bool(outcome['fallen']), 'end_s': outcome['end_s']})
            continue
        for suffix in ('.json', '.npz'):
            target = out / 'results' / (sid + suffix)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(stem.with_suffix(suffix), target)
        segments.append({**common, 'takeover_chunk': pt['chunk'], 'state': pt['state'], 'state_sha256': pt['state_sha256'],
                         'history': pt['record'], 'history_sha256': pt['record_sha256'], 'groups': pt['groups'],
                         'case': str(case_path), 'canonical_episode_index': case['canonical_episode_index'], 'difficulty': case['difficulty'],
                         'entry_decision': expert['entry']['decision'], 'end_s': outcome['end_s'], 'commands': outcome['commands']})
    write_json(out / 'segments.json', {
        'schema': 'qlm-sft-v1-corrective-segments-v1', 'task_id': TASK, 'work_id': WORK_ID, 'gate_run': str(gate), 'prep_run': str(prep),
        'split_sha256': sha(gate / 'split.json'), 'points_sha256': sha(gate / 'points.json'), 'cases_index_sha256': sha(prep / 'cases-index.json'),
        'controller_checkpoint': index['controller_checkpoint'], 'controller_sha256': index['controller_sha256'],
        'run_config': str(prep / 'starts/run-config.json'), 'run_config_sha256': sha(prep / 'starts/run-config.json'),
        'rule': points['rules'][POINT], 'point': POINT,
        'routine': {'version': frozen['version'], 'commit': ROUTINE_COMMIT, 'params_sha256': frozen['params_sha256'], 'file_sha256': frozen['file_sha256']},
        'acceptance': 'task_success terminal of the frozen routine, no fall, within the 40 s horizon; anything else is discarded, nothing is tuned',
        'scenes': len(wanted), 'segments': segments, 'discarded': discarded})
    print(len(wanted), 'scenes,', len(segments), 'accepted segments,', len(discarded), 'discarded')


# ------------------------------------------------------------------ trace

def batch_identity(record, segment, run, commit):
    from qlm_bench.sft_v1 import sweep_recovery
    source = json.loads(Path(record['run_config']).read_text())
    summary = json.loads((run / 'takeover/results' / f"{segment['segment_id']}.json").read_text())
    expert = summary['expert']
    if (expert['recovery_params'] != sweep_recovery.DEFAULT_PARAMS or summary['code']['files']['sweep_recovery.py'] != sha(Path(sweep_recovery.__file__))
            or record['routine']['file_sha256'] != summary['code']['files']['sweep_recovery.py']):
        raise SystemExit('Takeover was not produced by the frozen routine')
    return {'work_id': WORK_ID, 'source_commit': commit, 'native_trace_profile': 'native-cpu-original-rambo-v1',
            'checkpoint_sha256': record['controller_sha256'],
            'corrective': {
                'release': RELEASE_NAME, 'round': 'r1', 'design': DESIGN,
                'content': 'expert segment after the takeover only; the student half before the takeover is a sidecar and not an episode',
                'source_model': {'name': source['model'], 'method': 'streaming_with_anchor (quadruped OPD-v5.0), S900 EMA', 'nfe': '1/2',
                                 'seed': source['seed'], 'residual': source['residual'], 'inference_sha256': source['inference_sha256'],
                                 'student_manifest_sha256': source['student']['manifest_sha256'], 'student_adapter_sha256': source['student']['adapter_sha256'],
                                 'successful_updates': source['student']['successful_updates'], 'variant': source['student']['variant']},
                'scene': {'case_id': segment['case_id'], 'base_release_split': 'train', 'canonical_episode_index': segment['canonical_episode_index']},
                'takeover': {'point': segment['point'], 'absolute_tick': segment['takeover_tick'], 'absolute_time_s': segment['takeover_s'],
                             'rule': record['rule'], 'points_sha256': record['points_sha256'], 'split_sha256': record['split_sha256'],
                             'own_state_sha256': segment['state_sha256'], 'at_takeover': segment['at_takeover'], 'gate_run': record['gate_run'],
                             'entry_decision': expert['entry']['decision']},
                'routine': {'module': 'qlm_bench.sft_v1.sweep_recovery', 'version': expert['version'], 'commit': record['routine']['commit'],
                            'params_sha256': expert['recovery_params_sha256'], 'file_sha256': summary['code']['files']['sweep_recovery.py'],
                            'frozen_production_expert_manifest_sha256': expert['frozen_expert']['manifest_sha256']},
                'physics': 'native MuJoCo CPU, float64', 'controller': 'original RAMBO model_2000', 'controller_sha256': record['controller_sha256'],
                'pre_takeover_sidecar': f"pre_takeover/{segment['case_id']}.json"}}


def _trace_worker(args):
    jobs, run, commit = args
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    from qlm_bench.backends.mujoco.rendition import audit_trace
    from qlm_bench.sft_v1 import corrective_trace, takeover
    run = Path(run)
    record, _ = load_segments(run)
    cache = takeover.RuntimeCache(record['controller_checkpoint'])
    done = []
    try:
        for segment in jobs:
            uid = uid_of(segment)
            result = corrective_trace.record_segment(cache, segment, run / 'takeover/results' / segment['segment_id'], run / 'traces' / uid,
                                                     batch_identity=batch_identity(record, segment, run, commit), uid=uid, reset_first=True)
            audit = audit_trace(run / 'traces' / uid)
            result['audit'] = {k: audit[k] for k in ('manifest_sha256', 'trajectory_sha256', 'source_identity_sha256', 'quality', 'n_actions')}
            write_json(run / 'trace-results' / f'{uid}.json', result)
            print(json.dumps({'uid': uid, 'n_actions': result['n_actions'], 'wall_s': round(result['wall_s'], 1)}), flush=True)
            done.append(uid)
    finally:
        cache.close()
    return done


def stage_trace(a):
    run = a.run.resolve()
    commit = source_commit()
    frozen_routine()
    _, segments = load_segments(run)
    pending = [s for s in segments if not (run / 'trace-results' / f'{uid_of(s)}.json').exists()]
    if a.only:
        pending = [s for s in pending if s['case_id'][-3:] in a.only]
    for s in pending:  # A trace directory without a result is an interrupted attempt; set it aside, never delete.
        left = [run / 'traces' / uid_of(s), run / 'traces' / (uid_of(s) + '.writing')]
        for path in left:
            if path.exists():
                k = 0
                while (run / 'superseded' / f'trace-{path.name}-{k}').exists():
                    k += 1
                (run / 'superseded').mkdir(parents=True, exist_ok=True)
                path.rename(run / 'superseded' / f'trace-{path.name}-{k}')
    print(f'{len(segments)} segments, {len(pending)} to trace, source {commit[:12]}', flush=True)
    tasks = [([s], str(run), commit) for s in pending]
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
    base = json.loads((BASE / 'metadata' / segment['case_id'] / 'provenance.json').read_text())['formal_metadata']
    if base['episode_uid'] != segment['case_id'] or base['split'] != 'train' or base['task_id'] != TASK:
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
    end = segment['takeover_s'] + len(action) * 0.02
    if end > HORIZON_S + 1e-9:
        raise ValueError('Segment ends after the horizon')
    low, high = NORMALIZER_OFFSET - NORMALIZER_SCALE, NORMALIZER_OFFSET + NORMALIZER_SCALE
    oor = (action[:, :6] < low) | (action[:, :6] > high)
    return {'uid': uid, 'segment_id': segment['segment_id'], 'case_id': segment['case_id'], 'point': segment['point'], 'passed': True,
            'rows': int(len(action)), 'duration_s': len(action) * 0.02, 'takeover_s': segment['takeover_s'], 'end_absolute_s': end, 'horizon_s': HORIZON_S,
            'out_of_range_by_dim': oor.sum(0).tolist(), 'out_of_range_elements': int(oor.sum()), 'out_of_range_rows': int(oor.any(1).sum()),
            'task_text': episode['task_text'],
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
        k = 0
        while (run / 'superseded' / f'{uid}-{k}').exists():
            k += 1
        (run / 'superseded').mkdir(parents=True, exist_ok=True);output.rename(run / 'superseded' / f'{uid}-{k}')
    meta = run / 'render-inputs' / f'{uid}.json'
    write_json(meta, formal_metadata(segment, uid))
    manifest = json.loads((run / 'traces' / uid / 'manifest.json').read_text())
    log = run / 'logs' / f'render-{uid}.log';log.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(QLM / 'scripts/mujoco/synthesis/render_trace.py'), '--trace', str(run / 'traces' / uid),
               '--model', manifest['scene']['model'], '--output', str(output), '--episode-uid', uid,
               '--ffmpeg', str(FFMPEG), '--ffprobe', str(FFPROBE), '--formal-pilot', '--metadata', str(meta)]
    env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'MUJOCO_GL', 'PYOPENGL_PLATFORM', 'CUDA_VISIBLE_DEVICES')}
    env.update(RENDER_ENVIRONMENT);env['CUDA_VISIBLE_DEVICES'] = ''
    with log.open('w') as f:
        code = subprocess.run(command, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
    if code:
        return uid, f'render failed ({code}), see {log}'
    write_json(accepted, check_episode(run, segment, uid))
    return uid, 'ok'


def stage_render(a):
    run = a.run.resolve()
    _, segments = load_segments(run)
    if a.only:
        segments = [s for s in segments if s['case_id'][-3:] in a.only]
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

def held_out_tokens():
    return [f'{TASK}-20261016-{i:03d}' for i in range(81, 101)]


def stage_package(a):
    from qlm_bench.compatibility.dataset_v2.media import MediaTools
    from qlm_bench.compatibility.dataset_v2.merge import merge
    from qlm_bench.compatibility.dataset_v2.validation import validate_canonical, validate_raw
    run, release = a.run.resolve(), a.release.resolve()
    if release.name != RELEASE_NAME or release.exists():
        raise SystemExit('Release directory must be new and carry the release name')
    record, segments = load_segments(run)
    results = {uid_of(s): json.loads((run / 'episode-results' / f'{uid_of(s)}.json').read_text()) for s in segments}
    if not all(r['passed'] for r in results.values()):
        raise SystemExit('Unaccepted episode present')
    base_split = json.loads((BASE / 'meta/split.json').read_text())['episodes']
    train_scenes, held_out = set(base_split['train']), set(base_split['validation']) | set(base_split['test'])
    if sorted(held_out) != sorted(held_out_tokens()) or len(train_scenes) != 80:
        raise SystemExit('Base release split is not train 001-080 / held-out 081-100')
    scenes = sorted({s['case_id'] for s in segments})
    if len(scenes) != len(segments) or not set(scenes) <= train_scenes or set(scenes) & held_out:
        raise SystemExit('Segments are not one per scene of the 80 train scenes')
    validation = sorted(random.Random(VALIDATION_SEED).sample(scenes, VALIDATION_SCENES))
    order = sorted(segments, key=lambda s: (s['case_id'] in validation, s['case_id']))
    entries = [{'canonical': str(run / 'episodes' / uid_of(s) / 'canonical'), 'split': 'validation' if s['case_id'] in validation else 'train'} for s in order]
    tools = MediaTools(str(FFMPEG), str(FFPROBE))
    partial = release.with_name(release.name + '.writing')
    if partial.exists():
        raise SystemExit(f'Unfinished release attempt present: {partial}')
    partial.mkdir(parents=True)
    merged = merge(entries, partial / 'canonical', tools, WORK_ID)
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
    leaks = [p.name for p in partial.rglob('*') if any(t in p.name for t in held_out_tokens())]
    texts = set()
    for uid in uids:
        prov = json.loads((partial / 'canonical/metadata' / uid / 'provenance.json').read_text())
        scene = prov['source_identity']['corrective']['scene']['case_id']
        if scene != by_uid[uid]['case_id'] or scene not in train_scenes or scene in held_out or prov['formal_metadata']['split'] != 'train':
            leaks.append(uid)
        texts.add(results[uid]['task_text'])
    if leaks or set(uids) != set(by_uid) or set(split['train']) | set(split['validation']) != set(uids) or set(split['train']) & set(split['validation']):
        raise SystemExit(f'Held-out or inconsistent content: {leaks[:5]}')
    if {by_uid[u]['case_id'] for u in split['validation']} != set(validation) or {by_uid[u]['case_id'] for u in split['train']} & set(validation):
        raise SystemExit('Validation split is not whole scenes')
    if len(texts) != 1 or texts != {e['task_text'] for e in contract['episodes']}:
        raise SystemExit('Task text is not unique')
    recheck = validate_canonical(partial / 'canonical', tools=tools)
    info = json.loads((partial / 'canonical/meta/info.json').read_text())
    rows = np.array([results[u]['rows'] for u in uids]);oor = np.array([results[u]['out_of_range_by_dim'] for u in uids]).sum(0)
    oor_rows = int(sum(results[u]['out_of_range_rows'] for u in uids))
    takeover = np.array([by_uid[u]['takeover_s'] for u in uids])
    first = json.loads((partial / 'canonical/metadata' / uids[0] / 'provenance.json').read_text())['source_identity']['corrective']

    def size(path):
        return int(sum(p.stat().st_size for p in Path(path).rglob('*') if p.is_file()))
    summary = {
        'schema': 'qlm-sft-v1-corrective-release-v1', 'release': RELEASE_NAME, 'task_id': TASK, 'work_id': WORK_ID, 'dataset_schema_version': recheck['dataset_schema_version'],
        'design': DESIGN, 'source_commit': contract['episodes'][0]['source_commit'],
        'task_text': contract['episodes'][0]['task_text'], 'episodes': len(uids), 'frames': int(info['total_frames']), 'splits': info['splits'],
        'source_rollouts': len(scenes), 'points': {POINT: len(uids)}, 'discarded': record['discarded'],
        'validation': {'unit': 'scene', 'seed': VALIDATION_SEED, 'method': f'random.Random({VALIDATION_SEED}).sample(sorted scenes with a corrective segment, {VALIDATION_SCENES})',
                       'scenes': validation, 'episodes': split['validation']},
        'train_scenes': sorted(set(scenes) - set(validation)),
        'split_counts': {k: {'episodes': len(split[k]), 'scenes': len({by_uid[u]['case_id'] for u in split[k]}), 'frames': int(sum(results[u]['rows'] for u in split[k])),
                             'full_16_action_groups': int(sum(results[u]['rows'] // 16 for u in split[k]))} for k in ('train', 'validation')},
        'episode_rows': {'median': float(np.median(rows)), 'min': int(rows.min()), 'max': int(rows.max()), 'duration_s_median': float(np.median(rows) * 0.02),
                         'duration_s_min': float(rows.min() * 0.02), 'duration_s_max': float(rows.max() * 0.02)},
        'takeover_time_s': {'median': float(np.median(takeover)), 'min': float(takeover.min()), 'max': float(takeover.max())},
        'end_absolute_s': {'max': float(max(results[u]['end_absolute_s'] for u in uids)), 'horizon_s': HORIZON_S},
        'action_out_of_range': {'normalizer': 'SFT5000 export provenance data.action_normalizer, q01-q99, first 6 native9 dims',
                                'by_dim': {k: int(v) for k, v in zip(('vx', 'vy', 'yaw_rate', 'fl_x', 'fl_y', 'fl_z'), oor)},
                                'commands': int(rows.sum()), 'element_share': float(oor.sum() / (6 * rows.sum())),
                                'commands_with_any_dim_out': oor_rows, 'command_share': float(oor_rows / rows.sum())},
        'held_out': {'scenes_excluded': sorted(held_out), 'present': False, 'base_release': str(BASE), 'base_split_sha256': sha(BASE / 'meta/split.json')},
        'routine': first['routine'], 'source_model': first['source_model'],
        'render': {'mode': 'offline_state_replay', 'backend': 'osmesa', 'gl': results[uids[0]]['gl'], 'views': ['ego', 'task_centric'], 'size': [640, 360], 'fps': 50,
                   'note': 'the base sweep demonstrations were rendered with hardware EGL; these episodes with OSMesa (llvmpipe)'},
        'gate': {'run': record['gate_run'], 'split_sha256': record['split_sha256'], 'points_sha256': record['points_sha256'], 'point_rule': record['rule']},
        'validation_results': {'canonical': recheck['contract_valid'], 'canonical_video': recheck['video_validation'], 'merge': merged['contract_valid'],
                               'raw_episodes_valid': sum(r['contract_valid'] for r in raw_reports.values()), 'raw_episodes': len(raw_reports)},
        'canonical_inventory_sha256': sha(partial / 'canonical/meta/checksums.json'),
        'pre_takeover': {'path': 'pre_takeover/', 'cases': len(sidecars['cases']), 'index_sha256': sha(partial / 'pre_takeover/index.json'), 'in_sft_pool': False},
        'bytes': {'canonical': size(partial / 'canonical'), 'raw': size(partial / 'raw'), 'pre_takeover': size(partial / 'pre_takeover')},
        'episodes_table': [{'episode_index': i, 'episode_uid': u, 'split': 'validation' if u in split['validation'] else 'train', 'scene': by_uid[u]['case_id'],
                            'point': by_uid[u]['point'], 'takeover_s': by_uid[u]['takeover_s'], 'rows': results[u]['rows'],
                            'end_absolute_s': results[u]['end_absolute_s'], 'entry_decision': by_uid[u]['entry_decision'],
                            'out_of_range_rows': results[u]['out_of_range_rows'], 'out_of_range_elements': results[u]['out_of_range_elements']} for i, u in enumerate(uids)],
        'published': False}
    write_json(partial / 'release.json', summary)
    partial.rename(release)
    print(json.dumps({k: summary[k] for k in ('release', 'episodes', 'frames', 'splits', 'validation_results')}, ensure_ascii=False), flush=True)


# ------------------------------------------------------------------ verify

def stage_verify(a):
    import av
    import pyarrow.parquet as pq
    run, release = a.run.resolve(), a.release.resolve()
    record, segments = load_segments(run)
    by_uid = {uid_of(s): s for s in segments}
    out = run / 'validation';(out / 'configs').mkdir(parents=True, exist_ok=True)
    contract = json.loads((release / 'canonical/meta/contract.json').read_text())
    info = json.loads((release / 'canonical/meta/info.json').read_text())
    uids = [e['episode_uid'] for e in contract['episodes']]
    env = {**os.environ, 'PYTHONPATH': str(QLM / 'src'), 'CUDA_VISIBLE_DEVICES': ''}

    def cli(name, raw_uid, raw):
        config = out / 'configs' / f'{name}.json'
        config.write_text(json.dumps({'dataset_root': str(release / 'raw' / raw_uid), 'canonical_root': str(release / 'canonical'),
                                      'cache_root': str(out / 'cache'), 'ffmpeg': str(FFMPEG), 'ffprobe': str(FFPROBE)}))
        r = subprocess.run([sys.executable, '-m', 'qlm_bench.compatibility.dataset_v2', '--config', str(config)] + (['--raw'] if raw else []),
                           capture_output=True, text=True, env=env)
        if r.returncode:
            raise SystemExit(f'validation CLI failed for {name}:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}')
        return json.loads(r.stdout[r.stdout.index('{'):])
    canonical = cli('canonical', uids[0], False)
    raw = {u: cli(f'raw-{u}', u, True) for u in uids}
    write_json(out / 'cli-validation.json', {'canonical': canonical, 'raw': raw,
                                             'raw_summary': {'episodes': len(raw), 'contract_valid': sum(bool(r.get('contract_valid')) for r in raw.values())}})
    # ---- text scan for held-out scene ids
    tokens = held_out_tokens();hits = []
    files = [p for p in release.rglob('*') if p.is_file()]
    for p in files:
        if any(t in p.name for t in tokens):
            hits.append(str(p.relative_to(release)))
        elif p.suffix in ('.json', '.jsonl', '.md', '.txt') and any(t in p.read_text(errors='replace') for t in tokens):
            hits.append(str(p.relative_to(release)))
    # ---- provenance, actions and frame 0 per episode
    ego, task = [], []
    for e in contract['episodes']:
        u = e['episode_uid'];s = by_uid[u]
        prov = json.loads((release / 'canonical/metadata' / u / 'provenance.json').read_text())
        c = prov['source_identity']['corrective']
        assert c['scene']['case_id'] == s['case_id'] and c['takeover']['absolute_tick'] == s['takeover_tick'] and c['takeover']['point'] == POINT
        assert c['takeover']['own_state_sha256'] == s['state_sha256'] and c['routine'] == {**c['routine'], **{k: record['routine'][k] for k in ('version', 'commit', 'params_sha256', 'file_sha256')}}
        assert c['source_model']['name'] == 'Dual-level OPD (full) S900 EMA' and c['source_model']['seed'] == 42 and c['source_model']['nfe'] == '1/2'
        assert prov['formal_metadata']['split'] == 'train' and prov['backend']['physics'] == 'native' and prov['backend']['render'] == 'osmesa'
        table = pq.read_table(release / 'canonical' / info['data_path'].format(episode_chunk=0, episode_index=e['episode_index']))
        with np.load(run / 'takeover/results' / f"{s['segment_id']}.npz") as z:
            np.testing.assert_array_equal(np.asarray(table['action'].to_pylist(), np.float32), z['requested'].astype(np.float32))
        with np.load(release / 'pre_takeover' / f"{s['case_id']}.npz") as z:
            assert int(z['ticks'][-1]) == s['takeover_tick']
            student = z['frames'][-1].astype(np.float32)
        for k, (key, acc) in enumerate((('observation.images.ego', ego), ('observation.images.task_centric', task))):
            path = release / 'canonical' / info['video_path'].format(episode_chunk=0, episode_index=e['episode_index'], video_key=key)
            with av.open(str(path)) as container:
                frame = next(container.decode(video=0)).to_ndarray(format='rgb24').astype(np.float32)
            acc.append(float(np.abs(frame - student[k]).mean()))
    checks = {'held_out_text_scan': {'files': len(files), 'hits': hits,
                                     'note': 'release.json lists the 20 excluded scene ids in held_out.scenes_excluded; any other hit is a leak'},
              'episodes': len(uids), 'provenance_and_actions': 'all assertions passed',
              'frame0_vs_student_takeover_frame': {'note': 'release frame 0 (OSMesa, H.264) against the policy feedback frame at the takeover tick in the sidecar (EGL); mean absolute difference on 0-255',
                                                   'ego_median': float(np.median(ego)), 'ego_max': float(max(ego)), 'task_median': float(np.median(task)), 'task_max': float(max(task))},
              'release_json_sha256': sha(release / 'release.json')}
    if [h for h in hits if h != 'release.json']:
        raise SystemExit(f'Held-out scene id found: {hits}')
    write_json(out / 'independent-checks.json', checks)
    print(json.dumps({'canonical': canonical.get('contract_valid'), 'raw_valid': sum(bool(r.get('contract_valid')) for r in raw.values()), 'raw': len(raw),
                      'held_out_hits': hits, 'frame0': checks['frame0_vs_student_takeover_frame']}, ensure_ascii=False), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='stage', required=True)
    for name in ('segments', 'trace', 'render', 'package', 'verify'):
        s = sub.add_parser(name);s.add_argument('--run', type=Path, required=True)
        if name == 'segments':
            s.add_argument('--gate', type=Path, required=True);s.add_argument('--prep', type=Path, required=True)
            s.add_argument('--results', type=Path, nargs='+', required=True)
        if name in ('trace', 'render'):
            s.add_argument('--workers', type=int, default=1);s.add_argument('--only', nargs='*', default=None, help='scene numbers, e.g. 049')
        if name in ('package', 'verify'):
            s.add_argument('--release', type=Path, required=True)
    a = p.parse_args()
    {'segments': stage_segments, 'trace': stage_trace, 'render': stage_render, 'package': stage_package, 'verify': stage_verify}[a.stage](a)


if __name__ == '__main__':
    main()
