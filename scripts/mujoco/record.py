"""Explicit short P2 diagnostic recording entrypoint; no formal collection slots."""
import argparse
import json
from pathlib import Path
import subprocess
import traceback


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--checkpoint',required=True)
    p.add_argument('--backend',choices=('native','mjwarp'),required=True);p.add_argument('--output',required=True)
    p.add_argument('--ffmpeg',required=True);p.add_argument('--ffprobe',required=True)
    p.add_argument('--commands',type=int,default=101);p.add_argument('--seed',type=int,default=42)
    p.add_argument('--expert-profile');a=p.parse_args()
    if not 1<=a.commands<=1200:raise ValueError('P2 engineering capture is bounded to24 simulation seconds')
    root=Path(__file__).resolve().parents[2]
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    (out/'attempt.json').write_text(json.dumps({'work_id':'QLM-SIM-005','kind':'diagnostic_collection','args':vars(a)},indent=2)+'\n')
    r=None;result=None;phase='startup'
    try:
        import torch
        from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
        from qlm_bench.backends.mujoco.recording import record_engineering
        torch.set_num_threads(1);torch.manual_seed(a.seed)
        r=MuJoCoRuntime(a.model,a.checkpoint,backend=a.backend,device='cpu' if a.backend=='native' else 'cuda:0',seed=a.seed)
        phase='collection'
        result=record_engineering(r,a.output,ffmpeg=a.ffmpeg,ffprobe=a.ffprobe,commands=a.commands,
                                 expert_profile=json.loads(Path(a.expert_profile).read_text()) if a.expert_profile else None,
                                 source_commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip())
        print(json.dumps(result),flush=True)
        phase='close';owned,r=r,None;owned.close()
    except BaseException as error:
        failure={'passed':False,'stage':phase,
                 'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc(),
                 'prior_result':result,'publication_status':'local_only','eligible_demonstration':False}
        (out/'failure.json').write_text(json.dumps(failure,indent=2)+'\n')
        (out/'result.json').write_text(json.dumps(failure,indent=2)+'\n')
        raise
    finally:
        if r is not None:r.close()
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
