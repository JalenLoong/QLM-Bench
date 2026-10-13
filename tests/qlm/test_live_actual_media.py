"""Actual callback/video/terminal/reset proof, without a learned-model claim."""
import json
import os
from pathlib import Path
import pytest


@pytest.mark.skipif(not os.environ.get('QLM_MUJOCO_TASK') or os.environ.get('MUJOCO_GL') not in ('egl','osmesa'),
                    reason='Explicit actual scene and renderer required')
def test_two_actual_episodes_have_owned_media_and_frozen_controller(tmp_path):
    import torch
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.live.media import ActualRGBRecorder
    from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
    torch.set_num_threads(1)
    runtime=create_runtime('push_box','native',model_path=os.environ['QLM_MUJOCO_TASK'],
                           checkpoint=os.environ['QLM_RAMBO_CHECKPOINT'],device='cpu',seed=91)
    runtime.profile['horizon_s']=.12
    media=ActualRGBRecorder(tmp_path/'media',ffmpeg=os.environ['QLM_FFMPEG'],ffprobe=os.environ['QLM_FFPROBE'],
                            identity={'kind':'actual_test_fixture_not_policy_evaluation'})
    runtime.on_observation=media.observe;runtime.on_terminal=media.seal_terminal
    try:
        for episode in range(2):
            runtime.reset();before=runtime.freeze_token()
            for _ in range(3):runtime.state()
            assert before==runtime.freeze_token()
            for command in range(6):
                result=runtime.step(prepare_command([0.,0.,0.,.1934,.142,.05,0.,0.,0.],str(command),command*10))
            assert result['terminal'] is not None
    finally:
        try:media.close()
        finally:runtime.close()
    report=json.loads((tmp_path/'media/result.json').read_text())
    assert report['passed'] and len(report['episodes'])==2
    for episode in report['episodes']:
        assert episode['terminal_before_reset'] and episode['actual_observation_boundaries']==7
        assert episode['videos']['ego']['frames']==7 and episode['videos']['task_centric']['frames']==7
        assert episode['videos']['observer']['frames']==4
        folder=tmp_path/'media'/f"epoch_{episode['reset_epoch']:06d}"
        assert (folder/'terminal-ego.png').is_file() and (folder/'terminal-observer.png').is_file()


def test_public_backend_discovery_and_help_do_not_import_simulators():
    import subprocess,sys
    code='''import sys
from qlm_bench.backends.factory import backend_binding
assert backend_binding('push_box','mjwarp')['status']=='engineering'
from qlm_bench.cli import main
try:main(['live','--backend','native','--help'])
except SystemExit as e:assert e.code==0
assert not any(k in sys.modules for k in ('torch','mujoco','isaaclab','isaacsim','wam_policy'))
'''
    subprocess.run([sys.executable,'-c',code],check=True,capture_output=True)
