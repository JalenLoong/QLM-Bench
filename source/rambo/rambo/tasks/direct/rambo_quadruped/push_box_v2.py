"""Approved Box 05 task, reusing the existing quadruped controller unchanged."""
from pathlib import Path
import json
import numpy as np
import torch
from pxr import Usd, UsdGeom, Gf
import isaaclab.sim as sim
from isaaclab.assets import RigidObject, RigidObjectCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import quat_apply
from .native9_task_env import Native9TaskEnv, Native9TaskCfg
from ...common.push_box_scenarios import goal_markers
from ...common.push_box_geometry import source_geometry, world_geometry, fully_inside, PolicySuccessHold

@configclass
class PushBoxV2Cfg(Native9TaskCfg):
    # Reuse the camera rig's existing mounting implementation, not Lift success.
    task_kind = 'lift_basket'
    approved_asset_path = ''
    approved_profile = None
    pilot_max_physics_steps = 5000
    primary_orientation = (0.,0.,0.,1.)


def asset_geometry(path):
    stage=Usd.Stage.Open(str(path));root=stage.GetDefaultPrim();cache=UsdGeom.XformCache();points=[]
    if UsdGeom.GetStageUpAxis(stage)!='Z' or UsdGeom.GetStageMetersPerUnit(stage)!=1:
        raise ValueError('Expected approved meter/Z-up source')
    for p in stage.Traverse():
        if p.IsA(UsdGeom.Mesh):
            transform=cache.ComputeRelativeTransform(p,root)[0]
            points.extend(list(transform.Transform(Gf.Vec3d(*x))) for x in UsdGeom.Mesh(p).GetPointsAttr().Get())
    values=np.asarray(points);return values.min(0),values.max(0)


class PushBoxV2Env(Native9TaskEnv):
    def _spawn_task_asset(self):
        low,high=asset_geometry(self.cfg.approved_asset_path)
        self._box_geometry=source_geometry(low,high,face=self.cfg.approved_profile.get("episode_scenario",{}).get("selected_face","local_x_min"))
        self._box_center_local_np=(low+high)/2
        self._initial_center_x=world_geometry(self._box_geometry,[*self.cfg.primary_position,*self.cfg.primary_orientation])['center'][0]
        self._success_hold=PolicySuccessHold(self.cfg.approved_profile["success_policy_ticks"])
        path=self._root+'/box05'
        cfg=sim.UsdFileCfg(usd_path=self.cfg.approved_asset_path)
        cfg.func(path,cfg,translation=tuple(self.cfg.primary_position),orientation=tuple(self.cfg.primary_orientation))
        self._primary=RigidObject(RigidObjectCfg(prim_path=path,init_state=RigidObjectCfg.InitialStateCfg(pos=tuple(self.cfg.primary_position),rot=tuple(self.cfg.primary_orientation))))
        self.scene.rigid_objects['box05']=self._primary
        for i,(pos,size) in enumerate(goal_markers(self.cfg.approved_profile)):
            marker=sim.CuboidCfg(size=size,visual_material=sim.PreviewSurfaceCfg(diffuse_color=tuple(self.cfg.approved_profile.get("goal_color",(.05,.8,.15)))))
            marker.func('/World/Goal_'+str(i),marker,translation=pos)

    @property
    def geometric_center(self):
        pose=self.primary_pose_w
        local=torch.as_tensor(self._box_center_local_np,device=self.device,dtype=pose.dtype).expand(self.num_envs,-1)
        return pose[:,:3]+quat_apply(pose[:,3:],local)

    def geometry_world(self):
        return world_geometry(self._box_geometry,self.primary_pose_w[0].detach().cpu().numpy())

    def review_diagnostics(self):
        geometry=self.geometry_world()
        return dict(**geometry,actual_fl_eef_world=self.actual_fl_world().tolist(),
                    box_fully_inside=fully_inside(geometry['footprint_xy'],self.cfg.approved_profile['goal_x'],self.cfg.approved_profile['goal_y']),
                    success_count=self._success_hold.count,first_fully_inside_policy_ns=self._success_hold.first_inside_ns,
                    expert=getattr(self,'_expert_diagnostics',None))

    def _get_dones(self):
        geometry=self.geometry_world();profile=self.cfg.approved_profile
        inside=fully_inside(geometry['footprint_xy'],profile['goal_x'],profile['goal_y'])
        tick=self.episode_tick
        fallen=self.fallen
        success=self._success_hold.update(tick,inside,not bool(fallen[0]))
        return self._finish_task_outcome(success,fallen)
