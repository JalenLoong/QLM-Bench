"""Conservative factor isolation: successful A05 contact path, bounded X follow.

Only the artificial X cap changes. Case-centre Y and original heading feedback
remain. All physical/source/controller contracts and original A05 bytes remain.
"""
from pathlib import Path
import importlib.util,json
import numpy as np
spec=importlib.util.spec_from_file_location('successful_a05_contact',Path(__file__).with_name('sweep_front_diagnostic_executor.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class SweepExecutor(old.SweepExecutor):
 def configure(self):
  super().configure();goal=np.array([np.mean(self.runtime.profile['goal_x']),np.mean(self.runtime.profile['goal_y'])]);self.base_x_cap=min(float(self.block[0]),float(goal[0]))-float(self.config.get('front_workspace_rear_min_m',.36));self.base_goal[0]=min(float(self.block[0])-float(self.config.get('working_forward_m',.43)),self.base_x_cap);self.reach_diag_second=-1;self.reach_rows=[]
 def interaction(self,age,t,dt):
  world=super().interaction(age,t,dt);p=self.runtime.task.geometric_center(0);self.base_goal[0]=min(float(p[0])-float(self.config.get('working_forward_m',.43)),self.base_x_cap);self.base_goal[1]=self.fixed_base_y;return world
 def command(self):
  values,diag=super().command();m=self.runtime.physics.model;d=self.runtime.physics.data[0];sec=int(self.runtime.physics.ticks[0])//500
  if 'commanded_world_base_velocity' in diag:diag['commanded_world_base_velocity'][2]=values[2]
  if sec!=self.reach_diag_second:
   self.reach_diag_second=sec;gid=m.geom('sw_block').id;rot=d.geom_xmat[gid].reshape(3,3);row={'s':sec,'phase':diag['phase'],'actual_block_xyz':d.geom_xpos[gid].tolist(),'actual_block_yaw_rad':float(np.arctan2(rot[1,0],rot[0,0])),'actual_foot_xyz':d.geom_xpos[m.geom('FL').id].tolist(),'actual_base_xyz':self.core.robot.position[0].cpu().tolist(),'desired_world_target':diag.get('unprojected_world_target'),'projected_world_target':diag['world_target'],'base_goal_xy':self.base_goal.tolist(),'actual_robot_yaw_rad':diag['actual_yaw_rad']};self.reach_rows.append(row);print(json.dumps({'actual_reach_diagnostic':row}),flush=True)
   if self.config.get('reach_diagnostic_file'):
    path=Path(self.config['reach_diagnostic_file']).resolve();assert path.is_relative_to(Path(__file__).resolve().parent);path.write_text(json.dumps({'role':'Lightweight1Hz actual geometry/target observations only','original_A05_contact_math_retained':True,'rows':self.reach_rows},indent=2)+'\n')
  return values,diag
