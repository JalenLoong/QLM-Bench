"""User-approved Lift100: original ten plus90 NativeCPU/RAMBO CPU + EGL entries."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from qlm_bench.backends.mujoco.lift_production import configuration_candidates, load_campaign, LiftProductionQueue, NEAR, QUOTAS
from qlm_bench.backends.mujoco.trace import sha, write_json, verify_trace
from qlm_bench.compatibility.dataset_v2.validation import digest, validate_canonical
from qlm_bench.compatibility.dataset_v2.media import MediaTools

REPO=Path(__file__).resolve().parents[3]
W=REPO.parents[1]
PILOT=W/'runs/audit/lift-formal-pilots-20261015-v1'


def implementation():
    return {str(p.relative_to(REPO)):sha(p) for folder in ('src/qlm_bench','scripts/mujoco/synthesis')
        for p in sorted((REPO/folder).rglob('*')) if p.suffix in ('.py','.json')}


def prepare(root):
    import mujoco
    from scipy.spatial.transform import Rotation
    from qlm_bench.backends.mujoco.resources import resource_closure
    authorization=json.loads((root/'user-approval.json').read_text())
    old=json.loads((PILOT/'campaign.json').read_text());state=json.loads((PILOT/'campaign-state.json').read_text())
    if not authorization['pilot_approved'] or state['accepted']!=10:raise ValueError('Ten approved pilots required')
    pilots=[]
    for slot in old['slots']:
        uid=slot['episode_uid'];row=state['slots'][uid];member=json.loads(Path(row['recording_profile']).read_text())['slots'][0]
        out=W/'data/qlm_bench/lift-approved-pilot-20261015-v1/slots'/uid/'episodes'/uid
        pilots.append({**copy.deepcopy(member),'parameters':row['scene']['configuration_parameters'],'output':str(out),
            'recording_profile':row['recording_profile'],'canonical_sha256':sha(out/'canonical/meta/checksums.json')})
    program="""import json,sys
from qlm_bench.backends.mujoco.rendition import validate_output
from qlm_bench.backends.mujoco.trace import write_json
from qlm_bench.compatibility.dataset_v2.media import MediaTools
p=json.load(open(sys.argv[1]));results=[validate_output(s['output'],profile_path=s['recording_profile'],tools=MediaTools(p['ffmpeg'],p['ffprobe']),check_media=False) for s in p['pilots']]
write_json(sys.argv[2],{'passed':True,'source':'original frozen CUDA/OSMesa pilot producer','WAM_execution':False,'episodes':results})
"""
    write_json(root/'pilot-reuse-input.json',{'pilots':pilots,'ffmpeg':old['ffmpeg'],'ffprobe':old['ffprobe']})
    subprocess.run([old['python'],'-c',program,str(root/'pilot-reuse-input.json'),str(root/'pilot-reuse-validation.json')],
        env=dict(os.environ,PYTHONPATH=str(PILOT/'frozen-source/src'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),check=True)
    pool=json.loads((PILOT/'asset-pool.json').read_text());models={k:Path(v['path']) for k,v in pool['primary_models'].items()}
    reference=verify_trace(W/'runs/audit/lift-reference-20261015-v1/nominal-a03/trace')[0]
    compiled=mujoco.MjModel.from_xml_path(str(models['ap_00']));adr=int(compiled.joint('object_free').qposadr[0])
    slots=configuration_candidates(pilots)
    for slot in slots:
        model=models[slot['appearance_preset']];identity=resource_closure(model,require_portable=True)['identity']
        if identity!=pool['primary_models'][slot['appearance_preset']]['identity']:raise ValueError('Approved asset pool changed')
        for scene in slot['candidates']:
            values=np.asarray(scene['configuration_parameters']);initial=copy.deepcopy(reference['scene']['initial_state'])
            q=np.asarray(initial['qpos']);q[adr:adr+2]+=values[:2]
            q[adr+3:adr+7]=(Rotation.from_euler('z',values[2],degrees=True)*Rotation.from_quat(q[adr+3:adr+7][[1,2,3,0]])).as_quat()[[3,0,1,2]]
            initial.update(qpos=q.tolist(),model_identity=identity)
            scene.update(task_id='lift_basket',model=str(model),model_identity=identity,initial_state=initial,asset_id='oasis-basket',
                appearance_preset=slot['appearance_preset'],difficulty=slot['difficulty'],split=slot['split'],
                canonical_goal_position=[float(q[adr]),float(q[adr+1]),.02])
    protected={name:h for name,h in old['source']['implementation'].items() if name.startswith('src/qlm_bench/controllers/') or name in
        ['src/qlm_bench/backends/mujoco/physics.py','src/qlm_bench/backends/mujoco/runtime.py','src/qlm_bench/backends/mujoco/tasks.py',
         'src/qlm_bench/backends/mujoco/render.py','src/qlm_bench/backends/mujoco/lift_reference_smooth.py']}
    for name,h in protected.items():
        if sha(REPO/name)!=h:raise ValueError('Approved semantics changed: '+name)
    source={**copy.deepcopy(old['source']),'work_id':'QLM-DATA-022','implementation':implementation(),
        'native_trace_profile':'native-cpu-original-rambo-v1','execution_profile':'native-cpu-rambo-cpu-egl-v1',
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        'checkpoint_sha256':sha(W/'checkpoints/rambo/go2/quadruped/model_2000.pt')}
    environment={'PYTHONPATH':str(REPO/'src'),'MUJOCO_GL':'egl','PYOPENGL_PLATFORM':'egl','MUJOCO_EGL_DEVICE_ID':'0',
                 'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'4'}
    c={'schema':'qlm-lift100-production-v1','work_id':'QLM-DATA-022','task_id':'lift_basket','authorization':authorization,
       'approval':old['approval'],'source':source,'pilots':pilots,'slots':slots,'template_root':old['template_root'],
       'python':old['python'],'checkpoint':str(W/'checkpoints/rambo/go2/quadruped/model_2000.pt'),
       'entrypoint':str(Path(__file__).resolve()),'data_root':str(W/'data/qlm_bench/lift100-20261015-v1'),
       'ffmpeg':old['ffmpeg'],'ffprobe':old['ffprobe'],'render_environment':environment,
       'render_script':str(REPO/'scripts/mujoco/synthesis/render_trace.py'),'consumer_validation':'task_already_validated_skip',
       'physics_workers':4,'render_workers':4,'near_duplicate_tolerance_dx_dy_yaw_deg':NEAR.tolist(),'quotas':QUOTAS,
       'approved_semantics_preserved':protected,'visual_profile':'explicit user-adopted EGL; no OSMesa pixel-equivalence claim'}
    c['profile_sha256']=digest(c);write_json(root/'campaign.json',c);load_campaign(root/'campaign.json',REPO)
    for name in source['implementation']:
        dst=root/'frozen-source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/name,dst)
    write_json(root/'configuration-coverage.json',{'pilot_parameters':[s['parameters'] for s in pilots],
        'slots':slots,'all_splits_same_ID_support':True,'variable_intervals_partitioned':False,
        'cross_split_near_tolerance_dx_dy_yaw_deg':NEAR.tolist()})
    print('Frozen approved ten plus90,450 candidates; explicit NativeCPU/EGL source profile',flush=True)


def physics(root,a):
    import torch
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    from qlm_bench.backends.mujoco.lift_reference_smooth import SmoothLiftExecutor
    from qlm_bench.backends.mujoco.trace import collect_trace
    from lift_pilots import motion_evidence
    c=load_campaign(root/'campaign.json',REPO);scene=json.loads(Path(a.candidate).read_text())
    declared=next(x for s in c['slots'] for x in s['candidates'] if x['candidate_id']==scene['candidate_id'])
    if scene!=declared or sha(c['checkpoint'])!=c['source']['checkpoint_sha256']:raise ValueError('Frozen scene/checkpoint changed')
    config=json.loads((Path(c['template_root'])/'template.json').read_text())['recipe_config'];torch.set_num_threads(1)
    start=time.monotonic();rt=MuJoCoRuntime(scene['model'],c['checkpoint'],backend='native',device='cpu',trace_only=True,
        seed=scene['seed'],profile_override={'canonical_goal_position':scene['canonical_goal_position']})
    try:
        result=collect_trace(rt,SmoothLiftExecutor(config),scene,a.trace,
            batch_identity={**c['source'],'production_campaign_sha256':c['profile_sha256']},quality_policy='evidence-review-v1')
        if result['passed']:
            motion=motion_evidence(a.trace);write_json(root/'motion'/(scene['candidate_id']+'.json'),motion)
            if not motion['full_foot_through_before_lift']:raise ValueError('Actual successful Lift needs threading behavior review; trace retained')
        result['total_wall_s']=time.monotonic()-start;write_json(a.result,result);print(json.dumps(result),flush=True)
    finally:rt.close()


def finalize(root):
    from qlm_bench.backends.mujoco.rendition import audit_trace,validate_output
    from qlm_bench.compatibility.dataset_v2.merge import merge
    c=load_campaign(root/'campaign.json',REPO);q=json.loads((root/'queue.json').read_text())
    if q['status']!='production_complete' or sum(r['status']=='accepted' for r in q['slots'].values())!=90:raise ValueError('90 actual new accepted episodes required')
    tools=MediaTools(c['ffmpeg'],c['ffprobe']);seen=set();configs=[];entries=[];records=[]
    for s in sorted(c['pilots']+c['slots'],key=lambda x:({'train':0,'validation':1,'test':2}[x['split']],x['episode_uid'])):
        uid=s['episode_uid'];retained='output' in s;row=q['slots'].get(uid)
        out=Path(s['output']) if retained else Path(c['data_root'])/'new'/uid/'episodes'/uid
        trace=s['trace'] if retained else row['trace'];m=verify_trace(trace)[0];audit=audit_trace(trace)
        if audit['trajectory_sha256'] in seen:raise ValueError('Duplicate physical trajectory')
        seen.add(audit['trajectory_sha256'])
        if retained:
            if sha(out/'canonical/meta/checksums.json')!=s['canonical_sha256'] or audit['manifest_sha256']!=s['trace_manifest_sha256']:raise ValueError('Approved pilot changed')
            validate_canonical(out/'canonical',tools=tools,check_media=False)
        else:validate_output(out,profile_path=root/'profiles'/(uid+'.json'),tools=tools,check_media=False)
        point=np.asarray(m['scene']['configuration_parameters'])
        if any(other!=s['split'] and np.all(np.abs(point-old)<=NEAR) for old,other in configs):raise ValueError('Cross-split near duplicate')
        configs.append((point,s['split']));entries.append({'canonical':str(out/'canonical'),'split':s['split']})
        records.append({'episode_uid':uid,'split':s['split'],'difficulty':s['difficulty'],'appearance_preset':s['appearance_preset'],
            'trace':trace,'output':str(out),'parameters_dx_dy_yaw_deg':point.tolist(),'physical_trajectory_sha256':audit['trajectory_sha256'],
            'actions':m['n_actions'],'retained_pilot':retained,'physics':m['backend']['physics'],
            'renderer':'osmesa' if retained else 'egl'})
        print('Final artifact admitted',uid,flush=True)
    destination=Path(c['data_root'])/'canonical'
    merged=merge(entries,destination,tools,'QLM-DATA-022') if not destination.exists() else validate_canonical(destination,tools=tools)
    raw_view=Path(c['data_root'])/'episodes';raw_view.mkdir(exist_ok=True)
    for row in records:
        link=raw_view/row['episode_uid']
        if not link.exists():link.symlink_to(os.path.relpath(row['output'],raw_view),target_is_directory=True)
    epochs=[json.loads(p.read_text()) for p in (root/'execution-policies').glob('*-result.json')]
    report={'passed':True,'accepted':100,'retained_pilots':10,'new_demonstrations':90,'quotas':QUOTAS,
        'actions':sum(s['actions'] for s in records),'boundaries':sum(s['actions']+1 for s in records),'unique_physical_trajectories':100,
        'cross_split_near_duplicates':0,'new_physical_attempts':sum(r['physical_attempts'] for r in q['slots'].values()),
        'consumer_validation':'not_run; existing Lift task-once v2/v3 evidence reused','model_validation_caches_generated':False,
        'backend_composition':{'retained_CUDA_OSMesa':10,'new_NativeCPU_EGL':90},'OSMesa_pixel_equivalence_claimed':False,
        'episodes':records,'collection_validation':merged,'execution_epochs':epochs,'training_AMD_publication':False}
    write_json(root/'completion.json',report)
    (root/'report.md').write_text('# Lift Basket100条本地交付\n\n原批准10条CUDA/OSMesa＋新90条NativeCPU/RAMBO CPU/EGL；各自source身份保持。\n\n'
        +f"{report['actions']}actions/{report['boundaries']}boundaries，80train/10validation/10test、20Clean/80Randomized；跨split无近重复，100物理身份唯一。\n\n"
        +'4physics+4render为目标，实际并发/资源保护/降档见execution-policies。EGL为用户采用的独立本地visual profile，不宣称与OSMesa像素等价；AMD参考/smoke保持。\n\n'
        +'原recipe/native9/force-zero/时序/camera/success predicate保持；WAM task一次资格复用，无新WAM验证/cache/fit/训练。Raw视图为明确相对symlink，发布前须独立materialized staging。\n\n完成后随机十条交用户最终验收，未训练/AMD/commit/push/发布。\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=('prepare','physics','admission','run','finalize'));p.add_argument('--root',required=True)
    for key in ('candidate','trace','result'):p.add_argument('--'+key)
    p.add_argument('--physics-workers',type=int,default=4);p.add_argument('--render-workers',type=int,default=4)
    a=p.parse_args();root=Path(a.root).resolve()
    if a.stage=='prepare':prepare(root)
    elif a.stage=='physics':physics(root,a)
    elif a.stage=='finalize':finalize(root)
    else:
        if a.stage=='run' and not (root/'production-admission.json').is_file():raise ValueError('Actual Native/EGL end-to-end admission required')
        LiftProductionQueue(root,root/'campaign.json',REPO).run_parallel(a.physics_workers,a.render_workers,admission=a.stage=='admission')
