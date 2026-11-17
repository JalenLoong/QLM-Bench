"""Measured physical door following through high-level native9 only."""
from pathlib import Path
import importlib.util,numpy as np,torch
from qlm_bench.synthesis.press_reference import blend,limited_step
from qlm_bench.controllers.rambo.math import quat_apply_inverse
P=Path(str(__import__('qlm_bench.synthesis.references',fromlist=['REFERENCES']).REFERENCES)+'/runs/audit/fridge-body-advance-reference-20261016-v1/far-stop-v2/fridge_body_advance.py')
spec=importlib.util.spec_from_file_location('far_stationary_parent',P);parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
class Fridge(parent.Fridge):
 def configure(self):
  super().configure();self.follow_body=None;self.measured_follow_world=None
 def interaction(self,age,t,dt):
  if self.brace_s is None:
   result=super().interaction(age,t,dt)
   if self.brace_s is not None:self.follow_body=self.held_body.copy()
   return result
  d=self.runtime.physics.data[0];normal=d.xmat[self.primary].reshape(3,3)[:,0]
  if normal[0]<.15:raise RuntimeError('Door outside forward-follow geometry')
  lead=self.config['approach_normal_lead_m']+blend((t-self.brace_s)/self.config['contact_lead_ramp_s'])*(self.config['closing_normal_lead_m']-self.config['approach_normal_lead_m'])
  self.plane_target_x=float(self.pivot[0]+(self.rest_local_x+lead-normal[1]*(self.contact_line_y-self.pivot[1]))/normal[0])
  base=self.core.robot.position[0].cpu().numpy();point=self.world_body_point(self.follow_body)
  measured=np.array([self.plane_target_x,self.contact_line_y,point[2]])
  body=quat_apply_inverse(self.core.base_quat,torch.tensor((measured-base)[None],dtype=torch.float32,device=self.core.device))[0].cpu().numpy()
  desired=self.full_extension.copy();desired[0]=float(np.clip(body[0],self.braced_body[0],self.full_extension[0]))
  self.follow_body=limited_step(self.follow_body,desired,self.config['post_contact_body_reach_rate_m_s'],dt)
  self.held_body=self.follow_body.copy();self.measured_follow_world=measured
  # Base follows the same real door surface, leaving room for continued leg
  # extension instead of advancing immediately with the first-touch short pose.
  long_offset=self.world_body_point(self.full_extension)-base
  self.base_goal=np.array([max(self.far_stop[0],self.plane_target_x-long_offset[0]),self.contact_line_y-long_offset[1]])
  self.phase='body_advance_while_leg_held' # retained base speed limiter routing
  self.last_contact_force=self.contact();self.actual_plane_gap=float(-normal@(d.geom_xpos[self.foot]-self.pivot)+self.rest_local_x)
  return self.world_body_point(self.follow_body)
 def command(self):
  values,diag=super().command()
  if self.brace_s is not None:
   diag['phase']='follow_actual_door_and_advance_body'
   diag['strategy']='measured_door_following_FL_extension_with_coordinated_body'
  diag.update(post_contact_target_is_fixed=False,actual_door_follow_world=None if self.measured_follow_world is None else self.measured_follow_world.tolist(),follow_body_target_m=None if self.follow_body is None else self.follow_body.tolist(),body_uses_full_working_extension=True)
  return values,diag
