"""Actual small-step recorder tests with explicit injected failure boundaries.

These are failure-handling fixtures, not task success or controller evaluations.
"""
import copy
import json
import os
from pathlib import Path
import subprocess

import pytest

pytestmark=pytest.mark.skipif(not os.environ.get('QLM_MUJOCO_TASK') or os.environ.get('MUJOCO_GL') not in ('egl','osmesa'),
    reason='Explicit original task, checkpoint and rendering backend required')


@pytest.fixture
def runtime():
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    import torch
    torch.set_num_threads(1);torch.manual_seed(42)
    value=MuJoCoRuntime(os.environ['QLM_MUJOCO_TASK'],os.environ['QLM_RAMBO_CHECKPOINT'],backend='native',device='cpu')
    try:yield value
    finally:value.close()


def record(runtime,output):
    from qlm_bench.backends.mujoco.recording import record_engineering
    root=Path(__file__).resolve().parents[2]
    return record_engineering(runtime,output,ffmpeg=os.environ['QLM_FFMPEG'],ffprobe=os.environ['QLM_FFPROBE'],
        commands=2,source_commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip())


def capture(output):
    path=next((output/'raw').glob('*/capture.json'))
    return json.loads(path.read_text()),path.parent


def test_actual_partial_interval_is_preserved_without_canonical(runtime,tmp_path,monkeypatch):
    def partial(prepared):
        runtime.lifecycle.submit(prepared,int(runtime.physics.ticks[0]))
        runtime.current=copy.deepcopy(runtime.lifecycle.current_command)
        runtime.core.submit([prepared['filtered']]);residual=runtime.core.begin_control()
        for _ in range(5):runtime.physics.step(runtime.core.motor_effort().numpy())
        runtime.core.end_control(residual);runtime.lifecycle.confirm_control(int(runtime.physics.ticks[0]))
        runtime.current=copy.deepcopy(runtime.lifecycle.current_command);runtime.cached=None
        terminal=runtime.abort('test_partial_at10ms')
        return {'command':runtime.current,'completed_interval':False,'terminal':terminal}
    monkeypatch.setattr(runtime,'step',partial)
    out=tmp_path/'partial';result=record(runtime,out);cap,raw=capture(out)
    assert not result['passed'] and not (out/'canonical').exists()
    assert cap['terminal']['physics_step']==5 and cap['terminal']['partial_interval']
    assert cap['command_attempts'][0]['status']=='partial'
    assert cap['terminal']['actual_images']['ego'] and (raw/'terminal/ego.png').is_file()
    assert (raw/'terminal/observer.png').is_file()
    assert cap['commands']==[] and len(cap['boundaries'])==1


def test_render_failure_keeps_actual_confirmed_execution(runtime,tmp_path,monkeypatch):
    original=runtime.renderer.capture
    def fail(snapshot,**kwargs):
        if snapshot['physics_step']>=10:raise RuntimeError('injected renderer failure after execution')
        return original(snapshot,**kwargs)
    monkeypatch.setattr(runtime.renderer,'capture',fail)
    out=tmp_path/'render_error';result=record(runtime,out);cap,raw=capture(out)
    assert not result['passed'] and not (out/'canonical').exists()
    assert cap['terminal']['physics_step']==10 and cap['terminal']['rgb_unavailable']
    assert cap['executed_history'][0]['status']=='completed'
    assert cap['current_command']['status']=='completed'
    assert (raw/'capture-state.json').is_file() and cap['errors']


def test_encoder_failure_cannot_drop_terminal_or_admit_canonical(runtime,tmp_path,monkeypatch):
    from qlm_bench.backends.mujoco.video import VideoSink
    original=VideoSink.close
    def fail(self):
        original(self)
        raise RuntimeError('injected encoder finalization failure')
    monkeypatch.setattr(VideoSink,'close',fail)
    out=tmp_path/'encoder_error';result=record(runtime,out);cap,raw=capture(out)
    assert not result['passed'] and not (out/'canonical').exists()
    assert cap['terminal']['physics_step']==20 and len(cap['commands'])==2
    assert any(e['stage']=='encoder_close' for e in cap['errors'])
    assert cap['terminal']['actual_images']['ego'] and (raw/'events.jsonl').is_file()


def test_explicit_abort_keeps_completed_prefix_and_diagnostic_failure(runtime,tmp_path,monkeypatch):
    original=runtime.step
    def stop(prepared):
        result=original(prepared)
        result['terminal']=runtime.abort('test_explicit_abort')
        return result
    monkeypatch.setattr(runtime,'step',stop)
    out=tmp_path/'abort';result=record(runtime,out);cap,raw=capture(out)
    assert result['passed']  # Transport is valid; it is still a failed diagnostic episode.
    assert cap['status']=='failure' and cap['diagnostic_only']
    assert cap['terminal']['reason']=='test_explicit_abort' and len(cap['commands'])==1
    assert cap['terminal']['physics_step']==10 and (raw/'terminal/observer.png').is_file()
    contract=json.loads((out/'canonical/meta/contract.json').read_text())
    assert contract['diagnostic_only'] and contract['episodes'][0]['status']=='failure'
