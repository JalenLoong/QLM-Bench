"""Streaming training environment worker (Stage 1.2 OPSD, Stage 2.2 M-OPD).

One persistent CPU process per learner rank: it takes episode tickets from the shared EpisodeSchedule,
resets a train-pool initial state and drives the episode against the learner's qlm-live-v1 RPC endpoint
until the learner stops it. Native MuJoCo CPU physics, RAMBO on CPU and OSMesa/llvmpipe rendering only.
Heavy imports happen after the CPU GL selection. ``--render-mode`` / ``$QLM_RENDER_MODE``: ``full``
(default) or ``sampled`` (accelerated; the policy receives the same frames).

Sub-commands: prepare-pool, inspect-pool, make-profile, inspect-profile, schedule-init/-snapshot/-restore/-stop, worker.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
import uuid

CPU_ENV = {'MUJOCO_GL':'osmesa','PYOPENGL_PLATFORM':'osmesa','LIBGL_ALWAYS_SOFTWARE':'true',
           'GALLIUM_DRIVER':'llvmpipe','CUDA_VISIBLE_DEVICES':'','HIP_VISIBLE_DEVICES':'',
           'ROCR_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','LP_NUM_THREADS':'1'}
SEMANTICS = {'reference':'root_link','quaternion':'xyzw','velocity_frame':'world',
             'projected_gravity_frame':'body','ground_z':0.,'ground_reference':'push-box-v2-plane-world-z0'}


def select_cpu_environment():
    if 'mujoco' in sys.modules and os.environ.get('MUJOCO_GL')!='osmesa':
        raise RuntimeError('Select OSMesa in a separate worker before importing MuJoCo')
    os.environ.update(CPU_ENV)


def assert_cpu_runtime(runtime):
    if runtime.physics.backend!='native' or runtime.core.device!='cpu':
        raise ValueError('Training requires Native MuJoCo and original RAMBO CPU')
    if any(p.device.type!='cpu' for p in runtime.core.actor.parameters()):
        raise ValueError('RAMBO parameters escaped CPU worker')
    if os.environ.get('MUJOCO_GL')!='osmesa' or 'llvmpipe' not in runtime.renderer.gl_identity['renderer'].lower():
        raise ValueError('OSMesa/llvmpipe renderer required; no GPU fallback')
    return {'physics':'native_cpu','controller':'rambo_cpu','rendering':runtime.renderer.gl_identity,
            'rgb_profile':runtime.rgb_profile}


def normalized(value):
    if isinstance(value,dict):return {k:normalized(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [normalized(v) for v in value]
    if hasattr(value,'shape') and hasattr(value,'tobytes'):
        return {'shape':list(value.shape),'dtype':str(value.dtype),'sha256':hashlib.sha256(value.tobytes()).hexdigest()}
    if hasattr(value,'item'):return value.item()
    return value


def run_worker(pool_path,pool_sha256,*,rank,world_size,port,output,rpc_timeout_s,
               wall_timeout_s,max_episodes=1201,segment=None,allow_diagnostic=False,
               training_profile=None,schedule_db=None,render_mode=None):
    if not 0<=rank<world_size or world_size not in (1,2,4,8):raise ValueError('Invalid training rank')
    if any(not math.isfinite(x) or x<=0 for x in (rpc_timeout_s,wall_timeout_s)):
        raise ValueError('Explicit finite worker timeouts required')
    if type(max_episodes) is not int or max_episodes<1:raise ValueError('Bounded episode budget required')
    select_cpu_environment()
    from qlm_bench.training_env.pool import load,sha,under
    from qlm_bench.training_env.schedule import read_profile,EpisodeSchedule
    if sha(pool_path)!=pool_sha256:raise ValueError('--pool-sha256 does not match the selected pool manifest')
    pool=load(pool_path,allow_diagnostic=allow_diagnostic)
    if not all((training_profile,schedule_db,segment)):
        raise ValueError('--training-profile, --schedule-db and --segment are required')
    selected_profile=read_profile(training_profile,pool_sha256)
    profile_sha=sha(training_profile)
    from qlm_bench.backends.mujoco.runtime import apply_render_mode,render_mode as select_render_mode
    render_mode=select_render_mode(render_mode)
    import torch
    torch.set_num_threads(1)
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.live import RPCClient,SynchronousDriver
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    schedule=EpisodeSchedule(schedule_db,selected_profile)
    records={r['episode_uid']:r for r in pool['episodes']}
    client=RPCClient(port=port,timeout_s=rpc_timeout_s)
    root=Path(pool_path).parent
    start=time.monotonic();results=[];freeze_waits=0;all_frozen=True
    def event(kind,payload):
        nonlocal freeze_waits,all_frozen
        if kind=='wait':
            freeze_waits+=1;all_frozen &= bool(payload['simulation_frozen'])
        with (output/'events.jsonl').open('a') as f:
            f.write(json.dumps({'event':kind,**normalized(payload)},allow_nan=False)+'\n')
    def expired(*_):raise TimeoutError('CPU rollout worker wall-time budget exhausted')
    use_alarm=hasattr(signal,'setitimer') and __import__('threading').current_thread() is __import__('threading').main_thread()
    old_handler=None
    if use_alarm:
        old_handler=signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,wall_timeout_s)
    try:
        for episode_index in range(max_episodes):
            if time.monotonic()-start>=wall_timeout_s:expired()
            ticket=schedule.reserve(segment,rank,episode_index)
            if ticket['status']!='reserved':raise ValueError('Episode ticket already used; physical replay is forbidden')
            entry=records[ticket['episode_uid']];resource=pool['resources'][entry['resource_identity']]
            horizon=selected_profile['training_horizons_s'][entry['task']]
            runtime=None
            try:
                runtime=create_runtime(entry['task'],'native',model_path=under(root,resource['entrypoint']),
                    checkpoint=under(root,pool['controller']),device='cpu',seed=entry['seed'],trace_only=False,
                    rgb_profile='dual-rgb-360p-v1',profile_override={**entry['goal_overlay'],'horizon_s':horizon})
                apply_render_mode(runtime,render_mode)
            except BaseException:
                schedule.cancel(ticket['id']);raise
            try:
                runtime_identity=assert_cpu_runtime(runtime)
                if runtime.physics.model_identity!=entry['resource_identity'] or runtime.profile['instruction']!=entry['instruction']:
                    raise ValueError('Runtime scene/instruction differs from the train-pool reset')
                initial=runtime.reset(initial_state=entry['initial_state'])
                # New runtime may restart physical epochs; never reuse the prior session ID.
                session=f'train-{segment}-{rank}-{episode_index}'
                driver=SynchronousDriver(runtime,client,session_id=session,instruction=entry['instruction'],
                    task_id=entry['task'],task_version=entry['task_version'],timeout_s=rpc_timeout_s,
                    state_semantics=SEMANTICS,on_event=event,max_groups=math.ceil(horizon/.32))
                driver.reset_episode(entry['episode_uid']+f'-visit-{episode_index}',
                    policy_seed=42+rank+world_size*episode_index,initial_snapshot=initial,
                    extensions={'training':{'train_pool_sha256':pool_sha256,'training_profile_sha256':profile_sha,
                        'train_episode_uid':entry['episode_uid'],'segment':segment,'schedule_ticket':ticket['id'],
                        'render_mode':render_mode,'runtime':runtime_identity}})
                schedule.confirm(ticket['id'])
                result=driver.run_episode(feedback_hook=lambda response: bool(response.get('stop_after_feedback',False)))
                schedule.finish(ticket['id'],natural=bool(result['task_terminal']))
                result.update(training_reset_uid=entry['episode_uid'],runtime=runtime_identity,
                              task=entry['task'],training_horizon_s=horizon,schedule_ticket=ticket['id'],
                              training_outcome='training_timeout' if result['termination_reason']=='timeout' else result['termination_reason'],
                              stream_id=f'train-{rank}',segment=segment,diagnostic_only=allow_diagnostic,render_mode=render_mode)
                results.append(result)
                with (output/'episodes.jsonl').open('a') as f:f.write(json.dumps(normalized(result),allow_nan=False)+'\n')
                if result['training_stopped']:
                    if not freeze_waits or not all_frozen:raise RuntimeError('Simulation was not frozen during every learner wait')
                    report={'schema':'qlm-training-worker-result-v1','training_budget_end':result['training_budget_end'],
                        'stop_reason':result['training_stop_reason'],
                        'episodes':len(results),'freeze_waits':freeze_waits,'all_waits_frozen':all_frozen,
                        'rank':rank,'segment':segment,'elapsed_s':time.monotonic()-start,'diagnostic_only':allow_diagnostic,
                        'render_mode':render_mode}
                    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
                    return report
                if not result['task_terminal']:
                    raise RuntimeError('Engineering group budget cannot replace real task terminal')
            except BaseException:
                schedule.cancel(ticket['id']);raise
            finally:
                if runtime is not None:runtime.close()
        raise RuntimeError('Worker episode safety budget exhausted before learner stop')
    except BaseException as exc:
        (output/'failure.json').write_text(json.dumps({'error':type(exc).__name__,'message':str(exc),
                'elapsed_s':time.monotonic()-start,'rank':rank,'segment':segment},indent=2)+'\n')
        raise
    finally:
        if use_alarm:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old_handler)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);commands=p.add_subparsers(dest='command',required=True)
    prepare=commands.add_parser('prepare-pool');prepare.add_argument('--snapshot',required=True)
    prepare.add_argument('--output',required=True);prepare.add_argument('--controller-root',required=True)
    prepare.add_argument('--resource-map')
    check=commands.add_parser('inspect-pool');check.add_argument('--pool',required=True)
    run=commands.add_parser('worker');run.add_argument('--pool',required=True);run.add_argument('--pool-sha256',required=True)
    run.add_argument('--rank',required=True,type=int);run.add_argument('--world-size',required=True,type=int)
    run.add_argument('--port',required=True,type=int);run.add_argument('--output',required=True)
    run.add_argument('--rpc-timeout-s',required=True,type=float);run.add_argument('--wall-timeout-s',required=True,type=float)
    run.add_argument('--max-episodes',type=int,default=1201);run.add_argument('--segment',required=True)
    run.add_argument('--training-profile',required=True);run.add_argument('--schedule-db',required=True)
    run.add_argument('--diagnostic',action='store_true')
    run.add_argument('--render-mode',choices=('full','sampled'),default=None,
                     help='full (default): render every command + observer; sampled: only the 80 ms sample points')
    for name in ('make-profile','inspect-profile','schedule-init','schedule-snapshot','schedule-restore','schedule-stop'):
        c=commands.add_parser(name)
        c.add_argument('--profile',required=True)
        if name in ('make-profile','inspect-profile','schedule-init'):c.add_argument('--pool',required=True);c.add_argument('--diagnostic',action='store_true')
        if name=='make-profile':c.add_argument('--tasks');c.add_argument('--max-active-per-task',type=int,default=2)
        if name.startswith('schedule-'):c.add_argument('--db',required=True)
        if name in ('schedule-init','schedule-restore'):c.add_argument('--segment',required=True)
        if name=='schedule-restore':c.add_argument('--input',required=True)
    a=p.parse_args(argv)
    if a.command in ('make-profile','inspect-profile') or a.command.startswith('schedule-'):
        from qlm_bench.training_env.schedule import prepare_profile,read_profile,EpisodeSchedule
        from qlm_bench.training_env.pool import sha,read,load
        if a.command=='make-profile':result=prepare_profile(a.pool,a.profile,diagnostic=a.diagnostic,
            tasks=a.tasks.split(',') if a.tasks else None,max_active_per_task=a.max_active_per_task)
        else:
            pool_sha=sha(a.pool) if hasattr(a,'pool') else read(a.profile)['train_pool_sha256']
            selected=read_profile(a.profile,pool_sha)
            if a.command=='inspect-profile':
                pool=load(a.pool,allow_diagnostic=a.diagnostic)
                result={'profile':selected,'profile_sha256':sha(a.profile),
                        'pool':{'episodes':len(pool['episodes']),'tasks':pool['tasks']}}
            elif a.command=='schedule-init':
                obj=EpisodeSchedule.create(a.db,selected,load(a.pool,allow_diagnostic=a.diagnostic),a.segment);result=obj.snapshot()
            else:
                obj=EpisodeSchedule(a.db,selected)
                if a.command=='schedule-restore':obj.restore(read(a.input),a.segment)
                elif a.command=='schedule-stop':obj.stop()
                result=obj.snapshot()
        print(json.dumps(result,allow_nan=False));return

    if a.command=='prepare-pool':
        from qlm_bench.training_env.pool import prepare as prepare_pool,read
        return print(json.dumps(prepare_pool(a.snapshot,a.output,a.controller_root,
                          model_map=read(a.resource_map) if a.resource_map else None)))
    if a.command=='inspect-pool':
        from qlm_bench.training_env.pool import load
        return print(json.dumps({'episodes':len(load(a.pool)['episodes']),'passed':True}))
    print(json.dumps(run_worker(a.pool,a.pool_sha256,rank=a.rank,world_size=a.world_size,port=a.port,
        output=a.output,rpc_timeout_s=a.rpc_timeout_s,wall_timeout_s=a.wall_timeout_s,
        max_episodes=a.max_episodes,segment=a.segment,allow_diagnostic=a.diagnostic,
        training_profile=a.training_profile,schedule_db=a.schedule_db,render_mode=a.render_mode)))


if __name__=='__main__':main()
