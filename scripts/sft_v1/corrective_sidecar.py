"""Pre-takeover sidecars for the corrective push_box demonstrations (sft-v1/QLM-DATA-001, design 4.4).

For every failed G1 rollout that contributes segments: the student's own half before the takeover (policy feedback frames on the 80 ms grid,
both views, and the executed native9 command groups) up to its latest takeover boundary, plus the source model identity and, per segment, how
much of that prefix precedes its takeover. These files trace where a segment came from; they are not episodes and never enter the SFT pool.

Usage: corrective_sidecar.py --segments takeover/segments.json --run-config GATE/g1/run-config.json --out DIR
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--segments', type=Path, required=True)
    p.add_argument('--run-config', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    record = json.loads(a.segments.read_text())
    source = json.loads(a.run_config.read_text())
    by_case = {}
    for s in record['segments']:
        by_case.setdefault(s['case_id'], []).append(s)
    a.out.mkdir(parents=True, exist_ok=True)
    index = []
    for case_id, segments in sorted(by_case.items()):
        history = Path(segments[0]['history'])
        if any(s['history'] != str(history) for s in segments) or sha(history) != segments[0]['history_sha256']:
            raise SystemExit(f'{case_id}: history record does not match points.json')
        z = np.load(history)
        last = max(s['takeover_tick'] for s in segments)
        groups = last // 160
        keep = z['ticks'] <= last
        if int(z['ticks'][keep][-1]) != last or groups > len(z['executed']) or int(z['ticks'][0]) != 0:
            raise SystemExit(f'{case_id}: history does not reach the takeover boundary')
        ticks, frames, executed = z['ticks'][keep], z['frames'][keep], z['executed'][:groups]
        name = a.out / f'{case_id}.npz'
        np.savez_compressed(name, ticks=ticks, frames=frames, executed=executed)
        meta = {'schema': 'qlm-sft-v1-pre-takeover-sidecar-v1', 'case_id': case_id, 'arrays': name.name, 'arrays_sha256': sha(name),
                'source_history': str(history), 'source_history_sha256': segments[0]['history_sha256'],
                'content': {'ticks': 'physics tick of each frame (80 ms grid, 40 ticks)', 'frames': '[n, 2 (ego, task_centric), 360, 640, 3] uint8, the policy feedback frames',
                            'executed': '[groups, 16, 9] native9 commands executed by the student before the takeover'},
                'frames': int(len(ticks)), 'command_groups': int(groups), 'through_tick': int(last),
                'source_model': {'name': source['model'], 'nfe': '1/2', 'seed': source['seed'], 'residual': source['residual'],
                                 'inference_sha256': source['inference_sha256'], 'student': source['student']},
                'segments': [{'segment_id': s['segment_id'], 'point': s['point'], 'takeover_tick': s['takeover_tick'],
                              'command_groups_before_takeover': s['takeover_tick'] // 160,
                              'frames_through_takeover': int((ticks <= s['takeover_tick']).sum())} for s in segments],
                'in_sft_pool': False}
        (a.out / f'{case_id}.json').write_text(json.dumps(meta, indent=1) + '\n')
        index.append({'case_id': case_id, 'json': f'{case_id}.json', 'json_sha256': sha(a.out / f'{case_id}.json'), 'arrays_sha256': meta['arrays_sha256']})
    (a.out / 'index.json').write_text(json.dumps({'schema': 'qlm-sft-v1-pre-takeover-sidecar-index-v1', 'cases': index}, indent=1) + '\n')
    print(len(index), 'sidecars')


if __name__ == '__main__':
    main()
