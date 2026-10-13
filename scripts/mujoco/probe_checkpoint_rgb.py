"""Bounded original RAMBO/MuJoCo evidence with actual RGB and full snapshots.

This diagnostic never converts assets or changes the controller/physics model.
Observer is a free rendering camera only. Policy videos remain dual720p50Hz.
"""
import argparse
from fractions import Fraction
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import time

import av
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch

from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.render import RenderMirror
from qlm_bench.controllers.rambo.core import RAMBOCore, CHECKPOINT_SHA256

PHASES = [('settle',0,2),('stand',2,4),('forward',4,7),('lateral',7,10),
          ('yaw',10,13),('FL_extension',13,16),('return',16,18)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def phase_command(t):
    phase = next(name for name,start,end in PHASES if start <= t < end)
    command = [0.,0.,0.,.1934,.142,.05,0.,0.,0.]
    if phase=='forward':command[0]=.15
    elif phase=='lateral':command[1]=.1
    elif phase=='yaw':command[2]=.15
    elif phase=='FL_extension':command[3:6]=[.3,.142,.18]
    return phase,command


class Sink:
    def __init__(self,path,fps,width=1280,height=720):
        self.path=path;self.count=0;self.fps=fps
        self.container=av.open(str(path),'w')
        self.stream=self.container.add_stream('libx264',rate=fps)
        self.stream.width,self.stream.height,self.stream.pix_fmt=width,height,'yuv420p'
        self.stream.time_base=Fraction(1,fps)
        self.stream.options={'crf':'18','preset':'medium','threads':'2'}

    def write(self,rgb):
        frame=av.VideoFrame.from_ndarray(np.ascontiguousarray(rgb),format='rgb24')
        frame.pts,frame.time_base=self.count,Fraction(1,self.fps)
        for packet in self.stream.encode(frame):self.container.mux(packet)
        self.count+=1

    def close(self):
        for packet in self.stream.encode():self.container.mux(packet)
        self.container.close()


def parameter_hash(core):
    h=hashlib.sha256()
    for name,value in core.actor.state_dict().items():
        h.update(name.encode());h.update(value.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser()
    for name in ('model','checkpoint','output'):p.add_argument('--'+name,required=True)
    p.add_argument('--backend',required=True,choices=('native','mjwarp'))
    p.add_argument('--work-id',choices=('QLM-SIM-003','QLM-SIM-004','QLM-SIM-005'),default='QLM-SIM-003')
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    if os.environ.get('MUJOCO_GL') not in ('egl','osmesa'):raise ValueError('Explicit renderer required')
    assert sha(a.checkpoint)==CHECKPOINT_SHA256
    source=Path(__file__).resolve().parents[2]
    files={str(f.relative_to(source)):sha(f) for folder in ('src/qlm_bench/controllers/rambo','src/qlm_bench/backends/mujoco')
           for f in (source/folder).rglob('*.py')}
    attempt={'work_id':a.work_id,'kind':'actual_original_checkpoint_diagnostic_not_demonstration',
        'args':vars(a),'source_base':subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),
        'source_files_sha256':files,'entry_sha256':sha(__file__),'model_sha256':sha(a.model),
        'checkpoint_sha256':sha(a.checkpoint),'render_backend':os.environ['MUJOCO_GL'],
        'versions':{name:importlib.metadata.version(name) for name in ('torch','mujoco','mujoco-warp','warp-lang','qpth','av')},
        'started_unix':time.time(),'schedule':PHASES,'scope':'RAMBO verification only; no task assets or model weights modified by this probe'}
    (out/'attempt.json').write_text(json.dumps(attempt,indent=2)+'\n')
    torch.set_num_threads(1);torch.manual_seed(42)
    start=time.monotonic();sinks={};rows=[];captures=[];snapshots=[];obs_rows=[];actor_rows=[];effort_rows=[];report={}
    mirror=None
    try:
        physics=MuJoCoPhysics(a.model,backend=a.backend)
        attempt['resource_profile']=physics.resource_profile
        core=RAMBOCore(physics,a.checkpoint,device='cuda:0' if a.backend=='mjwarp' else 'cpu')
        weights=parameter_hash(core)
        mirror=RenderMirror(a.model)
        from OpenGL import GL
        attempt['GL']={name:GL.glGetString(value).decode() for name,value in
                       (('vendor',GL.GL_VENDOR),('renderer',GL.GL_RENDERER),('version',GL.GL_VERSION))}
        attempt['actor_parameters_sha256']=weights
        attempt['normalizer_mean_sha256']=hashlib.sha256(core.actor.mean.cpu().numpy().tobytes()).hexdigest()
        attempt['normalizer_std_sha256']=hashlib.sha256(core.actor.std.cpu().numpy().tobytes()).hexdigest()
        attempt['motor_lags_physics_ticks']=core.motor.lags.cpu().tolist()
        (out/'identity.json').write_text(json.dumps(attempt,indent=2)+'\n')
        observer=mujoco.MjvCamera();observer.type=mujoco.mjtCamera.mjCAMERA_FREE
        observer.lookat[:]=[.35,.15,.2];observer.distance=1.8;observer.azimuth=135;observer.elevation=-24
        for name,fps in (('ego',50),('task_centric',50),('observer',25),('preview',25)):
            sinks[name]=Sink(out/(name+'.mp4'),fps,height=768 if name=='preview' else 720)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
        init_s=time.monotonic()-start

        def capture(phase,command,terminal=False):
            snapshot=physics.snapshot();before=physics.data[0].qpos.copy();tick=int(physics.ticks[0])
            rgb=mirror.capture(snapshot)['rgb']
            rgb={'ego':rgb['go2_ego'],'task_centric':rgb['d435i_rgb_task']}
            if tick%20==0 or terminal:
                mirror.renderer.update_scene(mirror.data,camera=observer)
                rgb['observer']=mirror.renderer.render().copy()
            assert tick==int(physics.ticks[0]) and np.array_equal(before,physics.data[0].qpos)
            snapshots.append(snapshot)
            item={'physics_step':tick,'simulation_time_ns':tick*2_000_000,'reset_epoch':snapshot['reset_epoch'],
                  'phase':phase,'command':command,'terminal':terminal,
                  'rgb_sha256':{k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in rgb.items()},
                  'rgb_std':{k:float(v.std()) for k,v in rgb.items()},'render_physics_advanced':False}
            captures.append(item)
            if terminal:
                for name,image in rgb.items():Image.fromarray(image).save(out/('terminal_'+name+'.png'))
            else:
                for name,image in rgb.items():sinks[name].write(image)
                if 'observer' in rgb:
                    img=Image.new('RGB',(1280,768),'#10151d');draw=ImageDraw.Draw(img)
                    draw.text((12,8),f'{a.backend} | ORIGINAL RAMBO model_2000 | t={tick*.002:.2f}s | {phase}',font=font,fill='white')
                    draw.text((12,32),f'native9: vx={command[0]:.2f} vy={command[1]:.2f} yaw={command[2]:.2f} FL={command[3:6]}',font=font,fill='#b9e1ff')
                    img.paste(Image.fromarray(rgb['observer']).resize((960,720),Image.Resampling.LANCZOS),(0,48))
                    img.paste(Image.fromarray(rgb['ego']).resize((320,180),Image.Resampling.LANCZOS),(960,48))
                    img.paste(Image.fromarray(rgb['task_centric']).resize((320,180),Image.Resampling.LANCZOS),(960,228))
                    draw.text((966,416),'Actual RGB',font=font,fill='white')
                    draw.text((966,448),'500/100/50Hz',font=font,fill='white')
                    draw.text((966,480),'force-zero',font=font,fill='white')
                    sinks['preview'].write(np.asarray(img))
                    # Lossless actual RGB keyframes, independent of MP4 compression.
                    if tick in (760,1760,2760,4260,5760,7260,8500):
                        img.save(out/(f'preview_{tick:05d}.png'))
            return item

        for action in range(900):
            phase,command=phase_command(action/50)
            capture(phase,command)
            core.submit([command])
            for _ in range(2):
                obs_rows.append(core._obs_history.flatten(1)[0].cpu().numpy().copy())
                residual=core.begin_control();actor_rows.append(residual[0].cpu().numpy().copy())
                for _ in range(5):
                    effort=core.motor_effort().cpu().numpy();effort_rows.append(effort[0].copy())
                    physics.step(effort)
                core.end_control(residual)
                robot=core.robot;g=core.projected_gravity_b[0].cpu().numpy();height=float(core.base_height[0])
                row={'phase':phase,'physics_step':int(physics.ticks[0]),'height':height,
                     'root_position':robot.position[0].cpu().tolist(),'quaternion_xyzw':robot.quaternion_xyzw[0].cpu().tolist(),
                     'linear_velocity_body':core.base_lin_vel_b[0].cpu().tolist(),
                     'angular_velocity_body':core.base_ang_vel_b[0].cpu().tolist(),
                     'gravity_error':float(np.linalg.norm(g-[0,0,-1])),
                     'contact':core.foot_contacts[0].cpu().tolist(),
                     'FL_RP_height_position':(core.base_rot_mat_rp[0]@core.ee_pos_b[0,0]).cpu().tolist(),
                     'command':command}
                row['FL_RP_height_position'][2]+=height
                rows.append(row)
                if not all(np.isfinite(v).all() for v in (physics.data[0].qpos,physics.data[0].qvel,effort,residual.cpu().numpy())):
                    raise FloatingPointError('Nonfinite physics/controller output')
                if height<.1 or row['gravity_error']>.75:raise RuntimeError('Original fall criterion triggered')
            if action%50==0:print(a.backend,phase,action/50,'height',height,'position',row['root_position'],flush=True)
        capture('terminal',command,terminal=True)
        assert len(obs_rows)==1800 and int(physics.ticks[0])==9000
        assert weights==parameter_hash(core) and sha(a.checkpoint)==CHECKPOINT_SHA256
        physics.reset();core.reset(torch.tensor([0],device=core.device))
        reset=physics.snapshot()
        reset_check={'tick':reset['physics_step'],'time_s':reset['time'],'qvel_zero':bool(np.all(reset['qvel']==0)),
            'motor_history_zero':bool(torch.count_nonzero(core.motor.history)==0),
            'motor_age_zero':bool(torch.count_nonzero(core.motor.age)==0),
            'old_obs_history_zero':bool(torch.count_nonzero(core._obs_history[:,:-1])==0),
            'last_action_zero':bool(torch.count_nonzero(core._last_action)==0)}
        assert all(v is True for k,v in reset_check.items() if k.endswith('_zero'))
        assert reset_check['tick']==0 and reset_check['time_s']==0
        physics.close()
        report={'status':'completed','run_through_passed':True,'reset':reset_check,
                'actor_forward_calls':len(actor_rows),'weights_unchanged':True,'initialization_s':init_s}
    except BaseException as error:
        report={'status':'failed','run_through_passed':False,'error':type(error).__name__+': '+str(error)}
        if mirror is not None and rows:
            try:capture('failure',rows[-1]['command'],terminal=True)
            except Exception as capture_error:report['failure_capture_error']=str(capture_error)
    finally:
        for name,sink in sinks.items():
            try:sink.close()
            except Exception as error:report.setdefault('encoder_errors',{})[name]=str(error)
        if mirror is not None:mirror.close()
        if snapshots:
            np.savez_compressed(out/'actual_snapshots.npz',
                **{name:np.stack([s[name] for s in snapshots]) for name in ('qpos','qvel','mocap_pos','mocap_quat','act','eq_active')},
                physics_step=np.array([s['physics_step'] for s in snapshots]),
                simulation_time_ns=np.array([s['simulation_time_ns'] for s in snapshots]),
                reset_epoch=np.array([s['reset_epoch'] for s in snapshots]))
        np.savez_compressed(out/'controller_tensors.npz',observations=np.asarray(obs_rows),
                            actor_residual=np.asarray(actor_rows),motor_effort=np.asarray(effort_rows))
        (out/'telemetry.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
        (out/'captures.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in captures))
        report.update(elapsed_s=time.monotonic()-start,physics_ticks=rows[-1]['physics_step'] if rows else 0,
                      control_ticks=len(rows),camera_frames={name:sink.count for name,sink in sinks.items()},
                      checkpoint_sha256=sha(a.checkpoint),model_sha256=sha(a.model),asset_migration_executed=False)
        summaries={}
        for phase,begin,end in PHASES:
            selected=[row for row in rows if row['phase']==phase and row['physics_step']*.002>=begin+1]
            if not selected:continue
            fl=np.asarray([row['FL_RP_height_position'] for row in selected]);command=np.asarray(selected[0]['command'])
            summaries[phase]={'mean_body_velocity':np.mean([r['linear_velocity_body'] for r in selected],axis=0).tolist(),
                'mean_body_angular_velocity':np.mean([r['angular_velocity_body'] for r in selected],axis=0).tolist(),
                'height_range':[min(r['height'] for r in selected),max(r['height'] for r in selected)],
                'gravity_error_max':max(r['gravity_error'] for r in selected),
                'FL_target_RP_height':command[3:6].tolist(),'FL_position_mean':fl.mean(0).tolist(),
                'FL_error_norm_mean':float(np.linalg.norm(fl-command[3:6],axis=1).mean()),
                'root_displacement_world':(np.asarray(selected[-1]['root_position'])-selected[0]['root_position']).tolist()}
        report['phase_metrics']=summaries
        report['limitations']=['Bounded18s nominal flat-ground verification, not task/benchmark/AMD acceptance',
            'Tracking is reported numerically; run_through_passed means finite, no-fall, complete clocks and reset only',
            'Observer is diagnostic free camera; original model camera geometry unchanged',
            'All RGB is newly captured during this actual rollout, not state reconstruction or WAM-predicted video']
        report['files_sha256']={f.name:sha(f) for f in out.iterdir() if f.is_file() and f.name!='result.json'}
        (out/'result.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print('RESULT',report['status'],report['physics_ticks'],report['camera_frames'],flush=True)
    if report['status']!='completed' or report.get('encoder_errors'):raise SystemExit(1)


if __name__=='__main__':main()
