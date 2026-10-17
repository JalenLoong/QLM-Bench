"""Press100 planning and recovery; original physics/controller recipe is reused."""
import concurrent.futures as futures
import copy
import errno
import fcntl
import json
import os
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

import numpy as np
from .trace import sha, write_json, verify_trace
from .production import ProductionQueue, QUOTAS
from .rendition import audit_trace, RecordingIntegrityError
from .quality import analyze_trace
from qlm_bench.compatibility.dataset_v2.validation import digest
from qlm_bench.compatibility.dataset_v2.pilot_rendition import PRESS_PRODUCTION_SCHEMA, load_profile

NOMINAL = np.array([.1, .3])
LIMITS = np.array([.03, .02])
CLEAN_LIMITS = np.array([.003, .001])
NEAR = np.array([.001, .0005])


def configuration_candidates(pilots, seed=2026101519):
    """All splits share ID support; reject concrete close configs, not intervals."""
    rng = np.random.default_rng(seed)
    background_rng = np.random.default_rng(seed+711)
    prior = [(np.array(s['parameters']), s['split']) for s in pilots]
    rows = []
    # Reserve sparse held-out concrete configurations before the denser train set.
    # This avoids an order-dependent exhaustion of the small Clean2D support.
    for split, clean, randomized in [('validation',2,8),('test',2,8),('train',14,56)]:
        for difficulty, count in [('clean',clean),('randomized',randomized)]:
            background_bias=background_rng.integers(0,2,4)
            for j in range(count):
                index=len(rows)+11;uid=f'press100-20261015-{index:03d}'
                limit=CLEAN_LIMITS if difficulty=='clean' else LIMITS
                signs=np.array([1 if j%4 & (1<<k) else -1 for k in range(2)])
                base=None;candidates=[]
                for attempt in range(5):
                    for _ in range(10000):
                        if base is None:
                            offset=rng.uniform(-1,1,2)*limit
                            if difficulty=='randomized':offset=np.abs(offset)*signs
                            yz=NOMINAL+offset
                        else:
                            yz=np.clip(base+rng.uniform(-1,1,2)*([.00015,.0001] if difficulty=='clean' else [.001,.00075]),NOMINAL-limit,NOMINAL+limit)
                        if difficulty=='randomized' and np.max(np.abs(yz-NOMINAL)/LIMITS)<=.25:continue
                        if any(np.all(np.abs(yz-old)<=NEAR) for old,other in prior if other!=split):continue
                        if any(np.array_equal(yz,old) for old,_ in prior):continue
                        break
                    else:raise ValueError('Press concrete-config dedup exhausted; do not shrink approved support')
                    if base is None:base=yz.copy()
                    prior.append((yz.copy(),split))
                    candidates.append({'candidate_id':f'{uid}-c{attempt+1:02d}','seed':1915000+index*10+attempt,
                        'configuration_parameters':yz.tolist(),'configuration_sha256':digest(yz.tolist())})
                preset='ap_00' if difficulty=='clean' else f'ap_{(j//4+int(background_bias[j%4]))%2:02d}'
                rows.append({'episode_uid':uid,'task_id':'press_button','split':split,'difficulty':difficulty,
                    'appearance_preset':preset,'geometry_bin':'near-nominal' if difficulty=='clean' else ''.join('+' if x>0 else '-' for x in signs),
                    'candidates':candidates})
    return sorted(rows,key=lambda s:({'train':0,'validation':1,'test':2}[s['split']],s['episode_uid']))


def translate_press(source,destination,y,z,*,work_id='QLM-DATA-019'):
    """Translate only the passive cap and housing within the qualified wall plane."""
    import mujoco
    from .resources import resource_closure
    source=Path(source);destination=Path(destination)
    original=resource_closure(source,require_portable=True)
    profile=json.loads(source.with_suffix('.task.json').read_text())
    delta=np.array([0.,y-profile['button_rest_front_xyz'][1],z-profile['button_rest_front_xyz'][2]])
    # Decimal endpoint arithmetic (e.g. .3-.02) differs by sub-picometer float error.
    if np.any(np.asarray([y,z]) < np.asarray([.07,.28])-1e-12) or np.any(np.asarray([y,z]) > np.asarray([.13,.32])+1e-12):
        raise ValueError('Outside frozen wall ID support')
    def link_or_copy(src,dst):
        try:os.link(src,dst)
        except OSError as exc:
            if exc.errno!=errno.EXDEV:raise
            shutil.copy2(src,dst)
    shutil.copytree(source.parent,destination,copy_function=link_or_copy)
    tree=ET.parse(source)
    for name in ('primary','task_static'):
        body=tree.find(f"worldbody/body[@name='{name}']")
        if body is None:raise ValueError('Qualified Press assembly missing')
        body.set('pos',' '.join(format(x,'.17g') for x in np.fromstring(body.get('pos'),sep=' ')+delta))
    for name in ('scene.xml','scene.task.json','resource-manifest.json'):(destination/name).unlink()
    tree.write(destination/'scene.xml',encoding='unicode')
    for target in (profile,profile['source_profile']):
        for key in ('button_rest_front_xyz','canonical_goal_position','asset_origin_xyz'):
            if key in target:target[key]=(np.array(target[key])+delta).tolist()
    profile['initial_object_pose_xyzw'][:3]=(np.array(profile['initial_object_pose_xyzw'][:3])+delta).tolist()
    profile['environment_profile']['button_in_plane_yz_m']=[y,z]
    profile['source_asset_preparation']['geometry_root_translation_m']=(np.array(profile['source_asset_preparation']['geometry_root_translation_m'])+delta).tolist()
    profile['wall_position_variant']={'work_id':work_id,'parent_resource_identity':original['identity'],'delta_xyz_m':delta.tolist()}
    write_json(destination/'scene.task.json',profile)
    manifest=json.loads((source.parent/'resource-manifest.json').read_text())
    for name in ('scene.xml','scene.task.json'):manifest['files'][name]={'sha256':sha(destination/name),'size_bytes':(destination/name).stat().st_size}
    write_json(destination/'resource-manifest.json',manifest)
    a=mujoco.MjModel.from_xml_path(str(source));b=mujoco.MjModel.from_xml_path(str(destination/'scene.xml'))
    expected=a.body_pos.copy()
    for name in ('primary','task_static'):expected[mujoco.mj_name2id(a,mujoco.mjtObj.mjOBJ_BODY,name)]+=delta
    np.testing.assert_allclose(b.body_pos,expected,atol=1e-14,rtol=0)
    static=mujoco.mj_name2id(a,mujoco.mjtObj.mjOBJ_BODY,'task_static')
    if a.body_mass[static]!=0 or b.body_mass[static]!=0:raise ValueError('Housing must remain massless static world geometry')
    # MuJoCo recomputes dummy inertial/frame optimization caches for this massless body.
    # Dynamic inertia and the actual fixed-camera poses must still be exact.
    expected_ipos=a.body_ipos.copy();expected_ipos[static]=b.body_pos[static]
    np.testing.assert_array_equal(b.body_ipos,expected_ipos)
    for key in ('body_sameframe','body_simple'):
        keep=np.arange(a.nbody)!=static;np.testing.assert_array_equal(getattr(a,key)[keep],getattr(b,key)[keep])
    da=mujoco.MjData(a);db=mujoco.MjData(b);mujoco.mj_forward(a,da);mujoco.mj_forward(b,db)
    np.testing.assert_array_equal(a.cam_mode,np.zeros(a.ncam,dtype=a.cam_mode.dtype))
    np.testing.assert_array_equal(da.cam_xpos,db.cam_xpos);np.testing.assert_array_equal(da.cam_xmat,db.cam_xmat)
    for name in dir(a):
        if name.startswith(('body_','jnt_','dof_','geom_','cam_','actuator_','eq_','tendon_','pair_','exclude_','mesh_')) and name not in ('body_pos','body_ipos','body_sameframe','body_simple','cam_poscom0'):
            x,yvalue=getattr(a,name),getattr(b,name)
            if isinstance(x,np.ndarray):np.testing.assert_array_equal(x,yvalue,err_msg=name)
    for name in ('qpos0','qpos_spring'):np.testing.assert_array_equal(getattr(a,name),getattr(b,name))
    for name in dir(a.opt):
        if name.startswith('_'):continue
        x,yvalue=getattr(a.opt,name),getattr(b.opt,name)
        if isinstance(x,np.ndarray):np.testing.assert_array_equal(x,yvalue,err_msg='opt.'+name)
        elif isinstance(x,(int,float,bool)) or isinstance(getattr(x,'value',None),int):
            if x!=yvalue:raise ValueError('Physics option changed: '+name)
    return resource_closure(destination/'scene.xml',require_portable=True)


def load_campaign(path,source_root=None):
    c=json.loads(Path(path).read_text())
    if c.get('schema')!='qlm-press100-production-v1' or digest({k:v for k,v in c.items() if k!='profile_sha256'})!=c['profile_sha256']:
        raise RecordingIntegrityError('Frozen Press100 campaign changed')
    if c['authorization'].get('pilot_approved') is not True or len(c['pilots'])!=10 or len(c['slots'])!=90 or c['consumer_validation']!='task_already_validated_skip':
        raise RecordingIntegrityError('Approved10 plus90 without repeated WAM validation required')
    quotas={s:{d:0 for d in ('clean','randomized')} for s in QUOTAS};ids=[]
    for s in c['pilots']+c['slots']:
        ids.append(s['episode_uid']);quotas[s['split']][s['difficulty']]+=1
        if s['task_id']!='press_button' or (s['difficulty']=='clean' and s['appearance_preset']!='ap_00'):raise RecordingIntegrityError('Wrong task/Clean background')
    if quotas!=QUOTAS or len(set(ids))!=100:raise RecordingIntegrityError('Wrong final quota/identity')
    if source_root:
        for name,h in c['source']['implementation'].items():
            if sha(Path(source_root)/name)!=h:raise RecordingIntegrityError('Frozen source changed: '+name)
        if sha(Path(c['template_root'])/'template.json')!=c['source']['template_sha256']:raise RecordingIntegrityError('Approved recipe changed')
    return c


def freeze_episode(c,slot,trace,path):
    from .rendition import validate_slot_inputs
    audit=audit_trace(trace);m=verify_trace(trace)[0];review,_=analyze_trace(trace)
    member={k:slot[k] for k in ('episode_uid','task_id','split','difficulty','appearance_preset')}
    member.update(trace=str(trace),model=m['scene']['model'],model_identity=m['model_identity'],physical_source_sha256=audit['source_identity_sha256'],
        trace_manifest_sha256=audit['manifest_sha256'],physical_trajectory_sha256=audit['trajectory_sha256'],quality=audit['quality'],quality_review_sha256=digest(review),
        review_status='approved_task_recipe_technical_quality',n_actions=m['n_actions'],rendition_id=slot['episode_uid']+'@production360p-v1',
        candidate_id=m['scene']['candidate_id'],asset_id=m['profile']['asset_id'],seed=m['scene']['seed'])
    p={k:copy.deepcopy(c[k]) for k in ('approval','template_root','python','ffmpeg','ffprobe','render_environment','render_script','work_id','task_id')}
    p.update(schema=PRESS_PRODUCTION_SCHEMA,profile_id=slot['episode_uid']+'-recording-v1',rgb_profile='dual-rgb-360p-v1',quality_policy='evidence-review-v1',
        maximum_render_attempts=3,slots=[member],production_authorization=c['authorization'],campaign_sha256=c['profile_sha256'],
        recording_source={**c['source'],'stage':'production_offline_recording'},template_sha256=c['source']['template_sha256'],template_id=c['source']['template_id'])
    p['profile_sha256']=digest(p)
    if Path(path).exists():
        if json.loads(Path(path).read_text())!=p:raise RecordingIntegrityError('Existing Press rendition differs')
    else:write_json(path,p)
    validate_slot_inputs(load_profile(path),member['episode_uid']);return member,review


def memory():
    v={l.split(':')[0]:int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines()}
    return {'available':v['MemAvailable'],'swap_used':v['SwapTotal']-v['SwapFree']}


class PressProductionQueue(ProductionQueue):
    def __init__(self,root,campaign_path,source_root):
        self.root=Path(root);self.path=self.root/'queue.json';self.campaign_path=Path(campaign_path);self.source_root=Path(source_root)
        self.p=load_campaign(campaign_path,source_root);self.root.mkdir(parents=True,exist_ok=True)
        self.state=json.loads(self.path.read_text()) if self.path.exists() else {'profile_sha256':self.p['profile_sha256'],'status':'running','retained_pilots':10,
            'consecutive_failures':0,'slots':{s['episode_uid']:{'status':'planned','physical_attempts':0} for s in self.p['slots']}}
        if self.state['profile_sha256']!=self.p['profile_sha256']:raise RecordingIntegrityError('Queue/campaign mismatch')
        self.save()

    def retain(self,slot,row):
        member,review=freeze_episode(self.p,slot,row['trace'],self.root/'profiles'/f"{slot['episode_uid']}.json")
        write_json(self.root/'quality'/f"{slot['episode_uid']}.json",review)
        known={s['physical_trajectory_sha256'] for s in self.p['pilots']}
        known.update(r['trajectory_sha256'] for uid,r in self.state['slots'].items() if uid!=slot['episode_uid'] and 'trajectory_sha256' in r)
        if member['physical_trajectory_sha256'] in known:raise RecordingIntegrityError('Duplicate actual trajectory')
        row.update(status='render_pending',trajectory_sha256=member['physical_trajectory_sha256']);self.save()

    def run_parallel(self,physics_workers=4,render_workers=4):
        lock=(self.root/'queue.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        epoch=f'launch-{time.time_ns()}';start=time.time();baseline=memory();jobs={};error=None;pressure=None
        policy={'epoch':epoch,'started_unix_s':start,'physics_workers':physics_workers,'render_workers':render_workers,'maximum_pending_with_inflight':8,
            'minimum_available_RAM_bytes':2*1024**3,'maximum_swap_growth_bytes':512*1024**2,'campaign_sha256':self.p['profile_sha256'],
            'orchestrator_sha256':sha(__file__),'resource_baseline':baseline,'status':'running'}
        self.state.update(status='running',execution_policy=epoch);self.state.pop('reason',None);self.save()
        write_json(self.root/'execution-policies'/(epoch+'.json'),policy)
        try:
            self.reconcile()
            with futures.ThreadPoolExecutor(max_workers=physics_workers+render_workers) as pool:
                while self.accepted()<100 or jobs:
                    mem=memory();write_json(self.root/'resource-current.json',mem)
                    if mem['available']<policy['minimum_available_RAM_bytes'] or mem['swap_used']-baseline['swap_used']>policy['maximum_swap_growth_bytes']:
                        if pressure is None:self.event(None,'resource_pressure_drain',**mem,execution_policy=epoch)
                        pressure=mem
                    active_p=sum(j[0]=='physics' for j in jobs.values());active_r=sum(j[0]=='render' for j in jobs.values())
                    pending=sum(r['status'] in ('render_pending','rendering') for r in self.state['slots'].values())
                    if error is None:
                        load_campaign(self.campaign_path,self.source_root)
                        # Drain success traces even after pressure, without starting new physics.
                        for s in self.p['slots']:
                            r=self.state['slots'][s['episode_uid']]
                            if r['status']=='render_pending' and active_r<render_workers and mem['available']>=2*1024**3:
                                r['status']='rendering';self.save();self.event(s['episode_uid'],'render_started',physical_execution=False,execution_policy=epoch)
                                jobs[pool.submit(self.render_job,s['episode_uid'])]=('render',s,r);active_r+=1
                        while pressure is None and active_p<physics_workers and pending+active_p<8:
                            s=next((s for s in self.p['slots'] if self.state['slots'][s['episode_uid']]['status']=='planned'),None)
                            if s is None:break
                            r=self.state['slots'][s['episode_uid']];attempt=r['physical_attempts']
                            if attempt>=5 or sum(v['physical_attempts'] for v in self.state['slots'].values())>=270 or self.state['consecutive_failures']>=10:
                                error='Frozen candidate budget exhausted';break
                            scene=copy.deepcopy(s['candidates'][attempt]);trace=self.root/'traces'/scene['candidate_id']
                            r.update(status='physics_running',physical_attempts=attempt+1,scene=scene,trace=str(trace));self.save()
                            self.event(s['episode_uid'],'physics_started',candidate_id=scene['candidate_id'],execution_policy=epoch)
                            jobs[pool.submit(self.physics_job,scene,trace)]=('physics',s,r);active_p+=1
                    if not jobs:
                        if pressure or error:break
                        if self.accepted()!=100:raise RuntimeError('Queue stalled')
                        break
                    done,_=futures.wait(jobs,timeout=1,return_when=futures.FIRST_COMPLETED)
                    for job in done:
                        stage,s,r=jobs.pop(job);uid=s['episode_uid']
                        try:
                            result=job.result()
                            if stage=='physics':
                                self.event(uid,'physics_result',candidate_id=r['scene']['candidate_id'],result=result,execution_policy=epoch)
                                if result['passed']:self.state['consecutive_failures']=0;self.retain(s,r)
                                else:r['status']='planned';self.state['consecutive_failures']+=1
                            else:r.update(status='accepted',acceptance=result);self.event(uid,'accepted',total=self.accepted(),execution_policy=epoch)
                            print(json.dumps({'accepted':self.accepted(),'stage':stage,'episode_uid':uid,'physics_workers':physics_workers,'render_workers':render_workers}),flush=True)
                        except Exception as exc:
                            r['status']='review_hold' if stage=='physics' and (Path(r['trace'])/'manifest.json').exists() else 'error'
                            error=str(exc);self.event(uid,'fail_closed',reason=error)
                        self.save()
            if error:raise RuntimeError(error)
            self.state.update(status='production_complete' if self.accepted()==100 else 'resource_pressure_drained',resource_pressure=pressure);self.save()
            policy.update(status=self.state['status'],resource_pressure=pressure,accepted=self.accepted())
        except BaseException as exc:
            self.state.update(status='stopped',reason=str(exc));self.save();policy.update(status='stopped',reason=str(exc));raise
        finally:
            policy.update(ended_unix_s=time.time(),wall_s=time.time()-start,resource_final=memory());write_json(self.root/'execution-policies'/(epoch+'.json'),policy)
            fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
