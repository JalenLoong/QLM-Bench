"""Portable train-only reset pool; no demonstration futures reach the policy."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import shutil
import tempfile
import errno

SCHEMA = 'qlm-opd-v4-train-pool-v1'
DATA_REVISION = '470e0a1f290ef65a25ca1933a91a51ccd6427fcf'
PAYLOAD_REVISION = 'b84488eca8a723767cef27fa455ec2ea8169f81c'
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
    return Path(__file__).parents[2]/'data/spec/mujoco1000_catalog.json'


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
        if exc.errno not in (errno.EXDEV,errno.EPERM,errno.EOPNOTSUPP,errno.ENOSYS):raise
        shutil.copyfile(source,target)


def prepare(snapshot,destination,controller_root,*,catalog=None,model_map=None):
    """Stage original resource bytes and 800 published training initializations."""
    from .resources import resource_closure
    from qlm_bench.tasks.prompts import current_instruction_profile
    snapshot,destination=Path(snapshot),Path(destination)
    if destination.exists():raise FileExistsError(destination)
    catalog=Path(catalog) if catalog else catalogue()
    if sha(catalog) != sha(catalogue()):
        raise ValueError('Approved source catalogue required')
    cat=read(catalog)
    if tuple(cat['tasks'])!=TASKS:raise ValueError('Approved ten-task catalogue required')
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
            if ref['revision']!=PAYLOAD_REVISION or sha(path)!=ref['manifest_sha256']:
                raise ValueError('Fixed training DataRef changed')
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
                if sha(bundle_path)!=e['snapshot_bundle_sha256'] or sha(trace_path)!=e['source_trace_manifest_sha256']:
                    raise ValueError('Training initialization provenance changed')
                bundle,trace=read(bundle_path),read(trace_path)
                resource_id=bundle['model_identity']
                model=Path((model_map or {}).get(resource_id,trace['scene']['model']))
                if not model.is_file():
                    raise ValueError('Original scene path is unavailable; supply --resource-map for '+resource_id)
                closure=resource_closure(model,require_portable=True,hash_cache=cache)
                if closure['identity']!=resource_id:raise ValueError('Training model identity mismatch')
                if resource_id not in resources:
                    prefix='resources/'+resource_id
                    for name in closure['files']:copy_file(model.parent/name,prefix+'/'+name)
                    resources[resource_id]={'entrypoint':prefix+'/'+model.name,'files':closure['files']}
                profile=current_instruction_profile(read(model.with_suffix('.task.json')))
                if entry['instruction']!=profile['instruction']:raise ValueError('Training instruction mismatch')
                initial=trace['scene']['initial_state']
                if initial['model_identity']!=resource_id:raise ValueError('Reset state/model mismatch')
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
        manifest={'schema':SCHEMA,'diagnostic_only':False,'dataset_revision':DATA_REVISION,
            'payload_revision':PAYLOAD_REVISION,'catalog_sha256':sha(catalog),'tasks':list(TASKS),
            'episodes':records,'releases':releases,'heldout_uids':sorted(excluded),'resources':resources,
            'controller':'controller/model_2000.pt','files':files,
            'runtime':{'backend':'native','controller_device':'cpu','render_backend':'osmesa','renderer':'llvmpipe',
                       'rgb_profile':'dual-rgb-360p-v1'}}
        validate(manifest)
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
        stage.rename(destination)
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True);raise
    return {'path':str(destination/'manifest.json'),'sha256':sha(destination/'manifest.json'),
            'episodes':len(records),'tasks':dict(Counter(r['task'] for r in records))}


def validate(manifest,*,allow_diagnostic=False):
    if manifest.get('schema')!=SCHEMA:raise ValueError('Typed OPD train pool required')
    diagnostic=manifest.get('diagnostic_only',False)
    if diagnostic and not allow_diagnostic:raise ValueError('Diagnostic reset pool cannot enter formal training')
    records=manifest['episodes'];uids=[r['episode_uid'] for r in records]
    if not records or len(set(uids))!=len(uids) or set(uids)&set(manifest['heldout_uids']):
        raise ValueError('Duplicate or held-out training initialization')
    if manifest['runtime']!={'backend':'native','controller_device':'cpu','render_backend':'osmesa',
                             'renderer':'llvmpipe','rgb_profile':'dual-rgb-360p-v1'}:
        raise ValueError('CPU-only training runtime identity required')
    declared={uid for release in manifest['releases'] for uid in release['train_uids']}
    heldout={uid for release in manifest['releases'] for k in ('validation_uids','test_uids') for uid in release[k]}
    if set(uids)!=declared or declared&heldout or heldout!=set(manifest['heldout_uids']):
        raise ValueError('Training membership does not match declared source splits')
    if not diagnostic:
        if (manifest['dataset_revision'],manifest['payload_revision'])!=(DATA_REVISION,PAYLOAD_REVISION):
            raise ValueError('Training data revision mismatch')
        if tuple(manifest['tasks'])!=TASKS or Counter(r['task'] for r in records)!=Counter({t:80 for t in TASKS}):
            raise ValueError('Formal pool requires all ten tasks and 800 train resets')
    for r in records:
        if r['task'] not in manifest['tasks'] or r['resource_identity'] not in manifest['resources']:
            raise ValueError('Missing task/resource binding')
        if r['initial_state'].get('model_identity')!=r['resource_identity'] or r['horizon_s']!=HORIZONS[r['task']]:
            raise ValueError('Training reset/horizon identity mismatch')
    return manifest


def load(path,*,allow_diagnostic=False):
    path=Path(path);m=validate(read(path),allow_diagnostic=allow_diagnostic)
    for resource in m['resources'].values():
        prefix=Path(resource['entrypoint']).parent
        if resource['entrypoint'] not in m['files']:
            raise ValueError('Unbound training resource entrypoint')
        for name,h in resource['files'].items():
            if m['files'].get(str(prefix/name))!=h:raise ValueError('Incomplete training resource inventory')
    controller=Path(m['controller'])
    if any(str(controller.parent/name) not in m['files'] for name in (controller.name,'agent.yaml','env.yaml')):
        raise ValueError('Incomplete controller inventory')
    checked={}
    for name,h in m['files'].items():
        target=under(path.parent,name);stat=target.stat()
        key=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns)
        if key not in checked:checked[key]=sha(target)
        if checked[key]!=h:raise ValueError('Training pool resource checksum mismatch: '+name)
    if not m.get('diagnostic_only',False):
        # The pool's own heldout/train declarations are not independent evidence.
        # Authenticate the original release manifests against the source-pinned
        # catalogue, then check every selected UID/task/difficulty against them.
        cat_path=catalogue()
        if m.get('catalog_sha256')!=sha(cat_path):raise ValueError('Training catalogue binding changed')
        cat=read(cat_path)
        releases={r['task']:r for r in m['releases']}
        if len(releases)!=len(m['releases']) or set(releases)!=set(TASKS):
            raise ValueError('Exactly one authenticated release per task required')
        for entry in cat['demonstrations']:
            selected=releases[entry['task']]
            name=selected.get('source_manifest')
            if (selected.get('ref')!=entry['ref'] or name not in m['files'] or
                    m['files'][name]!=entry['ref']['manifest_sha256']):
                raise ValueError('Authenticated source release required; rebuild legacy train pool')
            source=read(under(path.parent,name))
            for split,field in (('train','train_uids'),('validation','validation_uids'),('test','test_uids')):
                if set(source['split'][split])!=set(selected[field]):
                    raise ValueError('Pool membership differs from authenticated source split')
            originals={e['episode_uid']:e for e in source['episodes']}
            rows=[r for r in m['episodes'] if r['task']==entry['task']]
            if {r['episode_uid'] for r in rows}!=set(source['split']['train']):
                raise ValueError('Training UID assigned to the wrong task')
            for row in rows:
                original=originals[row['episode_uid']]
                if (row['instruction']!=entry['instruction'] or any(row.get(k)!=original[k] for k in
                        ('difficulty','snapshot_bundle_sha256','source_trace_manifest_sha256'))):
                    raise ValueError('Training initialization provenance/difficulty changed')
                trace_name=row.get('source_trace')
                if trace_name not in m['files'] or m['files'][trace_name]!=original['source_trace_manifest_sha256']:
                    raise ValueError('Authenticated source trace required; rebuild legacy train pool')
                scene=read(under(path.parent,trace_name))['scene']
                overlay={k:scene[k] for k in ('goal_x','goal_y','canonical_goal_position') if k in scene}
                if (row['initial_state']!=scene['initial_state'] or row['seed']!=scene['seed'] or
                        row['goal_overlay']!=overlay):
                    raise ValueError('Training reset differs from authenticated source trace')
    return m


class ResetSchedule:
    """Global deterministic task rotation at real episode boundaries, not updates."""
    def __init__(self,manifest,rank,world_size):
        self.tasks=manifest['tasks'];self.rank=rank;self.world_size=world_size;self.index=0
        self.by_task={t:sorted((r for r in manifest['episodes'] if r['task']==t),key=lambda r:r['episode_uid']) for t in self.tasks}
        import random
        for task,records in self.by_task.items():
            # Preserve each cycle's exact difficulty counts without a Clean-first prefix.
            random.Random(int(digest(['opd4-reset-v1',42,task]),16)).shuffle(records)

    def next(self):
        global_index=self.rank+self.index*self.world_size;self.index+=1
        task=self.tasks[global_index%len(self.tasks)]
        visit=global_index//len(self.tasks)
        return self.by_task[task][visit%len(self.by_task[task])]
