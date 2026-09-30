"""Lift task column adapter; unchanged recorder timing and terminal hooks."""
import numpy as np
from .recording_v2 import Recorder

class LiftRecorder(Recorder):
    def state(self):
        import torch
        from rambo.utils import math as rm
        e=self.env;r=e._robot.data;o=e._primary.data
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
        state={k:self.arr(v).astype(np.float32).tolist() for k,v in values.items()}
        state.update({'observation.state.foot_contact':self.arr(torch.linalg.vector_norm(feet,dim=-1)>0).tolist(),'task.goal.position':list(e.cfg.approved_profile['lift_goal_position']),'task.progress':[float(e.geometry_world()['minimum_world_z'])-e.cfg.approved_profile['floor_z_m']],'task.success':[bool(e.task_success[0])],'task.contact.fl_object':[False],'task.contact.body_object':[False]})
        return state
