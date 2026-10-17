"""Shared bounded NativeCPU/EGL streaming queue, retaining existing worker recovery.

Derived from the accepted Lift production queue without changing historical producers.
Task-specific admission/freezing is supplied explicitly; no model consumer runs here.
"""
import concurrent.futures as futures
import fcntl,json,os,signal,subprocess,threading,time
from pathlib import Path
from .production import ProductionQueue
from .trace import sha,write_json
from .rendition import RecordingIntegrityError
from .lift_production import memory

class NativeProductionQueue(ProductionQueue):
    def __init__(self, root, campaign_path, source_root, *, campaign_loader, freeze_recording):
        self.root=Path(root); self.path=self.root/'queue.json'; self.campaign_path=Path(campaign_path); self.source_root=Path(source_root)
        self.campaign_loader=campaign_loader; self.freeze_recording=freeze_recording
        self.p=campaign_loader(campaign_path,source_root)
        self.state=json.loads(self.path.read_text()) if self.path.exists() else {'profile_sha256':self.p['profile_sha256'],
            'status':'prepared', 'retained_pilots':len(self.p.get('pilots', [])), 'consecutive_failures':0,
            'slots':{s['episode_uid']:{'status':'planned','physical_attempts':0} for s in self.p['slots']}}
        if self.state['profile_sha256']!=self.p['profile_sha256']:raise RecordingIntegrityError('Queue/campaign mismatch')
        self.processes={}; self.process_lock=threading.Lock(); self.evicted=set(); self.save()

    def accepted(self):
        return self.state['retained_pilots'] + sum(r['status']=='accepted' for r in self.state['slots'].values())

    def retain(self, slot, row):
        member,review=self.freeze_recording(self.p,slot,row['trace'],self.root/'profiles'/f"{slot['episode_uid']}.json")
        known={s['physical_trajectory_sha256'] for s in self.p['pilots']}
        known.update(r['trajectory_sha256'] for uid,r in self.state['slots'].items() if uid!=slot['episode_uid'] and 'trajectory_sha256' in r)
        if member['physical_trajectory_sha256'] in known:raise RecordingIntegrityError('Duplicate physical trajectory')
        write_json(self.root/'quality'/f"{slot['episode_uid']}.json",review)
        row.update(status='render_pending',trajectory_sha256=member['physical_trajectory_sha256']);self.save()

    def worker(self, stage, slot, scene=None):
        uid=slot['episode_uid']; env=dict(os.environ, PYTHONPATH=str(self.source_root/'src'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
        if stage=='physics':
            candidate=self.root/'candidates'/(scene['candidate_id']+'.json');write_json(candidate,scene)
            receipt=self.root/'attempts'/(scene['candidate_id']+'.json')
            cmd=[self.p['python'],'-u',self.p['entrypoint'],'physics','--root',str(self.root),'--candidate',str(candidate),
                 '--trace',self.state['slots'][uid]['trace'],'--result',str(receipt)]
            log=self.root/'logs'/(scene['candidate_id']+'.log')
        else:
            cmd=[self.p['python'],'-u',str(self.source_root/'scripts/mujoco/synthesis/rerecord_pilots.py'),
                 '--profile',str(self.root/'profiles'/(uid+'.json')),'--output',str(Path(self.p['data_root'])/'new'/uid)]
            log=self.root/'logs'/(uid+'-render-dispatch.log')
        log.parent.mkdir(parents=True,exist_ok=True);start=time.monotonic()
        with log.open('a') as output:
            process=subprocess.Popen(cmd,env=env,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
            with self.process_lock:self.evicted.discard(uid);self.processes[uid]=(stage,process,time.time())
            process.wait()
            with self.process_lock:self.processes.pop(uid,None)
        self.event(uid,stage+'_process',exit_code=process.returncode,wall_s=time.monotonic()-start)
        if uid in self.evicted:return {'resource_evicted':True}
        if process.returncode:raise RuntimeError(f'Worker failed closed; see {log}')
        if stage=='physics':return json.loads(receipt.read_text())
        queue=json.loads((Path(self.p['data_root'])/'new'/uid/'recording-queue.json').read_text())
        return queue['slots'][uid]['acceptance']

    def run_parallel(self, physics_workers=3, render_workers=3, admission=False):
        if not 1<=physics_workers<=4 or not 1<=render_workers<=4:raise ValueError('Bounded worker count1..4 required')
        lock=(self.root/'queue.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        epoch=f'launch-{time.time_ns()}';baseline=memory();start=time.time();jobs={};error=None;pressure=None
        slots=self.p['slots'][:2] if admission else self.p['slots']
        target=self.state['retained_pilots']+len(slots)
        policy={'epoch':epoch,'started_unix_s':start,'physics_workers':physics_workers,'render_workers':render_workers,
            'resource_baseline':baseline,'minimum_available_ram_bytes':1024**3,'maximum_swap_growth_bytes':self.p['resource_policy']['maximum_swap_growth_bytes'],
            'emergency_render_eviction_available_bytes':512*1024**2,'new_render_minimum_available_bytes':4*1024**3,
            'campaign_sha256':self.p['profile_sha256'],'source_sha256':sha(__file__),'admission_only':admission}
        maxima={'physics':0,'render':0,'simultaneous_3_plus_3':False}
        write_json(self.root/'execution-policies'/(epoch+'.json'),policy)
        self.state.update(status='running',execution_epoch=epoch);self.save()
        try:
            self.reconcile()
            with futures.ThreadPoolExecutor(max_workers=physics_workers+render_workers) as pool:
                while True:
                    mem=memory()
                    with self.process_lock:
                        ap=sum(x[0]=='physics' for x in self.processes.values());ar=sum(x[0]=='render' for x in self.processes.values())
                        if mem['available']<policy['emergency_render_eviction_available_bytes']:
                            candidates=[(u,v) for u,v in self.processes.items() if v[0]=='render' and u not in self.evicted]
                            if candidates:
                                uid,(_,proc,_)=max(candidates,key=lambda x:x[1][2]);self.evicted.add(uid);os.killpg(proc.pid,signal.SIGTERM)
                                self.event(uid,'resource_render_evicted',physics_reexecuted=False,**mem)
                    maxima['physics']=max(maxima['physics'],ap);maxima['render']=max(maxima['render'],ar);maxima['simultaneous_3_plus_3']|=ap==3 and ar==3
                    resource={'epoch':epoch,'unix_s':time.time(),**mem,'active_physics':ap,'active_render':ar,'maxima':maxima}
                    write_json(self.root/'resource-current.json',resource)
                    with (self.root/'resources.jsonl').open('a') as f:f.write(json.dumps(resource)+'\n')
                    if mem['available']<policy['minimum_available_ram_bytes'] or mem['swap_used']-baseline['swap_used']>policy['maximum_swap_growth_bytes']:
                        if pressure is None:self.event(None,'resource_pressure_drain',**mem,execution_epoch=epoch)
                        pressure=mem
                    if (self.root/'PAUSE_NEW').exists():
                        pressure=pressure or {'reason':'explicit_pause_new'}
                    ap=sum(x[0]=='physics' for x in jobs.values());ar=sum(x[0]=='render' for x in jobs.values())
                    if not error:
                        self.campaign_loader(self.campaign_path,self.source_root)
                        for slot in slots:
                            row=self.state['slots'][slot['episode_uid']]
                            if row['status']=='render_pending' and ar<(min(render_workers,2) if pressure else render_workers) and mem['available']>=4*1024**3:
                                row['status']='rendering';self.save();jobs[pool.submit(self.worker,'render',slot)]=('render',slot);ar+=1
                        pending=sum(r['status'] in ('render_pending','rendering') for r in self.state['slots'].values())
                        for slot in slots:
                            if pressure or ap>=physics_workers or pending+ap>=self.p.get('maximum_render_backlog',6):break
                            row=self.state['slots'][slot['episode_uid']]
                            if row['status']!='planned':continue
                            if row['physical_attempts']>=self.p.get('per_slot_attempt_limits',{}).get(slot['episode_uid'],self.p.get('maximum_per_slot',5)) or self.p.get('prior_physics_attempts',0)+sum(x['physical_attempts'] for x in self.state['slots'].values())>=self.p.get('maximum_physics_attempts',270) or self.state['consecutive_failures']>=self.p.get('maximum_consecutive_failures',10):
                                error='Frozen candidate budget exhausted';break
                            scene=slot['candidates'][row['physical_attempts']]
                            row.update(status='physics_running',physical_attempts=row['physical_attempts']+1,scene=scene,
                                trace=str(self.root/'traces'/scene['candidate_id']));self.save()
                            self.event(slot['episode_uid'],'physics_started',candidate_id=scene['candidate_id'],execution_epoch=epoch)
                            jobs[pool.submit(self.worker,'physics',slot,scene)]=('physics',slot);ap+=1
                    if not jobs:break
                    done,_=futures.wait(jobs,timeout=2,return_when=futures.FIRST_COMPLETED)
                    for job in done:
                        stage,slot=jobs.pop(job);uid=slot['episode_uid'];row=self.state['slots'][uid]
                        try:
                            result=job.result()
                            if result.get('resource_evicted'):row['status']='render_pending'
                            elif stage=='physics':
                                self.event(uid,'physics_result',result=result)
                                if result['passed']:self.state['consecutive_failures']=0;self.retain(slot,row)
                                else:row['status']='planned';self.state['consecutive_failures']+=1
                            else:row.update(status='accepted',acceptance=result);self.event(uid,'accepted',total=self.accepted())
                            print(json.dumps({'accepted':self.accepted(),'episode_uid':uid,'stage':stage}),flush=True)
                        except Exception as exc:row['status']='review_hold' if stage=='physics' and (Path(row['trace'])/'manifest.json').exists() else 'error';error=str(exc);self.event(uid,'fail_closed',reason=error)
                        self.save()
            status=('admission_complete' if admission else 'production_complete') if self.accepted()>=target else 'resource_pressure_drained' if pressure and not error else 'stopped'
            self.state.update(status=status,reason=error,resource_pressure=pressure);self.save()
            if error:raise RuntimeError(error)
            if self.accepted()<target and not pressure:raise RuntimeError('Queue stalled')
        finally:
            policy.update(ended_unix_s=time.time(),wall_s=time.time()-start,status=self.state['status'],accepted=self.accepted(),
                reason=error,resource_pressure=pressure,actual_maxima=maxima,resource_final=memory())
            write_json(self.root/'execution-policies'/(epoch+'-result.json'),policy);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
