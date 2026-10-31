"""Ten held-out task-specific normal initial states via the existing synchronous driver; one rollout per (case, policy seed)."""
import argparse
import json
import math
import os
from pathlib import Path
import re
from qlm_bench.backends.mujoco.rl_v2.storage import sha256,write_json

SCHEMAS=('qlm-rl-v2-validation-v1','qlm-rl-v2-validation-v2')
ROLLOUT=re.compile(r'(0|[1-9][0-9]*):(0|[1-9][0-9]*)')


def read_cases(path):
    """v1 (policy_seed 42) or v2 (policy_seeds: distinct non-negative ints, first 42); both return a normalised 'policy_seeds' list."""
    record=json.loads(Path(path).read_text())
    if record.get('schema') not in SCHEMAS:raise ValueError('Typed validation split required')
    if sha256(record['split_path'])!=record['split_sha256'] or sha256(record['release_manifest'])!=record['release_manifest_sha256']:
        raise ValueError('Validation lineage changed')
    if sha256(record['prompt_path'])!=record['prompt_sha256']:raise ValueError('Validation prompt changed')
    task_id=record.get('task_id','push_box')
    if task_id not in ('push_box','sweep_block_to_zone'):raise ValueError('Unsupported RL validation task')
    instruction=json.loads(Path(record['prompt_path']).read_text())['prompts'][task_id]
    split=json.loads(Path(record['split_path']).read_text())['episodes']
    manifest=json.loads(Path(record['release_manifest']).read_text());rows={r['episode_uid']:r for r in manifest['episodes']}
    cases=record['episodes'];uids=[x['demo_uid'] for x in cases]
    if len(uids)!=10 or len(set(uids))!=10 or set(uids)!=set(split['validation']):raise ValueError('Exactly ten held-out validation episodes required')
    if set(uids)&set(split['train']+split['test']):raise ValueError('Split leakage')
    payload=Path(record['release_manifest']).parents[2]
    for case in cases:
        e=rows[case['demo_uid']]
        if e['task']!=task_id or e['split']!='validation' or case['split']!='validation':raise ValueError('Selected task validation only')
        trace=(payload/e['snapshot_bundle']).parent/'source-trace-manifest.json'
        if sha256(trace)!=e['source_trace_manifest_sha256']:raise ValueError('Reset scene provenance changed')
        source=json.loads(trace.read_text())
        if case['scene']!=source['scene'] or case['instruction']!=instruction:raise ValueError('Reset scene differs from held-out source')
        from .resources import verify_scene_resource
        verify_scene_resource(case['model'],source['model_identity'])
    if record['horizon_seconds']!=60:raise ValueError('Fixed sixty-second validation protocol required')
    if record['schema']==SCHEMAS[0]:
        if record['policy_seed']!=42:raise ValueError('Fixed seed42 validation protocol required')
        seeds=[42]
    else:
        seeds=record.get('policy_seeds')
        if type(seeds) is not list or not seeds or any(type(s) is not int or s<0 for s in seeds) or len(set(seeds))!=len(seeds) or seeds[0]!=42:
            raise ValueError('Distinct non-negative policy seeds starting with 42 required')
    record['policy_seeds']=list(seeds);return record


def _cpu_only():
    if os.environ.get('MUJOCO_GL')!='osmesa' or os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('CPU-only OSMesa required')
    import torch
    torch.set_num_threads(1)
    if torch.cuda.is_available():raise ValueError('Validation worker exposes accelerator')


def run_case(record,case,controller,port,seed,*,on_observation=None,observer=False):
    """One held-out case under one policy seed through the synchronous driver; the observer view is diagnostic only."""
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.backends.mujoco.suite import SEMANTICS
    from qlm_bench.live import RPCClient,SynchronousDriver
    scene=case['scene'];rt=create_runtime(record.get('task_id','push_box'),'native',model_path=case['model'],checkpoint=controller,trace_only=False,device='cpu',seed=scene['seed'],
        rgb_profile='dual-rgb-360p-v1',profile_override={**{k:scene[k] for k in ('goal_x','goal_y','canonical_goal_position') if k in scene},'horizon_s':record['horizon_seconds']})
    try:
        rt.observation_ticks=40  # The driver samples RGB at 40-tick boundaries; the observer frames below are also saved there.
        if observer:rt.renderer.evaluation_observer=True
        else:rt.renderer.observer_clip=None
        if not any(x in rt.renderer.gl_identity['renderer'].lower() for x in ('llvmpipe','softpipe','swrast')):raise ValueError('Software renderer required')
        rt.on_observation=on_observation
        rt.set_case_seed(scene['seed']);rt.reset(initial_state=scene['initial_state'])
        if rt.state()['physics_step'] or rt.state()['simulation_time_ns']:raise ValueError('Normal initial state required')
        driver=SynchronousDriver(rt,RPCClient(port=port),session_id=f"rl-validation-{case['demo_uid']}-s{seed}",  # Seeds of one case never share a session.
            instruction=case['instruction'],task_id=record.get('task_id','push_box'),task_version=rt.profile['asset_profile'],state_semantics=SEMANTICS,
            max_groups=math.ceil(record['horizon_seconds']/.32)+1)
        driver.reset_episode(case['demo_uid'],policy_seed=seed,initial_snapshot=rt.state())
        result=driver.run_episode()
        if not result['task_terminal']:raise RuntimeError('Validation ended without task terminal')
        return {'demo_uid':case['demo_uid'],'policy_seed':seed,'outcome':dict(rt.outcome),'simulation_time_ns':result['simulation_time_ns'],'renderer':rt.renderer.gl_identity}
    finally:rt.close()


def rollout_set(record,rollouts=None,case_indices=None):
    """Explicit (case index, seed) pairs, the --case-indices alias (listed cases under every seed) or everything; seed-major."""
    seeds=record['policy_seeds'];full=[(i,s) for s in seeds for i in range(10)]
    if rollouts is not None and case_indices is not None:raise ValueError('Rollouts and case indices are alternatives')
    if case_indices is not None:rollouts=[(i,s) for s in seeds for i in case_indices]
    pairs=full if rollouts is None else list(rollouts)
    if not pairs or any(not isinstance(x,(tuple,list)) or len(x)!=2 or type(x[0]) is not int or not 0<=x[0]<10 or type(x[1]) is not int or x[1] not in seeds for x in pairs):
        raise ValueError('Non-empty (case index in 0..9, policy seed of the record) rollouts required')
    pairs=[(i,s) for i,s in pairs]
    if len(set(pairs))!=len(pairs):raise ValueError('Duplicate validation rollout')
    return pairs,full


def run(cases,controller,port,output,rollouts=None,*,case_indices=None):
    """A rollout is a (case index, policy seed) pair; None runs every case under every seed, seed-major. Every rollout
    writes '<demo_uid>-seed<seed>.json' (the v1 '<demo_uid>.json' name is never written, even for one seed); the
    complete set writes result.json with seed-major outcomes, any other set (one subprocess per rank) writes subset.json."""
    record=read_cases(cases);pairs,full=rollout_set(record,rollouts,case_indices)
    out=Path(output);out.mkdir(parents=True,exist_ok=False);_cpu_only();rows={}
    for index,seed in pairs:
        case=record['episodes'][index];row=run_case(record,case,controller,port,seed)
        rows[index,seed]=row;write_json(out/f"{case['demo_uid']}-seed{seed}.json",row)
    task=record.get('task_id','push_box')
    if set(pairs)!=set(full):
        subset={'schema':'qlm-rl-v2-validation-subset-v2','task_id':task,'rollouts':[[i,s] for i,s in pairs],'outcomes':[rows[x] for x in pairs],'cases_sha256':sha256(cases)}
        write_json(out/'subset.json',subset);return subset
    rate=lambda keys:sum(bool(rows[k]['outcome']['success']) for k in keys)/len(keys)
    result={'passed':True,'schema':'qlm-rl-v2-validation-result-v2','task_id':task,'split':'validation','GT_actor_visible':False,
            'cases_sha256':sha256(cases),'policy_seeds':list(record['policy_seeds']),'outcomes':[rows[x] for x in full],'success_rate':rate(full),
            'per_seed_success_rate':{str(s):rate([(i,s) for i in range(10)]) for s in record['policy_seeds']}}
    write_json(out/'result.json',result);return result


def visualize(cases,case_index,controller,port,output):
    """One fixed held-out case under the first seed (42) with the observer camera saved at the model's 0.32 s/4 ticks."""
    from PIL import Image
    record=read_cases(cases);case=record['episodes'][case_index];seed=record['policy_seeds'][0]
    out=Path(output);(out/'observer').mkdir(parents=True,exist_ok=False);_cpu_only()
    def save(snapshot):
        tick=int(snapshot['physics_step']);image=snapshot.get('observer_rgb')
        if image is not None and tick%40==0:
            Image.fromarray(image).resize((640,360),Image.BILINEAR).save(out/'observer'/f'{tick:08d}.jpg',quality=90)
    row=run_case(record,case,controller,port,seed,on_observation=save,observer=True)
    row.update(case_index=case_index,task_id=record.get('task_id','push_box'),observer_view='evaluation_observer')
    write_json(out/'result.json',row);return row


def parse_rollouts(text):
    """Strict 'index:seed,index:seed' list (decimal, no signs/spaces/leading zeros); any other item fails closed."""
    pairs=[]
    for item in text.split(','):
        m=ROLLOUT.fullmatch(item)
        if m is None:raise ValueError(f'Malformed rollout {item!r}: expected comma-separated "<case index>:<policy seed>" items')
        pairs.append((int(m[1]),int(m[2])))
    return pairs


def parse_indices(text):
    items=text.split(',')
    if any(not re.fullmatch(r'0|[1-9][0-9]*',x) for x in items):raise ValueError(f'Malformed case indices {text!r}: expected comma-separated integers')
    return [int(x) for x in items]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('cases','controller','output'):p.add_argument('--'+k,required=True)
    p.add_argument('--port',required=True,type=int);p.add_argument('--visualize-case',type=int,help='One case index under the first seed (42) with observer frames')
    g=p.add_mutually_exclusive_group()
    g.add_argument('--rollouts',help='Comma-separated index:seed rollouts (case index 0..9, seed of the record); default every case under every seed')
    g.add_argument('--case-indices',help='Compatibility alias: comma-separated case indices, each run under every seed of the record')
    a=p.parse_args()
    try:rollouts=None if a.rollouts is None else parse_rollouts(a.rollouts);indices=None if a.case_indices is None else parse_indices(a.case_indices)
    except ValueError as exc:p.error(str(exc))
    if a.visualize_case is None:run(a.cases,a.controller,a.port,a.output,rollouts,case_indices=indices)
    elif rollouts is not None or indices is not None:p.error('--visualize-case runs one case under the first seed; no rollouts/case indices')
    else:visualize(a.cases,a.visualize_case,a.controller,a.port,a.output)

if __name__=='__main__':main()
