"""Lift100 admission and bounded streaming production, retaining the approved ten."""
import concurrent.futures as futures
import copy
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

import numpy as np

from .production import ProductionQueue, QUOTAS
from .quality import analyze_trace
from .rendition import audit_trace, validate_slot_inputs, RecordingIntegrityError
from .trace import sha, verify_trace, write_json
from qlm_bench.compatibility.dataset_v2.pilot_rendition import LIFT_PRODUCTION_SCHEMA, load_profile
from qlm_bench.compatibility.dataset_v2.validation import digest

LIMITS = np.array([.03, .03, 5.])
CLEAN_LIMITS = np.array([.003, .003, .3])
NEAR = np.array([.0005, .0005, .05])


def configuration_candidates(pilots, seed=2026101522):
    rng = np.random.default_rng(seed)
    prior = [(np.asarray(s['parameters']), s['split']) for s in pilots]
    rows = []
    for split, clean, randomized in [('validation', 2, 8), ('test', 2, 8), ('train', 14, 56)]:
        for difficulty, count in [('clean', clean), ('randomized', randomized)]:
            limit = CLEAN_LIMITS if difficulty == 'clean' else LIMITS
            for j in range(count):
                index = len(rows) + 11
                uid = f'lift100-20261015-{index:03d}'
                signs = np.array([1 if j % 8 & (1 << k) else -1 for k in range(3)])
                base = None
                candidates = []
                for attempt in range(5):
                    for _ in range(20000):
                        if base is None:
                            point = rng.uniform(-1, 1, 3) * limit
                            if difficulty == 'randomized':
                                point = np.abs(point) * signs
                        else:
                            point = np.clip(base + rng.uniform(-1, 1, 3) *
                                ([.0001, .0001, .02] if difficulty == 'clean' else [.001, .001, .15]), -limit, limit)
                        if any(np.all(np.abs(point - p) <= NEAR) for p, other in prior if other != split):
                            continue
                        if any(np.array_equal(point, p) for p, _ in prior):
                            continue
                        break
                    else:
                        raise ValueError('Concrete config dedup exhausted; do not shrink ID support')
                    if base is None:
                        base = point.copy()
                    prior.append((point.copy(), split))
                    candidates.append({'candidate_id': f'{uid}-c{attempt+1:02d}', 'seed': 2215000+index*10+attempt,
                        'configuration_parameters': point.tolist(), 'configuration_sha256': digest(point.tolist())})
                rows.append({'episode_uid': uid, 'task_id': 'lift_basket', 'split': split, 'difficulty': difficulty,
                    'appearance_preset': 'ap_00' if difficulty == 'clean' else f'ap_{(j+j//8)%2:02d}',
                    'geometry_bin': 'near-nominal' if difficulty == 'clean' else ''.join('+' if x>0 else '-' for x in signs),
                    'candidates': candidates})
    rows.sort(key=lambda s: ({'train':0, 'validation':1, 'test':2}[s['split']], s['episode_uid']))
    # The first two complete production entries qualify both difficulty/background routes.
    random = next(s for s in rows if s['difficulty']=='randomized' and s['appearance_preset']=='ap_01')
    rows.remove(random)
    rows.insert(1, random)
    return rows


def load_campaign(path, source_root=None):
    c = json.loads(Path(path).read_text())
    if c.get('schema') != 'qlm-lift100-production-v1' or digest({k:v for k,v in c.items() if k!='profile_sha256'}) != c['profile_sha256']:
        raise RecordingIntegrityError('Frozen Lift100 campaign changed')
    if not c['authorization'].get('pilot_approved') or len(c['pilots'])!=10 or len(c['slots'])!=90 or c['consumer_validation']!='task_already_validated_skip':
        raise RecordingIntegrityError('Approved ten plus90 without repeated WAM required')
    if c['source'].get('native_trace_profile') != 'native-cpu-original-rambo-v1' or c['render_environment']['MUJOCO_GL']!='egl':
        raise RecordingIntegrityError('Explicit approved NativeCPU/EGL profile required')
    quotas = {s:{d:0 for d in ('clean','randomized')} for s in QUOTAS}
    ids = []
    for slot in c['pilots']+c['slots']:
        ids.append(slot['episode_uid'])
        quotas[slot['split']][slot['difficulty']] += 1
        if slot['task_id']!='lift_basket' or (slot['difficulty']=='clean' and slot['appearance_preset']!='ap_00'):
            raise RecordingIntegrityError('Wrong task or Clean appearance')
    if quotas != QUOTAS or len(set(ids))!=100:
        raise RecordingIntegrityError('Wrong final quotas or duplicate identity')
    if source_root:
        for name, expected in c['source']['implementation'].items():
            if sha(Path(source_root)/name)!=expected:
                raise RecordingIntegrityError('Frozen source changed: '+name)
        if sha(Path(c['template_root'])/'template.json')!=c['source']['template_sha256']:
            raise RecordingIntegrityError('Approved recipe changed')
    return c


def freeze_episode(c, slot, trace, path):
    audit = audit_trace(trace)
    m = verify_trace(trace)[0]
    if m['backend']['physics']!='native' or m['backend'].get('controller_device')!='cpu':
        raise RecordingIntegrityError('New production requires actual NativeCPU/RAMBO CPU')
    review, _ = analyze_trace(trace)
    member = {k:slot[k] for k in ('episode_uid','task_id','split','difficulty','appearance_preset')}
    member.update(trace=str(trace), model=m['scene']['model'], model_identity=m['model_identity'],
        physical_source_sha256=audit['source_identity_sha256'], trace_manifest_sha256=audit['manifest_sha256'],
        physical_trajectory_sha256=audit['trajectory_sha256'], quality=audit['quality'], quality_review_sha256=digest(review),
        review_status='approved_task_recipe_technical_quality', n_actions=m['n_actions'],
        rendition_id=slot['episode_uid']+'@native-cpu-egl-360p-v1', candidate_id=m['scene']['candidate_id'],
        asset_id=m['profile']['asset_id'], seed=m['scene']['seed'])
    p = {k:copy.deepcopy(c[k]) for k in ('approval','template_root','python','ffmpeg','ffprobe','render_environment','render_script','work_id','task_id')}
    p.update(schema=LIFT_PRODUCTION_SCHEMA, profile_id=slot['episode_uid']+'-recording-v1', rgb_profile='dual-rgb-360p-v1',
        quality_policy='evidence-review-v1', maximum_render_attempts=3, slots=[member], production_authorization=c['authorization'],
        campaign_sha256=c['profile_sha256'], recording_source={**c['source'], 'stage':'production_offline_recording'},
        template_sha256=c['source']['template_sha256'], template_id=c['source']['template_id'])
    p['profile_sha256'] = digest(p)
    if Path(path).exists() and json.loads(Path(path).read_text())!=p:
        raise RecordingIntegrityError('Existing rendition changed')
    write_json(path, p)
    validate_slot_inputs(load_profile(path), slot['episode_uid'])
    return member, review


def memory():
    fields = {s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines()}
    return {'available':fields['MemAvailable'], 'swap_used':fields['SwapTotal']-fields['SwapFree']}


class LiftProductionQueue(ProductionQueue):
    def __init__(self, root, campaign_path, source_root):
        self.root=Path(root); self.path=self.root/'queue.json'; self.campaign_path=Path(campaign_path); self.source_root=Path(source_root)
        self.p=load_campaign(campaign_path,source_root)
        self.state=json.loads(self.path.read_text()) if self.path.exists() else {'profile_sha256':self.p['profile_sha256'],
            'status':'prepared', 'retained_pilots':10, 'consecutive_failures':0,
            'slots':{s['episode_uid']:{'status':'planned','physical_attempts':0} for s in self.p['slots']}}
        if self.state['profile_sha256']!=self.p['profile_sha256']:raise RecordingIntegrityError('Queue/campaign mismatch')
        self.processes={}; self.process_lock=threading.Lock(); self.evicted=set(); self.save()

    def retain(self, slot, row):
        member, review=freeze_episode(self.p,slot,row['trace'],self.root/'profiles'/f"{slot['episode_uid']}.json")
        known={s['physical_trajectory_sha256'] for s in self.p['pilots']}
        known.update(r['trajectory_sha256'] for uid,r in self.state['slots'].items() if uid!=slot['episode_uid'] and 'trajectory_sha256' in r)
        if member['physical_trajectory_sha256'] in known:raise RecordingIntegrityError('Duplicate physical trajectory')
        write_json(self.root/'quality'/f"{slot['episode_uid']}.json",review)
        row.update(status='render_pending',trajectory_sha256=member['physical_trajectory_sha256']); self.save()

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

    def run_parallel(self, physics_workers=4, render_workers=4, admission=False):
        if not 1<=physics_workers<=4 or not 1<=render_workers<=4:raise ValueError('Bounded worker count1..4 required')
        lock=(self.root/'queue.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        epoch=f'launch-{time.time_ns()}';baseline=memory();start=time.time();jobs={};error=None;pressure=None
        slots=self.p['slots'][:2] if admission else self.p['slots'];target=12 if admission else 100
        policy={'epoch':epoch,'started_unix_s':start,'physics_workers':physics_workers,'render_workers':render_workers,
            'resource_baseline':baseline,'minimum_available_ram_bytes':1024**3,'maximum_swap_growth_bytes':6*1024**3,
            'emergency_render_eviction_available_bytes':512*1024**2,'new_render_minimum_available_bytes':4*1024**3,
            'campaign_sha256':self.p['profile_sha256'],'source_sha256':sha(__file__),'admission_only':admission}
        maxima={'physics':0,'render':0,'simultaneous_4_plus_4':False}
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
                    maxima['physics']=max(maxima['physics'],ap);maxima['render']=max(maxima['render'],ar);maxima['simultaneous_4_plus_4']|=ap==4 and ar==4
                    resource={'epoch':epoch,'unix_s':time.time(),**mem,'active_physics':ap,'active_render':ar,'maxima':maxima}
                    write_json(self.root/'resource-current.json',resource)
                    with (self.root/'resources.jsonl').open('a') as f:f.write(json.dumps(resource)+'\n')
                    if mem['available']<policy['minimum_available_ram_bytes'] or mem['swap_used']-baseline['swap_used']>policy['maximum_swap_growth_bytes']:
                        if pressure is None:self.event(None,'resource_pressure_drain',**mem,execution_epoch=epoch)
                        pressure=mem
                    ap=sum(x[0]=='physics' for x in jobs.values());ar=sum(x[0]=='render' for x in jobs.values())
                    if not error:
                        load_campaign(self.campaign_path,self.source_root)
                        for slot in slots:
                            row=self.state['slots'][slot['episode_uid']]
                            if row['status']=='render_pending' and ar<(min(render_workers,2) if pressure else render_workers) and mem['available']>=4*1024**3:
                                row['status']='rendering';self.save();jobs[pool.submit(self.worker,'render',slot)]=('render',slot);ar+=1
                        pending=sum(r['status'] in ('render_pending','rendering') for r in self.state['slots'].values())
                        for slot in slots:
                            if pressure or ap>=physics_workers or pending+ap>=8:break
                            row=self.state['slots'][slot['episode_uid']]
                            if row['status']!='planned':continue
                            if row['physical_attempts']>=5 or sum(x['physical_attempts'] for x in self.state['slots'].values())>=270 or self.state['consecutive_failures']>=10:
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
                        except Exception as exc:row['status']='review_hold' if stage=='physics' and (Path(row['trace'])/'manifest.json').exists() else 'error';error=str(exc)
                        self.save()
            status=('admission_complete' if admission else 'production_complete') if self.accepted()>=target else 'resource_pressure_drained' if pressure and not error else 'stopped'
            self.state.update(status=status,reason=error,resource_pressure=pressure);self.save()
            if error:raise RuntimeError(error)
            if self.accepted()<target and not pressure:raise RuntimeError('Queue stalled')
        finally:
            policy.update(ended_unix_s=time.time(),wall_s=time.time()-start,status=self.state['status'],accepted=self.accepted(),
                reason=error,resource_pressure=pressure,actual_maxima=maxima,resource_final=memory())
            write_json(self.root/'execution-policies'/(epoch+'-result.json'),policy);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
