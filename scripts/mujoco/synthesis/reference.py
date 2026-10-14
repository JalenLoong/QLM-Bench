"""M1 known nominal expert: actual renderer-free reference for template development."""
import argparse,json
from pathlib import Path
import torch
from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
from qlm_bench.backends.mujoco.expert_adapter import ExpertAdapter
from qlm_bench.backends.mujoco.trace import collect_trace,write_json

p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--checkpoint',required=True)
p.add_argument('--output',required=True);a=p.parse_args();torch.set_num_threads(1)
r=MuJoCoRuntime(a.model,a.checkpoint,trace_only=True,seed=42)
class Nominal:
 def reset(self,rt,scene):self.expert=ExpertAdapter(rt.physics,rt.core,rt.task)
 def command(self):return self.expert.command()
s=r.physics.snapshot();scene={'candidate_id':'reference-a01','seed':42,'initial_state':{'schema':'qlm-mujoco-initial-state-v1','model_identity':s['model_identity'],'qpos':s['qpos'].tolist(),'qvel':s['qvel'].tolist()},'goal_x':r.profile['goal_x'],'goal_y':r.profile['goal_y'],'appearance_preset':'ap_00','difficulty':'clean'}
try:
 result=collect_trace(r,Nominal(),scene,a.output,batch_identity={'work_id':'QLM-DATA-011','reference_id':'reference-a01'},reference=True)
 write_json(Path(a.output).parent/'reference-result.json',result);print(result,flush=True)
finally:r.close()
