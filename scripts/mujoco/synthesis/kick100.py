"""Approved Kick100: preserve ten pilots, add90 using unchanged NativeCPU/EGL semantics."""
import argparse,copy,json,os,shutil,subprocess,time
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from qlm_bench.backends.mujoco.kick_production import configuration_candidates,load_campaign,KickProductionQueue,QUOTAS,NEAR
from qlm_bench.backends.mujoco.trace import sha,write_json,verify_trace
from qlm_bench.compatibility.dataset_v2.validation import digest,validate_canonical
from qlm_bench.compatibility.dataset_v2.media import MediaTools
REPO=Path(__file__).resolve().parents[3];W=REPO.parents[1]
PILOT=W/'runs/audit/kick-formal-pilots-20261015-v1'


def implementation():
    return {str(p.relative_to(REPO)):sha(p) for folder in ('src/qlm_bench','scripts/mujoco/synthesis') for p in sorted((REPO/folder).rglob('*')) if p.suffix in ('.py','.json')}


def pilot_members():
    c=json.loads((PILOT/'campaign.json').read_text());state=json.loads((PILOT/'campaign-state.json').read_text());assert state['accepted']==10
    pilots=[]
    for slot in c['slots']:
        uid=slot['episode_uid'];row=state['slots'][uid];member=json.loads(Path(row['recording_profile']).read_text())['slots'][0];out=W/'data/qlm_bench/kick-approved-pilot-20261015-v1/slots'/uid/'episodes'/uid
        pilots.append({**copy.deepcopy(member),'parameters':row['scene']['configuration_parameters'],'output':str(out),'recording_profile':row['recording_profile'],'canonical_sha256':sha(out/'canonical/meta/checksums.json')})
    return pilots,c


def validate_pilot_reuse(root,pilots,old):
    program="""import json,sys
from qlm_bench.backends.mujoco.rendition import validate_output
from qlm_bench.backends.mujoco.trace import write_json
from qlm_bench.compatibility.dataset_v2.media import MediaTools
p=json.load(open(sys.argv[1]));results=[validate_output(s['output'],profile_path=s['recording_profile'],tools=MediaTools(p['ffmpeg'],p['ffprobe']),check_media=False) for s in p['pilots']]
write_json(sys.argv[2],{'passed':True,'episodes':results,'source':'original frozen Kick pilot producer','WAM_execution':False})
"""
    inp=root/'pilot-reuse-input.json';write_json(inp,{'pilots':pilots,'ffmpeg':old['ffmpeg'],'ffprobe':old['ffprobe']})
    subprocess.run([old['python'],'-c',program,str(inp),str(root/'pilot-reuse-validation.json')],env=dict(os.environ,PYTHONPATH=str(PILOT/'frozen-source/src'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),check=True)


def prepare(root):
    import mujoco
    from qlm_bench.backends.mujoco.resources import resource_closure
    authorization=json.loads((root/'user-approval.json').read_text());assert authorization['pilot_approved'] and authorization['target_accepted']==100
    pilots,old=pilot_members();validate_pilot_reuse(root,pilots,old)
    qualified=json.loads((PILOT/'dual-wam-compatibility.json').read_text());assert qualified['passed'] and qualified['task_id']=='kick_ball_to_goal'
    reference=W/'runs/audit/kick-reference-20261015-v1';initial=verify_trace(reference/'nominal-a03/trace')[0]['scene']['initial_state']
    pool=json.loads((PILOT/'asset-pool.json').read_text());slots=configuration_candidates(pilots)
    compiled=mujoco.MjModel.from_xml_path(str(reference/'backgrounds/ap_00/scene.xml'));adr=int(compiled.joint('object_free').qposadr[0])
    for slot in slots:
        preset=slot['appearance_preset'];source=reference/'backgrounds'/preset
        for scene in slot['candidates']:
            target=root/'models'/scene['candidate_id'];shutil.copytree(source,target,copy_function=os.link)
            for name in ('scene.xml','scene.task.json','resource-manifest.json'):(target/name).unlink()
            dx,dy,gx,gy=scene['configuration_parameters'];tree=ET.parse(source/'scene.xml');xml=tree.getroot()
            xml.find("worldbody/body[@name='primary']").set('pos',f'{.62+dx} {.18+dy} .10');xml.find("worldbody/body[@name='goal']").set('pos',f'{1.62+gx} {.18+gy} 0');xml.find("worldbody/geom[@name='goal_line_visual']").set('pos',f'{1.62+gx} {.18+gy} .0008');tree.write(target/'scene.xml',encoding='unicode')
            profile=json.loads((source/'scene.task.json').read_text());profile['goal_geometry']['front_center_xyz_m']=[1.62+gx,.18+gy,0.];profile['canonical_goal_position']=[1.82+gx,.18+gy,.1];profile['source_profile']['canonical_goal_position']=profile['canonical_goal_position'];profile['appearance_preset']=preset;write_json(target/'scene.task.json',profile)
            manifest=json.loads((source/'resource-manifest.json').read_text())
            for name in ('scene.xml','scene.task.json'):manifest['files'][name]={'sha256':sha(target/name),'size_bytes':(target/name).stat().st_size}
            write_json(target/'resource-manifest.json',manifest);model=target/'scene.xml';identity=resource_closure(model,require_portable=True)['identity']
            # The original RAMBO reset stance remains the approved reference stance.
            state=copy.deepcopy(initial);state['model_identity']=identity;state['qpos'][adr:adr+3]=[.62+dx,.18+dy,.1]
            scene.update(task_id='kick_ball_to_goal',model=str(model),model_identity=identity,initial_state=state,asset_id=old['approval']['primary'],appearance_preset=preset,difficulty=slot['difficulty'],split=slot['split'])
        print('Prepared Kick slot',slot['episode_uid'],flush=True)
    protected={n:h for n,h in old['source']['implementation'].items() if n.startswith('src/qlm_bench/controllers/') or n in ['src/qlm_bench/backends/mujoco/'+x for x in ('physics.py','runtime.py','tasks.py','render.py','kick_reference.py','kick_goal.py','kick_quality.py','trace.py')]}
    for n,h in protected.items():
        if sha(REPO/n)!=h:raise ValueError('Approved execution semantics changed: '+n)
    source={**copy.deepcopy(old['source']),'work_id':'QLM-DATA-025','implementation':implementation(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'checkpoint_sha256':sha(W/'checkpoints/rambo/go2/quadruped/model_2000.pt'),'execution_profile':'native-cpu-rambo-cpu-egl-v1'}
    resource_policy={'minimum_available_ram_bytes':1024**3,'maximum_swap_growth_bytes':8160437862,'emergency_render_eviction_available_bytes':512*1024**2,'new_render_minimum_available_bytes':4*1024**3}
    c={'schema':'qlm-kick100-production-v1','task_id':'kick_ball_to_goal','work_id':'QLM-DATA-025','authorization':authorization,'approval':old['approval'],'source':source,'pilots':pilots,'slots':slots,'template_root':old['template_root'],'python':old['python'],'checkpoint':str(W/'checkpoints/rambo/go2/quadruped/model_2000.pt'),'entrypoint':str(Path(__file__).resolve()),'data_root':str(W/'data/qlm_bench/kick100-20261015-v1'),'ffmpeg':old['ffmpeg'],'ffprobe':old['ffprobe'],'render_environment':old['render_environment'],'render_script':str(REPO/'scripts/mujoco/synthesis/render_trace.py'),'consumer_validation':'task_already_validated_skip','consumer_evidence_sha256':sha(PILOT/'dual-wam-compatibility.json'),'physics_workers':3,'render_workers':3,'maximum_render_backlog':6,'resource_policy':resource_policy,'near_duplicate_tolerance_ball_xy_goal_xy_m':NEAR.tolist(),'quotas':QUOTAS,'approved_semantics_preserved':protected,'configuration_sampling':'full-support Latin-hypercube per difficulty/split; bounded4% local retry jitter; no interval partition/OOD'}
    c['profile_sha256']=digest(c);write_json(root/'campaign.json',c);load_campaign(root/'campaign.json',REPO)
    for n in source['implementation']:
        dst=root/'frozen-source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/n,dst)
    write_json(root/'asset-pool.json',{**pool,'status':'frozen_for100','source_pilot_asset_pool_sha256':sha(PILOT/'asset-pool.json'),'new_candidate_models':{scene['candidate_id']:{'path':scene['model'],'identity':scene['model_identity']} for s in slots for scene in s['candidates']}})
    write_json(root/'configuration-coverage.json',{'pilot_parameters':[s['parameters'] for s in pilots],'slots':slots,'all_splits_same_ID_support':True,'variable_intervals_partitioned':False,'near_duplicate_tolerance_m':NEAR.tolist(),'sampling':c['configuration_sampling']})
    print('Frozen10+90,450 candidates,3+3/7.6GiB; WAM task-once skipped',flush=True)


def physics(root,a):
    import torch
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    from qlm_bench.backends.mujoco.kick_reference import KickExecutor
    from qlm_bench.backends.mujoco.kick_quality import analyze_kick
    from qlm_bench.backends.mujoco.trace import collect_trace
    from qlm_bench.backends.mujoco.resources import resource_closure
    c=load_campaign(root/'campaign.json',REPO);scene=json.loads(Path(a.candidate).read_text());declared=next(x for s in c['slots'] for x in s['candidates'] if x['candidate_id']==scene['candidate_id']);assert scene==declared
    if resource_closure(scene['model'],require_portable=True)['identity']!=scene['model_identity']:raise ValueError('Frozen physical model changed')
    config=json.loads((Path(c['template_root'])/'template.json').read_text())['recipe_config'];torch.set_num_threads(1);started=time.monotonic()
    rt=MuJoCoRuntime(scene['model'],c['checkpoint'],backend='native',device='cpu',trace_only=True,seed=scene['seed'])
    try:
        result=collect_trace(rt,KickExecutor(config),scene,a.trace,batch_identity={**c['source'],'production_campaign_sha256':c['profile_sha256']},quality_policy='evidence-review-v1')
        write_json(a.result,result)
        if result['passed']:
            motion,records=analyze_kick(a.trace);write_json(root/'motion'/(scene['candidate_id']+'.json'),motion);write_json(root/'contacts'/(scene['candidate_id']+'.json'),records)
            if motion['behavior_review_holds']:raise ValueError('Successful Kick retained for separate behavior review: '+str(motion['behavior_review_holds']))
        result['total_wall_s']=time.monotonic()-started;write_json(a.result,result);print(json.dumps(result),flush=True)
    finally:rt.close()


def admission_receipt(root):
    from qlm_bench.backends.mujoco.rendition import validate_output
    c=load_campaign(root/'campaign.json',REPO);q=json.loads((root/'queue.json').read_text());assert q['status']=='admission_complete'
    selected=c['slots'][:2];assert [s['difficulty'] for s in selected]==['clean','randomized'];checks=[]
    for s in selected:
        uid=s['episode_uid'];assert q['slots'][uid]['status']=='accepted';checks.append(validate_output(Path(c['data_root'])/'new'/uid/'episodes'/uid,profile_path=root/'profiles'/(uid+'.json'),tools=MediaTools(c['ffmpeg'],c['ffprobe']),check_media=False))
    write_json(root/'production-admission.json',{'passed':True,'campaign_sha256':c['profile_sha256'],'episodes':checks,'WAM_execution':False,'admission_trajectories_retained_counted_in90':True})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('prepare','physics','admission','run'));p.add_argument('--root',required=True)
    for k in ('candidate','trace','result'):p.add_argument('--'+k)
    p.add_argument('--physics-workers',type=int,default=3);p.add_argument('--render-workers',type=int,default=3);a=p.parse_args();root=Path(a.root).resolve()
    if a.stage=='prepare':prepare(root)
    elif a.stage=='physics':physics(root,a)
    elif a.stage=='admission':KickProductionQueue(root,root/'campaign.json',REPO).run_parallel(a.physics_workers,a.render_workers,admission=True);admission_receipt(root)
    else:
        c=load_campaign(root/'campaign.json',REPO);gate=json.loads((root/'production-admission.json').read_text());assert gate['passed'] and gate['campaign_sha256']==c['profile_sha256']
        KickProductionQueue(root,root/'campaign.json',REPO).run_parallel(a.physics_workers,a.render_workers)
