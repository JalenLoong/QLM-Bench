"""Actual restore/continuation acceptance against the uninterrupted CPU GT replay.

Replay determinism is a property of the CPU physics/renderer build, not of a demo: one
probe demo per task is replayed twice and its measured noise (bitwise zero on native CPU)
sets the tolerances used for every demo of that task.
"""
import argparse
import json
from pathlib import Path
import numpy as np

ANCHOR_CHECK_COMMANDS = 8  # Two RGB ticks and eight state checks after every restore.


def determinism(binding, reference, repeat, output):
    """Measure uninterrupted replay noise on the probe demo and record it for the task."""
    from PIL import Image
    from qlm_bench.backends.mujoco.rl_v2.storage import sha256, write_json
    ref, rep = Path(reference), Path(repeat)
    r = json.loads((ref / 'result.json').read_text()); other = json.loads((rep / 'result.json').read_text())
    if not r['passed'] or not other['passed'] or r['binding_sha256'] != other['binding_sha256'] or r['source_identity'] != other['source_identity']:
        raise ValueError('Two successful matched CPU replays required')
    with np.load(ref / 'trajectory.npz') as a, np.load(rep / 'trajectory.npz') as c:
        if not np.array_equal(a['ticks'], c['ticks']): raise ValueError('CPU replay clocks differ')
        noise = {k: float(np.abs(a[k] - c[k]).max()) for k in ('qpos', 'qvel')}
    observations = {x['tick']: x for x in json.loads((ref / 'observations.json').read_text())}
    repeated = {x['tick']: x for x in json.loads((rep / 'observations.json').read_text())}
    repeat_rgb = 0
    for tick, row in observations.items():
        if tick % 40: continue
        for view, desc in row['rgb'].items():
            x = np.array(Image.open(ref / desc['path'])); y = np.array(Image.open(rep / repeated[tick]['rgb'][view]['path']))
            repeat_rgb = max(repeat_rgb, int(np.abs(x.astype(int) - y.astype(int)).max()))
    if repeat_rgb > 1: raise ValueError('Unstable uninterrupted software-renderer baseline')
    value = {'schema': 'qlm-rl-v2-replay-determinism-v1', 'probe_episode_uid': r['episode_uid'],
             'repeat_error': noise, 'tolerances': {k: max(1e-12, 3 * v) for k, v in noise.items()},
             'repeat_RGB_max_error': repeat_rgb, 'source_identity': r['source_identity'],
             'reference_result_sha256': sha256(ref / 'result.json'), 'repeat_result_sha256': sha256(rep / 'result.json')}
    write_json(output, value)
    return value


def verify(binding, reference, controller, output, *, repeat=None, determinism_path=None):
    from PIL import Image
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.backends.mujoco.rl_v2.snapshot import load, restore
    from qlm_bench.backends.mujoco.rl_v2.storage import sha256, write_json
    from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
    b = json.loads(Path(binding).read_text()); ref = Path(reference)
    r = json.loads((ref / 'result.json').read_text())
    if not r['passed']: raise ValueError('Successful CPU GT replay required')
    if repeat is not None:
        probe = determinism(binding, reference, repeat, determinism_path)
    else:
        probe = json.loads(Path(determinism_path).read_text())
        if probe.get('schema') != 'qlm-rl-v2-replay-determinism-v1': raise ValueError('Task replay-determinism probe required')
    tolerance, repeat_rgb = probe['tolerances'], probe['repeat_RGB_max_error']
    rows = json.loads((ref / 'commands.json').read_text()); observations = {x['tick']: x for x in json.loads((ref / 'observations.json').read_text())}
    result = {'schema': 'qlm-rl-v2-restore-verification-v1', 'passed': False, 'repeat_error': probe['repeat_error'], 'tolerances': tolerance,
              'repeat_RGB_max_error': repeat_rgb, 'reference_result_sha256': sha256(ref / 'result.json'),
              'repeat_result_sha256': probe['repeat_result_sha256'] if repeat is not None else None,
              'determinism_probe': probe['probe_episode_uid'], 'determinism_sha256': sha256(determinism_path), 'checks': []}
    scene = b['scene']; rt = create_runtime(b['episode']['task'], 'native', model_path=b['model'], checkpoint=controller, trace_only=False, device='cpu', seed=scene['seed'],
              rgb_profile='dual-rgb-360p-v1', profile_override={k: scene[k] for k in ('goal_x', 'goal_y', 'canonical_goal_position') if k in scene})
    rt.renderer.observer_clip = None
    def continuation(group, count):
        restore(rt, load(ref / f'anchors/{group:05d}.pt')); before = rt.freeze_token()
        if rt.freeze_token() != before: raise ValueError('Inspection advanced controller/RNG')
        maximum = {'qpos': 0., 'qvel': 0., 'rgb': 0}
        start = group * 16
        for i in range(start, min(start + count, len(rows))):
            outcome = rt.step(prepare_command(rows[i]['requested'], f'verify:{group}:{i}', i * 10))
            tick = int(rt.physics.ticks[0]); expected = observations[tick]; state = rt.physics.snapshot()
            for key in ('qpos', 'qvel'):
                error = float(np.abs(state[key] - expected[key]).max()); maximum[key] = max(maximum[key], error)
                if error > tolerance[key]: raise ValueError(f'Restore continuation diverged: {group}/{i}/{key}/{error}')
            if outcome['completed_interval'] and outcome['command']['executed'] != rows[i]['executed']: raise ValueError('Restored command differs')
            if expected['rgb'] and (tick % 40 == 0 or outcome['terminal']):
                for view, image in rt.state()['rgb'].items():
                    original = np.asarray(Image.open(ref / expected['rgb'][view]['path']))
                    error = int(np.abs(image.astype(int) - original.astype(int)).max()); maximum['rgb'] = max(maximum['rgb'], error)
                    if error > max(1, 3 * repeat_rgb): raise ValueError('Restored RGB differs from reference')
            if outcome['terminal']: break
        result['checks'].append({'group': group, 'commands': i - start + 1, 'max_error': maximum, 'passed': True})
    try:
        n = r['valid_full_groups']
        # Every admitted anchor is restored and checked; one long continuation from the
        # midpoint must still reach the recorded GT success.
        for group in range(n): continuation(group, ANCHOR_CHECK_COMMANDS)
        continuation(n // 2, len(rows) - 16 * (n // 2))
        if not rt.outcome['success']: raise ValueError('Restored GT continuation did not retain success')
        result.update(passed=True, all_admitted_anchors=n, full_continuation_success=True, independent_process_load=True)
    finally: rt.close(); write_json(output, result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('binding', 'reference', 'controller', 'output', 'determinism'): p.add_argument('--' + name, required=True)
    p.add_argument('--repeat', help='second uninterrupted replay of the task probe demo; writes --determinism')
    a = p.parse_args()
    r = verify(a.binding, a.reference, a.controller, a.output, repeat=a.repeat, determinism_path=a.determinism)
    print(json.dumps({'passed': r['passed'], 'anchors': r['all_admitted_anchors']}))


if __name__ == '__main__': main()
