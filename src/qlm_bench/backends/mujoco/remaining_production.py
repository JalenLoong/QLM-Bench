"""Fresh100 planning and admission using existing trace/rendition queues."""
import copy
import json
from pathlib import Path
import numpy as np

from .remaining_tasks import TASKS
from .remaining_bindings import binding
from .remaining_scenes import SUPPORT
from .trace import sha, write_json, verify_trace
from .quality import analyze_trace
from .rendition import audit_trace, RecordingIntegrityError
from .native_production import NativeProductionQueue
from .production import QUOTAS
from qlm_bench.compatibility.dataset_v2.pilot_rendition import REMAINING_PRODUCTION_SCHEMA
from qlm_bench.compatibility.dataset_v2.validation import digest

_HASH_CACHE = {}


def check_files(inventory, root=None):
    for name, expected in inventory.items():
        path=Path(name) if root is None else Path(root)/name
        st=path.stat();key=(str(path),st.st_ino,st.st_size,st.st_mtime_ns)
        if key not in _HASH_CACHE:_HASH_CACHE[key]=sha(path)
        if _HASH_CACHE[key]!=expected:raise RecordingIntegrityError('Frozen source changed: '+str(path))


def candidates(task, seed=2026101640):
    lo,hi,nominal=map(np.asarray,SUPPORT[task]);width=hi-lo
    near=width*.005
    rng=np.random.default_rng(seed+TASKS.index(task));prior=[];rows=[]
    for split,quota in QUOTAS.items():
        for difficulty,count in quota.items():
            lower=np.maximum(lo,nominal-width*.05) if difficulty=='clean' else lo
            upper=np.minimum(hi,nominal+width*.05) if difficulty=='clean' else hi
            points=np.stack([(rng.permutation(count)+rng.random(count))/count for _ in lo],axis=1)
            for j,unit in enumerate(points):
                base=lower+unit*(upper-lower);attempts=[]
                uid=f'{task}-20261016-{len(rows)+1:03d}'
                for attempt in range(5):
                    for draw in range(20000):
                        value=base.copy() if attempt==0 and draw==0 else np.clip(base+rng.uniform(-1,1,len(lo))*(upper-lower)*.04,lower,upper)
                        if any(np.array_equal(value,v) or (other!=split and np.all(abs(value-v)<=near)) for v,other in prior):continue
                        break
                    else:raise ValueError('Dedup exhausted; approved support must not shrink')
                    prior.append((value.copy(),split))
                    attempts.append(dict(candidate_id=f'{uid}-c{attempt+1:02d}',seed=42,
                        configuration_parameters=value.tolist(),configuration_sha256=digest(value.tolist())))
                rows.append(dict(episode_uid=uid,task_id=task,split=split,difficulty=difficulty,
                    appearance_preset='ap_00' if difficulty=='clean' else f'ap_{j%2:02d}',candidates=attempts))
    # Engineering admission uses the earliest actual Clean and ap01 Randomized.
    representative=next(s for s in rows if s['difficulty']=='randomized' and s['appearance_preset']=='ap_01')
    rows.remove(representative);rows.insert(1,representative)
    return rows


def load_campaign(path, source_root=None):
    c=json.loads(Path(path).read_text())
    if c.get('schema')!='qlm-approved-six-fresh100-v1' or digest({k:v for k,v in c.items() if k!='profile_sha256'})!=c['profile_sha256']:
        raise RecordingIntegrityError('Frozen fresh100 campaign changed')
    if c['task_id'] not in TASKS or c['pilots'] or len(c['slots'])!=100 or not c['authorization']['remaining_six_approved']:
        raise RecordingIntegrityError('Fresh100 approved task required')
    counts={s:{d:0 for d in ('clean','randomized')} for s in QUOTAS}
    ids=set();lo,hi,_=map(np.asarray,SUPPORT[c['task_id']]);seen=[]
    for slot in c['slots']:
        if slot['episode_uid'] in ids or slot['task_id']!=c['task_id']:raise RecordingIntegrityError('Duplicate or wrong slot')
        ids.add(slot['episode_uid']);counts[slot['split']][slot['difficulty']]+=1
        if slot['difficulty']=='clean' and slot['appearance_preset']!='ap_00':raise RecordingIntegrityError('Clean background')
        for row in slot['candidates']:
            p=np.array(row['configuration_parameters'])
            if p.shape!=lo.shape or np.any(p<lo) or np.any(p>hi) or digest(p.tolist())!=row['configuration_sha256'] or row['seed']!=42:
                raise RecordingIntegrityError('Candidate/support/seed changed')
            for old,split in seen:
                if np.array_equal(old,p) or (split!=slot['split'] and np.all(abs(old-p)<=(hi-lo)*.005)):
                    raise RecordingIntegrityError('Duplicate/near duplicate candidate')
            seen.append((p,slot['split']))
    if counts!=QUOTAS:raise RecordingIntegrityError('Frozen quota mismatch')
    if c['resource_policy']!={'minimum_available_ram_bytes':2**30,'maximum_swap_growth_bytes':8160437862,
        'emergency_render_eviction_available_bytes':2**29,'new_render_minimum_available_bytes':4*2**30}:
        raise RecordingIntegrityError('Resource policy differs')
    if source_root:check_files(c['source']['implementation'],source_root)
    check_files(c['source']['external_files'])
    check_files({c['checkpoint']:c['source']['checkpoint_sha256'],str(Path(c['template_root'])/'template.json'):c['source']['template_sha256']})
    return c


def freeze_episode(c, slot, trace, path):
    actual=audit_trace(trace);m=verify_trace(trace)[0];review,_=analyze_trace(trace)
    source=m['batch_identity']
    if source.get('production_campaign_sha256')!=c['profile_sha256'] or source.get('approval_sha256')!=digest(c['approval']):
        raise RecordingIntegrityError('Actual physical campaign/approval differs')
    if m['backend']['physics']!='native' or m['backend']['controller_device']!='cpu':
        raise RecordingIntegrityError('NativeCPU original RAMBO required')
    member={k:slot[k] for k in ('episode_uid','task_id','split','difficulty','appearance_preset')}
    member.update(trace=str(trace),model=m['scene']['model'],model_identity=m['model_identity'],
        physical_source_sha256=actual['source_identity_sha256'],trace_manifest_sha256=actual['manifest_sha256'],
        physical_trajectory_sha256=actual['trajectory_sha256'],quality=actual['quality'],quality_review_sha256=digest(review),
        review_status='approved_task_recipe_technical_quality',n_actions=m['n_actions'],
        rendition_id=slot['episode_uid']+'@native-cpu-egl-360p-v1',candidate_id=m['scene']['candidate_id'],
        asset_id=m['profile']['asset_id'],seed=m['scene']['seed'])
    p={k:copy.deepcopy(c[k]) for k in ('approval','template_root','python','ffmpeg','ffprobe','render_environment','render_script','work_id','task_id')}
    p.update(schema=REMAINING_PRODUCTION_SCHEMA,profile_id=slot['episode_uid']+'-recording-v1',rgb_profile='dual-rgb-360p-v1',
        quality_policy='evidence-review-v1',maximum_render_attempts=3,slots=[member],production_authorization=c['authorization'],
        campaign_sha256=c['profile_sha256'],recording_source={**c['source'],'stage':'production_offline_recording'},
        template_id=c['source']['template_id'],template_sha256=c['source']['template_sha256'])
    p['profile_sha256']=digest(p)
    if Path(path).exists() and json.loads(Path(path).read_text())!=p:raise RecordingIntegrityError('Existing rendition changed')
    write_json(path,p)
    return member,review


def validate_recording_inputs(profile, slot):
    actual=audit_trace(slot['trace'])
    for a,b in [('manifest_sha256','trace_manifest_sha256'),('trajectory_sha256','physical_trajectory_sha256'),
                ('source_identity_sha256','physical_source_sha256'),('model_identity','model_identity'),('quality','quality')]:
        if actual[a]!=slot[b]:raise RecordingIntegrityError('Frozen trace mismatch: '+b)
    if actual['task_id']!=slot['task_id'] or actual['task_id']!=profile['task_id']:raise RecordingIntegrityError('Wrong task')
    physical=actual['physical_source'];source=profile['recording_source']
    root=Path(source['source_snapshot'])
    check_files(source['implementation'],root);check_files(source['external_files'])
    check_files({str(Path(profile['template_root'])/'template.json'):profile['template_sha256']})
    for k,expected in [('production_campaign_sha256',profile['campaign_sha256']),('approval_sha256',digest(profile['approval'])),
                       ('template_id',profile['template_id']),('template_sha256',profile['template_sha256'])]:
        if physical.get(k)!=expected:raise RecordingIntegrityError('Physical approved source mismatch: '+k)
    review,_=analyze_trace(slot['trace'])
    if digest(review)!=slot['quality_review_sha256']:raise RecordingIntegrityError('Actual quality evidence changed')
    return actual


class RemainingProductionQueue(NativeProductionQueue):
    def __init__(self, root, campaign_path, source_root):
        super().__init__(root,campaign_path,source_root,campaign_loader=load_campaign,freeze_recording=freeze_episode)

    def reconcile(self):
        retained=self.p.get('retained_production_members', {})
        for slot in self.p['slots']:
            uid=slot['episode_uid'];row=self.state['slots'][uid]
            if uid in retained:
                record=retained[uid]
                if sha(self.root/'profiles'/(uid+'.json'))!=record['profile_sha256']:
                    raise RecordingIntegrityError('Retained production profile changed')
                acceptance=self.validate(uid)
                if acceptance['trace']['trajectory_sha256']!=record['trajectory_sha256']:
                    raise RecordingIntegrityError('Retained production trajectory changed')
                row.update(status='accepted',acceptance=acceptance)
            elif (self.output(uid)/'result.json').is_file():
                row.update(status='accepted',acceptance=self.validate(uid))
            elif row.get('trace') and (Path(row['trace'])/'manifest.json').is_file():
                self.retain(slot,row)
            elif row['status']=='physics_running':
                receipt=self.root/'attempts'/(row['scene']['candidate_id']+'.json')
                if receipt.exists() and json.loads(receipt.read_text())['passed']:
                    raise RecordingIntegrityError('Success receipt missing actual trace')
                self.event(uid,'interrupted_physics_retains_attempt_budget');row['status']='planned'
        self.save()
