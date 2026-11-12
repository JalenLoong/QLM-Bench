"""One user-requested staged sweep. High-level native9 only; unchanged RAMBO."""
from pathlib import Path
from collections import deque
import importlib.util,json
import numpy as np,torch,mujoco
from qlm_bench.backends.mujoco.press_reference_smooth import limited_step
from qlm_bench.controllers.rambo.math import quat_apply_inverse,quat_mul,quat_inv
A=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('retained_a06_high_level',A/'four_task_experts_v6.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class Sweep(old.Sweep):
 def configure(self):
  self.staged_ready=False;super().configure()
  self.fixed_base_y=float(self.scene['initial_state']['qpos'][1]);self.coord_anchor[1]=self.fixed_base_y
  self.fixed_case_center=self.workspace_center.copy();self.route='entry';self.route_start=None
  self.contact_window=deque(maxlen=5);self.body_samples=deque(maxlen=11);self.stable_contact_first=None;self.stable_contact_final=None
  self.first_block_start=None;self.first_progress=0.;self.first_endpoint=None;self.shift_start=None;self.shift_origin=None;self.shift_hold=None;self.shift_fraction=0.;self.shift_feedforward=0.;self.completed_shift=False;self.cross_guard=False;self.stage_log_second=-1
  self.staged_ready=True;self.update_reach_goal()
 def update_reach_goal(self):
  if not getattr(self,'staged_ready',False):return super().update_reach_goal()
  super().update_reach_goal();safe_cap=float(self.base_x_cap)
  t=float(self.runtime.physics.ticks[0])*.002
  x=float(self.base_goal[0]) if self.route=='entry' else self.config['coordinated_push_base_x_m']
  y=self.fixed_base_y;self.shift_feedforward=0.;self.shift_fraction=0.
  if self.shift_start is not None:
   u=float(np.clip((t-self.shift_start)/self.config['body_shift_seconds'],0,1));self.shift_fraction=u*u*(3-2*u)
   y=float(self.shift_origin[1]+self.direction[1]*self.config['body_shift_distance_m']*self.shift_fraction)
   if u<1:self.shift_feedforward=float(self.direction[1]*self.config['body_shift_distance_m']*6*u*(1-u)/self.config['body_shift_seconds'])
  self.base_goal=np.array([min(x,safe_cap),y]);self.workspace_center=self.fixed_case_center+np.array([0.,y-self.fixed_base_y])
 def enter(self,stage,t):
  self.route=stage;self.route_start=t;self.contact_window.clear()
 def state(self):
  m=self.runtime.physics.model;d=self.runtime.physics.data[0];gid=m.geom('sw_block').id;f=m.geom('FL').id
  p=d.geom_xpos[gid].copy();foot=d.geom_xpos[f].copy();R=d.geom_xmat[gid].reshape(3,3);half=m.geom_size[gid];radius=float(m.geom_size[f,0]);support=sum(abs(self.direction@R[:2,k])*half[k] for k in [0,1])
  side=p.copy();side[:2]-=self.direction*(support+radius-self.config['contact_overlap_m']);goal_x=float(np.mean(self.runtime.profile['goal_x']));side[0]+=float(np.clip(.15*(p[0]-goal_x),-.008,.008))+self.entry_x_bias;side[2]=self.config['contact_height_m']
  force=0.
  for i,c in enumerate(d.contact[:d.ncon]):
   if set(map(int,c.geom))!={gid,f}:continue
   wrench=np.zeros(6);mujoco.mj_contactForce(m,d,i,wrench);force+=max(0.,float(wrench[0]))
  actual_side=bool(np.dot(foot[:2]-p[:2],-self.direction)>.015 and abs(foot[2]-p[2])<.055)
  self.contact_window.append(bool(force>=self.config['stable_contact_normal_N'] and actual_side))
  stable=len(self.contact_window)==5 and sum(self.contact_window)>=3
  b=m.body('base').id;rotation=d.xmat[b].reshape(3,3);gap=float((foot-d.geom_xpos[m.geom('FR').id])@rotation[:,1])
  self.body_samples.append(d.xpos[b,:2].copy());stopped=False
  if len(self.body_samples)==11:
   pts=np.asarray(self.body_samples);vel=(pts[-5:].mean(0)-pts[:5].mean(0))/.12
   stopped=bool(np.linalg.norm(vel)<.08 and max(abs(pts.mean(0)-self.base_goal))<.04)
  self.current_contact_normal=force;self.current_side_contact=actual_side;self.current_stable_contact=stable;self.current_body_stopped=stopped;self.current_foot_gap=gap
  return p,foot,side,stable,stopped,gap
 def interaction(self,age,t,dt):
  if self.entry_stage!='sweep':return super().interaction(age,t,dt)
  if self.route=='entry':self.enter('acquire_first_side_contact',t)
  p,foot,side,stable,stopped,gap=self.state()
  if self.route=='acquire_first_side_contact':
   desired=side
   if stable and stopped:
    self.stable_contact_first=t;self.first_block_start=p.copy();self.first_endpoint=self.last_target.copy();self.first_endpoint[:2]+=self.direction*self.config['first_foot_stroke_m'];self.first_endpoint[2]=self.config['contact_height_m'];self.enter('first_small_stroke_body_held',t)
  elif self.route=='first_small_stroke_body_held':
   desired=self.first_endpoint.copy();self.first_progress=float((p[:2]-self.first_block_start[:2])@self.direction)
   if gap<self.config['foot_lateral_margin_m']:
    desired=self.last_target.copy();self.cross_guard=True
   if t-self.route_start>=self.config['first_stroke_seconds'] or self.cross_guard:
    if self.runtime.task.condition(0):self.enter('hold_first_goal_candidate',t);desired=self.last_target.copy()
    elif self.first_progress>=self.config['minimum_first_block_motion_m']:
     self.shift_start=t;self.shift_origin=self.core.robot.position[0,:2].cpu().numpy().astype(float);self.shift_hold=self.last_target.copy();self.enter('body_shift_right_foot_world_held',t);desired=self.shift_hold.copy()
    else:self.enter('hold_unconfirmed_first_stroke_no_body_shift',t);desired=self.last_target.copy()
  elif self.route=='body_shift_right_foot_world_held':
   desired=self.shift_hold.copy()
   if t-self.shift_start>=self.config['body_shift_seconds'] and stopped and abs(float(self.base_goal[1]-self.core.robot.position[0,1].cpu()))<.025:
    self.completed_shift=True;self.enter('reacquire_final_side_contact_body_held',t)
  elif self.route=='reacquire_final_side_contact_body_held':
   desired=side
   if stable and stopped:self.stable_contact_final=t;self.enter('final_sweep_body_held',t)
  elif self.route=='final_sweep_body_held':
   desired=side
   if gap<self.config['foot_lateral_margin_m']:desired=self.last_target.copy();self.cross_guard=True
  else:desired=self.last_target.copy()
  self.last_target=limited_step(self.last_target,desired,[.055,.025,.03],dt);self.phase=self.route
  return self.last_target
 def command(self):
  previous_velocity=self.velocity.copy();values,diag=super().command();t=float(self.runtime.physics.ticks[0])*.002
  if self.interaction_start is not None and self.phase not in ['settle','carry']:
   self.lateral_integral=0.;error=float(self.base_goal[1]-self.base_feedback[1]);moving=self.route=='body_shift_right_foot_world_held'
   cap=self.config['body_shift_speed_cap_m_s'] if moving else .02
   wanted=float(np.clip(1.2*error+self.shift_feedforward if moving else .8*error,-cap,cap));step=self.config.get('base_acceleration_m_s2',.12)*.02
   self.velocity[1]=previous_velocity[1]+float(np.clip(wanted-previous_velocity[1],-step,step))
   projected=quat_mul(self.core.base_quat,quat_inv(self.core.base_quat_rp));native=quat_apply_inverse(projected,torch.tensor([[*self.velocity,0.]],dtype=torch.float32,device=self.core.device))[0].cpu().tolist();values[:2]=native[:2];diag['commanded_world_base_velocity']=[*self.velocity.tolist(),values[2]]
  diag.update(body_hold_override_active=self.interaction_start is not None,original_entry_control_preserved=self.interaction_start is None,route_stage=self.route,route_stage_start_s=self.route_start,stable_first_contact_s=self.stable_contact_first,stable_final_contact_s=self.stable_contact_final,first_stroke_actual_block_motion_m=self.first_progress,body_shift_start_s=self.shift_start,body_shift_completed=self.completed_shift,actual_foot_side_contact=getattr(self,'current_side_contact',False),actual_foot_contact_normal_N=getattr(self,'current_contact_normal',0.),actual_contact_stable=getattr(self,'current_stable_contact',False),actual_body_stopped=getattr(self,'current_body_stopped',False),FL_minus_FR_body_lateral_m=getattr(self,'current_foot_gap',None),cross_guard_limited=self.cross_guard,staged_body_shift_only=True,body_goal_follows_actual_block_toward_goal=False,fixed_task_workspace_center_xy=self.fixed_case_center.tolist(),coordinated_base_goal=self.base_goal.tolist())
  sec=int(t)
  if sec!=self.stage_log_second:
   self.stage_log_second=sec;print(json.dumps(dict(staged_sweep_actual=True,t=t,route=self.route,base_goal=self.base_goal.tolist(),actual_base=self.core.robot.position[0].cpu().tolist(),foot_force_N=getattr(self,'current_contact_normal',0.),stable_contact=getattr(self,'current_stable_contact',False),first_block_motion_m=self.first_progress,shift_started_s=self.shift_start,shift_completed=self.completed_shift,foot_gap_m=getattr(self,'current_foot_gap',None))),flush=True)
  return values,diag
