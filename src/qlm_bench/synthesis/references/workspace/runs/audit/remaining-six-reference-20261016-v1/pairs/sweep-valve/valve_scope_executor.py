"""Scope wrapper: retain successful v6 behavior and expose actual pose binding."""
from pathlib import Path
import importlib.util
import numpy as np
spec=importlib.util.spec_from_file_location('successful_valve_v6',Path(__file__).with_name('valve_near_axis_executor_v6.py'));original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)

class ValveExecutor(original.ValveExecutor):
 def configure(self):
  super().configure()
  assert np.allclose(self.basis.T@self.basis,np.eye(3),atol=1e-8)
  self.scope_pose={'actual_pivot_xyz':self.pivot.tolist(),'actual_mount_rotation_matrix':self.basis.tolist(),'actual_initial_hinge_rad':self.angle0,'goal_hinge_rad':self.theta_goal,'method':'Same successful v6 points transform by actual mount matrix; motion begins at actual hinge angle. No qpos or dynamics writes.'}
 def command(self):
  values,diagnostic=super().command();diagnostic['retarget_geometry']=self.scope_pose;return values,diagnostic
