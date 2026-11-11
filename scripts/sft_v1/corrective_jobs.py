"""Takeover jobs for the corrective push_box demonstrations (sft-v1/QLM-DATA-001, design 4.4 of task-specific-sft-design-20261110).

Every failed G1 rollout (exploration + gate set of the gate run's split.json) is taken over by the frozen E* at takeover points A and B of
g2/points.json. A and B of one rollout that are the same persisted chunk boundary give one segment (labelled ``A=B``), not two identical ones.
Refuses any scene outside the 80 push train scenes, checks every start state's sha256 against points.json, and records the split/points hashes.

Usage: corrective_jobs.py --gate RUN_DIR --out OUT_DIR   (writes OUT_DIR/jobs.json and OUT_DIR/segments.json)
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--gate', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    gate = a.gate.resolve()
    split = json.loads((gate / 'split.json').read_text())
    points = json.loads((gate / 'g2/points.json').read_text())
    index = json.loads((gate / 'cases-index.json').read_text())
    cases = {c['case_id']: c for c in index['cases']}
    failures = {f['case_id']: f for f in points['failures']}
    wanted = sorted(split['exploration'] + split['gate'])
    if sorted(failures) != wanted or len(wanted) != 61:
        raise SystemExit('points.json failures do not match split.json exploration + gate')
    held_out = set(split['held_out_excluded'])
    jobs, segments = [], []
    for case_id in wanted:
        case = cases[case_id]
        if case['split'] != 'train' or case['task_id'] != 'push_box' or case_id in held_out:
            raise SystemExit(f'{case_id} is not a push train scene')
        case_path = gate / 'cases' / f'{case_id}.json'
        if sha(case_path) != case['case_sha256']:
            raise SystemExit(f'{case_id}: EvalCase hash mismatch')
        f = failures[case_id]
        same = f['A']['state'] == f['B']['state']
        for label in (['A=B'] if same else ['A', 'B']):
            pt = f[label[0]]
            if sha(pt['state']) != pt['state_sha256'] or pt['tick'] % 160 or pt['tick'] != (pt['chunk'] + 1) * 160:
                raise SystemExit(f'{case_id} {label}: start state does not match points.json')
            sid = f"{case_id}-{label.replace('=', '')}"
            jobs.append({'id': sid, 'case': str(case_path), 'model': case['model_path'], 'kind': 'recovery', 'state': pt['state']})
            segments.append({'segment_id': sid, 'case_id': case_id, 'point': label, 'takeover_tick': pt['tick'], 'takeover_s': pt['t_s'],
                             'takeover_chunk': pt['chunk'], 'state': pt['state'], 'state_sha256': pt['state_sha256'],
                             'history': pt['record'], 'history_sha256': pt['record_sha256'], 'groups': pt['groups'],
                             'at_takeover': {k: pt[k] for k in ('D', 'yaw_deg', 'dyaw_deg', 'dlat_m', 'lateral_from_goal_centre')},
                             'origin_set': 'exploration' if case_id in split['exploration'] else 'gate',
                             'canonical_episode_index': case['canonical_episode_index'], 'difficulty': case['difficulty']})
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'jobs.json').write_text(json.dumps({'jobs': jobs}, indent=1) + '\n')
    (a.out / 'segments.json').write_text(json.dumps({
        'schema': 'qlm-sft-v1-corrective-segments-v1', 'gate_run': str(gate), 'split_sha256': sha(gate / 'split.json'),
        'points_sha256': sha(gate / 'g2/points.json'), 'cases_index_sha256': sha(gate / 'cases-index.json'),
        'controller_checkpoint': index['controller_checkpoint'], 'controller_sha256': index['controller_sha256'],
        'rule': points['rule'], 'failures': len(wanted), 'segments': segments}, indent=1) + '\n')
    print(len(wanted), 'failures,', len(segments), 'segments;', sum(s['point'] == 'A=B' for s in segments), 'with A and B on the same boundary')


if __name__ == '__main__':
    main()
