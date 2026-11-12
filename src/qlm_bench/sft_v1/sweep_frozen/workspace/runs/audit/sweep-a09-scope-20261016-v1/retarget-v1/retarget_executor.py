"""Geometry-only reference retarget. Exact identity at approved nominal scene."""
from pathlib import Path
import importlib.util,copy,numpy as np
R=Path('/home/jalen/workspace/WAM-Policy');A=R/'runs/audit/four-reference-refinement-20261016-v1'
spec=importlib.util.spec_from_file_location('approved_frozen_a09',A/'sweep_staged_executor_v9.py');approved=importlib.util.module_from_spec(spec);spec.loader.exec_module(approved)
class Sweep(approved.Sweep):
 def __init__(self,config=None):
  super().__init__(config);self.nominal_config=copy.deepcopy(self.config)
 def configure(self):
  self.config=copy.deepcopy(self.nominal_config)
  self.retarget_ready=False
  actual=self.runtime.task.geometric_center(0)[:2];self.scope_translation=np.asarray(actual)-np.array([.75,.075]);self.scope_translation=np.where(abs(self.scope_translation)<1e-12,0.,self.scope_translation)
  p=self.runtime.profile;goal=np.array([np.mean(p['goal_x']),np.mean(p['goal_y'])]);delta=float(np.linalg.norm(goal-actual)-.225);self.scope_distance_delta=0. if abs(delta)<1e-12 else delta
  assert max(abs(self.scope_translation))<=.020000000001 and abs(self.scope_distance_delta)<=.020000000001
  self.config['coordinated_entry_base_x_m']+=float(self.scope_translation[0]);self.config['coordinated_push_base_x_m']+=float(self.scope_translation[0]);self.config['body_shift_distance_m']+=self.scope_distance_delta
  super().configure();self.fixed_base_y+=float(self.scope_translation[1]);self.coord_anchor[1]=self.fixed_base_y;self.retarget_ready=True;self.update_reach_goal()
 def update_reach_goal(self):
  super().update_reach_goal()
  if getattr(self,'retarget_ready',False) and self.shift_start is not None:
   dx=float(self.direction[0]*self.config['body_shift_distance_m']*self.shift_fraction)
   self.base_goal[0]=min(self.base_goal[0]+dx,self.base_x_cap);self.workspace_center[0]+=dx
 def command(self):
  values,diag=super().command();diag.update(geometry_retarget_translation_xy_m=self.scope_translation.tolist(),geometry_retarget_distance_delta_m=self.scope_distance_delta,geometry_retarget_identity_at_nominal=True);return values,diag
