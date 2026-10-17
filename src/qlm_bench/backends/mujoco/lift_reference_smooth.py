"""Review-stage Lift composition: original expert plus bounded native9 geometry.

No controller internals, joint gains/history, physical object states or task
predicates are written. Original RAMBO IK/FK is used read-only for target geometry.
"""
import copy

import numpy as np

from .expert_adapter import ExpertAdapter
from .press_reference_smooth import retained_fk, limited_step


DEFAULT = {'recipe_id':'lift-body-lane-geometry-v1','working_lateral_m':.20,
    'joint_reference_rate_deg_s':[60.,90.,90.], 'base_acceleration_m_s2':.12,
    'body_standoff_m':None,'raise_seconds':None,'present_seconds':None,'lift_seconds':None}


class SmoothLiftExecutor:
    def __init__(self, config=None):
        self.config=copy.deepcopy(DEFAULT)
        if config:
            if set(config)-set(DEFAULT):raise ValueError('Unknown explicit Lift recipe parameter')
            self.config.update(copy.deepcopy(config))
        if not .16<=self.config['working_lateral_m']<=.24:
            raise ValueError('Bounded explicit FL working lane required')
        rates=np.asarray(self.config['joint_reference_rate_deg_s'])
        if rates.shape!=(3,) or not np.isfinite(rates).all() or np.any(rates<=0):
            raise ValueError('Three finite positive geometry reference rates required')

    def reset(self, runtime, scene):
        self.runtime=runtime;self.core=runtime.core
        self.expert=ExpertAdapter(runtime.physics,runtime.core,runtime.task)
        for field,parameter in [('body_standoff_m','body_standoff_m'),('raise_s','raise_seconds'),
                                ('present_s','present_seconds'),('lift_s','lift_seconds')]:
            value=self.config[parameter]
            if value is not None:
                if not np.isfinite(value) or value<=0:raise ValueError('Finite positive phase parameters required')
                self.expert.cfg.approved_profile['expert'][field]=value
        self.lateral_goal=float(runtime.task.geometric_center(0)[1])-self.config['working_lateral_m']
        self.joints=None;self.velocity=np.zeros(2);self.last_time=None
        self.lower=self.core.default_joint_pos_limits[0,[0,4,8],0].cpu().numpy()+.1
        self.upper=self.core.default_joint_pos_limits[0,[0,4,8],1].cpu().numpy()-.1

    def command(self):
        import torch
        from qlm_bench.controllers.rambo.math import quat_apply,quat_apply_inverse,quat_mul,quat_inv
        time=float(self.runtime.physics.ticks[0])*.002
        dt=.02 if self.last_time is None else time-self.last_time
        if not 0<dt<=.020001:raise ValueError('One recipe command per50Hz boundary required')
        self.last_time=time
        if hasattr(self.expert,'_lift_body_goal'):
            self.expert._lift_body_goal[1]=self.lateral_goal
        values,diagnostic=self.expert.command()
        # The original expert creates its Base goal at approach entry (zero speed).
        if hasattr(self.expert,'_lift_body_goal'):
            self.expert._lift_body_goal[1]=self.lateral_goal
        if diagnostic['phase']=='settle':
            diagnostic.update(recipe=self.config['recipe_id'])
            return values,diagnostic
        if self.joints is None:
            self.joints=self.core.joint_pos[0,[0,4,8]].cpu().numpy().astype(float)
        base=self.core.robot.position[0]
        world=np.asarray(diagnostic['world_target'],float)
        wanted_body=quat_apply_inverse(self.core.base_quat,
            torch.tensor(world[None],dtype=torch.float32,device=self.core.device)-base[None])[0]
        ideal=self.core.get_motor_angles_from_foot_positions_fl(wanted_body[None])[0].cpu().numpy()
        ideal=np.clip(ideal,self.lower,self.upper)
        self.joints=limited_step(self.joints,ideal,np.deg2rad(self.config['joint_reference_rate_deg_s']),dt)
        body=retained_fk(self.joints,self.core.hip_offset[0].cpu().numpy(),self.core.link_lengths.cpu().numpy())
        projected=quat_mul(self.core.base_quat,quat_inv(self.core.base_quat_rp))
        world=quat_apply(self.core.base_quat,
            torch.tensor(body[None],dtype=torch.float32,device=self.core.device))+base[None]
        origin=base.clone();origin[2]=0
        native=quat_apply_inverse(projected,world-origin[None])[0].cpu().tolist()
        wanted_velocity=np.asarray(diagnostic['commanded_world_base_velocity'])[:2]
        self.velocity=limited_step(self.velocity,wanted_velocity,self.config['base_acceleration_m_s2'],dt)
        velocity=quat_apply_inverse(projected,
            torch.tensor([[*self.velocity,0]],dtype=torch.float32,device=self.core.device))[0].cpu().tolist()
        result=[velocity[0],velocity[1],0.,*native,0.,0.,0.]
        diagnostic.update(recipe=self.config['recipe_id'],working_lateral_m=self.config['working_lateral_m'],
            unprojected_world_target=diagnostic['world_target'],world_target=world[0].cpu().tolist(),
            reference_body_point=body.tolist(),reference_geometric_joints_rad=self.joints.tolist(),
            commanded_world_base_velocity=[*self.velocity.tolist(),0.],
            trajectory_projection_scope='native9 target only, original expert phase/contact rules and RAMBO internals retained')
        return result,diagnostic
