"""Kick100 whole-episode quotas, identical split support and fail-closed authorization."""
import itertools,json
import numpy as np
import pytest
from qlm_bench.backends.mujoco.kick_production import configuration_candidates,NEAR,LIMITS,CLEAN_LIMITS,QUOTAS
from qlm_bench.compatibility.dataset_v2.pilot_rendition import KICK_PRODUCTION_SCHEMA,KICK_SCHEMA,load_profile
from qlm_bench.compatibility.dataset_v2.validation import digest


def pilots():
    rows=[[.003,-.003,.008,-.005],[-.003,.003,-.008,.005]]+[[a*.03,b*.03,c*.08,a*b*c*.05] for a,b,c in itertools.product([-1,1],repeat=3)]
    return [{'parameters':p,'split':'train','difficulty':'clean' if i<2 else 'randomized'} for i,p in enumerate(rows)]


def test_same_ID_support_quota_and_all_retry_dedup():
    old=pilots();slots=configuration_candidates(old);assert len(slots)==90
    assert [s['difficulty'] for s in slots[:2]]==['clean','randomized'] and slots[1]['appearance_preset']=='ap_01'
    counts={split:{d:0 for d in ('clean','randomized')} for split in QUOTAS};prior=[(np.array(s['parameters']),s['split']) for s in old]
    for s in old+slots:counts[s['split']][s['difficulty']]+=1
    assert counts==QUOTAS
    for s in slots:
        for c in s['candidates']:
            point=np.array(c['configuration_parameters']);assert len(point)==4
            assert np.all(np.abs(point)<=(CLEAN_LIMITS if s['difficulty']=='clean' else LIMITS))
            assert all(not np.all(np.abs(point-p)<=NEAR) for p,other in prior if other!=s['split'])
            assert all(not np.array_equal(point,p) for p,_ in prior)
            prior.append((point,s['split']))
    # Every split spans both sides of each full-support axis; no split owns a variable interval.
    for split in QUOTAS:
        points=np.array([s['candidates'][0]['configuration_parameters'] for s in slots if s['split']==split and s['difficulty']=='randomized'])
        assert np.all(points.min(0)<0) and np.all(points.max(0)>0)


@pytest.mark.parametrize('split',['train','validation','test'])
def test_kick_production_requires_explicit100_approval(tmp_path,split):
    p={'schema':KICK_PRODUCTION_SCHEMA,'task_id':'kick_ball_to_goal','rgb_profile':'dual-rgb-360p-v1','maximum_render_attempts':3,'campaign_sha256':'fixed','production_authorization':{'pilot_approved':True,'target_accepted':100},'quality_policy':'evidence-review-v1','approval':{'reference_quality_approved':True,'retarget_scope_approved':True,'evidence_sha256':'approval'},'slots':[{'episode_uid':'kick','task_id':'kick_ball_to_goal','split':split,'difficulty':'clean','appearance_preset':'ap_00','rendition_id':'new','physical_trajectory_sha256':'physical','quality_review_sha256':'quality','review_status':'approved_task_recipe_technical_quality'}]}
    def save():
        p.pop('profile_sha256',None);p['profile_sha256']=digest(p);f=tmp_path/'profile.json';f.write_text(json.dumps(p));return f
    assert load_profile(save())['slots'][0]['split']==split
    p['production_authorization']['pilot_approved']=False
    with pytest.raises(ValueError,match='Approved100'):load_profile(save())
