"""Approved six-task fresh production: explicit prepare, physics, admission, run."""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from qlm_bench.backends.mujoco.remaining_tasks import WORKSPACE as W, TASKS, binding, BINDINGS
from qlm_bench.backends.mujoco.remaining_production import candidates, load_campaign, RemainingProductionQueue
from qlm_bench.backends.mujoco.trace import sha, write_json, collect_trace
from qlm_bench.backends.mujoco.resources import resource_closure
from qlm_bench.compatibility.dataset_v2.validation import digest

REPO=Path(__file__).resolve().parents[3]
AUDIT=W/'runs/audit/remaining-six-production-20261016-v1'
CHECKPOINT=W/'assets/qlm/resources/20261003-refactor-v1/rambo-go2-controller/iteration-2000/runtime/model_2000.pt'


def implementation(root):
    return {str(p.relative_to(root)):sha(p) for folder in ('src/qlm_bench','scripts/mujoco/synthesis')
            for p in sorted((root/folder).rglob('*')) if p.suffix in ('.py','.json')}


def prepare(task,root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if (root/'campaign.json').exists():
        load_campaign(root/'campaign.json',root/'frozen-source');return
    b=binding(task);assert sha(b['nominal_executor'])==b['nominal_executor_sha256']
    auth=json.loads((AUDIT/'user-authorization.json').read_text());assert auth['target_new']==600
    frozen=root/'frozen-source';frozen.mkdir(exist_ok=False)
    for folder in ('src/qlm_bench','scripts/mujoco/synthesis'):
        shutil.copytree(REPO/folder,frozen/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    recipe=copy.deepcopy(b.get('recipe_config'))
    if recipe is None:recipe=json.loads(Path(b['recipe']).read_text()) if 'recipe' in b else {}
    template=root/'template';template.mkdir()
    external={str(BINDINGS):sha(BINDINGS)}
    # Anchor lazy scene construction to the approved asset bytes, not only paths.
    primary=Path(b['primary_model'])
    for relative,expected in resource_closure(primary,require_portable=True)['files'].items():
        external[str(primary.parent/relative)]=expected
    # Preserve actual source dependencies including imported older Python modules;
    # no historical media/payload is required or reconstructed.
    for parent in ('remaining-six-reference-20261016-v1','four-reference-refinement-20261016-v1',
                   'fridge-body-advance-reference-20261016-v1','fridge-door-follow-20261016-v1',
                   'sweep-a09-scope-20261016-v1','sweep-task-success-scope-20261016-v1',
                   'door-lowered-reference-20261016-v1'):
        base=W/'runs/audit'/parent
        for p in base.rglob('*.py'):
            if any(x in p.relative_to(base).parts for x in ('source','frozen-source','__pycache__')):continue
            external[str(p)]=sha(p)
    for p in b['approval_receipts']:
        external[p]=sha(p)
    for p in b.get('scope_binding_files', []):
        external[p]=sha(p)
    ref=Path(b['reference']);snap=ref/'review50/snapshots.npz'
    for p in ([snap] if snap.exists() else [ref/'trace/manifest.json']):external[str(p)]=sha(p)
    if 'recipe' in b:external[b['recipe']]=sha(b['recipe'])
    if 'success_adapter' in b:external[b['success_adapter']]=sha(b['success_adapter'])
    reference=dict(binding=b,recipe=recipe,external_files=external,
        actual_executor=b.get('scope_executor',b['nominal_executor']),
        nominal_motion_source=b['nominal_executor'],old_traces_counted_as_production=0)
    write_json(template/'template.json',reference)
    approval=dict(reference_quality_approved=True,retarget_scope_approved=True,
        evidence_sha256=digest({p:external[p] for p in b['approval_receipts']}),primary='A',
        approval_receipts=b['approval_receipts'],actual_scope_successes=b['scope_physical_successes'],
        actual_scope_cases=b['scope_cases'],historical_failures_preserved=True)
    source=dict(work_id='QLM-DATA-040',native_trace_profile='native-cpu-original-rambo-v1',
        implementation=implementation(frozen),external_files=external,
        template_id=task+'-approved-production-v1',template_sha256=sha(template/'template.json'),
        checkpoint_sha256=sha(CHECKPOINT),source_commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),
        source_snapshot=str(frozen),dirty_source_included=True)
    policy=dict(minimum_available_ram_bytes=2**30,maximum_swap_growth_bytes=8160437862,
        emergency_render_eviction_available_bytes=2**29,new_render_minimum_available_bytes=4*2**30)
    c=dict(schema='qlm-approved-six-fresh100-v1',task_id=task,work_id='QLM-DATA-040',
        authorization=dict(remaining_six_approved=True,target_accepted=100,user_receipt_sha256=sha(AUDIT/'user-authorization.json')),
        approval=approval,source=source,template_root=str(template),pilots=[],slots=candidates(task),
        python=str(W/'envs/qlm-mujoco-py312-v1/bin/python'),checkpoint=str(CHECKPOINT),
        entrypoint=str(frozen/'scripts/mujoco/synthesis/remaining100.py'),data_root=str(W/'data/qlm_bench/remaining-six-20261016-v1'/task),
        ffmpeg=str(W/'cache/tools/bin/ffmpeg'),ffprobe=str(W/'cache/tools/bin/ffprobe'),
        render_environment=dict(MUJOCO_GL='egl',PYOPENGL_PLATFORM='egl',MUJOCO_EGL_DEVICE_ID='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONPATH=str(frozen/'src')),
        render_script=str(frozen/'scripts/mujoco/synthesis/render_trace.py'),resource_policy=policy,
        maximum_render_backlog=6,maximum_per_slot=5,maximum_physics_attempts=300,maximum_consecutive_failures=10,
        recipe=recipe,horizon_s=b.get('horizon_s',40),consumer_validation='task_once_receipt_required',
        configuration_sampling='full-support Latin hypercube in each split; fixed seed42; predeclared bounded4% local retries; no OOD/interval partition',
        created_unix_s=time.time())
    c['profile_sha256']=digest(c);write_json(root/'campaign.json',c);load_campaign(root/'campaign.json',frozen)
    print('PREPARED',task,'100fresh slots;0physics',flush=True)


def physics(root,args):
    import torch
    import numpy as np
    import mujoco
    from qlm_bench.backends.mujoco.remaining_scenes import create_scene,initial_state
    from qlm_bench.backends.mujoco.remaining_runtime import ApprovedExpert
    from qlm_bench.backends.factory import create_runtime
    torch.set_num_threads(1)
    root=Path(root);c=load_campaign(root/'campaign.json',REPO);scene=json.loads(Path(args.candidate).read_text())
    slot=next(s for s in c['slots'] if any(x['candidate_id']==scene['candidate_id'] for x in s['candidates']))
    assert scene in slot['candidates']
    model=create_scene(c['task_id'],scene['configuration_parameters'],root/'models'/scene['candidate_id'],slot['appearance_preset'])
    scene.update(task_id=c['task_id'],model=str(model),initial_state=initial_state(c['task_id'],model),
                 appearance_preset=slot['appearance_preset'],difficulty=slot['difficulty'],split=slot['split'],
                 asset_id=json.loads(model.with_suffix('.task.json').read_text())['asset_id'])
    entry=dict(c['source'],production_campaign_sha256=c['profile_sha256'],approval_sha256=digest(c['approval']),
        actual_executor=binding(c['task_id']).get('scope_executor',binding(c['task_id'])['nominal_executor']),
        actual_executor_sha256=sha(binding(c['task_id']).get('scope_executor',binding(c['task_id'])['nominal_executor'])),
        recipe_config=c['recipe'],model_identity=resource_closure(model)['identity'],scene=scene,started_unix_s=time.time())
    write_json(root/'physical-attempts'/(scene['candidate_id']+'.json'),entry)
    runtime=create_runtime(c['task_id'],'native',model_path=model,checkpoint=c['checkpoint'],seed=scene['seed'],horizon_s=c['horizon_s'])
    try:
        expert=ApprovedExpert(c['task_id'],c['recipe']);original=expert.command;m=runtime.physics.model
        robot={m.body('base').id}
        for body in range(m.nbody):
            if int(m.body_parentid[body]) in robot:robot.add(body)
        assets=set(range(1,m.nbody))-robot
        def command():
            values,diag=original();d=runtime.physics.data[0];contacts=[]
            for i,contact in enumerate(d.contact[:d.ncon]):
                g1,g2=map(int,contact.geom);b1,b2=map(int,m.geom_bodyid[[g1,g2]])
                if b1 in robot and b2 in assets:rb,ag=b1,g2
                elif b2 in robot and b1 in assets:rb,ag=b2,g1
                else:continue
                force=np.zeros(6);mujoco.mj_contactForce(m,d,i,force)
                contacts.append(dict(robot_body=m.body(rb).name,asset_geom=m.geom(ag).name,normal_force_N=float(force[0])))
            diag['actual_robot_asset_contacts']=contacts
            return values,diag
        expert.command=command
        result=collect_trace(runtime,expert,scene,args.trace,batch_identity=entry,reference=False,quality_policy='evidence-review-v1')
        write_json(args.result,result);print(json.dumps(result),flush=True)
    finally:runtime.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','physics','admission','run'])
    p.add_argument('--root',required=True,type=Path);p.add_argument('--task',choices=TASKS)
    for key in ('candidate','trace','result'):p.add_argument('--'+key)
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.task,a.root)
    elif a.mode=='physics':physics(a.root,a)
    else:
        c=load_campaign(a.root/'campaign.json',REPO)
        queue=RemainingProductionQueue(a.root,a.root/'campaign.json',REPO)
        if a.mode=='run':
            receipt=json.loads((a.root/'production-admission.json').read_text())
            assert receipt['passed'] and receipt['campaign_sha256']==c['profile_sha256']
        queue.run_parallel(physics_workers=3,render_workers=3,admission=a.mode=='admission')


if __name__=='__main__':main()
