"""CPU-only production planning, QC evidence and single-writer staged recovery.

Physics and OSMesa run in separate subprocesses. No WAM validation/import exists.
"""
import concurrent.futures as futures
import copy
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np
from .trace import sha, write_json, verify_trace
from .quality import analyze_trace
from .rendition import audit_trace, validate_output, RecordingIntegrityError
from qlm_bench.compatibility.dataset_v2.validation import digest
from qlm_bench.compatibility.dataset_v2.media import MediaTools

LIMITS=np.array([.04,.035,.06,.03,.02])
CLEAN_LIMITS=np.array([.004,.004,.008,.003,.002])
NEAR=np.array([.002,.002,.005,.002,.002])
QUOTAS={'train':{'clean':16,'randomized':64},'validation':{'clean':2,'randomized':8},'test':{'clean':2,'randomized':8}}


def configuration_candidates(pilots,seed=2026101416):
    """Same ID support for every split; immutable geometrical bins/retry candidates."""
    rng=np.random.default_rng(seed);prior=[(np.array(p['parameters']),p['split']) for p in pilots]
    rows=[];index=0
    for split,clean_count,random_count in [('train',14,56),('validation',2,8),('test',2,8)]:
        for difficulty,count in [('clean',clean_count),('randomized',random_count)]:
            for j in range(count):
                uid=f'push100-20261014-{index+11:03d}';signs=np.array([1 if (j%8)&(1<<k) else -1 for k in range(3)])
                preset='ap_00' if difficulty=='clean' else f'ap_{int(rng.integers(2)):02d}'
                candidates=[];base=None
                for attempt in range(5):
                    for draw in range(10000):
                        if base is None:
                            params=rng.uniform(-1,1,5)*(CLEAN_LIMITS if difficulty=='clean' else LIMITS)
                            if difficulty=='randomized':params[:3]=np.abs(params[:3])*signs
                        else:
                            params=base.copy();params[:3]+=rng.uniform(-1,1,3)*([.0005,.0005,.001] if difficulty=='clean' else [.002,.002,.003])
                            params=np.clip(params,-(CLEAN_LIMITS if difficulty=='clean' else LIMITS),CLEAN_LIMITS if difficulty=='clean' else LIMITS)
                            if difficulty=='randomized':params[:3]=np.abs(params[:3])*signs
                        if difficulty=='randomized' and np.max(np.abs(params[:3])/LIMITS[:3])<=.25:continue
                        if any(np.all(np.abs(params-old)<=NEAR) for old,other_split in prior if other_split!=split):continue
                        if any(np.array_equal(params,old) for old,_ in prior):continue
                        break
                    else:raise ValueError('Configuration deduplication exhausted; do not shrink distribution')
                    if base is None:base=params.copy()
                    prior.append((params.copy(),split))
                    candidates.append({'candidate_id':f'{uid}-c{attempt+1:02d}','seed':1614000+index*10+attempt,
                                       'configuration_parameters':params.tolist(),'configuration_sha256':digest(params.tolist())})
                rows.append({'episode_uid':uid,'task_id':'push_box','split':split,'difficulty':difficulty,
                             'appearance_preset':preset,'geometry_bin':'near-nominal' if difficulty=='clean' else ''.join('+' if x>0 else '-' for x in signs),
                             'candidates':candidates});index+=1
    return rows


def quality_flags(review):
    flags=[]
    if review['world_target_step_max_m'] is None or review['world_target_step_max_m']>.00801:flags.append('world-target continuity')
    if review['push_body_midline_crossing_s']>0:flags.append('measured push midline crossing')
    if review['late_FL_hip_min_deg']< -40:flags.append('posture outside reviewed neighborhood')
    if review['contact']['body_contact_boundaries']>0:flags.append('inspect actual body-contact behavior')
    return flags


def load_campaign(path,source_root=None):
    p=json.loads(Path(path).read_text());unsigned={k:v for k,v in p.items() if k!='profile_sha256'}
    if digest(unsigned)!=p.get('profile_sha256') or p.get('schema')!='qlm-push100-production-v1':raise ValueError('Invalid frozen100 profile')
    if p['authorization'].get('pilot_approved') is not True or len(p['pilots'])!=10 or len(p['slots'])!=90:raise ValueError('Approved10 plus90 required')
    actual={k:{d:0 for d in ['clean','randomized']} for k in QUOTAS}
    for s in p['pilots']+p['slots']:
        actual[s['split']][s['difficulty']]+=1
        if s['difficulty']=='clean' and s['appearance_preset']!='ap_00':raise ValueError('Clean requires ap_00')
    if actual!=QUOTAS:raise ValueError('Wrong100 split/difficulty quotas')
    uids=[s['episode_uid'] for s in p['pilots']+p['slots']]
    if len(set(uids))!=100:raise ValueError('Duplicate production identity')
    if p['consumer_validation']!='task_already_validated_skip':raise ValueError('Repeated WAM validation is not a production stage')
    if source_root is not None:
        for name,h in p['source']['implementation'].items():
            if sha(Path(source_root)/name)!=h:raise RecordingIntegrityError('Frozen source changed: '+name)
        if sha(Path(p['template_root'])/'template.json')!=p['source']['template_sha256']:raise RecordingIntegrityError('Template changed')
    return p


def freeze_episode(campaign,slot,trace,path):
    audit=audit_trace(trace);m=verify_trace(trace)[0];review,_=analyze_trace(trace)
    flags=quality_flags(review)
    resolution=None
    if flags:
        resolution_path=Path(path).parent.parent/'quality-resolutions'/(slot['episode_uid']+'.json')
        if not resolution_path.is_file():raise ValueError('Behavior review hold: '+', '.join(flags))
        resolution=json.loads(resolution_path.read_text())
        if resolution.get('accepted') is not True or resolution.get('trace_manifest_sha256')!=audit['manifest_sha256'] or resolution.get('quality_review_sha256')!=digest(review) or resolution.get('flags')!=flags or not resolution.get('evidence'):
            raise RecordingIntegrityError('Behavior review resolution does not match actual evidence')
        for evidence in resolution['evidence']:
            if sha(evidence['path'])!=evidence['sha256']:raise RecordingIntegrityError('Behavior review evidence changed')
    member={k:slot[k] for k in ['episode_uid','task_id','split','difficulty']}
    member.update(trace=str(Path(trace).resolve()),model=m['scene']['model'],model_identity=m['model_identity'],
        physical_source_sha256=audit['source_identity_sha256'],trace_manifest_sha256=audit['manifest_sha256'],physical_trajectory_sha256=audit['trajectory_sha256'],
        quality=audit['quality'],quality_review_sha256=digest(review),review_status='approved_task_recipe_technical_quality',n_actions=m['n_actions'],
        rendition_id=slot['episode_uid']+'@production360p-v1',candidate_id=m['scene']['candidate_id'],asset_id=m['profile']['asset_id'],
        appearance_preset=m['scene']['appearance_preset'],seed=m['scene']['seed'])
    if resolution is not None:member['behavior_review_resolution']=resolution
    p={k:copy.deepcopy(campaign[k]) for k in ['approval','template_root','python','ffmpeg','ffprobe','render_environment']}
    p.update(schema='qlm-push-production-rendition-v1',profile_id=slot['episode_uid']+'-recording-v1',work_id='QLM-DATA-016',task_id='push_box',
        rgb_profile='dual-rgb-360p-v1',quality_policy='evidence-review-v1',maximum_render_attempts=3,slots=[member],
        production_authorization={'pilot_approved':True,'target_accepted':100},campaign_sha256=campaign['profile_sha256'],
        recording_source={**campaign['source'],'stage':'production_offline_recording'},render_script=campaign['render_script'],
        template_sha256=campaign['source']['template_sha256'],template_id=campaign['source']['template_id'])
    p['profile_sha256']=digest(p)
    if Path(path).exists():
        if json.loads(Path(path).read_text())!=p:raise RecordingIntegrityError('Existing episode profile differs')
    else:write_json(path,p)
    return member,review


class ProductionQueue:
    """One writer; one physics process, up to two disjoint render-only processes."""
    def __init__(self,root,campaign_path,source_root):
        self.root=Path(root);self.path=self.root/'queue.json';self.campaign_path=Path(campaign_path)
        self.source_root=Path(source_root);self.p=load_campaign(campaign_path,source_root)
        self.root.mkdir(parents=True,exist_ok=True)
        if self.path.exists():
            self.state=json.loads(self.path.read_text())
            if self.state['profile_sha256']!=self.p['profile_sha256']:raise RecordingIntegrityError('Queue campaign changed')
        else:
            self.state={'profile_sha256':self.p['profile_sha256'],'status':'running','retained_pilots':10,'consecutive_failures':0,
                        'slots':{s['episode_uid']:{'status':'planned','physical_attempts':0} for s in self.p['slots']}}
            self.save()
    def save(self):write_json(self.path,self.state)
    def event(self,uid,event,**data):
        with (self.root/'events.jsonl').open('a') as f:f.write(json.dumps({'time_unix_s':time.time(),'episode_uid':uid,'event':event,**data},allow_nan=False)+'\n')
    def accepted(self):return 10+sum(r['status']=='accepted' for r in self.state['slots'].values())
    def output(self,uid):return Path(self.p['data_root'])/'new'/uid/'episodes'/uid
    def validate(self,uid):return validate_output(self.output(uid),profile_path=self.root/'profiles'/f'{uid}.json',tools=MediaTools(self.p['ffmpeg'],self.p['ffprobe']),check_media=False)
    def retain(self,slot,row):
        member,review=freeze_episode(self.p,slot,row['trace'],self.root/'profiles'/f"{slot['episode_uid']}.json")
        write_json(self.root/'quality'/f"{slot['episode_uid']}.json",review)
        known={s['physical_trajectory_sha256'] for s in self.p['pilots']}
        known.update(v['trajectory_sha256'] for k,v in self.state['slots'].items() if k!=slot['episode_uid'] and 'trajectory_sha256' in v)
        if member['physical_trajectory_sha256'] in known:raise RecordingIntegrityError('Duplicate actual physical trajectory')
        row.update(status='render_pending',trajectory_sha256=member['physical_trajectory_sha256']);self.save()
    def reconcile(self):
        for s in self.p['slots']:
            uid=s['episode_uid'];r=self.state['slots'][uid]
            if (self.output(uid)/'result.json').is_file():
                self.validate(uid);r['status']='accepted';continue
            if r.get('trace') and (Path(r['trace'])/'manifest.json').is_file():self.retain(s,r)
            elif r['status']=='physics_running':
                receipt=self.root/'attempts'/(r['scene']['candidate_id']+'.json')
                if receipt.exists():
                    result=json.loads(receipt.read_text())
                    if result['passed']:raise RecordingIntegrityError('Success receipt missing actual trace')
                    self.state['consecutive_failures']+=1
                self.event(uid,'interrupted_physics_retains_attempt_budget');r['status']='planned'
        self.save()
    def physics_job(self,scene,trace):
        candidate=self.root/'candidates'/(scene['candidate_id']+'.json');write_json(candidate,scene)
        receipt=self.root/'attempts'/(scene['candidate_id']+'.json')
        log=self.root/'logs'/(scene['candidate_id']+'.log');log.parent.mkdir(parents=True,exist_ok=True)
        env=dict(os.environ,PYTHONPATH=str(self.source_root/'src'),OMP_NUM_THREADS='1',WARP_CACHE_PATH=self.p['warp_cache'])
        cmd=[self.p['python'],'-u',self.p['entrypoint'],'physics','--root',str(self.root),'--candidate',str(candidate),'--trace',str(trace),'--result',str(receipt)]
        with log.open('a') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
        if r.returncode:raise RuntimeError('Physics system error; see '+str(log))
        return json.loads(receipt.read_text())
    def render_job(self,uid):
        env=dict(os.environ,PYTHONPATH=str(self.source_root/'src'),OMP_NUM_THREADS='4')
        log=self.root/'logs'/(uid+'-recording.log')
        cmd=[self.p['python'],'-u',str(self.source_root/'scripts/mujoco/synthesis/rerecord_pilots.py'),'--profile',str(self.root/'profiles'/f'{uid}.json'),'--output',str(Path(self.p['data_root'])/'new'/uid)]
        with log.open('a') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
        if r.returncode:raise RuntimeError('Recording error; original trace retained; see '+str(log))
        return self.validate(uid)
    def run(self):
        lock=(self.root/'queue.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        jobs={};error=None;self.state['status']='running';self.save()
        try:
            self.reconcile()
            with futures.ThreadPoolExecutor(max_workers=3) as pool:
                while self.accepted()<100 or jobs:
                    active_physics=any(stage=='physics' for stage,_,_ in jobs.values());active_render=sum(stage=='render' for stage,_,_ in jobs.values())
                    pending=sum(r['status'] in ('render_pending','rendering') for r in self.state['slots'].values())
                    if error is None:
                        load_campaign(self.campaign_path,self.source_root)
                        for s in self.p['slots']:
                            uid=s['episode_uid'];r=self.state['slots'][uid]
                            if r['status']=='render_pending' and active_render<2:
                                r['status']='rendering';self.save();self.event(uid,'render_started',physical_execution=False)
                                jobs[pool.submit(self.render_job,uid)]=('render',s,r);active_render+=1
                        if not active_physics and pending<3:
                            s=next((s for s in self.p['slots'] if self.state['slots'][s['episode_uid']]['status']=='planned'),None)
                            if s is not None:
                                r=self.state['slots'][s['episode_uid']];attempt=r['physical_attempts']
                                if attempt>=5 or sum(v['physical_attempts'] for v in self.state['slots'].values())>=270 or self.state['consecutive_failures']>=10:
                                    raise RuntimeError('Bounded physics candidate budget exhausted')
                                scene=copy.deepcopy(s['candidates'][attempt]);trace=self.root/'traces'/scene['candidate_id']
                                r.update(status='physics_running',physical_attempts=attempt+1,scene=scene,trace=str(trace));self.save();self.event(s['episode_uid'],'physics_started',candidate_id=scene['candidate_id'])
                                jobs[pool.submit(self.physics_job,scene,trace)]=('physics',s,r)
                    if not jobs:
                        if error:break
                        if self.accepted()!=100:raise RuntimeError('Queue stalled without runnable work')
                        break
                    done,_=futures.wait(jobs,timeout=1,return_when=futures.FIRST_COMPLETED)
                    for job in done:
                        stage,s,r=jobs.pop(job);uid=s['episode_uid']
                        try:
                            result=job.result()
                            if stage=='physics':
                                self.event(uid,'physics_result',candidate_id=r['scene']['candidate_id'],result=result)
                                if result['passed']:
                                    self.state['consecutive_failures']=0;self.retain(s,r)
                                else:
                                    self.state['consecutive_failures']+=1;r['status']='planned'
                            else:
                                r.update(status='accepted',acceptance=result);self.event(uid,'accepted',total=self.accepted())
                                print(json.dumps({'accepted':self.accepted(),'new_physical_attempts':sum(v['physical_attempts'] for v in self.state['slots'].values())}),flush=True)
                        except Exception as exc:
                            r['status']='review_hold' if stage=='physics' and (Path(r['trace'])/'manifest.json').exists() else 'error'
                            error=str(exc);self.event(uid,'fail_closed',reason=error)
                        self.save()
                if error:raise RuntimeError(error)
            self.state['status']='production_complete';self.save()
        except BaseException as exc:
            self.state.update(status='stopped',reason=str(exc));self.save();raise
        finally:fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
