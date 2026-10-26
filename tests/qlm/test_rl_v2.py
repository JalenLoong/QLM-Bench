"""Public worker framing/idempotency and independent CPU-profile contracts."""
import io
import json
import subprocess
import sys
import numpy as np
import pytest
from qlm_bench.rl_v2.worker import read_frame,write_frame,AnchorWorker


def request(i='1',operation='execute'):
    return {'schema':'qlm-rl-v2-ipc-v1','id':i,'operation':operation,'session':'candidate-1','payload':{}}


def worker(handler):
    w=object.__new__(AnchorWorker);w.seen={};w.last_id=None;w.last_response=None;w.poisoned=False;w._dispatch=handler
    return w


def test_lossless_bounded_RGB_frames():
    image=np.arange(36,dtype=np.uint8).reshape(3,4,3);s=io.BytesIO()
    write_frame(s,{'rgb':image});s.seek(0);assert np.array_equal(read_frame(s)['rgb'],image)
    with pytest.raises(ValueError):read_frame(io.BytesIO(b'\xff\xff\xff\xff'))
    with pytest.raises(EOFError):read_frame(io.BytesIO(b'\x00\x00\x00\x03x'))


def test_duplicate_never_reexecutes_and_conflict_rejected():
    calls=[];w=worker(lambda r:calls.append(r) or {'commands':16})
    a=w.handle(request());assert w.handle(request())==a and len(calls)==1
    with pytest.raises(ValueError):w.handle({**request(),'payload':{'different':True}})
    w.handle(request('2'))
    with pytest.raises(ValueError,match='expired'):w.handle(request())
    assert len(calls)==2


def test_failure_is_cached_before_retry():
    calls=[]
    def fail(r):calls.append(r);raise RuntimeError('uncertain physical side effect')
    w=worker(fail);a=w.handle(request());assert not a['ok'] and w.poisoned
    assert w.handle(request())==a and len(calls)==1


def test_import_worker_does_not_import_simulator_or_torch():
    result=subprocess.check_output([sys.executable,'-c',"import sys,qlm_bench.rl_v2.worker; print('torch' in sys.modules, 'mujoco' in sys.modules)"],text=True)
    assert result.strip()=='False False'


def test_cpu_profile_does_not_replace_egl_contract():
    from qlm_bench.rl_v2.evaluation import PROFILE
    from qlm_bench.backends.mujoco.suite import RUNTIME
    assert PROFILE!=RUNTIME and 'osmesa' in PROFILE


def test_finite_unrepresentable_commands_are_policy_failure_without_physics():
    from types import SimpleNamespace
    class Runtime:
        terminal=None
        physics=SimpleNamespace(ticks=np.array([0]))
        def state(self):return {'rgb':{'ego':np.zeros((2,2,3),np.uint8)}}
        def freeze_token(self):return {'tick':0}
        def step(self,*args):raise AssertionError('Rejected commands cannot execute')
    w=object.__new__(AnchorWorker);w.runtime=Runtime();w.poisoned=False;w.ended=False;w.session='candidate-1';w.anchor_tick=0;w.chunk=0
    r=request();r['payload']={'commands':np.full((16,9),1e100).tolist(),'chunk':0}
    out=w._dispatch(r)
    assert out['completed_count']==0 and out['terminal']['policy_failure'] and not out['terminal']['task_terminal']
    assert w.ended


def test_actual_controller_observation_command_offsets():
    torch=pytest.importorskip('torch')
    from types import SimpleNamespace
    from qlm_bench.controllers.rambo.control import update_observations
    env=SimpleNamespace(num_envs=1,base_height=torch.ones(1),projected_gravity_b=torch.zeros(1,3),
        base_lin_vel_b=torch.zeros(1,3),base_ang_vel_b=torch.zeros(1,3),joint_pos=torch.zeros(1,12),
        default_joint_pos=torch.zeros(1,12),joint_vel=torch.zeros(1,12),_desired_joint_pos=torch.zeros(1,12),
        contact_generator=SimpleNamespace(desired_contact_phase=torch.zeros(1,4),desired_contact_mode=torch.zeros(1,4)),
        _velocity_commands=torch.tensor([[1.,2.,3.]]),_ee_pos_commands=torch.tensor([[4.,5.,6.]]),
        _ee_force_commands=torch.tensor([[7.,8.,9.]]),_last_action=torch.arange(18.)[None],
        cfg=SimpleNamespace(history_length=5),_obs_history=torch.zeros(1,5,81))
    observed=update_observations(env)['policy'].reshape(1,5,81)
    torch.testing.assert_close(observed[0,-1,54:63],torch.arange(1.,10.))
    torch.testing.assert_close(observed[0,-1,63:81],torch.arange(18.))
