"""Smoke test of the DP3 planner training on synthetic demonstrations (no simulator, CPU is enough).

Writes a small random dataset in the demonstration format (point cloud 768x3, state 17, 31-D trajectory
parameters with unit calf directions) and runs `lm-train-planner` for a few epochs.

    python scripts/smoke/planner_synthetic.py --out /tmp/legmanip-smoke [--device cpu]
"""
import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

from leg_manip.demo_io import write_zarr


def episode(rng, frames=48, points=768):
    action = rng.normal(size=(frames, 31)).astype(np.float32)
    action[:, 0] = 0.0                                   # FL
    for s in (25, 28):                                   # unit start/end calf directions
        action[:, s:s + 3] /= np.linalg.norm(action[:, s:s + 3], axis=1, keepdims=True)
    return {'point_cloud': rng.normal(size=(frames, points, 3)).astype(np.float32),
            'state': rng.normal(size=(frames, 17)).astype(np.float32), 'action': action}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--device', default='cpu')
    p.add_argument('--epochs', type=int, default=2)
    a = p.parse_args()
    rng = np.random.default_rng(0)
    data = a.out / 'synthetic.zarr'
    write_zarr(data, [episode(rng) for _ in range(4)], {'task': 'synthetic', 'synthetic': True})
    cmd = [sys.executable, '-m', 'leg_manip.planner.train', '--data', str(data), '--out-root', str(a.out / 'planner'),
           '--device', a.device, '--num-epochs', str(a.epochs), '--batch-size', '8', '--warmup-steps', '2',
           '--val-every', '1', '--checkpoint-every', '1', '--wandb-mode', 'disabled']
    print(' '.join(cmd), flush=True)
    raise SystemExit(subprocess.call(cmd))


if __name__ == '__main__':
    main()
