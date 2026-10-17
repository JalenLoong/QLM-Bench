"""Approved bounded ten-slot Kick pilots; retained RAMBO and independent render workers."""
import argparse,copy,json,os,shutil,subprocess,time
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from qlm_bench.backends.mujoco.trace import sha,write_json,verify_trace
from qlm_bench.compatibility.dataset_v2.validation import digest

REPO=Path(__file__).resolve().parents[3];WORKSPACE=REPO.parents[1]
DATA=WORKSPACE/'data/qlm_bench/kick-approved-pilot-20261015-v1';WORK_ID='QLM-DATA-024'
REFERENCE=WORKSPACE/'runs/audit/kick-reference-20261015-v1'


def implementation():
    return {str(p.relative_to(REPO)):sha(p) for f in ('src/qlm_bench','scripts/mujoco/synthesis') for p in sorted((REPO/f).rglob('*')) if p.suffix in ('.py','.json')}


def prepare(root):
    import mujoco
    from qlm_bench.backends.mujoco.resources import resource_closure
    approval=json.loads((root/'approval.json').read_text());assert all(approval[k] is True for k in ('reference_quality_approved','retarget_scope_approved','asset_pool_approved'))
    config=json.loads((root/'recipe-config.json').read_text());assert sha(root/'recipe-config.json')==approval['approved_recipe_sha256']
    assert config['recipe_id']=='kick-impulse-retract-v3-tucked-carry'
    reference=verify_trace(REFERENCE/'nominal-a03/trace')[0]
    assert sha(REFERENCE/'nominal-a03/trace/manifest.json')==approval['approved_reference_trace_manifest_sha256']
    template=root/'template';template.mkdir(exist_ok=False)
    write_json(template/'template.json',{'template_id':'kick-v3-tucked-carry-approved-20261015','recipe_config':config,'approved_recipe_sha256':approval['approved_recipe_sha256'],'approved_reference_trace_manifest_sha256':approval['approved_reference_trace_manifest_sha256']})
    # Two true small geometric variations, then an eight-point balanced4D design.
    centers=[[.003,-.003,.008,-.005],[-.003,.003,-.008,.005]]
    centers += [[a*.03,b*.03,c*.08,a*b*c*.05] for a in (-1,1) for b in (-1,1) for c in (-1,1)]
    presets=['ap_00','ap_00','ap_00','ap_01','ap_01','ap_00','ap_01','ap_00','ap_00','ap_01']
    rng=np.random.default_rng(2026101524);seen=set();slots=[];model_receipts={}
    for i,center in enumerate(centers):
        uid=f'kick-approved-20261015-{i+1:02d}';preset=presets[i];source=REFERENCE/'backgrounds'/preset;candidates=[]
        for j in range(5):
            limits=np.array([.003,.003,.008,.005] if i<2 else [.03,.03,.08,.05])
            for draw in range(100):
                values=np.array(center)+ (rng.uniform(-1,1,4)*limits*.08 if j else 0)
                values=np.clip(values,-limits,limits);token=digest(values.tolist())
                if token not in seen:break
            else:raise ValueError('Duplicate candidate support')
            seen.add(token);cid=f'{uid}-c{j+1:02d}';target=root/'models'/cid
            shutil.copytree(source,target,copy_function=os.link)
            for name in ('scene.xml','scene.task.json','resource-manifest.json'):(target/name).unlink()
            dx,dy,gx,gy=map(float,values);tree=ET.parse(source/'scene.xml');world=tree.getroot()
            world.find("worldbody/body[@name='primary']").set('pos',f'{.62+dx} {.18+dy} .10')
            world.find("worldbody/body[@name='goal']").set('pos',f'{1.62+gx} {.18+gy} 0')
            world.find("worldbody/geom[@name='goal_line_visual']").set('pos',f'{1.62+gx} {.18+gy} .0008');tree.write(target/'scene.xml',encoding='unicode')
            profile=json.loads((source/'scene.task.json').read_text());profile['goal_geometry']['front_center_xyz_m']=[1.62+gx,.18+gy,0.]
            profile['canonical_goal_position']=[1.82+gx,.18+gy,.1];profile['source_profile']['canonical_goal_position']=profile['canonical_goal_position'];profile['appearance_preset']=preset;write_json(target/'scene.task.json',profile)
            manifest=json.loads((source/'resource-manifest.json').read_text())
            for name in ('scene.xml','scene.task.json'):manifest['files'][name]={'sha256':sha(target/name),'size_bytes':(target/name).stat().st_size}
            write_json(target/'resource-manifest.json',manifest)
            model=target/'scene.xml';identity=resource_closure(model,require_portable=True)['identity']
            compiled=mujoco.MjModel.from_xml_path(str(model));data=mujoco.MjData(compiled);mujoco.mj_forward(compiled,data)
            # Preserve the approved RAMBO reset stance; XML qpos0 alone has straight robot joints.
            initial=copy.deepcopy(reference['scene']['initial_state']);initial['model_identity']=identity
            adr=int(compiled.joint('object_free').qposadr[0]);initial['qpos'][adr:adr+7]=data.qpos[adr:adr+7].tolist()
            candidates.append({'candidate_id':cid,'task_id':'kick_ball_to_goal','model':str(model),'model_identity':identity,'seed':2451000+i*10+j,'initial_state':initial,'asset_id':approval['primary'],'appearance_preset':preset,'difficulty':'clean' if i<2 else 'randomized','configuration_parameters':values.tolist(),'configuration_sha256':token})
            model_receipts[cid]={'model':str(model),'identity':identity}
        slots.append({'episode_uid':uid,'task_id':'kick_ball_to_goal','difficulty':'clean' if i<2 else 'randomized','split':'train','appearance_preset':preset,'coverage_bin':i,'candidates':candidates})
    source={'work_id':WORK_ID,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'implementation':implementation(),'template_id':'kick-v3-tucked-carry-approved-20261015','template_sha256':sha(template/'template.json'),'executor_variant':config['recipe_id'],'approval_sha256':digest(approval),'native_trace_profile':'native-cpu-original-rambo-v1'}
    checkpoint=WORKSPACE/'checkpoints/rambo/go2/quadruped/model_2000.pt'
    campaign={'schema':'qlm-approved-kick-ten-campaign-v1','task_id':'kick_ball_to_goal','work_id':WORK_ID,'source':source,'approval':approval,'template_root':str(template),'slots':slots,'maximum_physics_attempts':30,'maximum_per_slot':5,'maximum_consecutive_failures':10,'physics_workers':3,'render_workers':3,'maximum_render_backlog':6,'minimum_available_ram_bytes':1024**3,'maximum_swap_growth_bytes':8160437862,'emergency_render_eviction_available_bytes':512*1024**2,'new_render_minimum_available_bytes':4*1024**3,'quality_policy':'evidence-review-v1','consumer_validation':'Kick-task-once-Clean-and-Randomized-v2-and-v3','checkpoint':str(checkpoint),'checkpoint_sha256':sha(checkpoint),'python':str(WORKSPACE/'envs/qlm-mujoco-py312-v1/bin/python'),'ffmpeg':str(WORKSPACE/'cache/tools/bin/ffmpeg'),'ffprobe':str(WORKSPACE/'cache/tools/bin/ffprobe'),'render_environment':{'PYTHONPATH':str(REPO/'src'),'MUJOCO_GL':'egl','PYOPENGL_PLATFORM':'egl','MUJOCO_EGL_DEVICE_ID':'0','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}}
    campaign['profile_sha256']=digest(campaign);write_json(root/'campaign.json',campaign)
    write_json(root/'asset-pool.json',{'status':'frozen_for_ten_pilots','primary':approval['primary'],'backups':approval['backups'],'backup_usage_quota':False,'backup_physics_qualification':str(REFERENCE/'qualification-native-a01/result.json'),'models':model_receipts,'approved_scope':approval['approved_scope'],'clean_bounds':[.003,.003,.008,.005],'clutter':False,'required_recovery':False})
    for name in source['implementation']:
        target=root/'frozen-source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/name,target)
    print(json.dumps({'slots':10,'candidates':50,'campaign_sha256':campaign['profile_sha256']}),flush=True)


def checked(root):
    c=json.loads((root/'campaign.json').read_text())
    if digest({k:v for k,v in c.items() if k!='profile_sha256'})!=c['profile_sha256'] or implementation()!=c['source']['implementation']:raise ValueError('Frozen Kick campaign/source changed')
    if sha(Path(c['template_root'])/'template.json')!=c['source']['template_sha256'] or digest(json.loads((root/'approval.json').read_text()))!=c['source']['approval_sha256'] or sha(c['checkpoint'])!=c['checkpoint_sha256']:raise ValueError('Frozen recipe/approval/checkpoint changed')
    if len(c['slots'])!=10 or [sum(s['difficulty']==d for s in c['slots']) for d in ('clean','randomized')]!=[2,8] or any(s['split']!='train' for s in c['slots']):raise ValueError('Ten pilot quota differs')
    return c


def physics(root,candidate):
    import torch
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    from qlm_bench.backends.mujoco.kick_reference import KickExecutor
    from qlm_bench.backends.mujoco.resources import resource_closure
    from qlm_bench.backends.mujoco.trace import collect_trace
    from qlm_bench.backends.mujoco.kick_quality import analyze_kick
    c=checked(root);scene=next(x for s in c['slots'] for x in s['candidates'] if x['candidate_id']==candidate)
    if resource_closure(scene['model'],require_portable=True)['identity']!=scene['model_identity']:raise ValueError('Frozen Kick model changed')
    config=json.loads((Path(c['template_root'])/'template.json').read_text())['recipe_config'];torch.set_num_threads(1)
    rt=MuJoCoRuntime(scene['model'],c['checkpoint'],backend='native',device='cpu',trace_only=True,seed=scene['seed'])
    try:
        result=collect_trace(rt,KickExecutor(config),scene,root/'physical'/candidate/'trace',batch_identity={**c['source'],'pilot_campaign_sha256':c['profile_sha256']},quality_policy='evidence-review-v1')
        write_json(root/'physical'/candidate/'result.json',result)
        if result['passed']:
            quality,records=analyze_kick(result['trace']);write_json(root/'motion'/(candidate+'.json'),quality);write_json(root/'contacts'/(candidate+'.json'),records)
            if quality['behavior_review_holds']:raise ValueError('Successful Kick trace retained for separate behavior review: '+str(quality['behavior_review_holds']))
        print(json.dumps(result),flush=True)
    finally:rt.close()


def freeze_slot(root,c,slot,scene):
    from qlm_bench.backends.mujoco.rendition import audit_trace,validate_slot_inputs
    from qlm_bench.backends.mujoco.quality import analyze_trace
    from qlm_bench.compatibility.dataset_v2.pilot_rendition import KICK_SCHEMA,load_profile
    trace=root/'physical'/scene['candidate_id']/'trace';audit=audit_trace(trace);m=verify_trace(trace)[0];review,_=analyze_trace(trace)
    row={k:slot[k] for k in ('episode_uid','task_id','difficulty','split','appearance_preset')}
    row.update(trace=str(trace),model=scene['model'],model_identity=m['model_identity'],physical_source_sha256=audit['source_identity_sha256'],trace_manifest_sha256=audit['manifest_sha256'],physical_trajectory_sha256=audit['trajectory_sha256'],quality=audit['quality'],quality_review_sha256=digest(review),review_status='eligible_for_ten_pilot_user_review',n_actions=m['n_actions'],rendition_id=slot['episode_uid']+'@dual-rgb-360p-v1',candidate_id=scene['candidate_id'],asset_id=scene['asset_id'],seed=scene['seed'])
    p={k:copy.deepcopy(c[k]) for k in ('task_id','work_id','approval','quality_policy','template_root','python','ffmpeg','ffprobe','render_environment')}
    p.update(schema=KICK_SCHEMA,profile_id=slot['episode_uid']+'-recording-v1',pilot_target=10,pilot_campaign_sha256=c['profile_sha256'],rgb_profile='dual-rgb-360p-v1',maximum_render_attempts=3,template_id=c['source']['template_id'],template_sha256=c['source']['template_sha256'],recording_source={**c['source'],'stage':'offline-recording','pilot_campaign_sha256':c['profile_sha256']},render_script=str(REPO/'scripts/mujoco/synthesis/render_trace.py'),slots=[row])
    p['profile_sha256']=digest(p);path=root/'recording-profiles'/(slot['episode_uid']+'.json');write_json(path,p);validate_slot_inputs(load_profile(path),slot['episode_uid']);return str(path)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('prepare','physics','dispatch'));p.add_argument('--root',required=True);p.add_argument('--candidate');p.add_argument('--physics-workers',type=int,default=3);p.add_argument('--render-workers',type=int,default=3);a=p.parse_args();root=Path(a.root).resolve()
    if a.stage=='prepare':prepare(root)
    elif a.stage=='physics':physics(root,a.candidate)
    else:
        from slot_campaign import dispatch
        dispatch(root,DATA,checked,freeze_slot,Path(__file__),a.physics_workers,a.render_workers)
