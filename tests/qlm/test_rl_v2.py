"""Public worker framing/idempotency and independent CPU-profile contracts."""
import copy
import io
import json
import os
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


def test_c_level_stdout_cannot_corrupt_protocol_frames():
    # libmujoco prints 'WARNING: ...' through C stdio on fd 1; PYTHONUNBUFFERED makes it immediate.
    code=("import ctypes,os\n"
          "from qlm_bench.rl_v2.worker import protocol_stdout,write_frame\n"
          "channel=protocol_stdout();libc=ctypes.CDLL(None)\n"
          "for i in range(3):\n"
          "    libc.printf(b'WARNING: Nan, Inf or huge value in QACC\\n');libc.fflush(None);os.write(1,b'fd1 text\\n')\n"
          "    write_frame(channel,{'ok':True,'i':i})\n")
    import os
    result=subprocess.run([sys.executable,'-c',code],capture_output=True,check=True,env={**os.environ,'PYTHONUNBUFFERED':'1'})
    stream=io.BytesIO(result.stdout)
    assert [read_frame(stream)['i'] for _ in range(3)]==[0,1,2] and read_frame(stream) is None
    assert b'WARNING: Nan' in result.stderr and b'fd1 text' in result.stderr


LEGACY_SOURCE='95feae2a199082d2a7d81ecc364d43390bd815d36ba55866989e8e94d30ca571'  # 42cda63, AMD-prepared pools
ACTUAL=pytest.mark.skipif(not os.environ.get('QLM_MUJOCO_TASK') or not os.environ.get('QLM_RAMBO_CHECKPOINT') or os.environ.get('MUJOCO_GL') not in ('osmesa','egl'),
                          reason='Actual task model, RAMBO checkpoint and explicitly selected renderer required')


def test_simulator_source_identity_matches_anchors_prepared_on_amd():
    # Anchors prepared on AMD with 42cda63 store LEGACY_SOURCE. QLM-INFRA-006 (opt-in observation_ticks) changed the
    # hashed folders; the old digest is registered as a bitwise-equivalent predecessor (render-cadence-20261030
    # evidence) bound to this exact successor, so restore accepts those pools with a WARNING only on it. Any further
    # edit must re-pin here and register the new digest as a successor with new evidence.
    from qlm_bench.backends.mujoco.rl_v2.equivalence import EQUIVALENT_SOURCE_IDENTITIES
    from qlm_bench.backends.mujoco.rl_v2.storage import execution_source_identity
    assert execution_source_identity()=='6f7c06212cdabdfe02439b9b25d0a7ff28386fca5bd5672a50c8a5c8ac2ab3ac'
    assert EQUIVALENT_SOURCE_IDENTITIES[LEGACY_SOURCE]['successors']=={execution_source_identity()}


def test_observation_cadence_accepts_only_multiples_of_10_dividing_40():
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    rt=object.__new__(MuJoCoRuntime)
    for value in (10,20,40):rt.observation_ticks=value;assert rt.observation_ticks==value
    for value in (0,-10,5,15,30,80,'10',10.,True):
        with pytest.raises(ValueError):rt.observation_ticks=value


def test_restore_accepts_registered_equivalent_source_only(capsys):
    from types import SimpleNamespace
    from qlm_bench.backends.mujoco.rl_v2.snapshot import SCHEMA,check_identity,identity,restore
    from qlm_bench.backends.mujoco.rl_v2.equivalence import EQUIVALENT_SOURCE_IDENTITIES
    rt=SimpleNamespace(physics=SimpleNamespace(backend='native',count=1,model_identity='m',full_model_identity='p'),
                       core=SimpleNamespace(device='cpu'),profile={'asset_profile':'x'},rgb_profile='dual-rgb-360p-v1')
    live=identity(rt)
    assert check_identity(copy.deepcopy(live),live) is None and capsys.readouterr().err==''
    assert check_identity({**live,'source':LEGACY_SOURCE},live)==EQUIVALENT_SOURCE_IDENTITIES[LEGACY_SOURCE]['reason']
    assert 'WARNING: anchor source 95feae2a1990 accepted as registered equivalent' in capsys.readouterr().err
    for stored in ({**live,'source':'0'*64},{**live,'source':LEGACY_SOURCE,'controller':'other'},{**live,'extra':1},{**live,'source':LEGACY_SOURCE,'mujoco':'0'}):
        with pytest.raises(ValueError,match='mismatch'):check_identity(stored,live)
    # The legacy digest binds to its registered successor only: an unregistered live source (a later edit under the
    # hashed folders without a new entry) is rejected even though the stored source is registered.
    for unregistered in ('deadbeef'*8,'ef4f7da3b0ffc4da74fb9829e39fae60540f98a4f9384f29eff3d33b0bb1c7c1'):
        with pytest.raises(ValueError,match='Anchor source identity mismatch'):check_identity({**live,'source':LEGACY_SOURCE},{**live,'source':unregistered})
        with pytest.raises(ValueError,match='mismatch'):check_identity({**live,'source':unregistered},live)
    assert capsys.readouterr().err==''
    # restore() runs the same gate before touching physics: an equivalent source reaches the boundary check.
    with pytest.raises(ValueError,match='Invalid anchor boundary'):restore(rt,{'schema':SCHEMA,'identity':{**live,'source':LEGACY_SOURCE},'tick':5})
    with pytest.raises(ValueError,match='mismatch'):restore(rt,{'schema':SCHEMA,'identity':{**live,'source':'0'*64},'tick':0})
    with pytest.raises(ValueError,match='mismatch'):restore(rt,{'schema':'other','identity':live,'tick':0})


@ACTUAL
def test_observation_cadence_40_captures_a_quarter_with_identical_model_frames(capsys):
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.backends.mujoco.rl_v2 import snapshot as anchors
    from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
    command=[0.,0.,0.,.1934,.142,.05,0.,0.,0.];runs={}
    for cadence in (10,40):
        ticks=[];rt=create_runtime(os.environ.get('QLM_MUJOCO_TASK_ID','push_box'),'native',model_path=os.environ['QLM_MUJOCO_TASK'],
                                   checkpoint=os.environ['QLM_RAMBO_CHECKPOINT'],trace_only=False,device='cpu',seed=7)
        try:
            rt.renderer.observer_clip=None;rt.observation_ticks=cadence;rt.on_observation=lambda s:ticks.append(s['physics_step'])
            rt.set_case_seed(7);rt.reset();ticks.clear();rgb={}
            for i in range(16):
                out=rt.step(prepare_command(command,f'c:{i}',i*10));assert out['terminal'] is None
                if (i+1)*10%40==0:rgb[(i+1)*10]=rt.state()['rgb']
            runs[cadence]=(sorted(set(ticks)),rgb)
            if cadence==10:anchor=anchors.capture(rt)
            else:
                # A pool captured at cadence 10 (AMD, legacy source) restores at cadence 40 with the same frame.
                legacy=copy.deepcopy(anchor);legacy['identity']['source']=LEGACY_SOURCE
                receipt=anchors.restore(rt,legacy);assert 'WARNING: anchor source' in capsys.readouterr().err
                assert receipt['absolute_tick']==160 and all(np.array_equal(receipt['observation']['rgb'][v],rgb[160][v]) for v in rgb[160])
        finally:rt.close()
    assert runs[10][0]==list(range(10,170,10)) and runs[40][0]==[40,80,120,160]
    for tick in (40,80,120,160):
        for view in ('ego','task_centric'):assert np.array_equal(runs[10][1][tick][view],runs[40][1][tick][view])


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


def test_physics_instability_is_a_policy_failure_with_the_last_observed_frame():
    from types import SimpleNamespace
    last=np.full((2,2,3),7,np.uint8)
    class Runtime:
        terminal=None
        physics=SimpleNamespace(ticks=np.array([0]))
        def state(self):return {'rgb':{'ego':last}}
        def freeze_token(self):return {'tick':int(self.physics.ticks[0])}
        def step(self,command):
            if self.physics.ticks[0]>=50:raise FloatingPointError('Physics instability warning2 in world0')
            self.physics.ticks[0]+=10
            return {'command':{**command,'status':'completed'},'terminal':None}
    w=object.__new__(AnchorWorker);w.runtime=Runtime();w.poisoned=False;w.ended=False;w.session='candidate-1';w.anchor_tick=0;w.chunk=0
    w.last_rgb={'ego':np.zeros((2,2,3),np.uint8)}
    r=request();r['payload']={'commands':np.zeros((16,9)).tolist(),'chunk':0}
    out=w._dispatch(r)
    terminal=out['terminal']
    assert terminal['reason']=='physics_instability' and terminal['policy_failure'] and not terminal['task_terminal']
    assert out['completed_count']==5 and [s['tick'] for s in out['samples']]==[40]
    assert np.array_equal(terminal['rgb']['ego'],last) and w.ended


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
