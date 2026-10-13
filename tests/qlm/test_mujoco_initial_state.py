"""Validate all reset lanes before mutation; actual reconstruction is a runtime gate."""
from types import SimpleNamespace
import numpy as np
import pytest
import mujoco
from qlm_bench.backends.mujoco.physics import MuJoCoPhysics


def validator():
    value=MuJoCoPhysics.__new__(MuJoCoPhysics);value.model_identity='a'*64
    value.model=SimpleNamespace(nq=8,nv=7,njnt=2,
        jnt_type=np.array([mujoco.mjtJoint.mjJNT_FREE,mujoco.mjtJoint.mjJNT_HINGE]),
        jnt_qposadr=np.array([0,7]),jnt_limited=np.array([False,True]),
        jnt_range=np.array([[0,0],[-.4,1.2]]))
    return value


def state():
    return {'schema':'qlm-mujoco-initial-state-v1','model_identity':'a'*64,
            'qpos':[0,0,.4,1,0,0,0,.2],'qvel':[0]*7}


def test_validated_arrays_are_owned_and_all_lanes_are_required():
    value=validator();s=state();result=value.validate_initial_states([0,1],{0:s,1:s})
    result[0][0][0]=5
    assert s['qpos'][0]==0 and result[1][0][0]==0
    with pytest.raises(ValueError):value.validate_initial_states([0,1],{0:s})
    with pytest.raises(ValueError):value.validate_initial_states([],{0:s})
    with pytest.raises(ValueError):value.validate_initial_states([1],{True:s})


@pytest.mark.parametrize('change',[{'model_identity':'wrong'}, {'schema':'wrong'},
    {'qpos':[0]*8},{'qvel':[float('nan')]*7}, {'qpos':[0,0,.4,1,0,0,0,2]}, {'qvel':[0]*6}])
def test_invalid_descriptors_cannot_enter_reset(change):
    s=state();s.update(change)
    with pytest.raises(ValueError):validator().validate_initial_states([0],{0:s})
