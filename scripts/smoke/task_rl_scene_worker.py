"""Smoke test of the Task RL scene worker through its real entry point (``python -m qlm_bench.task_rl.scene_worker``).

Resets an EvalCase, executes one window of recorded 16-command chunks, captures a rollout state, executes the
next chunk, then restores the captured state in a new session and executes that chunk again: the two
executions must return identical privileged rows and progress, and (with deterministic OSMesa rendering,
MUJOCO_GL=osmesa) bit-identical policy frames. Hardware EGL frames are not bit-reproducible between runs.

    python scripts/smoke/task_rl_scene_worker.py --case <case.json> --model <scene.xml> --controller <model_2000.pt> \
        --commands inputs/task_rl/push_box/commands/<case>.npz --output <new dir> [--chunks 4] [--render-mode sampled]
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np


class Worker:
    def __init__(self, controller, state_root, render_mode, env):
        from qlm_bench.task_rl.ipc import read_frame, write_frame
        self.read_frame, self.write_frame, self.n = read_frame, write_frame, 0
        self.proc = subprocess.Popen([sys.executable, '-m', 'qlm_bench.task_rl.scene_worker', '--controller', str(controller),
                                      '--state-root', str(state_root), '--render-mode', render_mode],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env)

    def call(self, operation, session, payload):
        self.n += 1
        self.write_frame(self.proc.stdin, {'schema': 'qlm-task-rl-scene-ipc-v1', 'id': f'req-{self.n}',
                                           'operation': operation, 'session': session, 'payload': payload})
        response = self.read_frame(self.proc.stdout)
        if not response['ok']:
            raise RuntimeError(f"{operation}: {response['error_type']}: {response['error']}")
        return response['result']

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=60)


def frames(result):
    return [hashlib.sha256(np.asarray(s['rgb'][k]).tobytes()).hexdigest() for s in result['samples'] for k in sorted(s['rgb'])]


def physics(result):
    return json.dumps([result['privileged']['rows'], result['progress'], result['end_tick']])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ('--case', '--model', '--controller', '--commands', '--output'):
        p.add_argument(name, required=True)
    p.add_argument('--chunks', type=int, default=4)
    p.add_argument('--render-mode', choices=('full', 'sampled'), default='sampled')
    a = p.parse_args()
    out = Path(a.output)
    (out / 'states').mkdir(parents=True, exist_ok=False)
    commands = np.load(a.commands)['executed']
    env = dict(os.environ)
    env.setdefault('MUJOCO_GL', 'osmesa')
    worker = Worker(a.controller, out / 'states', a.render_mode, env)
    started = time.monotonic()
    try:
        boundary = worker.call('reset', 's1', {'case': a.case, 'model': a.model})
        for chunk in range(a.chunks):
            result = worker.call('execute', 's1', {'chunk': chunk, 'commands': commands[chunk].tolist(), 'ring': False})
            if result['terminal'] is not None:
                raise RuntimeError('Episode ended inside the smoke window')
        state = worker.call('capture_state', 's1', {'path': 'window.pt'})
        live = worker.call('execute', 's1', {'chunk': a.chunks, 'commands': commands[a.chunks].tolist(), 'ring': False})
        restored = worker.call('restore_state', 's2', {'case': a.case, 'model': a.model, 'path': 'window.pt'})
        replay = worker.call('execute', 's2', {'chunk': 0, 'commands': commands[a.chunks].tolist(), 'ring': False})
    finally:
        worker.close()
    rgb_same = frames(live) == frames(replay)
    passed = physics(live) == physics(replay) and (rgb_same or env['MUJOCO_GL'] != 'osmesa')
    report = {'passed': passed, 'render_mode': a.render_mode, 'mujoco_gl': env['MUJOCO_GL'], 'chunks': a.chunks,
              'reset_tick': boundary['absolute_tick'], 'captured_tick': state['absolute_tick'],
              'restored_tick': restored['absolute_tick'], 'samples_per_chunk': len(live['samples']),
              'privileged_columns': len(live['privileged']['columns']), 'progress_after_window': live['progress'],
              'restore_replay_physics_identical': physics(live) == physics(replay),
              'restore_replay_rgb_identical': rgb_same, 'renderer': boundary['renderer'],
              'elapsed_s': time.monotonic() - started}
    (out / 'smoke-result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
