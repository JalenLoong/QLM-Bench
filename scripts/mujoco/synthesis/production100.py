"""User-approved Push100 production. No adaptation-v2/v3 validation stage."""
import argparse,copy,importlib.util,json,os,shutil,subprocess,time
from pathlib import Path
import numpy as np
from qlm_bench.backends.mujoco.production import configuration_candidates,load_campaign,ProductionQueue,QUOTAS,NEAR
from qlm_bench.backends.mujoco.trace import sha,write_json,verify_trace,collect_trace
from qlm_bench.compatibility.dataset_v2.validation import digest,validate_canonical
from qlm_bench.compatibility.dataset_v2.pilot_rendition import validate_formal_pilot
from qlm_bench.compatibility.dataset_v2.media import MediaTools

REPO=Path(__file__).resolve().parents[3];W=REPO.parents[1]

def implementation():
 return {str(p.relative_to(REPO)):sha(p) for folder in ['src/qlm_bench','scripts/mujoco/synthesis'] for p in sorted((REPO/folder).rglob('*')) if p.suffix in ('.py','.json')}

def prepare(root):
 import mujoco
 authorization=json.loads((root/'user-approval.json').read_text())
 oldroot=W/'runs/audit/push-formal-pilots-20261014-v3';old=json.loads((oldroot/'recording-profile.json').read_text())
 tools=MediaTools(old['ffmpeg'],old['ffprobe']);pilots=[]
 for s in old['slots']:
  output=W/'data/qlm_bench/push-approved-pilot-20261014-v3/episodes'/s['episode_uid']
  validate_formal_pilot(output/'canonical',profile_path=oldroot/'recording-profile.json',tools=tools,check_media=False)
  m=verify_trace(s['trace'])[0]
  if sha(Path(s['trace'])/'manifest.json')!=s['trace_manifest_sha256']:raise ValueError('Approved pilot trace changed')
  pilots.append({**copy.deepcopy(s),'output':str(output),'canonical_sha256':sha(output/'canonical/meta/checksums.json'),
                 'parameters':m['scene']['configuration_parameters']})
 spec=importlib.util.spec_from_file_location('approved_pilot_assets',REPO/'scripts/mujoco/synthesis/approved_pilots.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 slots=configuration_candidates(pilots);template=json.loads((Path(old['template_root'])/'template.json').read_text())
 for slot in slots:
  uid=slot['episode_uid'];source=W/f"assets/mujoco/push-two-backgrounds-20261014-v1/{slot['appearance_preset']}/scene.xml"
  model=root/'resources-production-v2'/uid/'scene.xml';model.parent.parent.mkdir(parents=True,exist_ok=True)
  goal=slot['candidates'][0]['configuration_parameters'][3:]
  closure=helper.goal_variant(source,model.parent,*goal,work_id='QLM-DATA-016')
  task=json.loads(model.with_suffix('.task.json').read_text());compiled=mujoco.MjModel.from_xml_path(str(model))
  joint=mujoco.mj_name2id(compiled,mujoco.mjtObj.mjOBJ_JOINT,'object_free');assert joint>=0;adr=int(compiled.jnt_qposadr[joint])
  candidates=[]
  for declared in slot['candidates']:
   scene=copy.deepcopy(template['source_scene']);scene.update(declared)
   scene.update(model=str(model),appearance_preset=slot['appearance_preset'],difficulty=slot['difficulty'],split=slot['split'],
                goal_x=task['goal_x'],goal_y=task['goal_y'],canonical_goal_position=task['canonical_goal_position'])
   params=np.array(declared['configuration_parameters']);q=np.array(scene['initial_state']['qpos']);q[adr:adr+2]+=params[:2]
   quat=np.empty(4);mujoco.mju_mulQuat(quat,np.array([np.cos(params[2]/2),0,0,np.sin(params[2]/2)]),q[adr+3:adr+7]);q[adr+3:adr+7]=quat
   scene['initial_state'].update(qpos=q.tolist(),model_identity=closure['identity']);candidates.append(scene)
  slot['candidates']=candidates;print('Frozen candidate resource',uid,flush=True)
 source={'work_id':'QLM-DATA-016','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
  'implementation':implementation(),'template_id':old['template_id'],'template_sha256':old['template_sha256'],
  'executor_variant':'cross-track-smooth-v3','maximum_world_target_step_m':.008,'approval_sha256':digest(old['approval']),
  'checkpoint_sha256':sha(W/'checkpoints/rambo/go2/quadruped/model_2000.pt')}
 campaign={'schema':'qlm-push100-production-v1','work_id':'QLM-DATA-016','task_id':'push_box','authorization':authorization,'approval':old['approval'],
  'source':source,'pilots':pilots,'slots':slots,'template_root':old['template_root'],'python':str(W/'envs/qlm-mujoco-py312-v1/bin/python'),
  'checkpoint':str(W/'checkpoints/rambo/go2/quadruped/model_2000.pt'),'entrypoint':str(Path(__file__).resolve()),
  'data_root':str(W/'data/qlm_bench/push100-20261014-v1'),'ffmpeg':old['ffmpeg'],'ffprobe':old['ffprobe'],
  'render_environment':old['render_environment'],'render_script':old['render_script'],'warp_cache':str(W/'cache/warp'),
  'consumer_validation':'task_already_validated_skip','physics_workers':1,'render_workers':2,'maximum_pending_traces':3,
  'near_duplicate_tolerance_m_rad':NEAR.tolist(),'quotas':QUOTAS}
 campaign['profile_sha256']=digest(campaign);write_json(root/'campaign.json',campaign);load_campaign(root/'campaign.json',REPO)
 for relative in source['implementation']:
  dest=root/'frozen-source'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/relative,dest)
 write_json(root/'configuration-coverage.json',{'approved_pilots':[{k:s[k] for k in ['episode_uid','difficulty','split','appearance_preset','parameters']} for s in pilots],
  'planned':[{k:s[k] for k in ['episode_uid','difficulty','split','appearance_preset','geometry_bin']}|{'candidates':[c['configuration_parameters'] for c in s['candidates']]} for s in slots],
  'same_ID_support_for_all_splits':True,'cross_split_configuration_deduplication':True,'WAM_validation_stage':False})
 print(json.dumps({'passed':True,'retained':10,'new_slots':90,'profile_sha256':campaign['profile_sha256']}),flush=True)

def physics(root,args):
 import torch
 from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
 from qlm_bench.backends.mujoco.reference_retarget import ContactAwarePushExecutor
 p=load_campaign(root/'campaign.json',REPO);scene=json.loads(Path(args.candidate).read_text());torch.set_num_threads(1)
 declared=[c for s in p['slots'] for c in s['candidates'] if c['candidate_id']==scene['candidate_id']]
 if len(declared)!=1 or declared[0]!=scene:raise ValueError('Candidate differs from predeclared profile')
 if sha(p['checkpoint'])!=p['source']['checkpoint_sha256']:raise ValueError('Frozen original RAMBO checkpoint changed')
 start=time.monotonic();rt=MuJoCoRuntime(scene['model'],p['checkpoint'],trace_only=True,seed=scene['seed'])
 try:
  executor=ContactAwarePushExecutor(p['template_root'],working_y=.12,gain=1.,maximum_world_step=.008)
  if rt.profile.get('appearance_preset','ap_00')!=scene['appearance_preset']:raise ValueError('Scene preset mismatch')
  result=collect_trace(rt,executor,scene,args.trace,batch_identity=p['source'],quality_policy='evidence-review-v1')
  result.update(total_wall_s=time.monotonic()-start,configuration_sha256=scene['configuration_sha256']);write_json(args.result,result)
  print(json.dumps(result),flush=True)
 finally:rt.close()

def finalize(root):
 from qlm_bench.compatibility.dataset_v2.merge import merge
 from qlm_bench.backends.mujoco.rendition import audit_trace,validate_output
 p=load_campaign(root/'campaign.json',REPO);queue=json.loads((root/'queue.json').read_text());tools=MediaTools(p['ffmpeg'],p['ffprobe'])
 if queue['status']!='production_complete' or any(v['status']!='accepted' for v in queue['slots'].values()):raise ValueError('100 actual accepted episodes required')
 records=[];seen=set();configs=[];entries=[]
 for s in p['pilots']+p['slots']:
  uid=s['episode_uid'];pilot='output' in s
  output=Path(s['output']) if pilot else Path(p['data_root'])/'new'/uid/'episodes'/uid
  trace=s['trace'] if pilot else queue['slots'][uid]['trace']
  audit=audit_trace(trace);m=verify_trace(trace)[0]
  if audit['trajectory_sha256'] in seen:raise ValueError('Duplicate physical trajectory')
  seen.add(audit['trajectory_sha256'])
  if pilot:
   if sha(output/'canonical/meta/checksums.json')!=s['canonical_sha256'] or audit['manifest_sha256']!=s['trace_manifest_sha256']:raise ValueError('Approved pilot changed')
   validate_canonical(output/'canonical',tools=tools,check_media=False)
  else:validate_output(output,profile_path=root/'profiles'/f'{uid}.json',tools=tools,check_media=False)
  params=np.array(m['scene']['configuration_parameters'])
  if any(split!=s['split'] and np.all(np.abs(params-other)<=NEAR) for other,split in configs):raise ValueError('Cross-split near duplicate')
  configs.append((params,s['split']));entries.append({'canonical':str(output/'canonical'),'split':s['split']})
  records.append({'episode_uid':uid,'split':s['split'],'difficulty':s['difficulty'],'appearance_preset':s['appearance_preset'],
                  'trace':trace,'canonical':str(output/'canonical'),'configuration_parameters':params.tolist(),
                  'physical_trajectory_sha256':audit['trajectory_sha256'],'actions':m['n_actions'],'retained_pilot':pilot})
 destination=Path(p['data_root'])/'canonical'
 if not destination.exists():merged=merge(entries,destination,tools,'QLM-DATA-016')
 else:merged=validate_canonical(destination,tools=tools)
 events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
 attempts=[e for e in events if e['event']=='physics_result'];failed=[e for e in attempts if not e['result']['passed']]
 report={'passed':True,'accepted':100,'retained_pilots':10,'new_demonstrations':90,'quotas':QUOTAS,'actions':sum(r['actions'] for r in records),
  'boundaries':sum(r['actions']+1 for r in records),'unique_physical_trajectories':len(seen),'cross_split_near_duplicates':0,
  'new_physical_attempts':sum(v['physical_attempts'] for v in queue['slots'].values()),'failed_physical_candidates':len(failed),
  'consumer_validation':'not_run; user rule: once per task; prior Push evidence retained','model_validation_caches_generated':False,
  'dataset_root':str(destination),'episodes':records,'collection_validation':merged,'training_AMD_publication':False}
 write_json(root/'completion.json',report)
 lines=['# Push Box 100条本地交付','',f"100条：原审核通过10条＋新90条；共{report['actions']} actions / {report['boundaries']} boundaries。",'','| Split | Clean | Randomized | Total |','|---|---:|---:|---:|']
 for split,counts in QUOTAS.items():lines.append(f"|{split}|{counts['clean']}|{counts['randomized']}|{sum(counts.values())}|")
 lines+=['',f"本次新physics尝试{report['new_physical_attempts']}次，失败candidate {len(failed)}次；不将success-filtered数据收集率作为policy benchmark。",
  '100条物理身份唯一；split从相同已批准ID分布采样并排除跨split近重复。Clean均ap_00；Randomized覆盖两套背景和真实几何变化。',
  'QLM逐条physics/quality/Raw/Canonical/terminal/media验收与最终合并验证通过。WAM v2/v3未重复验证、未生成模型缓存；复用该task已有验收。',
  '原RAMBO/native9、physics/controller频率、camera、success predicate、primaryBox05与smooth-v3保持。失败仅轻量日志，成功trace支持独立渲染恢复。',
  '未进行训练、AMD、其他任务、commit/push或发布。']
 (root/'report.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:report[k] for k in ['accepted','new_physical_attempts','actions','boundaries']}),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('stage',choices=['prepare','run','physics','finalize']);ap.add_argument('--root',required=True)
 ap.add_argument('--candidate');ap.add_argument('--trace');ap.add_argument('--result');a=ap.parse_args();root=Path(a.root).resolve()
 if a.stage=='prepare':prepare(root)
 elif a.stage=='physics':physics(root,a)
 elif a.stage=='finalize':finalize(root)
 else:
  ProductionQueue(root,root/'campaign.json',REPO).run();finalize(root)
