"""Near-axis real bar contact with bounded high-level tangential preload."""
from pathlib import Path
import importlib.util
import numpy as np
from qlm_bench.backends.mujoco.press_reference_smooth import blend
spec=importlib.util.spec_from_file_location('near_axis_v5',Path(__file__).with_name('valve_near_axis_executor.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class ValveExecutor(old.ValveExecutor):
 def point(self,theta,tangent_gap):
  radial=np.array([0,np.cos(theta),np.sin(theta)]);tangent=np.array([0,-np.sin(theta),np.cos(theta)])
  return self.pivot+self.basis@(self.radius*radial-tangent_gap*tangent+np.array([-.002,0,0]))
 def interaction(self,age,t,dt):
  if age<self.present_s:return super().interaction(age,t,dt)
  elapsed=age-self.present_s;actual=float(self.runtime.task.progress(0));self.peak_angle=max(self.peak_angle,actual)
  planned=self.angle0+(self.theta_goal-self.angle0)*blend(elapsed/6.);theta=min(planned,max(actual,0)+.7)
  self.phase='near_axis_tangent_contact_preload';gap=.045+(-.005-.045)*blend(elapsed/1.)
  return self.point(theta,gap)
