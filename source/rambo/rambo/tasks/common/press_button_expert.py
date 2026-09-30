"""Scripted native9 position/velocity references; never moves the button directly."""
import numpy as np

def smooth(x):
    x=float(np.clip(x,0.,1.));return x*x*(3.-2.*x)

def command(env,time):
    import torch
    from isaaclab.utils.math import quat_mul,quat_inv,quat_apply_inverse
    profile=env.cfg.approved_profile;p=profile['expert'];base=env.base_pos_w[0].cpu().numpy();actual=env.actual_fl_world();face=np.asarray(profile['button_rest_front_xyz']);vx=0.;vy=0.;yaw_rate=0.
    if time<p['settle_s']:
        result=[0.,0.,0.,.1934,.142,.05,0.,0.,0.];target=None;phase='settle'
    else:
        elapsed=time-p['settle_s'];u=smooth(elapsed/p['raise_s'])
        q=env.base_quat[0].cpu().numpy();x,y,z,w=q;yaw=float(np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z)))
        vy=float(np.clip(p['base_y_gain']*(face[1]-.142-base[1]),-p['base_y_speed_limit'],p['base_y_speed_limit']))*u
        yaw_rate=float(np.clip(-p['base_yaw_gain']*yaw,-.15,.15))*u
        aligned=abs(actual[1]-face[1])<=.035 and abs(actual[2]-face[2])<=.04
        if not hasattr(env,'_press_expert'):env._press_expert={'phase':'raise'}
        st=env._press_expert
        if elapsed>=p['raise_s'] and st['phase']=='raise':st['phase']='approach';st['start']=time
        if st['phase']=='approach' and aligned and face[0]-actual[0]<=p['standoff_from_eef_m']:
            st.update(phase='press',start=time,foot_start=actual.copy(),base_stop_x=float(base[0]))
        phase=st['phase']
        target=np.array([base[0]+.1934+u*(p['approach_foot_x']-.1934),base[1]+.142+u*(face[1]-(base[1]+.142)),.05+u*(face[2]+p['height_tracking_offset_m']-.05)])
        if phase=='approach':vx=p['approach_speed']*smooth((time-st['start'])/.5) if aligned else 0.
        if phase=='press':
            v=smooth((time-st['start'])/p['press_seconds']);end=face.copy();end[0]+=p['press_center_beyond_face_m'];end[2]+=p['height_tracking_offset_m']
            target=st['foot_start']*(1-v)+end*v
            vx=p['approach_speed']*(1-smooth((time-st['start'])/p['brake_s']))+float(np.clip(1.2*(st['base_stop_x']-base[0]),-.04,.04))
        if phase in ('approach','press'):
            integral=getattr(env,'_press_integral',np.zeros(3));integral=np.clip(integral+.02*p['tracking_gain']*(target-actual),-p['tracking_limit_m'],p['tracking_limit_m']);env._press_integral=integral
            target+=integral
        if phase=='press' and 'displacement_hold_target_m' in p:
            displacement=float(env.displacement[0])
            if displacement>=p['displacement_servo_entry_m'] and 'displacement_reference_x' not in st:
                st['displacement_reference_x']=getattr(env,'_expert_diagnostics',{}).get('commanded_world_fl_position',target.tolist())[0]
            if 'displacement_reference_x' in st:
                error=p['displacement_hold_target_m']-displacement
                st['displacement_reference_x']+=.02*float(np.clip(2.*error,-.012,.004))
                target[0]=st['displacement_reference_x']
        target[0]=min(target[0],base[0]+p['max_foot_x'])
        projected=quat_mul(env.base_quat,quat_inv(env.base_quat_rp));origin=env.base_pos_w[0].clone();origin[2]=0
        point=torch.as_tensor(target,device=env.device,dtype=torch.float32)[None]-origin[None];local=quat_apply_inverse(projected,point)[0]
        velocity=quat_apply_inverse(projected,torch.tensor([[vx,vy,0.]],device=env.device,dtype=torch.float32))[0]
        result=[float(velocity[0]),float(velocity[1]),yaw_rate,*local.cpu().tolist(),0.,0.,0.]
    diag=dict(phase=phase,commanded_world_fl_position=None if target is None else target.tolist(),actual_fl_eef_world=actual.tolist(),button_displacement_m=float(env.displacement[0]),commanded_world_base_velocity=[vx,vy,yaw_rate],source='scripted_expert_not_manual_teleoperation',contact='unknown_diagnostic_only')
    diag.update(motion=profile.get('motion','baseline'),base_world_position=base.tolist(),base_stop_reference_x=getattr(env,'_press_expert',{}).get('base_stop_x'),standoff_m=p['standoff_from_eef_m'],reference_extension_world_x=None if target is None else float(target[0]-base[0]),reference_x_saturated=False if target is None else bool(target[0]>=base[0]+p['max_foot_x']-1e-7))
    env._expert_diagnostics=diag;return result,diag
