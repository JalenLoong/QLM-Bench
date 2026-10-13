"""Actual two-world original-scene RGB/reset isolation; no dataset admission."""
import argparse
import json
from pathlib import Path
import traceback

import numpy as np
import torch
from PIL import Image

from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.render import RenderMirror
from qlm_bench.backends.mujoco.tasks import TaskState
from qlm_bench.controllers.rambo.core import RAMBOCore


def main():
    p=argparse.ArgumentParser()
    for key in ('model','checkpoint','output'):p.add_argument('--'+key,required=True)
    p.add_argument('--backend',choices=('native','mjwarp'),required=True);a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);mirrors=[];result={}
    try:
        torch.set_num_threads(1)
        physics=MuJoCoPhysics(a.model,count=2,backend=a.backend)
        device='cpu' if a.backend=='native' else 'cuda:0'
        core=RAMBOCore(physics,a.checkpoint,device=device,case_seeds=[42,43])
        task=TaskState(physics,json.loads(Path(a.model).with_suffix('.task.json').read_text()))
        mirrors=[RenderMirror(a.model,world_id=i) for i in range(2)]
        for control in range(40):
            if control%2==0:
                core.submit([[.1,0.,0.,.1934,.142,.05,0.,0.,0.],[-.1,0.,0.,.1934,.142,.05,0.,0.,0.]])
            residual=core.begin_control()
            for _ in range(5):physics.step(core.motor_effort().cpu().numpy())
            core.end_control(residual)
        snapshots=[physics.snapshot(i) for i in range(2)]
        images=[mirrors[i].capture(snapshots[i],terminal=True) for i in range(2)]
        if np.array_equal(snapshots[0]['qpos'],snapshots[1]['qpos']):raise ValueError('Worlds did not diverge under different commands')
        if np.array_equal(images[0]['rgb']['d435i_rgb_task'],images[1]['rgb']['d435i_rgb_task']):raise ValueError('World images were mixed or stale')
        for i,capture in enumerate(images):
            for camera,rgb in capture['rgb'].items():Image.fromarray(rgb).save(out/f'world{i}-{camera}.png')
        try:mirrors[0].capture(snapshots[1])
        except ValueError:pass
        else:raise AssertionError('Cross-world render snapshot accepted')
        before_rng=core.case_rng.identity();before_history=core._obs_history[1].clone()
        physics.reset([0]);core.reset(torch.tensor([0],device=device),case_seeds=[100]);task.reset([0])
        after=physics.snapshot(1)
        for name in ('qpos','qvel'):np.testing.assert_array_equal(after[name],snapshots[1][name])
        torch.testing.assert_close(before_history,core._obs_history[1],rtol=0,atol=0)
        for stream in before_rng['state_sha256']:
            assert before_rng['state_sha256'][stream][1]==core.case_rng.identity()['state_sha256'][stream][1]
        repeated=mirrors[1].capture(after,terminal=True)
        differences={k:int(np.abs(v.astype(int)-images[1]['rgb'][k].astype(int)).max()) for k,v in repeated['rgb'].items()}
        if max(differences.values())>1:raise ValueError('Unselected world RGB changed on another world reset')
        reset=mirrors[0].capture(physics.snapshot(0),terminal=True)
        for camera,rgb in reset['rgb'].items():Image.fromarray(rgb).save(out/f'reset-world0-{camera}.png')
        if physics.ticks.tolist()!=[0,200]:raise ValueError('Subset reset changed the wrong clock')
        result={'passed':True,'backend':a.backend,'worlds':2,'different_command_states_and_RGB':True,
                'cross_world_snapshot_rejected':True,'other_world_state_history_rng_unchanged':True,
                'other_world_RGB_max_abs_255':differences,'clocks_after_reset':physics.ticks.tolist(),
                'resource_identity':physics.model_identity,'GL':mirrors[0].gl_identity,'formal_demonstration':False}
        physics.close()
    except BaseException as error:
        result={'passed':False,'error':repr(error),'traceback':traceback.format_exc()};raise
    finally:
        for mirror in mirrors:mirror.close()
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
