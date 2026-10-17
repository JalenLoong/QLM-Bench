"""Native source admission, Lift100 split hygiene and retained legacy compatibility."""
import gzip
import json
import itertools

import numpy as np
import pytest

from qlm_bench.backends.mujoco.lift_production import configuration_candidates,NEAR,LIMITS,CLEAN_LIMITS,QUOTAS
from qlm_bench.backends.mujoco.trace import verify_trace,sha
from qlm_bench.compatibility.dataset_v2.pilot_rendition import LIFT_PRODUCTION_SCHEMA,load_profile
from qlm_bench.compatibility.dataset_v2.validation import digest


def pilots():
    points=[(.003,-.003,.3),(-.003,.003,-.3)]+list(itertools.product((-.03,.03),(-.03,.03),(-5,5)))
    return [{'parameters':list(p),'split':'train','difficulty':'clean' if i<2 else 'randomized','appearance_preset':'ap_00'} for i,p in enumerate(points)]


def test_same_ID_support_quotas_and_every_retry_cross_split_dedup():
    old=pilots();rows=configuration_candidates(old);assert rows==configuration_candidates(old) and len(rows)==90
    assert rows[0]['difficulty']=='clean' and rows[1]['difficulty']=='randomized' and rows[1]['appearance_preset']=='ap_01'
    prior=[(np.asarray(s['parameters']),s['split']) for s in old];counts={s:{d:0 for d in ('clean','randomized')} for s in QUOTAS}
    for s in old+rows:counts[s['split']][s['difficulty']]+=1
    assert counts==QUOTAS
    for s in rows:
        for c in s['candidates']:
            point=np.asarray(c['configuration_parameters']);limit=CLEAN_LIMITS if s['difficulty']=='clean' else LIMITS
            assert np.all(np.abs(point)<=limit)
            assert all(not np.all(np.abs(point-p)<=NEAR) for p,split in prior if split!=s['split'])
            prior.append((point,s['split']))
    for split in QUOTAS:
        assert len({s['geometry_bin'] for s in rows if s['split']==split and s['difficulty']=='randomized'})==8


def trace_fixture(tmp_path,backend='mjwarp'):
    n=2
    np.savez(tmp_path/'render_snapshots.npz',qpos=np.zeros((3,7)),qvel=np.zeros((3,6)),time=np.arange(3)*.02,
        physics_step=np.arange(3)*10,simulation_time_ns=np.arange(3)*20_000_000)
    (tmp_path/'commands.jsonl').write_text('\n'.join(json.dumps({'status':'completed','start_tick':i*10,'end_tick':(i+1)*10,'executed':[0.]*9}) for i in range(n)))
    with gzip.open(tmp_path/'telemetry.json.gz','wt') as f:json.dump({'boundaries':[{}]*3,'physics':[{}]*21,'controller':[{}]*4},f)
    (tmp_path/'terminal.json').write_text(json.dumps({'success':True,'fallen':False,'partial_interval':False,'physics_step':20}))
    m={'schema':'qlm-physical-trace-v1','passed':True,'n_actions':2,'n_boundaries':3,'backend':{'physics':backend},'batch_identity':{},
       'files':{p.name:sha(p) for p in tmp_path.iterdir()}}
    return m


def test_legacy_cuda_accepted_and_native_requires_explicit_profile(tmp_path):
    m=trace_fixture(tmp_path)
    def save():
        (tmp_path/'manifest.json').write_text(json.dumps(m));return tmp_path
    verify_trace(save())
    m['backend']['physics']='native'
    with pytest.raises(ValueError,match='qualified Native'):verify_trace(save())
    m['batch_identity']['native_trace_profile']='native-cpu-original-rambo-v1'
    m['backend'].update(controller_device='cpu',effective_physics_options={'device':'cpu','backend':'native','precision':'float64'})
    verify_trace(save())
    m['backend']['controller_device']='cuda:0'
    with pytest.raises(ValueError,match='qualified Native'):verify_trace(save())
    m['backend']['physics']='unknown'
    with pytest.raises(ValueError,match='Unknown physical'):verify_trace(save())


@pytest.mark.parametrize('split',['train','validation','test'])
def test_lift_production_retains_approval_and_split_gate(tmp_path,split):
    p={'schema':LIFT_PRODUCTION_SCHEMA,'task_id':'lift_basket','rgb_profile':'dual-rgb-360p-v1','maximum_render_attempts':3,
       'campaign_sha256':'fixed','production_authorization':{'pilot_approved':True,'target_accepted':100},'quality_policy':'evidence-review-v1',
       'approval':{'reference_quality_approved':True,'retarget_scope_approved':True,'evidence_sha256':'approved'},
       'slots':[{'episode_uid':'lift','task_id':'lift_basket','split':split,'difficulty':'clean','appearance_preset':'ap_00',
          'rendition_id':'rendition','physical_trajectory_sha256':'physical','quality_review_sha256':'quality','review_status':'approved_task_recipe_technical_quality'}]}
    def save():
        p.pop('profile_sha256',None);p['profile_sha256']=digest(p);f=tmp_path/'profile.json';f.write_text(json.dumps(p));return f
    assert load_profile(save())['slots'][0]['split']==split
    p['production_authorization']['pilot_approved']=False
    with pytest.raises(ValueError,match='Approved100'):load_profile(save())
