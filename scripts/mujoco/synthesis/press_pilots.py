"""Approved ten-slot Press campaign; independent physics and render-only workers.

One immutable recording profile per successful slot permits bounded backpressure.
The campaign, rather than individual render profiles, owns the exact2/8 quota.
"""
import argparse
import concurrent.futures as futures
import copy
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
from qlm_bench.backends.mujoco.trace import sha, write_json, verify_trace
from qlm_bench.compatibility.dataset_v2.validation import digest

REPO = Path(__file__).resolve().parents[3]
WORKSPACE = REPO.parents[1]
DATA = WORKSPACE / 'data/qlm_bench/press-approved-pilot-20261015-v1'
WORK_ID = 'QLM-DATA-018'


def implementation():
    return {str(p.relative_to(REPO)): sha(p) for folder in ('src/qlm_bench', 'scripts/mujoco/synthesis')
            for p in sorted((REPO / folder).rglob('*')) if p.suffix in ('.py', '.json')}


def prepare(root):
    from prepare_backgrounds import prepare as backgrounds
    sys.path.insert(0, str(REPO / 'scripts/mujoco'))
    from build_press_wall import build
    from qlm_bench.backends.mujoco.resources import resource_closure
    approval = json.loads((root / 'approval.json').read_text())
    retarget = json.loads((root / 'retarget/result.json').read_text())
    if not retarget['passed'] or not all(approval[k] for k in ('reference_quality_approved', 'retarget_scope_approved', 'asset_pool_approved')):
        raise ValueError('Approved reference/assets and actual four-corner recheck required')
    config = json.loads((root / 'recipe-config.json').read_text())
    template_root = root / 'template'; template_root.mkdir(exist_ok=False)
    template = {'template_id': 'press-body-carry-v2-approved-20261015', 'recipe_config': config,
                'approved_recipe_sha256': approval['approved_recipe_sha256'],
                'approved_reference_trace_manifest_sha256': approval['approved_reference_trace_manifest_sha256']}
    write_json(template_root / 'template.json', template)
    reference = verify_trace(WORKSPACE / 'runs/audit/press-reference-smoothing-20261015-v1/reference-a02/trace')[0]
    centers = [( .103,.301),(.097,.299),(.07,.28),(.07,.32),(.13,.28),(.13,.32),
               (.085,.315),(.115,.285),(.079,.30),(.121,.30)]
    rng = np.random.default_rng(2026101518); slots = []; seen = set()
    for i, center in enumerate(centers):
        uid = f'press-approved-20261015-{i+1:02d}'
        preset = 'ap_00' if i < 2 else ('ap_00' if i % 2 == 0 else 'ap_01')
        candidates = []
        for j in range(5):
            for draw in range(100):
                yz = np.asarray(center, float)
                if j: yz = np.clip(yz + rng.uniform(-1, 1, 2)*([.0005,.0005] if i<2 else [.002,.0015]), [.07,.28], [.13,.32])
                if digest(yz.tolist()) not in seen: break
            else: raise ValueError('Predeclared candidate deduplication exhausted')
            seen.add(digest(yz.tolist()))
            cid = f'{uid}-c{j+1:02d}'; asset = root / 'resources' / cid
            build(WORKSPACE / 'assets/mujoco/original-press_button-v1-step-rig-lod-a02/scene.xml',
                  WORKSPACE / 'runs/audit/press-reference-20261014-v1/asset-review', 'A', asset, y=yz[0], z=yz[1])
            bg = backgrounds(asset / 'scene.xml', root / 'backgrounds' / cid, work_id=WORK_ID)
            model = Path(next(p['model'] for p in bg['profiles'] if p['preset'] == preset))
            identity = resource_closure(model, require_portable=True)['identity']
            initial = copy.deepcopy(reference['scene']['initial_state']); initial['model_identity'] = identity
            scene = {'candidate_id': cid, 'task_id': 'press_button', 'model': str(model), 'model_identity': identity,
                     'seed': 1518000+i*10+j, 'initial_state': initial, 'asset_id': 'industrial-button',
                     'appearance_preset': preset, 'difficulty': 'clean' if i<2 else 'randomized',
                     'configuration_parameters': yz.tolist(), 'configuration_sha256': digest(yz.tolist())}
            candidates.append(scene)
        slots.append({'episode_uid': uid, 'task_id': 'press_button', 'difficulty': 'clean' if i<2 else 'randomized',
                      'split': 'train', 'appearance_preset': preset, 'coverage_bin': i, 'candidates': candidates})
    configs = [s['configuration_sha256'] for slot in slots for s in slot['candidates']]
    if len(configs) != len(set(configs)): raise ValueError('Duplicate predeclared configurations')
    source = {'work_id': WORK_ID, 'source_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=REPO, text=True).strip(),
              'implementation': implementation(), 'template_id': template['template_id'],
              'template_sha256': sha(template_root / 'template.json'), 'executor_variant': config['recipe_id'],
              'approval_sha256': digest(approval), 'resource_preparation_sha256': sha(REPO/'scripts/mujoco/build_press_wall.py')}
    campaign = {'schema': 'qlm-press-ten-pilot-campaign-v1', 'work_id': WORK_ID, 'task_id': 'press_button',
                'approval': approval, 'source': source, 'slots': slots, 'template_root': str(template_root),
                'maximum_physics_attempts': 30, 'maximum_per_slot': 5, 'maximum_consecutive_failures': 10,
                'physics_workers': 2, 'render_workers': 2, 'maximum_render_backlog': 4,
                'minimum_available_ram_bytes': 2*1024**3, 'maximum_swap_growth_bytes': 512*1024**2,
                'quality_policy': 'evidence-review-v1', 'consumer_validation': 'Press-task-once-Clean-and-Randomized-v2-and-v3',
                'python': str(WORKSPACE/'envs/qlm-mujoco-py312-v1/bin/python'),
                'ffmpeg': str(WORKSPACE/'cache/tools/bin/ffmpeg'), 'ffprobe': str(WORKSPACE/'cache/tools/bin/ffprobe'),
                'render_environment': {'PYTHONPATH': str(REPO/'src'), 'MUJOCO_GL': 'osmesa', 'OMP_NUM_THREADS': '4',
                    'OPENBLAS_NUM_THREADS': '1', 'MESA_SHADER_CACHE_DIR': str(WORKSPACE/'cache/mesa'),
                    'LD_LIBRARY_PATH': str(WORKSPACE/'assets/mujoco/p0-v1/osmesa/root/usr/lib/x86_64-linux-gnu')}}
    campaign['profile_sha256'] = digest(campaign); write_json(root/'campaign.json', campaign)
    for name in source['implementation']:
        target = root/'frozen-source'/name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(REPO/name, target)
    print(json.dumps({'slots':10,'candidates':50,'frozen_campaign':campaign['profile_sha256']}), flush=True)


def checked(root):
    c = json.loads((root/'campaign.json').read_text())
    if digest({k:v for k,v in c.items() if k!='profile_sha256'}) != c['profile_sha256'] or implementation() != c['source']['implementation']:
        raise ValueError('Frozen Press campaign/source changed')
    if sha(Path(c['template_root'])/'template.json') != c['source']['template_sha256'] or digest(json.loads((root/'approval.json').read_text())) != c['source']['approval_sha256']:
        raise ValueError('Frozen approved recipe/approval changed')
    if len(c['slots']) != 10 or [sum(s['difficulty']==d for s in c['slots']) for d in ('clean','randomized')] != [2,8] or any(s['split']!='train' for s in c['slots']):
        raise ValueError('Incorrect ten-pilot quota')
    return c


def motion_evidence(trace):
    _, _, t, commands, _ = verify_trace(trace)
    phase = np.asarray([r['extensions']['expert']['phase'] for r in commands])
    controls = t['controller']; physics = {r['physics_step']:r for r in t['physics']}
    times = np.array([r['timestamp_ns']/1e9 for r in controls])
    selected = phase[np.minimum((times/.02-1e-6).astype(int),len(phase)-1)] == 'approach_base'
    actual = np.rad2deg([physics[r['controller_tick']*5]['joint_position'] for r in controls])[:,[0,4,8]][selected]
    ik = np.rad2deg([r['reference_state'] for r in controls])[:,[0,4,8]][selected]
    return {'joint_order':['FL_hip_roll','FL_thigh','FL_calf'], 'approach_controller_rows':int(selected.sum()),
            'actual_range_deg':np.ptp(actual,axis=0).tolist(),
            'actual_max_10ms_step_deg':np.max(np.abs(np.diff(actual,axis=0)),axis=0).tolist(),
            'IK_max_10ms_step_deg':np.max(np.abs(np.diff(ik,axis=0)),axis=0).tolist(),
            'task_success_separate_from_quality':True, 'metrics_are_not_new_task_predicates':True}


def physics(root, candidate):
    import torch
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    from qlm_bench.backends.mujoco.press_reference_smooth import SmoothPressExecutor
    from qlm_bench.backends.mujoco.resources import resource_closure
    from qlm_bench.backends.mujoco.trace import collect_trace
    from qlm_bench.backends.mujoco.quality import analyze_trace
    c = checked(root); scene = next(s for slot in c['slots'] for s in slot['candidates'] if s['candidate_id']==candidate)
    if resource_closure(scene['model'],require_portable=True)['identity'] != scene['model_identity']: raise ValueError('Frozen asset changed')
    config = json.loads((Path(c['template_root'])/'template.json').read_text())['recipe_config']
    torch.set_num_threads(1); start=time.monotonic()
    rt = MuJoCoRuntime(scene['model'],str(WORKSPACE/'checkpoints/rambo/go2/quadruped/model_2000.pt'),trace_only=True,seed=scene['seed'])
    try:
        if rt.profile.get('appearance_preset','ap_00') != scene['appearance_preset']: raise ValueError('Frozen background differs')
        result = collect_trace(rt,SmoothPressExecutor(config),scene,root/'physical'/candidate/'trace',
            batch_identity={**c['source'],'pilot_campaign_sha256':c['profile_sha256']},quality_policy='evidence-review-v1')
        result['total_wall_s']=time.monotonic()-start
        if result['passed']:
            review,_=analyze_trace(result['trace']); write_json(root/'quality'/(candidate+'.json'),review)
            motion=motion_evidence(result['trace']); write_json(root/'motion'/(candidate+'.json'),motion)
            # These are review holds, never a changed task predicate or unknown-contact rejection.
            if review['contact']['body_contact_boundaries'] or motion['actual_range_deg'][0]>15 or motion['actual_max_10ms_step_deg'][0]>2:
                raise ValueError('Successful task needs actual behavior review; trace retained')
        write_json(root/'physical'/candidate/'result.json',result); print(json.dumps(result),flush=True)
    finally: rt.close()


def freeze_slot(root,c,slot,scene):
    from qlm_bench.backends.mujoco.rendition import audit_trace,validate_slot_inputs
    from qlm_bench.backends.mujoco.quality import analyze_trace
    from qlm_bench.compatibility.dataset_v2.pilot_rendition import PRESS_SCHEMA,load_profile
    trace=root/'physical'/scene['candidate_id']/'trace'; audit=audit_trace(trace); m=verify_trace(trace)[0]; review,_=analyze_trace(trace)
    row={k:slot[k] for k in ('episode_uid','task_id','difficulty','split','appearance_preset')}
    row.update(trace=str(trace),model=scene['model'],model_identity=m['model_identity'],
        physical_source_sha256=audit['source_identity_sha256'],trace_manifest_sha256=audit['manifest_sha256'],
        physical_trajectory_sha256=audit['trajectory_sha256'],quality=audit['quality'],quality_review_sha256=digest(review),
        review_status='eligible_for_ten_pilot_user_review',n_actions=m['n_actions'],rendition_id=slot['episode_uid']+'@dual-rgb-360p-v1',
        candidate_id=scene['candidate_id'],asset_id='industrial-button',seed=scene['seed'])
    p={k:copy.deepcopy(c[k]) for k in ('task_id','work_id','approval','quality_policy','template_root','python','ffmpeg','ffprobe','render_environment')}
    p.update(schema=PRESS_SCHEMA,profile_id=slot['episode_uid']+'-recording-v1',pilot_target=10,pilot_campaign_sha256=c['profile_sha256'],
        rgb_profile='dual-rgb-360p-v1',maximum_render_attempts=3,template_id=c['source']['template_id'],template_sha256=c['source']['template_sha256'],
        recording_source={**c['source'],'stage':'offline-recording','pilot_campaign_sha256':c['profile_sha256']},
        render_script=str(REPO/'scripts/mujoco/synthesis/render_trace.py'),slots=[row])
    p['profile_sha256']=digest(p); path=root/'recording-profiles'/(slot['episode_uid']+'.json'); write_json(path,p)
    validate_slot_inputs(load_profile(path),slot['episode_uid']); return str(path)


def memory():
    values={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()}
    return {'available':values['MemAvailable'],'swap_used':values['SwapTotal']-values['SwapFree']}


def dispatch(root):
    c=checked(root); root.mkdir(parents=True,exist_ok=True); DATA.mkdir(parents=True,exist_ok=True)
    lock=(root/'campaign.lock').open('a'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    path=root/'campaign-state.json'
    state=json.loads(path.read_text()) if path.exists() else {'campaign_sha256':c['profile_sha256'],'status':'running','consecutive_failures':0,
        'slots':{s['episode_uid']:{'status':'planned','physics_attempts':0} for s in c['slots']}}
    if state['campaign_sha256'] != c['profile_sha256'] or any(r['status'] in ('physics_running','render_running','error','review_hold') for r in state['slots'].values()):
        raise ValueError('Ambiguous/interrupted campaign needs explicit evidence reconciliation')
    baseline=memory(); started=time.time(); jobs={}; error=None; resource_reason=None
    def save(): write_json(path,state)
    def event(uid,stage,**data):
        with (root/'attempts.jsonl').open('a') as f:f.write(json.dumps({'unix_s':time.time(),'episode_uid':uid,'stage':stage,**data})+'\n')
    def run(stage,slot,scene=None):
        uid=slot['episode_uid']; row=state['slots'][uid]; env=dict(os.environ);env.update(PYTHONPATH=str(REPO/'src'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
        if stage=='physics':
            cmd=[c['python'],'-u',str(Path(__file__)), 'physics','--root',str(root),'--candidate',scene['candidate_id']]
            log=root/'logs'/(scene['candidate_id']+'.log')
        else:
            cmd=[c['python'],'-u',str(REPO/'scripts/mujoco/synthesis/rerecord_pilots.py'),'--profile',row['recording_profile'],'--output',str(DATA/'slots'/uid)]
            log=root/'logs'/(uid+'-render-dispatch.log')
        log.parent.mkdir(parents=True,exist_ok=True); t=time.monotonic()
        with log.open('a') as f:p=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
        event(uid,stage+'_process',exit_code=p.returncode,wall_s=time.monotonic()-t,log=str(log))
        if p.returncode:raise RuntimeError('Worker failed closed: '+str(log))
        if stage=='physics':return json.loads((root/'physical'/scene['candidate_id']/'result.json').read_text())
        q=json.loads((DATA/'slots'/uid/'recording-queue.json').read_text());return q['slots'][uid]['acceptance']
    try:
        save()
        with futures.ThreadPoolExecutor(max_workers=4) as pool:
            while True:
                mem=memory(); write_json(root/'resource-current.json',mem)
                if mem['available']<c['minimum_available_ram_bytes'] or mem['swap_used']-baseline['swap_used']>c['maximum_swap_growth_bytes']:
                    resource_reason='RAM/swap guard'; state['resource_pressure']=mem
                if not error:
                    active_render=sum(j[0]=='render' for j in jobs.values())
                    for slot in c['slots']:
                        row=state['slots'][slot['episode_uid']]
                        if active_render>=c['render_workers']:break
                        if row['status']=='render_pending':
                            row['status']='render_running';save();jobs[pool.submit(run,'render',slot)]=('render',slot,None);active_render+=1
                if not error and not resource_reason:
                    active=sum(j[0]=='physics' for j in jobs.values());backlog=sum(r['status'] in ('render_pending','render_running') for r in state['slots'].values())
                    for slot in c['slots']:
                        row=state['slots'][slot['episode_uid']]
                        if active>=c['physics_workers'] or backlog+active>=c['maximum_render_backlog']:break
                        if row['status']!='planned':continue
                        if sum(r['physics_attempts'] for r in state['slots'].values())>=c['maximum_physics_attempts'] or state['consecutive_failures']>=c['maximum_consecutive_failures'] or row['physics_attempts']>=c['maximum_per_slot']:
                            error='Predeclared physics budget exhausted';break
                        scene=slot['candidates'][row['physics_attempts']]; row.update(status='physics_running',physics_attempts=row['physics_attempts']+1,scene=scene)
                        event(slot['episode_uid'],'physics_start',candidate_id=scene['candidate_id']);save()
                        jobs[pool.submit(run,'physics',slot,scene)]=('physics',slot,scene);active+=1
                if not jobs:break
                done,_=futures.wait(jobs,timeout=1,return_when=futures.FIRST_COMPLETED)
                for job in done:
                    stage,slot,scene=jobs.pop(job);uid=slot['episode_uid'];row=state['slots'][uid]
                    try:
                        result=job.result()
                        if stage=='physics':
                            event(uid,'physics_result',result=result)
                            if result['passed']:
                                row['recording_profile']=freeze_slot(root,c,slot,scene);row['trace']=result['trace'];row['status']='render_pending';state['consecutive_failures']=0
                            else:row['status']='planned';state['consecutive_failures']+=1
                        else:
                            row.update(status='accepted',acceptance=result);event(uid,'accepted',physical_demo_count=1)
                            print(json.dumps({'accepted':sum(r['status']=='accepted' for r in state['slots'].values()),'episode_uid':uid}),flush=True)
                    except Exception as exc:
                        row['status']='review_hold' if stage=='physics' and (root/'physical'/scene['candidate_id']/'trace/manifest.json').exists() else 'error'
                        error=str(exc);event(uid,'fail_closed',reason=error)
                    save()
        accepted=sum(r['status']=='accepted' for r in state['slots'].values())
        state.update(status='technical_pilots_complete' if accepted==10 else 'stopped',accepted=accepted,reason=error or resource_reason,
            started_unix_s=started,ended_unix_s=time.time(),wall_s=time.time()-started,resource_baseline=baseline,resource_final=memory(),
            physics_workers=2,render_workers=2,pilot_user_quality_review='pending',scale100_started=False);save()
        if error or resource_reason or accepted!=10:raise RuntimeError(error or resource_reason or 'Incomplete pilot campaign')
    finally:fcntl.flock(lock,fcntl.LOCK_UN);lock.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=('prepare','physics','dispatch'));p.add_argument('--root',required=True);p.add_argument('--candidate')
    a=p.parse_args();r=Path(a.root).resolve()
    if a.stage=='physics':physics(r,a.candidate)
    else:{'prepare':prepare,'dispatch':dispatch}[a.stage](r)
