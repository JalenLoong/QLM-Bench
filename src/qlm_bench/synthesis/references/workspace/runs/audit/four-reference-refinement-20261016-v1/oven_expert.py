"""Fixed-default-stance45deg Oven expert: raw native9 intent, original RAMBO/core untouched.

World-fixed pre-contact/support; physical-leaf contact frame only after braking.
All physical state is read-only. No rendering mirror, added force or joint control.
"""
import math,json
import numpy as np,mujoco,torch
from qlm_bench.controllers.rambo.math import quat_apply,quat_apply_inverse,quat_mul,quat_inv
from qlm_bench.synthesis.press_reference import retained_fk


def ry(q):
 c,s=math.cos(q),math.sin(q)
 return np.array([[c,0,s],[0,1,0],[-s,0,c]])

def rz(q):
 c,s=math.cos(q),math.sin(q)
 return np.array([[c,-s,0],[s,c,0],[0,0,1.]])

class OvenBase:
 def __init__(self,config=None):self.config=dict(config or {})
 def actual_world_point(self):
  return (quat_apply(self.core.base_quat,self.core.ee_pos_b[:,0,:])+self.core.robot.position)[0].detach().cpu().numpy().astype(float)
 def reset(self,runtime,scene):
  self.runtime=runtime;self.core=runtime.core;self.scene=scene;self.m=runtime.physics.model;self.primary=self.m.body('primary').id;self.hinge=self.m.joint('close_oven_door_hinge');self.adr=int(self.hinge.qposadr[0]);self.dof=int(self.hinge.dofadr[0]);self.pivot=self.m.body('primary').pos.copy();rot=np.zeros(9);mujoco.mju_quat2Mat(rot,self.m.body('primary').quat);self.fixture=rot.reshape(3,3)
  self.phase='original_stance_prefix';self.time=None;self.sent_world=self.actual_world_point();self.previous_leaf=None;self.expected_previous_native=None;self.velocity=np.zeros(2);self.yaw_velocity=0.;self.base_feedback=self.core.robot.position[0,:2].cpu().numpy().astype(float);self.base_goal=self.base_feedback.copy();self.fixed_start_base=self.base_goal.copy();self.previous_base_goal=self.base_goal.copy();self.base_ff=np.zeros(2);self.maximum_forward_goal=None;self.pressure_requested=0.;self.filtered_torque=0.;self.filtered_qdot=0.;self.support_stable_since=None;self.first_contact=None;self.last_log_second=-1;self.budget=[];self.swing_started=None;self.entry_stable_since=None;self.entry_origin_world=None;self.entry_working_base=None
  q=float(runtime.physics.data[0].qpos[self.adr]);leaf=self.fixture@ry(q);local=leaf.T@(self.sent_world-self.pivot);self.radius=float(np.clip(local[2],.09,.42));self.precontact_goal=self.pivot+leaf@np.array([-.038,self.config.get('contact_y_m',-.248),self.radius]);self.reset_q=q;self.source_ready_robot=scene['initial_state']['qpos'][:19]
 def contacts(self,d):
  rows=[];torque=0.;other_robot=[];self.nonFL_contact_evidence=[];axis=self.fixture@np.array([0.,1.,0])
  for i,c in enumerate(d.contact):
   a,b=int(c.geom1),int(c.geom2);ba,bb=int(self.m.geom_bodyid[a]),int(self.m.geom_bodyid[b])
   if self.primary not in (ba,bb):continue
   other=b if ba==self.primary else a;name=self.m.body(int(self.m.geom_bodyid[other])).name
   if name.startswith('FL_'):
    wrench=np.zeros(6);mujoco.mj_contactForce(self.m,d,i,wrench);frame=c.frame.reshape(3,3);sign=1. if bb==self.primary else -1.;value=float(np.dot(axis,np.cross(c.pos-d.xpos[self.primary],sign*frame.T@wrench[:3])+sign*frame.T@wrench[3:]));torque+=value
    rows.append({'robot_body':name,'geoms':[self.m.geom(a).name,self.m.geom(b).name],'normal_force_N':float(wrench[0]),'closing_torque_Nm':value})
   elif name in ['base','Head_upper','Head_lower'] or name.startswith(('FR_','RL_','RR_')):
    other_robot.append(name);wrench=np.zeros(6);mujoco.mj_contactForce(self.m,d,i,wrench);frame=c.frame.reshape(3,3);sign=1. if bb==self.primary else -1.;moment=float(np.dot(axis,np.cross(c.pos-d.xpos[self.primary],sign*frame.T@wrench[:3])+sign*frame.T@wrench[3:]));self.nonFL_contact_evidence.append(dict(body=name,normal_force_N=float(wrench[0]),closing_torque_Nm=moment,distance_m=float(c.dist)))
  return rows,torque,other_robot
 def command(self):
  d=self.runtime.physics.data[0];t=float(self.runtime.physics.ticks[0])*.002;dt=.02 if self.time is None else t-self.time
  if not 0<dt<=.020001:raise ValueError('50Hz expert boundary required')
  self.time=t;q=float(d.qpos[self.adr]);qdot=float(d.qvel[self.dof]);leaf=self.fixture@ry(q);normal=leaf@np.array([1.,0,0]);actual=self.actual_world_point();base=self.core.robot.position[0].cpu().numpy().astype(float);quaternion=self.core.base_quat[0].cpu().numpy();x,y,z,w=map(float,quaternion);yaw=math.atan2(2*(w*z+x*y),1-2*(y*y+z*z));fl,tau,other_robot=self.contacts(d)
  seen=self.core._ee_pos_commands[0].detach().cpu().numpy();history=self.core._obs_history[0,-1,-24:-21].detach().cpu().numpy();match=None if self.expected_previous_native is None else bool(np.array_equal(seen,self.expected_previous_native))
  if match is False:raise RuntimeError('Original core did not receive prior native9 raw intent')
  real_contact=any(r['normal_force_N']>self.config.get('contact_force_detection_N',.05) for r in fl)
  alpha=1-np.exp(-dt/self.config.get('feedback_filter_seconds',.08));self.filtered_torque+=alpha*(tau-self.filtered_torque);self.filtered_qdot+=alpha*(qdot-self.filtered_qdot)
  original_FL_mode=float(self.core.contact_generator.desired_contact_mode[0,0])
  if self.phase=='original_stance_prefix' and original_FL_mode<-.5:
   self.phase='under_leaf_entry';self.swing_started=t;self.radius=self.config.get('entry_radius_m',.38);self.precontact_goal=self.pivot+leaf@np.array([-.070,self.config.get('contact_y_m',-.248),self.radius]);self.entry_origin_world=self.sent_world.copy();self.entry_working_base=self.precontact_goal[:2]-(self.fixture@np.array([self.config.get('working_forward_m',.26),self.config.get('working_lateral_m',.252),0]))[:2]
  if real_contact and self.first_contact is None:
   self.first_contact={'time_s':t,'q_rad':q,'q_deg':math.degrees(q),'actual_FL_world':actual.tolist(),'contacts':fl};print(json.dumps({'first_real_FL_contact':self.first_contact,'reset_angle_deg':math.degrees(self.reset_q)}),flush=True)
  if self.phase=='under_leaf_entry':
   error_entry=float(np.linalg.norm(actual-self.precontact_goal))
   if error_entry<.025:
    if self.entry_stable_since is None:self.entry_stable_since=t
    if t-self.entry_stable_since>=.12:self.phase='ready_precontact_world';self.precontact_goal=self.pivot+leaf@np.array([-.038,self.config.get('contact_y_m',-.248),self.radius])
   else:self.entry_stable_since=None
  reliable_FL_support=real_contact and tau>.10 and float(np.linalg.norm(actual-self.sent_world))<.055
  if reliable_FL_support and self.phase=='ready_precontact_world':self.phase='world_support_braking'
  if self.phase=='world_support_braking':
   if reliable_FL_support and self.filtered_qdot>=-.10:
    if self.support_stable_since is None:self.support_stable_since=t
    if t-self.support_stable_since>=self.config.get('support_stable_seconds',.12):
     self.phase='leaf_attached_close';local=leaf.T@(actual-self.pivot);self.radius=float(np.clip(local[2],.09,.42));anchor=self.pivot+leaf@np.array([-.038,self.config.get('contact_y_m',-.248),self.radius]);self.pressure_requested=float(np.clip(np.dot(self.sent_world-anchor,normal),0.,.04));self.previous_leaf=leaf.copy()
   else:self.support_stable_since=None
  self.base_feedback+=(1-np.exp(-dt/.2))*(base[:2]-self.base_feedback)
  requested_torque=None;pressure_prior=self.pressure_requested;anchor=None
  if self.phase=='leaf_attached_close':
   target_radius=float(np.clip((self.config.get('maximum_contact_world_height_m',.25)-self.pivot[2]+math.sin(q)*(-.038))/max(math.cos(q),.0001),.09,.42));self.radius+=float(np.clip(target_radius-self.radius,-.04*dt,.04*dt));anchor=self.pivot+leaf@np.array([-.038,self.config.get('contact_y_m',-.248),self.radius])
   peek=min(.02,q+.04);rpeek=float(np.clip((self.config.get('maximum_contact_world_height_m',.30)-self.pivot[2]+math.sin(peek)*(-.038))/max(math.cos(peek),.0001),.09,.42));look=self.pivot+self.fixture@ry(peek)@np.array([-.038,self.config.get('contact_y_m',-.248),rpeek]);goal=look[:2]-(self.fixture@np.array([self.config.get('working_forward_m',.26),self.config.get('working_lateral_m',.252),0]))[:2];localgoal=self.fixture[:2,:2].T@(goal-self.pivot[:2])
   if self.maximum_forward_goal is None:self.maximum_forward_goal=float(localgoal[0])
   self.maximum_forward_goal=max(self.maximum_forward_goal,float(localgoal[0]));localgoal[0]=self.maximum_forward_goal;self.base_goal=self.pivot[:2]+self.fixture[:2,:2]@localgoal
   if t>=self.config.get('preapproach_stop_s',4.):self.base_goal=self.timed_stop_goal.copy()
   allowed=bool(np.max(abs(self.base_goal-self.base_feedback))<.05);desired_speed=.10 if allowed else 0.;requested_torque=max(0.,float(d.qfrc_bias[self.dof]-d.qfrc_passive[self.dof])+2.*(desired_speed-self.filtered_qdot));rate=float(np.clip(self.config.get('pressure_integral_m_Nm_s',.006)*(requested_torque-self.filtered_torque),-.012,.012));self.pressure_requested=float(np.clip(pressure_prior+dt*rate,0.,.04));wanted=anchor+normal*self.pressure_requested
   baseline=self.pivot+leaf@(self.previous_leaf.T@(self.sent_world-self.pivot)) if self.previous_leaf is not None else self.sent_world.copy()
  else:
   wanted=self.precontact_goal.copy();baseline=self.sent_world.copy();self.base_goal=self.fixed_start_base.copy()
   if self.entry_working_base is not None:
    if self.phase=='under_leaf_entry':
     delta=self.precontact_goal-self.entry_origin_world;den=max(float(delta@delta),1e-9);fraction=float(np.clip(min((actual-self.entry_origin_world)@delta,(self.sent_world-self.entry_origin_world)@delta)/den,0.,1.));self.base_goal=self.fixed_start_base+fraction*(self.entry_working_base-self.fixed_start_base)
    else:self.base_goal=self.entry_working_base.copy()
  if self.phase=='original_stance_prefix':
   yawframe=quat_mul(self.core.base_quat,quat_inv(self.core.base_quat_rp));origin=self.core.robot.position[0].clone();origin[2]=0.;wanted=(quat_apply(yawframe,torch.tensor([[.1934,.142,.05]],dtype=torch.float32,device=self.core.device))+origin[None])[0].cpu().numpy().astype(float);baseline=wanted.copy()
  step=wanted-baseline;length=float(np.linalg.norm(step));bound=self.config.get('relative_position_speed_m_s',.06)*dt;limited=length>bound
  if limited:step*=bound/length
  sent=baseline+step
  # Bound active position preload; a moving leaf may require absolute world motion.
  local_sent=leaf.T@(sent-self.pivot);upper=-.038+.04
  if local_sent[0]>upper:local_sent[0]=upper;sent=self.pivot+leaf@local_sent
  delivered_normal=float(local_sent[0]+.038)
  if self.phase=='leaf_attached_close':
   # Slow bounded back-calculation. requested pressure is not replaced each tick.
   delivered=float(np.dot(sent-anchor,normal));error=min(0.,delivered-self.pressure_requested);correction=(1-np.exp(-dt/self.config.get('antiwindup_seconds',5.)))*error
   state=float(np.clip(self.pressure_requested+correction,0.,.04));self.pressure_requested=float(np.clip(state,pressure_prior-.012*dt,pressure_prior+.012*dt));self.previous_leaf=leaf.copy()
  error=self.base_goal-self.base_feedback;instantaneous=np.clip((self.base_goal-self.previous_base_goal)/dt,-.08,.08);self.previous_base_goal=self.base_goal.copy();self.base_ff+=(1-np.exp(-dt/.15))*(instantaneous-self.base_ff);wantedv=np.clip(1.5*error+self.base_ff,[-.15,-.18],[.15,.18])
  self.velocity+=np.clip(wantedv-self.velocity,-.12*dt,.12*dt);yawgoal=math.atan2(self.fixture[1,0],self.fixture[0,0]);yawerr=math.atan2(math.sin(yawgoal-yaw),math.cos(yawgoal-yaw));yawwant=float(np.clip(2.5*yawerr,-.4,.4));self.yaw_velocity+=float(np.clip(yawwant-self.yaw_velocity,-.8*dt,.8*dt))
  yawframe=quat_mul(self.core.base_quat,quat_inv(self.core.base_quat_rp));origin=self.core.robot.position[0].clone();origin[2]=0.;native=quat_apply_inverse(yawframe,torch.tensor(sent[None],dtype=torch.float32,device=self.core.device)-origin[None])[0].cpu().tolist();vel=quat_apply_inverse(yawframe,torch.tensor([[*self.velocity,0.]],dtype=torch.float32,device=self.core.device))[0].cpu().tolist();values=[*vel[:2],self.yaw_velocity,*native,0.,0.,0.]
  emitted=(quat_apply(yawframe,torch.tensor([native],dtype=torch.float32,device=self.core.device))+origin[None])[0].cpu().numpy().astype(float);self.sent_world=emitted;self.expected_previous_native=np.asarray(native,np.float32)
  diag={'phase':self.phase,'recipe':self.config['recipe_id'],'world_target':emitted.tolist(),'unprojected_world_target':wanted.tolist(),'actual_fl_eef_world':actual.tolist(),'commanded_world_base_velocity':[*self.velocity.tolist(),0.],'base_goal_xy':self.base_goal.tolist(),'base_world_position':base.tolist(),'actor_target_mode':'raw native9 world intent; original core IK/PD/actor/history unchanged','core_seen_previous_native_ee':seen.tolist(),'latest_history_previous_native_ee':history.tolist(),'previous_native_ee_match':match,'latest_history_matches_seen':bool(np.array_equal(history,seen)),'original_FL_contact_mode':original_FL_mode,'swing_started_s':self.swing_started,'normal_requested_state_m':self.pressure_requested,'delivered_normal_from_leaf_center_m':delivered_normal,'actual_q_rad':q,'actual_qdot_rad_s':qdot,'filtered_qdot_rad_s':self.filtered_qdot,'actual_FL_contact_closing_torque_Nm':tau,'requested_torque_Nm':requested_torque,'first_real_contact':self.first_contact,'other_robot_contact_bodies':other_robot,'nonFL_force_contacts':self.nonFL_contact_evidence,'actual_FL_contacts':fl,'position_limiter_frame':'world before contact; actual physical leaf after support stable','relative_position_limited':limited}
  if t<=self.config.get('initial_angle_diagnostic_seconds',1.) or int(t)!=self.last_log_second:
   self.last_log_second=int(t);print(json.dumps({'oven45_actual_boundary':True,'time_s':t,'reset_q_deg':math.degrees(self.reset_q),'q_deg':math.degrees(q),'phase':self.phase,'actual_FL_world':actual.tolist(),'raw_intent_world':emitted.tolist(),'actual_base_xyzw':quaternion.tolist(),'base_goal_xy':self.base_goal.tolist(),'actual_robot_qpos':d.qpos[:19].tolist(),'core_desired_joint_pos':self.core.desired_pos[0].cpu().tolist(),'commanded_world_base_velocity':self.velocity.tolist(),'yaw_command':self.yaw_velocity,'normal_requested_m':self.pressure_requested,'delivered_normal_m':delivered_normal,'FL_contacts':fl,'other_robot_contacts':other_robot,'filtered_qdot':self.filtered_qdot,'original_FL_contact_mode':original_FL_mode,'base_world':base.tolist(),'core_previous_intent_match':match}),flush=True)
  return values,diag


class Oven45WorldExpert(OvenBase):
 def reset(self,runtime,scene):
  super().reset(runtime,scene)
  self.timed_origin=None;self.timed_stop_goal=self.pivot[:2]+(self.fixture@np.array([self.config.get('preapproach_goal_x_m',.25)-.84,-.18,0]))[:2]
  self.timed_velocity=np.zeros(2);self.timed_handoff=False
 def command(self):
  t=float(self.runtime.physics.ticks[0])*.002;dt=.02
  if t>=4. and not self.timed_handoff:
   self.timed_handoff=True;self.phase='under_leaf_entry';self.entry_origin_world=self.sent_world.copy()
   d=self.runtime.physics.data[0];q=float(d.qpos[self.adr]);self.radius=.25
   self.precontact_goal=self.pivot+self.fixture@ry(q)@np.array([-self.config.get('precontact_standoff_m',.05),self.config.get('contact_y_m',0),self.radius])
   self.fixed_start_base=self.timed_stop_goal.copy();self.entry_working_base=self.timed_stop_goal.copy();self.base_goal=self.timed_stop_goal.copy();self.previous_base_goal=self.base_goal.copy();self.base_ff[:]=0.;self.entry_stable_since=None
  values,diag=super().command();base=self.core.robot.position[0].cpu().numpy().astype(float)
  if t>=1.02:
   yawframe=quat_mul(self.core.base_quat,quat_inv(self.core.base_quat_rp));origin=self.core.robot.position[0].clone();origin[2]=0.
   if t<4.:
    if self.timed_origin is None:self.timed_origin=base[:2].copy()
    u=float(np.clip((t-1.)/3.,0.,1.));b=u*u*(3-2*u);derivative=6*u*(1-u)/3.
    goal=self.timed_origin+(self.timed_stop_goal-self.timed_origin)*b
    wanted=(self.timed_stop_goal-self.timed_origin)*derivative+2.*(goal-base[:2]);cap=.22
    self.phase='timed_body_approach_with_carried_FL'
    world=(quat_apply(self.core.base_quat,torch.tensor([[.24,.15,-.15]],dtype=torch.float32,device=self.core.device))+self.core.robot.position)[0].cpu().numpy()
    native=quat_apply_inverse(yawframe,torch.tensor(world[None],dtype=torch.float32,device=self.core.device)-origin[None])[0].cpu().tolist();values[3:6]=native
    self.sent_world=world.astype(float);self.expected_previous_native=np.asarray(native,np.float32);diag['world_target']=world.tolist();diag['unprojected_world_target']=world.tolist()
   else:
    goal=self.timed_stop_goal;wanted=1.2*(goal-base[:2]);cap=.035
   norm=float(np.linalg.norm(wanted))
   if norm>cap:wanted*=cap/norm
   delta=wanted-self.timed_velocity;norm=float(np.linalg.norm(delta))
   if norm>.30*dt:delta*=.30*dt/norm
   self.timed_velocity+=delta;self.velocity=self.timed_velocity.copy();self.base_goal=goal.copy()
   native_velocity=quat_apply_inverse(yawframe,torch.tensor([[*self.timed_velocity,0]],dtype=torch.float32,device=self.core.device))[0].cpu().tolist();values[:2]=native_velocity[:2]
   diag.update(phase=self.phase,base_goal_xy=goal.tolist(),commanded_world_base_velocity=[*self.timed_velocity.tolist(),values[2]],timed_body_stop_and_extension_s=4.,body_stop_goal_xy=self.timed_stop_goal.tolist())
  assert values[6:9]==[0.,0.,0.]
  return values,diag
