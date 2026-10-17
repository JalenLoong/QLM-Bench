"""Single-writer pilot queue with separate physical/render attempts and backpressure."""
import copy
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import time

from .trace import verify_trace,write_json,sha


class PilotQueue:
    def __init__(self,root,profile):
        self.root=Path(root);self.profile=profile;self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'queue.json'
        if self.path.exists():
            self.state=json.loads(self.path.read_text())
            if self.state['profile_sha256']!=profile['profile_sha256']:raise ValueError('Frozen queue profile mismatch')
        else:
            self.state={'schema':'qlm-pilot-queue-v1','profile_sha256':profile['profile_sha256'],
                'slots':{s['episode_uid']:{'status':'planned','physical_attempts':0,'render_attempts':0} for s in profile['slots']}}
            self.save()
        self.lock=None
    def __enter__(self):
        self.lock=(self.root/'queue.lock').open('a');fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB);return self
    def __exit__(self,*args):
        fcntl.flock(self.lock,fcntl.LOCK_UN);self.lock.close()
    def save(self):write_json(self.path,self.state)
    def event(self,uid,stage,**values):
        with (self.root/'attempts.jsonl').open('a') as f:
            f.write(json.dumps({'slot':uid,'stage':stage,**values},allow_nan=False)+'\n');f.flush()
    def reconcile(self):
        for uid,row in self.state['slots'].items():
            if row.get('trace') and (Path(row['trace'])/'manifest.json').is_file():
                m,*_=verify_trace(row['trace'])
                if m['scene']['candidate_id']!=row['scene']['candidate_id']:raise ValueError('Queue trace/candidate conflict')
                if row['status']!='accepted':row['status']='render_pending'
            elif row['status']=='physics_running':
                self.event(uid,'physics_interrupted',candidate_id=row['scene']['candidate_id'])
                row['status']='planned'
            result=self.root/'episodes'/uid/'result.json'
            if result.is_file():
                r=json.loads(result.read_text());producer=json.loads((result.parent/'producer.json').read_text())
                if r.get('passed') is True and producer.get('passed') is True:
                    if producer['physical_trace']['manifest_sha256']!=sha(Path(row['trace'])/'manifest.json'):
                        raise ValueError('Episode/trace conflict on restart')
                    inventory=result.parent/'canonical/meta/checksums.json'
                    if inventory.is_file():
                        for name,expected in json.loads(inventory.read_text()).items():
                            if sha(result.parent/'canonical'/name)!=expected:raise ValueError('Accepted payload corrupted on restart')
                    row['status']='accepted';row['accepted_output']=str(result.parent)
        self.save()
    def accepted(self):return sum(r['status']=='accepted' for r in self.state['slots'].values())
    def run(self,physical_runner,render_runner,*,stop_after_physics=False,limit=None,defer_render=False):
        self.reconcile();continuous_failures=self.state.get("continuous_failures",0)
        for slot in self.profile['slots']:
            uid=slot['episode_uid'];row=self.state['slots'][uid]
            if row['status']=='accepted':continue
            while row['status'] not in ('render_pending','accepted'):
                total=sum(r['physical_attempts'] for r in self.state['slots'].values())
                if row['physical_attempts']>=5 or total>=30 or continuous_failures>=10:
                    raise RuntimeError('Physical candidate budget exhausted; review required')
                attempt=row['physical_attempts'];scene=copy.deepcopy(slot['candidates'][attempt])
                trace=self.root/'traces'/scene['candidate_id']
                row.update(status='physics_running',physical_attempts=attempt+1,scene=scene,trace=str(trace))
                self.save();self.event(uid,'physics_running',candidate_id=scene['candidate_id'],seed=scene['seed'])
                try:result=physical_runner(scene,trace)
                except Exception as error:
                    self.event(uid,'system_error',candidate_id=scene['candidate_id'],reason=str(error));raise
                if result['passed']:
                    verify_trace(trace);row.update(status='render_pending',physics_result=result)
                    continuous_failures=0;self.state['continuous_failures']=0;self.save();self.event(uid,'physics_passed',candidate_id=scene['candidate_id'])
                else:
                    self.event(uid,'physics_failed',candidate_id=scene['candidate_id'],seed=scene['seed'],result=result)
                    temporary=trace.with_name(trace.name+'.writing')
                    if temporary.exists():shutil.rmtree(temporary)
                    row['status']='planned';continuous_failures+=1;self.state['continuous_failures']=continuous_failures;self.save()
            if defer_render:
                self.event(uid,'physics_retained_for_frozen_rendition');continue
            if stop_after_physics:
                self.event(uid,'verification_stop_after_physics');return
            while row['status']!='accepted':
                if row['render_attempts']>=3:raise RuntimeError('Render retry budget exhausted; trace retained')
                row.update(status='rendering',render_attempts=row['render_attempts']+1);self.save()
                output=self.root/'episodes'/uid
                if output.exists():
                    # Only this queue's incomplete render staging may be removed.
                    if (output/'result.json').exists() and json.loads((output/'result.json').read_text()).get('passed'):
                        raise ValueError('Refuse clearing a valid episode')
                    shutil.rmtree(output)
                try:result=render_runner(row['trace'],row['scene'],slot,output)
                except Exception as error:
                    row['status']='render_pending';self.save();self.event(uid,'render_failed',reason=str(error));continue
                if result.get('passed') is not True:raise RuntimeError('Render returned without acceptance')
                row.update(status='accepted',accepted_output=str(output),render_result=result)
                self.save();self.event(uid,'accepted',candidate_id=row['scene']['candidate_id'])
            print(f'Accepted {uid}; total {self.accepted()}/10',flush=True)
            if limit is not None and self.accepted()>=limit:return


def run_production(profile_path,root,checkpoint,*,stop_after_physics=False,limit=None):
    profile=json.loads(Path(profile_path).read_text())
    unsigned={k:v for k,v in profile.items() if k!='profile_sha256'}
    import hashlib
    if hashlib.sha256(json.dumps(unsigned,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=profile['profile_sha256']:
        raise ValueError('Frozen synthesis profile checksum mismatch')
    if profile['task_id']!='push_box' or len(profile['slots'])!=10:raise ValueError('M0-M6 only admits ten Push pilots')
    source_root=Path(__file__).resolve().parents[4]
    for name,expected in profile['source']['implementation'].items():
        if sha(source_root/name)!=expected:raise ValueError('Frozen implementation changed: '+name)
    if sha(Path(profile['template_root'])/'template.json')!=profile['template_sha256']:
        raise ValueError('Frozen template changed')
    import torch
    from .runtime import MuJoCoRuntime
    from .template import PushTemplateExecutor
    from .trace import collect_trace
    torch.set_num_threads(1);runtimes={};executor=PushTemplateExecutor(profile['template_root'])
    def physics(scene,dest):
        for name,expected in profile['source']['implementation'].items():
            if sha(source_root/name)!=expected:raise ValueError('Source changed during pilot batch')
        model=scene['model']
        if model not in runtimes:runtimes[model]=MuJoCoRuntime(model,checkpoint,trace_only=True)
        runtime=runtimes[model]
        runtime.profile.update(goal_x=scene['goal_x'],goal_y=scene['goal_y'],canonical_goal_position=scene['canonical_goal_position'])
        return collect_trace(runtime,executor,scene,dest,batch_identity=profile['source'])
    def render(trace,scene,slot,output):
        metadata={k:slot[k] for k in ('episode_uid','task_id','difficulty','split')}
        metadata.update(asset_id='cardboard-box-05',appearance_preset=scene['appearance_preset'],environment_seed=scene['seed'],
            initial_condition_id=scene['candidate_id'],goal_condition_id=scene['candidate_id'])
        meta=Path(root)/'render-inputs'/f'{slot["episode_uid"]}.json';write_json(meta,metadata)
        source=Path(root)/'batch-source.json';write_json(source,profile['source'])
        import os
        env=dict(os.environ);env['MUJOCO_GL']='osmesa';env.update(profile['render_environment'])
        command=[profile['python'],'-u',profile['render_script'],'--trace',str(trace),'--model',scene['model'],
            '--output',str(output),'--episode-uid',slot['episode_uid'],'--ffmpeg',profile['ffmpeg'],
            '--ffprobe',profile['ffprobe'],'--formal-pilot','--metadata',str(meta),'--batch-source',str(source)]
        with (Path(root)/f'{slot["episode_uid"]}-render.log').open('a') as log:
            subprocess.run(command,env=env,stdout=log,stderr=log,check=True)
        return json.loads((output/'result.json').read_text())
    started=time.monotonic()
    try:
        with PilotQueue(root,profile) as queue:
            queue.run(physics,render,stop_after_physics=stop_after_physics,limit=limit)
            return {'accepted':queue.accepted(),'wall_s':time.monotonic()-started}
    finally:
        for rt in runtimes.values():rt.close()
