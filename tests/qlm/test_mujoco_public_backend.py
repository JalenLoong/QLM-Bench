"""Shared backend contracts, case rejection and state-cache equivalence."""
import os
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from qlm_bench.backends.factory import backend_binding
from qlm_bench.backends.mujoco.evaluation import MuJoCoEvaluationAdapter,CONTROLLER


def test_conversion_and_evaluation_use_common_implementations():
    from qlm_bench.compatibility.dataset_v2.conversion import convert
    from qlm_bench.backends.mujoco.conversion import convert as alias
    from qlm_bench.backends.controller import ControllerRuntimeAdapter
    from qlm_bench.backends.isaac.adapter import ControllerRuntimeAdapter as IsaacAdapter
    assert convert is alias and issubclass(IsaacAdapter,ControllerRuntimeAdapter)
    for task in ('push_box','press_button','lift_basket'):
        assert backend_binding(task,'native')['converter']==backend_binding(task,'isaac')['converter']


def test_no_silent_nominal_substitution_for_wrong_case_goal():
    profile={'task_id':'push_box','instruction':'Push the box into the target area.','asset_id':'box',
             'asset_profile':'fixture','canonical_goal_position':[1.,0.,0.]}
    runtime=SimpleNamespace(profile=profile,physics=SimpleNamespace(model_identity='a'*64,backend='native'))
    case=SimpleNamespace(task_id='push_box',instruction=profile['instruction'],runtime_profile='mujoco-native-original-v1',
        controller_profile=CONTROLLER,assets={'box':'a'*64},scene={'resource_identity':'a'*64},
        goal={'position':[9.,9.,9.],'task_profile':'fixture'})
    adapter=MuJoCoEvaluationAdapter.__new__(MuJoCoEvaluationAdapter)
    with pytest.raises(ValueError,match='Case goal differs'):adapter.reconstruct_case(runtime,case)


@pytest.mark.skipif(not os.environ.get('QLM_MUJOCO_MODEL'),reason='Explicit actual robot resource required')
def test_cached_state_reads_preserve_actual_controller_trajectory():
    from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
    from qlm_bench.controllers.rambo.core import RAMBOCore
    torch.set_num_threads(1)
    physics=[MuJoCoPhysics(os.environ['QLM_MUJOCO_MODEL'],cache_reads=cache) for cache in (True,False)]
    controllers=[RAMBOCore(p,os.environ['QLM_RAMBO_CHECKPOINT'],case_seeds=[123]) for p in physics]
    for _ in range(12):
        for p,c in zip(physics,controllers):
            residual=c.begin_control()
            for _ in range(5):
                p.read();p.read();p.snapshot()
                p.step(c.motor_effort().numpy())
            c.end_control(residual)
        np.testing.assert_array_equal(physics[0].data[0].qpos,physics[1].data[0].qpos)
        np.testing.assert_array_equal(physics[0].data[0].qvel,physics[1].data[0].qvel)
    state=physics[0].read();state.q.zero_()
    assert torch.count_nonzero(physics[0].read().q)>0  # Caller never owns cached tensors.
    for p in physics:p.close()


@pytest.mark.skipif(not os.environ.get('QLM_MUJOCO_MODEL'),reason='Explicit actual robot resource required')
def test_invalid_lane_or_nonfinite_physics_cannot_silently_recover():
    from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
    physics=MuJoCoPhysics(os.environ['QLM_MUJOCO_MODEL'],count=2)
    before=physics.snapshot(1)
    for ids in ([-1],[2],[0,0],[True]):
        with pytest.raises(ValueError,match='world indices'):physics.reset(ids)
    np.testing.assert_array_equal(before['qpos'],physics.snapshot(1)['qpos'])
    physics.data[0].qvel[0]=float('nan')
    with pytest.raises(FloatingPointError,match='Nonfinite'):physics.step(np.zeros((2,12)))
    assert physics.ticks.tolist()==[0,0]
    physics.reset([0]);physics.close()
