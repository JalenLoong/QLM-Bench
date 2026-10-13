"""Physical geometry facade for the retained three-task scripted experts."""
from pathlib import Path
from types import SimpleNamespace
import itertools
import json
import copy

import numpy as np
import torch
import mujoco

from qlm_bench.controllers.rambo.math import quat_apply


class ExpertAdapter:
    def __init__(self,physics,core,task):
        self.physics,self.core,self.task=physics,core,task
        self.device=core.device
        configs=Path(__file__).resolve().parents[4]/'configs/collection'
        profile=copy.deepcopy(task.profile.get('source_profile')) or json.loads((configs/(task.task+'.json')).read_text())
        if task.task=='push_box' and 'source_profile' not in task.profile:
            profile['expert'].update(motion='continuous',transition_s=.8)
        self.cfg=SimpleNamespace(approved_profile=profile)
        self.override=None
        geom=physics.model.geom('FL');self._foot_body=int(geom.bodyid[0])
        if geom.type[0]!=mujoco.mjtGeom.mjGEOM_SPHERE:
            raise ValueError('Original FL sphere collision expected; no guessed foot envelope')
        radius=float(geom.size[0]);self._foot_vertices=np.array(list(itertools.product([-radius,radius],repeat=3)))+geom.pos
        self._foot_radius=float(np.linalg.norm(self._foot_vertices,axis=1).max())
        if task.task=='push_box' and 'bounds_local' in task.profile:
            from .experts.push_box_geometry import source_geometry
            self._box_geometry=source_geometry(*task.profile['bounds_local'],face=profile.get('episode_scenario',{}).get('selected_face','local_x_min'))

    def apply_profile_override(self,override):
        if override.get('task_id')!=self.task.task or set(override)-{'task_id','expert','rationale','version'}:
            raise ValueError('Only an explicit task expert configuration may be overridden')
        if not override.get('version') or not override.get('rationale'):
            raise ValueError('Versioned expert override and rationale required')
        original=self.cfg.approved_profile['expert']
        if set(override['expert'])-set(original):raise ValueError('Unknown expert parameter')
        self.override=copy.deepcopy(override);original.update(copy.deepcopy(override['expert']))

    @property
    def base_pos_w(self):return self.core.robot.position
    @property
    def base_quat(self):return self.core.base_quat
    @property
    def base_quat_rp(self):return self.core.base_quat_rp
    @property
    def primary_pose_w(self):
        d=self.physics.data[0];q=d.xquat[self.task.body]
        return torch.tensor(np.r_[d.xpos[self.task.body],q[[1,2,3,0]]][None],dtype=torch.float32,device=self.device)
    @property
    def displacement(self):
        m=self.physics.model;d=self.physics.data[0]
        joint=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,'button_slide')
        return [float(d.qpos[m.jnt_qposadr[joint]])]

    def actual_fl_world(self):
        return (quat_apply(self.base_quat,self.core.ee_pos_b[:,0])+self.base_pos_w)[0].cpu().numpy()

    def geometry_world(self):
        p,r,corners=self.task.geometry(0)
        if self.task.task=='push_box' and hasattr(self,'_box_geometry'):
            from .experts.push_box_geometry import world_geometry
            return world_geometry(self._box_geometry,self.primary_pose_w[0].cpu().numpy())
        result={'center':self.task.geometric_center(0).tolist(),'minimum_world_z':float(corners[:,2].min())}
        if self.task.task=='push_box':
            half=self.task.profile['half_extent']
            result.update(face_center=(p+r@[-half[0],0.,0.]).tolist(),face_normal=(r@[-1.,0.,0.]).tolist(),
                          yaw_rad=float(np.arctan2(r[1,0],r[0,0])),
                          footprint_xy=[[float(x),float(y)] for x,y in itertools.product(
                              [corners[:,0].min(),corners[:,0].max()],[corners[:,1].min(),corners[:,1].max()])])
        return result

    def insertion_geometry(self):
        if 'handle_vertices_local' in self.task.profile:
            from scipy.spatial.transform import Rotation
            p,r,_=self.task.geometry(0)
            handle=np.asarray(self.task.profile['handle_vertices_local'])@r.T+p
            original=Rotation.from_quat(self.task.profile['initial_orientation_xyzw']).as_matrix()
            axis=r@original.T@np.array([1.,0.,0.])
            data=self.physics.data[0];foot=data.xpos[self._foot_body].copy()
            points=self._foot_vertices@data.xmat[self._foot_body].reshape(3,3).T+foot
            return handle,axis,foot,points
        p,r,_=self.task.geometry(0);h=self.task.profile['handle_local']
        corners=np.array(list(itertools.product([h['x']-h['half_thickness'],h['x']+h['half_thickness']],
                            [-.072,.072],[.11,.278])))@r.T+p
        d=self.physics.data[0];geom=self.physics.foot_geom_ids[0]
        foot=d.geom_xpos[geom].copy()
        points=foot+np.array(list(itertools.product([-.022,.022],repeat=3)))
        return corners,r[:,0],foot,points

    def command(self):
        if self.task.task=='push_box':from .experts.push_box_expert import command
        elif self.task.task=='press_button':from .experts.press_button_expert import command
        else:from .experts.lift_basket_expert import command
        return command(self,float(self.physics.ticks[0])*.002)
