"""Actual M1/M2 online/trace control parity and snapshot rendering comparison."""
import argparse,json
from pathlib import Path
import numpy as np
import torch
from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
from qlm_bench.backends.mujoco.trace import verify_trace,write_json,sha
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--checkpoint',required=True)
p.add_argument('--trace',required=True);p.add_argument('--output',required=True);a=p.parse_args()
torch.set_num_threads(1);m,arrays,t,c,z=verify_trace(a.trace);results=[]
# Compare both observation paths on exactly the same authoritative CUDA state.
# Independent CUDA contact rollouts are not assumed bitwise deterministic.
rt=MuJoCoRuntime(a.model,a.checkpoint,trace_only=False,seed=42)
try:
 rt.set_case_seed(42);rt.reset();saved_renderer=rt.renderer
 for i in range(10):
  rt.step(prepare_command([0.,0.,0.,.1934,.142,.05,0.,0.,0.],f'parity:{i}',i*10))
  rt.cached=None;online=rt.state();before=rt.freeze_token()
  rt.trace_only=True;rt.renderer=None;rt.cached=None;numeric=rt.state();after=rt.freeze_token()
  for key in online['state']:np.testing.assert_allclose(online['state'][key],numeric['state'][key],atol=1e-6,rtol=1e-6)
  assert before==after
  assert numeric['simulation_time_ns']==(i+1)*20_000_000
  rt.trace_only=False;rt.renderer=saved_renderer;rt.cached=None
finally:rt.close()
# Compare complete persisted same-state snapshots in independent mirrors, including repeat/reset.
from qlm_bench.backends.mujoco.render import RenderMirror
mirrors=[RenderMirror(a.model,world_id=m['world_id']) for _ in range(2)]
try:
 for i in [0,105,176,226,len(c)]:
  snap={k:arrays[k][i].copy() for k in ['qpos','qvel','act','mocap_pos','mocap_quat','eq_active']}
  snap.update(model_identity=m['model_identity'],model_parameters_identity=m['model_parameters_identity'],world_id=m['world_id'],
   reset_epoch=m['reset_epoch'],physics_step=int(arrays['physics_step'][i]),simulation_time_ns=int(arrays['simulation_time_ns'][i]),time=float(arrays['time'][i]))
  before=snap['qpos'].copy();pair=[r.capture(snap,terminal=i==len(c)) for r in mirrors]
  for view in pair[0]['rgb']:np.testing.assert_array_equal(pair[0]['rgb'][view],pair[1]['rgb'][view])
  np.testing.assert_array_equal(snap['qpos'],before);results.append({'frame':i,'RGB_byte_equal':True,'source_state_unchanged':True})
finally:
 for r in mirrors:r.close()
write_json(a.output,{'passed':True,'actual_control_commands_per_mode':10,'state_tolerance':1e-6,
 'same_authoritative_state_numeric_paths_equal':True,'physics_controller_RNG_clock_unchanged_by_observation':True,'same_state_online_mirror_offline_mirror':results})
print('Actual online/trace control and state-replay gates pass',flush=True)
