import numpy as np
import pytest
from qlm_bench.backends.mujoco.kick_goal import GoalEntry


GOAL={'front_center_xyz_m':[1.,0.,0.], 'width_m':.8,'height_m':.45,'depth_m':.4}


def test_front_entry_needs_whole_sphere_in_goal():
    goal=GoalEntry(GOAL,.1);goal.reset([.7,0,.1])
    assert not goal.update(10,[1.02,0,.1])
    assert goal.update(20,[1.15,0,.1])
    assert not goal.update(30,[1.32,0,.1])


@pytest.mark.parametrize('start,crossing,inside',[
    ([1.2,0,.1],[1.2,0,.1],[1.2,0,.1]),
    ([1.6,0,.1],[1.3,0,.1],[1.2,0,.1]),
    ([.7,.5,.1],[1.1,.5,.1],[1.2,0,.1]),
    ([.7,0,.6],[1.1,0,.6],[1.2,0,.1]),
])
def test_initial_inside_back_side_or_over_crossbar_never_score(start,crossing,inside):
    goal=GoalEntry(GOAL,.1);goal.reset(start)
    assert not goal.update(10,crossing)
    assert not goal.update(20,inside)


def test_goal_orientation_and_duplicate_boundary():
    profile={**GOAL,'yaw_rad':np.pi/2}
    goal=GoalEntry(profile,.1);goal.reset([1.,-.3,.1])
    assert goal.update(10,[1.,.2,.1])
    with pytest.raises(ValueError):goal.update(10,[1.,.2,.1])
