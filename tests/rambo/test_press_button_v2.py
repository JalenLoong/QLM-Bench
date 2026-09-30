import numpy as np
import pytest
from rambo.tasks.common.press_button_logic import PressSuccessHold
from rambo.dataset_v2.task_state import goal_position,task_values
from rambo.tasks.common.push_box_geometry import PolicySuccessHold


def test_press_requires_three_unique_consecutive_policy_boundaries():
    h=PressSuccessHold()
    assert not h.update(10,.012,True)
    assert not h.update(10,.012,True)
    assert not h.update(15,.02,True)
    assert not h.update(20,.012,True)
    assert h.update(30,.012,True)
    assert not h.update(35,.02,False)


def test_drop_gap_reset_and_below_threshold():
    h=PressSuccessHold()
    assert not h.update(10,.011999,True)
    assert not h.update(20,.02,True)
    assert not h.update(40,.02,True)
    assert h.count==1
    assert not h.update(50,0.,True)
    assert h.count==0
    h.reset();assert h.first_pressed_ns is None and h.last_tick is None
    with pytest.raises(ValueError):h.update(10,float('nan'),True)


def test_button_goal_and_progress_are_axial_metres():
    p={'task_profile_version':'press-button-v2-1','button_rest_front_xyz':[.56,.10,.30],
       'press_axis_world':[1.,0.,0.],'success_displacement_m':.012}
    assert np.allclose(goal_position(p),[.572,.10,.30])
    s=task_values(p,[.575,.10,.30],0.)
    assert s['task.progress'][0]==pytest.approx(.015)
    assert task_values(p,[.56,.20,.40],0.)['task.progress']==[0.]


def test_existing_push_box_mapping_and_hold_unchanged():
    p={'task_profile_version':'push-box-v2-2','goal_x':[.95,1.35],'goal_y':[-.10,.40]}
    center=np.array([1.12,.2,.15],dtype=np.float32)
    assert task_values(p,center,.69)=={'task.goal.position':[sum(p['goal_x'])/2,sum(p['goal_y'])/2,0.],
                                    'task.progress':[float(center[0])-.69]}
    h=PolicySuccessHold();assert not h.update(10,True,True);assert not h.update(20,True,True);assert h.update(30,True,True)


def test_press_unknown_contact_sidecar_is_required(tmp_path):
    import json
    from rambo.dataset_v2.validation import _task_contact_diagnostics,file_hash,ContractError
    ext={'task_profile_version':'press-button-v2-1'}
    with pytest.raises(ContractError):_task_contact_diagnostics(tmp_path,{'extensions':ext},1)
    rows=[dict(simulation_time_ns=i*20_000_000,valid=False,status='unknown',fl_object=None,body_object=None,reason='pair unavailable') for i in range(2)]
    data=dict(role='diagnostic_only',unavailable='unknown',bool_columns_are_invalid_placeholders=True,rows=rows)
    side=tmp_path/'contact.json';side.write_text(json.dumps(data));ext['contact_diagnostics']={'path':side.name,'sha256':file_hash(side)}
    _task_contact_diagnostics(tmp_path,{'extensions':ext},1)
    rows[0]['fl_object']=False;side.write_text(json.dumps(data));ext['contact_diagnostics']['sha256']=file_hash(side)
    with pytest.raises(ContractError):_task_contact_diagnostics(tmp_path,{'extensions':ext},1)
