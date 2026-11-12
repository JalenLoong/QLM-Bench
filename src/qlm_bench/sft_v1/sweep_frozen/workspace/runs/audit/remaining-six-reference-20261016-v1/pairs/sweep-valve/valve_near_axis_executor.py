"""Actual near-axis bar operation, fixed rear stance; no physics/controller writes."""
from pathlib import Path
import json
import numpy as np
from shared_executor import SmoothReference
from qlm_bench.backends.mujoco.press_reference_smooth import blend

class ValveExecutor(SmoothReference):
 def configure(self):
  m=self.runtime.physics.model;d=self.runtime.physics.data[0];self.pivot=d.xpos[m.body('primary').id].copy();self.basis=d.xmat[m.body('vl_stand').id].reshape(3,3).copy();self.angle0=float(self.runtime.task.progress(0));self.radius=.058;self.base_goal=self.pivot[:2]-np.array([.35,.10]);self.present_s=2.5;self.turn_s=8.;self.theta_goal=1.63;self.entry=self.point(self.angle0,.045);self.last_second=-1;self.contacts={};self.peak_angle=self.angle0
 def point(self,theta,tangent_gap):
  radial=np.array([0,np.cos(theta),np.sin(theta)]);tangent=np.array([0,-np.sin(theta),np.cos(theta)])
  return self.pivot+self.basis@(self.radius*radial-tangent_gap*tangent+np.array([-.024,0,0]))
 def interaction(self,age,t,dt):
  if age<self.present_s:
   self.phase='present_near_axis_bar';return self.interaction_world_start+(self.entry-self.interaction_world_start)*blend(age/self.present_s)
  elapsed=age-self.present_s;actual=float(self.runtime.task.progress(0));self.peak_angle=max(self.peak_angle,actual)
  planned=self.angle0+(self.theta_goal-self.angle0)*blend(elapsed/self.turn_s);theta=min(planned,max(actual,0)+.25)
  self.phase='near_axis_tangent_quarter_turn';gap=.045+(.020-.045)*blend(elapsed/1.)
  return self.point(theta,gap)
 def command(self):
  values,diagnostic=super().command();m=self.runtime.physics.model;d=self.runtime.physics.data[0];foot=m.geom('FL').id
  for c in d.contact[:d.ncon]:
   gs=[int(g) for g in c.geom]
   if foot in gs:
    name=m.geom(gs[1] if gs[0]==foot else gs[0]).name
    if name and name.startswith('vl_'):self.contacts[name]=self.contacts.get(name,0)+1
  sec=int(self.runtime.physics.ticks[0])//500
  if sec!=self.last_second:
   self.last_second=sec;report={'sim_s':sec,'actual_angle_rad':float(self.runtime.task.progress(0)),'peak_angle_rad':self.peak_angle,'actual_FL_geom_center':d.geom_xpos[foot].tolist(),'actual_robot_base':self.core.robot.position[0].cpu().tolist(),'foot_asset_contact_boundaries_by_geom':self.contacts,'no_sim_state_or_controller_writes':True};print(json.dumps(report),flush=True)
   if self.config.get('diagnostic_file'):
    target=Path(self.config['diagnostic_file']).resolve();assert target.is_relative_to(Path(__file__).resolve().parent);target.write_text(json.dumps(report,indent=2)+'\n')
  return values,diagnostic
