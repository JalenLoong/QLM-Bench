"""Keep the whole frozen front workspace ahead: heading feedback and rear X cap."""
from pathlib import Path
import importlib.util
import numpy as np
spec=importlib.util.spec_from_file_location('successful_front_sweep_v3',Path(__file__).with_name('sweep_front_executor_v3.py'));original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)

class SweepExecutor(original.SweepExecutor):
 def configure(self):
  super().configure();goal=np.array([np.mean(self.runtime.profile['goal_x']),np.mean(self.runtime.profile['goal_y'])]);self.workspace_center=(self.block[:2]+goal)/2
  self.base_x_cap=min(float(self.block[0]),float(goal[0]))-float(self.config.get('rear_distance_m',.45));self.base_goal[0]=min(self.base_goal[0],self.base_x_cap);self.base_goal[1]=self.workspace_center[1];self.fixed_base_y=float(self.workspace_center[1]);self.yaw_rate=0.;self.yaw_time=None
 def interaction(self,age,t,dt):
  world=super().interaction(age,t,dt);self.base_goal[0]=min(float(self.base_goal[0]),self.base_x_cap);self.base_goal[1]=self.fixed_base_y;return world
 def command(self):
  values,diagnostic=super().command();t=float(self.runtime.physics.ticks[0])*.002;dt=.02 if self.yaw_time is None else t-self.yaw_time;self.yaw_time=t
  m=self.runtime.physics.model;d=self.runtime.physics.data[0];rotation=d.xmat[m.body('base').id].reshape(3,3);yaw=float(np.arctan2(rotation[1,0],rotation[0,0]));base=self.core.robot.position[0].cpu().numpy();delta=self.workspace_center-base[:2];heading=float(np.arctan2(delta[1],delta[0]));error=float(np.arctan2(np.sin(heading-yaw),np.cos(heading-yaw)))
  wanted=float(np.clip(float(self.config.get('heading_gain',1.4))*error,-float(self.config.get('yaw_rate_max_rad_s',.25)),float(self.config.get('yaw_rate_max_rad_s',.25))))
  step=float(self.config.get('yaw_acceleration_max_rad_s2',.5))*dt;self.yaw_rate+=float(np.clip(wanted-self.yaw_rate,-step,step));values[2]=self.yaw_rate
  diagnostic.update(workspace_center_xy=self.workspace_center.tolist(),base_x_cap=self.base_x_cap,actual_yaw_rad=yaw,desired_workspace_heading_rad=heading,workspace_heading_error_rad=error,commanded_native_yaw_rate_rad_s=self.yaw_rate,heading_feedback_scope='High-level native9 omega only; original controller/IK/history/physics/camera unchanged')
  return values,diagnostic
