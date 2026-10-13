"""Separate-process Native render correctness and throughput over fixed physical snapshots."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np
from PIL import Image
import psutil

from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.render import RenderMirror


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',required=True)
    parser.add_argument('--fixtures',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--iterations',type=int,default=12)
    parser.add_argument('--prepare',action='store_true')
    args=parser.parse_args()
    if not 1<=args.iterations<=100:raise ValueError('Bounded rendering probe')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    root=Path(args.fixtures)
    start=time.monotonic()
    if args.prepare:
        from qlm_bench.controllers.rambo.core import RAMBOCore
        import torch
        torch.set_num_threads(1);torch.manual_seed(42)
        root.mkdir(parents=True,exist_ok=False)
        physical=MuJoCoPhysics(args.model)
        workspace=Path(__file__).resolve().parents[4]
        controller=RAMBOCore(physical,workspace/'checkpoints/rambo/go2/quadruped/model_2000.pt')
        snapshots=[physical.snapshot()]
        for tick in range(220):
            if tick%2==0:controller.submit([[.08 if tick>=120 else 0.,0.,0.,.3 if tick>=120 else .1934,.142,.18 if tick>=120 else .05,0.,0.,0.]])
            residual=controller.begin_control()
            for _ in range(5):physical.step(controller.motor_effort().numpy())
            controller.end_control(residual)
            if tick in (19,99,159,219):snapshots.append(physical.snapshot())
        for i,snapshot in enumerate(snapshots):
            arrays={k:v for k,v in snapshot.items() if isinstance(v,np.ndarray)}
            np.savez(root/f'{i:02}.npz',**arrays)
            (root/f'{i:02}.json').write_text(json.dumps({k:v for k,v in snapshot.items() if k not in arrays},indent=2)+'\n')
        print('Prepared actual physical snapshots',len(snapshots),flush=True)
        (out/'result.json').write_text(json.dumps({'kind':'actual_physics_render_fixture','status':'completed','count':len(snapshots)},indent=2)+'\n')
        return
    mirror=RenderMirror(args.model)
    initialization=time.monotonic()-start;timings=[];frames=[]
    for meta in sorted(root.glob('*.json')):
        s=json.loads(meta.read_text())
        with np.load(meta.with_suffix('.npz')) as z:s.update({k:z[k].copy() for k in z.files})
        captured=mirror.capture(s)
        masks=mirror.geometry_masks()
        np.savez_compressed(out/(meta.stem+'-geometry.npz'),**masks)
        for name,rgb in captured['rgb'].items():
            path=out/(meta.stem+'-'+name+'.png');Image.fromarray(rgb).save(path)
            frames.append({'source':meta.stem,'camera':name,'simulation_time_ns':s['simulation_time_ns'],
                           'std':float(rgb.std()),'sha256':hashlib.sha256(rgb.tobytes()).hexdigest()})
    # Duplicate same-boundary captures measure rendering only; never count as source50Hz frames.
    for _ in range(args.iterations):
        t=time.monotonic();capture=mirror.capture(s);timings.append({'total':time.monotonic()-t,**capture['timing_s']})
    mirror.close()
    report={'kind':'render_probe_not_demonstration','render_backend':os.environ['MUJOCO_GL'],
            'GL':mirror.gl_identity,'resource_profile':mirror.resource_profile,
            'model_parameters_identity':mirror.model_parameters_identity,
            'model_sha256':hashlib.sha256(Path(args.model).read_bytes()).hexdigest(),'initialization_s':initialization,
            'frames':frames,'timings_s':timings,'rss_bytes':psutil.Process().memory_info().rss,
            'median_pair_s':float(np.median([v['total'] for v in timings])),
            'projected_1000x20s_render_hours':float(np.median([v['total'] for v in timings]))*1000*20*50/3600,
            'physics_advanced_by_renderer':False,'status':'completed'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['render_backend'],report['median_pair_s'],report['rss_bytes'],flush=True)


if __name__=='__main__':main()
