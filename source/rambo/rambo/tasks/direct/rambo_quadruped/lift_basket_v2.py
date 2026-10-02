"""Approved lift task; original controller/reset hooks, no attachment forces."""
import numpy as np
import torch
from pxr import Usd,UsdGeom,Gf
from scipy.spatial import ConvexHull
from rambo.assets import BASKET_INITIAL_ORIENTATION_XYZW,spawn_lift_basket_asset
from .native9_task_env import Native9TaskEnv,Native9TaskCfg
from isaaclab.utils import configclass
from ...common.push_box_geometry import PolicySuccessHold,rotation_xyzw
from ...common.lift_basket_geometry import world_geometry,lifted

def asset_vertices(path, include_handle=False):
    stage=Usd.Stage.Open(str(path));root=stage.GetDefaultPrim();cache=UsdGeom.XformCache();points=[]
    if UsdGeom.GetStageMetersPerUnit(stage)!=1:raise ValueError('Expected meter source')
    scale=root.GetAttribute('xformOp:scale').Get()
    for p in stage.Traverse():
        if p.IsA(UsdGeom.Mesh):
            transform=cache.ComputeRelativeTransform(p,root)[0]
            points.extend(list(transform.Transform(Gf.Vec3d(*x))) for x in UsdGeom.Mesh(p).GetPointsAttr().Get())
    points=np.asarray(points,dtype=np.float64)*np.asarray(scale,dtype=np.float64)
    hull=ConvexHull(points)
    support=points[hull.vertices]
    if not include_handle:return support
    upright=points@rotation_xyzw(BASKET_INITIAL_ORIENTATION_XYZW).T
    handle=points[upright[:,2]>upright[:,2].min()+.18]
    handle=handle[ConvexHull(handle).vertices]
    return support,handle

@configclass
class LiftBasketV2Cfg(Native9TaskCfg):
    pass


class LiftBasketV2Env(Native9TaskEnv):
    def _spawn_task_asset(self):
        self._basket_vertices,self._handle_vertices=asset_vertices(self.cfg.approved_asset_path,include_handle=True)
        self._success_hold=PolicySuccessHold(3)
        self._primary=spawn_lift_basket_asset(self._root+'/basket',tuple(self.cfg.primary_position),usd_path=self.cfg.approved_asset_path)
        self.scene.rigid_objects['basket']=self._primary
    @property
    def geometric_center(self):
        return torch.tensor([self.geometry_world()['center']],device=self.device,dtype=torch.float32)
    def geometry_world(self):
        return world_geometry(self._basket_vertices,self.primary_pose_w[0].detach().cpu().numpy())
    def review_diagnostics(self):
        g=self.geometry_world();p=self.cfg.approved_profile
        return dict(**g,clearance_m=g['minimum_world_z']-p['floor_z_m'],basket_lifted=lifted(g,p['floor_z_m'],p['minimum_clearance_m']),not_fallen=not bool(self.fallen[0]),success_count=self._success_hold.count,actual_fl_eef_world=self.actual_fl_world().tolist(),expert=getattr(self,'_expert_diagnostics',None),contact='unknown_diagnostic_only')
    def _get_dones(self):
        tick=self.episode_tick
        p=self.cfg.approved_profile;fallen=self.fallen
        eligible=tick*0.002>=p.get('success_enable_after_s',0.)
        success=self._success_hold.update(tick,eligible and lifted(self.geometry_world(),p['floor_z_m'],p['minimum_clearance_m']),not bool(fallen[0]))
        return self._finish_task_outcome(success,fallen)

    def configure_foot_geometry(self):
        import omni.usd
        from itertools import product
        from pxr import UsdPhysics
        stage=omni.usd.get_context().get_stage();name=self._robot.body_names[self.feet_ids[0]]
        roots=[p for p in stage.Traverse() if p.GetName()==name and p.HasAPI(UsdPhysics.RigidBodyAPI) and str(p.GetPath()).startswith('/World/envs/env_0/Robot/')]
        if len(roots)!=1:raise RuntimeError('Cannot unambiguously resolve FL rigid foot')
        body=roots[0];cache=UsdGeom.XformCache();bbox=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render','proxy','guide']);vertices=[];paths=[]
        for prim in Usd.PrimRange(body,Usd.TraverseInstanceProxies()):
            if prim.HasAPI(UsdPhysics.CollisionAPI) and prim.GetAttribute('physics:collisionEnabled').Get() is not False:
                bounds=bbox.ComputeLocalBound(prim).ComputeAlignedBox();lo=bounds.GetMin();hi=bounds.GetMax();transform=cache.ComputeRelativeTransform(prim,body)[0]
                mesh_points=UsdGeom.Mesh(prim).GetPointsAttr().Get() if prim.IsA(UsdGeom.Mesh) else list(product(*zip(lo,hi)))
                vertices.extend(list(transform.Transform(Gf.Vec3d(*v))) for v in mesh_points);paths.append(str(prim.GetPath()))
        if not vertices:raise RuntimeError('No FL collision geometry; refuse guessed foot extent')
        radius=float(np.linalg.norm(np.asarray(vertices),axis=1).max())
        if not 0<radius<.08:raise RuntimeError(f'Unexpected FL collision envelope {radius}')
        self._foot_radius=radius
        v=np.asarray(vertices);self._foot_vertices=v[ConvexHull(v).vertices]
        return dict(body=str(body.GetPath()),collision_prims=paths,conservative_radius_m=radius,method='actual collision mesh convex-hull vertices in FL rigid-link coordinates; transformed per tick',local_support_vertices=self._foot_vertices.tolist())
    def insertion_geometry(self):
        pose=self.primary_pose_w[0].detach().cpu().numpy();R=rotation_xyzw(pose[3:]);handle=self._handle_vertices@R.T+pose[:3]
        axis=R@rotation_xyzw(BASKET_INITIAL_ORIENTATION_XYZW).T@np.array([1.,0.,0.])
        foot=self._robot.data.body_link_pos_w.torch[0,self.feet_ids[0]].detach().cpu().numpy().copy()
        foot_q=self._robot.data.body_link_quat_w.torch[0,self.feet_ids[0]].detach().cpu().numpy()
        foot_vertices=self._foot_vertices@rotation_xyzw(foot_q).T+foot
        return handle,axis,foot,foot_vertices
