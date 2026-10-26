"""Explicit bounded GT command replay; never replaces a failed demonstration."""
import argparse
import json
import os
from pathlib import Path
import time

from .storage import sha256, write_json


def replay(binding_path, output, controller):
    if os.environ.get('MUJOCO_GL') != 'osmesa' or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('Set MUJOCO_GL=osmesa and CUDA_VISIBLE_DEVICES= before starting worker')
    import numpy as np
    import torch
    from PIL import Image
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
    from .snapshot import capture, save

    torch.set_num_threads(1)
    binding = json.loads(Path(binding_path).read_text())
    episode = binding['episode']
    if episode['split'] != 'train' or episode['task'] not in ('push_box','sweep_block_to_zone'):
        raise ValueError('Selected supported train demonstration required')
    trace_path = Path(binding['source_trace_manifest'])
    if sha256(trace_path) != episode['source_trace_manifest_sha256']:
        raise ValueError('Parent source trace identity mismatch')
    bundle_path = Path(binding['source_snapshot_bundle'])
    if sha256(bundle_path) != episode['snapshot_bundle_sha256']:
        raise ValueError('Parent snapshot bundle mismatch')
    bundle = json.loads(bundle_path.read_text())
    for name, desc in bundle['files'].items():
        expected = desc['sha256'] if isinstance(desc, dict) else desc
        if sha256(bundle_path.parent / name) != expected:
            raise ValueError('Parent payload mismatch: ' + name)
    scene = binding['scene']
    rows = [json.loads(x) for x in Path(binding['commands']).read_text().splitlines()]
    if len(rows) != episode['length']:
        raise ValueError('Demonstration command count mismatch')
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    rt = None
    result = {'schema': 'qlm-rl-v2-replay-v1', 'passed': False,
              'episode_uid': episode['episode_uid'], 'parent': episode,
              'binding_sha256': sha256(binding_path), 'status': 'started'}
    write_json(out / 'attempt.json', result)
    states, commands, anchors = [], [], []
    last_tick = None

    def observe(packet):
        nonlocal last_tick
        tick = packet['physics_step']
        if tick == last_tick:
            return
        last_tick = tick
        paths = {}
        for view, rgb in packet['rgb'].items():
            rel = f'rgb/{tick:08d}-{view}.png'
            path = out / rel
            path.parent.mkdir(exist_ok=True)
            Image.fromarray(rgb).save(path)
            paths[view] = {'path': rel, 'sha256': sha256(path)}
        snap = rt.physics.snapshot()
        states.append({'tick': tick, 'simulation_time_ns': packet['simulation_time_ns'],
                       'qpos': snap['qpos'].tolist(), 'qvel': snap['qvel'].tolist(),
                       'rgb': paths, 'outcome': packet['outcome']})

    try:
        rt = create_runtime(episode['task'],'native',model_path=binding['model'],checkpoint=controller,trace_only=False,device='cpu',
                           seed=scene['seed'], rgb_profile='dual-rgb-360p-v1',
                           profile_override={k: scene[k] for k in
                                             ('goal_x', 'goal_y', 'canonical_goal_position') if k in scene})
        renderer = rt.renderer.gl_identity
        if not any(x in renderer['renderer'].lower() for x in ('llvmpipe', 'softpipe', 'swrast')):
            raise ValueError('OSMesa software renderer not verified: ' + str(renderer))
        # Observer is not part of reference/model/reward inputs.
        rt.renderer.observer_clip = None
        rt.on_observation = observe
        rt.set_case_seed(scene['seed'])
        rt.reset(initial_state=scene['initial_state'])
        for index, row in enumerate(rows):
            if index % 16 == 0:
                path = out / 'anchors' / f'{index // 16:05d}.pt'
                save(path, capture(rt))
                anchors.append({'group': index // 16, 'tick': index * 10,
                                'path': str(path.relative_to(out)), 'sha256': sha256(path),
                                'restore_verified': False})
            tick = int(rt.physics.ticks[0])
            if tick != row['start_tick']:
                raise ValueError('GT command timeline differs from actual CPU timeline')
            outcome = rt.step(prepare_command(row['requested'], f'gt:{index}', tick))
            commands.append(outcome['command'])
            if (index + 1) % 32 == 0:
                print(f'GT replay {index + 1}/{len(rows)} at {tick * .002:.2f}s', flush=True)
            if outcome['terminal'] is not None:
                break
        complete = sum(c['status'] == 'completed' for c in commands)
        result.update(status='complete' if rt.outcome['success'] else 'gt_replay_failed',
                      passed=bool(rt.outcome['success'] and not rt.outcome['fallen']),
                      outcome=rt.outcome, completed_commands=complete,
                      original_commands=len(rows), final_tick=int(rt.physics.ticks[0]),
                      software_renderer=renderer, physics_backend='native', controller_device='cpu',
                      source_identity=capture_identity(rt), model_identity=rt.physics.model_identity,
                      valid_full_groups=complete // 16, anchors=anchors,
                      GPU_visible=torch.cuda.is_available())
        np.savez_compressed(out / 'trajectory.npz',
                            qpos=np.asarray([s['qpos'] for s in states]),
                            qvel=np.asarray([s['qvel'] for s in states]),
                            ticks=np.asarray([s['tick'] for s in states]))
        write_json(out / 'observations.json', states)
        write_json(out / 'commands.json', commands)
    except BaseException as exc:
        result.update(status='error', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        result['wall_seconds'] = time.monotonic() - started
        write_json(out / 'result.json', result)
        if rt is not None:
            rt.close()
    return result


def capture_identity(rt):
    from .snapshot import identity
    return identity(rt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--controller', required=True)
    args = parser.parse_args()
    result = replay(args.binding, args.output, args.controller)
    print(json.dumps({k: result[k] for k in ('passed', 'status', 'outcome', 'completed_commands', 'wall_seconds')}))
    if not result['passed']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
