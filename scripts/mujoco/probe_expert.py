"""Bounded real-contact engineering attempt; success never selects benchmark trials."""
import argparse
import json
from pathlib import Path
import time
import hashlib
import os

import torch
import numpy as np

from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.tasks import TaskState
from qlm_bench.backends.mujoco.expert_adapter import ExpertAdapter
from qlm_bench.controllers.rambo.core import RAMBOCore


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--checkpoint',required=True)
    p.add_argument('--backend',choices=('native','mjwarp'),default='native');p.add_argument('--output',required=True)
    p.add_argument('--seconds',type=float,default=24.)
    p.add_argument('--seed',type=int,default=42);p.add_argument('--expert-profile')
    p.add_argument('--record-rgb',action='store_true');p.add_argument('--ffmpeg')
    args=p.parse_args()
    if not 0<args.seconds<=24:raise ValueError('Bounded P2 expert attempt')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).resolve().parents[2]
    identity={'kind':'actual_engineering_not_demonstration','work_id':'QLM-SIM-005','args':vars(args),
        'entry_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'source_files':{str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest()
                        for folder in ('src/qlm_bench/backends/mujoco','src/qlm_bench/controllers/rambo','src/qlm_bench/tasks')
                        for f in (source/folder).rglob('*.py')}}
    (out/'attempt.json').write_text(json.dumps(identity,indent=2)+'\n')
    torch.set_num_threads(1);torch.manual_seed(args.seed)
    physics=MuJoCoPhysics(args.model,backend=args.backend)
    core=RAMBOCore(physics,args.checkpoint,device='cuda:0' if args.backend=='mjwarp' else 'cpu',case_seeds=[args.seed])
    profile=json.loads(Path(args.model).with_suffix('.task.json').read_text());task=TaskState(physics,profile)
    expert=ExpertAdapter(physics,core,task);rows=[];start=time.monotonic();result={}
    if args.expert_profile:
        override=json.loads(Path(args.expert_profile).read_text())
        expert.apply_profile_override(override)
        identity['expert_override']=override;identity['expert_override_sha256']=hashlib.sha256(Path(args.expert_profile).read_bytes()).hexdigest()
    identity.update(resource_profile=physics.resource_profile,expert_profile=expert.cfg.approved_profile,rng=core.case_rng.identity(),
                    motor_lags=core.motor.lags.cpu().tolist())
    mirror=None;sinks={};captures=[]
    if args.record_rgb:
        if not args.ffmpeg or os.environ.get('MUJOCO_GL') not in ('egl','osmesa'):
            raise ValueError('Actual RGB requires explicit ffmpeg and rendering backend')
        from qlm_bench.backends.mujoco.render import RenderMirror
        from qlm_bench.backends.mujoco.video import VideoSink
        mirror=RenderMirror(args.model)
        sinks={name:VideoSink(out/(name+'.mp4'),args.ffmpeg,25 if name=='observer' else 50)
               for name in ('ego','task_centric','observer')}
        identity['GL']=mirror.gl_identity
    (out/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
    def capture(terminal=False):
        if mirror is None:return
        snap=physics.snapshot();frame=mirror.capture(snap,terminal=terminal)
        rgb={'ego':frame['rgb']['go2_ego'],'task_centric':frame['rgb']['d435i_rgb_task']}
        if frame['observer_rgb'] is not None:rgb['observer']=frame['observer_rgb']
        from PIL import Image
        same_tick=bool(captures and captures[-1]['physics_step']==snap['physics_step'])
        for role,image in rgb.items():
            if not same_tick and (role!='observer' or snap['physics_step']%20==0):sinks[role].write(image)
            if terminal:Image.fromarray(image).save(out/('terminal_'+role+'.png'))
        record={'physics_step':snap['physics_step'],'simulation_time_ns':snap['simulation_time_ns'],
                'reset_epoch':snap['reset_epoch'],'terminal':terminal,
                'hashes':{k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in rgb.items()},
                'RGB_std':{k:float(v.std()) for k,v in rgb.items()},
                'qpos':snap['qpos'].tolist(),'qvel':snap['qvel'].tolist()}
        captures.append(record)
        with (out/'captures.jsonl').open('a') as stream:stream.write(json.dumps(record)+'\n')
    try:
        capture()
        for index in range(int(args.seconds*50)):
            command,diagnostic=expert.command();core.submit([command])
            for _ in range(2):
                residual=core.begin_control()
                for _ in range(5):physics.step(core.motor_effort().cpu().numpy())
                core.end_control(residual)
            outcome=task.evaluate(0,core)
            row={'command_index':index,'simulation_time_ns':int(physics.ticks[0])*2_000_000,
                 'command':command,'outcome':outcome,'diagnostic':diagnostic,'root':core.robot.position[0].cpu().tolist()}
            rows.append(row)
            capture(terminal=bool(outcome['success'] or outcome['fallen'] or outcome['timed_out']))
            if index%100==0:print(profile['task_id'],index,diagnostic['phase'],outcome,row['root'],flush=True)
            if outcome['success'] or outcome['fallen'] or outcome['timed_out']:
                result.update(outcome);break
        result.update(elapsed_s=time.monotonic()-start,rows=rows,kind='actual_engineering_not_demonstration')
        np.savez(out/'terminal.npz',**{k:v for k,v in physics.snapshot().items() if isinstance(v,np.ndarray)})
        result['status']='completed'
        physics.close()
    except BaseException as error:
        result={'status':'error','error':str(error),'rows':rows,'elapsed_s':time.monotonic()-start}
        (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');raise
    finally:
        try:
            if mirror is not None:
                if result.get('status')=='error':capture(terminal=True)
                mirror.close()
        finally:
            result['media']={role:sink.close() for role,sink in sinks.items()}
            (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(result.get('success'),result.get('fallen'),len(rows),flush=True)


if __name__=='__main__':main()
