"""Retain actual side contact and corridor direction without large X overreach."""
from pathlib import Path
import importlib.util
import numpy as np
from qlm_bench.backends.mujoco.press_reference_smooth import limited_step
spec=importlib.util.spec_from_file_location('front_sweep_v2',Path(__file__).with_name('sweep_front_executor_v2.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class SweepExecutor(old.SweepExecutor):
 def interaction(self,age,t,dt):
  if age<self.present_s:return super().interaction(age,t,dt)
  m=self.runtime.physics.model;d=self.runtime.physics.data[0];gid=m.geom('sw_block').id;p=self.runtime.task.geometric_center(0);goal=np.array([np.mean(self.runtime.profile['goal_x']),np.mean(self.runtime.profile['goal_y'])]);rotation=d.geom_xmat[gid].reshape(3,3);half=m.geom_size[gid]
  support=sum(abs(np.dot(self.direction,rotation[:2,k]))*half[k] for k in (0,1));radius=float(m.geom('FL').size[0]);xy=p[:2]-self.direction*(support+radius-float(self.config.get('contact_overlap_m',.012)))
  xy[0]+=np.clip(.15*(p[0]-goal[0]),-.008,.008)
  desired=np.array([*xy,float(self.config.get('contact_height_m',.025))]);self.last_target=limited_step(self.last_target,desired,[.055,.055,.03],dt)
  self.base_goal=np.array([p[0]-float(self.config.get('working_forward_m',.43)),self.fixed_base_y]);self.phase='front_fixed_direction_contact_follow'
  return self.last_target
