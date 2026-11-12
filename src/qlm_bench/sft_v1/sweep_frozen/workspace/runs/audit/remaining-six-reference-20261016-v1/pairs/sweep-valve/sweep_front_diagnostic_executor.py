"""Same front heading recipe plus lightweight aggregate failure diagnostics."""
from pathlib import Path
import importlib.util,json
import numpy as np
spec=importlib.util.spec_from_file_location('front_heading_v4',Path(__file__).with_name('sweep_front_executor_v4.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class SweepExecutor(old.SweepExecutor):
 def configure(self):
  super().configure();self.summary={'role':'50Hz pre-command actual Native geometry aggregates, excludes terminal boundary; not mandatory new demonstration telemetry','samples':0,'operation':{},'robot_asset_contact_boundaries':{},'source_dynamics_unchanged':True};self.diag_second=-1
  m=self.runtime.physics.model;root=m.body('base').id;self.robot_bodies={root}
  for i in range(m.nbody):
   if int(m.body_parentid[i]) in self.robot_bodies:self.robot_bodies.add(i)
 def command(self):
  values,diagnostic=super().command();m=self.runtime.physics.model;d=self.runtime.physics.data[0];base=self.core.robot.position[0].cpu().numpy();yaw=diagnostic['actual_yaw_rad'];c,s=np.cos(yaw),np.sin(yaw);to_heading=np.array([[c,s],[-s,c]]);p=to_heading@(self.workspace_center-base[:2]);self.summary['samples']+=1
  active=diagnostic['phase'] not in ('settle','carry','approach_base','stabilize_base')
  if active:
   metrics={'workspace_center_forward_m':float(p[0]),'workspace_center_lateral_m':float(p[1]),'actual_base_x_m':float(base[0]),'actual_base_y_m':float(base[1]),'actual_yaw_deg':float(np.rad2deg(yaw)),'heading_error_deg':float(np.rad2deg(diagnostic['workspace_heading_error_rad']))}
   for name,value in metrics.items():
    r=self.summary['operation'].setdefault(name,[value,value]);r[0]=min(r[0],value);r[1]=max(r[1],value)
  hits=set();primary=m.body('primary').id
  for contact in d.contact[:d.ncon]:
   g1,g2=map(int,contact.geom);b1,b2=int(m.geom_bodyid[g1]),int(m.geom_bodyid[g2])
   if primary not in (b1,b2):continue
   other=b2 if b1==primary else b1
   if other in self.robot_bodies:hits.add(m.body(other).name)
  for name in hits:self.summary['robot_asset_contact_boundaries'][name]=self.summary['robot_asset_contact_boundaries'].get(name,0)+1
  t=float(self.runtime.physics.ticks[0])*.002;self.summary['covered_until_s']=t;sec=int(t)
  if self.config.get('diagnostic_file') and (sec!=self.diag_second or t>=self.runtime.profile['horizon_s']-.1):
   self.diag_second=sec;path=Path(self.config['diagnostic_file']).resolve();assert path.is_relative_to(Path(__file__).resolve().parent);path.write_text(json.dumps(self.summary,indent=2)+'\n')
  return values,diagnostic
