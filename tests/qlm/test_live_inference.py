"""Physical/RPC contracts, no model, Isaac or offline future-trajectory reader."""
from copy import deepcopy
import hashlib
import multiprocessing
import socket
import struct
import time

import numpy as np
import pytest

from qlm_bench.live import (PolicyHistory, RPCClient, RPCServer, SynchronousDriver,
                            make_message, make_observation, validate_live_observation)
from qlm_bench.live.protocol import STATE_SEMANTICS
from qlm_bench.live.transport import ProtocolError, RemoteError, dumps, loads, receive


ROOT = {'observation.state.base.position':[0.,0.,.31],
        'observation.state.base.orientation':[0.,0.,0.,1.],
        'observation.state.base.linear_velocity':[0.,0.,0.],
        'observation.state.base.angular_velocity':[0.,0.,0.],
        'observation.state.projected_gravity':[0.,0.,-1.]}


class Runtime:
    def __init__(self, terminal_tick=None):
        self.epoch = 0
        self.tick = 0
        self.steps = 0
        self.commands = []
        self.terminal_tick = terminal_tick
        self.pixel = 0
        self.reset_count = 0

    def reset(self):
        self.epoch += 1
        self.tick = 0
        self.commands = []
        self.pixel = 0
        self.reset_count += 1
        return self.state()

    def state(self):
        root = deepcopy(ROOT)
        root['task.secret'] = [99.]
        root['observation.state.base.linear_velocity'][0] = self.pixel/100.
        image = np.full((720,1280,3),self.pixel,np.uint8)
        return dict(physics_step=self.tick,simulation_time_ns=self.tick*2_000_000,
                    reset_epoch=self.epoch,state=root,rgb={'ego':image,'task_centric':image.copy()},
                    sensor_frame_ids={'ego':self.tick//10,'task_centric':self.tick//10},
                    executed_history=deepcopy(self.commands),outcome={})

    def step(self, prepared):
        assert prepared['start_tick'] == self.tick
        self.steps += 1
        self.tick += 10
        if self.terminal_tick is not None and self.tick >= self.terminal_tick:
            self.tick = self.terminal_tick
        actual = deepcopy(prepared)
        completed = self.tick == prepared['end_tick']
        actual.update(executed_until_tick=self.tick,status='completed' if completed else 'partial',
                      executed=deepcopy(prepared['filtered']) if completed else None)
        if completed:self.commands.append(deepcopy(actual))
        self.pixel = (self.pixel + round(abs(prepared['filtered'][0])*10)+1)%255
        terminal = None
        if self.terminal_tick is not None and self.tick >= self.terminal_tick:
            terminal = self.state()
            terminal.update(reason='task_success',success=True,fallen=False,timed_out=False)
            self.reset()  # Existing low-level auto-reset retains the copied terminal.
        return dict(command=actual,terminal=terminal,completed_interval=completed,
                    simulation_time_ns=actual['executed_until_tick']*2_000_000)


class PhysicalPolicy:
    def __init__(self):
        self.history = PolicyHistory()
        self.calls = []
        self.feedback_pixels = []
        self.observation = None

    def __call__(self, request):
        self.calls.append((request['method'],request['request_id']))
        method,payload = request['method'],request['payload']
        if method == 'reset':
            self.history.reset(payload['reset'])
            self.history.observe(payload['observation']['observation'])
            self.observation = payload['observation']
            return {'status':'observed'}
        if method == 'predict':
            assert payload['observation_id'] == self.history.observation_id
            pixel = int(self.observation['samples'][-1]['rgb']['go2_ego'][0,0,0])
            actions = [[.1 + pixel/100.,0.,0.,.3,.1,.2,1.,2.,3.] for _ in range(16)]
            chunk = make_message('ActionChunk',dict(observation_id=self.history.observation_id,
                        chunk_id=f'chunk:{self.history.tick}',start_tick=self.history.tick,
                        action_period_ticks=10,actions=actions),
                        session_id=request['session_id'],episode_id=request['episode_id'],
                        reset_epoch=request['reset_epoch'],message_id=f'chunk:{self.history.tick}')
            self.history.expect_chunk(chunk)
            return chunk
        if method == 'feedback':
            self.history.accept_ack(payload['ack'])
            if payload['observation'] is not None:
                self.observation = payload['observation']
                validate_live_observation(self.observation)
                self.history.observe(self.observation['observation'])
                self.feedback_pixels.append(int(self.observation['samples'][-1]['rgb']['go2_ego'][0,0,0]))
            return {'status':self.history.state}
        return {'status':'ended'}


class DirectClient:
    def __init__(self, policy, runtime):
        self.policy = policy
        self.runtime = runtime
        self.wait_steps = []

    def call(self, method, payload, **identity):
        before = self.runtime.steps
        time.sleep(.001)
        answer = self.policy(dict(method=method,payload=payload,**identity))
        assert self.runtime.steps == before
        self.wait_steps.append(before)
        return answer


def driver(runtime, policy=None, **kwargs):
    policy = policy or PhysicalPolicy()
    events = []
    result = SynchronousDriver(runtime,DirectClient(policy,runtime),session_id='live-test',
             instruction='Push the box',max_groups=kwargs.pop('max_groups',2),
             state_semantics=dict(STATE_SEMANTICS,ground_z=0.,ground_reference='floor'),
             on_event=lambda k,v:events.append((k,v)),**kwargs)
    return result, policy, events


def test_two_physical_groups_then_second_reset_actual_feedback_and_paused_wait():
    runtime = Runtime()
    run, policy, events = driver(runtime)
    run.reset_episode('first',policy_seed=7)
    report = run.run_episode()
    assert report['groups']==2 and report['completed_commands']==32
    assert report['simulation_time_ns']==640_000_000
    records = [p for kind,p in events if kind=='execution']
    assert records[0]['sample_ticks']==[40,80,120,160]
    assert records[1]['sample_ticks']==[200,240,280,320]
    assert records[1]['requested']['body']['actions'][0][0] != records[0]['requested']['body']['actions'][0][0]
    assert policy.feedback_pixels[0] != policy.feedback_pixels[1]
    assert all(row['executed'][6:]==[0.,0.,0.] for row in policy.history.records)
    assert all(p['simulation_frozen'] for k,p in events if k=='wait')
    assert all('task.secret' not in sample['root_state'] for sample in policy.observation['samples'])
    run.reset_episode('second',policy_seed=8)
    assert len(policy.history.records)==0 and run.history.completed==()
    assert run.run_episode()['simulation_time_ns']==640_000_000


@pytest.mark.parametrize('terminal_tick',[45,80,160])
def test_terminal_prefix_uses_pre_reset_snapshot_without_fake_feedback(terminal_tick):
    runtime = Runtime(terminal_tick)
    run,policy,events = driver(runtime)
    run.reset_episode('terminal',policy_seed=7)
    original_epoch = run.identity[2]
    report = run.run_episode()
    assert report['task_terminal'] and report['simulation_time_ns']==terminal_tick*2_000_000
    assert report['completed_commands']==terminal_tick//10
    assert runtime.epoch > original_epoch and report['terminal']['reset_epoch']==original_epoch
    assert policy.history.state=='ENDED' and policy.feedback_pixels==[]
    execution = next(p for kind,p in events if kind=='execution')
    assert execution['ack']['body']['completed_count']==terminal_tick//10
    assert sum(row['status']=='not_executed' for row in execution['ack']['body']['commands']) == 16-((terminal_tick+9)//10)


def test_duplicate_chunk_does_not_repeat_physics_conflict_and_stale_rejected():
    runtime = Runtime()
    run,policy,_ = driver(runtime)
    run.reset_episode('dup',policy_seed=0)
    chunk = run._rpc('predict',{'observation_id':run.observation['observation']['message_id']},'predict-once')
    first = run.execute_chunk(chunk)
    assert run.execute_chunk(chunk)['ack']==first['ack'] and runtime.steps==16
    conflict = deepcopy(chunk);conflict['body']['actions'][0][0] += .01
    with pytest.raises(ValueError,match='Conflicting'):run.execute_chunk(conflict)
    run.reset_episode('new',policy_seed=0)
    with pytest.raises(ValueError,match='Stale'):run.execute_chunk(chunk)


def test_live_rgb_roundtrip_and_packet_tamper():
    runtime=Runtime();snapshot=runtime.reset()
    packet=make_observation([snapshot],session_id='s',episode_id='e',reset_epoch=runtime.epoch,
              message_id='o',instruction='Push',executed_history=[],state_semantics={})
    restored=loads(dumps(packet))
    validate_live_observation(restored,expected_capture_ticks=[0])
    assert np.array_equal(restored['samples'][0]['rgb']['go2_ego'],snapshot['rgb']['ego'])
    altered=deepcopy(restored);altered['samples'][0]['rgb']['go2_ego'][0,0,0]=1
    with pytest.raises(ValueError,match='payload'):validate_live_observation(altered)
    altered=deepcopy(restored);altered['samples'][0]['capture_sim_ns']=2
    with pytest.raises(ValueError,match='timing'):validate_live_observation(altered)
    with pytest.raises(ValueError,match='root'):validate_live_observation(restored,require_root_state=True)


def _serve(pipe):
    policy=PhysicalPolicy()
    server=RPCServer(policy,port=0,timeout_s=10.)
    pipe.send(server.address[1]);pipe.close()
    server.serve_forever()


def test_two_process_rpc_full_feedback_loop():
    ctx=multiprocessing.get_context('spawn')
    parent,child=ctx.Pipe(duplex=False)
    process=ctx.Process(target=_serve,args=(child,));process.start();child.close()
    try:
        assert parent.poll(15.)
        port=parent.recv()
        runtime=Runtime()
        run=SynchronousDriver(runtime,RPCClient(port=port,timeout_s=15.),session_id='two-process',
               instruction='Push',max_groups=2)
        run.reset_episode('first',policy_seed=17)
        report=run.run_episode()
        assert report['completed_commands']==32 and report['simulation_time_ns']==640_000_000
        run.reset_episode('second',policy_seed=18)
        assert run.run_episode()['completed_commands']==32
    finally:
        process.terminate();process.join(10.);parent.close()


def request(method='reset',request_id='r',epoch=1,payload=None):
    return dict(protocol='qlm-live-v1',method=method,request_id=request_id,
                session_id='s',episode_id='e',reset_epoch=epoch,payload=payload or {})


def test_rpc_retries_conflicts_expiry_stale_and_error_do_not_repeat_mutation():
    called=[]
    def handler(req):
        called.append(req['request_id'])
        if req['request_id']=='error':raise RuntimeError('mutated then failed')
        return {'id':req['request_id']}
    with RPCServer(handler,port=0,max_cached_bytes=50) as server:
        reset=request();assert server.dispatch(reset)==server.dispatch(reset)
        assert called==['r']
        conflict=deepcopy(reset);conflict['payload']={'different':True}
        with pytest.raises(ProtocolError,match='Conflicting'):server.dispatch(conflict)
        newer=request('predict','next');server.dispatch(newer)
        with pytest.raises(ProtocolError,match='expired'):server.dispatch(reset)
        failed=request('predict','error');assert not server.dispatch(failed)['ok']
        assert server.dispatch(failed)==server.dispatch(failed) and called.count('error')==1
        server.dispatch(request(epoch=2,request_id='new-reset'))
        with pytest.raises(ProtocolError,match='Stale'):server.dispatch(newer)


def test_transport_bounded_frame_duplicate_json_keys_and_no_pickle():
    a,b=socket.socketpair()
    try:
        a.sendall(struct.pack('!I',1025))
        with pytest.raises(ProtocolError,match='length'):receive(b,limit=1024)
    finally:a.close();b.close()
    with pytest.raises(ProtocolError,match='Duplicate'):loads(b'{"x":1,"x":2}')
    with pytest.raises(ProtocolError):loads(b'\x80\x04pickle')
    with pytest.raises(ProtocolError):dumps(np.zeros((2,2,3),np.float32))


def test_rpc_timeout_retry_keeps_single_handler_mutation():
    import threading
    seen = []
    def handler(req):
        seen.append(req['request_id'])
        time.sleep(.15)
        return {'sampled_once': True}
    with RPCServer(handler,port=0,timeout_s=2.) as server:
        thread=threading.Thread(target=server.serve_forever);thread.start()
        try:
            client=RPCClient(port=server.address[1],timeout_s=.10,retries=1)
            result=client.call('reset',{},request_id='retry',session_id='timeout',episode_id='one',reset_epoch=1)
            assert result=={'sampled_once':True} and seen==['retry']
        finally:
            server.shutdown();thread.join(3.)


def test_nonfinite_json_and_model_free_core_import():
    import subprocess,sys
    with pytest.raises(ProtocolError):loads(b'{"x":1e9999}')
    code="import sys, qlm_bench.live; assert not any(k in sys.modules for k in ('torch','rambo','wam_policy','isaaclab','isaacsim'))"
    subprocess.run([sys.executable,'-c',code],check=True)
