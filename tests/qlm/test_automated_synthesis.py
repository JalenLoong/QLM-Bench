"""Recovery, provenance and coordinate gates for the actual two-pass producer."""
import copy,json,shutil
from pathlib import Path
import numpy as np
import pytest
from qlm_bench.backends.mujoco.trace import verify_trace,write_json
from qlm_bench.backends.mujoco.template import rotation_z,quat_matrix
from qlm_bench.backends.mujoco.synthesis_queue import PilotQueue

ROOT=Path(__file__).resolve().parents[4]
TRACE=ROOT/'runs/audit/automated-push-synthesis-20261013-v1/reference-a02'

def test_position_and_velocity_frame_roundtrip():
 for yaw in [0.,.1,-.7,1.5]:
  R=rotation_z(yaw);origin=np.array([.6,-.2,0.]);p=np.array([.9,.3,.16]);v=np.array([.12,.03,0.])
  np.testing.assert_allclose(R@(R.T@(p-origin))+origin,p,atol=1e-14)
  np.testing.assert_allclose(R@(R.T@v),v,atol=1e-14)
  np.testing.assert_allclose(quat_matrix([0.,0.,np.sin(yaw/2),np.cos(yaw/2)]),R,atol=1e-14)

def actual_trace_or_skip():
 if not TRACE.exists():pytest.skip('Explicit actual reference fixture not supplied')
 return TRACE

def test_trace_full_frequency_inventory_and_detached_buffers(tmp_path):
 trace=actual_trace_or_skip();m,a,t,c,z=verify_trace(trace)
 assert m['renderer_created'] is False and m['renderer_calls']==0
 assert len(t['physics'])==len(c)*10+1 and len(t['controller'])==len(c)*2
 old=a['qpos'][0].copy();a['qpos'][-1,0]+=1
 np.testing.assert_array_equal(a['qpos'][0],old)
 path=tmp_path/'trace';shutil.copytree(trace,path)
 with (path/'commands.jsonl').open('a') as f:f.write('{}\n')
 with pytest.raises(ValueError,match='inventory'):verify_trace(path)

def test_restart_and_render_failure_never_repeat_successful_physics(tmp_path):
 trace=actual_trace_or_skip();original=verify_trace(trace)[0]['scene']
 scene=copy.deepcopy(original);scene['candidate_id']='test-candidate'
 profile={'profile_sha256':'test-profile','slots':[{'episode_uid':'push_box__ep0001','candidates':[scene]*5}]}
 calls={'physics':0,'render':0}
 def physics(scene,dest):
  calls['physics']+=1;shutil.copytree(trace,dest);m=json.loads((dest/'manifest.json').read_text());m['scene']=scene
  write_json(dest/'manifest.json',m);return {'passed':True}
 def render(trace,scene,slot,output):
  calls['render']+=1
  if calls['render']==1:raise RuntimeError('Injected temporary encoder fault')
  output.mkdir(parents=True);from qlm_bench.backends.mujoco.trace import sha
  write_json(output/'producer.json',{'passed':True,'physical_trace':{'manifest_sha256':sha(Path(trace)/'manifest.json')}})
  write_json(output/'result.json',{'passed':True});return {'passed':True}
 with PilotQueue(tmp_path/'queue',profile) as q:q.run(physics,render,stop_after_physics=True)
 assert calls=={'physics':1,'render':0}
 with PilotQueue(tmp_path/'queue',profile) as q:q.run(physics,render);assert q.accepted()==1
 with PilotQueue(tmp_path/'queue',profile) as q:q.run(physics,render);assert q.accepted()==1
 assert calls=={'physics':1,'render':2}

def test_single_writer_queue_lease(tmp_path):
 p={'profile_sha256':'fixed','slots':[]}
 with PilotQueue(tmp_path,p):
  with pytest.raises(BlockingIOError):
   with PilotQueue(tmp_path,p):pass

def test_irrecoverable_goal_overshoot_is_candidate_failure_not_system_error():
 from types import SimpleNamespace
 from qlm_bench.backends.mujoco.template import PushTemplateExecutor
 from qlm_bench.backends.mujoco.trace import CandidateRejected
 e=object.__new__(PushTemplateExecutor)
 e.runtime=SimpleNamespace(physics=SimpleNamespace(ticks=np.array([2500])),
   task=SimpleNamespace(geometry=lambda index:(None,None,np.array([[1.5,0,0],[1.7,.1,.2]]))))
 e.wait=0.;e.scene={'goal_x':[.95,1.35]};e.template={'stages':[{'start_s':0.,'phase':'straight_push'}]}
 with pytest.raises(CandidateRejected,match='Whole box passed'):e.command()
