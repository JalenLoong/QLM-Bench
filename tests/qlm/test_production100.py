import copy,json,threading,time
from pathlib import Path
import numpy as np
import pytest
from qlm_bench.backends.mujoco.production import configuration_candidates,LIMITS,CLEAN_LIMITS,NEAR,QUOTAS,ProductionQueue
from qlm_bench.backends.mujoco import production
from qlm_bench.compatibility.dataset_v2.validation import digest
from qlm_bench.compatibility.dataset_v2.pilot_rendition import load_profile,PRODUCTION_SCHEMA


def pilots():
 centers=[[.003,-.003,.005,.002,-.001],[-.003,.003,-.005,-.002,.001]]+[[.035*(1 if i&1 else -1),.03*(1 if i&2 else -1),.05*(1 if i&4 else -1),0,0] for i in range(8)]
 return [{'parameters':v,'split':'train','difficulty':'clean' if i<2 else 'randomized','appearance_preset':'ap_00' if i<2 or i%2==0 else 'ap_01'} for i,v in enumerate(centers)]

def test_same_ID_split_quotas_real_geometry_and_cross_split_dedup():
 prior=pilots();rows=configuration_candidates(prior);assert rows==configuration_candidates(prior)
 assert len(rows)==90
 actual={s:{d:0 for d in ['clean','randomized']} for s in QUOTAS}
 configs=[(np.array(s['parameters']),s['split']) for s in prior]
 for row in prior+rows:actual[row['split']][row['difficulty']]+=1
 assert actual==QUOTAS
 for row in rows:
  assert len(row['candidates'])==5
  if row['difficulty']=='clean':assert row['appearance_preset']=='ap_00'
  for c in row['candidates']:
   p=np.array(c['configuration_parameters']);limit=CLEAN_LIMITS if row['difficulty']=='clean' else LIMITS
   assert np.all(np.abs(p)<=limit+1e-12)
   if row['difficulty']=='randomized':assert np.max(np.abs(p[:3])/LIMITS[:3])>.25
   assert all(not np.all(np.abs(p-old)<=NEAR) for old,split in configs if split!=row['split'])
   configs.append((p,row['split']))
 for split in QUOTAS:
  assert len({r['geometry_bin'] for r in rows if r['split']==split and r['difficulty']=='randomized'})==8

@pytest.mark.parametrize('split',['train','validation','test'])
def test_explicit_one_episode_production_admission_preserves_pilot_rules(tmp_path,split):
 p={'schema':PRODUCTION_SCHEMA,'task_id':'push_box','rgb_profile':'dual-rgb-360p-v1','maximum_render_attempts':3,
    'campaign_sha256':'frozen','production_authorization':{'pilot_approved':True,'target_accepted':100},
    'quality_policy':'evidence-review-v1','approval':{'reference_quality_approved':True,'retarget_scope_approved':True,'evidence_sha256':{'proof':'abc'}},
    'slots':[{'episode_uid':'new','rendition_id':'record','physical_trajectory_sha256':'actual','task_id':'push_box','difficulty':'clean','appearance_preset':'ap_00','split':split,'quality_review_sha256':'measured','review_status':'approved_task_recipe_technical_quality'}]}
 def save():
  p.pop('profile_sha256',None);p['profile_sha256']=digest(p);f=tmp_path/'profile.json';f.write_text(json.dumps(p));return f
 assert load_profile(save())['slots'][0]['split']==split
 p['production_authorization']['pilot_approved']=False
 with pytest.raises(ValueError,match='Approved100'):load_profile(save())
 p['production_authorization']['pilot_approved']=True;p['slots'][0]['appearance_preset']='ap_01'
 with pytest.raises(ValueError,match='Clean'):load_profile(save())


def test_staged_queue_has_one_physics_two_render_workers_and_no_model_validation(tmp_path,monkeypatch):
 slots=[{'episode_uid':str(i),'candidates':[{'candidate_id':f'{i}-{j}'} for j in range(5)]} for i in range(90)]
 p={'profile_sha256':'fixed','slots':slots,'data_root':str(tmp_path/'data')}
 monkeypatch.setattr(production,'load_campaign',lambda *_:p)
 q=ProductionQueue(tmp_path/'queue',tmp_path/'campaign',tmp_path)
 active={'physics':0,'render':0};maxima=active.copy();calls=[];lock=threading.Lock()
 def job(kind,uid):
  with lock:active[kind]+=1;maxima[kind]=max(maxima[kind],active[kind]);calls.append((kind,uid))
  time.sleep(.003)
  with lock:active[kind]-=1
  return {'passed':False if kind=='physics' and uid=='0-0' else True}
 q.physics_job=lambda scene,trace:job('physics',scene['candidate_id'])
 q.render_job=lambda uid:job('render',uid)
 q.retain=lambda s,r:r.update(status='render_pending',trajectory_sha256=s['episode_uid'])
 q.run();assert q.accepted()==100 and q.state['status']=='production_complete'
 assert maxima['physics']==1 and maxima['render']<=2
 assert sum(k=='physics' for k,_ in calls)==91
 assert q.state['slots']['0']['physical_attempts']==2
 assert not any(k=='model' for k,_ in calls)


def test_system_error_stops_new_work(tmp_path,monkeypatch):
 p={'profile_sha256':'fixed','slots':[{'episode_uid':str(i),'candidates':[{'candidate_id':str(i)}]*5} for i in range(90)],'data_root':str(tmp_path/'data')}
 monkeypatch.setattr(production,'load_campaign',lambda *_:p);q=ProductionQueue(tmp_path/'queue',tmp_path/'campaign',tmp_path);calls=[]
 def fail(scene,trace):calls.append(scene);raise RuntimeError('source/model mismatch')
 q.physics_job=fail
 with pytest.raises(RuntimeError,match='mismatch'):q.run()
 assert len(calls)==1 and q.state['status']=='stopped'


def test_quality_hold_requires_trace_bound_actual_review_evidence(tmp_path,monkeypatch):
 from qlm_bench.backends.mujoco.trace import sha,write_json
 audit={'manifest_sha256':'actual-trace','source_identity_sha256':'source','trajectory_sha256':'trajectory','quality':{}}
 manifest={'scene':{'model':'scene.xml','candidate_id':'candidate','appearance_preset':'ap_00','seed':7},'model_identity':'model','profile':{'asset_id':'box'},'n_actions':400}
 review={'actual_measurement':'requires-inspection'}
 monkeypatch.setattr(production,'audit_trace',lambda _:audit);monkeypatch.setattr(production,'verify_trace',lambda _:(manifest,))
 monkeypatch.setattr(production,'analyze_trace',lambda _:(review,{}));monkeypatch.setattr(production,'quality_flags',lambda _:['behavior flag'])
 slot={'episode_uid':'uid','task_id':'push_box','difficulty':'clean','split':'train'}
 campaign={k:'fixture' for k in ['template_root','python','ffmpeg','ffprobe','render_script','profile_sha256']}
 campaign.update(approval={},render_environment={},source={'template_sha256':'template','template_id':'template'})
 path=tmp_path/'profiles/uid.json'
 with pytest.raises(ValueError,match='review hold'):production.freeze_episode(campaign,slot,tmp_path/'trace',path)
 proof=tmp_path/'review.txt';proof.write_text('Synthetic review fixture')
 resolution={'accepted':True,'trace_manifest_sha256':'wrong','quality_review_sha256':digest(review),'flags':['behavior flag'],'evidence':[{'path':str(proof),'sha256':sha(proof)}]}
 dest=tmp_path/'quality-resolutions/uid.json';write_json(dest,resolution)
 with pytest.raises(production.RecordingIntegrityError,match='does not match'):production.freeze_episode(campaign,slot,tmp_path/'trace',path)
 resolution['trace_manifest_sha256']='actual-trace';write_json(dest,resolution)
 member,_=production.freeze_episode(campaign,slot,tmp_path/'trace',path)
 assert member['behavior_review_resolution']==resolution
 proof.write_text('Changed evidence')
 with pytest.raises(production.RecordingIntegrityError,match='evidence changed'):production.freeze_episode(campaign,slot,tmp_path/'trace',path)
