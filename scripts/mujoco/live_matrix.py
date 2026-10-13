"""Run the bounded three-task real-model matrix with owned child processes and fail-closed gates."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import sys


def main():
    root=Path(__file__).resolve().parents[2]
    # A direct script launch must use its own checkout, never a shared editable
    # installation pointing at the retained Isaac source.
    sys.path.insert(0,str(root/'src'))
    from qlm_bench.backends.mujoco.defaults import default_model_set,resolve_model
    p=argparse.ArgumentParser();p.add_argument('--policy-python',required=True);p.add_argument('--sim-python',required=True)
    p.add_argument('--wam-source',required=True);p.add_argument('--model-root',help='Defaults to QLM_MUJOCO_MODEL_ROOT')
    p.add_argument('--prompt-root',required=True);p.add_argument('--checkpoint',required=True)
    p.add_argument('--output',required=True);p.add_argument('--port-base',type=int,default=8913)
    p.add_argument('--ffmpeg',required=True);p.add_argument('--ffprobe',required=True)
    p.add_argument('--render-backend',choices=('egl','osmesa'),default='osmesa')
    p.add_argument('--model-profile-suffix',
                   help='Explicit historical profile override; default is the accepted STEP rendering LOD')
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    reports={}
    # Resolve every resource before starting a costly model service.
    models={task:resolve_model(
        str(Path(a.model_root or os.environ['QLM_MUJOCO_MODEL_ROOT'])/('original-'+task+'-'+a.model_profile_suffix)/'scene.xml')
        if a.model_profile_suffix else None,task_id=task,model_root=a.model_root)
        for task in default_model_set()['tasks']}
    from qlm_bench.backends.factory import load_model_profile
    from qlm_bench.backends.mujoco.defaults import validate_default_identity
    from qlm_bench.backends.mujoco.resources import resource_closure
    for task,model in models.items():
        load_model_profile(model,task_id=task)
        validate_default_identity(model,resource_closure(model,require_portable=True))
    for index,task in enumerate(('push_box','press_button','lift_basket')):
        current=out/task;current.mkdir()
        env=dict(os.environ);env.update(PYTHONPATH=str(Path(a.wam_source)/'src')+':'+str(root/'src'),OMP_NUM_THREADS='4')
        log=(current/'policy.log').open('x')
        service=subprocess.Popen([a.policy_python,'-m','wam_policy.v3.online_service','--config',str(Path(a.prompt_root)/(task+'.inference.json')),
            '--output',str(current/'policy'),'--port',str(a.port_base+index)],env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(180):
                if (current/'policy/ready.json').exists():break
                if service.poll() is not None:raise RuntimeError('Policy startup failed: '+task)
                time.sleep(1)
            else:raise TimeoutError('Policy startup timeout')
            env.update(MUJOCO_GL=a.render_backend,OMP_NUM_THREADS='1')
            with (current/'runtime.log').open('x') as stream:
                subprocess.run([a.sim_python,'-m','qlm_bench.cli','live','--model',str(models[task]),
                    '--checkpoint',a.checkpoint,'--backend','mjwarp','--episodes','2','--seconds','2.02',
                    '--ffmpeg',a.ffmpeg,'--ffprobe',a.ffprobe,'--task',task,
                    '--port',str(a.port_base+index),'--output',str(current/'runtime')],env=env,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=600)
            result=json.loads((current/'runtime/result.json').read_text())
            if not result['passed'] or not result['all_waits_frozen'] or len(result['results'])!=2:
                raise RuntimeError('Physical/model engineering gate failed')
            if any(v['groups']<5 or v['completed_commands']!=101 for v in result['results']):
                raise RuntimeError('Required multichunk/terminal prefix coverage missing')
            media=json.loads((current/'runtime/actual_media/result.json').read_text())
            if not media['passed'] or len(media['episodes'])!=2 or any(not e['terminal_before_reset'] for e in media['episodes']):
                raise RuntimeError('Actual RGB/state/terminal media gate failed')
            reports[task]=result
        finally:
            service.send_signal(signal.SIGINT)
            try:service.wait(timeout=30)
            except subprocess.TimeoutExpired:service.terminate();service.wait(timeout=10)
            log.close()
        events=[json.loads(line) for line in (current/'policy/events.jsonl').read_text().splitlines()]
        if not any(v.get('event')=='eviction' for v in events) or sum(v.get('event')=='reset' for v in events)!=2:
            raise RuntimeError('KV eviction/reset gate missing')
        print('Passed real-model matrix',task,result['rpc_waits'],flush=True)
    (out/'completion.json').write_text(json.dumps({'passed':True,'kind':'bounded_actual_engineering_not_benchmark',
        'tasks':{task:{k:v[k] for k in ('passed','rpc_waits','elapsed_s','all_waits_frozen')} for task,v in reports.items()}},indent=2)+'\n')


if __name__=='__main__':main()
