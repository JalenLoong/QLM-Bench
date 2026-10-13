"""Regress task-state against the original Isaac contract, without a rollout."""
from types import SimpleNamespace

import mujoco
import numpy as np
import pytest
import torch

from qlm_bench.backends.mujoco.tasks import TaskState
from qlm_bench.compatibility.dataset_v2.task_state import task_values


def fixture():
    model=mujoco.MjModel.from_xml_string('''<mujoco><worldbody>
      <body name="primary" pos="0.69 .14 .13"><freejoint/>
        <geom type="box" size=".15 .087 .113" mass=".207"/>
      </body></worldbody></mujoco>''')
    data=[mujoco.MjData(model) for _ in range(2)]
    for d in data:mujoco.mj_forward(model,d)
    physics=SimpleNamespace(model=model,data=data,count=2,ticks=np.zeros(2,dtype=int))
    profile=dict(task_id='push_box',half_extent=[.15,.087,.113],goal_x=[.95,1.35],
                 goal_y=[-.1,.4],horizon_s=24.)
    core=SimpleNamespace(base_height=torch.tensor([.3,.3]),
                         projected_gravity_b=torch.tensor([[0.,0.,-1.],[0.,0.,-1.]]))
    return physics,profile,core


def test_progress_uses_reset_displacement_not_goal_margin():
    physics,profile,core=fixture();task=TaskState(physics,profile)
    initial=float(physics.data[0].qpos[0])
    assert task.progress(0)==0
    for dx in (0.,.02,-.03,.18):
        # A geometry fixture, not a teleported expert trajectory.
        d=physics.data[0];d.qpos[0]=initial+dx
        d.qpos[3:7]=[np.cos(.3),0,0,np.sin(.3)]
        mujoco.mj_forward(physics.model,d)
        expected=task_values(profile,d.xpos[task.body],initial)['task.progress'][0]
        physics.ticks[0]+=10
        assert task.evaluate(0,core)['progress']==pytest.approx(expected,abs=1e-12)
        assert task.progress(0)==pytest.approx(dx,abs=1e-12)
    profile['goal_x']=[2.,3.]
    assert task.progress(0)==pytest.approx(.18)


def test_reset_reanchors_only_selected_world():
    physics,profile,core=fixture();task=TaskState(physics,profile)
    for i,dx in enumerate((.12,.2)):
        physics.data[i].qpos[0]+=dx;mujoco.mj_forward(physics.model,physics.data[i])
    task.reset([0])
    assert task.progress(0)==0
    assert task.progress(1)==pytest.approx(.2)
    physics.data[0].qpos[0]+=.04;mujoco.mj_forward(physics.model,physics.data[0])
    assert task.progress(0)==pytest.approx(.04)


def test_original_asset_origin_is_not_its_geometric_center():
    physics,profile,core=fixture()
    profile.update(bounds_local=[[-.14,-.16,-.08],[.16,.02,.15]],center_local=[.01,-.07,.035])
    task=TaskState(physics,profile);initial_center=task.geometric_center(0).copy()
    data=physics.data[0]
    # Rotate a source-origin-offset object without translating its rigid root.
    data.qpos[3:7]=[np.sqrt(.5),0.,0.,np.sqrt(.5)]
    mujoco.mj_forward(physics.model,data)
    expected_center=data.xpos[task.body]+np.array([.07,.01,.035])
    np.testing.assert_allclose(task.geometric_center(0),expected_center,atol=1e-12)
    assert task.progress(0)==pytest.approx(.06,abs=1e-12)
    assert task.evaluate(0,core)['progress']==pytest.approx(expected_center[0]-initial_center[0],abs=1e-12)
    task.reset([0]);assert task.progress(0)==0


def test_repeated_read_and_partial_ticks_do_not_satisfy_success_hold():
    physics,profile,core=fixture();task=TaskState(physics,profile)
    physics.data[0].qpos[0]=1.15;mujoco.mj_forward(physics.model,physics.data[0])
    for tick in (10,10,10,15,20):
        physics.ticks[0]=tick
        assert not task.evaluate(0,core)['success']
    physics.ticks[0]=30
    assert task.evaluate(0,core)['success']
    task.reset([0]);physics.ticks[0]=40
    assert not task.evaluate(0,core)['success']
    physics.ticks[0]=60
    assert not task.evaluate(0,core)['success']
    assert task.hold[0]==1
