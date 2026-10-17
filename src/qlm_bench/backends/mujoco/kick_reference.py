"""High-level native9 impulse/retract recipe; retained RAMBO remains untouched."""
import copy
import numpy as np
from .press_reference_smooth import SmoothPressExecutor,blend,limited_step,retained_fk

DEFAULT={'recipe_id':'kick-impulse-retract-v1','settle_seconds':2.1,'carry_seconds':1.2,
    'carry_body_xyz_m':[.23,.18,-.16], 'working_lateral_m':.18,'working_forward_m':.34,
    'base_speed_m_s':.08,'base_acceleration_m_s2':.15,'base_feedback_smoothing_s':.2,
    'base_tolerance_m':.012,'base_stable_seconds':.5,'present_seconds':1.6,'ready_seconds':.5,
    'strike_seconds':.4,'retract_seconds':.8,'precontact_gap_m':.02,'follow_through_m':.10,
    'contact_height_m':.10,'joint_reference_rate_deg_s':[90.,120.,120.],
    'lateral_integral_gain':.2,'lateral_integral_limit_m_s':.03}


class KickExecutor(SmoothPressExecutor):
    def __init__(self,config=None):
        self.config=copy.deepcopy(DEFAULT)
        if config:
            if set(config)-set(DEFAULT):raise ValueError('Unknown Kick recipe parameter')
            self.config.update(copy.deepcopy(config))
        if not np.isfinite([v for v in self.config.values() if isinstance(v,(int,float))]).all():raise ValueError('Finite recipe required')

    def reset(self,runtime,scene):
        self.runtime=runtime;self.core=runtime.core;self.phase='settle';self.phase_start=0.
        self.time=None;self.velocity=np.zeros(2);self.base_feedback=None;self.lateral_integral=0.;self.stable_since=None;self.filtered_joints=None
        self.ball_initial=np.asarray(runtime.task.geometric_center(0)).copy()
        center=np.asarray(runtime.profile['goal_geometry']['front_center_xyz_m']);direction=center[:2]-self.ball_initial[:2];self.direction=direction/np.linalg.norm(direction)
        self.side=np.array([-self.direction[1],self.direction[0]])
        self.base_goal=self.ball_initial[:2]-self.direction*self.config['working_forward_m']-self.side*self.config['working_lateral_m']
        radius=runtime.profile['ball_radius_m'];foot_radius=float(runtime.physics.model.geom('FL').size[0])
        self.ready=self.ball_initial.copy();self.ready[:2]-=self.direction*(radius+foot_radius+self.config['precontact_gap_m']);self.ready[2]=self.config['contact_height_m']
        self.strike=self.ball_initial.copy();self.strike[:2]+=self.direction*self.config['follow_through_m'];self.strike[2]=self.config['contact_height_m']
        self.joint_lower=self.core.default_joint_pos_limits[0,[0,4,8],0].cpu().numpy()+.1
        self.joint_upper=self.core.default_joint_pos_limits[0,[0,4,8],1].cpu().numpy()-.1

    def command(self):
        import torch
        from qlm_bench.controllers.rambo.math import quat_apply_inverse,quat_mul,quat_inv
        t=float(self.runtime.physics.ticks[0])*.002;dt=.02 if self.time is None else t-self.time
        if not 0<dt<=.020001:raise ValueError('One Kick reference per50Hz boundary')
        self.time=t;base=self.core.robot.position[0].cpu().numpy();actual=self.actual_world_point()
        if self.base_feedback is None:self.base_feedback=base[:2].copy()
        else:self.base_feedback+=(1-np.exp(-dt/self.config['base_feedback_smoothing_s']))*(base[:2]-self.base_feedback)
        if self.phase=='settle' and t>=self.config['settle_seconds']:
            self.filtered_joints=self.core.joint_pos[0,[0,4,8]].cpu().numpy().astype(float)
            self.output_body=self.core.ee_pos_b[0,0].cpu().numpy();self.carry_start=self.output_body.copy();self.transition('carry',t)
        if self.phase=='settle':return [0.,0.,0.,.1934,.142,.05,0.,0.,0.],{'phase':'settle','recipe':self.config['recipe_id'],'actual_fl_eef_world':actual.tolist(),'world_target':actual.tolist(),'commanded_world_base_velocity':[0.,0.,0.]}
        age=t-self.phase_start;wanted_velocity=np.zeros(2);wanted_world=None
        error=self.base_goal-self.base_feedback
        self.lateral_integral=float(np.clip(self.lateral_integral+dt*self.config['lateral_integral_gain']*error[1],-self.config['lateral_integral_limit_m_s'],self.config['lateral_integral_limit_m_s']))
        if self.phase=='carry':
            wanted_body=self.carry_start+(np.asarray(self.config['carry_body_xyz_m'])-self.carry_start)*blend(age/self.config['carry_seconds'])
            if age>=self.config['carry_seconds']:self.transition('approach_base',t)
        elif self.phase in ('approach_base','stabilize_base'):
            wanted_body=np.asarray(self.config['carry_body_xyz_m']);speed=self.config['base_speed_m_s'] if self.phase=='approach_base' else .02
            wanted_velocity=np.clip(error,-speed,speed);wanted_velocity[1]=np.clip(wanted_velocity[1]+self.lateral_integral,-.08,.08)
            if self.phase=='approach_base' and np.max(abs(error))<self.config['base_tolerance_m']:self.transition('stabilize_base',t)
            elif self.phase=='stabilize_base':
                if np.max(abs(error))<.02:
                    if self.stable_since is None:self.stable_since=t
                    if t-self.stable_since>=self.config['base_stable_seconds']:self.transition('present',t)
                else:self.stable_since=None
        else:
            wanted_velocity=np.clip(.7*error,-.02,.02);wanted_velocity[1]=np.clip(wanted_velocity[1]+self.lateral_integral,-.04,.04)
            if self.phase=='present':
                wanted_world=self.phase_world_start+(self.ready-self.phase_world_start)*blend(age/self.config['present_seconds'])
                if age>=self.config['present_seconds']:self.transition('ready',t)
            elif self.phase=='ready':
                wanted_world=self.ready.copy()
                if age>=self.config['ready_seconds']:self.transition('strike',t)
            elif self.phase=='strike':
                wanted_world=self.phase_world_start+(self.strike-self.phase_world_start)*blend(age/self.config['strike_seconds'])
                if age>=self.config['strike_seconds']:self.transition('retract',t)
            elif self.phase=='retract':
                end=self.world_body_point(np.asarray(self.config['carry_body_xyz_m']))
                wanted_world=self.phase_world_start+(end-self.phase_world_start)*blend(age/self.config['retract_seconds'])
                if age>=self.config['retract_seconds']:self.transition('observe',t)
            else:wanted_world=self.world_body_point(np.asarray(self.config['carry_body_xyz_m']))
            wanted_body=quat_apply_inverse(self.core.base_quat,torch.tensor((wanted_world-base)[None],dtype=torch.float32,device=self.core.device))[0].cpu().numpy()
        ideal=self.core.get_motor_angles_from_foot_positions_fl(torch.tensor(wanted_body[None],dtype=torch.float32,device=self.core.device))[0].cpu().numpy()
        ideal=np.clip(ideal,self.joint_lower,self.joint_upper)
        self.filtered_joints=limited_step(self.filtered_joints,ideal,np.deg2rad(self.config['joint_reference_rate_deg_s']),dt)
        self.output_body=retained_fk(self.filtered_joints,self.core.hip_offset[0].cpu().numpy(),self.core.link_lengths.cpu().numpy())
        world=self.world_body_point(self.output_body)
        self.velocity=limited_step(self.velocity,wanted_velocity,self.config['base_acceleration_m_s2'],dt)
        projected=quat_mul(self.core.base_quat,quat_inv(self.core.base_quat_rp));origin=self.core.robot.position[0].clone();origin[2]=0.
        native=quat_apply_inverse(projected,torch.tensor(world[None],dtype=torch.float32,device=self.core.device)-origin[None])[0].cpu().tolist()
        velocity=quat_apply_inverse(projected,torch.tensor([[*self.velocity,0.]],dtype=torch.float32,device=self.core.device))[0].cpu().tolist()
        return [velocity[0],velocity[1],0.,*native,0.,0.,0.],{'phase':self.phase,'recipe':self.config['recipe_id'],'world_target':world.tolist(),'actual_fl_eef_world':actual.tolist(),'ball_initial':self.ball_initial.tolist(),'ball_measured':self.runtime.task.geometric_center(0).tolist(),'base_goal_xy':self.base_goal.tolist(),'base_world_position':base.tolist(),'reference_geometric_joints_rad':self.filtered_joints.tolist(),'commanded_world_base_velocity':[*self.velocity.tolist(),0.],'kick_direction_xy':self.direction.tolist(),'one_shot_strike_retract_no_ball_chasing':True}
