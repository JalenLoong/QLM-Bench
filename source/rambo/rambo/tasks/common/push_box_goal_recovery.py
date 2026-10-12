"""Actual bounded +/-Y goal overflow, brake, side placement and inward push.

All perturbations and corrections are native9 commands. No object pose, goal,
physics, controller, external force or success-predicate writes occur here.
"""
from __future__ import annotations
import numpy as np
from .push_box_scaleup_motion import smooth


def bounds(geometry,profile,side):
    pts=np.asarray(geometry['footprint_xy']);lo=pts.min(0);hi=pts.max(0)
    gx,gy=profile['goal_x'],profile['goal_y']
    excess=float(hi[1]-gy[1] if side>0 else gy[0]-lo[1])
    overlap=max(0.,min(hi[1],gy[1])-max(lo[1],gy[0]))/float(hi[1]-lo[1])
    ready=bool(lo[0]>=gx[0]+.002 and hi[0]<=gx[1]-.005 and .005<=excess<=.07 and overlap>=.78)
    return lo,hi,excess,float(overlap),ready


def reference(state,time,*,geometry,profile,base,actual,actual_velocity,target,vx):
    cfg=profile['scaleup_goal_recovery'];side=int(cfg['side']);base=np.asarray(base,dtype=float)
    actual=np.asarray(actual,dtype=float);target=np.asarray(target,dtype=float).copy()
    actual_velocity=np.asarray(actual_velocity,dtype=float)
    lo,hi,excess,overlap,ready=bounds(geometry,profile,side);center=np.asarray(geometry['center'])
    progress=float(center[0]-profile['initial_center_x_world']);vy=0.;phase=None
    state.setdefault('side',side)
    if 'deviation_start' not in state and progress>=cfg.get('deviation_start_progress_m',.12):
        state.update(deviation_start=time,progress_before=progress)
    if 'deviation_start' not in state:return target,vx,vy,phase,None
    if 'repair_start' not in state:
        if ready:
            state.update(repair_start=time,base_start=base.tolist(),foot_start=state.get('last_target',target).tolist(),
                vx_start=float(vx),trigger_excess_m=excess,trigger_overlap=overlap,trigger_footprint=geometry['footprint_xy'],
                brake_ticks=0,braked=False,body_shift_signed_m=0.,inward_stroke=False,cycle=-1)
            state['actual_forward_velocity_before_m_s']=float(actual_velocity[0])
        else:
            age=time-state['deviation_start'];u=smooth(age/.6)
            if cfg.get('configuration')=='near_goal_side':
                # A fixed, visible near-edge goal creates a realistic small
                # missed boundary during an otherwise normal forward push.
                # This goal is defined before reset and never moves afterward.
                target[1]-=side*cfg.get('contact_offset_m',.02)*u
                phase='goal_near_edge_push';state['last_target']=target.copy()
                return target,vx,0.,phase,{'side':side,'progress_before_m':state['progress_before'],
                    'current_overflow_m':excess,'triggered':False}
            if excess>=cfg.get('deviation_excess_target_m',.025) and 'hold_y' not in state:
                state.update(hold_y=float(state.get('last_target',target)[1]),hold_start=time)
            if 'hold_y' in state:
                target[1]=state['hold_y'];vy=float(np.clip(1.2*(center[1]-.142-base[1]),-.04,.04))
                vx=min(vx,.08);phase='goal_deviation_forward_hold'
            else:
                # Off-centre forward contact rotates/translates the box toward
                # the opposite Y side. Keep the body aligned with the actual
                # box instead of strafing away until the FL loses its reach.
                target[1]-=side*.05*u
                vy=float(np.clip(1.2*(center[1]-.142-base[1]),-.04,.04))*u
                vx=min(vx,.08)
                # Keep the rear edge outside X until actual lateral overflow
                # appears, so unchanged task success cannot precede Recovery.
                if lo[0]>=profile['goal_x'][0]-.05:vx=0.
                phase='goal_deviation_diagonal_push'
            state['last_target']=target.copy()
            return target,vx,vy,phase,{'side':side,'progress_before_m':state['progress_before'],
                'current_overflow_m':excess,'triggered':False}
    age=time-state['repair_start'];start=np.asarray(state['foot_start']);base_start=np.asarray(state['base_start'])
    state['body_shift_signed_m']=max(state['body_shift_signed_m'],float(side*(base[1]-base_start[1])))
    if age>=.35 and abs(float(actual_velocity[0]))<=.03:state['brake_ticks']+=1
    else:state['brake_ticks']=0
    state['braked']=state['braked'] or state['brake_ticks']>=3
    if age<.4:
        u=smooth(age/.4);target=start+np.array([-.035*u,0.,.045*u]);vx=state['vx_start']*(1-u);phase='goal_recovery_brake'
    elif 'side_ready' not in state:
        surface=hi[1] if side>0 else lo[1];side_y=float(surface+side*.03)
        desired_base_y=side_y-.142
        shift_age=age-.4;u=smooth(shift_age/3.2)
        raised=start+np.array([-.035,0.,.045])
        end=np.array([min(center[0],base[0]+.40),side_y,min(center[2]+.06,.26)])
        target=raised*(1-u)+end*u;vx=0.;vy=float(np.clip(1.2*(desired_base_y-base[1]),-.06,.06))*smooth(shift_age/.4)
        phase='goal_recovery_sidestep'
        if shift_age>=2.8 and (abs(desired_base_y-base[1])<=.025 or shift_age>=4.5):
            state.update(side_ready=time,cycle=-1)
    else:
        age=time-state['side_ready'];cycle=min(int(age/2.2),2);local=age-cycle*2.2
        if state['cycle']!=cycle:
            surface=hi[1] if side>0 else lo[1]
            state.update(cycle=cycle,stroke_start=actual.tolist(),side_target=[min(center[0],base[0]+.42),float(surface+side*.025),max(.06,float(center[2]))],
                inset_m=float(np.clip(max(0.,excess)+.02,.02,.085)))
        point=np.asarray(state['side_target']);entry=np.asarray(state['stroke_start']);vx=0.;vy=0.
        if local<.5:
            u=smooth(local/.5);target=entry*(1-u)+(point+np.array([0.,0.,.045]))*u;phase='goal_recovery_reposition'
        elif local<.9:
            u=smooth((local-.5)/.4);target=point+np.array([0.,0.,.045*(1-u)]);phase='goal_recovery_lower'
        else:
            u=smooth((local-.9)/1.3);end=point.copy();end[1]-=side*(state['inset_m']+.025)
            target=point*(1-u)+end*u;phase='goal_recovery_inward_push';state['inward_stroke']=True
    state['last_target']=target.copy()
    evidence={'side':side,'triggered':True,'trigger_overflow_m':state['trigger_excess_m'],
        'trigger_overlap':state['trigger_overlap'],'trigger_footprint':state['trigger_footprint'],
        'progress_before_m':state['progress_before'],'braked_actual_forward_velocity':state['braked'],
        'actual_forward_velocity_before_m_s':state['actual_forward_velocity_before_m_s'],
        'actual_forward_velocity_m_s':float(actual_velocity[0]),'body_shift_signed_m':state['body_shift_signed_m'],
        'inward_stroke':state['inward_stroke'],'current_overflow_m':excess}
    return target,float(vx),float(vy),phase,evidence


def command(env,time,normal_request,diagnostic):
    import torch
    from isaaclab.utils.math import quat_apply_inverse,quat_mul,quat_inv
    state=getattr(env,'_scaleup_goal_recovery',None)
    if state is None:state={};env._scaleup_goal_recovery=state
    target,vx,vy,phase,evidence=reference(state,time,geometry=env.geometry_world(),profile=env.cfg.approved_profile,
        base=env.base_pos_w[0].cpu().numpy(),actual=env.actual_fl_world(),actual_velocity=env.base_velocity_world(),
        target=diagnostic['commanded_contact_point'],vx=diagnostic['commanded_world_base_velocity'][0])
    if phase is None:return normal_request,diagnostic
    projected=quat_mul(env.base_quat,quat_inv(env.base_quat_rp));origin=env.base_pos_w[0].clone();origin[2]=0
    local=quat_apply_inverse(projected,torch.as_tensor(target,device=env.device,dtype=torch.float32)[None]-origin[None])[0]
    velocity=quat_apply_inverse(projected,torch.tensor([[vx,vy,0.]],device=env.device,dtype=torch.float32))[0]
    request=[float(velocity[0]),float(velocity[1]),0.,*local.cpu().tolist(),0.,0.,0.]
    diagnostic.update(phase=phase,commanded_contact_point=target.tolist(),commanded_world_base_velocity=[vx,vy,0.],goal_recovery_evidence=evidence)
    env._expert_diagnostics=diagnostic
    return request,diagnostic
