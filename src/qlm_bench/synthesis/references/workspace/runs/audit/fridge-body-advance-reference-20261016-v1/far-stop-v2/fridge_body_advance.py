"""Far stationary reach with the original ego camera; body-driven closing after touch."""
from pathlib import Path
import importlib.util,numpy as np
from qlm_bench.synthesis.press_reference import blend,limited_step
spec=importlib.util.spec_from_file_location('prior_body_brace',Path(__file__).resolve().parent.parent/'fridge_body_advance.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)

class Fridge(parent.Fridge):
 def configure(self):
  super().configure();self.full_extension=np.array(self.config['extended_body_xyz_m'],float)
  d=self.runtime.physics.data[0];normal=d.xmat[self.primary].reshape(3,3)[:,0]
  base=self.core.robot.position[0].cpu().numpy();offset=self.world_body_point(self.full_extension)-base
  face_x=self.pivot[0]+(self.rest_local_x+self.config['far_stop_normal_allowance_m']-normal[1]*(self.contact_line_y-self.pivot[1]))/normal[0]
  self.far_stop=np.array([face_x-offset[0],self.contact_line_y-offset[1]])
  self.base_goal=self.far_stop.copy();self.raise_start_s=None;self.brace_s=None;self.brace_evidence=None
  self.reach_body=None;self.braced_body=None;self.yaw_command=0.
  b=self.runtime.physics.model.body('base').id;rotation=d.xmat[b].reshape(3,3)
  self.heading=np.arctan2(rotation[1,0],rotation[0,0])
 def physical_touch(self):
  m=self.runtime.physics.model;d=self.runtime.physics.data[0]
  for c in d.contact[:d.ncon]:
   a,b=map(int,c.geom)
   if ((a==self.foot and int(m.geom_bodyid[b])==self.primary) or (b==self.foot and int(m.geom_bodyid[a])==self.primary)) and c.dist<=.001:return True
  return False
 def interaction(self,age,t,dt):
  d=self.runtime.physics.data[0];normal=d.xmat[self.primary].reshape(3,3)[:,0]
  if normal[0]<.15:raise RuntimeError('Actual door left the frozen frontal approach geometry')
  if self.raise_start_s is None:
   self.raise_start_s=t;self.reach_body=self.output_body.copy()
  if self.brace_s is None:
   self.phase='far_stop_raise_and_extend';self.base_goal=self.far_stop.copy()
   if self.physical_touch():
    self.brace_s=t;self.brace_evidence='actual FL foot versus primary MuJoCo contact pair';self.braced_body=self.reach_body.copy();self.push_start_base=self.core.robot.position[0,:2].cpu().numpy().astype(float)
   else:self.reach_body=limited_step(self.reach_body,self.full_extension,self.config['reach_body_rate_m_s'],dt)
   self.held_body=self.reach_body.copy()
  if self.brace_s is not None:
   self.phase='body_advance_while_leg_held';self.held_body=self.braced_body.copy()
   lead=self.config['approach_normal_lead_m']+blend((t-self.brace_s)/self.config['contact_lead_ramp_s'])*(self.config['closing_normal_lead_m']-self.config['approach_normal_lead_m'])
   point=self.world_body_point(self.held_body);base=self.core.robot.position[0].cpu().numpy();offset=point-base
   self.plane_target_x=float(self.pivot[0]+(self.rest_local_x+lead-normal[1]*(self.contact_line_y-self.pivot[1]))/normal[0])
   self.base_goal=np.array([self.plane_target_x-offset[0],self.contact_line_y-offset[1]])
  self.last_contact_force=self.contact();self.actual_plane_gap=float(-normal@(d.geom_xpos[self.foot]-self.pivot)+self.rest_local_x)
  return self.world_body_point(self.held_body)
 def command(self):
  values,diag=super().command();m=self.runtime.physics.model;d=self.runtime.physics.data[0];rotation=d.xmat[m.body('base').id].reshape(3,3)
  yaw=np.arctan2(rotation[1,0],rotation[0,0]);error=np.arctan2(np.sin(self.heading-yaw),np.cos(self.heading-yaw))
  if self.phase!='settle':
   wanted=np.clip(self.config['body_heading_gain']*error,-self.config['body_yaw_rate_cap_rad_s'],self.config['body_yaw_rate_cap_rad_s'])
   self.yaw_command=float(limited_step(self.yaw_command,wanted,self.config['body_yaw_acceleration_rad_s2'],.02));values[2]=self.yaw_command
   diag['commanded_world_base_velocity'][2]=self.yaw_command
  diag.update(far_stop_goal_xy=self.far_stop.tolist(),main_raise_extend_start_s=self.raise_start_s,actual_brace_s=self.brace_s,brace_evidence=self.brace_evidence,body_pose_at_brace_m=None if self.braced_body is None else self.braced_body.tolist(),desired_full_extension_m=self.full_extension.tolist(),heading_error_rad=float(error),original_ego_camera_unchanged=True)
  return values,diag
