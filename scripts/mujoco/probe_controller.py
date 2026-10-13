"""Bounded actual controller probe; every invocation records its own source and failure."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np
import torch

from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.controllers.rambo.core import RAMBOCore


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',required=True)
    parser.add_argument('--checkpoint',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--backend',choices=('native','mjwarp'),required=True)
    parser.add_argument('--worlds',type=int,default=1)
    parser.add_argument('--seconds',type=float,default=6.)
    parser.add_argument('--device',default='cpu')
    parser.add_argument('--work-id',default='QLM-SIM-001',choices=('QLM-SIM-001','QLM-SIM-005'))
    args=parser.parse_args()
    if not 0<args.seconds<=20 or args.worlds not in (1,2):
        raise ValueError('Bounded foundation probe requires1/2 worlds and at most20 simulation seconds')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[2]
    source={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('src/qlm_bench/controllers/rambo','src/qlm_bench/backends/mujoco')
            for p in (root/folder).glob('*.py')}
    attempt={'schema':'qlm-mujoco-controller-probe-v1','work_id':args.work_id,'args':vars(args),'source_files':source,
             'base_commit':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
             'kind':'actual_runtime','started_unix':time.time(),'status':'running'}
    (out/'attempt.json').write_text(json.dumps(attempt,indent=2)+'\n')
    start=time.monotonic();rows=[]
    try:
        torch.set_num_threads(1);torch.manual_seed(42)
        physics=MuJoCoPhysics(args.model,count=args.worlds,backend=args.backend)
        attempt['resource_profile']=physics.resource_profile
        (out/'identity.json').write_text(json.dumps(attempt,indent=2)+'\n')
        core=RAMBOCore(physics,args.checkpoint,device=args.device)
        init_s=time.monotonic()-start
        for control in range(int(args.seconds*100)):
            t=control/100
            command=[0.,0.,0.,.1934,.142,.05,0.,0.,0.]
            if 1<=t<2:command[0]=.15
            elif 2<=t<3:command[1]=.1
            elif 3<=t<4:command[2]=.15
            elif t>=4:command[3:6]=[.3,.142,.18]
            # Native9 changes only at50Hz command boundaries.
            if control%2==0:core.submit([command]*args.worlds)
            residual=core.begin_control()
            for _ in range(5):physics.step(core.motor_effort().cpu().numpy())
            core.end_control(residual)
            row={'control_tick':control+1,'simulation_time_ns':int(physics.ticks[0])*2_000_000,
                 'height':core.base_height.cpu().tolist(),'gravity':core.projected_gravity_b.cpu().tolist(),
                 'root_position':[d.xpos[physics.root_id].tolist() for d in physics.data],
                 'residual_max':float(residual.abs().max()),'contacts':core.foot_contacts.cpu().tolist()}
            rows.append(row)
            if not np.isfinite(np.concatenate([d.qpos for d in physics.data])).all():
                raise FloatingPointError('Nonfinite physics')
            if min(row['height'])<.1 or any(np.linalg.norm(np.asarray(g)-[0,0,-1])>.75 for g in row['gravity']):
                raise RuntimeError('Retained controller fall/large-orientation criterion triggered')
            if control%100==0:print(row,flush=True)
        before=physics.snapshot(args.worlds-1)
        physics.reset([0]);core.reset(torch.tensor([0],device=args.device))
        after=physics.snapshot(args.worlds-1)
        isolation=args.worlds==1 or (np.array_equal(before['qpos'],after['qpos']) and before['simulation_time_ns']==after['simulation_time_ns'])
        if not isolation:raise RuntimeError('Other world changed at subset reset')
        physics.close()
        report={'passed':True,'elapsed_s':time.monotonic()-start,'initialization_s':init_s,
                'rows':rows,'subset_reset_isolation':isolation,'status':'completed'}
    except BaseException as error:
        report={'passed':False,'status':'failed','error':type(error).__name__+': '+str(error),
                'rows':rows,'elapsed_s':time.monotonic()-start}
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        raise
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Passed actual controller probe',report['elapsed_s'],flush=True)


if __name__=='__main__':main()
