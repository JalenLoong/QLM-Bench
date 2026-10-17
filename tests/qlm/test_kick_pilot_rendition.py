"""Formal Kick must replay a forward whole-sphere entry, not just a terminal point."""
import json
import numpy as np
import pytest
from qlm_bench.backends.mujoco import rendition
from qlm_bench.compatibility.dataset_v2.pilot_rendition import KICK_SCHEMA,LIFT_SCHEMA,load_profile
from qlm_bench.compatibility.dataset_v2.validation import digest


def profile(tmp_path,task='kick_ball_to_goal',schema=KICK_SCHEMA):
    d={'schema':schema,'task_id':task,'rgb_profile':'dual-rgb-360p-v1','pilot_target':10,'pilot_campaign_sha256':'campaign','maximum_render_attempts':3,'quality_policy':'evidence-review-v1','approval':{'reference_quality_approved':True,'retarget_scope_approved':True,'evidence_sha256':'review'},'slots':[{'episode_uid':'kick01','rendition_id':'kick01@360p','physical_trajectory_sha256':'trajectory','task_id':task,'difficulty':'clean','split':'train','appearance_preset':'ap_00','review_status':'eligible_for_ten_pilot_user_review','quality_review_sha256':'behavior'}]}
    d['profile_sha256']=digest(d);p=tmp_path/'profile.json';p.write_text(json.dumps(d));return p


def fixture(tmp_path,monkeypatch,positions=None):
    positions=positions or [[-.3,0,.1],[-.05,0,.1],[.11,0,.1],[.12,0,.1],[.13,0,.1]]
    (tmp_path/'manifest.json').write_text('{}');n=len(positions)
    goal={'front_center_xyz_m':[0,0,0],'width_m':.8,'height_m':.45,'depth_m':.4}
    m={'profile':{'task_id':'kick_ball_to_goal','ball_radius_m':.1,'goal_geometry':goal,'success_hold_commands':3},'terminal_before_reset':True,'quality_policy':'evidence-review-v1','quality':{'fl_contact_boundaries':0,'body_contact_boundaries':0},'model_identity':'actual-model','batch_identity':{},'n_actions':n-1,'n_boundaries':n,'scene':{}}
    arr={'qpos':np.zeros((n,7)),'qvel':np.zeros((n,6)),'simulation_time_ns':np.arange(n)*20_000_000}
    boundaries=[{'state':{'task.object.position':p,'observation.state.base.position':[0,0,.3],'observation.state.projected_gravity':[0,0,-1]},'contact':{'status':'unknown'}} for p in positions]
    terminal={'success':True,'fallen':False};commands=[{'executed':[0.]*9} for _ in range(n-1)]
    monkeypatch.setattr(rendition,'verify_trace',lambda _:(m,arr,{'boundaries':boundaries},commands,terminal));return m,arr,boundaries,terminal


def test_kick_explicit_task_schema(tmp_path):
    assert load_profile(profile(tmp_path))['task_id']=='kick_ball_to_goal'
    for task,schema in [('lift_basket',KICK_SCHEMA),('kick_ball_to_goal',LIFT_SCHEMA)]:
        with pytest.raises(ValueError,match='membership'):load_profile(profile(tmp_path,task,schema))


def test_actual_forward_goal_and_unknown_contact(tmp_path,monkeypatch):
    fixture(tmp_path,monkeypatch);report=rendition.audit_trace(tmp_path)
    assert report['quality']['front_whole_ball_goal_three_ticks']
    assert report['quality']['fl_contact_boundaries']==0
    assert 'whole_basket_clearance_three_ticks' not in report['quality']


@pytest.mark.parametrize('error',['initial_inside','side','not_whole','fallen','gap','false_terminal','changed_radius','changed_hold'])
def test_reject_invalid_entry_or_changed_contract(tmp_path,monkeypatch,error):
    positions={'initial_inside':[[.11,0,.1]]*5,'side':[[-.3,.7,.1],[.05,.7,.1],[.11,0,.1],[.12,0,.1],[.13,0,.1]],'not_whole':[[-.3,0,.1],[-.05,0,.1],[.09,0,.1],[.12,0,.1],[.13,0,.1]]}.get(error)
    m,a,b,t=fixture(tmp_path,monkeypatch,positions)
    if error=='fallen':b[-1]['state']['observation.state.base.position'][2]=.05
    if error=='gap':a['simulation_time_ns'][-1]+=20_000_000
    if error=='false_terminal':t['success']=False
    if error=='changed_radius':m['profile']['ball_radius_m']=.01
    if error=='changed_hold':m['profile']['success_hold_commands']=1
    with pytest.raises(rendition.RecordingIntegrityError):rendition.audit_trace(tmp_path)
