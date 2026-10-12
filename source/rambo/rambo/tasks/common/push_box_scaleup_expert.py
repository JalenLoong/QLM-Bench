"""Measured contact separation/recontact through native9 only; no object writes."""
from __future__ import annotations
import numpy as np
from .push_box_expert import command as normal_command
from .push_box_geometry import forward_face_ray


def command(env, time):
    profile = env.cfg.approved_profile
    if profile.get('large_goal_recovery'):
        from .push_box_large_recovery import command as large_command
        return large_command(env,time)
    if profile.get('scaleup_motion_revision')=='continuous-v2':
        from .push_box_scaleup_motion import command as continuous_command
        request,diagnostic=continuous_command(env,time)
    else:request,diagnostic=normal_command(env,time)
    if profile.get('scaleup_goal_recovery'):
        from .push_box_goal_recovery import command as goal_command
        return goal_command(env,time,request,diagnostic)
    if not profile.get('scaleup_recovery', False):
        return request, diagnostic
    g = env.geometry_world(); actual = np.asarray(env.actual_fl_world()); base = env.base_pos_w[0].cpu().numpy()
    state = getattr(env, '_scaleup_recovery', None)
    progress = g['center'][0] - profile['initial_center_x_world']
    face, _ = forward_face_ray(env._box_geometry, env.primary_pose_w[0].cpu().numpy())
    if state is None and progress >= profile.get('recovery_progress_m', .12):
        state = dict(start=time, foot_start=actual.copy(), progress_before=progress,
                     face_before=face.copy(), max_separation=0., corrected=False)
        env._scaleup_recovery = state
    if state is None:
        return request, diagnostic
    elapsed = time-state['start']; separation=float(face[0]-actual[0])
    state['max_separation']=max(state['max_separation'],separation)
    phase=None; target=None; vx=0.
    if elapsed < .5:
        u=float(np.clip(elapsed/.5,0,1));u=u*u*(3-2*u)
        target=state['foot_start']+np.array([-.09*u,0.,.055*u]);phase='recovery_contact_withdraw'
    elif elapsed < 1.0:
        target=state['foot_start']+np.array([-.09,0.,.055]);phase='recovery_contact_gap'
    elif elapsed < 2.2:
        u=float(np.clip((elapsed-1.)/1.2,0,1));u=u*u*(3-2*u)
        begin=state['foot_start']+np.array([-.09,0.,.055])
        end=face.copy();end[0]+=.012
        target=begin*(1-u)+end*u;target[0]=min(target[0],base[0]+.40)
        phase='recovery_corrective_recontact';state['corrected']=True
    if target is not None:
        import torch
        from isaaclab.utils.math import quat_apply_inverse,quat_mul,quat_inv
        projected=quat_mul(env.base_quat,quat_inv(env.base_quat_rp));origin=env.base_pos_w[0].clone();origin[2]=0
        local=quat_apply_inverse(projected,torch.as_tensor(target,device=env.device,dtype=torch.float32)[None]-origin[None])[0]
        request=[0.,0.,0.,*local.cpu().tolist(),0.,0.,0.]
        diagnostic.update(phase=phase, commanded_contact_point=target.tolist(), commanded_world_base_velocity=[0.,0.,0.])
    diagnostic['recovery_evidence']={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in state.items()}
    diagnostic['recovery_evidence'].update(current_separation_m=separation,progress_m=progress)
    env._expert_diagnostics=diagnostic
    return request,diagnostic
