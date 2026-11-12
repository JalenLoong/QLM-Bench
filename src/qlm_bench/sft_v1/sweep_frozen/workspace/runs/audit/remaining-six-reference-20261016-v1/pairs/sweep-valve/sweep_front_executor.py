"""User-corrected front workspace; base stays behind the block/zone corridor."""
import numpy as np
from shared_executor import SmoothReference
from qlm_bench.backends.mujoco.press_reference_smooth import blend

class SweepExecutor(SmoothReference):
 def configure(self):
  m=self.runtime.physics.model;d=self.runtime.physics.data[0];gid=m.geom('sw_block').id
  self.block=self.runtime.task.geometric_center(0).copy();half=m.geom_size[gid];rotation=d.geom_xmat[gid].reshape(3,3)
  goal=np.array([np.mean(self.runtime.profile['goal_x']),np.mean(self.runtime.profile['goal_y'])]);self.direction=goal-self.block[:2];self.direction/=np.linalg.norm(self.direction)
  radius=float(m.geom('FL').size[0]);support=sum(abs(np.dot(self.direction,rotation[:2,k]))*half[k] for k in (0,1))
  self.contact=self.block.copy();self.contact[:2]-=self.direction*(support+radius+.018)
  self.end=self.block.copy();self.end[:2]=goal-self.direction*(support+radius-.012)
  center=(self.block[:2]+goal)/2;self.base_goal=np.array([min(self.block[0],goal[0])-float(self.config.get('working_forward_m',.45)),center[1]])
  self.present_s=float(self.config.get('present_s',2.5));self.sweep_s=float(self.config.get('sweep_s',7.))
 def interaction(self,age,t,dt):
  if age<self.present_s:
   self.phase='present_front_workspace_outer_side';return self.interaction_world_start+(self.contact-self.interaction_world_start)*blend(age/self.present_s)
  u=blend((age-self.present_s)/self.sweep_s);self.phase='lateral_sweep_in_front_workspace' if u<1 else 'hold_front_sweep_endpoint'
  return self.contact+(self.end-self.contact)*u
