"""Standard100: the frozen held-out cases of QLM-Bench and their exact MuJoCo reconstruction.

``mujoco-standard-test100-v1`` holds the test split of the ten demonstration releases: ten scene
configurations per task (2 Clean + 8 Randomized), each with its published initial state, goal overlay,
scene pack and seed. Preparation reads only published test initial states; neither case reconstruction
nor the runner reads demonstration actions or future frames.
"""
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil

from qlm_bench.data import under
from qlm_bench.benchmark.cases import EvalCase, EvaluationProtocol, TrialSpec
from qlm_bench.contracts.policy import ObservationProfile
from qlm_bench.contracts.policy.physical import CAMERAS, ROOT_FIELDS

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


def protocol(cases):
    """Standard100 protocol: one trial per case at policy seed 42, budget = task horizon x 50 Hz,
    errors excluded and retried (the first non-error attempt counts)."""
    budgets = {c.task_id: HORIZONS[c.task_id]*50 for c in cases}
    trials = tuple(TrialSpec('trial-'+c.case_id+f'-{i:03d}', c.case_id, c.task_id, 42)
                   for i,c in enumerate(cases))
    return EvaluationProtocol(RELEASE, RELEASE, RELEASE, RUNTIME, CONTROLLER, max(budgets.values()),
        'exclude_and_retry', 'first_non_error_attempt', 'benchmark', 'verified', trials, {}, budgets)


def prepare(snapshot, destination, *, controller_root, catalog=None, model_map=None):
    """Maintainer tool: freeze the 100 test-split configurations of a QLM-Bench dataset snapshot into a suite.

    Writes ``benchmarks/<RELEASE>/{cases/,resource_registry_snapshot.json,protocol_snapshot.json,manifest.json}``
    and the scene/controller packs under ``assets/``. Run ``verify`` afterwards to reconstruct every case."""
    from qlm_bench.backends.mujoco.resources import resource_closure
    from qlm_bench.contracts.rgb_profiles import dataset_profile, RGB_360
    from qlm_bench.data.lerobot.validation import PROFILE
    from qlm_bench.tasks.prompts import current_instruction_profile
    snapshot, destination = Path(snapshot), Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    bench = destination/'benchmarks'/RELEASE
    catalog = read(catalog or Path(__file__).parents[1]/'data/spec/catalog.json')
    resources = {}; cases = []; content = {}; hashes = {}
    def copy_pack(model, asset, version, files, kind='asset'):
        prefix = f'assets/{asset}/{version}'
        runtime = destination/prefix/'runtime'; runtime.mkdir(parents=True)
        listed = {}
        for name,h in files.items():
            src = Path(model).parent/name; target = under(runtime, name); target.parent.mkdir(parents=True, exist_ok=True)
            if h in content: os.link(content[h], target)
            else: shutil.copyfile(src, target); content[h] = target
            listed[name] = {'size_bytes':src.stat().st_size, 'sha256':h}
        manifest = dict(schema='qlm-resource-manifest-v1', kind=kind, asset_id=asset, version=version,
                        entrypoint=Path(model).name, cache_subdir=prefix+'/runtime', files=listed,
                        resource_identity=version if kind == 'asset' else None)
        write(destination/prefix/'manifest.json', manifest)
        return {'manifest':prefix+'/manifest.json','entrypoint':prefix+'/runtime/'+Path(model).name,
                'resource_identity':manifest['resource_identity']}
    for entry in catalog['demonstrations']:
        ref=entry['ref']; release=read(under(snapshot,ref['manifest'])); test=set(release['split']['test'])
        selected=sorted((x for x in release['episodes'] if x['episode_uid'] in test),key=lambda x:x['canonical_episode_index'])
        if len(selected)!=10 or sum(x['difficulty']=='clean' for x in selected)!=2:raise ValueError('Each task needs 10 test episodes (2 Clean)')
        for episode in selected:
            bpath=under(snapshot,episode['snapshot_bundle']); trace_path=bpath.parent/'source-trace-manifest.json'
            bundle,trace=read(bpath),read(trace_path)
            model=Path((model_map or {}).get(bundle['model_identity'],trace['scene']['model']))
            closure=resource_closure(model,require_portable=True,hash_cache=hashes)
            if closure['identity']!=bundle['model_identity']:raise ValueError('Scene pack differs from the episode scene')
            p=current_instruction_profile(read(model.with_suffix('.task.json'))); identity=closure['identity']
            if identity not in resources:resources[identity]=copy_pack(model,p['asset_id'],identity,closure['files'])
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
                {'source_ref':ref,'source_episode':episode['episode_uid']},'draft')
            cases.append(case);write(bench/'cases'/f'{case.case_id}.json',case.record())
    rambo=Path(controller_root)
    controller=copy_pack(rambo/'model_2000.pt','rambo-go2-controller','iteration-2000',
                         {n:sha(rambo/n) for n in ('model_2000.pt','agent.yaml','env.yaml')},'controller')
    write(bench/'resource_registry_snapshot.json',{'schema':'qlm-evaluation-resources-v1','resources':resources,'controller':controller})
    write(bench/'protocol_snapshot.json',{'spec':protocol(cases).record()})
    write(bench/'manifest.json',{'schema':'qlm-benchmark-manifest-v1','benchmark_release':RELEASE,
        'validation_status':'draft','case_ids':[c.case_id for c in cases]})
    return bench


def resource(stage, row):
    """Absolute entrypoint of a registry row (scene pack or controller) under the resource root."""
    stage=Path(stage); m=read(under(stage,row['manifest']))
    if row['entrypoint']!=m['cache_subdir']+'/'+m['entrypoint']:raise ValueError('Resource entrypoint mismatch')
    path=under(stage,row['entrypoint'])
    if not path.is_file():raise FileNotFoundError(f'{path} is missing; run `python -m qlm_bench.benchmark fetch` first')
    return path


def reconstruct(runtime, case):
    import numpy as np
    from qlm_bench.contracts.rgb_profiles import dataset_profile, RGB_360
    from qlm_bench.data.lerobot.validation import PROFILE
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
        raise ValueError('Standard100 renders with hardware EGL (MUJOCO_GL=egl)')
    registry=read(Path(bench)/'resource_registry_snapshot.json')
    model=resource(stage,registry['resources'][case.scene['resource_identity']]);checkpoint=resource(stage,registry['controller'])
    kwargs=dict(model_path=model,checkpoint=checkpoint,seed=case.seed,device='cpu',trace_only=False,
                rgb_profile='dual-rgb-360p-v1')
    overlay={**case.scene.get('goal_overlay',{}),'horizon_s':case.scene['horizon_s'] if horizon is None else horizon}
    # Both runtime families accept the same explicit immutable episode overlay.
    kwargs['profile_override']=overlay
    r=create_runtime(case.task_id,'native',**kwargs)
    r.renderer.evaluation_observer=True
    if any(s in r.renderer.gl_identity['renderer'].lower() for s in ('llvmpipe','softpipe','swrast')):
        r.close();raise ValueError('Standard100 needs a hardware EGL renderer; software EGL was selected')
    return ControllerRuntimeAdapter(r,reconstruct=reconstruct)


def load_suite(bench):
    """The suite manifest plus its cases, in manifest order (structure checks only)."""
    bench=Path(bench);m=read(bench/'manifest.json')
    if m.get('schema')!='qlm-benchmark-manifest-v1' or m.get('benchmark_release')!=RELEASE:
        raise ValueError(f'{bench} is not a {RELEASE} suite')
    cases=[EvalCase.from_record(read(bench/'cases'/f'{c}.json')) for c in m['case_ids']]
    if len({c.case_id for c in cases})!=len(cases) or any(c.case_id!=i for c,i in zip(cases,m['case_ids'])):
        raise ValueError('Suite case files do not match the manifest')
    return m,cases


def verify_cases(stage, bench, case_ids=None):
    """Reset every case and check the reconstructed state and RGB; no physics step and no policy call."""
    import numpy as np
    from PIL import Image
    bench=Path(bench);manifest=read(bench/'manifest.json'); reports=[]
    for ident in manifest['case_ids'] if case_ids is None else case_ids:
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
            report={'reset_reconstruction_passed':True,'case_id':ident,
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
            reports.append(report)
            print(json.dumps({'case_id':ident,'reset_passed':True}),flush=True)
        finally:adapter.close()
    return {'passed':True,'cases':len(reports),'physics_steps':0,'policy_calls':0,'reports':reports}
