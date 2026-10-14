"""Bounded M4 fixed-recipe development cases; no official pilot quota."""
import argparse,copy,json,math
from pathlib import Path
import numpy as np
import torch
import mujoco
from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
from qlm_bench.backends.mujoco.template import PushTemplateExecutor
from qlm_bench.backends.mujoco.trace import collect_trace,write_json

p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--checkpoint',required=True)
p.add_argument('--template',required=True);p.add_argument('--output',required=True);a=p.parse_args()
out=Path(a.output);out.mkdir(parents=True,exist_ok=False);torch.set_num_threads(1)
rt=MuJoCoRuntime(a.model,a.checkpoint,trace_only=True)
executor=PushTemplateExecutor(a.template);original=executor.template['source_scene'];rows=[]
try:
 j=mujoco.mj_name2id(rt.physics.model,mujoco.mjtObj.mjOBJ_JOINT,'object_free');adr=int(rt.physics.model.jnt_qposadr[j])
 cases=[(0.,0.,0.,0.,0.,42),(.025,.012,.015,.015,.01,43),(-.025,-.012,-.015,-.015,-.01,44)]
 for i,(dx,dy,yaw,gx,gy,seed) in enumerate(cases):
  scene=copy.deepcopy(original);scene.update(candidate_id=f'development-{i:02}',seed=seed)
  state=scene['initial_state'];q=np.array(state['qpos']);q[adr:adr+2]+=[dx,dy];q[adr+3:adr+7]=[math.cos(yaw/2),0,0,math.sin(yaw/2)]
  state['qpos']=q.tolist();scene['goal_x']=[v+gx for v in original['goal_x']];scene['goal_y']=[v+gy for v in original['goal_y']]
  scene['difficulty']='clean' if i==0 else 'randomized'
  rt.profile.update(goal_x=scene['goal_x'],goal_y=scene['goal_y'],canonical_goal_position=[np.mean(scene['goal_x']),np.mean(scene['goal_y']),0.])
  try:r=collect_trace(rt,executor,scene,out/scene['candidate_id'],batch_identity={'work_id':'QLM-DATA-011','stage':'M4-development'})
  except Exception as error:r={'passed':False,'reason':str(error),'stage':'physics'}
  rows.append({'scene':scene,'result':r});write_json(out/'results.json',rows);print(scene['candidate_id'],r,flush=True)
finally:rt.close()
