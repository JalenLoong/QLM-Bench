"""Press100 preserves task support, split hygiene and fail-closed rendering."""
import json
from pathlib import Path
import numpy as np
import pytest
from qlm_bench.backends.mujoco.press_production import configuration_candidates,NOMINAL,LIMITS,CLEAN_LIMITS,NEAR,QUOTAS,translate_press
from qlm_bench.compatibility.dataset_v2.pilot_rendition import PRESS_PRODUCTION_SCHEMA,load_profile
from qlm_bench.compatibility.dataset_v2.validation import digest


def pilots():
    points=[(.103,.301),(.097,.299),(.07,.28),(.07,.32),(.13,.28),(.13,.32),(.085,.315),(.115,.285),(.079,.30),(.121,.30)]
    return [{'parameters':list(p),'split':'train','difficulty':'clean' if i<2 else 'randomized','appearance_preset':'ap_00' if i<2 or i%2==0 else 'ap_01'} for i,p in enumerate(points)]


def test_press_same_ID_quotas_and_all_retry_cross_split_dedup():
    old=pilots();rows=configuration_candidates(old);assert rows==configuration_candidates(old)
    assert len(rows)==90;prior=[(np.array(s['parameters']),s['split']) for s in old]
    quotas={s:{d:0 for d in ('clean','randomized')} for s in QUOTAS}
    for s in old+rows:quotas[s['split']][s['difficulty']]+=1
    assert quotas==QUOTAS
    for row in rows:
        limit=CLEAN_LIMITS if row['difficulty']=='clean' else LIMITS
        if row['difficulty']=='clean':assert row['appearance_preset']=='ap_00'
        for c in row['candidates']:
            yz=np.array(c['configuration_parameters']);assert np.all(np.abs(yz-NOMINAL)<=limit+1e-12)
            assert all(not np.all(np.abs(yz-p)<=NEAR) for p,split in prior if split!=row['split'])
            prior.append((yz,row['split']))
    for split in QUOTAS:
        assert {s['geometry_bin'] for s in rows if s['split']==split and s['difficulty']=='randomized'}=={'++','+-','-+','--'}
        for quadrant in ('++','+-','-+','--'):
            assert {s['appearance_preset'] for s in rows if s['split']==split and s['geometry_bin']==quadrant}=={'ap_00','ap_01'}


@pytest.mark.parametrize('split',['train','validation','test'])
def test_press_production_needs_pilot_approval_and_explicit_split(tmp_path,split):
    p={'schema':PRESS_PRODUCTION_SCHEMA,'task_id':'press_button','rgb_profile':'dual-rgb-360p-v1','maximum_render_attempts':3,
       'campaign_sha256':'frozen','production_authorization':{'pilot_approved':True,'target_accepted':100},'quality_policy':'evidence-review-v1',
       'approval':{'reference_quality_approved':True,'retarget_scope_approved':True,'evidence_sha256':{'proof':'approved'}},
       'slots':[{'episode_uid':'press','task_id':'press_button','split':split,'difficulty':'clean','appearance_preset':'ap_00',
                 'rendition_id':'record','physical_trajectory_sha256':'actual','quality_review_sha256':'actual-behavior','review_status':'approved_task_recipe_technical_quality'}]}
    def save():
        p.pop('profile_sha256',None);p['profile_sha256']=digest(p);path=tmp_path/'profile.json';path.write_text(json.dumps(p));return path
    assert load_profile(save())['slots'][0]['split']==split
    p['production_authorization']['pilot_approved']=False
    with pytest.raises(ValueError,match='Approved100'):load_profile(save())


def test_wall_translation_preserves_qualified_robot_physics_and_source_bytes(tmp_path):
    root=Path(__file__).resolve().parents[4];source=root/'assets/mujoco/press-full-wall-a-v1/scene.xml'
    if not source.is_file():pytest.skip('Qualified local wall resource not provided')
    from qlm_bench.backends.mujoco.resources import resource_closure
    old=resource_closure(source,require_portable=True)['identity']
    new=translate_press(source,tmp_path/'variant',.083,.313)
    assert new['portable'] and new['identity']!=old
    assert resource_closure(source,require_portable=True)['identity']==old
    profile=json.loads((tmp_path/'variant/scene.task.json').read_text())
    assert profile['button_rest_front_xyz'][1:]==[.083,.313]
    assert profile['threshold_m']==.012 and profile['environment_profile']['installation_depth_randomized'] is False


def fake_queue(tmp_path,monkeypatch):
    from qlm_bench.backends.mujoco import press_production as module
    p={'profile_sha256':'frozen','slots':[{'episode_uid':str(i),'candidates':[{'candidate_id':f'{i}-{j}'} for j in range(5)]} for i in range(90)]}
    monkeypatch.setattr(module,'load_campaign',lambda *_:p)
    q=module.PressProductionQueue(tmp_path/'queue',tmp_path/'campaign',tmp_path)
    q.reconcile=lambda:None;q.retain=lambda s,r:r.update(status='render_pending',trajectory_sha256=s['episode_uid'])
    return q,module


def test_four_independent_physics_and_four_render_bounded_retries(tmp_path,monkeypatch):
    import threading,time
    q,module=fake_queue(tmp_path,monkeypatch)
    monkeypatch.setattr(module,'memory',lambda:{'available':100*1024**3,'swap_used':0})
    counts={'physics':0,'render':0};maxima=counts.copy();calls=[];lock=threading.Lock()
    def job(stage,uid):
        with lock:counts[stage]+=1;maxima[stage]=max(maxima[stage],counts[stage]);calls.append((stage,uid))
        time.sleep(.02)
        with lock:counts[stage]-=1
        return {'passed':not(stage=='physics' and uid=='0-0')}
    q.physics_job=lambda scene,trace:job('physics',scene['candidate_id']);q.render_job=lambda uid:job('render',uid)
    q.run_parallel(4,4)
    assert q.accepted()==100 and maxima=={'physics':4,'render':4}
    assert sum(stage=='physics' for stage,_ in calls)==91 and q.state['slots']['0']['physical_attempts']==2
    assert not any('WAM' in stage for stage,_ in calls)


def test_resource_guard_preserves_pending_success_and_stops_new_physics(tmp_path,monkeypatch):
    import time
    q,module=fake_queue(tmp_path,monkeypatch);calls=[];reads=[]
    def memory():
        reads.append(1);return {'available':100*1024**3 if len(reads)<=2 else 1024**3,'swap_used':0}
    monkeypatch.setattr(module,'memory',memory)
    def physical(scene,trace):calls.append(scene['candidate_id']);time.sleep(.02);return {'passed':True}
    q.physics_job=physical;q.render_job=lambda _:pytest.fail('No RAM admission for rendering')
    q.run_parallel(4,4)
    assert len(calls)==4 and q.state['status']=='resource_pressure_drained'
    assert sum(r['status']=='render_pending' for r in q.state['slots'].values())==4
