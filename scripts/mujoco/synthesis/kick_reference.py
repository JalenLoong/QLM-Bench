"""Bounded original-RAMBO Kick reference; failed attempts retain only light logs."""
import argparse,json,subprocess,time
from pathlib import Path
import numpy as np
import torch
from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
from qlm_bench.backends.mujoco.kick_reference import KickExecutor,DEFAULT
from qlm_bench.backends.mujoco.trace import collect_trace,sha,write_json

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--output',required=True);p.add_argument('--config');p.add_argument('--seed',type=int,default=42);a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);torch.set_num_threads(1)
    config=json.loads(Path(a.config).read_text()) if a.config else DEFAULT
    entry={'kind':'reference development not formal','work_id':'QLM-DATA-023','native_trace_profile':'native-cpu-original-rambo-v1','entry_sha256':sha(__file__),'recipe_config':config,'checkpoint_sha256':sha(a.checkpoint),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[3],text=True).strip(),'started_unix_s':time.time(),'WAM_execution':'not_run'}
    write_json(out/'attempt.json',entry);rt=MuJoCoRuntime(a.model,a.checkpoint,backend='native',device='cpu',trace_only=True,seed=a.seed)
    class Logged(KickExecutor):
        def reset(self,runtime,scene):super().reset(runtime,scene);self.last_second=-1
        def command(self):
            values,diagnostic=super().command();sec=int(rt.physics.ticks[0])//500
            if sec!=self.last_second:
                self.last_second=sec;print(json.dumps({'sim_s':sec,'phase':diagnostic['phase'],'ball':rt.task.geometric_center(0).tolist(),'base':rt.core.robot.position[0].cpu().tolist(),'FL':self.actual_world_point().tolist(),'progress':rt.task.progress(0)}),flush=True)
            return values,diagnostic
    try:
        s=rt.physics.snapshot();scene={'candidate_id':out.name,'task_id':'kick_ball_to_goal','seed':a.seed,'initial_state':{'schema':'qlm-mujoco-initial-state-v1','model_identity':s['model_identity'],'qpos':s['qpos'].tolist(),'qvel':s['qvel'].tolist()},'asset_id':rt.profile['asset_id'],'appearance_preset':rt.profile.get('appearance_preset','ap_00'),'difficulty':'reference_development','model':str(Path(a.model).resolve())}
        result=collect_trace(rt,Logged(config),scene,out/'trace',batch_identity=entry,reference=True,quality_policy='evidence-review-v1');write_json(out/'result.json',result);print(json.dumps(result),flush=True)
        if not result['passed']:raise SystemExit(2)
    finally:rt.close()
