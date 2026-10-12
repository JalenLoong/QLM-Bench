"""Task-owned real Push wave capture; packaging stays in the CPU data process."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time


def main(argv=None):
    raw=list(sys.argv[1:] if argv is None else argv)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--conditions',type=Path,required=True)
    p.add_argument('--output-root',type=Path,required=True)
    p.add_argument('--uid',action='append',required=True)
    p.add_argument('--attempt',type=int,default=1)
    p.add_argument('--resource-root',type=Path,required=True)
    p.add_argument('--ffmpeg',required=True)
    p.add_argument('--horizon',type=float,default=24.)
    p.add_argument('--diagnostic',action='store_true')
    from isaaclab.app import AppLauncher
    from rambo.utils.physx import validate_rambo_visualizer_args
    AppLauncher.add_app_launcher_args(p)
    args=p.parse_args(raw);validate_rambo_visualizer_args(p,args,raw);args.enable_cameras=True
    definitions=json.loads(args.conditions.read_text())['slots']
    cases=[next(s['case'] for s in definitions if s['metadata']['episode_uid']==uid and s['source']=='new') for uid in args.uid]
    from rambo.tasks.common.push_box_retry import realization_ordinal
    ordinals=[realization_ordinal(args.output_root,case['metadata'],args.attempt) for case in cases]
    if len(set(ordinals))!=1:p.error('Wave requires equal retry realization ordinal')
    ordinal=ordinals[0]
    if ordinal >= 3:
        # Retry stays in the frozen asset/difficulty/trajectory envelope; all
        # accepted realized conditions are retained in the capture profile.
        from rambo.tasks.common.push_box_scaleup_plan import resolve_case
        for index, case in enumerate(cases):
            case=copy.deepcopy(case);old=case['profile']
            asset_bounds=json.loads((args.conditions.parent/'asset-pool.json').read_text())['assets'][case['metadata']['asset_id']]
            old_angle=round(float(__import__('math').degrees(__import__('math').atan2(case['orientation'][2],case['orientation'][3])*2)))%360
            yaw=0 if case['metadata']['difficulty']=='clean' else (old_angle+90*(ordinal-2))%360
            realized=resolve_case(old,low=asset_bounds['low'],high=asset_bounds['high'],seed=case['seed']+ordinal,
                clean=case['metadata']['difficulty']=='clean',recovery=case['metadata']['trajectory_type']=='recovery',yaw_deg=yaw)
            realized['metadata']=case['metadata'];realized['profile']['scaleup_metadata']=case['metadata']
            realized['profile']['retry_realized_condition']={'attempt':args.attempt,'realization_ordinal':ordinal,'seed':realized['seed'],'yaw_deg':yaw,'original_condition_id':case['metadata']['initial_condition_id']}
            cases[index]=realized
    group={(c['metadata']['asset_id'],c['metadata']['appearance_preset']) for c in cases}
    if len(group)!=1:p.error('Wave shares asset and appearance preset')
    from qlm_bench.collection.orchestrator import source_identity
    source=source_identity();outdirs=[args.output_root/'attempts'/f'{uid}__a{args.attempt:02d}' for uid in args.uid]
    if any(path.exists() for path in outdirs):p.error('Refuse attempt overwrite')
    for out in outdirs:out.mkdir(parents=True)
    app=runtime=None;recorders=[];closed=set();started=time.monotonic();code=1
    try:
        app=AppLauncher(args)
        import numpy as np
        import torch
        import omni.replicator.core as rep
        from PIL import Image
        from qlm_bench.assets import resolve_asset
        from rambo.tasks.common.batch_controller_runtime import BatchControllerRuntime
        from rambo.recording_v2 import Recorder
        from rambo.recording_batch import BatchRecorderMux
        from rambo.contracts_v2.runtime import prepare_command
        from qlm_bench.collection.batch import collect_wave
        from rambo.tasks.common.push_box_scaleup_plan import PRESETS
        from rambo.tasks.common.environment_factory import PUSH_BOX_TASK_ID
        profile=copy.deepcopy(cases[0]['profile'])
        profile.update(scaleup_lane_cases=cases,scaleup_appearance=PRESETS[cases[0]['metadata']['appearance_preset']])
        observer_handles=[]
        def attach(created):
            env=created.base_env;geometry=profile['observer']
            for i,out in enumerate(outdirs):
                offset=env._terrain.env_origins[i].cpu().numpy()
                camera=rep.create.camera(position=(np.asarray(geometry['position'])+offset).tolist(),look_at=(np.asarray(geometry['look_at'])+offset).tolist(),focal_length=24)
                product=rep.create.render_product(camera,(1280,720));rgb=rep.AnnotatorRegistry.get_annotator('rgb',device='cpu');rgb.attach(product)
                observer_handles.append((camera,product,rgb))
                recorders.append(Recorder(env,out/'raw'/args.uid[i],args.ffmpeg,rgb,env_index=i))
        runtime=BatchControllerRuntime(PUSH_BOX_TASK_ID,num_envs=len(cases),profile=profile,resource_root=args.resource_root,
                                       episode_length_s=args.horizon,seed=42,on_environment_ready=attach)
        after=source_identity()
        if any(source.get(k)!=after.get(k) for k in ('source_commit','dirty_source_sha256')):
            raise RuntimeError('Source changed during startup')
        runtime.prime_render()
        env=runtime.base_env
        for _ in range(4):env.sim.render()
        mux=BatchRecorderMux(env,recorders)
        initial=[env.review_lane(i) for i in range(env.num_envs)]
        original_step=runtime.step;progress_count=0;inspection_saved=set()
        def step_with_progress(commands):
            nonlocal progress_count
            result=original_step(commands);progress_count+=1
            for index,uid in enumerate(args.uid):
                diagnostic=env.expert_lanes[index].get('_expert_diagnostics') or {}
                if index not in inspection_saved and diagnostic.get('large_goal_evidence',{}).get('visual_relationship_verified'):
                    from rambo.tasks.common.snapshots import capture_rgb
                    pixels,_,_=capture_rgb(env,index);folder=outdirs[index]/'look-again';folder.mkdir(exist_ok=True)
                    for view,frame in pixels.items():Image.fromarray(frame).save(folder/(view+'.png'))
                    (folder/'evidence.json').write_text(json.dumps({'simulation_time_ns':env.lane_tick(index)*2_000_000,
                        'evidence':diagnostic['large_goal_evidence']},indent=2)+'\n');inspection_saved.add(index)
            if progress_count%50==0:
                rows=[]
                for index,uid in enumerate(args.uid):
                    review=env.review_lane(index);diagnostic=review.get('expert') or {}
                    rows.append({'uid':uid,'simulation_seconds':env.lane_tick(index)/500,
                        'active':bool(env.lane_active[index]),'phase':diagnostic.get('phase'),
                        'geometry':review['footprint_xy'],'recovery_evidence':diagnostic.get('large_goal_evidence',diagnostic.get('goal_recovery_evidence'))})
                args.output_root.mkdir(parents=True,exist_ok=True)
                tmp=args.output_root/'progress.tmp.json';tmp.write_text(json.dumps({'lanes':rows})+'\n');tmp.replace(args.output_root/'progress.json')
            return result
        runtime.step=step_with_progress
        with torch.inference_mode():
            wave=collect_wave(runtime,mux,prepare_command=prepare_command,max_actions=round(args.horizon*50),command_prefix='QLM-DATA-001')
        reports=[]
        for index,(out,recorder,case) in enumerate(zip(outdirs,recorders,cases)):
            terminal=env.lanes[index].terminal
            if terminal is None or recorder.terminal is None:
                raise RuntimeError('Wave produced no owned terminal for '+args.uid[index])
            status='failure' if terminal['fallen'] else 'success' if terminal['success'] else 'failure'
            outcome='fall' if terminal['fallen'] else 'success' if terminal['success'] else 'timeout'
            full=not recorder.terminal['partial_interval'] and len(recorder.boundaries)==len(recorder.commands)+1
            p_lane=env.profile_for_lane(index)
            p_lane['scaleup_metadata']=case['metadata']
            capture=recorder.close(dict(work_id='QLM-DATA-001',scenario={'id':args.uid[index],'seed':case['seed'],'asset':case['metadata']['asset_id'],'appearance':case['metadata']['appearance_preset']},
                mode='diagnostic' if args.diagnostic else 'demonstration',diagnostic_only=args.diagnostic,profile=p_lane,
                implementation=source.get('implementation',{}),source_commit=source['source_commit'],source_identity=source,
                checkpoint_sha256=runtime.contract.sha256,status=status,task_text='Push the box into the target area.',
                initial_geometry=initial[index],post_reset_state=runtime.state()[index]['state']))
            closed.add(index)
            summary=dict(passed=full,status=status,outcome=outcome,terminal_before_reset=True,n_actions=len(recorder.commands),n_boundaries=len(recorder.boundaries),
                         initial_geometry=initial[index],scenario=capture['scenario'],mode=capture['mode'],source=source)
            if p_lane.get('large_goal_recovery'):
                events=[c['extensions']['expert'].get('large_goal_evidence') for c in recorder.commands if c['extensions']['expert'].get('large_goal_evidence',{}).get('major_failure_reproduced')]
                verified=outcome=='success' and bool(events) and any(e['trigger_inside_y_ratio']<=.4
                    and e['braked_actual_velocity'] and e['backward_distance_m']>=.15 and e['left_shift_m']>=.12
                    and e['visual_relationship_verified'] and e['inward_push'] and e['inward_box_displacement_m']>=.1 for e in events)
                summary.update(recovery_verified=verified,recovery_kind='large_goal_overflow_reacquire',recovery_evidence=events[-1] if events else None)
            elif p_lane.get('scaleup_goal_recovery'):
                events=[c['extensions']['expert'].get('goal_recovery_evidence') for c in recorder.commands if c['extensions']['expert'].get('goal_recovery_evidence',{}).get('triggered')]
                verified=bool(events) and any(.005<=e['trigger_overflow_m']<=.07 and e['trigger_overlap']>=.78
                    and e['progress_before_m']>=.10 and e['braked_actual_forward_velocity']
                    and e['body_shift_signed_m']>=.05 and e['inward_stroke'] for e in events)
                summary['recovery_verified']=verified;summary['recovery_kind']='goal_side_overflow'
                summary['recovery_evidence']=events[-1] if events else None
            elif case['metadata']['trajectory_type']=='recovery':
                events=[c['extensions']['expert'].get('recovery_evidence') for c in recorder.commands if c['extensions']['expert'].get('recovery_evidence')]
                verified=bool(events) and max(e['progress_before'] for e in events)>=.10 and max(e['max_separation'] for e in events)>=.045 and any(e['corrected'] for e in events)
                summary['recovery_verified']=verified
            else:summary['recovery_verified']=True
            if p_lane.get('scaleup_motion_revision')=='continuous-v2':
                points=[c for c in recorder.commands if 3.<=c['start_tick']/500<=5.5]
                changes=[float(np.linalg.norm(np.asarray(b['requested'][3:6])-a['requested'][3:6])) for a,b in zip(points,points[1:])]
                summary['approach_max_native_target_step_m']=max(changes or [0.])
                summary['approach_continuity_verified']=summary['approach_max_native_target_step_m']<.025
            (out/'raw'/args.uid[index]/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
            (out/'result.json').write_text(json.dumps(summary,indent=2)+'\n');reports.append({k:v for k,v in summary.items() if k!='source'})
        print('PUSH_SCALEUP_WAVE_RESULT='+json.dumps({'wave':wave,'reports':reports,'wall_seconds':time.monotonic()-started}),flush=True)
        code=0
    except BaseException as error:
        import traceback;traceback.print_exc()
        for out in outdirs:
            if not (out/'result.json').exists():(out/'runtime-error.json').write_text(json.dumps({'type':type(error).__name__,'reason':str(error)},indent=2)+'\n')
    finally:
        for index,recorder in enumerate(recorders):
            if index not in closed:
                try:recorder.close({'invalid':True,'diagnostic_only':True})
                except Exception:pass
        if runtime is not None:runtime.close()
        if app is not None:app.app.close(exit_code=code)
    return code


if __name__=='__main__':raise SystemExit(main())
