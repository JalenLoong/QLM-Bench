"""Lift admission uses whole geometry, not a high center or a claimed progress."""
import itertools
import json

import numpy as np
import pytest

from qlm_bench.backends.mujoco import rendition
from qlm_bench.compatibility.dataset_v2.pilot_rendition import LIFT_SCHEMA,PRESS_SCHEMA,load_profile
from qlm_bench.compatibility.dataset_v2.validation import digest


def profile(tmp_path,task='lift_basket',schema=LIFT_SCHEMA):
    d={'schema':schema,'task_id':task,'rgb_profile':'dual-rgb-360p-v1','pilot_target':10,
        'pilot_campaign_sha256':'campaign','maximum_render_attempts':3,'quality_policy':'evidence-review-v1',
        'approval':{'reference_quality_approved':True,'retarget_scope_approved':True,'evidence_sha256':'review'},
        'slots':[{'episode_uid':'lift01','rendition_id':'lift01@360p','physical_trajectory_sha256':'physical',
            'task_id':task,'difficulty':'clean','split':'train','appearance_preset':'ap_00',
            'review_status':'eligible_for_ten_pilot_user_review','quality_review_sha256':'behavior'}]}
    d['profile_sha256']=digest(d);p=tmp_path/'profile.json';p.write_text(json.dumps(d));return p


def fixture(tmp_path,monkeypatch):
    (tmp_path/'manifest.json').write_text('{}')
    vertices=list(itertools.product((-.1,.1),(-.1,.1),(-.1,.1)))
    m={'profile':{'task_id':'lift_basket','minimum_clearance_m':.02,'floor_z_m':0.,'success_hold_commands':3,
        'success_enable_after_s':2.1,'support_vertices_local':vertices},'terminal_before_reset':True,
        'quality_policy':'evidence-review-v1','quality':{'fl_contact_boundaries':0,'body_contact_boundaries':0},
        'model_identity':'real-model','batch_identity':{},'n_actions':2,'n_boundaries':3,'scene':{}}
    arrays={'qpos':np.zeros((3,7)),'qvel':np.zeros((3,6)),
        'simulation_time_ns':np.array([2_100_000_000,2_120_000_000,2_140_000_000],np.int64)}
    b=[{'state':{'task.object.position':[0.,0.,.123],'task.object.orientation':[0.,0.,0.,1.],
        'task.progress':[.023],'observation.state.base.position':[0.,0.,.3],
        'observation.state.projected_gravity':[0.,0.,-1.]},'contact':{'status':'unknown'}} for _ in range(3)]
    terminal={'success':True,'fallen':False};commands=[{'executed':[0.]*9} for _ in range(2)]
    monkeypatch.setattr(rendition,'verify_trace',lambda _:(m,arrays,{'boundaries':b},commands,terminal))
    return m,arrays,b,terminal


def test_lift_schema_requires_its_own_task_and_approved_campaign(tmp_path):
    assert load_profile(profile(tmp_path))['task_id']=='lift_basket'
    with pytest.raises(ValueError,match='membership'):load_profile(profile(tmp_path,'press_button'))
    with pytest.raises(ValueError,match='membership'):load_profile(profile(tmp_path,'lift_basket',PRESS_SCHEMA))


def test_whole_basket_clearance_and_unknown_foot_contact(tmp_path,monkeypatch):
    fixture(tmp_path,monkeypatch);a=rendition.audit_trace(tmp_path)
    assert a['quality']['whole_basket_clearance_three_ticks'] is True
    assert a['quality']['fl_contact_boundaries']==0
    assert 'full_footprint_three_ticks' not in a['quality']


@pytest.mark.parametrize('error',['low_bottom','tilted_corner','false_progress','early','gap','changed_threshold','fallen','false_terminal'])
def test_rejects_false_lift_or_changed_contract(tmp_path,monkeypatch,error):
    m,arr,b,t=fixture(tmp_path,monkeypatch)
    if error=='low_bottom':
        b[0]['state']['task.object.position'][2]=.119;b[0]['state']['task.progress']=[.019]
    if error=='tilted_corner':
        b[0]['state']['task.object.orientation']=[np.sin(.1),0,0,np.cos(.1)]
    if error=='false_progress':b[0]['state']['task.progress']=[.05]
    if error=='early':arr['simulation_time_ns']-=2_100_000_000
    if error=='gap':arr['simulation_time_ns'][-1]+=20_000_000
    if error=='changed_threshold':m['profile']['minimum_clearance_m']=.005
    if error=='fallen':b[-1]['state']['observation.state.base.position'][2]=.05
    if error=='false_terminal':t['success']=False
    with pytest.raises(rendition.RecordingIntegrityError):rendition.audit_trace(tmp_path)
