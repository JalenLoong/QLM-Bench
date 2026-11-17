"""Versioned Valve retarget: actual fixture frame for stance and native9 heading.

Original v6 real bar path/preload is retained. This only constructs high-level
base velocity/yaw and foot goals; no simulator/controller/history writes.
"""
from pathlib import Path
import importlib.util,json
import numpy as np
spec=importlib.util.spec_from_file_location('unchanged_valve_v6_scope',Path(__file__).with_name('valve_scope_executor.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class ValveExecutor(old.ValveExecutor):
 def configure(self):
  super().configure()
  self.base_goal=self.pivot[:2]-(self.basis@np.array([.35,.10,0.]))[:2]
  self.fixture_yaw=float(np.arctan2(self.basis[1,0],self.basis[0,0]));self.heading_rate=0.;self.heading_time=None;self.mount_diag_second=-1;self.mount_diag_rows=[];self.interaction_angle_bound=False
 def interaction(self,age,t,dt):
  if not self.interaction_angle_bound:
   self.angle0=float(self.runtime.task.progress(0));self.entry=self.point(self.angle0,.045);self.interaction_angle_bound=True
  return super().interaction(age,t,dt)
 def command(self):
  values,diag=super().command();m=self.runtime.physics.model;d=self.runtime.physics.data[0];t=float(self.runtime.physics.ticks[0])*.002;dt=.02 if self.heading_time is None else t-self.heading_time;self.heading_time=t;R=d.xmat[m.body('base').id].reshape(3,3);yaw=float(np.arctan2(R[1,0],R[0,0]));error=float(np.arctan2(np.sin(self.fixture_yaw-yaw),np.cos(self.fixture_yaw-yaw)));wanted=float(np.clip(float(self.config.get('heading_gain',1.4))*error,-.25,.25));self.heading_rate+=float(np.clip(wanted-self.heading_rate,-.5*dt,.5*dt));values[2]=self.heading_rate
  diag.update(fixture_heading_rad=self.fixture_yaw,actual_yaw_rad=yaw,fixture_heading_error_rad=error,commanded_native_yaw_rate_rad_s=self.heading_rate,retargeted_base_goal_xy=self.base_goal.tolist(),interaction_initial_angle_rad=self.angle0,high_level_only=True)
  if 'commanded_world_base_velocity' in diag:diag['commanded_world_base_velocity'][2]=self.heading_rate
  second=int(t)
  if second!=self.mount_diag_second:
   self.mount_diag_second=second;foot=m.geom('FL').id;contacts=[]
   for con in d.contact[:d.ncon]:
    gs=list(map(int,con.geom))
    if foot in gs:
     name=m.geom(gs[1] if gs[0]==foot else gs[0]).name
     if name and name.startswith('vl_'):contacts.append(name)
   target=np.asarray(diag.get('world_target',d.geom_xpos[foot]),float);row={'s':second,'phase':diag['phase'],'actual_angle_rad':float(self.runtime.task.progress(0)),'actual_yaw_rad':yaw,'desired_yaw_rad':self.fixture_yaw,'actual_base_xyz':self.core.robot.position[0].cpu().tolist(),'base_goal_xy':self.base_goal.tolist(),'actual_foot_xyz':d.geom_xpos[foot].tolist(),'projected_world_target':target.tolist(),'actual_foot_target_error_xyz':(target-d.geom_xpos[foot]).tolist(),'FL_contact_geoms':contacts};self.mount_diag_rows.append(row);print(json.dumps({'mount_retarget_actual':row}),flush=True)
   if self.config.get('mount_diagnostic_file'):
    path=Path(self.config['mount_diagnostic_file']).resolve();assert path.is_relative_to(Path(__file__).resolve().parent);path.write_text(json.dumps({'physics_or_controller_modified':False,'role':'Lightweight1Hz actual pose/target diagnostics, not mandatory new demonstration retention','rows':self.mount_diag_rows},indent=2)+'\n')
  return values,diag
