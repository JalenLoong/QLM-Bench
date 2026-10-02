"""Owned physical/evaluator snapshots; simulator state never becomes a policy packet implicitly."""
from __future__ import annotations
import hashlib
import numpy as np
from rambo.dataset_v2.task_state import task_values


def as_array(tensor):
    return tensor.detach().cpu().numpy().copy()


def capture_state(env):
    import torch
    from rambo.utils import math as rm
    e=env;r=e._robot.data;o=e._primary.data
    g=e.projected_gravity_b;R=e.base_rot_mat_rp;foot=e.ee_pos_b[:,0]
    pos=(R@foot.unsqueeze(-1)).squeeze(-1);pos[:,2]+=e.base_height
    # Derivative of the existing analytical projected-frame foot point.
    body_v=(e.all_foot_jacobian[:,:3]@e.joint_vel.unsqueeze(-1)).squeeze(-1)
    dg=-torch.linalg.cross(e.base_ang_vel_b,g,dim=-1);eps=1e-4
    g1=g+eps*dg;g1=g1/torch.linalg.vector_norm(g1,dim=-1,keepdim=True)
    R1=rm.rp_rotation_from_gravity_b(g1).transpose(1,2)
    vel=(R@body_v.unsqueeze(-1)).squeeze(-1)+((R1-R)/eps@foot.unsqueeze(-1)).squeeze(-1);vel[:,2]+=e.base_lin_vel_w[:,2]
    forces=e._contact_sensor._data.net_forces_w.torch[0]
    feet=forces[e._contact_feet_ids]
    center=e.geometric_center[0]
    values={'observation.state.base.position':r.root_link_pos_w.torch[0], 'observation.state.base.orientation':r.root_link_quat_w.torch[0], 'observation.state.base.linear_velocity':r.root_link_lin_vel_w.torch[0], 'observation.state.base.angular_velocity':r.root_link_ang_vel_w.torch[0], 'observation.state.projected_gravity':g[0], 'observation.state.joint_position':e.joint_pos[0], 'observation.state.joint_velocity':e.joint_vel[0], 'observation.state.fl_ee_position':pos[0], 'observation.state.fl_ee_velocity':vel[0], 'observation.state.fl_contact_force':feet[0], 'task.object.position':o.root_link_pos_w.torch[0], 'task.object.orientation':o.root_link_quat_w.torch[0], 'task.object.linear_velocity':o.root_link_lin_vel_w.torch[0], 'task.object.angular_velocity':o.root_link_ang_vel_w.torch[0]}
    state={k:as_array(v).astype(np.float32).tolist() for k,v in values.items()}
    profile=e.cfg.approved_profile
    if profile.get('task_profile_version','').startswith('lift-basket-'):
        task_fields={'task.goal.position':list(profile['lift_goal_position']),
                     'task.progress':[float(e.geometry_world()['minimum_world_z'])-profile['floor_z_m']]}
    else:
        task_fields=task_values(profile,as_array(center),e._initial_center_x)
    state.update({'observation.state.foot_contact':as_array(torch.linalg.vector_norm(feet,dim=-1)>0).tolist(),
                  **task_fields,'task.success':[bool(e.task_success[0])],
                  'task.contact.fl_object':[False],'task.contact.body_object':[False]})
    return state


def capture_rgb(env):
    rgb={};hashes={};frames={}
    for role,field in [("ego","front_camera"),("task_centric","task_camera")]:
        sensor=getattr(env,field,None)
        if sensor is None:
            continue
        rgb[role]=as_array(sensor.data.output["rgb"].torch[0])
        hashes[role]=hashlib.sha256(rgb[role].tobytes()).hexdigest()
        frame=sensor.frame
        frames[role]=int(frame.torch[0]) if hasattr(frame,"torch") else int(frame[0])
    return rgb,hashes,frames
