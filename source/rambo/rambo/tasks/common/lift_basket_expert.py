"""Far-body, visible full-foot threading before lift; unchanged native9 controller."""
import numpy as np
from itertools import product
from .lift_basket_geometry import completely_through,ego_projection

def smooth(t):
    t=float(np.clip(t,0,1));return t*t*(3-2*t)

def command(env,time):
    import torch
    from isaaclab.utils.math import quat_apply_inverse,quat_mul,quat_inv
    p=env.cfg.approved_profile['expert'];base=env.base_pos_w[0].detach().cpu().numpy();g=env.geometry_world();center=np.asarray(g['center']);vx=vy=0.
    handle,axis,foot,fpoints=env.insertion_geometry();radius=env._foot_radius;hmin=handle.min(0);hmax=handle.max(0);hcenter=(hmin+hmax)/2
    clearance=float(np.min(fpoints@axis)-np.max(handle@axis));through=clearance>=p['through_margin_m']
    rear_extent=float(foot[0]-fpoints[:,0].min());front_extent=float(fpoints[:,0].max()-foot[0])
    root=np.r_[base,env.base_quat[0].detach().cpu().numpy()]
    foot_view=ego_projection(fpoints,root,p['ego_margin_px']);handle_view=ego_projection(handle,root,p['ego_margin_px'])
    handle_contact_view=ego_projection(handle[handle[:,2]>=hmax[2]-.03],root,p['ego_margin_px'])
    both_visible=foot_view['in_frustum'] and handle_contact_view['in_frustum']
    target=None;comp=np.zeros(2)
    if time<p['settle_s']:
        result=[0.,0.,0.,.1934,.142,.05,0.,0.,0.];phase='settle'
    else:
        if not hasattr(env,'_lift_phase'):
            env._lift_phase='approach';env._lift_phase_start=time
            env._lift_body_goal=np.array([center[0]-p['body_standoff_m'],center[1]-.142])
            env._lift_comp=np.zeros(2);env._lift_through_count=0;env._lift_near_seen=False;env._lift_raise_progress=0.
        phase=env._lift_phase;age=time-env._lift_phase_start
        if float(np.max(fpoints@axis))<float(np.min(handle@axis)):env._lift_near_seen=True
        body_error=env._lift_body_goal-base[:2]
        speed=p['approach_speed'] if phase=='approach' else p['body_hold_speed_limit']
        vx,vy=np.clip(p['body_hold_gain']*body_error,-speed,speed).tolist()
        if phase=='approach':
            vx*=smooth((time-p['settle_s'])/.5);vy*=smooth((time-p['settle_s'])/.5)
            target=np.array([base[0]+.1934,base[1]+.142,.05])
            if np.max(np.abs(body_error))<.015:
                env._lift_phase='raise_before_rim';env._lift_phase_start=time;env._lift_start_target=env.actual_fl_world()
        elif phase=='raise_before_rim':
            goal=np.array([env._lift_body_goal[0]+.24,hcenter[1],p['preinsert_z_m']])
            target=env._lift_start_target+(goal-env._lift_start_target)*smooth(age/p['raise_s'])
            if age>=p['raise_s'] and foot[2]>=.20:
                env._lift_phase='present_at_handle';env._lift_phase_start=time;env._lift_start_target=target.copy()
        elif phase=='present_at_handle':
            goal=np.array([hmin[0]-front_extent-.012,hcenter[1],p['preinsert_z_m']])
            target=env._lift_start_target+(goal-env._lift_start_target)*smooth(age/p['present_s'])
            if age>=p['present_s']:
                env._lift_phase='thread_handle';env._lift_phase_start=time;env._lift_start_target=target.copy()
        elif phase=='thread_handle':
            goal=np.array([hmax[0]+rear_extent+p['through_margin_m']+p['insert_extra_m'],hcenter[1],p['preinsert_z_m']])
            target=env._lift_start_target+(goal-env._lift_start_target)*smooth(age/p['insert_s'])
            aligned=abs(foot[1]-hcenter[1])<=.035 and .195<=foot[2]<=hmax[2]-.015
            env._lift_through_count=env._lift_through_count+1 if through and aligned and env._lift_near_seen else 0
            if age>=p['insert_s'] and env._lift_through_count>=3:
                env._lift_phase='lift';env._lift_phase_start=time;env._lift_start_target=target.copy()
        else:
            # Once fully threaded, keep horizontal target fixed rather than chasing a pushed basket.
            env._lift_raise_progress=min(1.,env._lift_raise_progress+.02/p['lift_s'])
            target=env._lift_start_target.copy();target[2]+=(p['lift_target_z_m']-target[2])*smooth(env._lift_raise_progress)
        if phase in ('present_at_handle','thread_handle','lift'):
            error=target[:2]-env.actual_fl_world()[:2]
            env._lift_comp=np.clip(env._lift_comp+.02*p['tracking_gain']*error,-p['tracking_limit_m'],p['tracking_limit_m']);comp=env._lift_comp.copy();target[:2]+=comp
        target[0]=min(target[0],base[0]+p['max_foot_forward_m'])
        projected=quat_mul(env.base_quat,quat_inv(env.base_quat_rp));origin=env.base_pos_w[0].clone();origin[2]=0
        local=quat_apply_inverse(projected,torch.tensor(target[None],device=env.device,dtype=torch.float32)-origin[None])[0]
        velocity=quat_apply_inverse(projected,torch.tensor([[vx,vy,0.]],device=env.device,dtype=torch.float32))[0]
        result=[float(velocity[0]),float(velocity[1]),0.,*local.cpu().tolist(),0.,0.,0.]
    diagnostic=dict(phase=phase,world_target=None if target is None else target.tolist(),commanded_world_base_velocity=[vx,vy,0.],actual_fl_eef_world=env.actual_fl_world().tolist(),physical_foot_center=foot.tolist(),physical_foot_vertices_world=fpoints.tolist(),handle_axis_world=axis.tolist(),handle_far_side_projection_m=float(np.max(handle@axis)),physical_foot_envelope_radius_m=radius,handle_bounds_world=[hmin.tolist(),hmax.tolist()],foot_rear_past_handle_far_side_m=clearance,completely_through=through,ego_foot=foot_view,ego_handle=handle_view,ego_handle_contact_region=handle_contact_view,both_in_ego_frustum=both_visible,visibility_scope="entire physical foot and upper handle contact arc; full handle projection retained separately",through_count=getattr(env,'_lift_through_count',0),body_hold_goal=getattr(env,'_lift_body_goal',np.array([np.nan,np.nan])).tolist() if hasattr(env,'_lift_body_goal') else None,contact='unknown_diagnostic_only')
    env._expert_diagnostics=diagnostic
    return result,diagnostic
