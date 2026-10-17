import numpy as np
import pytest
from qlm_bench.backends.mujoco.reference_retarget import lateral_reference_command
from qlm_bench.backends.mujoco.reference_retarget import bounded_cross_track_offset
from qlm_bench.backends.mujoco.reference_retarget import continuous_world_target


@pytest.mark.parametrize('phase',['settle','base_approach','normal_approach'])
def test_non_manipulation_is_unchanged(phase):
    source=[.12,.01,.02,.3,-.02,.14,0,0,0]
    assert lateral_reference_command(source,phase=phase,elapsed=1)==source


def test_only_lateral_base_motion_changes_and_inboard_target_moves_base_right():
    source=np.array([.12,.01,.02,.3,-.02,.14,0,0,0])
    command=np.array(lateral_reference_command(source,phase='straight_push',elapsed=1))
    assert command[1]==-.05
    np.testing.assert_array_equal(command[[0,2,3,4,5,6,7,8]],source[[0,2,3,4,5,6,7,8]])
    np.testing.assert_array_equal(lateral_reference_command(source,phase='straight_push',elapsed=0),source)


def test_no_hidden_integral_or_mutation_and_reject_nan():
    source=[.12,.01,.02,.3,.12,.14,0,0,0]
    a=lateral_reference_command(source,phase='straight_push',elapsed=1)
    lateral_reference_command([.12,.01,.02,.3,.4,.14,0,0,0],phase='straight_push',elapsed=1)
    assert a==lateral_reference_command(source,phase='straight_push',elapsed=1)
    assert source[1]==.01 and a[1]==0
    with pytest.raises(ValueError):lateral_reference_command(source,phase='straight_push',elapsed=float('nan'))


def test_cross_track_correction_has_direction_rate_and_absolute_bounds():
    assert bounded_cross_track_offset(.04,0.)==pytest.approx(.003)
    assert bounded_cross_track_offset(-.04,0.)==pytest.approx(-.003)
    value=0.
    for _ in range(100):value=bounded_cross_track_offset(1.,value)
    assert value==pytest.approx(.1)
    assert bounded_cross_track_offset(0.,value)==pytest.approx(.097)
    with pytest.raises(ValueError):bounded_cross_track_offset(float('nan'),0.)


def test_world_target_slew_preserves_direction_without_instant_phase_jump():
    previous=np.array([.4,.1,.15]);target=np.array([.48,.16,.15])
    step=continuous_world_target(target,previous,.008)
    assert np.linalg.norm(step-previous)==pytest.approx(.008)
    np.testing.assert_allclose(np.cross(step-previous,target-previous),0,atol=1e-16)
    np.testing.assert_array_equal(previous,[.4,.1,.15])
    np.testing.assert_allclose(continuous_world_target(step,previous,.1),step)
