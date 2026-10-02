"""Source-backed lifecycle checks: recorder independence and retained task predicates."""
from __future__ import annotations
import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
import torch

from rambo.contracts_v2.runtime import prepare_command
from rambo.tasks.common.episode import EpisodeRuntime,EpisodeClock
from rambo.tasks.common.push_box_geometry import fully_inside,PolicySuccessHold
from rambo.tasks.common.lift_basket_geometry import lifted
from rambo.tasks.common.press_button_logic import PressSuccessHold

ROOT=Path(__file__).resolve().parents[2]
TASKS=ROOT/'source/rambo/rambo/tasks/direct/rambo_quadruped'


def test_clock_uses_actual_completed_physics_steps_and_epoch_origin():
    clock=EpisodeClock();clock.reset(1007)
    assert clock.tick(1012)==5 and clock.time_ns(1012)==10_000_000
    with pytest.raises(ValueError):clock.tick(1006)
    epoch=clock.reset_epoch;clock.reset(1037)
    assert clock.tick(1037)==0 and clock.reset_epoch==epoch+1


def test_history_contains_only_confirmed_full_holds_and_reset_isolation():
    runtime=EpisodeRuntime();runtime.reset(100)
    prepared=prepare_command([.1,0,0,.3,.1,.2,12,3,4],'first',0)
    runtime.submit(prepared,100);prepared['filtered'][0]=999
    runtime.confirm_control(105)
    assert runtime.history==[] and runtime.current_command['status']=='partial'
    with pytest.raises(ValueError):runtime.submit(prepare_command([0]*9,'overlap',0),105)
    runtime.confirm_control(110)
    assert len(runtime.history)==1 and runtime.history[0]['executed'][0]==pytest.approx(np.float32(.1))
    assert runtime.history[0]['executed'][6:]==[0.,0.,0.]
    returned=runtime.history;returned[0]['executed'][0]=999
    assert runtime.history[0]['executed'][0]!=999
    with pytest.raises(ValueError):runtime.confirm_control(115)
    runtime.set_outcome(success=False,fallen=True,timed_out=False)
    runtime.seal_terminal({'state':{'position':[1]},'rgb':{'ego':np.ones((2,2,3),np.uint8)}})
    saved=runtime.terminal;runtime.reset(115)
    assert runtime.history==[] and runtime.current_command is None and not runtime.outcome['terminated']
    saved['state']['position'][0]=999
    assert runtime.terminal['state']['position']==[1]


def load_native_runtime_class():
    """Execute the real task methods over a CPU controller/scene stub."""
    class ControllerBase:
        def _reset_idx(self,ids):self.events.append('controller_reset')
    tree=ast.parse((TASKS/'native9_task_env.py').read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Native9TaskEnv')
    module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),cls],type_ignores=[])
    def state(env):
        env.events.append('terminal_state_copy')
        return {'position':list(env.snapshot_position),'task.success':[bool(env._success[0])]}
    def rgb(env):
        env.events.append('terminal_rgb_copy')
        return {'ego':env.snapshot_rgb}, {'ego':'owned'}, {'ego':7}
    namespace=dict(QPEnv=ControllerBase,torch=torch,copy=copy,EpisodeRuntime=EpisodeRuntime,
                   capture_state=state,capture_rgb=rgb)
    exec(compile(ast.fix_missing_locations(module),'<real-native9-runtime>','exec'),namespace)
    return namespace['Native9TaskEnv']


def task_env(task,with_recorder=False):
    base=load_native_runtime_class()
    path,clsname={'push':('push_box_v2.py','PushBoxV2Env'),
                  'lift':('lift_basket_v2.py','LiftBasketV2Env'),
                  'press':('press_button_v2.py','PressButtonV2Env')}[task]
    tree=ast.parse((TASKS/path).read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==clsname)
    fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_get_dones')
    namespace=dict(torch=torch,fully_inside=fully_inside,lifted=lifted)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<real-task-predicate>','exec'),namespace)
    envtype=type('Task',(base,),{'_get_dones':namespace['_get_dones']})
    env=envtype.__new__(envtype)
    env._episode_runtime=EpisodeRuntime();env._episode_runtime.reset(1000);env._sim_step_counter=1000
    env.cfg=SimpleNamespace(approved_profile={'goal_x':[0,1],'goal_y':[0,1],
        'floor_z_m':0.,'minimum_clearance_m':.02,'success_enable_after_s':2.1},pilot_max_physics_steps=2000,
        ee_default_command=(.1934,.142,.05))
    env.base_height=torch.tensor([.3]);env.projected_gravity_b=torch.tensor([[0.,0.,-1.]])
    env.device=torch.device('cpu');env.num_envs=1;env.events=[]
    env._velocity_commands=torch.zeros(1,3);env._ee_pos_commands=torch.zeros(1,3);env._ee_force_commands=torch.zeros(1,3)
    env._success=torch.tensor([False]);env._success_hold=PressSuccessHold() if task=='press' else PolicySuccessHold()
    env.geometry_world=lambda:{'footprint_xy':[[.2,.2],[.8,.2],[.8,.8],[.2,.8]],'minimum_world_z':.03}
    env.displacement=torch.tensor([.012])
    env.review_diagnostics=lambda:{'count':env._success_hold.count}
    env.snapshot_position=[1.,2.,3.];env.snapshot_rgb=np.ones((2,2,3),np.uint8)
    if with_recorder:env._v2_recorder=SimpleNamespace(tick=999999)
    return env


@pytest.mark.parametrize('task',['push','lift','press'])
def test_task_completion_and_timeout_are_identical_without_recorder(task):
    traces=[]
    for enabled in [False,True]:
        env=task_env(task,enabled);trace=[]
        ticks=[5,10,15,20,30] if task!='lift' else [1040,1045,1050,1055,1060,1070]
        for tick in ticks:
            env._sim_step_counter=1000+tick
            term,timeout=env._get_dones()
            trace.append((bool(term[0]),bool(timeout[0]),env._success_hold.count))
        assert trace[-1]==(True,False,3)
        assert env.task_outcome['termination_reason']=='task_success'
        traces.append(trace)
        env._success_hold.reset();env.cfg.pilot_max_physics_steps=20
        env.geometry_world=lambda:{'footprint_xy':[[2,2]],'minimum_world_z':0.}
        env.displacement=torch.tensor([0.]);env._sim_step_counter=1020
        term,timeout=env._get_dones()
        assert not term[0] and timeout[0]
        assert env.task_outcome['termination_reason']=='timeout'
    assert traces[0]==traces[1]


@pytest.mark.parametrize('task',['push','lift','press'])
def test_fall_precedes_success_and_terminal_is_owned_before_reset(task):
    env=task_env(task);env.base_height=torch.tensor([.05]);env._sim_step_counter=1015
    env._get_dones();assert env.task_outcome['termination_reason']=='robot_fall'
    command=prepare_command([0,0,0,.3,.1,.2,0,0,0],'partial',0)
    env._episode_runtime.submit(command,1000);env._episode_runtime.confirm_control(1005)
    saved=env.capture_terminal_snapshot()
    assert saved['partial_interval'] and saved['executed_history']==[] and saved['state']['position'][0]==1
    env.snapshot_position[0]=999;env.snapshot_rgb[:]=0
    assert env.terminal_snapshot['state']['position'][0]==1 and env.terminal_snapshot['rgb']['ego'].all()
    env._expert_start_world=[1];env._lift_phase='raise';env._press_integral=7
    env._reset_idx([0])
    assert env.episode_tick==0 and env.executed_command_history==[] and env.current_command_confirmation is None
    assert not env.task_outcome['terminated'] and env._success_hold.count==0
    assert not hasattr(env,'_expert_start_world') and not hasattr(env,'_lift_phase') and not hasattr(env,'_press_integral')
    assert env.events.index('terminal_state_copy')<env.events.index('controller_reset')
    assert env.terminal_snapshot['reason']=='robot_fall'


def test_qp_hooks_capture_terminal_before_recorder_and_reset():
    source=(TASKS/'qp_env.py').read_text()
    tree=ast.parse(source);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='QPEnv')
    step=ast.get_source_segment(source,next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='step'))
    assert step.index('self._confirm_episode_control()')<step.index('recorder.after_control()')
    assert step.index('self.capture_terminal_snapshot()')<step.index('recorder.before_reset(')<step.index('self._reset_idx(')
