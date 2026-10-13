"""Bounded MuJoCo connection to the existing WAM/QLM synchronous live protocol."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import subprocess
import shutil
import math


from qlm_bench.live import RPCClient,SynchronousDriver
from .defaults import add_model_arguments,resolve_model


def execution_budget(episodes,seconds,max_groups=None):
    """Execution guard covers the horizon; this does not change model window units."""
    if not 1<=episodes<=2 or not math.isfinite(seconds) or not .32<seconds<=24:
        raise ValueError('Local engineering episodes require .32<seconds<=24 and1..2episodes')
    required=math.ceil(seconds/.32)
    if max_groups is not None and (type(max_groups) is not int or max_groups<required):
        raise ValueError('Execution group budget is too small for the declared horizon')
    return required if max_groups is None else max_groups


def main(argv=None):
    p=argparse.ArgumentParser();add_model_arguments(p);p.add_argument('--checkpoint',required=True)
    p.add_argument('--output',required=True);p.add_argument('--port',type=int,required=True)
    p.add_argument('--backend',choices=('native','mjwarp'),default='mjwarp');p.add_argument('--episodes',type=int,default=2)
    p.add_argument('--seconds',type=float,default=2.02);p.add_argument('--max-groups',type=int,
        help='Execution guard; defaults to enough16-command groups for the horizon,independent of model window')
    p.add_argument('--ffmpeg',required=True);p.add_argument('--ffprobe',required=True)
    p.add_argument('--seed',type=int,default=42);p.add_argument('--render-backend',choices=('egl','osmesa'))
    a=p.parse_args(argv)
    a.max_groups=execution_budget(a.episodes,a.seconds,a.max_groups)
    a.model=str(resolve_model(a.model,task_id=a.task,model_root=a.model_root))
    import os
    if a.render_backend:os.environ['MUJOCO_GL']=a.render_backend
    import numpy as np
    import torch
    from qlm_bench.backends.factory import create_runtime,load_model_profile
    from qlm_bench.live.media import ActualRGBRecorder
    scene=load_model_profile(a.model,task_id=a.task)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);torch.set_num_threads(1);torch.manual_seed(a.seed)
    # Preserve full event JSONL while retaining only bounded aggregate counters.
    # Full-history receipts can otherwise grow quadratically during a24s run.
    wait_count=0;all_waits_frozen=True
    def normalize(v):
        if isinstance(v,np.ndarray):return {'shape':list(v.shape),'dtype':str(v.dtype),'sha256':hashlib.sha256(v.tobytes()).hexdigest()}
        if isinstance(v,dict):return {k:normalize(x) for k,x in v.items()}
        if isinstance(v,(tuple,list)):return [normalize(x) for x in v]
        return v
    def event(kind,payload):
        nonlocal wait_count,all_waits_frozen
        v={'event':kind,**normalize(payload)}
        if kind=='wait':
            wait_count+=1;all_waits_frozen=all_waits_frozen and bool(v['simulation_frozen'])
        with (out/'events.jsonl').open('a') as f:f.write(json.dumps(v,allow_nan=False)+'\n')
    r=create_runtime(scene['task_id'],a.backend,model_path=a.model,checkpoint=a.checkpoint,seed=a.seed,device='cuda:0' if a.backend=='mjwarp' else 'cpu')
    r.profile['horizon_s']=a.seconds;r.task.profile['horizon_s']=a.seconds
    media=ActualRGBRecorder(out/'actual_media',ffmpeg=a.ffmpeg,ffprobe=a.ffprobe,observer=r.renderer.observer_clip is not None,
        identity={'task':scene['task_id'],'scene_profile':scene,'resources':r.physics.resource_profile,'GL':r.renderer.gl_identity,'scope':'actual_model_engineering_not_demonstration'})
    r.on_observation=media.observe;r.on_terminal=media.seal_terminal
    client=RPCClient(port=a.port,timeout_s=600.)
    semantics={'reference':'root_link','quaternion':'xyzw','velocity_frame':'world',
               'projected_gravity_frame':'body','ground_z':0.0,'ground_reference':'push-box-v2-plane-world-z0'}
    driver=SynchronousDriver(r,client,session_id='p2-'+r.task.task,instruction=r.profile['instruction'],
        task_id=r.task.task,task_version=r.profile['asset_profile'],state_semantics=semantics,
        on_event=event,max_groups=a.max_groups)
    start=time.monotonic();results=[]
    (out/'attempt.json').write_text(json.dumps({'kind':'actual_mujoco_engineering_not_benchmark','args':vars(a),
        'source_commit':subprocess.check_output(['git','-C',str(Path(__file__).resolve().parents[4]),'rev-parse','HEAD'],text=True).strip(),
        'implementation_sha256':{str(p.relative_to(Path(__file__).resolve().parents[4])):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('src/qlm_bench/controllers/rambo','src/qlm_bench/backends/mujoco')
            for p in (Path(__file__).resolve().parents[4]/folder).rglob('*') if p.suffix in ('.py','.json')},
        'scene_profile':r.profile,'checkpoint':'original Isaac SFT interface diagnostic; not new MuJoCo SFT',
        'ground_semantics':'same worldZ0 coordinate definition as original frozen normalizer; separate scene identity'},indent=2)+'\n')
    source_root=Path(__file__).resolve().parents[4]
    from qlm_bench.collection.orchestrator import source_identity
    copied={}
    for path in sorted(p for p in (source_root/'src/qlm_bench').rglob('*') if p.suffix in ('.py','.json')):
        name=str(path.relative_to(source_root));dest=out/'source_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,dest);copied[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (out/'source_snapshot/identity.json').write_text(json.dumps({'source':source_identity(source_root),'files':copied},indent=2)+'\n')
    try:
        for index in range(a.episodes):
            driver.reset_episode('p2-episode-'+str(index),policy_seed=a.seed+index)
            results.append(driver.run_episode())
        if not wait_count or not all_waits_frozen:raise ValueError('Physics freeze gate failed')
        if any(not v['task_terminal'] or v['termination_reason'] not in ('task_success','robot_fall','timeout') for v in results):
            raise ValueError('Rollout ended without a physical success/fall/timeout terminal')
        result={'passed':True,'results':results,'rpc_waits':wait_count,'all_waits_frozen':True,
                'elapsed_s':time.monotonic()-start,'task_success_not_required':True,'actual_media':'actual_media/result.json','case_seed':a.seed}
    except BaseException as error:
        failure={'type':type(error).__name__,'message':str(error)}
        try:failure['terminal']=normalize(r.abort('engineering_runtime_error'))
        except BaseException as abort_error:failure['abort_error']=repr(abort_error)
        (out/'failure.json').write_text(json.dumps(failure,indent=2)+'\n');raise
    finally:
        try:media.close()
        finally:r.close()
    (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print({k:result[k] for k in ('passed','rpc_waits','all_waits_frozen','elapsed_s')},flush=True)


if __name__=='__main__':main()
