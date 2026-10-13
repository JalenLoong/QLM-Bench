"""Independent-case RNG regressions, including the previously coupled reset path."""
import os
import pytest
import torch

from qlm_bench.controllers.rambo.random import CaseRandomStreams
from qlm_bench.controllers.rambo.core import DelayedMotor


def test_other_lane_reset_does_not_change_future_random_sequence():
    first=CaseRandomStreams([11,97]);control=CaseRandomStreams([11,97])
    for _ in range(7):torch.testing.assert_close(first.qp_uniform('cpu'),control.qp_uniform('cpu'),rtol=0,atol=0)
    first.reset([0],[123]);first.motor_delays([0],'cpu')
    for _ in range(31):
        torch.testing.assert_close(first.qp_uniform('cpu')[1],control.qp_uniform('cpu')[1],rtol=0,atol=0)
    torch.testing.assert_close(first.motor_delays([1],'cpu'),control.motor_delays([1],'cpu'),rtol=0,atol=0)


def test_case_identity_independent_of_lane_order_and_batch_size():
    batch=CaseRandomStreams([123,456]);reordered=CaseRandomStreams([456,123]);single=CaseRandomStreams([456])
    torch.testing.assert_close(batch.motor_delays([1],'cpu'),single.motor_delays([0],'cpu'),rtol=0,atol=0)
    for _ in range(13):
        a=batch.qp_uniform('cpu');b=reordered.qp_uniform('cpu');c=single.qp_uniform('cpu')
        torch.testing.assert_close(a[1],b[0],rtol=0,atol=0);torch.testing.assert_close(a[1],c[0],rtol=0,atol=0)


def test_motor_and_qp_streams_do_not_share_draw_order_or_global_rng():
    torch.manual_seed(1001);global_before=torch.get_rng_state().clone()
    a=CaseRandomStreams([42]);b=CaseRandomStreams([42])
    for _ in range(33):a.motor_delays([0],'cpu')
    torch.testing.assert_close(a.qp_uniform('cpu'),b.qp_uniform('cpu'),rtol=0,atol=0)
    torch.testing.assert_close(global_before,torch.get_rng_state(),rtol=0,atol=0)
    motor=DelayedMotor(1,'cpu',b);motor.reset(torch.tensor([0]));first=motor.lags.clone()
    b.reset([0],[42]);motor.reset(torch.tensor([0]));torch.testing.assert_close(first,motor.lags,rtol=0,atol=0)
    assert 0<=int(motor.lags.min())<=int(motor.lags.max())<=10


@pytest.mark.skipif(not os.environ.get('QLM_MUJOCO_MODEL'),reason='Explicit actual robot resource required')
def test_actual_controller_reset_retains_other_lane_rng_and_history():
    from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
    from qlm_bench.controllers.rambo.core import RAMBOCore
    physics=MuJoCoPhysics(os.environ['QLM_MUJOCO_MODEL'],count=2)
    before_global=torch.get_rng_state().clone()
    core=RAMBOCore(physics,os.environ['QLM_RAMBO_CHECKPOINT'],case_seeds=[7,19])
    for _ in range(5):
        action=core.begin_control()
        for _ in range(5):physics.step(core.motor_effort().numpy())
        core.end_control(action)
    state=core.case_rng.identity();history=core._obs_history[1].clone();lag=core.motor.lags[1].clone()
    physics.reset([0]);core.reset(torch.tensor([0]),case_seeds=[100])
    after=core.case_rng.identity()
    for stream in state['state_sha256']:
        assert state['state_sha256'][stream][1]==after['state_sha256'][stream][1]
    torch.testing.assert_close(history,core._obs_history[1],rtol=0,atol=0)
    torch.testing.assert_close(lag,core.motor.lags[1],rtol=0,atol=0)
    torch.testing.assert_close(before_global,torch.get_rng_state(),rtol=0,atol=0)
    physics.close()
