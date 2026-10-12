"""Reproduce major missed-goal pushing, back/left inspect, then push inward.

The reference uses recorded native9 actions as a local diagnostic prefix. It
does not run a WAM checkpoint or write object/robot poses during an episode.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
from .push_box_geometry import rotation_xyzw
from .push_box_scaleup_motion import smooth
from .lift_camera_rig import CAMERAS,camera_world_transform


def wrap(angle):return (angle+math.pi)%(2*math.pi)-math.pi


def relationship(geometry,profile):
    points=np.asarray(geometry['footprint_xy']);lo=points.min(0);hi=points.max(0)
    gx,gy=profile['goal_x'],profile['goal_y']
    x=max(0.,min(hi[0],gx[1])-max(lo[0],gx[0]))/(hi[0]-lo[0])
    y=max(0.,min(hi[1],gy[1])-max(lo[1],gy[0]))/(hi[1]-lo[1])
    return lo,hi,float(x),float(y)


def ray_side(geometry,pose,outward):
    pose=np.asarray(pose);R=rotation_xyzw(pose[3:]);d=np.asarray(outward,dtype=float);d=d/np.linalg.norm(d)
    local=R.T@d;half=(np.asarray(geometry['high'])-geometry['low'])/2
    distances=np.full(3,np.inf);np.divide(half,np.abs(local),out=distances,where=np.abs(local)>1e-10)
    center=R@geometry['center']+pose[:3]
    return center+d*float(distances.min())


def visibility(root,geometry,profile):
    gx,gy=profile['goal_x'],profile['goal_y'];goal=np.array([[x,y,.002] for x in gx for y in gy])
    box=np.array([[x,y,geometry['center'][2]] for x,y in geometry['projected_box_corners']])
    result={}
    for view in ('ego','task'):
        pos,R=camera_world_transform(root,view);mount=CAMERAS[view]
        fx=mount['focal_length_mm']/mount['horizontal_aperture_mm']*1280
        fy=mount['focal_length_mm']/mount['vertical_aperture_mm']*720
        def project(points):
            camera=(points-pos)@R;depth=camera[:,0];safe=np.where(depth>1e-6,depth,1.)
            uv=np.c_[640-fx*camera[:,1]/safe,360-fy*camera[:,2]/safe]
            inside=(depth>.01)&(uv[:,0]>=12)&(uv[:,0]<=1268)&(uv[:,1]>=12)&(uv[:,1]<=708)
            return int(inside.sum()),uv.tolist()
        b,bp=project(box);g,gp=project(goal)
        result[view]={'box_visible_points':b,'goal_visible_corners':g,'box_pixels':bp,'goal_pixels':gp,
            'geometric_relationship_visible':b>=6 and g>=3}
    return result


def command(env,time):
    import torch
    from isaaclab.utils.math import quat_mul,quat_inv
    profile=env.cfg.approved_profile;cfg=profile['large_goal_recovery']
    state=getattr(env,'_scaleup_large_recovery',None)
    if state is None:
        data=json.loads(Path(cfg['recorded_actions_path']).read_text())
        state={'phase':'replay_failure','phase_start':0.,'actions':data['actions'],'brake_ticks':0,
            'braked':False,'backward_distance_m':0.,'left_shift_m':0.,'visual_relationship_verified':False,'inward_push':False}
        env._scaleup_large_recovery=state
    base=env.base_pos_w[0].cpu().numpy();quat=env.base_quat[0].cpu().numpy()
    projected=quat_mul(env.base_quat,quat_inv(env.base_quat_rp))[0].cpu().numpy();R=rotation_xyzw(projected)
    origin=base.copy();origin[2]=0.;yaw=math.atan2(R[1,0],R[0,0]);g=env.geometry_world()
    lo,hi,xratio,yratio=relationship(g,profile);center=np.asarray(g['center']);velocity=env.base_velocity_world()
    phase=state['phase'];age=time-state['phase_start'];world_velocity=np.zeros(3);omega=0.;target=origin+R@np.array([.1934,.142,.05])
    def advance(name):state.update(phase=name,phase_start=time)
    def yaw_hold(desired,limit=.35):return float(np.clip(1.5*wrap(desired-yaw),-limit,limit))
    if phase in ('replay_failure','reproduce_missed_goal_push'):
        index=min(round(time*50),len(state['actions'])-1);raw=np.asarray(state['actions'][index],dtype=float)
        target=origin+R@raw[3:6];world_velocity=R@np.r_[raw[:2],0.];omega=float(raw[2])
        # Repair the known nominal-contact reset inside the historical prefix.
        # Preserve its body commands and later missed-goal behaviour.
        if cfg.get('repair_legacy_contact_reset',True) and 3.<=time<=5.8 and not state.get('handoff_fixed'):
            if 'contact_hold_x' not in state and 'last_native' in state and raw[3]<state['last_native'][3]-.08:
                state['contact_hold_x']=float(state['last_target'][0])
            if 'contact_hold_x' in state:
                if target[0]<state['contact_hold_x']:target[0]=state['contact_hold_x']
                else:state['handoff_fixed']=True
        if cfg.get('physical_missed_push') and time>=7.8 and xratio>=.4 and 'missed_push_start' not in state:
            state.update(missed_push_start=time,missed_push_target=state.get('last_target',target).tolist())
            advance('reproduce_missed_goal_push')
        if 'missed_push_start' in state:
            # An intentionally mistaken robot push, through real contact.
            # Sweep the front-contact point sideways while still advancing;
            # neither the goal nor the object state is written by the expert.
            from .push_box_geometry import forward_face_ray
            ray,_=forward_face_ray(env._box_geometry,env.primary_pose_w[0].cpu().numpy())
            speed_x=.012 if xratio>=.7 else .03
            world_velocity=np.array([speed_x,.04,0.])*smooth((time-state['missed_push_start'])/.5)
            previous=np.asarray(state['last_target']);target=previous+world_velocity*.02
            target[0]=max(target[0],float(ray[0]+.012));target[2]=float(g['center'][2])
            omega=float(np.clip(-1.2*yaw,-.25,.25))
        if xratio>=.7 and yratio<=cfg.get('inside_y_trigger_ratio',.4) and hi[1]>profile['goal_y'][1] and center[0]-profile['initial_center_x_world']>=.25:
            state.update(trigger_time=time,trigger_inside_y_ratio=yratio,trigger_footprint=g['footprint_xy'],
                brake_base=base.tolist(),brake_target=state.get('last_target',target).tolist(),
                brake_velocity=world_velocity.tolist(),heading=R[:,0].tolist(),left_axis=R[:,1].tolist(),
                actual_forward_before=float(np.dot(velocity,R[:,0])),inspect_target=[min(base[0]-.25,profile['goal_x'][0]-.45),max(base[1]+.15,(center[1]+sum(profile['goal_y'])/2)/2)])
            advance('large_recovery_brake')
    elif phase=='large_recovery_brake':
        start=np.asarray(state['brake_target']);u=smooth(age/.5)
        clear=start.copy();clear[0]=min(clear[0]-.04,lo[0]-.035);clear[2]+=.045
        target=start*(1-u)+clear*u;world_velocity=np.asarray(state['brake_velocity'])*(1-u)
        omega=yaw_hold(0.,.25)
        if age>=.4 and np.linalg.norm(velocity[:2])<=.04:state['brake_ticks']+=1
        else:state['brake_ticks']=0
        if state['brake_ticks']>=3:
            state['braked']=True;state['release_target']=target.tolist();advance('large_recovery_back_and_left')
    elif phase=='large_recovery_back_and_left':
        desired=np.asarray(state['inspect_target']);world_velocity[:2]=[np.clip(1.2*(desired[0]-base[0]),-.12,0.),np.clip(1.2*(desired[1]-base[1]),0.,.08)]
        omega=yaw_hold(0.,.25)
        release=np.asarray(state['release_target']);target=release*(1-smooth(age/.8))+target*smooth(age/.8)
        delta=base-np.asarray(state['brake_base'])
        state['backward_distance_m']=max(state['backward_distance_m'],-float(np.dot(delta,np.asarray(state['heading']))))
        state['left_shift_m']=max(state['left_shift_m'],float(np.dot(delta,np.asarray(state['left_axis']))))
        if np.linalg.norm(desired-base[:2])<.04 and abs(yaw)<.08:advance('large_recovery_observe')
    elif phase=='large_recovery_observe':
        omega=yaw_hold(0.,.2);checks=visibility(np.r_[base,quat],g,profile)
        from .snapshots import capture_rgb
        rgb,_,_=capture_rgb(env.env,env.index);pixel_checks={}
        for view,key in [('ego','ego'),('task','task_centric')]:
            pixels=np.asarray(rgb[key],dtype=np.float32);red,green,blue=pixels[:,:,0],pixels[:,:,1],pixels[:,:,2]
            green_count=int(((green>1.25*red)&(green>1.25*blue)&(green>70)).sum())
            yellow_count=int(((red>75)&(green>65)&(red-blue>18)&(red>green*.85)&(red<green*1.75)).sum())
            pixel_checks[view]={'goal_green_pixels':green_count,'box_yellow_pixels':yellow_count}
            checks[view]['actual_scene_pixels_present']=green_count>=150 and yellow_count>=500
        visible=any(d['geometric_relationship_visible'] and d['actual_scene_pixels_present'] for d in checks.values())
        state['visibility_checks']=checks;state['pixel_checks']=pixel_checks
        if visible and age>=.8:
            state['visual_relationship_verified']=True;state['observed_at_time']=time
            state['side_position']=[float(center[0]-.142),float(hi[1]+.43)]
            advance('large_recovery_side_clearance')
    elif phase=='large_recovery_side_clearance':
        desired=state['side_position'];world_velocity[1]=float(np.clip(1.2*(desired[1]-base[1]),0.,.09));omega=yaw_hold(0.,.25)
        if base[1]>=desired[1]-.03:advance('large_recovery_side_position')
    elif phase=='large_recovery_side_position':
        desired=np.asarray(state['side_position']);world_velocity[:2]=np.clip(1.2*(desired-base[:2]),[-.1,-.04],[.1,.04]);omega=yaw_hold(0.,.25)
        if np.linalg.norm(desired-base[:2])<.035:advance('large_recovery_turn_inward')
    elif phase=='large_recovery_turn_inward':
        omega=yaw_hold(-math.pi/2,.35)
        if abs(wrap(-math.pi/2-yaw))<.08:
            state['approach_entry']=target.tolist();advance('large_recovery_approach_side')
    elif phase=='large_recovery_approach_side':
        face=ray_side(env._box_geometry,env.primary_pose_w[0].cpu().numpy(),[0.,1.,0.])
        omega=yaw_hold(-math.pi/2,.25);gap=base[1]-face[1]
        world_velocity[0]=float(np.clip(1.2*(face[0]-.142-base[0]),-.035,.035))
        world_velocity[1]=-.045 if gap>.39 else 0.
        contact=face.copy();contact[1]-=.012
        contact[1]=max(contact[1],base[1]-.43)
        target=np.asarray(state['approach_entry'])*(1-smooth(age/1.2))+contact*smooth(age/1.2)
        if age>=1.2 and gap<=.395 and np.linalg.norm(env.actual_fl_world()-face)<.065:
            state['push_contact_y']=float(target[1]);state['push_start_center']=center.tolist();advance('large_recovery_push_inward')
    elif phase=='large_recovery_push_inward':
        omega=yaw_hold(-math.pi/2,.25);goal_x=sum(profile['goal_x'])/2
        world_velocity[0]=float(np.clip(1.5*(goal_x-center[0]),-.03,.03));world_velocity[1]=-.065*smooth(age/.5)
        target=np.array([base[0]+.142,min(state['push_contact_y'],base[1]-.38),float(center[2])])
        state['inward_push']=True;state['inward_box_displacement_m']=max(state.get('inward_box_displacement_m',0.),state['push_start_center'][1]-float(center[1]))
    local=R.T@(target-origin);vlocal=R.T@world_velocity
    request=[float(vlocal[0]),float(vlocal[1]),float(omega),*local.tolist(),0.,0.,0.]
    evidence={'major_failure_reproduced':'trigger_time' in state,'trigger_inside_y_ratio':state.get('trigger_inside_y_ratio'),
        'braked_actual_velocity':state['braked'],'actual_forward_before_m_s':state.get('actual_forward_before'),
        'backward_distance_m':state['backward_distance_m'],'left_shift_m':state['left_shift_m'],
        'visual_relationship_verified':state['visual_relationship_verified'],'observed_at_time':state.get('observed_at_time'),
        'visibility_checks':state.get('visibility_checks'),'pixel_checks':state.get('pixel_checks'),
        'inward_push':state['inward_push'],'inward_box_displacement_m':state.get('inward_box_displacement_m',0.),
        'current_inside_y_ratio':yratio,'current_inside_x_ratio':xratio}
    diag={'phase':state['phase'],'commanded_contact_point':target.tolist(),'commanded_world_base_velocity':world_velocity.tolist(),
        'actual_fl_eef_world':env.actual_fl_world().tolist(),'box_pose':env.primary_pose_w[0].cpu().tolist(),
        'box_yaw_rad':g['yaw_rad'],'contact_evidence':'unknown_diagnostic_only','large_goal_evidence':evidence}
    state['last_target']=target.copy();state['last_native']=request.copy();env._expert_diagnostics=diag
    return request,diag
