"""Actual snapshot/controller contract checks; no renderer/GPU starts implicitly."""
import ast
import subprocess
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from qlm_bench.controllers.rambo.core import FrozenActor, DelayedMotor
from qlm_bench.controllers.rambo import math
from qlm_bench.controllers.rambo.control import update_observations
from qlm_bench.controllers.rambo.qp_torque_optimizer import solve_grf_qpth

ROOT=Path(__file__).resolve().parents[2]


def reference_functions(relative):
    # Read immutable pre-extraction statements from Git, without importing Kit.
    source=subprocess.check_output(['git','-C',str(ROOT),'show','189545f:'+relative],text=True)
    tree=ast.parse(source)
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
    for f in functions:f.decorator_list=[]
    from qpth.qp import QPFunction,QPSolvers
    scope=dict(torch=torch,math_utils=math,rambo_quat_error=math.quat_error,
               xyzw_to_wxyz=math.xyzw_to_wxyz,QPFunction=QPFunction,QPSolvers=QPSolvers)
    exec(compile(ast.Module(body=functions,type_ignores=[]),relative,'exec'),scope)
    return scope


def test_original_analytical_ik_and_qp_numeric_regression():
    from qlm_bench.controllers.rambo.kinematics import motor_angles_from_foot_positions
    old=reference_functions('source/rambo/rambo/tasks/direct/rambo_quadruped/qp_env.py')
    hip=torch.tensor([[.1934,.0465,0.],[.1934,-.0465,0.],[-.1934,.0465,0.],[-.1934,-.0465,0.]])
    lengths=torch.tensor([.0955,.213,.213])
    points=hip[None]+torch.tensor([[[.02,.0955,-.3],[.02,-.0955,-.3],[.02,.0955,-.3],[.02,-.0955,-.3]]])
    torch.testing.assert_close(motor_angles_from_foot_positions(points,hip,lengths,'cpu'),
        old['motor_angles_from_foot_positions'](points,hip,lengths,'cpu'),rtol=0,atol=0)
    reference=reference_functions('source/rambo/rambo/tasks/direct/rambo_quadruped/modules/qp_torque_optimizer.py')
    mass=reference['construct_mass_mat'](points,torch.eye(3)[None]/16.087,
                                        torch.diag(torch.tensor([1/.21,1/.525,1/.525]))[None],'cpu')
    args=(mass,torch.zeros(1,6),torch.zeros(1,3),torch.eye(6),1e-4,1.,torch.eye(3)[None],.6,
          torch.tensor([[False,True,True,True]]),'cpu')
    torch.manual_seed(42);actual=solve_grf_qpth(*args)
    torch.manual_seed(42);expected=reference['solve_grf_qpth'](*args)
    for a,b in zip(actual,expected):torch.testing.assert_close(a,b,atol=1e-6,rtol=1e-6)


def test_delay_is_physics_ticks_and_reset_does_not_change_other_lane():
    motor=DelayedMotor(2,'cpu');motor.reset(torch.tensor([0,1]));motor.lags[:]=2
    zeros=torch.zeros(2,12)
    results=[]
    for i in range(4):results.append(motor.compute(torch.ones(2,12)*i*.01,zeros,zeros,zeros,zeros))
    assert results[1].abs().max()==0 and results[2].abs().max()==0
    torch.testing.assert_close(results[3],torch.ones(2,12)*.4)
    before=motor.history[:,1].clone();lags=motor.lags[1].clone()
    motor.reset(torch.tensor([0]))
    torch.testing.assert_close(motor.history[:,1],before)
    torch.testing.assert_close(motor.lags[1],lags)


def test_root_link_rotation_conventions():
    angle=torch.tensor(.4)
    quat=torch.tensor([[0.,0.,torch.sin(angle/2),torch.cos(angle/2)]])
    value=torch.tensor([[1.,2.,3.]])
    torch.testing.assert_close(math.quat_apply_inverse(quat,math.quat_apply(quat,value)),value)
    torch.testing.assert_close(math.quat_error(math.xyzw_to_wxyz(quat),math.xyzw_to_wxyz(quat)),torch.zeros(1,3))


def test_cpu_metadata_does_not_load_runtime():
    code='import sys; import qlm_bench.tasks, qlm_bench.live; assert not any(x in sys.modules for x in ("torch","mujoco","mujoco_warp","isaaclab","omni"))'
    subprocess.run([os.environ.get('QLM_TEST_PYTHON',__import__('sys').executable),'-c',code],check=True)


@pytest.mark.skipif(not os.environ.get('QLM_MUJOCO_TASK') or os.environ.get('MUJOCO_GL') not in ('osmesa','egl'),
                    reason='Actual task model and explicitly selected renderer required')
def test_actual_50hz_sensor_updates_and_read_only_observation():
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
    runtime=MuJoCoRuntime(os.environ['QLM_MUJOCO_TASK'],os.environ['QLM_RAMBO_CHECKPOINT'],backend='native',device='cpu')
    try:
        initial=runtime.reset();epoch=initial['reset_epoch']
        ids=[]
        for i in range(10):
            runtime.step(prepare_command([0.,0.,0.,.1934,.142,.05,0.,0.,0.],f'probe:{i}',i*10))
            packet=runtime.state();ids.append(packet['sensor_frame_ids']['ego'])
            assert packet['simulation_time_ns']==(i+1)*20_000_000 and packet['reset_epoch']==epoch
            history=runtime.core._obs_history.clone();tick=runtime.physics.ticks.copy()
            duplicate=runtime.state()
            assert duplicate['sensor_frame_ids']==packet['sensor_frame_ids']
            np.testing.assert_array_equal(runtime.physics.ticks,tick)
            torch.testing.assert_close(runtime.core._obs_history,history,rtol=0,atol=0)
        assert ids==list(range(initial['sensor_frame_ids']['ego']+1,initial['sensor_frame_ids']['ego']+11))
    finally:runtime.close()


@pytest.mark.skipif(not os.environ.get('QLM_MUJOCO_MODEL'),reason='Actual model resource supplied explicitly')
def test_native_read_and_subset_reset_preserve_physics_and_other_world():
    from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
    from qlm_bench.controllers.rambo.core import RAMBOCore
    physics=MuJoCoPhysics(os.environ['QLM_MUJOCO_MODEL'],count=2)
    core=RAMBOCore(physics,os.environ['QLM_RAMBO_CHECKPOINT'])
    for _ in range(4):
        residual=core.begin_control()
        for _ in range(5):physics.step(core.motor_effort().numpy())
        core.end_control(residual)
    before=physics.snapshot(1);history=core._obs_history[1].clone()
    physics.reset([0]);core.reset(torch.tensor([0]))
    after=physics.snapshot(1)
    assert before['simulation_time_ns']==after['simulation_time_ns']
    np.testing.assert_array_equal(before['qpos'],after['qpos'])
    torch.testing.assert_close(history,core._obs_history[1],rtol=0,atol=0)
    times=physics.ticks.copy();core.refresh();physics.read();physics.snapshot()
    np.testing.assert_array_equal(physics.ticks,times)
