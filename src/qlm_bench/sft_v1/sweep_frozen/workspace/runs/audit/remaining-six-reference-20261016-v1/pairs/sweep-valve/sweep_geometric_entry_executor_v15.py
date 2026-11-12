"""Above-box geometric alignment, followed by actual slow side-entry gate.

Actual low diagonal entry in018 hit the negative-X corner before alignment.
Raise the whole foot above the real block, align from outside, lower outside,
then start original side-contact mathematics. No core/asset/physics changes.
"""
from pathlib import Path
import importlib.util,json
import mujoco,numpy as np
from qlm_bench.backends.mujoco.press_reference_smooth import limited_step
spec=importlib.util.spec_from_file_location('retained_midface_v10',Path(__file__).with_name('sweep_midface_executor_v10.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class SweepExecutor(old.SweepExecutor):
 def configure(self):
  super().configure();self.entry_stage='raise';self.entry_target=None;self.entry_clear_ticks=0;self.entry_alignment_ticks=0;self.entry_last_second=-1;self.entry_start=None;self.entry_completion=None;self.entry_x_bias=0.;self.entry_lower_ticks=0;self.entry_lower_max_ticks=0
 def interaction(self,age,t,dt):
  if self.entry_stage=='sweep':
   self.update_reach_goal();m=self.runtime.physics.model;d=self.runtime.physics.data[0];gid=m.geom('sw_block').id;p=self.runtime.task.geometric_center(0);R=d.geom_xmat[gid].reshape(3,3);half=m.geom_size[gid];radius=float(m.geom_size[m.geom('FL').id,0]);goal=np.array([np.mean(self.runtime.profile['goal_x']),np.mean(self.runtime.profile['goal_y'])]);support=sum(abs(self.direction@R[:2,k])*half[k] for k in [0,1]);xy=p[:2]-self.direction*(support+radius-float(self.config.get('contact_overlap_m',.012)));xy[0]+=float(np.clip(.15*(p[0]-goal[0]),-.008,.008))+self.entry_x_bias;desired=np.array([*xy,float(self.config.get('contact_height_m',.045))]);self.last_target=limited_step(self.last_target,desired,[.055,.055,.03],dt);self.phase='front_original_side_sweep_with_frozen_entry_tracking_bias';return self.last_target
  self.update_reach_goal();m=self.runtime.physics.model;d=self.runtime.physics.data[0];gid=m.geom('sw_block').id;foot=m.geom('FL').id;p=d.geom_xpos[gid].copy();R=d.geom_xmat[gid].reshape(3,3);half=m.geom_size[gid];radius=float(m.geom_size[foot,0]);actual=d.geom_xpos[foot].copy();support=sum(abs(self.direction@R[:2,k])*half[k] for k in [0,1]);top=p[2]+float(np.abs(R[2])@half);outer=p[:2]-self.direction*(support+radius+.025);high=max(.125,top+radius+.020)
  jp=np.zeros((3,m.nv));jr=np.zeros_like(jp);mujoco.mj_jacGeom(m,d,jp,jr,foot);velocity=jp@d.qvel
  if self.entry_stage in ('align','lower'):
   delta=float(np.clip(.5*(p[0]-actual[0]),-.005,.005))*dt;self.entry_x_bias=float(np.clip(self.entry_x_bias+delta,-.020,.020))
  outer[0]+=self.entry_x_bias
  if self.entry_target is None:self.entry_target=self.interaction_world_start.copy();self.entry_start=self.entry_target.copy()
  clearance=float(actual[2]-radius-top);self.entry_clear_ticks=self.entry_clear_ticks+1 if clearance>=.008 else 0
  if self.entry_stage=='raise':
   target=np.array([*self.entry_start[:2],high]);self.phase='front_entry_raise_before_forward'
   if self.entry_clear_ticks>=5:self.entry_stage='align'
  elif self.entry_stage=='align':
   target=np.array([*outer,high]);self.phase='front_entry_align_above_and_outside_actual_block'
   normal_gap=float((actual[:2]-p[:2])@(-self.direction))-support-radius;aligned=abs(float(actual[0]-p[0]))<=.025 and normal_gap>=.010 and np.linalg.norm(actual[:2]-outer)<=.035 and clearance>=.004
   self.entry_alignment_ticks=self.entry_alignment_ticks+1 if aligned else 0
   if self.entry_alignment_ticks>=2:self.entry_stage='lower'
  else:
   target=np.array([*outer,float(self.config.get('contact_height_m',.045))]);self.phase='front_entry_lower_outside_aligned_face'
   # Lower outside the box: no hidden constraint or state writes. Start the
   # original lateral path only when real foot height/normal-side pose agree.
   gap=float((actual[:2]-p[:2])@(-self.direction))-support-radius
   self.entry_lower_ticks=self.entry_lower_ticks+1 if actual[2]<=.075 and abs(float(actual[0]-p[0]))<=.008 and abs(float(velocity[0]))<=.040 and gap>=.005 else 0
   self.entry_lower_max_ticks=max(self.entry_lower_max_ticks,self.entry_lower_ticks)
   if self.entry_lower_ticks>=2:
    self.entry_stage='sweep';self.entry_completion=t;self.last_target=self.entry_target.copy()
  self.entry_target=limited_step(self.entry_target,target,[.045,.045,.050],dt);self.last_target=self.entry_target.copy()
  second=int(d.time)
  if second!=self.entry_last_second:
   self.entry_last_second=second;print(json.dumps(dict(clearance_entry_diagnostic=True,t=t,entry_stage=self.entry_stage,actual_foot_world=actual.tolist(),actual_block_world=p.tolist(),whole_foot_clearance_above_block_m=clearance,target_world=self.entry_target.tolist(),clear_ticks=self.entry_clear_ticks,alignment_ticks=self.entry_alignment_ticks,actual_qpos=d.qpos.tolist(),actual_foot_velocity_world=velocity.tolist(),entry_x_bias_m=self.entry_x_bias,entry_lower_ticks=self.entry_lower_ticks,entry_lower_max_ticks=self.entry_lower_max_ticks,no_controller_or_physics_writes=True)),flush=True)
  return self.entry_target
 def command(self):
  values,diag=super().command();diag.update(entry_stage=self.entry_stage,entry_clear_ticks=self.entry_clear_ticks,entry_alignment_ticks=self.entry_alignment_ticks,entry_x_tracking_bias_m=self.entry_x_bias,entry_lower_ticks=self.entry_lower_ticks,entry_lower_max_ticks=self.entry_lower_max_ticks,entry_tracking_bias_max_m=.020,original_steering_max_m=.008,entry_completion_time=self.entry_completion,entry_scope='high-level actual-geometry gate; retained v8 original side sweep follows; task success unchanged');return values,diag
