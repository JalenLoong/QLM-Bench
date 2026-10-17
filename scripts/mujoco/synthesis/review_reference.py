"""One bounded actual reference/retarget attempt; never a formal pilot queue."""
import argparse
import copy
import json
from pathlib import Path
import subprocess

import mujoco
import numpy as np
import torch

from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
from qlm_bench.backends.mujoco.reference_retarget import ReviewPushExecutor, ContactAwarePushExecutor
from qlm_bench.backends.mujoco.quality import analyze_trace
from qlm_bench.backends.mujoco.trace import collect_trace, write_json, sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('model','checkpoint','template','output'):p.add_argument('--'+name,required=True)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--dx',type=float,default=0.)
    p.add_argument('--dy',type=float,default=0.)
    p.add_argument('--yaw',type=float,default=0.)
    p.add_argument('--working-y',type=float,default=.12)
    p.add_argument('--gain',type=float,default=1.)
    p.add_argument('--compact-diagnostics',action='store_true')
    p.add_argument('--recipe',choices=('approved-reference','cross-track-v2','cross-track-smooth-v3'),default='approved-reference')
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    if not np.isfinite([a.dx,a.dy,a.yaw]).all() or abs(a.dx)>.08 or abs(a.dy)>.06 or abs(a.yaw)>.12:
        raise ValueError('Outside this bounded reference-review matrix')
    torch.set_num_threads(1)
    kind=ReviewPushExecutor if a.recipe=='approved-reference' else ContactAwarePushExecutor
    options={'maximum_world_step':.008} if a.recipe=='cross-track-smooth-v3' else {}
    executor=kind(a.template,working_y=a.working_y,gain=a.gain,**options)
    runtime=MuJoCoRuntime(a.model,a.checkpoint,trace_only=True,seed=a.seed)
    try:
        scene=copy.deepcopy(executor.template['source_scene'])
        scene.update(candidate_id=out.name,seed=a.seed,difficulty='development',appearance_preset=runtime.profile.get('appearance_preset','ap_00'),
                     goal_x=runtime.profile['goal_x'],goal_y=runtime.profile['goal_y'])
        initial=scene['initial_state'];initial['model_identity']=runtime.physics.model_identity
        q=np.asarray(initial['qpos'],float)
        j=mujoco.mj_name2id(runtime.physics.model,mujoco.mjtObj.mjOBJ_JOINT,'object_free')
        if j<0:raise ValueError('Explicit Push freejoint required')
        adr=int(runtime.physics.model.jnt_qposadr[j]);q[adr:adr+2]+=[a.dx,a.dy]
        dq=np.array([np.cos(a.yaw/2),0.,0.,np.sin(a.yaw/2)])
        composed=np.empty(4);mujoco.mju_mulQuat(composed,dq,q[adr+3:adr+7]);q[adr+3:adr+7]=composed
        initial['qpos']=q.tolist()
        if a.compact_diagnostics:
            original_command=executor.command
            last_second=[-1]
            def diagnosed_command():
                values,detail=original_command()
                second=int(runtime.physics.ticks[0])//500
                if second!=last_second[0]:
                    last_second[0]=second
                    pos,rotation,corners=runtime.task.geometry(0)
                    row={'simulation_s':float(runtime.physics.ticks[0])*.002,'phase':detail['phase'],
                         'object_center':runtime.task.geometric_center(0).tolist(),
                         'footprint_min':corners[:,:2].min(0).tolist(),'footprint_max':corners[:,:2].max(0).tolist(),
                         'base_xy':runtime.core.robot.position[0,:2].cpu().tolist(),
                         'FL_body_y':float(runtime.core.ee_pos_b[0,0,1]),
                         'native9':values,'goal_x':scene['goal_x'],'goal_y':scene['goal_y']}
                    with (out/'diagnostic-summary.jsonl').open('a') as stream:
                        stream.write(json.dumps(row,allow_nan=False)+'\n')
                    print('DIAGNOSTIC '+json.dumps(row),flush=True)
                return values,detail
            executor.command=diagnosed_command
        write_json(out/'attempt.json',dict(work_id='QLM-DATA-015',kind='actual_reference_review_attempt',
            scene=scene,requested=vars(a),template_sha256=sha(Path(a.template)/'template.json'),
            formal_pilot=False,quality_gate='separate evidence review; no task predicate changes',
            telemetry_reason='Existing frozen Raw requires100/500Hz columns; this is scoped reference evidence'))
        source_commit=subprocess.check_output(['git','-C',str(Path(__file__).resolve().parents[3]),'rev-parse','HEAD'],text=True).strip()
        result=collect_trace(runtime,executor,scene,out/'trace',batch_identity={
            'work_id':'QLM-DATA-015','stage':'reference-review','template_id':executor.template['template_id'],
            'template_sha256':sha(Path(a.template)/'template.json'),'recipe':executor.coordination,
            'source_commit':source_commit,'executor_variant':a.recipe,
            'maximum_world_target_step_m':getattr(executor,'maximum_world_step',None)},
            reference=True,quality_policy='evidence-review-v1')
        write_json(out/'result.json',result)
        if result['passed']:
            quality,curves=analyze_trace(out/'trace')
            write_json(out/'quality.json',quality);np.savez_compressed(out/'quality-curves.npz',**curves)
            print(json.dumps(quality),flush=True)
        else:print(json.dumps(result),flush=True)
    finally:runtime.close()


if __name__=='__main__':main()
