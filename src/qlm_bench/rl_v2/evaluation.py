"""Versioned OSMesa evaluation profile; original EGL suite remains unchanged."""
import argparse
from dataclasses import replace
import json
import os
import re
import subprocess
from pathlib import Path

PROFILE='qlm-nativecpu-rambo-osmesa-rl-v2-v1'


def _io():
    from qlm_bench.backends.mujoco.rl_v2.storage import sha256,digest,write_json
    return sha256,digest,write_json


def source_identity():
    sha,digest,_=_io();root=Path(__file__).resolve().parents[1]
    return digest({str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.suffix in ('.py','.json')})


def reconstruct(runtime,case):
    import numpy as np
    from qlm_bench.compatibility.rgb_profiles import dataset_profile,RGB_360
    from qlm_bench.compatibility.dataset_v2.validation import PROFILE as DATA_PROFILE
    from qlm_bench.backends.mujoco.suite import CONTROLLER
    p=runtime.profile;identity=runtime.physics.model_identity
    if case.runtime_profile!=PROFILE or case.scene['render_backend']!='osmesa' or case.controller_profile!=CONTROLLER:
        raise ValueError('Explicit CPU evaluation identity required')
    if case.task_id!=p['task_id'] or case.instruction!=p['instruction'] or case.task_version!=p['asset_profile']:
        raise ValueError('Task/prompt/predicate profile mismatch')
    if dict(case.assets)!={p['asset_id']:identity} or case.scene['resource_identity']!=identity:
        raise ValueError('Evaluation resource identity mismatch')
    if case.goal!={'position':p['canonical_goal_position'],'task_profile':p['asset_profile']}:
        raise ValueError('Goal identity mismatch')
    if dict(case.cameras)!=dataset_profile(DATA_PROFILE,RGB_360)['policy_camera_geometry'] or case.initial_state['simulation_time_ns']!=0:
        raise ValueError('Evaluation must start at the declared normal initial state')
    runtime.set_case_seed(case.seed)
    initial={'schema':'qlm-mujoco-initial-state-v1','model_identity':identity,
             'qpos':case.initial_state['qpos'],'qvel':case.initial_state['qvel']}
    raw=runtime.reset(initial_state=initial);snapshot=runtime.physics.snapshot()
    for key in ('qpos','qvel'):np.testing.assert_allclose(snapshot[key],initial[key],rtol=0,atol=1e-6)
    if raw['physics_step'] or raw['simulation_time_ns'] or runtime.history or runtime.core.control_ticks.item():
        raise ValueError('Reset advanced clocks/history')


def runtime_for(stage,registry,case):
    from qlm_bench.backends.mujoco.suite import resource
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.backends.controller import ControllerRuntimeAdapter
    if os.environ.get('MUJOCO_GL')!='osmesa':raise ValueError('Select OSMesa before importing MuJoCo')
    model=resource(stage,registry['resources'][case.scene['resource_identity']]);controller=resource(stage,registry['controller'])
    runtime=create_runtime(case.task_id,'native',model_path=model,checkpoint=controller,device='cpu',seed=case.seed,
        rgb_profile='dual-rgb-360p-v1',profile_override={**case.scene.get('goal_overlay',{}),'horizon_s':case.scene['horizon_s']})
    if not any(x in runtime.renderer.gl_identity['renderer'].lower() for x in ('llvmpipe','softpipe','swrast')):
        runtime.close();raise ValueError('Software renderer required')
    runtime.renderer.observer_clip=None
    return ControllerRuntimeAdapter(runtime,reconstruct=reconstruct)


def execution_provenance(source_commit=None):
    root=Path(__file__).resolve().parents[3]
    try:
        top=subprocess.check_output(['git','-C',str(root),'rev-parse','--show-toplevel'],stderr=subprocess.DEVNULL,text=True).strip()
        if Path(top).resolve()!=root.resolve():raise subprocess.CalledProcessError(1,['git','rev-parse'])
        head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],stderr=subprocess.DEVNULL,text=True).strip()
        dirty=bool(subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True))
        if source_commit is not None and source_commit!=head:raise ValueError('Explicit source commit differs from checkout')
    except (OSError,subprocess.CalledProcessError):
        head=source_commit;dirty=None
    if not isinstance(head,str) or not re.fullmatch('[0-9a-f]{40}',head):
        raise ValueError('Source archive requires explicit reviewed --source-commit; parent EGL commit is not execution identity')
    return {'source_commit':head,'git_dirty':dirty,'execution_fingerprint':source_identity()}


def prepare(stage,parent_bench,output,source_commit=None):
    from qlm_bench.backends.mujoco.suite import validate_suite
    from qlm_bench.evaluation import EvalCase
    sha,digest,write=_io();parent=Path(parent_bench);manifest=validate_suite(parent)
    provenance=execution_provenance(source_commit)
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    registry=json.loads((parent/'resource_registry_snapshot.json').read_text());cases={}
    for uid in manifest['case_ids']:
        original=json.loads((parent/'cases'/f'{uid}.json').read_text())
        c=EvalCase.from_record(original)
        c=replace(c,runtime_profile=PROFILE,scene={**c.scene,'render_backend':'osmesa'},validation_status='draft')
        adapter=runtime_for(stage,registry,c)
        try:
            adapter.reset(c);rt=adapter.runtime;state=rt.state()
            if any(int(image.max())-int(image.min())<2 for image in state['rgb'].values()):raise ValueError('Invalid/constant scene RGB')
            evidence={'source':source_identity(),'case_parent':sha(parent/'cases'/f'{uid}.json'),
                      'physics_steps':0,'renderer':rt.renderer.gl_identity,'freeze':rt.freeze_token(),
                      'rgb':{k:__import__('hashlib').sha256(v.tobytes()).hexdigest() for k,v in state['rgb'].items()}}
            write(out/'evidence'/f'{uid}.json',evidence)
            c=replace(c,validation_status='verified',provenance={**c.provenance,'evidence_kind':'actual_runtime',
                 'reset_reconstruction_passed':True,'evidence_sha256':digest(evidence),'parent_EGL_case_sha256':evidence['case_parent']})
            write(out/'cases'/f'{uid}.json',c.record());cases[uid]=sha(out/'cases'/f'{uid}.json')
        finally:adapter.close()
    protocol=json.loads((parent/'protocol_snapshot.json').read_text())['spec']
    protocol.update(runtime_profile=PROFILE,protocol_id=protocol['protocol_id']+'-osmesa',suite_id=protocol['suite_id']+'-osmesa',
                    source_identity={'source_commit':provenance['source_commit'],'spec_sha256':digest(cases),
                                     'execution_source':source_identity(),'git_dirty':provenance['git_dirty']})
    write(out/'protocol.json',protocol);write(out/'resources.json',registry)
    write(out/'manifest.json',{'schema':'qlm-rl-v2-cpu-evaluation-v1','passed':True,'profile':PROFILE,
          'parent_manifest_sha256':sha(parent/'manifest.json'),'cases':cases,'source':source_identity(),'source_provenance':provenance,
          'files':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}})


def run(stage,profile,output,policy_port,policy_identity,previous=None):
    from qlm_bench.evaluation import EvalCase,EvaluationProtocol,TrialSpec,EvaluationRunner,write_result
    from qlm_bench.backends.mujoco.suite import LiveExecutor
    from qlm_bench.live import RPCClient
    sha,_,write=_io();root=Path(profile);m=json.loads((root/'manifest.json').read_text())
    if m.get('schema')!='qlm-rl-v2-cpu-evaluation-v1' or not m.get('passed') or m['source']!=source_identity():
        raise ValueError('Verified CPU evaluation profile with matching execution source required')
    for name,h in m['files'].items():
        p=(root/name).resolve()
        if not p.is_relative_to(root.resolve()) or sha(p)!=h:raise ValueError('CPU evaluation profile changed')
    values=json.loads((root/'protocol.json').read_text());values['expected_trials']=tuple(TrialSpec(**x) for x in values['expected_trials'])
    protocol=EvaluationProtocol(**values);cases={k:EvalCase.from_record(json.loads((root/'cases'/f'{k}.json').read_text())) for k in m['cases']}
    registry=json.loads((root/'resources.json').read_text());identity=json.loads(Path(policy_identity).read_text())
    runner=EvaluationRunner(protocol,cases,runtime_factory=lambda c:runtime_for(stage,registry,c),provider_factory=lambda _:None,
          source_commit=protocol.source_identity['source_commit'],policy_identity=identity,evidence_kind='actual_runtime',
          episode_executor=LiveExecutor(RPCClient(port=policy_port)))
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    rows=json.loads(Path(previous).read_text())['outcomes'] if previous else ()
    result=runner.run(submission_id=out.name,benchmark_release=protocol.suite_id,previous_outcomes=rows)
    result['cpu_profile']=PROFILE;result['execution_source']=source_identity()
    write_result(out/'result',result['run_manifest'],result['outcomes']);write(out/'result.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','run']);p.add_argument('--stage',required=True)
    p.add_argument('--profile',required=True);p.add_argument('--output',required=True);p.add_argument('--policy-port',type=int,default=8765);p.add_argument('--policy-identity');p.add_argument('--previous');p.add_argument('--source-commit')
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.stage,a.profile,a.output,a.source_commit)
    else:run(a.stage,a.profile,a.output,a.policy_port,a.policy_identity,a.previous)


if __name__=='__main__':main()
