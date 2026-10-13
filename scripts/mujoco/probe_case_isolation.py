"""Actual two-world controller/contact/RNG isolation; no images or formal data."""
import argparse
import hashlib
import json
from pathlib import Path
import traceback

import numpy as np
import torch

from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.controllers.rambo.core import RAMBOCore


def main():
    p=argparse.ArgumentParser()
    for name in ('model','checkpoint','output'):p.add_argument('--'+name,required=True)
    p.add_argument('--backend',choices=('native','mjwarp'),required=True);a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);result={}
    torch.set_num_threads(1)
    try:
        physics=MuJoCoPhysics(a.model,count=2,backend=a.backend)
        device='cpu' if a.backend=='native' else 'cuda:0'
        core=RAMBOCore(physics,a.checkpoint,device=device,case_seeds=[42,43])
        measured=[]
        for control in range(100):
            action=core.begin_control()
            for _ in range(5):physics.step(core.motor_effort().cpu().numpy())
            core.end_control(action)
            measured.append(physics.contact_history_tick.tolist())
            history=physics.contact_history.copy();calls=physics.transfer_metrics['calls']
            for _ in range(4):physics.read(device);physics.snapshot(0);physics.snapshot(1)
            np.testing.assert_array_equal(history,physics.contact_history)
            assert calls==physics.transfer_metrics['calls']
        np.testing.assert_array_equal(np.asarray(measured),np.repeat(np.arange(5,501,5)[:,None],2,axis=1))
        other=physics.snapshot(1);other_history=core._obs_history[1].clone();rng_before=core.case_rng.identity()
        reference=torch.Generator(device='cpu');reference.set_state(core.case_rng.streams['qp_regularizer'][1].get_state())
        physics.reset([0]);core.reset(torch.tensor([0],device=device),case_seeds=[999])
        after=physics.snapshot(1)
        for name in ('qpos','qvel'):np.testing.assert_array_equal(other[name],after[name])
        torch.testing.assert_close(other_history,core._obs_history[1],rtol=0,atol=0)
        for stream in rng_before['state_sha256']:
            assert rng_before['state_sha256'][stream][1]==core.case_rng.identity()['state_sha256'][stream][1]
        for _ in range(10):
            torch.rand(1,generator=reference)
            action=core.begin_control()
            expected=hashlib.sha256(reference.get_state().numpy().tobytes()).hexdigest()
            assert expected==core.case_rng.identity()['state_sha256']['qp_regularizer'][1]
            for _ in range(5):physics.step(core.motor_effort().cpu().numpy())
            core.end_control(action)
        physics.close()
        result={'passed':True,'backend':a.backend,'worlds':2,'source_model':physics.resource_profile,
                'effective_backend_options':physics.backend_options,'case_seeds':[42,43],
                'other_world_state_history_rng_preserved_at_reset':True,'future_other_lane_rng_sequence_preserved':True,
                'contact_history_period_physics_ticks':5,'contact_history_samples':measured,
                'repeated_reads_shift_history':False,'transfer_metrics':physics.transfer_metrics,
                'scope':'actual bounded controller/sensor/cache isolation, not task SR or AMD validation'}
    except BaseException as error:
        result={'passed':False,'error':repr(error),'traceback':traceback.format_exc()};raise
    finally:(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
