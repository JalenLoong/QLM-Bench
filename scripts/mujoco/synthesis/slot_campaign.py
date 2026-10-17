"""Bounded ten-slot campaign scheduling, reusing the render-only recovery queue."""
import concurrent.futures as futures
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

from qlm_bench.backends.mujoco.trace import write_json,sha


def memory():
    d={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines()}
    return {'available':d['MemAvailable'],'swap_used':d['SwapTotal']-d['SwapFree']}


def dispatch(root,data,checked,freeze_slot,entry,physics_workers,render_workers):
    if not 1<=physics_workers<=4 or not 1<=render_workers<=4:raise ValueError('Bounded1..4 workers required')
    root=Path(root);data=Path(data);c=checked(root);data.mkdir(parents=True,exist_ok=True)
    lock=(root/'campaign.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    path=root/'campaign-state.json'
    state=json.loads(path.read_text()) if path.exists() else {'campaign_sha256':c['profile_sha256'],
        'consecutive_failures':0,'slots':{s['episode_uid']:{'status':'planned','physics_attempts':0} for s in c['slots']}}
    if state['campaign_sha256']!=c['profile_sha256'] or any(r['status'] in ('physics_running','render_running','error','review_hold') for r in state['slots'].values()):
        raise ValueError('Ambiguous/interrupted campaign requires evidence reconciliation')
    epoch=f'launch-{time.time_ns()}';started=time.time();baseline=memory();jobs={};error=None;pressure=None
    processes={};process_lock=threading.Lock();evicted=set();maxima={'physics':0,'render':0,'simultaneous_4_plus_4':False}
    def save():write_json(path,state)
    def event(uid,stage,**values):
        with (root/'attempts.jsonl').open('a') as f:f.write(json.dumps({'unix_s':time.time(),'epoch':epoch,'episode_uid':uid,'stage':stage,**values})+'\n')
    policy={'epoch':epoch,'physics_workers':physics_workers,'render_workers':render_workers,'started_unix_s':started,
        'baseline':baseline,'source_sha256':sha(__file__),'campaign_sha256':c['profile_sha256'],
        'minimum_available_ram_bytes':c['minimum_available_ram_bytes'],'maximum_swap_growth_bytes':c['maximum_swap_growth_bytes'],
        'emergency_render_eviction_available_bytes':c.get('emergency_render_eviction_available_bytes',1536*1024**2),
        'new_render_minimum_available_bytes':c.get('new_render_minimum_available_bytes',4*1024**3),
        'pressure_drain_render_limit':2}
    write_json(root/'execution-policies'/(epoch+'.json'),policy);state.update(status='running',execution_epoch=epoch);save()
    repo=entry.resolve().parents[3]
    def run(stage,slot,scene=None):
        uid=slot['episode_uid'];row=state['slots'][uid];env=dict(os.environ)
        env.update(PYTHONPATH=str(repo/'src'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
        if stage=='physics':
            cmd=[c['python'],'-u',str(entry),'physics','--root',str(root),'--candidate',scene['candidate_id']]
            log=root/'logs'/(scene['candidate_id']+'.log')
        else:
            cmd=[c['python'],'-u',str(repo/'scripts/mujoco/synthesis/rerecord_pilots.py'),'--profile',row['recording_profile'],'--output',str(data/'slots'/uid)]
            log=root/'logs'/(uid+'-render-dispatch.log')
        log.parent.mkdir(parents=True,exist_ok=True);t=time.monotonic()
        with log.open('a') as f:
            process=subprocess.Popen(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            with process_lock:
                evicted.discard(uid)
                processes[uid]=(stage,process,time.time())
            process.wait()
            with process_lock:processes.pop(uid,None)
        event(uid,stage+'_process',exit_code=process.returncode,wall_s=time.monotonic()-t,log=str(log))
        if uid in evicted:return {'resource_evicted':True}
        if process.returncode:raise RuntimeError('Worker failed closed: '+str(log))
        if stage=='physics':return json.loads((root/'physical'/scene['candidate_id']/'result.json').read_text())
        queue=json.loads((data/'slots'/uid/'recording-queue.json').read_text());return queue['slots'][uid]['acceptance']
    try:
        with futures.ThreadPoolExecutor(max_workers=physics_workers+render_workers) as pool:
            while True:
                mem=memory();ap=sum(v[0]=='physics' for v in jobs.values());ar=sum(v[0]=='render' for v in jobs.values())
                maxima['physics']=max(maxima['physics'],ap);maxima['render']=max(maxima['render'],ar)
                with process_lock:
                    actual_p=sum(v[0]=='physics' for v in processes.values());actual_r=sum(v[0]=='render' for v in processes.values())
                    maxima['simultaneous_4_plus_4'] |= actual_p==4 and actual_r==4
                    if mem['available']<policy['emergency_render_eviction_available_bytes']:
                        candidates=[(uid,v) for uid,v in processes.items() if v[0]=='render' and uid not in evicted]
                        if candidates:
                            uid,(_,process,_) = max(candidates,key=lambda x:x[1][2])
                            evicted.add(uid);os.killpg(process.pid,signal.SIGTERM)
                            event(uid,'resource_render_evicted',**mem,physics_reexecuted=False)
                with (root/'resources.jsonl').open('a') as f:f.write(json.dumps({'unix_s':time.time(),'epoch':epoch,**mem,
                    'active_physics':actual_p,'active_render':actual_r})+'\n')
                write_json(root/'resource-current.json',{**mem,'active_physics':actual_p,'active_render':actual_r,'maxima':maxima})
                if mem['available']<c['minimum_available_ram_bytes'] or mem['swap_used']-baseline['swap_used']>c['maximum_swap_growth_bytes']:
                    if pressure is None:event(None,'resource_pressure_drain',**mem)
                    pressure=mem
                if not error:
                    checked(root)
                    render_limit=min(render_workers,2) if pressure is not None else render_workers
                    for slot in c['slots']:
                        row=state['slots'][slot['episode_uid']]
                        if ar>=render_limit:break
                        if row['status']=='render_pending' and mem['available']>=policy['new_render_minimum_available_bytes']:
                            uid=slot['episode_uid'];row['status']='render_running';save();event(uid,'render_start',physical_execution=False)
                            jobs[pool.submit(run,'render',slot)]=('render',slot,None);ar+=1
                    backlog=sum(r['status'] in ('render_pending','render_running') for r in state['slots'].values())
                    if pressure is None:
                        for slot in c['slots']:
                            row=state['slots'][slot['episode_uid']]
                            if ap>=physics_workers or backlog+ap>=c['maximum_render_backlog']:break
                            if row['status']!='planned':continue
                            if sum(r['physics_attempts'] for r in state['slots'].values())>=30 or state['consecutive_failures']>=10 or row['physics_attempts']>=5:
                                error='Predeclared physical budget exhausted';break
                            scene=slot['candidates'][row['physics_attempts']];row.update(status='physics_running',physics_attempts=row['physics_attempts']+1,scene=scene)
                            event(slot['episode_uid'],'physics_start',candidate_id=scene['candidate_id']);save()
                            jobs[pool.submit(run,'physics',slot,scene)]=('physics',slot,scene);ap+=1
                if not jobs:break
                done,_=futures.wait(jobs,timeout=2,return_when=futures.FIRST_COMPLETED)
                for job in done:
                    stage,slot,scene=jobs.pop(job);uid=slot['episode_uid'];row=state['slots'][uid]
                    try:
                        result=job.result()
                        if result.get('resource_evicted'):
                            row['status']='render_pending';event(uid,'render_retry_pending',same_physical_trace=True)
                        elif stage=='physics':
                            event(uid,'physics_result',result=result)
                            if result['passed']:
                                row['recording_profile']=freeze_slot(root,c,slot,scene);row.update(trace=result['trace'],status='render_pending');state['consecutive_failures']=0
                            else:row['status']='planned';state['consecutive_failures']+=1
                        else:
                            row.update(status='accepted',acceptance=result);event(uid,'accepted',physical_demo_count=1)
                            print(json.dumps({'accepted':sum(v['status']=='accepted' for v in state['slots'].values()),'episode_uid':uid}),flush=True)
                    except Exception as exc:
                        row['status']='review_hold' if stage=='physics' and (root/'physical'/scene['candidate_id']/'trace/manifest.json').exists() else 'error'
                        error=str(exc);event(uid,'fail_closed',reason=error)
                    save()
        accepted=sum(r['status']=='accepted' for r in state['slots'].values())
        result={'status':'technical_pilots_complete' if accepted==10 else 'stopped','accepted':accepted,
            'reason':error or ('RAM/swap guard; resume with evidence-based lower concurrency' if pressure else None),
            'started_unix_s':started,'ended_unix_s':time.time(),'wall_s':time.time()-started,'resource_baseline':baseline,
            'resource_final':memory(),'physics_workers':physics_workers,'render_workers':render_workers,'actual_maxima':maxima,
            'pilot_user_quality_review':'pending','scale100_started':False}
        state.update(result);save();write_json(root/'execution-policies'/(epoch+'-result.json'),result)
        if error:raise RuntimeError(error)
        if accepted!=10:raise SystemExit(3)
    finally:fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
