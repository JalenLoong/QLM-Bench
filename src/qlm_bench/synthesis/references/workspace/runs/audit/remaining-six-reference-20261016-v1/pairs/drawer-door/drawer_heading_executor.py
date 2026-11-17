"""Fixture-frame a05 path plus bounded high-level absolute heading hold.

Only native9 Omega is added. Retained controller/IK/history and approved physics
are unchanged. Actual quaternion and projection are lightweight diagnostics.
"""
from pathlib import Path
import importlib.util,json,math
import numpy as np

spec=importlib.util.spec_from_file_location('preserved_fixture_v2',Path(__file__).parent/'drawer_fixture_executor.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class DrawerHeadingExecutor(old.DrawerFixtureExecutor):
 def yaw(self):
  w,x,y,z=self.runtime.physics.data[0].qpos[3:7]
  return math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
 def configure(self):
  super().configure();self.config['recipe_id']='drawer-a05-fixture-frame-absolute-heading-v7'
  self.heading_target=self.yaw();self.heading_omega=0.;self.heading_time=None;self.pose_diag_tick=-1
 def command(self):
  values,diag=super().command();d=self.runtime.physics.data[0];t=float(d.time)
  dt=.02 if self.heading_time is None else t-self.heading_time;self.heading_time=t
  error=math.atan2(math.sin(self.heading_target-self.yaw()),math.cos(self.heading_target-self.yaw()))
  desired=float(np.clip(1.5*error,-.25,.25));self.heading_omega+=float(np.clip(desired-self.heading_omega,-.5*dt,.5*dt));values[2]=self.heading_omega
  diag.update(heading_actual_yaw_rad=self.yaw(),heading_target_yaw_rad=self.heading_target,heading_native_omega_rad_s=self.heading_omega,heading_acceleration_limit_rad_s2=.5)
  if 'commanded_world_base_velocity' in diag:diag['commanded_world_base_velocity'][2]=self.heading_omega
  tick=int(self.runtime.physics.ticks[0])//250
  if tick!=self.pose_diag_tick:
   self.pose_diag_tick=tick
   print(json.dumps(dict(drawer_actual_pose_diagnostic=True,t=t,phase=self.phase,segment=self.segment,actual_qpos=d.qpos.tolist(),actual_qvel=d.qvel.tolist(),actual_yaw_rad=self.yaw(),heading_target_rad=self.heading_target,native9=values,world_target=diag.get('world_target'),unprojected_world_target=diag.get('unprojected_world_target'),actual_FL=self.actual_world_point().tolist(),base_goal=self.base_goal.tolist(),source='actual Native physics; no qpos writes')),flush=True)
  return values,diag
