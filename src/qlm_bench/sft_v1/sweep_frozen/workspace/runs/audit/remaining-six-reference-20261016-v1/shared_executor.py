"""High-level native9 smoothing only; same retained IK/FK and controller semantics."""
import copy,numpy as np,torch
from qlm_bench.backends.mujoco.press_reference_smooth import SmoothPressExecutor,blend,limited_step,retained_fk
from qlm_bench.controllers.rambo.math import quat_apply_inverse,quat_mul,quat_inv

class SmoothReference(SmoothPressExecutor):
 def __init__(self,config=None):
  self.config=dict(recipe_id='remaining-six-reference-development-v1',settle_seconds=2.1,carry_seconds=1.2,carry_body_xyz_m=[.16,.18,-.16],base_speed_m_s=.07,base_acceleration_m_s2=.12,base_tolerance_m=.015,base_stable_seconds=.4,base_feedback_smoothing_s=.2,joint_reference_rate_deg_s=[60.,90.,90.],lateral_integral_gain=.2,lateral_integral_limit_m_s=.03)
  self.config.update(copy.deepcopy(config or {}))
 def reset(self,runtime,scene):
  self.runtime=runtime;self.core=runtime.core;self.scene=scene;self.phase='settle';self.phase_start=0.;self.time=None;self.velocity=np.zeros(2);self.base_feedback=None;self.lateral_integral=0.;self.stable_since=None;self.filtered_joints=None;self.base_goal=np.zeros(2);self.interaction_start=None
  self.joint_lower=self.core.default_joint_pos_limits[0,[0,4,8],0].cpu().numpy()+.1;self.joint_upper=self.core.default_joint_pos_limits[0,[0,4,8],1].cpu().numpy()-.1
  self.configure()
 def configure(self):raise NotImplementedError('Set self.base_goal from physical geometry')
 def interaction(self,age,t,dt):raise NotImplementedError('Return world FL endpoint; never mutate simulator/controller')
 def command(self):
  t=float(self.runtime.physics.ticks[0])*.002;dt=.02 if self.time is None else t-self.time
  if not 0<dt<=.020001:raise ValueError('Exactly one recipe decision per50Hz boundary')
  self.time=t;base=self.core.robot.position[0].cpu().numpy();actual=self.actual_world_point()
  if self.base_feedback is None:self.base_feedback=base[:2].copy()
  else:self.base_feedback+=(1-np.exp(-dt/self.config['base_feedback_smoothing_s']))*(base[:2]-self.base_feedback)
  if self.phase=='settle' and t>=self.config['settle_seconds']:
   self.filtered_joints=self.core.joint_pos[0,[0,4,8]].cpu().numpy().astype(float);self.output_body=self.core.ee_pos_b[0,0].cpu().numpy();self.carry_start=self.output_body.copy();self.transition('carry',t)
  if self.phase=='settle':return [0.,0.,0.,.1934,.142,.05,0.,0.,0.],{'phase':'settle','recipe':self.config['recipe_id'],'actual_fl_eef_world':actual.tolist(),'world_target':actual.tolist(),'commanded_world_base_velocity':[0.,0.,0.]}
  age=t-self.phase_start;wanted_world=None
  if self.phase=='carry':
   wanted_body=self.carry_start+(np.asarray(self.config['carry_body_xyz_m'])-self.carry_start)*blend(age/self.config['carry_seconds'])
   if age>=self.config['carry_seconds']:self.transition('approach_base',t)
  elif self.phase in ('approach_base','stabilize_base'):
   wanted_body=np.asarray(self.config['carry_body_xyz_m']);error=self.base_goal-self.base_feedback
   if self.phase=='approach_base' and max(abs(error))<=self.config['base_tolerance_m']:self.transition('stabilize_base',t)
   elif self.phase=='stabilize_base':
    if max(abs(error))<=.025:
     if self.stable_since is None:self.stable_since=t
     if t-self.stable_since>=self.config['base_stable_seconds']:self.transition('interaction',t);self.interaction_start=t;self.interaction_world_start=self.phase_world_start.copy()
    else:self.stable_since=None
  else:
   wanted_world=np.asarray(self.interaction(t-self.interaction_start,t,dt),float);wanted_body=quat_apply_inverse(self.core.base_quat,torch.tensor((wanted_world-base)[None],dtype=torch.float32,device=self.core.device))[0].cpu().numpy()
  error=self.base_goal-self.base_feedback;self.lateral_integral=float(np.clip(self.lateral_integral+dt*self.config['lateral_integral_gain']*error[1],-self.config['lateral_integral_limit_m_s'],self.config['lateral_integral_limit_m_s']));speed=self.config['base_speed_m_s'] if self.phase=='approach_base' else .035
  wanted_velocity=np.clip(.8*error,-speed,speed);wanted_velocity[1]=np.clip(wanted_velocity[1]+self.lateral_integral,-speed,speed)
  if self.phase=='carry':wanted_velocity[:]=0.
  ideal=self.core.get_motor_angles_from_foot_positions_fl(torch.tensor(wanted_body[None],dtype=torch.float32,device=self.core.device))[0].cpu().numpy();ideal=np.clip(ideal,self.joint_lower,self.joint_upper);self.filtered_joints=limited_step(self.filtered_joints,ideal,np.deg2rad(self.config['joint_reference_rate_deg_s']),dt);self.output_body=retained_fk(self.filtered_joints,self.core.hip_offset[0].cpu().numpy(),self.core.link_lengths.cpu().numpy());world=self.world_body_point(self.output_body);self.velocity=limited_step(self.velocity,wanted_velocity,self.config['base_acceleration_m_s2'],dt)
  projected=quat_mul(self.core.base_quat,quat_inv(self.core.base_quat_rp));origin=self.core.robot.position[0].clone();origin[2]=0.;native=quat_apply_inverse(projected,torch.tensor(world[None],dtype=torch.float32,device=self.core.device)-origin[None])[0].cpu().tolist();velocity=quat_apply_inverse(projected,torch.tensor([[*self.velocity,0.]],dtype=torch.float32,device=self.core.device))[0].cpu().tolist()
  return [*velocity[:2],0.,*native,0.,0.,0.],{'phase':self.phase,'recipe':self.config['recipe_id'],'world_target':world.tolist(),'unprojected_world_target':None if wanted_world is None else wanted_world.tolist(),'actual_fl_eef_world':actual.tolist(),'base_goal_xy':self.base_goal.tolist(),'base_world_position':base.tolist(),'reference_geometric_joints_rad':self.filtered_joints.tolist(),'commanded_world_base_velocity':[*self.velocity.tolist(),0.],'task_progress':self.runtime.task.progress(0)}
