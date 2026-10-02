"""Regression for resetting actuator buffers created by inference-mode steps."""
from __future__ import annotations
import copy
from types import SimpleNamespace
import numpy as np
import pytest
import torch

from rambo.contracts_v2.runtime import prepare_command
from rambo.tasks.common.controller_runtime import ControllerRuntime
from rambo.tasks.common.episode import EpisodeRuntime


def runtime_stub(monkeypatch):
    flags=[]
    def inside(operation):
        flags.append((operation,torch.is_inference_mode_enabled(),torch.is_grad_enabled()))
    class Base:
        def __init__(self):
            self.clock_runtime=EpisodeRuntime();self.completed=0
            self.buffer=None
            self.sim=SimpleNamespace(render=lambda:inside('render'))
        @property
        def episode_tick(self):return self.clock_runtime.clock.tick(self.completed)
        @property
        def simulation_time_ns(self):return self.clock_runtime.clock.time_ns(self.completed)
        @property
        def episode_clock(self):return self.clock_runtime.clock
        @property
        def task_outcome(self):return self.clock_runtime.outcome
        @property
        def executed_command_history(self):return self.clock_runtime.history
        @property
        def current_command_confirmation(self):return copy.deepcopy(self.clock_runtime.current_command)
        def submit_native9_command(self,prepared):
            inside('submit');self.clock_runtime.submit(prepared,self.completed)
            # A real reset can leave command/state buffers as inference tensors.
            if self.buffer is not None:self.buffer[0,0]=prepared['filtered'][0]
    base=Base()
    class Environment:
        def reset(self):
            inside('reset')
            if base.buffer is not None:
                # Mirrors the original delay buffer's indexed in-place clearing.
                base.buffer[:,:]=0.
            base.clock_runtime.reset(base.completed)
            return torch.zeros(1,405),{}
        def step(self,action):
            inside('step')
            assert action.shape==(1,18)
            if base.buffer is None:base.buffer=torch.ones(2,3)
            base.completed+=5;base.clock_runtime.confirm_control(base.completed)
            return torch.zeros(1,405),None,torch.tensor([False]),{}
    runtime=ControllerRuntime.__new__(ControllerRuntime)
    runtime.env=Environment();runtime.base_env=base
    runtime.observations=torch.zeros(1,405)
    def controller(observations):
        inside('controller')
        return torch.ones(1,18)
    runtime.controller=controller
    from rambo.tasks.common import snapshots
    def capture_state(env):
        inside('state')
        return {'buffer':[float(env.buffer[0,0]) if env.buffer is not None else 0.]}
    def capture_rgb(env):
        inside('rgb')
        return {'ego':np.full((2,2,3),42,np.uint8)},{'ego':'unchanged'},{'ego':7}
    monkeypatch.setattr(snapshots,'capture_state',capture_state)
    monkeypatch.setattr(snapshots,'capture_rgb',capture_rgb)
    return runtime,flags


def test_explicit_reset_after_controller_inference_clears_inference_buffers(monkeypatch):
    runtime,flags=runtime_stub(monkeypatch)
    initial=runtime.reset()
    first=runtime.step(prepare_command([0]*9,'first',0))
    assert first['completed_interval'] and first['simulation_time_ns']==20_000_000
    assert torch.is_inference(runtime.base_env.buffer)
    reset=runtime.reset()
    assert reset['simulation_time_ns']==0 and reset['state']==initial['state']
    assert reset['reset_epoch']>initial['reset_epoch']
    assert reset['executed_history']==[] and not runtime.base_env.buffer.any()
    second=runtime.step(prepare_command([.25,0,0,.3,.1,.2,0,0,0],'second',0))
    assert second['completed_interval'] and second['command']['executed'][0]==.25
    runtime.reset()
    assert all(inference and not grad for _,inference,grad in flags)
    assert not torch.is_inference_mode_enabled() and torch.is_grad_enabled()


def test_state_reads_preserve_values_and_context_is_restored_after_reset_failure(monkeypatch):
    runtime,flags=runtime_stub(monkeypatch)
    runtime.reset();runtime.step(prepare_command([0]*9,'one',0))
    before=runtime.base_env.buffer.clone()
    packet=runtime.state()
    torch.testing.assert_close(runtime.base_env.buffer,before)
    assert packet['rgb']['ego'].dtype==np.uint8 and (packet['rgb']['ego']==42).all()
    def fail():
        assert torch.is_inference_mode_enabled() and not torch.is_grad_enabled()
        raise OSError('actual reset failed')
    runtime.env.reset=fail
    with pytest.raises(OSError,match='actual reset failed'):runtime.reset()
    assert not torch.is_inference_mode_enabled() and torch.is_grad_enabled()


@pytest.mark.parametrize("callback_enabled",[False,True])
def test_initial_reset_and_render_precede_ppo_rng_initialization(monkeypatch,callback_enabled):
    """Preserve the collector's RNG-dependent actuator lag initialization order."""
    import sys
    from rambo.tasks.common import controller_runtime as module
    from rambo.tasks.common.environment_factory import PUSH_BOX_TASK_ID
    from rambo.tasks.common import snapshots
    from rambo.utils import registry
    from rambo.validation import checkpoints

    events=[];config_calls=[]
    prefix=['observer','recorder'] if callback_enabled else []
    base=SimpleNamespace(device='cpu',simulation_time_ns=0,episode_tick=0,
        episode_clock=SimpleNamespace(reset_epoch=0),task_outcome={},executed_command_history=[])
    def render():
        assert torch.is_inference_mode_enabled()
        events.append('render')
    base.sim=SimpleNamespace(render=render)
    class Environment:
        unwrapped=base
        def reset(self):
            assert torch.is_inference_mode_enabled()
            events.append('reset')
            self.reset_sample=float(torch.rand(1))
            self.last_observations=torch.zeros(1,405)
            return self.last_observations,{}
    env=Environment()
    class PPO:
        def __init__(self,**kwargs):
            events.append('ppo')
            assert hasattr(env,'last_observations')
            assert events==prefix+['reset','render','render','render','render','ppo']
            # Model construction reseeds/consumes the RNG after actuator reset.
            torch.manual_seed(kwargs['agent_cfg']['seed'])
            torch.randn(405,18)
        def get_inference_policy(self,device):
            events.append('policy')
            return lambda observations:torch.zeros(1,18)
    monkeypatch.setitem(sys.modules,'crl2.algorithms',SimpleNamespace(PPO=PPO))
    def configure(*args,**kwargs):
        config_calls.append(kwargs)
        return SimpleNamespace()
    monkeypatch.setattr(module,'make_task_config',configure)
    monkeypatch.setattr(module,'make_environment',lambda *args,**kwargs:env)
    monkeypatch.setattr(registry,'load_cfg_from_registry',lambda *args,**kwargs:{'general':{'num_envs':1}})
    monkeypatch.setattr(checkpoints,'contract_for_task',lambda *args:SimpleNamespace())
    monkeypatch.setattr(checkpoints,'load_verified_checkpoint',lambda *args:{})
    monkeypatch.setattr(checkpoints,'restore_runner',lambda *args,**kwargs:events.append('restore'))
    monkeypatch.setattr(snapshots,'capture_state',lambda env:{'unchanged':True})
    monkeypatch.setattr(snapshots,'capture_rgb',lambda env:({}, {}, {}))
    rng_state=torch.get_rng_state()
    try:
        torch.manual_seed(123)
        expected_reset_sample=float(torch.rand(1))
        torch.manual_seed(123)
        def attach(runtime):
            assert runtime.env is env and runtime.base_env is base and runtime.cfg is not None
            assert not hasattr(runtime,'controller') and not hasattr(env,'last_observations')
            events.extend(['observer','recorder']);base._v2_recorder=SimpleNamespace(active=False)
        runtime=module.ControllerRuntime(PUSH_BOX_TASK_ID,profile={},resource_root='resources',
                                         checkpoint_path='fixed.pt',seed=42,device='cpu',asset_id='toy-blue',
                                         on_environment_ready=attach if callback_enabled else None)
        assert env.reset_sample==expected_reset_sample
        assert events==prefix+['reset','render','render','render','render','ppo','restore','policy']
        assert config_calls[0]['asset_id']=='toy-blue'
        assert runtime.observations is env.last_observations
    finally:
        torch.set_rng_state(rng_state)
