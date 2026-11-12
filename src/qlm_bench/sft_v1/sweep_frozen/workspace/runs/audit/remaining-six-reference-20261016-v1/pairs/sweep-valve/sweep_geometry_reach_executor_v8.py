"""Keep front workspace, using actual 3-D non-FL clearance instead of rear cap.

Only original native9 base goals change. Original A05 side-contact math, original
RAMBO/IK/history, dimensions, dynamics, task success and cameras are unchanged.
"""
from pathlib import Path
import importlib.util,json
import numpy as np,mujoco
spec=importlib.util.spec_from_file_location('retained_sweep_v7',Path(__file__).with_name('sweep_reach_follow_executor_v7.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

def extent(model,data,g):
 R=data.geom_xmat[g].reshape(3,3);size=model.geom_size[g];kind=int(model.geom_type[g])
 if kind==int(mujoco.mjtGeom.mjGEOM_SPHERE):return np.full(3,size[0])
 if kind==int(mujoco.mjtGeom.mjGEOM_CAPSULE):return size[0]+np.abs(R[:,2])*size[1]
 if kind==int(mujoco.mjtGeom.mjGEOM_CYLINDER):return np.sqrt(np.maximum(0,1-R[:,2]**2))*size[0]+np.abs(R[:,2])*size[1]
 if kind==int(mujoco.mjtGeom.mjGEOM_BOX):return np.abs(R)@size
 if kind==int(mujoco.mjtGeom.mjGEOM_ELLIPSOID):return np.sqrt((R*R)@(size*size))
 return np.full(3,float(model.geom_rbound[g]))

class SweepExecutor(old.SweepExecutor):
 def configure(self):
  super().configure();m=self.runtime.physics.model;d=self.runtime.physics.data[0];root=m.body('base').id;robot={root}
  for i in range(m.nbody):
   if int(m.body_parentid[i]) in robot:robot.add(i)
  self.nonfl_geoms=[g for g in range(m.ngeom) if int(m.geom_bodyid[g]) in robot and not (m.body(int(m.geom_bodyid[g])).name or '').startswith('FL_') and (m.geom_contype[g] or m.geom_conaffinity[g])]
  gid=m.geom('sw_block').id;self.workspace_min_x=min(float(d.geom_xpos[gid,0]-extent(m,d,gid)[0]),float(self.runtime.profile['goal_x'][0]));self.clearance_second=-1;self.clearance_rows=[];self.update_reach_goal()
 def update_reach_goal(self):
  m=self.runtime.physics.model;d=self.runtime.physics.data[0];gid=m.geom('sw_block').id;center=d.geom_xpos[gid];half=extent(m,d,gid);low=center-half;high=center+half;base_x=float(self.core.robot.position[0,0].cpu());clearance=float(self.config.get('nonFL_geometry_clearance_m',.010));caps=[]
  for g in self.nonfl_geoms:
   bounds=extent(m,d,g);p=d.geom_xpos[g];glo=p-bounds;ghi=p+bounds
   if np.all(ghi[1:]+clearance>=low[1:]) and np.all(glo[1:]-clearance<=high[1:]):caps.append((base_x+float(low[0]-ghi[0])-clearance,m.geom(g).name))
  workspace_cap=self.workspace_min_x-float(self.config.get('workspace_body_origin_margin_m',.10));self.reach_clearance_binding=min([(workspace_cap,'workspace_front_bound')]+caps,key=lambda c:c[0]);self.base_x_cap=self.reach_clearance_binding[0];self.base_goal=np.array([min(float(center[0])-float(self.config.get('working_forward_m',.40)),self.base_x_cap),self.fixed_base_y])
 def interaction(self,age,t,dt):
  self.update_reach_goal();world=super().interaction(age,t,dt);self.update_reach_goal();return world
 def command(self):
  self.update_reach_goal();values,diag=super().command();m=self.runtime.physics.model;d=self.runtime.physics.data[0];sec=int(self.runtime.physics.ticks[0])//500;diag.update(reach_bound_method='Actual non-FL collidable AABB YZ-overlap/X-clearance and whole frozen workspace body-origin front bound; not a new task predicate',workspace_min_x=self.workspace_min_x,geometry_clearance_bound=self.reach_clearance_binding)
  if sec!=self.clearance_second:
   self.clearance_second=sec;row={'s':sec,'actual_qpos':d.qpos.tolist(),'actual_base_xyz':self.core.robot.position[0].cpu().tolist(),'base_goal_xy':self.base_goal.tolist(),'geometry_binding':list(self.reach_clearance_binding),'workspace_min_x':self.workspace_min_x,'base_x_cap':self.base_x_cap,'desired':diag.get('unprojected_world_target'),'projected':diag['world_target']};self.clearance_rows.append(row);print(json.dumps({'actual_geometry_reach':row}),flush=True)
   if self.config.get('clearance_diagnostic_file'):
    path=Path(self.config['clearance_diagnostic_file']).resolve();assert path.is_relative_to(Path(__file__).resolve().parent);path.write_text(json.dumps({'role':'Optional lightweight1Hz actual-state/geometry diagnosis; not mandatory new high-frequency retention','rows':self.clearance_rows},indent=2)+'\n')
  return values,diag
