"""Portable declared EvalCases and the existing synchronous learned-policy executor.

Preparation reads only published test initialization/provenance. Neither the live
executor nor the resource resolver reads demonstration actions or future frames.
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import math
import os
from pathlib import Path
import shutil

from qlm_bench.data import under
from qlm_bench.evaluation import EvalCase, EvaluationProtocol, TrialSpec, EvaluationRunner, write_result
from qlm_bench.policy_interface import ObservationProfile
from qlm_bench.policy_interface.physical import CAMERAS, ROOT_FIELDS

RELEASE = 'mujoco-standard-test100-v1'
CONTROLLER = 'rambo-original-model2000-case-rng-v1'
RUNTIME = 'mujoco-native-original-v1'
HORIZONS = dict(push_box=24, press_button=24, lift_basket=24, kick_ball_to_goal=24,
                sweep_block_to_zone=40, close_fridge_door=40, close_oven_door=60,
                turn_valve=32, pull_open_drawer=40, open_room_door=60)
SEMANTICS = dict(reference='root_link', quaternion='xyzw', velocity_frame='world',
                 projected_gravity_frame='body', ground_z=0., ground_reference='push-box-v2-plane-world-z0')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024**2), b''): h.update(block)
    return h.hexdigest()


def protocol(cases, source, *, engineering=False):
    budgets = {c.task_id: 200 if engineering else HORIZONS[c.task_id]*50 for c in cases}
    trials = tuple(TrialSpec('trial-'+c.case_id+f'-{i:03d}', c.case_id, c.task_id, 42)
                   for i,c in enumerate(cases))
    spec = hashlib.sha256(json.dumps([c.record() for c in cases], sort_keys=True).encode()).hexdigest()
    return EvaluationProtocol(RELEASE+('-engineering' if engineering else ''), RELEASE, RELEASE,
        RUNTIME, CONTROLLER, max(budgets.values()), 'exclude_and_retry', 'first_non_error_attempt',
        'engineering_diagnostic' if engineering else 'benchmark', 'draft' if engineering else 'verified',
        trials, {'source_commit': source, 'spec_sha256': spec}, budgets)


def prepare(snapshot, destination, *, authorization, source_commit):
    """Freeze all100 existing held-out configurations; create no execution records."""
    from .resources import resource_closure
    from qlm_bench.compatibility.rgb_profiles import dataset_profile, RGB_360
    from qlm_bench.compatibility.dataset_v2.validation import PROFILE
    from qlm_bench.tasks.prompts import current_instruction_profile
    from qlm_bench.assets import validate_manifest
    snapshot, destination = Path(snapshot), Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    bench = destination/'benchmarks'/RELEASE
    catalog = read(Path(__file__).parents[2]/'data/spec/mujoco1000_catalog.json')
    authorization = Path(authorization); auth = read(authorization)
    if auth.get('private_dataset') != 'dontKnow23456/QLM-Bench' or not auth.get('license_confirmation'):
        raise ValueError('Explicit private runtime/controller redistribution evidence required')
    resources = {}; cases = []; content = {}; hashes = {}
    def copy_pack(model, asset, version, closure, kind='asset', source=None):
        prefix = f'assets/{asset}/{version}'
        runtime = destination/prefix/'runtime'; runtime.mkdir(parents=True)
        files = {}
        for name,h in closure['files'].items():
            src = Path(model).parent/name; target = under(runtime, name); target.parent.mkdir(parents=True, exist_ok=True)
            # New staging inodes; deduplicate only inside the immutable stage.
            if h in content: os.link(content[h], target)
            else: shutil.copyfile(src, target); content[h] = target
            files[name] = {'size_bytes':src.stat().st_size, 'sha256':h}
        license = {'id':'upstream-attribution-preserved', 'redistribution_status':'user_confirmed_private_dataset',
                   'attribution':'Original retained QLM asset/controller provenance and upstream attribution',
                   'source_evidence_sha256':sha(authorization), 'scope':'private:dontKnow23456/QLM-Bench'}
        manifest = dict(schema='qlm-resource-manifest-v1',kind=kind,asset_id=asset,version=version,
            entrypoint=Path(model).name, cache_subdir=prefix+'/runtime', source=source or {'provider':'retained_approved_pack'},
            geometry={'original_bytes':True}, physics={'parameters_changed':False}, license=license, files=files,
            dependency_validation={'closed':True,'unresolved':[]}, resource_identity=closure.get('identity'),
            publication_status='candidate_not_uploaded')
        validate_manifest(manifest, for_publication=True)
        write(destination/prefix/'manifest.json', manifest)
        target=destination/prefix/'licenses/source-evidence.json';target.parent.mkdir(parents=True);shutil.copyfile(authorization,target)
        return {'manifest':prefix+'/manifest.json','manifest_sha256':sha(destination/prefix/'manifest.json'),
                'entrypoint':prefix+'/runtime/'+Path(model).name,'resource_identity':closure.get('identity')}
    for entry in catalog['demonstrations']:
        ref=entry['ref']; release_path=under(snapshot,ref['manifest'])
        if sha(release_path)!=ref['manifest_sha256']:raise ValueError('Training release manifest changed')
        release=read(release_path); test=set(release['split']['test'])
        selected=sorted((x for x in release['episodes'] if x['episode_uid'] in test),key=lambda x:x['canonical_episode_index'])
        if len(selected)!=10 or sum(x['difficulty']=='clean' for x in selected)!=2:raise ValueError('Standard test membership changed')
        for episode in selected:
            bpath=under(snapshot,episode['snapshot_bundle']); trace_path=bpath.parent/'source-trace-manifest.json'
            if sha(bpath)!=episode['snapshot_bundle_sha256'] or sha(trace_path)!=episode['source_trace_manifest_sha256']:
                raise ValueError('Published physical initialization provenance changed')
            bundle,trace=read(bpath),read(trace_path);model=Path(trace['scene']['model']); closure=resource_closure(model,require_portable=True,hash_cache=hashes)
            if closure['identity']!=bundle['model_identity']:raise ValueError('Held-out model identity differs')
            p=current_instruction_profile(read(model.with_suffix('.task.json'))); identity=closure['identity']
            if identity not in resources:resources[identity]=copy_pack(model,p['asset_id'],identity,closure)
            frozen=dataset_profile(PROFILE,RGB_360)
            observation=ObservationProfile('qlm-measured-root-link-dual-rgb-360p-v1',CAMERAS,ROOT_FIELDS,True,SEMANTICS)
            initial=deepcopy(trace['scene']['initial_state']); initial.pop('schema'); initial.pop('model_identity');initial['simulation_time_ns']=0
            case=EvalCase(episode['episode_uid'],entry['task'],p['asset_profile'],entry['instruction'],observation,
                {p['asset_id']:identity}, initial,
                {'position':trace['scene'].get('canonical_goal_position',p['canonical_goal_position']),'task_profile':p['asset_profile']},
                {'resource_identity':identity,'horizon_s':HORIZONS[entry['task']], 'render_backend':'egl',
                 'goal_overlay':{k:trace['scene'][k] for k in ('goal_x','goal_y','canonical_goal_position') if k in trace['scene']},
                 'difficulty':episode['difficulty'],'canonical_episode_index':episode['canonical_episode_index']},
                frozen['policy_camera_geometry'],trace['scene']['seed'],CONTROLLER,RUNTIME,
                {'kind':'explicit_published_initial_state','physics_steps_during_reset':0,'clear_controller_history':True},
                {'source_ref':ref,'source_episode':episode['episode_uid'],'source_trace_manifest_sha256':sha(trace_path),
                 'snapshot_bundle_sha256':sha(bpath),'evidence_kind':'declared_not_verified'},'draft')
            cases.append(case);write(bench/'cases'/f'{case.case_id}.json',case.record())
    rambo=Path(auth.get('rambo_root',str(authorization.parents[3]/'checkpoints/rambo/go2/quadruped')))
    # Explicit origin path is supplied by the authorized producer; never used by consumers.
    if not (rambo/'model_2000.pt').is_file():raise FileNotFoundError('RAMBO acquired source root required in authorization')
    rambo_files={n:sha(rambo/n) for n in ('model_2000.pt','agent.yaml','env.yaml')}
    if rambo_files['model_2000.pt']!='1cc5f68fe15e37ccabae26060d79a26a8c078ed465a81f6f729c2009b67ca706':raise ValueError('RAMBO source changed')
    controller=copy_pack(rambo/'model_2000.pt','rambo-go2-controller','iteration-2000',{'files':rambo_files},'controller',
        {'provider':'huggingface','repository':'dontKnow23456/rambo-go2-policies','revision':'65fa7b035ad16af78c2af2d64a3ac4aed9c81fdc','path':'quadruped/model_2000.pt'})
    write(bench/'resource_registry_snapshot.json',{'schema':'qlm-evaluation-resources-v1','resources':resources,'controller':controller})
    write(bench/'protocol_snapshot.json',{'source_identity':{'source_commit':source_commit},'spec':protocol(cases,source_commit).record()})
    write(bench/'manifest.json',{'schema':'qlm-benchmark-manifest-v1','benchmark_release':RELEASE,'source_commit':source_commit,
        'validation_status':'draft','case_ids':[c.case_id for c in cases],'snapshots':{},'case_validation':{},'evidence_files':{},
        'execution_status':'NOT_RUN','formal_score_available':False})
    return bench


def resource(stage, row):
    from qlm_bench.assets import validate_manifest, verify_payload
    stage=Path(stage); path=under(stage,row['manifest'])
    if sha(path)!=row['manifest_sha256']:raise ValueError('Resource registry manifest hash mismatch')
    m=read(path);validate_manifest(m,for_publication=True);runtime=under(stage,m['cache_subdir']);verify_payload(m,runtime)
    if row['entrypoint']!=m['cache_subdir']+'/'+m['entrypoint']:raise ValueError('Resource entrypoint mismatch')
    if m.get('resource_identity')!=row.get('resource_identity'):raise ValueError('Resource identity binding mismatch')
    return under(runtime,m['entrypoint'])


def reconstruct(runtime, case):
    import numpy as np
    from qlm_bench.compatibility.rgb_profiles import dataset_profile, RGB_360
    from qlm_bench.compatibility.dataset_v2.validation import PROFILE
    if case.task_id!=runtime.profile['task_id'] or case.instruction!=runtime.profile['instruction']:
        raise ValueError('Case task/instruction differs from runtime')
    identity=runtime.physics.model_identity
    if dict(case.assets)!={runtime.profile['asset_id']:identity} or case.scene['resource_identity']!=identity:
        raise ValueError('Case resource differs from runtime')
    if case.runtime_profile!=RUNTIME or case.controller_profile!=CONTROLLER or case.task_version!=runtime.profile['asset_profile']:
        raise ValueError('Case runtime/controller/task version differs')
    if case.goal!={'position':runtime.profile['canonical_goal_position'],'task_profile':runtime.profile['asset_profile']}:
        raise ValueError('Case goal differs from the declared runtime overlay')
    if dict(case.cameras)!=dataset_profile(PROFILE,RGB_360)['policy_camera_geometry'] or case.initial_state['simulation_time_ns']!=0:
        raise ValueError('Case camera/initial clock mismatch')
    runtime.set_case_seed(case.seed)
    initial={'schema':'qlm-mujoco-initial-state-v1','model_identity':identity,
             'qpos':case.initial_state['qpos'],'qvel':case.initial_state['qvel']}
    raw=runtime.reset(initial_state=initial);s=runtime.physics.snapshot()
    for k in ('qpos','qvel'):np.testing.assert_allclose(s[k],initial[k],atol=1e-6,rtol=0)
    if raw['physics_step'] or raw['simulation_time_ns'] or runtime.history:raise ValueError('Reset advanced clock/history')
    if runtime.core.control_ticks.item()!=0 or runtime.core.time_since_reset.item()!=0:raise ValueError('Controller reset clock changed')
    return raw


def runtime_for(stage, bench, case, *, horizon=None):
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.backends.controller import ControllerRuntimeAdapter
    if os.environ.get('MUJOCO_GL')!='egl' or case.scene.get('render_backend')!='egl':
        raise ValueError('This suite requires the explicit EGL renderer; no fallback')
    registry=read(Path(bench)/'resource_registry_snapshot.json')
    model=resource(stage,registry['resources'][case.scene['resource_identity']]);checkpoint=resource(stage,registry['controller'])
    kwargs=dict(model_path=model,checkpoint=checkpoint,seed=case.seed,device='cpu',trace_only=False,
                rgb_profile='dual-rgb-360p-v1')
    overlay={**case.scene.get('goal_overlay',{}),'horizon_s':case.scene['horizon_s'] if horizon is None else horizon}
    # Both runtime families accept the same explicit immutable episode overlay.
    kwargs['profile_override']=overlay
    r=create_runtime(case.task_id,'native',**kwargs)
    if any(s in r.renderer.gl_identity['renderer'].lower() for s in ('llvmpipe','softpipe','swrast')):
        r.close();raise ValueError('Software EGL cannot admit the declared hardware EGL runtime')
    return ControllerRuntimeAdapter(r,reconstruct=reconstruct)


def validate_suite(bench):
    """Authenticate frozen JSON, reset evidence and binary source archives before execution."""
    bench=Path(bench);m=read(bench/'manifest.json')
    if m.get('schema')!='qlm-benchmark-manifest-v1' or m.get('validation_status')!='verified':
        raise ValueError('A verified frozen suite is required')
    expected={f'cases/{i}.json' for i in m['case_ids']}
    if set(m.get('case_files',{}))!=expected:raise ValueError('Complete case hash inventory required')
    for group in ('case_files','snapshots','evidence_files','source_archives'):
        for name,h in m.get(group,{}).items():
            if sha(under(bench,name))!=h:raise ValueError('Frozen suite payload changed: '+name)
    from qlm_bench.publication import validate_cases
    cases=[read(bench/name) for name in m['case_files']]
    validate_cases(m,cases)
    return m


def fetch_case(revision, case_id, destination, *, repo_id='dontKnow23456/QLM-Bench'):
    """Explicit exact-file acquisition: suite metadata plus one scene/controller closure."""
    import re
    from huggingface_hub import hf_hub_download
    if not re.fullmatch(r'[0-9a-f]{40}',revision):raise ValueError('A fixed HF revision is required')
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    prefix='benchmarks/'+RELEASE
    def get(name):
        under(destination,name)
        return Path(hf_hub_download(repo_id,name,repo_type='dataset',revision=revision,local_dir=destination))
    manifest=read(get(prefix+'/manifest.json'))
    if case_id not in manifest['case_ids']:raise ValueError('Case is outside the frozen suite')
    for group in ('case_files','snapshots','evidence_files','source_archives'):
        for name,h in manifest.get(group,{}).items():
            if sha(get(prefix+'/'+name))!=h:raise ValueError('Downloaded suite hash mismatch')
    bench=destination/prefix;validate_suite(bench)
    case=EvalCase.from_record(read(bench/'cases'/f'{case_id}.json'));reg=read(bench/'resource_registry_snapshot.json')
    files=[]
    for row in (reg['resources'][case.scene['resource_identity']],reg['controller']):
        m=read(get(row['manifest']))
        if sha(under(destination,row['manifest']))!=row['manifest_sha256']:raise ValueError('Downloaded resource manifest mismatch')
        for name,info in m['files'].items():
            path=m['cache_subdir']+'/'+name
            if sha(get(path))!=info['sha256']:raise ValueError('Downloaded resource payload mismatch')
            files.append(path)
        resource(destination,row)
    return {'passed':True,'repo_id':repo_id,'revision':revision,'case_id':case_id,'runtime_files':len(files),
            'training_payload_downloaded':False,'resource_root':str(destination.resolve()),'suite':str(bench.resolve())}


def verify_cases(stage, bench):
    """Actual reset/RGB evidence, with no physics step and no policy invocation."""
    import numpy as np
    from PIL import Image
    bench=Path(bench);manifest=read(bench/'manifest.json'); reports=[]
    for ident in manifest['case_ids']:
        case=EvalCase.from_record(read(bench/'cases'/f'{ident}.json'))
        adapter=runtime_for(stage,bench,case)
        try:
            adapter.reset(case);raw=adapter.runtime.state();first=adapter.runtime.physics.snapshot()
            before=adapter.runtime.freeze_token();observed=adapter.observe();after=adapter.runtime.freeze_token()
            if before!=after:raise ValueError('Observation changed physics/controller/RNG')
            if set(observed.rgb)!=set(CAMERAS):raise ValueError('Missing policy camera')
            rgb={}
            for name,image in observed.rgb.items():
                if image.shape!=(360,640,3) or image.dtype!=np.uint8 or float(image.std())<1:
                    raise ValueError('Invalid/constant EGL scene feedback: '+name)
                rgb[name]={'sha256':hashlib.sha256(image.tobytes()).hexdigest(),'std':float(image.std()),'shape':list(image.shape)}
            report={'evidence_kind':'actual_runtime','reset_reconstruction_passed':True,'case_id':ident,
                'resource_identity':adapter.runtime.physics.model_identity,'physics_steps_during_reset':0,
                'simulation_time_ns':raw['simulation_time_ns'],'reset_epoch':raw['reset_epoch'],
                'qpos_sha256':hashlib.sha256(first['qpos'].tobytes()).hexdigest(),
                'qvel_sha256':hashlib.sha256(first['qvel'].tobytes()).hexdigest(),'history_empty':not adapter.runtime.history,
                'controller_history_initialized_from_reset_state':bool((adapter.runtime.core._obs_history[:,:-1,:]==0).all()),
                'controller_last_action_zero':bool((adapter.runtime.core._last_action==0).all()),
                'controller_clock_zero':adapter.runtime.core.control_ticks.item()==0,
                'RNG':adapter.runtime.core.case_rng.identity(),'RGB':rgb,'GL':adapter.runtime.renderer.gl_identity,
                'render_backend':'egl','observation_did_not_advance':before==after}
            if not report['controller_history_initialized_from_reset_state'] or not report['controller_last_action_zero']:
                raise ValueError('Reset controller history/action retains prior execution')
            evidence=f'validation/{ident}.json';write(bench/evidence,report);h=sha(bench/evidence)
            case=replace(case,validation_status='verified',provenance={**case.provenance,
                'evidence_kind':'actual_runtime','reset_reconstruction_passed':True,'evidence_sha256':h})
            write(bench/'cases'/f'{ident}.json',case.record());manifest['case_validation'][ident]=case.provenance
            manifest['evidence_files'][evidence]=h;write(bench/'manifest.json',manifest);reports.append(report)
            print(json.dumps({'case_id':ident,'reset_passed':True}),flush=True)
        finally:adapter.close()
    cases=[EvalCase.from_record(read(bench/'cases'/f'{i}.json')) for i in manifest['case_ids']]
    source=manifest['source_commit'];identity={'source_commit':source,'dirty':False,
        'source_tree_sha256':hashlib.sha256(json.dumps([c.record() for c in cases],sort_keys=True).encode()).hexdigest()}
    # Snapshot identity is finalized against the actual source archive by freeze_sources.
    write(bench/'protocol_snapshot.json',{'source_identity':identity,'spec':protocol(cases,source).record()})
    registry=read(bench/'resource_registry_snapshot.json');registry['source_identity']=identity
    write(bench/'resource_registry_snapshot.json',registry)
    manifest['snapshots']={n:sha(bench/n) for n in ('protocol_snapshot.json','resource_registry_snapshot.json')}
    manifest['validation_status']='verified';write(bench/'manifest.json',manifest)
    return {'passed':True,'cases':len(reports),'physics_steps':0,'policy_calls':0}


def main(argv=None):
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare-standard','verify-standard','run-learned','fetch-case'))
    p.add_argument('--snapshot');p.add_argument('--output',required=True);p.add_argument('--authorization');p.add_argument('--source-commit')
    p.add_argument('--resource-root');p.add_argument('--suite');p.add_argument('--policy-port',type=int);p.add_argument('--policy-identity')
    p.add_argument('--engineering',action='store_true');p.add_argument('--case-id',action='append');p.add_argument('--repeat-push',action='store_true')
    p.add_argument('--ffmpeg');p.add_argument('--ffprobe');p.add_argument('--previous-result')
    p.add_argument('--revision')
    a=p.parse_args(argv)
    if a.mode=='fetch-case':
        if not a.revision or not a.case_id or len(a.case_id)!=1:p.error('fetch-case requires fixed revision and one case-id')
        return print(json.dumps(fetch_case(a.revision,a.case_id[0],a.output)))
    if a.mode=='prepare-standard':
        if not all((a.snapshot,a.authorization,a.source_commit)):p.error('prepare requires snapshot/authorization/source-commit')
        print(prepare(a.snapshot,a.output,authorization=a.authorization,source_commit=a.source_commit))
        return 0
    os.environ['MUJOCO_GL']='egl'
    import torch
    torch.set_num_threads(1)
    if not a.resource_root or not a.suite:p.error('Explicit resource-root and suite required')
    if a.mode=='verify-standard':return write(a.output,verify_cases(a.resource_root,a.suite))
    if not a.policy_port or not a.policy_identity:p.error('learned provider requires policy port and exact identity')
    previous=read(a.previous_result)['outcomes'] if a.previous_result else ()
    result=run_learned(a.resource_root,a.suite,a.output,policy_port=a.policy_port,policy_identity=a.policy_identity,
        engineering=a.engineering,selected_case_ids=a.case_id,repeat_push=a.repeat_push,
        ffmpeg=a.ffmpeg,ffprobe=a.ffprobe,previous_outcomes=previous)
    if any(r['outcome'] in ('error','not_run') for r in result['outcomes']):raise SystemExit(1)
    return 0


class LiveExecutor:
    """Episode strategy for EvaluationRunner; all physical execution stays in SynchronousDriver."""
    def __init__(self, client, *, on_event=None):
        self.client=client;self.on_event=on_event or (lambda *a:None);self.drivers={}
        self.last_history=None;self.last_evidence={}

    def __call__(self, adapter, case, trial, budget):
        from qlm_bench.live import SynchronousDriver
        self.last_history=None;self.last_evidence={}
        key=id(adapter.runtime); counts={'predict':0,'feedback':0,'wait':0}; frozen=[True]
        def event(kind,payload):
            if kind=='wait':
                counts['wait']+=1;frozen[0] &= bool(payload['simulation_frozen'])
                if payload['method'] in counts: counts[payload['method']]+=1
            self.on_event(kind,payload)
        driver=self.drivers.get(key)
        if driver is None:
            driver=SynchronousDriver(adapter.runtime,self.client,session_id='evaluation-'+case.task_id,
                instruction=case.instruction,task_id=case.task_id,task_version=case.task_version,
                state_semantics=SEMANTICS,on_event=event,max_groups=math.ceil(budget/16))
            self.drivers[key]=driver
        driver.on_event=event;driver.max_groups=math.ceil(budget/16)
        observed=adapter.observe()
        try:
            driver.reset_episode(observed.episode_uid,policy_seed=trial.policy_seed,initial_snapshot=adapter.runtime.state())
            result=driver.run_episode()
        except BaseException:
            self.last_history=driver.history
            self.last_evidence={'inference_calls':counts['predict'],'feedback_calls':counts['feedback'],
                'rpc_waits':counts['wait'],'all_waits_frozen':frozen[0],
                'simulation_time_ns':adapter.runtime.state()['simulation_time_ns'],
                'closed_loop_status':'PARTIAL_CLOSED_LOOP' if driver.history and driver.history.completed else 'NOT_RUN'}
            self.on_event('partial_execution',{'trial_id':trial.trial_id,'counts':counts,'completed_commands':len(driver.history.completed) if driver.history else 0})
            raise
        adapter._terminal=deepcopy(adapter.runtime.terminal)
        terminal=adapter.terminal()
        closed=counts['predict']>=2 and counts['feedback']>=2 and frozen[0] and result['task_terminal']
        return {'terminal':terminal,'history':driver.history,'simulation_time_ns':result['simulation_time_ns'],
                'inference_calls':counts['predict'],'feedback_calls':counts['feedback'],'rpc_waits':counts['wait'],
                'all_waits_frozen':frozen[0], 'closed_loop_status':'PASS_CLOSED_LOOP' if closed else 'PARTIAL_CLOSED_LOOP'}


def run_learned(stage, bench, output, *, policy_port, policy_identity, engineering=False,
                selected_case_ids=None, repeat_push=False, ffmpeg=None, ffprobe=None, previous_outcomes=()):
    from qlm_bench.live import RPCClient
    from qlm_bench.live.media import ActualRGBRecorder
    manifest=validate_suite(bench);cases=[EvalCase.from_record(read(Path(bench)/'cases'/f'{c}.json')) for c in manifest['case_ids']]
    if selected_case_ids is not None:cases=[c for c in cases if c.case_id in selected_case_ids]
    if not cases:raise ValueError('Explicit nonempty case selection required')
    if engineering:
        first={}
        for c in cases:
            if c.scene['difficulty']=='clean':first.setdefault(c.task_id,c)
        cases=list(first.values())
        if repeat_push:cases.insert(1,next(c for c in cases if c.task_id=='push_box'))
    elif selected_case_ids is not None:
        raise ValueError('Formal suite cannot silently drop expected cases')
    output=Path(output);output.mkdir(parents=True,exist_ok=False); held={}; media={}
    p=protocol(cases,manifest['source_commit'],engineering=engineering)
    identity=read(policy_identity) if isinstance(policy_identity,(str,Path)) else dict(policy_identity)
    required={'code','adapter','observation_profile'}
    if not required<=set(identity):raise ValueError('Exact policy identity required')
    def event(kind,payload):
        from qlm_bench.live.runner import snapshot_receipt
        def normalize(x):
            if hasattr(x,'tobytes'):return {'shape':list(x.shape),'dtype':str(x.dtype),'sha256':hashlib.sha256(x.tobytes()).hexdigest()}
            if isinstance(x,dict):return {k:normalize(v) for k,v in x.items()}
            if isinstance(x,(tuple,list)):return [normalize(v) for v in x]
            return x
        with (output/'events.jsonl').open('a') as f:f.write(json.dumps({'event':kind,**normalize(payload)},allow_nan=False)+'\n')
    executor=LiveExecutor(RPCClient(port=policy_port,timeout_s=600),on_event=event)
    def factory(case):
        if repeat_push and case.case_id in held:return held[case.case_id]
        adapter=runtime_for(stage,bench,case,horizon=4 if engineering else None)
        if ffmpeg and ffprobe:
            recorder=ActualRGBRecorder(output/case.case_id/'actual_media',ffmpeg=ffmpeg,ffprobe=ffprobe,
                identity={'case_id':case.case_id,'scope':p.scope},observer=adapter.runtime.renderer.observer_clip is not None)
            adapter.runtime.on_observation=recorder.observe;adapter.runtime.on_terminal=recorder.seal_terminal
            media[case.case_id]=recorder
        if repeat_push:
            held[case.case_id]=adapter;adapter.close=lambda:None
        return adapter
    runner=EvaluationRunner(p,{c.case_id:c for c in cases},runtime_factory=factory,provider_factory=lambda _:None,
        source_commit=manifest['source_commit'],policy_identity=identity,evidence_kind='actual_runtime',episode_executor=executor)
    try:
        result=runner.run(submission_id=output.name,benchmark_release=RELEASE if not engineering else None,previous_outcomes=previous_outcomes)
        write_result(output/'result',result['run_manifest'],result['outcomes']);write(output/'result.json',result)
    finally:
        for recorder in media.values():recorder.close()
        for adapter in held.values():adapter.runtime.close()
    return result
