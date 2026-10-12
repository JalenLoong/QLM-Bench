"""Continuous world-space approach/push references for new scale-up captures."""
from __future__ import annotations
import numpy as np


def smooth(value):
    u=float(np.clip(value,0.,1.));return u*u*(3.-2.*u)


def reference(state,time,*,base,neutral,ray,normal,actual,expert):
    base,neutral,ray,normal,actual=map(lambda p:np.asarray(p,dtype=float),(base,neutral,ray,normal,actual))
    settle=expert['settle_seconds'];duration=expert['normal_approach_seconds']
    if time<settle:
        target=neutral.copy();vx=0.;phase='settle'
    else:
        if 'stage' not in state:state.update(stage='base_approach')
        if state['stage']=='base_approach' and ray[0]-base[0]<=expert['face_distance_for_foot_approach']:
            state.update(stage='normal_approach',contact_start=time,
                contact_target=state.get('last_target',neutral).copy(),contact_velocity=state.get('last_vx',0.))
        if state['stage']=='normal_approach' and time-state['contact_start']>=duration:
            state.update(stage='straight_push',push_start=time,
                push_target=state['last_target'].copy(),push_start_local_x=float(state['last_target'][0]-base[0]))
        phase=state['stage']
        if phase=='base_approach':
            u=smooth((time-settle)/.8)
            target=neutral*(1-u)+np.array([base[0]+expert['approach_foot_x'],ray[1],ray[2]])*u
            vx=expert['align_base_speed']*u
        elif phase=='normal_approach':
            age=time-state['contact_start'];u=float(np.clip(age/duration,0.,1.));s=smooth(u)
            end=ray-normal*expert['penetration_m']
            # Start at the previous command, with its incoming world-X velocity.
            # No reset to a nominal standoff position at phase boundaries.
            target=state['contact_target']*(1-s)+end*s
            target[0]+=state['contact_velocity']*duration*u*(1-u)**2
            vx=state['contact_velocity']*(1-smooth(age/.25))
        else:
            u=smooth((time-state['push_start'])/expert.get('transition_s',.45))
            foot_x=state['push_start_local_x']*(1-u)+expert['push_foot_x']*u
            # Let the body catch up with the existing contact point; never
            # pull the foot13cm backwards to approach_foot_x before pushing.
            x=max(state['push_target'][0],base[0]+foot_x)
            gain=expert.get('lateral_tracking_gain',0.);limit=expert.get('lateral_tracking_limit_m',0.)
            state['lateral_comp']=float(np.clip(state.get('lateral_comp',0.)+.02*gain*(ray[1]-actual[1]),-limit,limit))
            target=np.array([x,ray[1]+state['lateral_comp'],ray[2]])
            vx=expert['push_base_speed']*u
    step=float(np.linalg.norm(target-state['last_target'])) if 'last_target' in state else 0.
    state.update(last_target=target.copy(),last_vx=float(vx))
    return target,float(vx),0.,phase,{'revision':'continuous-v2','world_target_step_m':step}


def command(env,time):
    import torch
    from isaaclab.utils.math import quat_apply,quat_apply_inverse,quat_mul,quat_inv
    from .push_box_geometry import forward_face_ray
    state=getattr(env,'_scaleup_motion',None)
    if state is None:state={};env._scaleup_motion=state
    base=env.base_pos_w[0].cpu().numpy();g=env.geometry_world()
    ray,normal=forward_face_ray(env._box_geometry,env.primary_pose_w[0].cpu().numpy())
    projected=quat_mul(env.base_quat,quat_inv(env.base_quat_rp));origin=env.base_pos_w[0].clone();origin[2]=0
    neutral=(quat_apply(projected,torch.tensor([[.1934,.142,.05]],device=env.device,dtype=torch.float32))[0]+origin).cpu().numpy()
    target,vx,vy,phase,continuity=reference(state,time,base=base,neutral=neutral,ray=ray,normal=normal,
        actual=env.actual_fl_world(),expert=env.cfg.approved_profile['expert'])
    local=quat_apply_inverse(projected,torch.as_tensor(target,device=env.device,dtype=torch.float32)[None]-origin[None])[0]
    velocity=quat_apply_inverse(projected,torch.tensor([[vx,vy,0.]],device=env.device,dtype=torch.float32))[0]
    request=[float(velocity[0]),float(velocity[1]),0.,*local.cpu().tolist(),0.,0.,0.]
    diag=dict(phase=phase,intended_face_center=g['face_center'],intended_face_normal=g['face_normal'],
        commanded_contact_point=target.tolist(),centerline_face_intersection=ray.tolist(),
        commanded_world_base_velocity=[vx,vy,0.],actual_fl_eef_world=env.actual_fl_world().tolist(),
        box_pose=env.primary_pose_w[0].cpu().tolist(),box_yaw_rad=g['yaw_rad'],contact_evidence='unknown_diagnostic_only',
        lateral_tracking_compensation_m=state.get('lateral_comp',0.),motion_continuity=continuity)
    env._expert_diagnostics=diag
    return request,diag
