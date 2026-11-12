"""Maintain actual block-side contact in front, base Y stays on corridor centre."""
from pathlib import Path
import importlib.util,json
import numpy as np
from qlm_bench.backends.mujoco.press_reference_smooth import limited_step
spec=importlib.util.spec_from_file_location('front_sweep_v1',Path(__file__).with_name('sweep_front_executor.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class SweepExecutor(old.SweepExecutor):
 def configure(self):
  super().configure();self.fixed_base_y=float(self.base_goal[1]);self.last_target=self.contact.copy();self.last_target[2]=self.contact[2]=float(self.config.get('contact_height_m',.028));self.printed_second=-1
 def interaction(self,age,t,dt):
  if age<self.present_s:
   result=super().interaction(age,t,dt);self.last_target=np.asarray(result).copy();return result
  m=self.runtime.physics.model;d=self.runtime.physics.data[0];gid=m.geom('sw_block').id;p=self.runtime.task.geometric_center(0);goal=np.array([np.mean(self.runtime.profile['goal_x']),np.mean(self.runtime.profile['goal_y'])]);direction=goal-p[:2];distance=np.linalg.norm(direction);direction/=max(distance,.001)
  rotation=d.geom_xmat[gid].reshape(3,3);half=m.geom_size[gid];support=sum(abs(np.dot(direction,rotation[:2,k]))*half[k] for k in (0,1));radius=float(m.geom('FL').size[0])
  desired=np.array([*list(p[:2]-direction*(support+radius-float(self.config.get('contact_overlap_m',.012)))),float(self.config.get('contact_height_m',.028))])
  self.last_target=limited_step(self.last_target,desired,[.055,.055,.03],dt);self.base_goal=np.array([p[0]-float(self.config.get('working_forward_m',.45)),self.fixed_base_y]);self.phase='front_contact_follow_actual_block'
  return self.last_target
 def command(self):
  values,diagnostic=super().command();sec=int(self.runtime.physics.ticks[0])//500
  if sec!=self.printed_second:
   self.printed_second=sec;print(json.dumps({'contact_diagnostic_s':sec,'block_xyz':self.runtime.task.geometric_center(0).tolist(),'base_goal':self.base_goal.tolist()}),flush=True)
  return values,diagnostic
