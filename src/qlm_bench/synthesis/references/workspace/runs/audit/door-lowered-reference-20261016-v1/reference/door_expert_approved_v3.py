"""Versioned28cm slow top-contact expert; unchanged RAMBO/native9/physics."""
from pathlib import Path
import sys,json,math
import numpy as np,torch
from qlm_bench.controllers.rambo.math import quat_apply_inverse,quat_mul,quat_inv
OLD=Path(str(__import__('qlm_bench.synthesis.references',fromlist=['REFERENCES']).REFERENCES)+'/runs/audit/remaining-six-reference-20261016-v1');sys.path.insert(0,str(OLD));sys.path.insert(0,str(OLD/'pairs/drawer-door'))
from shared_executor import SmoothReference,blend
from world_intent_mixin import WorldIntentMixin
from qlm_bench.synthesis.trace import CandidateRejected
from door_geometry import DoorGeometry
from door_plan import DoorPlan

class HigherHoverPlanApprovedV3(DoorPlan):
 def hover(self,data,ready=False):
  point=super().hover(data,ready);point[2]+=float(self.config.get("hover_clearance_m",.020))-.004
  return point if ready else point+self.g.leaf_rotation(data)[:,0]*float(self.config.get('forward_bias_m',.028))
 def tracking_lead(self,data,point):
  normal=self.g.leaf_rotation(data)[:,0];gap=float(np.dot(self.g.point(data)-self.g.sphere(data)["centre"],normal));return point+normal*float(np.clip(.5*gap,0.,.008))
 def press(self,data,angle,depth=.002):
  point=super().press(data,angle,depth)
  if getattr(self,'hold_normal_bias',False):return point+self.g.leaf_rotation(data)[:,0]*float(self.config.get('press_normal_bias_m',.024))
  return self.tracking_lead(data,point)

 def press_base(self,data,angle):
  origin,fixture=self.g.fixture(data);door=float(np.clip(self.g.joints(data)[0],0.,math.radians(15.)));base=origin+self.g.leaf_rotation(data,door)@np.array([*self.base_offset,0.]);return base[:2]+(self.g.point(data,angle)-self.g.point(data,0.))[:2]

class DoorSlowExpertApprovedV3(WorldIntentMixin,SmoothReference):
 def configure(self):
  self.config.update(recipe_id='door28-a19-approved-geometric-terminal-v3',carry_body_xyz_m=[.32,.15,-.13],carry_seconds=2.,world_intent_speed_m_s=.045,world_intent_acceleration_m_s2=.12)
  self.g=DoorGeometry(self.runtime.physics.model,self.runtime.profile,self.config.get('station_fraction',.5652173913043478));self.plan=HigherHoverPlanApprovedV3(self.g,self.config);d=self.runtime.physics.data[0];self.base_goal=self.plan.neutral_base(d);self.fixture_yaw=math.atan2(self.g.fixture(d)[1][1,0],self.g.fixture(d)[1][0,0]);self.heading_target=self.fixture_yaw+self.plan.heading;self.heading_omega=0.;self.heading_time=None;self.stage='ready';self.stage_time=None;self.stage_start=None;self.segment='original_settle';self.clear_ticks=0;self.max_clear_ticks=0;self.overbar_ticks=0;self.upper_ticks=0;self.press_angle=0.;self.press_depth=.008;self.unlock_ticks=0;self.unlock_time=None;self.panel_time=None;self.panel_start=None;self.panel_base_start=None;self.panel_lead=0.;self.contact={};self.interaction_base_feedback=None;self.interaction_base_velocity=np.zeros(2);self.last_emitted_base_world_velocity=None;self.last_unlock_report=None;self.last_direct_unlock=False;self.first_press_time=None;self.current_base_advance=0.;self.original_base_offset=self.plan.base_offset.copy();self.lost_upper_ticks=0;self.last_sphere_goal=None;self.diag_tick=-1;self.initialize_world_intent()

 def yaw(self):
  w,x,y,z=self.runtime.physics.data[0].qpos[3:7]
  return math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))

 def transition_stage(self,stage,t,start=None):
  if stage=='press':
   self.plan.hold_normal_bias=True
   self.lost_upper_ticks=0
   if self.first_press_time is None:self.first_press_time=t
  previous=self.stage;self.stage=stage;self.stage_time=t;self.stage_start=None if start is None else np.asarray(start).copy()
  print(json.dumps(dict(door_stage_transition=True,t=t,from_stage=previous,to_stage=stage,original_task_sticky_unlocked=bool(self.runtime.task.unlocked[0]),actual_task_joints=dict(zip(['door','lever','bolt'],self.g.joints(self.runtime.physics.data[0]))))),flush=True)

 def interaction(self,age,t,dt):
  if self.first_press_time is not None:
   advance=.020*blend((t-self.first_press_time)/2.);delta=advance-self.current_base_advance;self.current_base_advance=advance;self.plan.base_offset[:]=self.original_base_offset+[advance,0.]
   if self.stage in ('forward','seat','press','initial_push'):self.base_goal+=self.g.fixture(self.runtime.physics.data[0])[1][:2,0]*delta
  d=self.runtime.physics.data[0];door,lever,bolt=self.g.joints(d);s=self.g.sphere(d);self.contact=self.g.contacts(d);self.add_contact_moments(d);axis=d.geom_xmat[self.g.handle].reshape(3,3)[:,2];along_actual=float(np.dot(s['centre']-d.geom_xpos[self.g.handle],axis));closest=d.geom_xpos[self.g.handle]+axis*np.clip(along_actual,-self.g.bar_half,self.g.bar_half);separation=s['centre']-closest;distance=float(np.linalg.norm(separation));self.geometric_upper=bool(distance<=.065 and abs(along_actual)<=self.g.bar_half+.003 and separation[2]>0.);upper=any(c['normal_N']>.1 and c['handle_to_toe_normal'][2]>0. for c in self.contact['actual_toe_handle']);self.contact['user_upper_surface_contact']=upper;self.upper_ticks=self.upper_ticks+1 if upper else 0;self.clear_ticks=self.clear_ticks+1 if s['clearance']>=.003 else 0;self.max_clear_ticks=max(self.max_clear_ticks,self.clear_ticks)
  if self.stage_time is None:
   self.stage_time=t;self.stage_start=np.asarray(self.interaction_world_start)+s['geom_offset_world']
  sticky=bool(self.runtime.task.unlocked[0]);direct=bool(self.runtime.task.criteria[0].observe(d)['geometric_unlock_event'])
  if sticky!=self.last_unlock_report or direct!=self.last_direct_unlock:
   print(json.dumps(dict(door_strict_unlock_observation=True,t=t,measurement_physics_step=int(self.runtime.physics.ticks[0]),original_task_sticky_unlocked=sticky,actual_current_socket_exit_and_lever_condition=direct,actual_task_joints=dict(door=door,lever=lever,bolt=bolt),read_only_observer_no_physical_unlock=True)),flush=True);self.last_unlock_report=sticky;self.last_direct_unlock=direct
  # Preserve the reviewed A19 action branches; task success ends the episode.
  # A17 ended while actual upper contact persisted. Do not abort at old5deg workspace marker; original success/fall/60s lifecycle remains authoritative.
  elapsed=t-self.stage_time;leaf=self.g.leaf_rotation(d);normal=leaf[:,0];point=self.g.point(d);self.heading_target=self.fixture_yaw+self.plan.heading+door
  # Front-upper/side contact is logged, not an automatic abort.
  # Any actual toe contact on the upper hemisphere may initiate downward pressing.
  if self.stage=='ready':
   target=self.plan.hover(d,True);target[2]=self.stage_start[2];target=self.stage_start+(target-self.stage_start)*blend(elapsed/2.);self.segment='uncontacted_world_ready_before_raise'
   if elapsed>=2.:self.transition_stage('raise',t,target)
  elif self.stage=='raise':
   wanted=self.plan.hover(d,True);target=self.stage_start+(wanted-self.stage_start)*blend(elapsed/4.);self.segment='raise_fixed_world_ready_XY_whole_sphere_clearance'
   if elapsed>=4. and self.clear_ticks>=10:self.transition_stage('forward',t,target)
  elif self.stage in ('forward','seat'):
   hover=self.plan.hover(d,False);axis=d.geom_xmat[self.g.handle].reshape(3,3)[:,2];along=float(np.dot(s['centre']-d.geom_xpos[self.g.handle],axis));gap=float(np.dot(point-s['centre'],normal));overbar=abs(gap)<=.008 and abs(along)<=self.g.bar_half-.015 and s['clearance']>=.006 and s['velocity'][2]>=-.10;self.overbar_ticks=self.overbar_ticks+1 if overbar else 0
   target=hover.copy();self.segment='slow_forward_while_actual_whole_sphere_clear'
   if self.stage=='forward' and s['clearance']<.003 and self.last_sphere_goal is not None:target[:2]=self.last_sphere_goal[:2];self.segment='hold_XY_restore_clearance'
   if upper:self.press_angle=lever;self.transition_stage('press',t);target=self.plan.press(d,self.press_angle,self.press_depth)
   elif self.stage=='forward' and self.overbar_ticks>=2:self.transition_stage('seat',t,hover)
   if self.stage=='seat':
    self.segment='guarded_slow_vertical_top_seat';target=self.stage_start.copy();desired=self.plan.press(d,lever,.001);target[:2]=desired[:2];target[2]=max(desired[2],float(self.stage_start[2])-.008*(t-self.stage_time))
    if abs(gap)>.030 or abs(along)>self.g.bar_half-.005:self.transition_stage('forward',t,hover);target=hover
  elif self.stage=='press':
   self.segment='real_top_toe_press_follow_actual_lever_cam_bolt';self.base_goal=self.plan.press_base(d,lever)
   self.lost_upper_ticks=0 if (upper or self.geometric_upper) else self.lost_upper_ticks+1
   if upper:
    desired=max(self.g.lever_min,lever-math.radians(3.));self.press_angle=desired;fz=self.contact['actual_FL_handle_world_force_N'][2]
    if fz>-20.:self.press_depth=min(.028,self.press_depth+.004*dt)
    elif fz<-30.:self.press_depth=max(.002,self.press_depth-.004*dt)
   else:self.press_angle=lever
   target=self.plan.press(d,self.press_angle,self.press_depth if (upper or self.geometric_upper) else -.003)
   if self.lost_upper_ticks>=10:
    self.overbar_ticks=0;self.transition_stage('forward',t,target);self.segment='lost_actual_upper_reanchor_to_current_bar_then_requalify_top';target=self.plan.hover(d,False)
   self.unlock_ticks=self.unlock_ticks+1 if direct else 0
  else:
   raise RuntimeError('Unknown approved A19 reference stage: '+self.stage)
  self.last_sphere_goal=target.copy()
  # Native9 target is retained kinematic foot-body origin, not collision centre.
  return target-s['geom_offset_world']

 def add_contact_moments(self,d):
  index=0;total=0.;anchor=d.xanchor[self.g.lever_joint];axis=d.xaxis[self.g.lever_joint]
  for contact in d.contact[:d.ncon]:
   a,b=map(int,contact.geom)
   if a in self.g.asset_geoms and int(self.g.model.geom_bodyid[b]) in self.g.robot:asset,robot=a,b
   elif b in self.g.asset_geoms and int(self.g.model.geom_bodyid[a]) in self.g.robot:asset,robot=b,a
   else:continue
   pair=self.contact['pairs'][index];index+=1;pair['actual_contact_world_position_m']=contact.pos.tolist()
   if asset==self.g.handle:
    moment=float(np.dot(np.cross(contact.pos-anchor,np.asarray(pair['actual_world_force_on_asset_N'])),axis));pair['actual_moment_about_lever_axis_Nm']=moment
    if pair['robot_body'].startswith('FL_'):total+=moment
  assert index==len(self.contact['pairs'])
  self.contact['actual_FL_handle_axis_moment_Nm']=total
  self.contact['contact_positions_and_moments_source']='current Native contact positions and measured forces; not snapshot reconstructed force'

 def reject(self,t,reason):
  d=self.runtime.physics.data[0];print(json.dumps(dict(door_candidate_rejected=True,t=t,stage=self.stage,reason=reason,actual_qpos=d.qpos.tolist(),actual_qvel=d.qvel.tolist(),actual_contact=self.contact,actual_core_IK_reference_rad=self.core._desired_joint_pos[0,[0,4,8]].cpu().tolist(),actual_motor_target_rad=self.core.desired_pos[0,[0,4,8]].cpu().tolist())),flush=True);raise CandidateRejected(reason)

 def command(self):
  values,diag=super().command();d=self.runtime.physics.data[0];t=float(d.time);dt=.02 if self.heading_time is None else t-self.heading_time;self.heading_time=t;error=math.atan2(math.sin(self.heading_target-self.yaw()),math.cos(self.heading_target-self.yaw()));wanted=float(np.clip(1.5*error,-.25,.25));self.heading_omega+=float(np.clip(wanted-self.heading_omega,-.5*dt,.5*dt));values[2]=self.heading_omega
  if self.phase=='interaction' and self.first_press_time is not None:
   actual_base=d.qpos[:2].copy()
   if self.interaction_base_feedback is None:self.interaction_base_feedback=actual_base.copy();self.interaction_base_velocity=self.velocity.copy() if self.last_emitted_base_world_velocity is None else self.last_emitted_base_world_velocity.copy()
   else:self.interaction_base_feedback+=(1-np.exp(-dt/.2))*(actual_base-self.interaction_base_feedback)
   wanted_base_velocity=1.2*(self.base_goal-self.interaction_base_feedback);norm=float(np.linalg.norm(wanted_base_velocity))
   if norm>.07:wanted_base_velocity*=.07/norm
   velocity_step=wanted_base_velocity-self.interaction_base_velocity;step_norm=float(np.linalg.norm(velocity_step))
   if step_norm>.10*dt:velocity_step*=.10*dt/step_norm
   self.interaction_base_velocity+=velocity_step;speed_norm=float(np.linalg.norm(self.interaction_base_velocity))
   if speed_norm>.07:self.interaction_base_velocity*=.07/speed_norm
   yaw_frame=quat_mul(self.core.base_quat,quat_inv(self.core.base_quat_rp));native_velocity=quat_apply_inverse(yaw_frame,torch.tensor([[*self.interaction_base_velocity,0.]],dtype=torch.float32,device=self.core.device))[0].cpu().tolist();values[:2]=native_velocity[:2];diag['commanded_world_base_velocity']=[*self.interaction_base_velocity.tolist(),self.heading_omega];diag['expert_base_feedback_xy_m']=self.interaction_base_feedback.tolist();diag['base_feedback_mode']='after_real_top_only actualposition lowpass0.2s;velocitynorm70mm/s;normacc100mm/s2;original_native9'
  if 'commanded_world_base_velocity' in diag:diag['commanded_world_base_velocity'][2]=self.heading_omega
  self.last_emitted_base_world_velocity=np.asarray(diag.get('commanded_world_base_velocity',[0.,0.,0.])[:2]).copy()
  diag['expert_base_error_xy_m']=(self.base_goal-d.qpos[:2]).tolist()
  assert values[6:9]==[0.,0.,0.]
  sphere=self.g.sphere(d);joints=dict(zip(['door','lever','bolt'],self.g.joints(d)));tick=int(self.runtime.physics.ticks[0]);diag.update(actual_requested_native9=values,actual_commanded_world_base_velocity=diag.get('commanded_world_base_velocity'),actual_base_error_xy_m=diag['expert_base_error_xy_m'],route_stage=self.stage,segment=self.segment,original_task_sticky_unlocked=bool(self.runtime.task.unlocked[0]),actual_task_joints=joints,actual_toe_world=sphere['centre'].tolist(),actual_toe_velocity_world=sphere['velocity'].tolist(),actual_whole_sphere_clearance_m=sphere['clearance'],actual_contact=self.contact,requested_sphere_world=None if self.last_sphere_goal is None else self.last_sphere_goal.tolist(),measurement_physics_step=tick,measurement_simulation_time_ns=tick*2_000_000,measurement_boundary='command start snapshot_i',geometric_upper_not_measured_force=getattr(self,'geometric_upper',False),clear_ticks=self.clear_ticks,max_clear_ticks=self.max_clear_ticks,actual_yaw_rad=self.yaw(),heading_target_rad=self.heading_target,high_level_pressure_target_depth_m=self.press_depth,pressure_depth_is_not_physical_penetration=True)
  logtick=tick//100
  if logtick!=self.diag_tick:
   self.diag_tick=logtick;print(json.dumps(dict(door_slow_diagnostic=True,t=t,phase=self.phase,actual_requested_native9=values,actual_commanded_world_base_velocity=diag.get('commanded_world_base_velocity'),actual_base_error_xy_m=diag['expert_base_error_xy_m'],route_stage=self.stage,segment=self.segment,actual_qpos=d.qpos.tolist(),actual_qvel=d.qvel.tolist(),original_task_sticky_unlocked=bool(self.runtime.task.unlocked[0]),actual_task_joints=joints,actual_toe_world=sphere['centre'].tolist(),actual_toe_velocity_world=sphere['velocity'].tolist(),actual_whole_sphere_clearance_m=sphere['clearance'],actual_contact=self.contact,requested_world=diag.get('requested_world_intent'),actual_emitted_world_reference=diag['actual_emitted_world_reference'],actual_previous_core_IK_reference_rad=self.core._desired_joint_pos[0,[0,4,8]].cpu().tolist(),actual_previous_motor_target_rad=self.core.desired_pos[0,[0,4,8]].cpu().tolist(),actual_previous_actor_residual18=self.core._last_action[0].cpu().tolist(),core_input_matches_previous=diag['previous_native_ee_match'],history_matches_seen=diag['latest_history_matches_seen'],base_goal=self.base_goal.tolist(),clear_ticks=self.clear_ticks,max_clear_ticks=self.max_clear_ticks)),flush=True)
  if self.contact.get('actual_FL_handle_normal_N',0.)>1.:
   print(json.dumps(dict(door_contact_diagnostic=True,t=t,measurement_physics_step=tick,measurement_simulation_time_ns=tick*2_000_000,measurement_boundary='command start snapshot_i',core_IK_clock='last end_control at boundary from previously submitted native9; field previous is historical label',motor_target_clock='preceding begin_control retained motor target; asynchronous with refreshed coreIK; FK difference is not actor causal attribution',actual_requested_native9=values,actual_commanded_world_base_velocity=diag.get('commanded_world_base_velocity'),actual_base_error_xy_m=diag['expert_base_error_xy_m'],route_stage=self.stage,segment=self.segment,original_task_sticky_unlocked=bool(self.runtime.task.unlocked[0]),actual_task_joints=joints,high_level_pressure_target_depth_m=self.press_depth,actual_toe_world=sphere['centre'].tolist(),actual_toe_velocity_world=sphere['velocity'].tolist(),actual_contact=self.contact,actual_emitted_world_reference=diag['actual_emitted_world_reference'],actual_qpos=d.qpos.tolist(),actual_previous_core_IK_reference_rad=self.core._desired_joint_pos[0,[0,4,8]].cpu().tolist(),actual_previous_motor_target_rad=self.core.desired_pos[0,[0,4,8]].cpu().tolist())),flush=True)
  return values,diag
