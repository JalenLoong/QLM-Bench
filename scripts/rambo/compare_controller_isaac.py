"""Original Isaac/CRL2 reference for the18s MuJoCo RAMBO tracking probe.

Launch with the reference worktree run60.sh; this entry never imports RAMBOCore.
Only passive telemetry and a diagnostic observer are added to the original env.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

PHASES=[('settle',0,2),('stand',2,4),('forward',4,7),('lateral',7,10),
        ('yaw',10,13),('FL_extension',13,16),('return',16,18)]
PIN='189545fbf0c00125f751f6f9bfb2c009f382319b'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(t):
    phase=next(n for n,b,e in PHASES if b<=t<e)
    values=[0.,0.,0.,.1934,.142,.05,0.,0.,0.]
    if phase=='forward':values[0]=.15
    elif phase=='lateral':values[1]=.1
    elif phase=='yaw':values[2]=.15
    elif phase=='FL_extension':values[3:6]=[.3,.142,.18]
    return phase,values


def source_identity(root):
    commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    assert commit==PIN
    rows=subprocess.check_output(['git','-C',str(root),'ls-tree','-r',PIN,'source/rambo/rambo','source/crl2/crl2'],text=True).splitlines()
    sources={}
    for row in rows:
        metadata,name=row.split('\t',1)
        if not name.endswith('.py'):continue
        data=(root/name).read_bytes()
        expected=metadata.split()[2]
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==expected,name
        sources[name]=hashlib.sha256(data).hexdigest()
    return {'reference_commit':commit,'original_source_sha256':sources}


class Sink:
    def __init__(self,path,ffmpeg,fps,height=720):
        self.count=0;self.path=path;self.errors=path.with_suffix('.encoder.log').open('x')
        self.command=[ffmpeg,'-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'1280x{height}',
            '-framerate',str(fps),'-i','pipe:0','-c:v','libx264','-threads','2','-crf','18','-preset','medium',
            '-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
        self.proc=subprocess.Popen(self.command,stdin=subprocess.PIPE,stderr=self.errors)
    def write(self,image):
        self.proc.stdin.write(image.tobytes());self.count+=1
    def close(self):
        self.proc.stdin.close();code=self.proc.wait();self.errors.close()
        if code:raise RuntimeError('RGB encoder failed')


def main():
    from isaaclab.app import AppLauncher
    p=argparse.ArgumentParser()
    for name in ('reference-source','checkpoint','output','ffmpeg'):p.add_argument('--'+name,required=True)
    AppLauncher.add_app_launcher_args(p);args=p.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    ref=Path(args.reference_source).resolve()
    identity=source_identity(ref)
    identity.update(work_id='QLM-SIM-004',kind='independent_original_Isaac_reference_not_demonstration',
        args=vars(args),entry_sha256=sha(__file__),checkpoint_sha256=sha(args.checkpoint),
        schedule=PHASES,started_unix=time.time(),eula='user authorized all task EULA; process scoped',
        original_source_assertion='all tracked RAMBO/CRL2 Python files equal original189545f blobs')
    (out/'attempt.json').write_text(json.dumps(identity,indent=2)+'\n')
    helper_path=ref/'scripts/rambo/physx_quadruped_policy_smoke.py'
    s=importlib.util.spec_from_file_location('original_policy_smoke',helper_path)
    helper=importlib.util.module_from_spec(s);sys.modules[s.name]=helper;s.loader.exec_module(helper)
    launcher=None;env=None;sinks={};rows=[];physics_rows=[];obs_rows=[];actions=[];captures=[];qp_rows=[];result={}
    start=time.monotonic()
    try:
        launcher=AppLauncher(args)
        runtime=helper._runtime_imports()
        import numpy as np
        import torch
        import warp as wp
        from PIL import Image,ImageDraw,ImageFont
        import rambo,crl2
        from scipy.spatial.transform import Rotation
        from rambo.tasks.common.camera import make_front_rgb_camera_cfg,create_front_rgb_camera
        from isaaclab.utils import math as math_utils
        from rambo.validation.checkpoints import assert_state_dict_equal
        torch.set_num_threads(1)
        assert Path(rambo.__file__).resolve().is_relative_to(ref/'source/rambo')
        assert Path(crl2.__file__).resolve().is_relative_to(ref/'source/crl2')
        assert not any(k.startswith('qlm_bench.controllers') for k in sys.modules)
        contract=runtime['contract_for_task'](helper.TASK)
        checkpoint=runtime['load_verified_checkpoint'](Path(args.checkpoint),contract)
        cfg=runtime['parse_env_cfg'](helper.TASK,device=args.device or 'cuda:0',num_envs=1,use_fabric=True)
        runtime['configure_physx'](cfg);helper._configure_deterministic_smoke(cfg,42,1800)
        cfg.contact_generator_config['contact_generator_debug_vis']=False
        cfg.qp_torque_optimizer_config['qp_debug_vis']=False
        cfg.joint_position_controller_config['joint_position_controller_debug_vis']=False
        cfg.scene.env_spacing=10.
        # Only duration changes: the original walking/FL manipulation modes stay intact.
        assert cfg.sim.dt==.002 and cfg.decimation==5
        agent=runtime['load_cfg_from_registry'](helper.TASK,'crl2_cfg_entry_point')
        agent['seed']=42;agent['general']['num_envs']=1
        env=runtime['Crl2VecEnvWrapper'](runtime['gym'].make(helper.TASK,cfg=cfg));base=env.unwrapped
        helper._seed_everything(42,env,torch);observations,_=env.reset()
        runner=runtime['PPO'](task=helper.TASK,env=env,agent_cfg=agent,train=False,device=env.device)
        runtime['restore_runner'](runner,checkpoint,load_values=False,verify=True)
        policy=runner.get_inference_policy(device=env.device)
        assert runner.current_iteration==2000 and runner.obs_normalizer.count==100003840
        identity.update(backend=runtime['assert_physx_environment'](env),checkpoint_iteration=runner.current_iteration,
            normalizer_count=runner.obs_normalizer.count,
            normalizer_sha256={k:hashlib.sha256(v.cpu().numpy().tobytes()).hexdigest() for k,v in runner.obs_normalizer.state_dict().items()},
            original_modules={'rambo':rambo.__file__,'crl2':crl2.__file__,'QPEnv':sys.modules[type(base).__module__].__file__},
            config={'physics_dt':cfg.sim.dt,'controller_decimation':cfg.decimation,'gait':cfg.contact_generator_config,
                'QP':helper._jsonable(cfg.qp_torque_optimizer_config),'robot_usd':cfg.robot.spawn.usd_path,
                'root_init':cfg.robot.init_state.pos,'nominal_height':cfg.nominal_base_height,
                'ground_material':cfg.terrain.physics_material.to_dict(),'events':cfg.events,
                'noise':cfg.obs_noise,'randomize_initial_state':cfg.randomize_initial_state,
                'source_motor_delays':{k:v.time_lags.cpu().tolist() for k,v in base._robot.actuators.items()}},
            robot={'body_names':base._robot.data.body_names,'body_mass':base.masses.cpu().tolist(),
                   'joint_names':base._robot.data.joint_names,'joint_limits':base.default_joint_pos_limits.cpu().tolist()})
        def jsonable(v):
            if isinstance(v,np.ndarray):return v.tolist()
            if isinstance(v,torch.Tensor):return v.detach().cpu().tolist()
            if isinstance(v,dict):return {str(k):jsonable(x) for k,x in v.items()}
            if isinstance(v,(list,tuple)):return [jsonable(x) for x in v]
            if isinstance(v,Path):return str(v)
            return v
        identity=jsonable(identity)
        (out/'resolved-config.json').write_text(json.dumps(identity,indent=2,default=str)+'\n')
        robot=base._robot
        origin=int(base._sim_step_counter)
        initial_clock=(int(base.sim._physics_step_count),float(base._time_since_reset[0]))
        def tensor(v):return v.torch if hasattr(v,'torch') else v
        def state():
            data=robot.data
            fl=(base.base_rot_mat_rp@base.ee_pos_b[:,0,:,None]).squeeze(-1)[0]
            fl=fl.clone();fl[2]+=base.base_height[0]
            return {'physics_step':int(base._sim_step_counter)-origin,
                'height':float(base.base_height[0]),'root_position':tensor(data.root_link_pos_w)[0].cpu().tolist(),
                'quaternion_xyzw':tensor(data.root_link_quat_w)[0].cpu().tolist(),
                'linear_velocity_body':base.base_lin_vel_b[0].cpu().tolist(),
                'angular_velocity_body':base.base_ang_vel_b[0].cpu().tolist(),
                'gravity_error':float(torch.linalg.vector_norm(base.projected_gravity_b[0]-torch.tensor([0.,0.,-1.],device=base.device))),
                'FL_RP_height_position':fl.cpu().tolist(),
                'joint_position':base.joint_pos[0].cpu().tolist(),'joint_velocity':base.joint_vel[0].cpu().tolist(),
                'controller_elapsed_time_s':float(base._time_since_reset[0])}
        identity['initial_state']=state();identity['origin_physics_step']=origin
        identity['total_robot_mass_kg']=float(base.total_mass[0])
        # This matches the previous MuJoCo diagnostic free observer, not a task camera contract.
        look=np.array([.35,.15,.2]);dist=1.8;az=math.radians(135);el=math.radians(-24)
        eye=look+dist*np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),-math.sin(el)])
        focal=24.;vertical=2*focal*math.tan(math.radians(45)/2);horizontal=vertical*1280/720
        forward=(look-eye)/np.linalg.norm(look-eye)
        left=np.cross([0.,0.,1.],forward);left/=np.linalg.norm(left)
        up=np.cross(forward,left)
        rotation=Rotation.from_matrix(np.stack([forward,left,up],axis=1)).as_quat()
        observer_cfg=make_front_rgb_camera_cfg(prim_path='/World/RamboComparisonObserver',
            width=1280,height=720,update_period=.04,offset_pos=tuple(eye),offset_rot=tuple(rotation))
        observer_cfg.spawn.focal_length=focal
        observer_cfg.spawn.horizontal_aperture=horizontal
        observer_cfg.spawn.vertical_aperture=vertical
        observer=create_front_rgb_camera(observer_cfg)
        observer._initialize_callback(None)  # Sensor created after the already-started reference env.
        observer.reset();base.scene.sensors['comparison_observer']=observer
        identity['observer']={'position':eye.tolist(),'look_at':look.tolist(),'focal_mm':focal,
            'horizontal_aperture_mm':horizontal,'vertical_aperture_mm':vertical,'fps':25,'diagnostic_only':True}
        (out/'identity.json').write_text(json.dumps(identity,indent=2,default=str)+'\n')
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
        sinks={'observer':Sink(out/'observer.mp4',args.ffmpeg,25),'preview':Sink(out/'preview.mp4',args.ffmpeg,25,height=768)}
        def capture(phase,values,terminal=False):
            before=(int(base._sim_step_counter),int(base.sim._physics_step_count),float(base._time_since_reset[0]))
            base.sim.render();wp.to_torch(observer._is_outdated).fill_(True)
            raw=tensor(observer.data.output['rgb'])
            image=raw[0,:,:,:3].cpu().numpy().copy()
            assert before==(int(base._sim_step_counter),int(base.sim._physics_step_count),float(base._time_since_reset[0]))
            if image.shape!=(720,1280,3) or image.dtype!=np.uint8 or image.std()<1:
                raise RuntimeError('Invalid actual Isaac observer RGB')
            tick=before[0]-origin
            captures.append({'physics_step':tick,'simulation_time_ns':tick*2_000_000,'phase':phase,
                'sha256':hashlib.sha256(image.tobytes()).hexdigest(),'std':float(image.std()),'terminal':terminal,
                'render_advances_physics':False})
            img=Image.new('RGB',(1280,768),'#10151d');draw=ImageDraw.Draw(img)
            draw.text((12,7),f'ORIGINAL ISAAC / PhysX / CRL2 | model_2000 | t={tick*.002:.2f}s | {phase}',font=font,fill='white')
            draw.text((12,31),f'native9: vx={values[0]:.2f} vy={values[1]:.2f} yaw={values[2]:.2f} FL={values[3:6]}',font=font,fill='#b9e1ff')
            img.paste(Image.fromarray(image),(0,48))
            if terminal:
                Image.fromarray(image).save(out/'terminal_observer.png');img.save(out/'terminal_preview.png')
            else:
                sinks['observer'].write(image);sinks['preview'].write(np.asarray(img))
                if tick in (1760,2760,4260,5760,7260,8500):img.save(out/f'preview_{tick:05d}.png')
        # Prime rendering only. Do not use orchestrator.step or sim.step for camera warmup.
        for _ in range(3):
            base.sim.render();wp.to_torch(observer._is_outdated).fill_(True)
            raw=tensor(observer.data.output['rgb'])
        assert int(base._sim_step_counter)==origin and (int(base.sim._physics_step_count),float(base._time_since_reset[0]))==initial_clock
        init_s=time.monotonic()-start
        phase,values=command(0.)
        class Hook:
            def before_control(self,action):pass
            def after_physics(self,force,torque):
                row=state();row.update(applied_joint_effort=tensor(robot.data.applied_torque)[0].cpu().tolist(),
                    external_force=force[0].cpu().tolist(),external_torque=torque[0].cpu().tolist())
                physics_rows.append(row)
            def after_control(self):pass
            def before_reset(self,ids):
                capture('unexpected_terminal',values,terminal=True)
                raise RuntimeError('Original Isaac episode terminated before diagnostic completion; automatic reset prevented')
        base._v2_recorder=Hook()
        original_grf=base.torque_optimizer.get_grf
        def passive_grf():
            result=original_grf()
            qp_rows.append({'physics_step':int(base._sim_step_counter)-origin,
                'desired_acceleration':base.torque_optimizer.desired_acc[0].cpu().tolist(),
                'desired_acceleration_body':result[2][0].cpu().tolist(),'solved_acceleration_body':result[3][0].cpu().tolist(),
                'desired_angular_velocity':base.torque_optimizer._desired_angular_velocity[0].cpu().tolist(),
                'residual_angular_acceleration':base.torque_optimizer._desired_angular_acceleration[0].cpu().tolist()})
            return result
        base.torque_optimizer.get_grf=passive_grf
        for control in range(1800):
            if control%2==0:
                phase,values=command(control/100)
                base._velocity_commands[:]=torch.tensor(values[:3],device=base.device)
                base._ee_pos_commands[:]=torch.tensor(values[3:6],device=base.device)
                base._ee_force_commands[:]=0
            if control%4==0:capture(phase,values)
            with torch.inference_mode():
                obs_rows.append(observations[0].cpu().numpy().copy())
                action=policy(observations);actions.append(action[0].cpu().numpy().copy())
                assert action.shape==(1,18) and torch.isfinite(action).all()
                observations,rewards,dones,extras=env.step(action)
                assert observations.shape==(1,405) and torch.isfinite(observations).all()
            row=state();row.update(phase=phase,command=values,command_consumed=base._velocity_commands[0].cpu().tolist())
            rows.append(row)
            if row['height']<.1 or row['gravity_error']>.75 or bool(dones[0]):raise RuntimeError('Original fall/termination criterion triggered')
            assert row['physics_step']==(control+1)*5
            if control%100==0:print('ISAAC',control/100,phase,row['linear_velocity_body'],row['angular_velocity_body'],flush=True)
        capture('terminal',values,terminal=True)
        assert_state_dict_equal('unchanged_policy',runner.policy.state_dict(),checkpoint['policy_dict'])
        assert_state_dict_equal('unchanged_normalizer',runner.obs_normalizer.state_dict(),checkpoint['obs_normalizer'])
        assert runner.obs_normalizer.count==100003840
        assert source_identity(ref)['original_source_sha256']==identity['original_source_sha256']
        result={'status':'completed','run_through_passed':True,'actor_forward_calls':len(actions),
            'weights_and_normalizer_verified':True,'initialization_s':init_s,
            'backend_after':runtime['assert_physx_environment'](env)}
    except BaseException as error:
        result={'status':'failed','run_through_passed':False,'error':type(error).__name__+': '+str(error),'traceback':traceback.format_exc()}
        print(result['traceback'],flush=True)
    finally:
        for name,sink in sinks.items():
            try:sink.close()
            except Exception as error:result.setdefault('encoder_errors',{})[name]=str(error)
        import numpy as np
        np.savez_compressed(out/'actor_tensors.npz',observations=np.asarray(obs_rows),actor_residual=np.asarray(actions))
        for name,data in (('telemetry',rows),('physics',physics_rows),('captures',captures),('qp',qp_rows)):
            (out/(name+'.jsonl')).write_text(''.join(json.dumps(row,allow_nan=False)+'\n' for row in data))
        result.update(elapsed_s=time.monotonic()-start,control_ticks=len(rows),
            physics_ticks=rows[-1]['physics_step'] if rows else 0,frames={k:s.count for k,s in sinks.items()},
            checkpoint_sha256=sha(args.checkpoint),asset_migration_executed=False,retraining_executed=False)
        result['phase_metrics']={}
        for name,begin,end in PHASES:
            selected=[r for r in rows if r['phase']==name and r['physics_step']*.002>=begin+1]
            if not selected:continue
            fl=np.array([r['FL_RP_height_position'] for r in selected]);target=np.array(selected[0]['command'][3:6])
            result['phase_metrics'][name]={'mean_body_velocity':np.mean([r['linear_velocity_body'] for r in selected],axis=0).tolist(),
                'mean_body_angular_velocity':np.mean([r['angular_velocity_body'] for r in selected],axis=0).tolist(),
                'FL_error_norm_mean':float(np.linalg.norm(fl-target,axis=1).mean()),
                'height_range':[min(r['height'] for r in selected),max(r['height'] for r in selected)],
                'root_displacement_world':(np.array(selected[-1]['root_position'])-selected[0]['root_position']).tolist()}
        (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        if env is not None:env.close()
        if launcher is not None:launcher.app.close()
    if result['status']!='completed' or result.get('encoder_errors'):raise SystemExit(1)


if __name__=='__main__':main()
