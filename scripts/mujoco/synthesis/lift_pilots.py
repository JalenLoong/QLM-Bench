"""Approved ten-slot Lift campaign; independent physics and render-only workers.

One immutable recording profile per successful slot permits bounded backlifture.
The campaign, rather than individual render profiles, owns the exact2/8 quota.
"""
import argparse
import concurrent.futures as futures
import copy
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
from qlm_bench.backends.mujoco.trace import sha, write_json, verify_trace
from qlm_bench.compatibility.dataset_v2.validation import digest

REPO = Path(__file__).resolve().parents[3]
WORKSPACE = REPO.parents[1]
DATA = WORKSPACE / 'data/qlm_bench/lift-approved-pilot-20261015-v1'
WORK_ID = 'QLM-DATA-021'


def implementation():
    return {str(p.relative_to(REPO)): sha(p) for folder in ('src/qlm_bench', 'scripts/mujoco/synthesis')
            for p in sorted((REPO / folder).rglob('*')) if p.suffix in ('.py', '.json')}


def prepare(root):
    import mujoco
    from scipy.spatial.transform import Rotation
    from qlm_bench.backends.mujoco.resources import resource_closure
    approval=json.loads((root/'approval.json').read_text())
    if not all(approval[k] for k in ('reference_quality_approved','retarget_scope_approved','asset_pool_approved')):
        raise ValueError('Explicit asset/reference/scope approval required')
    reference_root=WORKSPACE/'runs/audit/lift-reference-20261015-v1'
    reference=verify_trace(reference_root/'nominal-a03/trace')[0]
    backgrounds=json.loads((reference_root/'backgrounds/backgrounds.json').read_text())['profiles']
    models={p['preset']:Path(p['model']) for p in backgrounds}
    config=json.loads((root/'recipe-config.json').read_text())
    if sha(root/'recipe-config.json')!=approval['approved_recipe_sha256']:
        raise ValueError('Approved recipe differs')
    template_root=root/'template';template_root.mkdir(exist_ok=False)
    template={'template_id':'lift-body-lane-geometry-v2-approved-20261015','recipe_config':config,
        'approved_recipe_sha256':approval['approved_recipe_sha256'],
        'approved_reference_trace_manifest_sha256':approval['approved_reference_trace_manifest_sha256']}
    write_json(template_root/'template.json',template)
    compiled=mujoco.MjModel.from_xml_path(str(models['ap_00']));adr=int(compiled.joint('object_free').qposadr[0])
    centers=[(.003,-.003,.3),(-.003,.003,-.3)]
    centers += [(x,y,z) for x in (-.03,.03) for y in (-.03,.03) for z in (-5.,5.)]
    presets=['ap_00','ap_00']+['ap_00','ap_01','ap_01','ap_00','ap_01','ap_00','ap_00','ap_01']
    rng=np.random.default_rng(2026101521);seen=set();slots=[]
    for i,center in enumerate(centers):
        uid=f'lift-approved-20261015-{i+1:02d}';preset=presets[i];model=models[preset]
        identity=resource_closure(model,require_portable=True)['identity'];candidates=[]
        for j in range(5):
            for draw in range(100):
                values=np.asarray(center,float).copy()
                if j:values+=rng.uniform(-1,1,3)*([.0005,.0005,.05] if i<2 else [.002,.002,.3])
                limits=np.asarray([.003,.003,.3] if i<2 else [.03,.03,5.])
                values=np.clip(values,-limits,limits)
                token=digest(values.tolist())
                if token not in seen:break
            else:raise ValueError('Candidate dedup exhausted')
            seen.add(token);initial=copy.deepcopy(reference['scene']['initial_state']);initial['model_identity']=identity
            q=np.asarray(initial['qpos'],float);q[adr:adr+2]+=values[:2]
            q[adr+3:adr+7]=(Rotation.from_euler('z',values[2],degrees=True)*Rotation.from_quat(q[adr+3:adr+7][[1,2,3,0]])).as_quat()[[3,0,1,2]]
            initial['qpos']=q.tolist()
            candidates.append({'candidate_id':f'{uid}-c{j+1:02d}','task_id':'lift_basket','model':str(model),
                'model_identity':identity,'seed':2151000+i*10+j,'initial_state':initial,'asset_id':'oasis-basket',
                'appearance_preset':preset,'difficulty':'clean' if i<2 else 'randomized',
                'configuration_parameters':values.tolist(),'configuration_sha256':token,
                'canonical_goal_position':[float(q[adr]),float(q[adr+1]),.02]})
        slots.append({'episode_uid':uid,'task_id':'lift_basket','difficulty':'clean' if i<2 else 'randomized',
            'split':'train','appearance_preset':preset,'coverage_bin':i,'candidates':candidates})
    source={'work_id':WORK_ID,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        'implementation':implementation(),'template_id':template['template_id'],'template_sha256':sha(template_root/'template.json'),
        'executor_variant':config['recipe_id'],'approval_sha256':digest(approval)}
    campaign={'schema':'qlm-approved-lift-ten-campaign-v1','task_id':'lift_basket','work_id':WORK_ID,'source':source,
        'approval':approval,'template_root':str(template_root),'slots':slots,'maximum_physics_attempts':30,'maximum_per_slot':5,
        'maximum_consecutive_failures':10,'physics_workers':4,'render_workers':4,'maximum_render_backlog':8,
        'minimum_available_ram_bytes':2*1024**3,'maximum_swap_growth_bytes':512*1024**2,
        'quality_policy':'evidence-review-v1','consumer_validation':'Lift-task-once-Clean-and-Randomized-v2-and-v3',
        'python':str(WORKSPACE/'envs/qlm-mujoco-py312-v1/bin/python'),'ffmpeg':str(WORKSPACE/'cache/tools/bin/ffmpeg'),
        'ffprobe':str(WORKSPACE/'cache/tools/bin/ffprobe'),
        'render_environment':{'PYTHONPATH':str(REPO/'src'),'MUJOCO_GL':'osmesa','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'1',
            'MESA_SHADER_CACHE_DIR':str(WORKSPACE/'cache/mesa'),
            'LD_LIBRARY_PATH':str(WORKSPACE/'assets/mujoco/p0-v1/osmesa/root/usr/lib/x86_64-linux-gnu')}}
    campaign['profile_sha256']=digest(campaign);write_json(root/'campaign.json',campaign)
    write_json(root/'asset-pool.json',{'status':'frozen_for_pilot','primary':'oasis-basket','backups':approval['backups'],
        'primary_models':{k:{'path':str(v),'identity':resource_closure(v,require_portable=True)['identity']} for k,v in models.items()},
        'approved_scope':{'dx_m':[-.03,.03],'dy_m':[-.03,.03],'yaw_deg':[-5,5]},'Clean_bounds':[.003,.003,.3],
        'backup_usage_quota':False,'backup_qualification':'passive Native/CUDA only; actual RAMBO not_run; not used in this batch',
        'source_asset_license':'unknown/unverified; local synthesis only, no publication authorization'})
    for name in source['implementation']:
        target=root/'frozen-source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/name,target)
    print(json.dumps({'slots':10,'candidates':50,'campaign_sha256':campaign['profile_sha256']}),flush=True)


def checked(root):
    c = json.loads((root/'campaign.json').read_text())
    if digest({k:v for k,v in c.items() if k!='profile_sha256'}) != c['profile_sha256'] or implementation() != c['source']['implementation']:
        raise ValueError('Frozen Lift campaign/source changed')
    if sha(Path(c['template_root'])/'template.json') != c['source']['template_sha256'] or digest(json.loads((root/'approval.json').read_text())) != c['source']['approval_sha256']:
        raise ValueError('Frozen approved recipe/approval changed')
    if len(c['slots']) != 10 or [sum(s['difficulty']==d for s in c['slots']) for d in ('clean','randomized')] != [2,8] or any(s['split']!='train' for s in c['slots']):
        raise ValueError('Incorrect ten-pilot quota')
    return c


def motion_evidence(trace):
    _,_,t,commands,_=verify_trace(trace)
    high=[r for r in t['physics'] if r['physics_step']%5==0]
    q=np.rad2deg(np.asarray([r['joint_position'] for r in high])[:,[0,4,8]])
    phases=np.array([commands[min(r['physics_step']//10,len(commands)-1)]['extensions']['expert']['phase'] for r in high])
    metrics={}
    for phase in dict.fromkeys(phases):
        ix=np.where(phases==phase)[0];values=q[ix];d=np.diff(np.array([high[i]['physics_step'] for i in ix]))==5
        metrics[phase]={'actual_range_deg':np.ptp(values,axis=0).tolist(),
            'actual_max_10ms_step_deg':np.max(np.abs(np.diff(values,axis=0))[d],axis=0).tolist() if np.any(d) else [0,0,0]}
    through=[i for i,r in enumerate(commands) if r['extensions']['expert']['completely_through']]
    lift=[i for i,r in enumerate(commands) if r['extensions']['expert']['phase']=='lift']
    return {'joint_order':['FL_hip_roll','FL_thigh','FL_calf'],'phases':metrics,
        'full_foot_through_before_lift':bool(through and lift and through[0]<lift[0]),
        'task_success_separate_from_quality':True,'metrics_are_not_new_task_predicates':True}


def physics(root,candidate):
    import torch
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    from qlm_bench.backends.mujoco.lift_reference_smooth import SmoothLiftExecutor
    from qlm_bench.backends.mujoco.resources import resource_closure
    from qlm_bench.backends.mujoco.trace import collect_trace
    from qlm_bench.backends.mujoco.quality import analyze_trace
    c=checked(root);scene=next(s for slot in c['slots'] for s in slot['candidates'] if s['candidate_id']==candidate)
    if resource_closure(scene['model'],require_portable=True)['identity']!=scene['model_identity']:raise ValueError('Frozen asset changed')
    config=json.loads((Path(c['template_root'])/'template.json').read_text())['recipe_config']
    torch.set_num_threads(1);start=time.monotonic()
    rt=MuJoCoRuntime(scene['model'],str(WORKSPACE/'checkpoints/rambo/go2/quadruped/model_2000.pt'),trace_only=True,
        seed=scene['seed'],profile_override={'canonical_goal_position':scene['canonical_goal_position']})
    try:
        if rt.profile.get('appearance_preset','ap_00')!=scene['appearance_preset']:raise ValueError('Frozen background differs')
        result=collect_trace(rt,SmoothLiftExecutor(config),scene,root/'physical'/candidate/'trace',
            batch_identity={**c['source'],'pilot_campaign_sha256':c['profile_sha256']},quality_policy='evidence-review-v1')
        result['total_wall_s']=time.monotonic()-start
        if result['passed']:
            review,_=analyze_trace(result['trace']);write_json(root/'quality'/(candidate+'.json'),review)
            motion=motion_evidence(result['trace']);write_json(root/'motion'/(candidate+'.json'),motion)
            # Evidence review is independent of task outcome; no sphere-only contact requirement.
            if not motion['full_foot_through_before_lift']:
                write_json(root/'physical'/candidate/'result.json',{**result,'behavior_review':'hold: no complete threading before lift'})
                raise ValueError('Successful trajectory needs threading behavior review; trace retained')
        write_json(root/'physical'/candidate/'result.json',result);print(json.dumps(result),flush=True)
    finally:rt.close()


def freeze_slot(root,c,slot,scene):
    from qlm_bench.backends.mujoco.rendition import audit_trace,validate_slot_inputs
    from qlm_bench.backends.mujoco.quality import analyze_trace
    from qlm_bench.compatibility.dataset_v2.pilot_rendition import LIFT_SCHEMA,load_profile
    trace=root/'physical'/scene['candidate_id']/'trace'; audit=audit_trace(trace); m=verify_trace(trace)[0]; review,_=analyze_trace(trace)
    row={k:slot[k] for k in ('episode_uid','task_id','difficulty','split','appearance_preset')}
    row.update(trace=str(trace),model=scene['model'],model_identity=m['model_identity'],
        physical_source_sha256=audit['source_identity_sha256'],trace_manifest_sha256=audit['manifest_sha256'],
        physical_trajectory_sha256=audit['trajectory_sha256'],quality=audit['quality'],quality_review_sha256=digest(review),
        review_status='eligible_for_ten_pilot_user_review',n_actions=m['n_actions'],rendition_id=slot['episode_uid']+'@dual-rgb-360p-v1',
        candidate_id=scene['candidate_id'],asset_id='oasis-basket',seed=scene['seed'])
    p={k:copy.deepcopy(c[k]) for k in ('task_id','work_id','approval','quality_policy','template_root','python','ffmpeg','ffprobe','render_environment')}
    p.update(schema=LIFT_SCHEMA,profile_id=slot['episode_uid']+'-recording-v1',pilot_target=10,pilot_campaign_sha256=c['profile_sha256'],
        rgb_profile='dual-rgb-360p-v1',maximum_render_attempts=3,template_id=c['source']['template_id'],template_sha256=c['source']['template_sha256'],
        recording_source={**c['source'],'stage':'offline-recording','pilot_campaign_sha256':c['profile_sha256']},
        render_script=str(REPO/'scripts/mujoco/synthesis/render_trace.py'),slots=[row])
    p['profile_sha256']=digest(p); path=root/'recording-profiles'/(slot['episode_uid']+'.json'); write_json(path,p)
    validate_slot_inputs(load_profile(path),slot['episode_uid']); return str(path)


def memory():
    values={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()}
    return {'available':values['MemAvailable'],'swap_used':values['SwapTotal']-values['SwapFree']}


def dispatch(root,physics_workers=4,render_workers=4):
    from slot_campaign import dispatch as run
    return run(root,DATA,checked,freeze_slot,Path(__file__),physics_workers,render_workers)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=('prepare','physics','dispatch'));p.add_argument('--root',required=True);p.add_argument('--candidate');p.add_argument('--physics-workers',type=int,default=4);p.add_argument('--render-workers',type=int,default=4)
    a=p.parse_args();r=Path(a.root).resolve()
    if a.stage=='physics':physics(r,a.candidate)
    elif a.stage=='prepare':prepare(r)
    else:dispatch(r,a.physics_workers,a.render_workers)
