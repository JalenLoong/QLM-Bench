"""Bounded approved Press Button collection, with explicit work/scenario provenance."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys,traceback
from pathlib import Path
import numpy as np


def main():
    from isaaclab.app import AppLauncher
    from rambo.utils.physx import validate_rambo_visualizer_args
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ffmpeg',required=True)
    p.add_argument('--episode-config',type=Path)
    p.add_argument('--mode',choices=['terminal-gate','pilot','demonstration'],required=True)
    p.add_argument('--work-id',default='DATA-008')
    p.add_argument('--scenario-id',default='nominal')
    p.add_argument('--offset-x',type=float,default=0.)
    p.add_argument('--offset-y',type=float,default=0.)
    p.add_argument('--pilot-gate',type=Path)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--terminal-gate',type=Path)
    p.add_argument('--max-actions',type=int,default=500)
    AppLauncher.add_app_launcher_args(p);args=p.parse_args();validate_rambo_visualizer_args(p,args,sys.argv[1:]);args.enable_cameras=True
    root=Path(os.environ['WORKSPACE_ROOT']);repo=Path(__file__).resolve().parents[2]
    profile=json.loads((repo/'configs/press_button_v2.json').read_text())
    if profile['approval']['status']!='approved':raise ValueError('Asset/task approval required')
    watched=[repo/p for p in ['source/rambo/rambo/recording_v2.py','source/rambo/rambo/tasks/direct/rambo_quadruped/qp_env.py','source/rambo/rambo/tasks/direct/rambo_quadruped/press_button_v2.py','configs/press_button_v2.json','scripts/rambo/collect_press_button_v2.py','source/rambo/rambo/dataset_v2/task_state.py','source/rambo/rambo/tasks/common/press_button_logic.py','source/rambo/rambo/tasks/common/press_button_expert.py','source/rambo/rambo/tasks/direct/rambo_quadruped/push_box_v2.py','source/rambo/rambo/tasks/direct/rambo_quadruped/object_tasks_env.py']]
    watched.append(repo/'configs/press_button_collection_v1.json')
    implementation={str(f.relative_to(repo)):hashlib.sha256(f.read_bytes()).hexdigest() for f in watched}
    expansion=None;scenario=dict(id=args.scenario_id,seed=42,task='press_button')
    if args.episode_config:
        case=json.loads(args.episode_config.read_text())
        if case['work_id']!='DATA-010' or case['authorization']!='press-button-collection-v1' or args.work_id!='DATA-010' or args.mode not in ('terminal-gate','demonstration'):raise ValueError('Invalid local batch scope')
        profile=case['profile'];scenario={**case['scenario'],'attempt_parameters':case['attempt']};expansion={'parameters':{'seed':case['seed']}}
        if profile['approval']['status']!='approved' or profile['task_profile_version']!='press-button-v2-1':raise ValueError('Unapproved batch profile')
    elif args.mode not in ('terminal-gate','pilot') or args.work_id!='DATA-008':raise ValueError('Only approved pilot or explicit batch')
    if args.mode!='terminal-gate':
        gate=json.loads(args.terminal_gate.read_text()) if args.terminal_gate else {}
        if not gate.get('passed') or gate.get('implementation')!=implementation:raise ValueError('Current implementation requires passed real terminal gate')
        if expansion and gate['profile'].get('collection_asset')!=profile['collection_asset']:raise ValueError('Asset-specific terminal gate required')
    if not 1<=args.max_actions<=1000:raise ValueError('Bounded <=20s only')
    args.output_dir.mkdir(parents=True,exist_ok=False)
    out=args.output_dir.resolve();report=dict(work_id=args.work_id,scenario=scenario,mode=args.mode,passed=False,implementation=implementation,profile=profile,dataset_episode=args.mode!='terminal-gate')
    app=rec=None;code=1
    try:
        app=AppLauncher(args)
        import torch,omni.replicator.core as rep
        from PIL import Image
        from crl2.algorithms import PPO
        from rambo.rl import Crl2VecEnvWrapper
        from rambo.utils.registry import parse_env_cfg,load_cfg_from_registry
        from rambo.utils.physx import configure_physx,assert_physx_environment
        from rambo.validation.checkpoints import contract_for_task,load_verified_checkpoint,restore_runner
        from rambo.tasks.direct.rambo_quadruped.press_button_v2 import PressButtonV2Env
        from rambo.recording_v2 import Recorder,json_write
        from rambo.tasks.common.push_box_geometry import source_geometry,world_geometry
        from rambo.tasks.common.press_button_expert import command as expert_command
        if {str(f.relative_to(repo)):hashlib.sha256(f.read_bytes()).hexdigest() for f in watched}!=implementation:
            raise RuntimeError('Source changed during simulator startup; refuse ambiguous execution provenance')
        from rambo.contracts_v2.runtime import prepare_command
        spec=importlib.util.spec_from_file_location('pilot_teleop',repo/'scripts/rambo/teleop_loco_manip.py');teleop=importlib.util.module_from_spec(spec);spec.loader.exec_module(teleop)
        task='Isaac-RAMBO-Quadruped-Press-Button-V2-Go2-v0'
        cfg=parse_env_cfg(task,device='cuda:0',num_envs=1,use_fabric=True)
        teleop._configure_environment(cfg,argparse.Namespace(task=teleop.LIFT_BASKET_TASK_ID,seed=(expansion['parameters']['seed'] if expansion else 42),episode_length_s=24.,view='third-person',camera_setup='robot-dual-v3'))
        configure_physx(cfg);cfg.sim.render_interval=10
        cfg.front_camera.update_period=.02;cfg.task_camera.update_period=.02
        cfg.terminate_on_body_contact=False;cfg.terminate_on_limb_contact=False;cfg.terminate_on_undesired_foot_contact=False
        asset=root/profile['asset_path'];assert hashlib.sha256(asset.read_bytes()).hexdigest()==profile['asset_sha256']
        cfg.approved_asset_path=str(asset);cfg.approved_profile=profile
        cfg.primary_orientation=(0.,0.,0.,1.);cfg.primary_position=tuple(profile['asset_origin_xyz'])
        for rel,expected in profile['asset_bundle_sha256'].items():
            if hashlib.sha256((asset.parent/rel).read_bytes()).hexdigest()!=expected:raise ValueError('Asset bundle changed')
        report['initial_geometry']=dict(button_front_world=profile['button_rest_front_xyz'],press_axis_world=profile['press_axis_world'],cap_root_world=profile['asset_origin_xyz'],cap_diameter_m=profile['cap_diameter_m'],robot_config_position=list(cfg.robot.init_state.pos))
        cfg.pilot_max_physics_steps=(32 if args.mode=='terminal-gate' else args.max_actions)*10
        env=Crl2VecEnvWrapper(PressButtonV2Env(cfg));be=env.unwrapped
        observer=rep.create.camera(position=profile['observer']['position'],look_at=profile['observer']['look_at'],focal_length=24)
        rp=rep.create.render_product(observer,(1280,720));rgb=rep.AnnotatorRegistry.get_annotator('rgb',device='cpu');rgb.attach(rp)
        rec=Recorder(be,out,args.ffmpeg,rgb);be._v2_recorder=rec
        # Track reset entry/exit around the unmodified existing reset implementation.
        reset=be._reset_idx;events=[]
        def observed_reset(ids):
            if rec.active:raise RuntimeError('Reset attempted before terminal capture was sealed')
            if rec.terminal is not None:events.append('reset_enter_after_terminal_copy')
            value=reset(ids)
            if rec.terminal is not None:events.append('reset_exit')
            return value
        be._reset_idx=observed_reset
        obs,_=env.reset()
        for _ in range(4):be.sim.render()
        contract=contract_for_task(teleop.LIFT_BASKET_TASK_ID)
        checkpoint=load_verified_checkpoint(root/'checkpoints/rambo/go2/quadruped/model_2000.pt',contract)
        agent=load_cfg_from_registry(task,'crl2_cfg_entry_point');agent['general']['num_envs']=1;agent['seed']=expansion['parameters']['seed'] if expansion else 42
        runner=PPO(task=task,env=env,agent_cfg=agent,train=False,device=be.device);restore_runner(runner,checkpoint,load_values=False,verify=True);policy=runner.get_inference_policy(device=be.device)
        rec.begin();initial=rec.boundaries[0]
        for k in range(cfg.pilot_max_physics_steps//10):
            time=rec.ns/1e9
            request,expert=expert_command(be,time)
            prepared=prepare_command(request,f'{args.mode}:{k}',rec.tick);prepared['extensions']['expert']=expert;rec.submit(prepared)
            cmd=torch.tensor([prepared['filtered']],device=be.device,dtype=torch.float32)
            be.set_loco_manip_commands(cmd[:,:3],cmd[:,3:6],cmd[:,6:])
            for _ in range(2):
                with torch.inference_mode():
                    action=policy(obs)
                    if not torch.isfinite(action).all():raise ValueError('Nonfinite residual')
                    obs,_,done,_=env.step(action)
                if done.any():break
            if rec.terminal is not None:break
            rec.capture_boundary()
            if k%50==0:print(f'PILOT k={k} t={time:.2f} center={be.geometric_center[0].cpu().tolist()}',flush=True)
        if rec.terminal is None:raise ValueError('Missing terminal hook')
        if rec.terminal['partial_interval']:raise ValueError('Partial final action preserved; invalid episode')
        for _ in range(4):be.sim.render()
        after=rec.state();changes={}
        for role,sensor in [('ego',be.front_camera),('task_centric',be.task_camera)]:
            v=rec.arr(sensor.data.output['rgb'].torch[0]);Image.fromarray(v).save(out/'review'/f'post_reset_{role}.png')
            changes[role]=dict(pre_reset_sha256=hashlib.sha256(rec.terminal_rgb[role].tobytes()).hexdigest(),post_reset_sha256=hashlib.sha256(v.tobytes()).hexdigest(),mean_absolute_pixel_difference=float(np.abs(v.astype(float)-rec.terminal_rgb[role].astype(float)).mean()))
            assert changes[role]['pre_reset_sha256']==rec.terminal['rgb_hashes'][role]
        state_delta=float(np.max(np.abs(np.asarray(after['observation.state.base.position'])-np.asarray(rec.terminal['state']['observation.state.base.position']))))
        assert events==['reset_enter_after_terminal_copy','reset_exit']
        assert state_delta>1e-5 and all(v['mean_absolute_pixel_difference']>0 for v in changes.values())
        assert len(rec.boundaries)==len(rec.commands)+1
        for role in ['ego','task_centric']:
            ids=[x['sensor_frame_ids'][role] for x in rec.boundaries]
            assert all(b>a for a,b in zip(ids,ids[1:])),(role,ids)
        status='success' if rec.terminal['state']['task.success'][0] else 'failure'
        capture=rec.close(dict(work_id=args.work_id,scenario=scenario,mode=args.mode,diagnostic_only=args.mode!='demonstration',profile=profile,implementation=implementation,checkpoint_sha256=contract.sha256,source_commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),status=status,task_text='Press the button.',initial_geometry=report['initial_geometry'],post_reset_state=after))
        report.update(passed=True,terminal_before_reset=True,terminal_simulation_time_ns=rec.terminal['simulation_time_ns'],n_actions=len(rec.commands),n_boundaries=len(rec.boundaries),reset_events=events,terminal_vs_reset=changes,state_difference_m=state_delta,status=status,physics=assert_physx_environment(env),contact_provenance='unknown_diagnostic_only')
        code=0
    except BaseException:
        report['error']=traceback.format_exc();print(report['error'],flush=True)
        if rec is not None:
            try:rec.close(dict(invalid=True,mode=args.mode,profile=profile))
            except Exception:pass
    finally:
        (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print('PILOT_RESULT '+json.dumps(report),flush=True)
        if app is not None:app.app.close(exit_code=code)
    return code
if __name__=='__main__':raise SystemExit(main())
