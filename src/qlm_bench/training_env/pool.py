"""Portable train-only reset pool for the streaming training environment (Stage 1.2 / 2.2).

The pool holds the 800 train-split initial states of the ten QLM-Bench releases (80 per task), the scene
packs they need and the RAMBO controller. Validation and test episodes are excluded, so no held-out
configuration reaches training. Only initial states are stored: no demonstration actions or frames.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import shutil
import tempfile
import errno

SCHEMA = 'qlm-train-reset-pool-v1'
# The published train800 pool predates the release and carries this schema string; it is read unchanged.
ACCEPTED_SCHEMAS = (SCHEMA, 'qlm-opd-v4-train-pool-v1')
RUNTIME = {'backend':'native','controller_device':'cpu','render_backend':'osmesa','renderer':'llvmpipe',
           'rgb_profile':'dual-rgb-360p-v1'}
TASKS = ('push_box','press_button','lift_basket','kick_ball_to_goal','sweep_block_to_zone',
         'close_fridge_door','close_oven_door','turn_valve','pull_open_drawer','open_room_door')
HORIZONS = dict(zip(TASKS,(24,24,24,24,40,40,60,32,40,60)))


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def catalogue():
    return Path(__file__).parents[1]/'data/spec/catalog.json'


def under(root,name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe portable training path')
    result=(Path(root)/p).resolve()
    if not result.is_relative_to(Path(root).resolve()):raise ValueError('Resource escapes pool')
    return result


def copy_duplicate(source,target):
    """Dedup is an optimization, not a requirement of the destination filesystem."""
    try:Path(target).hardlink_to(source)
    except OSError as exc:
        if exc.errno not in (errno.EXDEV,errno.EPERM,errno.EOPNOTSUPP,errno.ENOSYS,errno.EMLINK):raise
        shutil.copyfile(source,target)


def prepare(snapshot,destination,controller_root,*,catalog=None,model_map=None):
    """Stage the scene packs and the 800 train initial states from a QLM-Bench HF dataset snapshot.

    Scene packs are located through each episode's source trace; pass ``model_map`` ({resource_identity:
    scene.xml}) when the recorded scene path does not exist on this machine (e.g. a downloaded ``assets/``)."""
    from qlm_bench.backends.mujoco.resources import resource_closure
    from qlm_bench.tasks.prompts import current_instruction_profile
    snapshot,destination=Path(snapshot),Path(destination)
    if destination.exists():raise FileExistsError(destination)
    catalog=Path(catalog) if catalog else catalogue()
    cat=read(catalog)
    if tuple(cat['tasks'])!=TASKS:raise ValueError('The catalogue must list the ten QLM-Bench tasks')
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.train-pool-',dir=destination.parent))
    resources={};files={};content={};cache={};records=[];excluded=set();releases=[]
    def copy_file(src,name):
        h=sha(src);target=under(stage,name);target.parent.mkdir(parents=True,exist_ok=True)
        # Deduplicate only new staging inodes; never hardlink mutable source inputs.
        if h in content:
            copy_duplicate(content[h],target)
        else:shutil.copyfile(src,target);content[h]=target
        files[name]=h
    try:
        for entry in cat['demonstrations']:
            ref=entry['ref'];path=under(snapshot,ref['manifest'])
            release=read(path);splits=release['split'];train=set(splits['train'])
            heldout=set(splits['validation'])|set(splits['test'])
            if len(train)!=80 or train & heldout:raise ValueError('Train80/heldout split mismatch')
            excluded.update(heldout)
            source_manifest='sources/'+entry['task']+'/manifest.json'
            copy_file(path,source_manifest)
            releases.append({'task':entry['task'],'ref':ref,'source_manifest':source_manifest,'train_uids':sorted(train),
                             'validation_uids':splits['validation'],'test_uids':splits['test']})
            episodes={e['episode_uid']:e for e in release['episodes']}
            for uid in sorted(train):
                e=episodes[uid];bundle_path=under(snapshot,e['snapshot_bundle'])
                trace_path=bundle_path.parent/'source-trace-manifest.json'
                bundle,trace=read(bundle_path),read(trace_path)
                resource_id=bundle['model_identity']
                model=Path((model_map or {}).get(resource_id,trace['scene']['model']))
                if not model.is_file():
                    raise ValueError('Original scene path is unavailable; supply --resource-map for '+resource_id)
                closure=resource_closure(model,require_portable=True,hash_cache=cache)
                if closure['identity']!=resource_id:raise ValueError('Scene pack differs from the episode scene: '+resource_id)
                if resource_id not in resources:
                    prefix='resources/'+resource_id
                    for name in closure['files']:copy_file(model.parent/name,prefix+'/'+name)
                    resources[resource_id]={'entrypoint':prefix+'/'+model.name,'files':closure['files']}
                profile=current_instruction_profile(read(model.with_suffix('.task.json')))
                if entry['instruction']!=profile['instruction']:raise ValueError('Training instruction mismatch')
                initial=trace['scene']['initial_state']
                if initial['model_identity']!=resource_id:raise ValueError('Reset state belongs to another scene')
                source_trace='sources/'+entry['task']+'/'+e['source_trace_manifest_sha256']+'.json'
                if source_trace not in files:copy_file(trace_path,source_trace)
                records.append({'episode_uid':uid,'task':entry['task'],'instruction':entry['instruction'],
                    'task_version':profile['asset_profile'],'difficulty':e['difficulty'],'resource_identity':resource_id,
                    'initial_state':initial,'seed':trace['scene']['seed'],'horizon_s':HORIZONS[entry['task']],
                    'goal_overlay':{k:trace['scene'][k] for k in ('goal_x','goal_y','canonical_goal_position') if k in trace['scene']},
                    'snapshot_bundle_sha256':e['snapshot_bundle_sha256'],
                    'source_trace_manifest_sha256':e['source_trace_manifest_sha256'],'source_trace':source_trace})
        controller_root=Path(controller_root)
        for name in ('model_2000.pt','agent.yaml','env.yaml'):copy_file(controller_root/name,'controller/'+name)
        manifest={'schema':SCHEMA,'diagnostic_only':False,'tasks':list(TASKS),
            'episodes':records,'releases':releases,'heldout_uids':sorted(excluded),'resources':resources,
            'controller':'controller/model_2000.pt','files':files,'runtime':dict(RUNTIME)}
        validate(manifest)
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
        stage.rename(destination)
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True);raise
    return {'path':str(destination/'manifest.json'),'sha256':sha(destination/'manifest.json'),
            'episodes':len(records),'tasks':dict(Counter(r['task'] for r in records))}


def validate(manifest,*,allow_diagnostic=False):
    """Shape checks: train/held-out disjointness and, for a full pool, 80 train resets for each of the ten tasks."""
    if manifest.get('schema') not in ACCEPTED_SCHEMAS:raise ValueError('Not a QLM-Bench train reset pool')
    diagnostic=manifest.get('diagnostic_only',False)
    if diagnostic and not allow_diagnostic:raise ValueError('Diagnostic reset pool needs --diagnostic')
    records=manifest['episodes'];uids=[r['episode_uid'] for r in records]
    if not records or len(set(uids))!=len(uids) or set(uids)&set(manifest['heldout_uids']):
        raise ValueError('Duplicate or held-out training initialization')
    if manifest['runtime']!=RUNTIME:raise ValueError('Train pools run on native CPU MuJoCo with OSMesa rendering')
    declared={uid for release in manifest['releases'] for uid in release['train_uids']}
    heldout={uid for release in manifest['releases'] for k in ('validation_uids','test_uids') for uid in release[k]}
    if set(uids)!=declared or declared&heldout or heldout!=set(manifest['heldout_uids']):
        raise ValueError('Training membership does not match the declared source splits')
    if not diagnostic and (tuple(manifest['tasks'])!=TASKS or Counter(r['task'] for r in records)!=Counter({t:80 for t in TASKS})):
        raise ValueError('A full (non-diagnostic) pool has all ten tasks with 80 train resets each')
    for r in records:
        if r['task'] not in manifest['tasks'] or r['resource_identity'] not in manifest['resources']:
            raise ValueError('Missing task/resource binding')
        if r['initial_state'].get('model_identity')!=r['resource_identity'] or r['horizon_s']!=HORIZONS[r['task']]:
            raise ValueError('Reset state/horizon does not match its scene/task')
    return manifest


def load(path,*,allow_diagnostic=False):
    path=Path(path);m=validate(read(path),allow_diagnostic=allow_diagnostic)
    for name in [m['controller'],*(r['entrypoint'] for r in m['resources'].values())]:
        if not under(path.parent,name).is_file():raise FileNotFoundError('Train pool file missing: '+name)
    return m
