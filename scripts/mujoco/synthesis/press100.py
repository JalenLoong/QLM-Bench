"""Approved Press100: retain ten, synthesize90, no WAM consumer execution."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
from qlm_bench.backends.mujoco.press_production import configuration_candidates,translate_press,load_campaign,PressProductionQueue,QUOTAS,NEAR
from qlm_bench.backends.mujoco.trace import sha,write_json,verify_trace
from qlm_bench.compatibility.dataset_v2.validation import digest,validate_canonical
from qlm_bench.compatibility.dataset_v2.media import MediaTools

REPO=Path(__file__).resolve().parents[3];W=REPO.parents[1]
PILOT=W/'runs/audit/press-formal-pilots-20261015-v1'


def implementation():
    return {str(p.relative_to(REPO)):sha(p) for folder in ('src/qlm_bench','scripts/mujoco/synthesis')
            for p in sorted((REPO/folder).rglob('*')) if p.suffix in ('.py','.json')}


def pilot_members():
    c=json.loads((PILOT/'campaign.json').read_text());state=json.loads((PILOT/'campaign-state.json').read_text())
    pilots=[]
    for slot in c['slots']:
        uid=slot['episode_uid'];row=state['slots'][uid];p=json.loads(Path(row['recording_profile']).read_text());s=p['slots'][0]
        out=W/'data/qlm_bench/press-approved-pilot-20261015-v1/slots'/uid/'episodes'/uid
        pilots.append({**copy.deepcopy(s),'parameters':row['scene']['configuration_parameters'],'output':str(out),
            'recording_profile':row['recording_profile'],'canonical_sha256':sha(out/'canonical/meta/checksums.json')})
    return pilots,c


def validate_pilot_reuse(root,pilots):
    # Verify the original producer with its actual frozen implementation, not a new source label.
    program="""import json,sys
from qlm_bench.backends.mujoco.rendition import validate_output
from qlm_bench.backends.mujoco.trace import write_json
from qlm_bench.compatibility.dataset_v2.media import MediaTools
p=json.load(open(sys.argv[1]));r=[validate_output(s['output'],profile_path=s['recording_profile'],tools=MediaTools(p['ffmpeg'],p['ffprobe']),check_media=False) for s in p['pilots']]
write_json(sys.argv[2],{'passed':True,'episodes':r,'source':'original frozen Press pilot source','WAM_execution':False})
"""
    input_path=root/'pilot-reuse-input.json';old=json.loads((PILOT/'campaign.json').read_text())
    write_json(input_path,{'pilots':pilots,'ffmpeg':old['ffmpeg'],'ffprobe':old['ffprobe']})
    env=dict(os.environ,PYTHONPATH=str(PILOT/'frozen-source/src'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    subprocess.run([old['python'],'-c',program,str(input_path),str(root/'pilot-reuse-validation.json')],env=env,check=True)


def prepare(root):
    from prepare_backgrounds import prepare as backgrounds
    from qlm_bench.backends.mujoco.resources import resource_closure
    authorization=json.loads((root/'user-approval.json').read_text());assert authorization['pilot_approved'] and authorization['target_accepted']==100
    pilots,old=pilot_members();validate_pilot_reuse(root,pilots);slots=configuration_candidates(pilots)
    background_path=root/'backgrounds-base/backgrounds.json'
    bg=json.loads(background_path.read_text()) if background_path.exists() else backgrounds(W/'assets/mujoco/press-full-wall-a-v1/scene.xml',root/'backgrounds-base',work_id='QLM-DATA-019')
    base_models={r['preset']:r['model'] for r in bg['profiles']}
    base_identities={r['preset']:resource_closure(r['model'],require_portable=True)['identity'] for r in bg['profiles']}
    initial=verify_trace(pilots[0]['trace'])[0]['scene']['initial_state']
    for slot in slots:
        for scene in slot['candidates']:
            yz=scene['configuration_parameters'];dst=root/'resources'/scene['candidate_id'];preset=slot['appearance_preset']
            if dst.exists():
                existing=json.loads((dst/'scene.task.json').read_text())
                if existing['environment_profile']['button_in_plane_yz_m']!=yz or existing.get('appearance_preset','ap_00')!=preset or existing['wall_position_variant']['parent_resource_identity']!=base_identities[preset]:
                    old=root/'preparation-replaced'/scene['candidate_id'];old.parent.mkdir(parents=True,exist_ok=True);dst.rename(old)
            identity=resource_closure(dst/'scene.xml',require_portable=True)['identity'] if dst.exists() else translate_press(base_models[preset],dst,*yz)['identity']
            state=copy.deepcopy(initial);state['model_identity']=identity
            scene.update(task_id='press_button',model=str(dst/'scene.xml'),model_identity=identity,initial_state=state,asset_id='industrial-button',
                appearance_preset=slot['appearance_preset'],difficulty=slot['difficulty'],split=slot['split'])
        print('Frozen Press slot',slot['episode_uid'],flush=True)
    # Execution/controller/native9 semantics must remain byte-identical to the approved source.
    preserved={name:h for name,h in old['source']['implementation'].items() if name.startswith('src/qlm_bench/controllers/') or name in [
        'src/qlm_bench/backends/mujoco/press_reference_smooth.py','src/qlm_bench/backends/mujoco/physics.py','src/qlm_bench/backends/mujoco/runtime.py',
        'src/qlm_bench/backends/mujoco/tasks.py','src/qlm_bench/backends/mujoco/render.py']}
    for name,h in preserved.items():
        if sha(REPO/name)!=h:raise ValueError('Approved physical/controller semantics changed: '+name)
    source={**copy.deepcopy(old['source']),'work_id':'QLM-DATA-019','implementation':implementation(),
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        'checkpoint_sha256':sha(W/'checkpoints/rambo/go2/quadruped/model_2000.pt')}
    c={'schema':'qlm-press100-production-v1','work_id':'QLM-DATA-019','task_id':'press_button','authorization':authorization,'approval':old['approval'],
        'source':source,'pilots':pilots,'slots':slots,'template_root':old['template_root'],'python':old['python'],
        'checkpoint':str(W/'checkpoints/rambo/go2/quadruped/model_2000.pt'),'entrypoint':str(Path(__file__).resolve()),
        'data_root':str(W/'data/qlm_bench/press100-20261015-v1'),'ffmpeg':old['ffmpeg'],'ffprobe':old['ffprobe'],
        'render_environment':old['render_environment'],'render_script':str(REPO/'scripts/mujoco/synthesis/render_trace.py'),'warp_cache':str(W/'cache/warp'),
        'consumer_validation':'task_already_validated_skip','physics_workers':4,'render_workers':4,'maximum_pending_traces':8,
        'near_duplicate_tolerance_yz_m':NEAR.tolist(),'quotas':QUOTAS,'approved_semantics_preserved':preserved}
    c['profile_sha256']=digest(c);write_json(root/'campaign.json',c);load_campaign(root/'campaign.json',REPO)
    for name in source['implementation']:
        dst=root/'frozen-source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/name,dst)
    write_json(root/'configuration-coverage.json',{'pilots':[{k:s[k] for k in ('episode_uid','split','difficulty','parameters')} for s in pilots],
        'planned':[{k:s[k] for k in ('episode_uid','split','difficulty','appearance_preset','geometry_bin')}|{'candidates':[d['configuration_parameters'] for d in s['candidates']]} for s in slots],
        'same_ID_support_for_all_splits':True,'intervals_partitioned':False,'near_duplicate_tolerance_yz_m':NEAR.tolist()})
    print(json.dumps({'frozen':True,'retained_pilots':10,'new_slots':90,'candidate_count':450,'campaign_sha256':c['profile_sha256']}),flush=True)


def physics(root,a):
    import torch
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    from qlm_bench.backends.mujoco.press_reference_smooth import SmoothPressExecutor
    from qlm_bench.backends.mujoco.trace import collect_trace
    from qlm_bench.backends.mujoco.quality import analyze_trace
    from qlm_bench.backends.mujoco.resources import resource_closure
    from press_pilots import motion_evidence
    c=load_campaign(root/'campaign.json',REPO);scene=json.loads(Path(a.candidate).read_text())
    declared=next(s for slot in c['slots'] for s in slot['candidates'] if s['candidate_id']==scene['candidate_id'])
    if scene!=declared or resource_closure(scene['model'],require_portable=True)['identity']!=scene['model_identity']:raise ValueError('Frozen candidate/model changed')
    if sha(c['checkpoint'])!=c['source']['checkpoint_sha256']:raise ValueError('Original RAMBO checkpoint changed')
    config=json.loads((Path(c['template_root'])/'template.json').read_text())['recipe_config'];torch.set_num_threads(1);start=time.monotonic()
    rt=MuJoCoRuntime(scene['model'],c['checkpoint'],trace_only=True,seed=scene['seed'])
    try:
        result=collect_trace(rt,SmoothPressExecutor(config),scene,a.trace,batch_identity={**c['source'],'production_campaign_sha256':c['profile_sha256']},quality_policy='evidence-review-v1')
        if result['passed']:
            review,_=analyze_trace(a.trace);motion=motion_evidence(a.trace);write_json(root/'motion'/(scene['candidate_id']+'.json'),motion)
            if review['contact']['body_contact_boundaries'] or motion['actual_range_deg'][0]>15 or motion['actual_max_10ms_step_deg'][0]>2:
                write_json(root/'review-holds'/(scene['candidate_id']+'.json'),{'task_success':True,'quality':review,'motion':motion,'automatic_task_failure':False})
                raise ValueError('Actual successful Press behavior needs review; trace retained')
        result['total_wall_s']=time.monotonic()-start;write_json(a.result,result);print(json.dumps(result),flush=True)
    finally:rt.close()


def finalize(root):
    from qlm_bench.backends.mujoco.rendition import audit_trace,validate_output
    from qlm_bench.compatibility.dataset_v2.merge import merge
    c=load_campaign(root/'campaign.json',REPO);q=json.loads((root/'queue.json').read_text())
    if q['status']!='production_complete' or sum(r['status']=='accepted' for r in q['slots'].values())!=90:raise ValueError('Actual90 accepted outputs required')
    tools=MediaTools(c['ffmpeg'],c['ffprobe']);seen=set();configs=[];entries=[];records=[]
    members=sorted(c['pilots']+c['slots'],key=lambda s:({'train':0,'validation':1,'test':2}[s['split']],s['episode_uid']))
    for s in members:
        retained='output' in s;uid=s['episode_uid'];row=q['slots'].get(uid);output=Path(s['output']) if retained else Path(c['data_root'])/'new'/uid/'episodes'/uid
        trace=s['trace'] if retained else row['trace'];m=verify_trace(trace)[0];audit=audit_trace(trace)
        if audit['trajectory_sha256'] in seen:raise ValueError('Duplicate actual physical trajectory')
        seen.add(audit['trajectory_sha256'])
        if retained:
            if sha(output/'canonical/meta/checksums.json')!=s['canonical_sha256'] or audit['manifest_sha256']!=s['trace_manifest_sha256']:raise ValueError('Approved pilot bytes changed')
            validate_canonical(output/'canonical',tools=tools,check_media=False)
        else:validate_output(output,profile_path=root/'profiles'/(uid+'.json'),tools=tools,check_media=False)
        params=np.array(m['scene']['configuration_parameters'])
        if any(split!=s['split'] and np.all(np.abs(params-old)<=NEAR) for old,split in configs):raise ValueError('Cross-split near duplicate')
        configs.append((params,s['split']));entries.append({'canonical':str(output/'canonical'),'split':s['split']})
        records.append({'episode_uid':uid,'split':s['split'],'difficulty':s['difficulty'],'appearance_preset':s['appearance_preset'],'trace':trace,
            'output':str(output),'canonical':str(output/'canonical'),'parameters_yz_m':params.tolist(),'physical_trajectory_sha256':audit['trajectory_sha256'],
            'actions':m['n_actions'],'retained_pilot':retained,'quality':audit['quality']})
        print('Final artifact admitted',uid,flush=True)
    destination=Path(c['data_root'])/'canonical'
    merged=merge(entries,destination,tools,'QLM-DATA-019') if not destination.exists() else validate_canonical(destination,tools=tools)
    events=[json.loads(l) for l in (root/'events.jsonl').read_text().splitlines()];results=[e for e in events if e['event']=='physics_result']
    report={'passed':True,'accepted':100,'retained_pilots':10,'new_demonstrations':90,'quotas':QUOTAS,'actions':sum(r['actions'] for r in records),
        'boundaries':sum(r['actions']+1 for r in records),'unique_physical_trajectories':len(seen),'cross_split_near_duplicates':0,
        'new_physical_attempts':sum(r['physical_attempts'] for r in q['slots'].values()),'failed_physical_candidates':sum(not e['result']['passed'] for e in results),
        'consumer_validation':'not_run; once-per-task Press evidence reused','model_validation_caches_generated':False,
        'dataset_root':str(destination),'episodes':records,'collection_validation':merged,'training_AMD_publication':False}
    write_json(root/'completion.json',report)
    lines=['# Press Button100条本地交付','',f"保留审核通过10条＋新90条，共{report['actions']}actions/{report['boundaries']}boundaries。",'','| Split | Clean | Randomized | Total |','|---|---:|---:|---:|']
    for split,d in QUOTAS.items():lines.append(f"|{split}|{d['clean']}|{d['randomized']}|{sum(d.values())}|")
    lines+=['',f"新physics尝试{report['new_physical_attempts']}，失败candidate{report['failed_physical_candidates']}；这不是policy成功率。",
        '已验收原RAMBO/press-body-carry-v2/真实12mm三tick/not-fallen/完整wall/固定X及Y/Z范围/双背景/360p50FPS保持；primary A only，backup不占quota。',
        '各split同一ID支持，具体配置跨split去重；100物理身份唯一。成功Trace只offline Native OSMesa渲染，镜像不推进physics。',
        'WAM v2/v3 task一次资格复用，无重复验证、新模型缓存、fit或训练。实际并发及resource保护见execution-policies/resources.jsonl。',
        '未进行其他task/训练/AMD/commit/push或发布；完成后另交均匀随机十条review。']
    (root/'report.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'accepted':100,'actions':report['actions'],'attempts':report['new_physical_attempts']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=('prepare','physics','run','finalize'));p.add_argument('--root',required=True)
    for k in ('candidate','trace','result'):p.add_argument('--'+k)
    p.add_argument('--physics-workers',type=int,default=4);p.add_argument('--render-workers',type=int,default=4)
    a=p.parse_args();root=Path(a.root).resolve()
    if a.stage=='prepare':prepare(root)
    elif a.stage=='physics':physics(root,a)
    elif a.stage=='finalize':finalize(root)
    else:PressProductionQueue(root,root/'campaign.json',REPO).run_parallel(a.physics_workers,a.render_workers)
