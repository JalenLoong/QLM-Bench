"""High-level native9: fixed forward FL pose, physical door closed by base advance."""
import json,numpy as np,mujoco,torch
from shared_executor import SmoothReference
from qlm_bench.synthesis.press_reference import blend,limited_step
from qlm_bench.controllers.rambo.math import quat_mul,quat_inv,quat_apply_inverse

class Fridge(SmoothReference):
 def configure(self):
  m=self.runtime.physics.model;d=self.runtime.physics.data[0]
  self.primary=m.body('primary').id;self.panel=m.geom('close_fridge_door_door_panel').id;self.foot=m.geom('FL').id
  self.pivot=d.xpos[self.primary].copy();rotation=d.xmat[self.primary].reshape(3,3)
  self.held_body=np.array(self.config['carry_body_xyz_m'],float)
  self.rest_local_x=-float(m.geom_size[self.panel,0]+m.geom_size[self.foot,0])
  initial_surface=self.pivot+rotation@np.array([self.rest_local_x,-self.config['panel_radius_m'],self.config['contact_height_m']-self.pivot[2]])
  self.contact_line_y=float(initial_surface[1]);self.initial_base=self.core.robot.position[0,:2].cpu().numpy().astype(float)
  self.base_goal=np.array([self.initial_base[0],self.contact_line_y-self.held_body[1]])
  self.first_contact_s=None;self.push_start_base=None;self.last_log_second=-1
  self.last_contact_force=0.;self.actual_plane_gap=None;self.plane_target_x=None
 def contact(self):
  m=self.runtime.physics.model;d=self.runtime.physics.data[0];force=0.
  for i,c in enumerate(d.contact[:d.ncon]):
   a,b=map(int,c.geom)
   if (a==self.foot and int(m.geom_bodyid[b])==self.primary) or (b==self.foot and int(m.geom_bodyid[a])==self.primary):
    wrench=np.zeros(6);mujoco.mj_contactForce(m,d,i,wrench);force+=max(0.,float(wrench[0]))
  return force
 def interaction(self,age,t,dt):
  d=self.runtime.physics.data[0];rotation=d.xmat[self.primary].reshape(3,3);normal=rotation[:,0]
  if normal[0]<.15:raise RuntimeError('Physical panel is outside the predeclared forward approach geometry')
  self.last_contact_force=self.contact();actual_foot=d.geom_xpos[self.foot]
  self.actual_plane_gap=float(-normal@(actual_foot-self.pivot)+self.rest_local_x)
  if self.first_contact_s is None and self.last_contact_force>=self.config['contact_detection_N']:
   self.first_contact_s=t;self.push_start_base=self.core.robot.position[0,:2].cpu().numpy().astype(float)
  if self.first_contact_s is None:
   self.phase='body_brace_approach';lead=self.config['approach_normal_lead_m']
  else:
   self.phase='body_advance_while_leg_held';u=blend((t-self.first_contact_s)/self.config['contact_lead_ramp_s'])
   lead=self.config['approach_normal_lead_m']+u*(self.config['closing_normal_lead_m']-self.config['approach_normal_lead_m'])
  # The foot reference never sweeps a closing arc after contact. Its body-frame
  # pose remains fixed; this actual physical plane determines ONLY the base goal.
  self.plane_target_x=float(self.pivot[0]+(self.rest_local_x+lead-normal[1]*(self.contact_line_y-self.pivot[1]))/normal[0])
  body_point=self.world_body_point(self.held_body);base=self.core.robot.position[0].cpu().numpy()
  offset=body_point-base
  self.base_goal=np.array([self.plane_target_x-offset[0],self.contact_line_y-offset[1]])
  return body_point
 def command(self):
  t=float(self.runtime.physics.ticks[0])*.002;self.last_contact_force=self.contact()
  if self.first_contact_s is None and self.last_contact_force>=self.config['contact_detection_N']:
   self.first_contact_s=t;self.push_start_base=self.core.robot.position[0,:2].cpu().numpy().astype(float)
  previous=self.velocity.copy();values,diag=super().command()
  if self.phase in ['body_brace_approach','body_advance_while_leg_held']:
   cap=self.config['body_push_speed_cap_m_s'];wanted=np.clip(self.velocity,-cap,cap)
   self.velocity=limited_step(previous,wanted,self.config['base_acceleration_m_s2'],.02)
   projected=quat_mul(self.core.base_quat,quat_inv(self.core.base_quat_rp))
   native=quat_apply_inverse(projected,torch.tensor([[*self.velocity,0.]],dtype=torch.float32,device=self.core.device))[0].cpu().tolist()
   values[:2]=native[:2];diag['commanded_world_base_velocity']=[*self.velocity.tolist(),0.]
  diag.update(strategy='fixed_body_FL_pose_and_body_forward_push',held_FL_body_target_m=self.held_body.tolist(),first_actual_FL_door_contact_s=self.first_contact_s,actual_FL_door_normal_N=self.last_contact_force,actual_plane_gap_m=self.actual_plane_gap,physical_panel_base_target_foot_x=self.plane_target_x,foot_world_closing_arc_used=False,body_advance_after_contact_m=None if self.push_start_base is None else (self.core.robot.position[0,:2].cpu().numpy()-self.push_start_base).tolist())
  if int(t)!=self.last_log_second:
   self.last_log_second=int(t);print(json.dumps(dict(fridge_body_advance_actual=True,t=t,phase=self.phase,first_contact_s=self.first_contact_s,q_rad=float(self.runtime.task.progress(0)),actual_base=self.core.robot.position[0].cpu().tolist(),base_goal=self.base_goal.tolist(),foot_force_N=self.last_contact_force,plane_gap_m=self.actual_plane_gap,held_body_target=self.held_body.tolist())),flush=True)
  return values,diag
