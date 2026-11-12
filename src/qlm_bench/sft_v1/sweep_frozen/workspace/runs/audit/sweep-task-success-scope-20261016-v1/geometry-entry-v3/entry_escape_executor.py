"""Optional A09 guidance plus bounded lower-waypoint wait under real geometry."""
from pathlib import Path
import importlib.util,numpy as np
R=Path('/home/jalen/workspace/WAM-Policy');P=R/'runs/audit/sweep-task-success-scope-20261016-v1/optional_order_executor.py'
spec=importlib.util.spec_from_file_location('optional_a09_parent',P);parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
class Sweep(parent.Sweep):
 def configure(self):
  self.lower_wait_start=None;self.lower_geometry_escape_s=None;super().configure()
 def command(self):
  values,diag=super().command();t=float(self.runtime.physics.ticks[0])*.002
  if self.entry_stage=='lower':
   if self.lower_wait_start is None:self.lower_wait_start=t
   if t-self.lower_wait_start>=6. and self.lower_geometry_escape_s is None:
    m=self.runtime.physics.model;d=self.runtime.physics.data[0];gid=m.geom('sw_block').id;f=m.geom('FL').id;p=d.geom_xpos[gid];foot=d.geom_xpos[f];rotation=d.geom_xmat[gid].reshape(3,3);half=m.geom_size[gid];radius=float(m.geom_size[f,0]);support=sum(abs(self.direction@rotation[:2,k])*half[k] for k in [0,1]);gap=float((foot[:2]-p[:2])@(-self.direction))-support-radius
    if foot[2]<=.09 and abs(float(foot[0]-p[0]))<=.025 and gap>=.005:
     self.lower_geometry_escape_s=t;self.entry_stage='sweep';self.entry_completion=t;self.last_target=self.entry_target.copy();self.enter('acquire_first_side_contact',t)
  else:self.lower_wait_start=None
  diag.update(lower_geometry_escape_s=self.lower_geometry_escape_s,lower_wait_start_s=self.lower_wait_start,lower_wait_limit_s=6.,optional_next_route=self.route,entry_geometry_diagnostic_only_after_safe_escape=True)
  return values,diag
