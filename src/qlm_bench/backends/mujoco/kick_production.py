"""Approved Kick100 planning over the same4D ID support for every split."""
import copy,json
from pathlib import Path
import numpy as np
from .production import QUOTAS
from .trace import sha,verify_trace,write_json
from .quality import analyze_trace
from .rendition import audit_trace,validate_slot_inputs,RecordingIntegrityError
from .native_production import NativeProductionQueue
from qlm_bench.compatibility.dataset_v2.pilot_rendition import KICK_PRODUCTION_SCHEMA,load_profile
from qlm_bench.compatibility.dataset_v2.validation import digest

LIMITS=np.array([.03,.03,.08,.05])
CLEAN_LIMITS=LIMITS*.1
NEAR=np.array([.0005,.0005,.001,.001])


def configuration_candidates(pilots,seed=2026101525):
    rng=np.random.default_rng(seed);prior=[(np.array(s['parameters']),s['split']) for s in pilots];rows=[]
    for split,clean,randomized in [('validation',2,8),('test',2,8),('train',14,56)]:
        for difficulty,count in [('clean',clean),('randomized',randomized)]:
            limit=CLEAN_LIMITS if difficulty=='clean' else LIMITS
            # Independent Latin-hypercube draws use the full identical bounds in each split.
            points=np.stack([(rng.permutation(count)+rng.random(count))/count*2-1 for _ in range(4)],axis=1)*limit
            for point in points:
                index=len(rows)+11;uid=f'kick100-20261015-{index:03d}';candidates=[];base=point.copy()
                for attempt in range(5):
                    for draw in range(20000):
                        value=base.copy() if attempt==0 and draw==0 else np.clip(base+rng.uniform(-1,1,4)*limit*.04,-limit,limit)
                        if any(np.all(np.abs(value-p)<=NEAR) for p,other in prior if other!=split):continue
                        if any(np.array_equal(value,p) for p,_ in prior):continue
                        break
                    else:raise ValueError('Cross-split dedup exhausted; do not shrink approved range')
                    prior.append((value.copy(),split));candidates.append({'candidate_id':f'{uid}-c{attempt+1:02d}','seed':2515000+index*10+attempt,'configuration_parameters':value.tolist(),'configuration_sha256':digest(value.tolist())})
                j=len([s for s in rows if s['split']==split and s['difficulty']==difficulty])
                rows.append({'episode_uid':uid,'task_id':'kick_ball_to_goal','split':split,'difficulty':difficulty,'appearance_preset':'ap_00' if difficulty=='clean' else f'ap_{j%2:02d}','candidates':candidates})
    rows.sort(key=lambda s:({'train':0,'validation':1,'test':2}[s['split']],s['episode_uid']))
    representative=next(s for s in rows if s['difficulty']=='randomized' and s['appearance_preset']=='ap_01');rows.remove(representative);rows.insert(1,representative)
    return rows


def load_campaign(path,source_root=None):
    c=json.loads(Path(path).read_text())
    if c.get('schema')!='qlm-kick100-production-v1' or digest({k:v for k,v in c.items() if k!='profile_sha256'})!=c['profile_sha256']:raise RecordingIntegrityError('Frozen Kick100 campaign changed')
    if not c['authorization'].get('pilot_approved') or c['authorization'].get('target_accepted')!=100 or len(c['pilots'])!=10 or len(c['slots'])!=90 or c['consumer_validation']!='task_already_validated_skip':raise RecordingIntegrityError('Approved ten plus90 without repeated WAM required')
    if c['source'].get('native_trace_profile')!='native-cpu-original-rambo-v1' or c['render_environment']['MUJOCO_GL']!='egl':raise RecordingIntegrityError('Qualified NativeCPU/EGL route required')
    counts={split:{d:0 for d in ('clean','randomized')} for split in QUOTAS};ids=[]
    for s in c['pilots']+c['slots']:
        ids.append(s['episode_uid']);counts[s['split']][s['difficulty']]+=1
        if s['task_id']!='kick_ball_to_goal' or s['difficulty']=='clean' and s['appearance_preset']!='ap_00':raise RecordingIntegrityError('Wrong task or Clean background')
    if counts!=QUOTAS or len(set(ids))!=100:raise RecordingIntegrityError('Wrong quota or duplicate slot')
    if c['resource_policy']!={'minimum_available_ram_bytes':1024**3,'maximum_swap_growth_bytes':8160437862,'emergency_render_eviction_available_bytes':512*1024**2,'new_render_minimum_available_bytes':4*1024**3}:raise RecordingIntegrityError('Frozen user resource policy differs')
    if source_root:
        for name,h in c['source']['implementation'].items():
            if sha(Path(source_root)/name)!=h:raise RecordingIntegrityError('Frozen source changed: '+name)
        if sha(Path(c['template_root'])/'template.json')!=c['source']['template_sha256'] or sha(c['checkpoint'])!=c['source']['checkpoint_sha256']:raise RecordingIntegrityError('Approved recipe/checkpoint changed')
    return c


def freeze_episode(c, slot, trace, path):
    from .kick_quality import analyze_kick
    motion, _ = analyze_kick(trace)
    if motion['behavior_review_holds']:
        raise RecordingIntegrityError('Kick behavior review hold; successful trace retained')
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
    p.update(schema=KICK_PRODUCTION_SCHEMA, profile_id=slot['episode_uid']+'-recording-v1', rgb_profile='dual-rgb-360p-v1',
        quality_policy='evidence-review-v1', maximum_render_attempts=3, slots=[member], production_authorization=c['authorization'],
        campaign_sha256=c['profile_sha256'], recording_source={**c['source'], 'stage':'production_offline_recording'},
        template_sha256=c['source']['template_sha256'], template_id=c['source']['template_id'])
    p['profile_sha256'] = digest(p)
    if Path(path).exists() and json.loads(Path(path).read_text())!=p:
        raise RecordingIntegrityError('Existing rendition changed')
    write_json(path, p)
    validate_slot_inputs(load_profile(path), slot['episode_uid'])
    return member, review


class KickProductionQueue(NativeProductionQueue):
    def __init__(self,root,campaign_path,source_root):
        super().__init__(root,campaign_path,source_root,campaign_loader=load_campaign,freeze_recording=freeze_episode)
