from collections import Counter
from pathlib import Path
import json
import numpy as np
from rambo.tasks.common.push_box_scaleup_plan import resolve_case
from rambo.tasks.common.push_box_geometry import source_geometry,world_geometry,fully_inside,PolicySuccessHold


def base_profile():
    root=Path(__file__).resolve().parents[2]
    return json.loads((root/'configs/collection/push_box.json').read_text())


def test_case_geometry_face_floor_goal_and_determinism():
    low=np.array([-.15,-.10,-.08]);high=np.array([.15,.10,.14])
    for yaw in [0,90,180,270]:
        case=resolve_case(base_profile(),low=low,high=high,seed=42,clean=False,recovery=True,yaw_deg=yaw)
        assert case==resolve_case(base_profile(),low=low,high=high,seed=42,clean=False,recovery=True,yaw_deg=yaw)
        geometry=world_geometry(source_geometry(low,high,face=case['selected_face']),case['position']+case['orientation'])
        assert geometry['face_normal'][0]<-.99
        assert abs(min(np.asarray(source_geometry(low,high)['corners'])@np.asarray([[1,0,0],[0,1,0],[0,0,1]])[:,2])+case['position'][2]-.02)<1e-7
        assert not fully_inside(geometry['footprint_xy'],case['profile']['goal_x'],case['profile']['goal_y'])
        assert case['profile']['success_policy_ticks']==3


def test_original_success_requires_complete_footprint_and_three_ticks():
    hold=PolicySuccessHold(3)
    footprint=[[0.95,-.1],[1.1,-.1],[1.1,.1],[.95,.1]]
    assert fully_inside(footprint,[.95,1.35],[-.1,.4])
    assert not hold.update(10,True,True)
    assert not hold.update(20,True,True)
    assert hold.update(30,True,True)
    assert not fully_inside([[.94,0],[1.1,0],[1.1,.1],[.94,.1]],[.95,1.35],[-.1,.4])
