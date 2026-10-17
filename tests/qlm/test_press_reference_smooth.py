"""Reference geometry must round-trip through the original controller without edits."""
import numpy as np
import torch

from qlm_bench.backends.mujoco.press_reference_smooth import limited_step, retained_fk
from qlm_bench.controllers.rambo.kinematics import motor_angles_from_foot_positions_fl


def test_fk_roundtrip_to_retained_ik_on_operating_workspace():
    hip = np.array([.1934, .0465, 0.]); lengths = np.array([.0955, .213, .213])
    for joints in ([.1, .9, -2.], [.55, .3, -2.1], [.7, -.05, -2.2]):
        point = retained_fk(joints, hip, lengths)
        recovered = motor_angles_from_foot_positions_fl(torch.tensor(point[None], dtype=torch.float32),
            torch.tensor(hip[None], dtype=torch.float32), torch.tensor(lengths, dtype=torch.float32), 'cpu')[0]
        np.testing.assert_allclose(recovered.numpy(), joints, atol=2e-6)


def test_reversal_does_not_bypass_reference_velocity_bound():
    value = np.array([0., .01])
    for target in ([.05, -.05], [-.05, .05], [.05, .05]):
        new = limited_step(value, target, .12, .02)
        assert np.max(abs(new-value)) <= .0024 + 1e-12
        value = new


def test_joint_rate_bound_applies_per_component():
    old = np.array([.2, .4, -2.]); rate = np.deg2rad([60., 90., 90.])
    new = limited_step(old, [.8, -.5, -1.], rate, .02)
    np.testing.assert_allclose(abs(new-old), rate*.02, atol=1e-12)
