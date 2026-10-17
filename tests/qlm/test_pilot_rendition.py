"""Render-only recovery and immutable-source formal pilot admission gates."""
import copy,json
from pathlib import Path
import pytest
from qlm_bench.compatibility.dataset_v2.validation import digest
from qlm_bench.compatibility.dataset_v2.pilot_rendition import load_profile,SCHEMA
from qlm_bench.backends.mujoco import rendition

ROOT=Path(__file__).resolve().parents[4]
TOOLS=ROOT/'cache/tools/bin'


def profile_file(tmp_path):
 profile={'schema':SCHEMA,'work_id':'QLM-DATA-014','task_id':'push_box','rgb_profile':'dual-rgb-360p-v1',
  'maximum_render_attempts':3,'ffmpeg':str(TOOLS/'ffmpeg'),'ffprobe':str(TOOLS/'ffprobe'),'slots':[]}
 for i in range(10):profile['slots'].append({'episode_uid':f'ep{i}','rendition_id':f'ep{i}@360v1',
  'physical_trajectory_sha256':str(i),'difficulty':'clean' if i<2 else 'randomized','task_id':'push_box','split':'train'})
 profile['profile_sha256']=digest(profile);p=tmp_path/'profile.json';p.write_text(json.dumps(profile));return p


def test_profile_rejects_duplicate_physical_demos_even_if_renditions_differ(tmp_path):
 p=profile_file(tmp_path);profile=load_profile(p);profile['slots'][1]['physical_trajectory_sha256']='0'
 profile.pop('profile_sha256');profile['profile_sha256']=digest(profile);p.write_text(json.dumps(profile))
 with pytest.raises(ValueError,match='Duplicate'):load_profile(p)


def test_recovery_revalidates_bytes_and_never_reexecutes_physics(tmp_path,monkeypatch):
 p=profile_file(tmp_path);monkeypatch.setattr(rendition,'validate_slot_inputs',lambda *_:None)
 calls=[]
 def validator(output):
  v=json.loads((output/'payload.json').read_text());assert v['complete'];return {'passed':True,'episode_uid':v['uid']}
 def worker(slot,out,attempt):
  calls.append(attempt)
  if attempt==1:raise RuntimeError('Transient encoder failure')
  out.mkdir(parents=True);(out/'payload.json').write_text(json.dumps({'uid':slot['episode_uid'],'complete':True}))
 root=tmp_path/'queue'
 with rendition.RenditionQueue(root,p,validator=validator) as q:q.run(worker,uids=['ep0']);assert q.accepted()==1
 with rendition.RenditionQueue(root,p,validator=validator) as q:q.run(worker,uids=['ep0']);assert q.accepted()==1
 assert calls==[1,2]
 (root/'episodes/ep0/payload.json').unlink()
 with rendition.RenditionQueue(root,p,validator=validator) as q:
  q.run(worker,uids=['ep0']);assert q.accepted()==1 and q.state['physical_executions']==0
 assert calls==[1,2,3]


def test_integrity_failure_is_fail_closed_without_render_retries(tmp_path,monkeypatch):
 p=profile_file(tmp_path);monkeypatch.setattr(rendition,'validate_slot_inputs',lambda *_:None);calls=[]
 def worker(*_):calls.append(1);raise rendition.RecordingIntegrityError('Wrong source/scene')
 with rendition.RenditionQueue(tmp_path/'queue',p,validator=lambda _:None) as q:
  with pytest.raises(rendition.RecordingIntegrityError):q.run(worker,uids=['ep0'])
 assert calls==[1]


def test_render_retry_budget_survives_restart(tmp_path,monkeypatch):
 p=profile_file(tmp_path);monkeypatch.setattr(rendition,'validate_slot_inputs',lambda *_:None);calls=[]
 def worker(*_):calls.append(1);raise RuntimeError('Encoder failed')
 for _ in range(2):
  with rendition.RenditionQueue(tmp_path/'queue',p,validator=lambda _:None) as q:
   with pytest.raises(RuntimeError,match='budget'):q.run(worker,uids=['ep0'])
 assert len(calls)==3


def test_actual_retained_trace_quality_and_physical_identity():
 root=ROOT/'data/qlm_bench/automated-push-pilot-20261013-v1/traces'
 if not root.exists():pytest.skip('Actual retained trace fixture not supplied')
 files=list(root.glob('*/manifest.json'));assert len(files)==10
 audits=[rendition.audit_trace(p.parent) for p in files]
 assert len({a['trajectory_sha256'] for a in audits})==10
 assert all(a['quality']['full_footprint_three_ticks'] and a['quality']['body_contact_boundaries']==0 for a in audits)


def test_evidence_profile_requires_both_user_approvals_and_actual_review(tmp_path):
 p=profile_file(tmp_path);profile=load_profile(p);profile.pop('profile_sha256')
 profile['quality_policy']='evidence-review-v1'
 def save():
  profile.pop('profile_sha256',None);profile['profile_sha256']=digest(profile);p.write_text(json.dumps(profile))
 save()
 with pytest.raises(ValueError,match='approval required'):load_profile(p)
 for slot in profile['slots']:slot['appearance_preset']='ap_00' if slot['difficulty']=='clean' else 'ap_01'
 profile['approval']={'reference_quality_approved':True,'retarget_scope_approved':True,'evidence_sha256':{'review':'abc'}}
 save()
 with pytest.raises(ValueError,match='behavior evidence'):load_profile(p)
 for slot in profile['slots']:
  slot.update(review_status='eligible_for_ten_pilot_user_review',quality_review_sha256='actual-evidence',
              quality={'fl_contact_boundaries':0,'body_contact_boundaries':0,'full_footprint_three_ticks':True,'not_fallen':True})
 save()
 assert load_profile(p)['quality_policy']=='evidence-review-v1'  # Unknown contact is not automatic rejection.
 profile['approval']['retarget_scope_approved']=False;save()
 with pytest.raises(ValueError,match='approval required'):load_profile(p)


def test_evidence_clean_rejects_ap01_without_changing_legacy_admission(tmp_path):
 p=profile_file(tmp_path);profile=load_profile(p);profile.pop('profile_sha256')
 profile.update(quality_policy='evidence-review-v1',approval={'reference_quality_approved':True,'retarget_scope_approved':True,'evidence_sha256':{'review':'abc'}})
 for slot in profile['slots']:slot.update(appearance_preset='ap_01',review_status='eligible_for_ten_pilot_user_review',quality_review_sha256='evidence')
 profile['profile_sha256']=digest(profile);p.write_text(json.dumps(profile))
 with pytest.raises(ValueError,match='Clean pilot requires ap_00'):load_profile(p)
 profile.pop('profile_sha256');profile.pop('quality_policy');profile['profile_sha256']=digest(profile);p.write_text(json.dumps(profile))
 assert load_profile(p)  # Old immutable profiles retain their historical rules.
