"""Bounded approved Lift Basket collection, with explicit work/scenario provenance."""
import argparse,hashlib,json,os,subprocess,sys,traceback
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"source/rambo"))
import numpy as np


def main():
    from isaaclab.app import AppLauncher
    from rambo.utils.physx import validate_rambo_visualizer_args
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ffmpeg',required=True)
    p.add_argument('--resource-root',type=Path,default=os.environ.get('QLM_RESOURCE_ROOT'))
    p.add_argument('--asset-id')
    p.add_argument('--checkpoint',type=Path)
    p.add_argument('--episode-config',type=Path)
    p.add_argument('--mode',choices=['terminal-gate','pilot','demonstration'],required=True)
    p.add_argument('--work-id',default='DATA-009')
    p.add_argument('--scenario-id',default='nominal')
    p.add_argument('--offset-x',type=float,default=0.)
    p.add_argument('--offset-y',type=float,default=0.)
    p.add_argument('--pilot-gate',type=Path)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--terminal-gate',type=Path)
    p.add_argument('--max-actions',type=int,default=500)
    AppLauncher.add_app_launcher_args(p);args=p.parse_args();validate_rambo_visualizer_args(p,args,sys.argv[1:]);args.enable_cameras=True
    repo=Path(__file__).resolve().parents[2]
    if args.resource_root is None:p.error('--resource-root or QLM_RESOURCE_ROOT is required')
    profile=json.loads((repo/'configs/lift_basket_v2.json').read_text())
    if profile['approval']['status']!='approved':raise ValueError('Asset/task approval required')
    watched=[repo/name for name in ['source/rambo/rambo/recording_v2.py','source/rambo/rambo/recording_lift_v2.py','source/rambo/rambo/tasks/direct/rambo_quadruped/qp_env.py','source/rambo/rambo/tasks/direct/rambo_quadruped/lift_basket_v2.py','source/rambo/rambo/tasks/common/lift_basket_geometry.py','source/rambo/rambo/tasks/common/lift_basket_expert.py','configs/lift_basket_v2.json','scripts/rambo/collect_lift_basket_v2.py']]
    watched.extend(repo/name for name in ['source/rambo/rambo/tasks/direct/rambo_quadruped/native9_task_env.py','source/rambo/rambo/tasks/common/episode.py','source/rambo/rambo/tasks/common/environment_factory.py','source/rambo/rambo/tasks/common/snapshots.py'])
    implementation={str(f.relative_to(repo)):hashlib.sha256(f.read_bytes()).hexdigest() for f in watched}
    expansion=None;scenario=dict(id=args.scenario_id,seed=42)
    if not np.isfinite([args.offset_x,args.offset_y]).all() or abs(args.offset_x)>.010000001 or abs(args.offset_y)>.005000001:
        raise ValueError('Only approved X +/-1cm and Y +/-0.5cm offsets')
    if args.mode=='demonstration':
        approved=json.loads(args.pilot_gate.read_text()) if args.pilot_gate else {}
        if not approved.get('user_accepted') or approved.get('pilot_uid')!='pilot-a6' or not approved.get('local_only'):
            raise ValueError('Explicit accepted a6/local batch record required')
        for name,expected in approved['implementation'].items():
            if name!='scripts/rambo/collect_lift_basket_v2.py' and implementation.get(name) not in approved.get('allowed_implementation_sha256',{}).get(name,[expected]):
                raise ValueError('Accepted a6 implementation changed: '+name)
    scenario.update(offset_x_m=args.offset_x,offset_y_m=args.offset_y)
    profile['primary_position'][0]+=args.offset_x;profile['primary_position'][1]+=args.offset_y
    profile['lift_goal_position'][0]+=args.offset_x;profile['lift_goal_position'][1]+=args.offset_y

    if args.mode!='terminal-gate':
        gate=json.loads(args.terminal_gate.read_text()) if args.terminal_gate else {}
        if not gate.get('passed') or gate.get('implementation')!=implementation:raise ValueError('Current terminal gate required')
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
        from rambo.tasks.direct.rambo_quadruped.lift_basket_v2 import LiftBasketV2Env,asset_vertices
        from rambo.assets import BASKET_INITIAL_ORIENTATION_XYZW
        import rambo
        if not Path(rambo.__file__).resolve().is_relative_to(repo.resolve()):raise RuntimeError("Wrong RAMBO source checkout")
        from rambo.recording_lift_v2 import LiftRecorder as Recorder
        from rambo.tasks.common.lift_basket_expert import command as expert_command
        if {str(f.relative_to(repo)):hashlib.sha256(f.read_bytes()).hexdigest() for f in watched}!=implementation:
            raise RuntimeError('Source changed during simulator startup; refuse ambiguous execution provenance')
        from rambo.contracts_v2.runtime import prepare_command
        from rambo.tasks.common.environment_factory import make_collection_config,make_environment,LIFT_BASKET_TASK_ID,resolve_task_asset
        task=LIFT_BASKET_TASK_ID
        asset=resolve_task_asset(profile,args.resource_root,args.asset_id)
        cfg=make_collection_config(task,seed=(expansion['parameters']['seed'] if expansion else 42),
                                   max_actions=(32 if args.mode=='terminal-gate' else args.max_actions),
                                   profile=profile,asset_path=str(asset))
        cfg.primary_position=tuple(profile['primary_position']);cfg.primary_orientation=BASKET_INITIAL_ORIENTATION_XYZW
        report['initial_geometry']=dict(basket_pose=[*cfg.primary_position,*cfg.primary_orientation],robot_config_position=list(cfg.robot.init_state.pos),geometry_method='actual source vertices including authored scale; convex hull exact extrema')
        cfg.pilot_max_physics_steps=(32 if args.mode=='terminal-gate' else args.max_actions)*10
        env=make_environment(cfg,environment_type=LiftBasketV2Env);be=env.unwrapped
        report["foot_geometry"]=be.configure_foot_geometry()
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
        contract=contract_for_task(LIFT_BASKET_TASK_ID)
        from qlm_bench.assets import resolve_asset
        checkpoint=load_verified_checkpoint(args.checkpoint or resolve_asset('rambo-go2-controller',args.resource_root),contract)
        agent=load_cfg_from_registry(task,'crl2_cfg_entry_point');agent['general']['num_envs']=1;agent['seed']=expansion['parameters']['seed'] if expansion else 42
        runner=PPO(task=task,env=env,agent_cfg=agent,train=False,device=be.device);restore_runner(runner,checkpoint,load_values=False,verify=True);policy=runner.get_inference_policy(device=be.device)
        rec.begin();initial=rec.boundaries[0]
        for k in range(cfg.pilot_max_physics_steps//10):
            time=be.simulation_time_ns/1e9
            request,expert=expert_command(be,time)
            prepared=prepare_command(request,f'{args.mode}:{k}',be.episode_tick);prepared['extensions']['expert']=expert;rec.submit(prepared)
            be.submit_native9_command(prepared)
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
        capture=rec.close(dict(work_id=args.work_id,scenario=scenario,mode=args.mode,diagnostic_only=args.mode!='demonstration',profile=profile,implementation=implementation,checkpoint_sha256=contract.sha256,source_commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),status=status,task_text=profile['task_text'],initial_geometry=report['initial_geometry'],foot_geometry=report['foot_geometry'],post_reset_state=after))
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
