"""Ten held-out task-specific normal initial states via the existing synchronous driver."""
import argparse
import json
import math
import os
from pathlib import Path
from qlm_bench.backends.mujoco.rl_v2.storage import sha256,write_json


def read_cases(path):
    record=json.loads(Path(path).read_text())
    if record.get('schema')!='qlm-rl-v2-validation-v1':raise ValueError('Typed validation split required')
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
    if record['horizon_seconds']!=60 or record['policy_seed']!=42:raise ValueError('Fixed sixty-second / seed42 validation protocol required')
    return record


def run(cases,controller,port,output):
    record=read_cases(cases);out=Path(output);out.mkdir(parents=True,exist_ok=False)
    if os.environ.get('MUJOCO_GL')!='osmesa' or os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('CPU-only OSMesa required')
    import torch
    torch.set_num_threads(1)
    if torch.cuda.is_available():raise ValueError('Validation worker exposes accelerator')
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.backends.mujoco.suite import SEMANTICS
    from qlm_bench.live import RPCClient,SynchronousDriver
    outcomes=[]
    for case in record['episodes']:
        scene=case['scene'];rt=create_runtime(record.get('task_id','push_box'),'native',model_path=case['model'],checkpoint=controller,trace_only=False,device='cpu',seed=scene['seed'],
            rgb_profile='dual-rgb-360p-v1',profile_override={**{k:scene[k] for k in ('goal_x','goal_y','canonical_goal_position') if k in scene},'horizon_s':record['horizon_seconds']})
        try:
            rt.renderer.observer_clip=None
            if not any(x in rt.renderer.gl_identity['renderer'].lower() for x in ('llvmpipe','softpipe','swrast')):raise ValueError('Software renderer required')
            rt.set_case_seed(scene['seed']);rt.reset(initial_state=scene['initial_state'])
            if rt.state()['physics_step'] or rt.state()['simulation_time_ns']:raise ValueError('Normal initial state required')
            driver=SynchronousDriver(rt,RPCClient(port=port),session_id='rl-validation-'+case['demo_uid'],
                instruction=case['instruction'],task_id=record.get('task_id','push_box'),task_version=rt.profile['asset_profile'],state_semantics=SEMANTICS,
                max_groups=math.ceil(record['horizon_seconds']/.32)+1)
            driver.reset_episode(case['demo_uid'],policy_seed=record['policy_seed'],initial_snapshot=rt.state())
            result=driver.run_episode()
            if not result['task_terminal']:raise RuntimeError('Validation ended without task terminal')
            row={'demo_uid':case['demo_uid'],'outcome':dict(rt.outcome),'simulation_time_ns':result['simulation_time_ns'],'renderer':rt.renderer.gl_identity}
            outcomes.append(row);write_json(out/(case['demo_uid']+'.json'),row)
        finally:rt.close()
    result={'passed':True,'schema':'qlm-rl-v2-validation-result-v1','task_id':record.get('task_id','push_box'),'split':'validation','GT_actor_visible':False,
            'cases_sha256':sha256(cases),'outcomes':outcomes,'success_rate':sum(x['outcome']['success'] for x in outcomes)/10}
    write_json(out/'result.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('cases','controller','output'):p.add_argument('--'+k,required=True)
    p.add_argument('--port',required=True,type=int);a=p.parse_args();run(a.cases,a.controller,a.port,a.output)

if __name__=='__main__':main()
