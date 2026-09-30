"""Reviewed external button with physical spring slide; retained Go2 controller."""
import numpy as np
import torch
import omni.usd
from pxr import UsdGeom,UsdPhysics,Gf,Sdf,PhysxSchema
import isaaclab.sim as sim
from isaaclab.assets import RigidObject,RigidObjectCfg
from isaaclab.utils import configclass
from .push_box_v2 import PushBoxV2Cfg,PushBoxV2Env
from ...common.press_button_logic import PressSuccessHold

@configclass
class PressButtonV2Cfg(PushBoxV2Cfg):
    pass

class PressButtonV2Env(PushBoxV2Env):
    def _spawn_lift_basket(self):
        p=self.cfg.approved_profile;path=self._root+'/button'
        spawn=sim.UsdFileCfg(usd_path=self.cfg.approved_asset_path)
        spawn.func(path,spawn,translation=tuple(self.cfg.primary_position),orientation=(0.,0.,0.,1.))
        stage=omni.usd.get_context().get_stage();cap_path=path+'/Cap';cap=stage.GetPrimAtPath(cap_path)
        UsdPhysics.RigidBodyAPI.Apply(cap).CreateKinematicEnabledAttr(False)
        UsdPhysics.MassAPI.Apply(cap).CreateMassAttr(p['cap_mass_kg'])
        physical=PhysxSchema.PhysxRigidBodyAPI.Apply(cap);physical.CreateDisableGravityAttr(True)
        physical.CreateSolverPositionIterationCountAttr(16);physical.CreateSolverVelocityIterationCountAttr(4)
        colliders=[]
        for prim in stage.Traverse():
            if str(prim.GetPath()).startswith(path+'/') and prim.IsA(UsdGeom.Mesh):
                UsdPhysics.CollisionAPI.Apply(prim)
                UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr('convexHull')
                PhysxSchema.PhysxCollisionAPI.Apply(prim).CreateContactOffsetAttr(.001)
                PhysxSchema.PhysxCollisionAPI(prim).CreateRestOffsetAttr(0.)
                if str(prim.GetPath()).startswith(path+'/Housing/'):colliders.append(prim.GetPath())
        UsdPhysics.FilteredPairsAPI.Apply(cap).CreateFilteredPairsRel().SetTargets(colliders)
        joint=UsdPhysics.PrismaticJoint.Define(stage,path+'/SlideJoint');joint.CreateAxisAttr('X')
        joint.CreateLowerLimitAttr(0.);joint.CreateUpperLimitAttr(p['stroke_m'])
        joint.CreateBody1Rel().SetTargets([Sdf.Path(cap_path)])
        joint.CreateLocalPos0Attr(Gf.Vec3f(*self.cfg.primary_position));joint.CreateLocalRot0Attr(Gf.Quatf(1.))
        joint.CreateLocalPos1Attr(Gf.Vec3f(0,0,0));joint.CreateLocalRot1Attr(Gf.Quatf(1.))
        drive=UsdPhysics.DriveAPI.Apply(joint.GetPrim(),'linear');drive.CreateTypeAttr('force')
        drive.CreateTargetPositionAttr(0.);drive.CreateTargetVelocityAttr(0.)
        drive.CreateStiffnessAttr(p['spring_stiffness_N_m']);drive.CreateDampingAttr(p['spring_damping_N_s_m']);drive.CreateMaxForceAttr(p['max_effort_N'])
        self._primary=RigidObject(RigidObjectCfg(prim_path=cap_path,init_state=RigidObjectCfg.InitialStateCfg(pos=tuple(self.cfg.primary_position),rot=(0.,0.,0.,1.))))
        self.scene.rigid_objects['button_cap']=self._primary
        wall=p.get('wall',{'size':[.025,.26,.38],'center':[.74,p['button_rest_front_xyz'][1],.21]})
        mount=sim.CuboidCfg(size=tuple(wall['size']),collision_props=sim.CollisionPropertiesCfg(),visual_material=sim.PreviewSurfaceCfg(diffuse_color=(.21,.23,.25)))
        mount.func('/World/ButtonMount',mount,translation=tuple(wall['center']))
        if 'wall' in p:
            back=p['button_rest_front_xyz'][0]+p['asset_back_depth_m'];front=wall['center'][0]-wall['size'][0]/2;gap=front-back
            if gap>0.001:
                bracket=sim.CuboidCfg(size=(gap,.06,.06),collision_props=sim.CollisionPropertiesCfg(),visual_material=sim.PreviewSurfaceCfg(diffuse_color=(.21,.23,.25)))
                bracket.func('/World/ButtonBracket',bracket,translation=((back+front)/2,p['button_rest_front_xyz'][1],p['button_rest_front_xyz'][2]))
        self._initial_center_x=p['button_rest_front_xyz'][0]
        self._success_hold=PressSuccessHold(p['success_displacement_m'],p['success_policy_ticks'])
    @property
    def displacement(self):
        rest=self._primary_rest_pose[:,:3] if hasattr(self,'_primary_rest_pose') else torch.as_tensor([self.cfg.primary_position],device=self.device)
        return (self.primary_pose_w[:,:3]-rest)[:,0]
    @property
    def geometric_center(self):
        p=self.cfg.approved_profile
        point=torch.as_tensor([p['button_rest_front_xyz']],device=self.device,dtype=self.primary_pose_w.dtype).clone()
        point[:,0]+=self.displacement
        return point
    def review_diagnostics(self):
        return dict(button_displacement_m=float(self.displacement[0]),button_front_world=self.geometric_center[0].cpu().tolist(),cap_pose=self.primary_pose_w[0].cpu().tolist(),press_axis_world=[1.,0.,0.],stroke_m=self.cfg.approved_profile['stroke_m'],threshold_m=self.cfg.approved_profile['success_displacement_m'],success_count=self._success_hold.count,first_pressed_policy_ns=self._success_hold.first_pressed_ns,not_fallen=not bool(self.fallen[0]),actual_fl_eef_world=self.actual_fl_world().tolist(),expert=getattr(self,'_expert_diagnostics',None))
    def _reset_idx(self,env_ids):
        super()._reset_idx(env_ids)
        for key in ['_press_expert','_press_integral']:
            if hasattr(self,key):delattr(self,key)
    def _get_dones(self):
        recorder=getattr(self,'_v2_recorder',None);tick=recorder.tick if recorder is not None else 0
        fallen=self.fallen;success=self._success_hold.update(tick,float(self.displacement[0]),not bool(fallen[0]))
        self._success=torch.full_like(fallen,success)
        timed_out=torch.full_like(fallen,recorder is not None and tick>=self.cfg.pilot_max_physics_steps)
        return fallen|self._success,timed_out&~self._success
