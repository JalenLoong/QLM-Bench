"""Opt-in replicated Press Button scenes; single-env implementation is unchanged."""
from __future__ import annotations
import copy
import torch
import numpy as np
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf, Sdf, PhysxSchema
import isaaclab.sim as sim
from isaaclab.assets import RigidObject, RigidObjectCfg
from .press_button_v2 import PressButtonV2Env
from ...common.batch_native9 import BatchNative9Mixin
from ...common.press_button_logic import PressSuccessHold


class BatchPressButtonEnv(BatchNative9Mixin, PressButtonV2Env):
    def _setup_post_clone_task_assets(self):
        p = self.cfg.approved_profile
        stage = omni.usd.get_context().get_stage()
        for index in range(self.num_envs):
            root = f'/World/envs/env_{index}/LingBotTask'
            path = root + '/button'
            spawn = sim.UsdFileCfg(usd_path=self.cfg.approved_asset_path)
            spawn.func(path, spawn, translation=tuple(self.cfg.primary_position), orientation=(0., 0., 0., 1.))
            cap_path = path + '/Cap'; cap = stage.GetPrimAtPath(cap_path)
            UsdPhysics.RigidBodyAPI.Apply(cap).CreateKinematicEnabledAttr(False)
            UsdPhysics.MassAPI.Apply(cap).CreateMassAttr(p['cap_mass_kg'])
            physical = PhysxSchema.PhysxRigidBodyAPI.Apply(cap)
            physical.CreateDisableGravityAttr(True)
            physical.CreateSolverPositionIterationCountAttr(16); physical.CreateSolverVelocityIterationCountAttr(4)
            colliders = []
            for prim in stage.Traverse():
                name = str(prim.GetPath())
                if name.startswith(path + '/') and prim.IsA(UsdGeom.Mesh):
                    UsdPhysics.CollisionAPI.Apply(prim)
                    UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr('convexHull')
                    PhysxSchema.PhysxCollisionAPI.Apply(prim).CreateContactOffsetAttr(.001)
                    PhysxSchema.PhysxCollisionAPI(prim).CreateRestOffsetAttr(0.)
                    if name.startswith(path + '/Housing/'):
                        colliders.append(prim.GetPath())
            UsdPhysics.FilteredPairsAPI.Apply(cap).CreateFilteredPairsRel().SetTargets(colliders)
            joint = UsdPhysics.PrismaticJoint.Define(stage, path + '/SlideJoint'); joint.CreateAxisAttr('X')
            joint.CreateLowerLimitAttr(0.); joint.CreateUpperLimitAttr(p['stroke_m'])
            joint.CreateBody1Rel().SetTargets([Sdf.Path(cap_path)])
            anchor = np.asarray(self.cfg.primary_position) + self._terrain.env_origins[index].cpu().numpy()
            joint.CreateLocalPos0Attr(Gf.Vec3f(*anchor)); joint.CreateLocalRot0Attr(Gf.Quatf(1.))
            joint.CreateLocalPos1Attr(Gf.Vec3f(0, 0, 0)); joint.CreateLocalRot1Attr(Gf.Quatf(1.))
            drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), 'linear'); drive.CreateTypeAttr('force')
            drive.CreateTargetPositionAttr(0.); drive.CreateTargetVelocityAttr(0.)
            drive.CreateStiffnessAttr(p['spring_stiffness_N_m']); drive.CreateDampingAttr(p['spring_damping_N_s_m']); drive.CreateMaxForceAttr(p['max_effort_N'])
            wall = p.get('wall', {'size': [.025, .26, .38], 'center': [.74, p['button_rest_front_xyz'][1], .21]})
            mount = sim.CuboidCfg(size=tuple(wall['size']), collision_props=sim.CollisionPropertiesCfg(), visual_material=sim.PreviewSurfaceCfg(diffuse_color=(.21, .23, .25)))
            mount.func(root + '/ButtonMount', mount, translation=tuple(wall['center']))
            if 'wall' in p:
                back = p['button_rest_front_xyz'][0] + p['asset_back_depth_m']; front = wall['center'][0] - wall['size'][0] / 2; gap = front - back
                if gap > .001:
                    bracket = sim.CuboidCfg(size=(gap, .06, .06), collision_props=sim.CollisionPropertiesCfg(), visual_material=sim.PreviewSurfaceCfg(diffuse_color=(.21, .23, .25)))
                    bracket.func(root + '/ButtonBracket', bracket, translation=((back + front) / 2, p['button_rest_front_xyz'][1], p['button_rest_front_xyz'][2]))
        self._primary = RigidObject(RigidObjectCfg(prim_path='/World/envs/env_.*/LingBotTask/button/Cap',
            init_state=RigidObjectCfg.InitialStateCfg(pos=tuple(self.cfg.primary_position), rot=(0., 0., 0., 1.))))
        self.scene.rigid_objects['button_cap'] = self._primary
        self._initial_center_x = p['button_rest_front_xyz'][0]
        self._success_hold = PressSuccessHold(p['success_displacement_m'], p['success_policy_ticks'])
        self._success_holds = [PressSuccessHold(p['success_displacement_m'], p['success_policy_ticks']) for _ in self.lanes]
        if self.cfg.lift_camera_setup == 'robot-dual-v3':
            from ...common.lift_camera_rig import spawn
            spawn(self)

    @property
    def geometric_center(self):
        point = torch.as_tensor(self.cfg.approved_profile['button_rest_front_xyz'], device=self.device, dtype=self.primary_pose_w.dtype).expand(self.num_envs, -1).clone()
        point += self._terrain.env_origins
        point[:, 0] += self.displacement
        return point

    def task_fields_for_lane(self, index):
        p = self.cfg.approved_profile
        goal = np.asarray(p['button_rest_front_xyz']) + np.asarray(p['press_axis_world']) * p['success_displacement_m']
        goal += self._terrain.env_origins[index].cpu().numpy()
        return {'task.goal.position': goal.tolist(), 'task.progress': [float(self.displacement[index]) ]}

    def profile_for_lane(self, index):
        profile = copy.deepcopy(self.cfg.approved_profile)
        profile['canonical_goal_position'] = self.task_fields_for_lane(index)['task.goal.position']
        profile['environment_origin'] = self._terrain.env_origins[index].cpu().tolist()
        return profile

    def review_lane(self, index):
        return dict(button_displacement_m=float(self.displacement[index]), success_count=self._success_holds[index].count,
                    not_fallen=not bool(self.fallen[index]), env_index=index)

    def _get_dones(self):
        fallen = self.fallen
        terminated = torch.zeros_like(fallen); timeout = torch.zeros_like(fallen)
        for index, lane in enumerate(self.lanes):
            if not self.lane_active[index]:
                continue
            tick = self.lane_tick(index)
            success = self._success_holds[index].update(tick, float(self.displacement[index]), not bool(fallen[index]))
            expired = tick >= self.cfg.pilot_max_physics_steps
            self._success[index] = success
            lane.set_outcome(success=success, fallen=bool(fallen[index]), timed_out=expired)
            terminated[index] = bool(fallen[index]) or success
            timeout[index] = expired and not success
        return terminated, timeout


class PressLaneView:
    """Reuse the unchanged expert with one lane's pose and independent phase state."""
    FIELDS = {'base_pos_w', 'base_quat', 'base_quat_rp', 'displacement'}
    STATE = {'_press_expert', '_press_integral', '_expert_diagnostics'}
    def __init__(self, env, index):
        object.__setattr__(self, 'env', env); object.__setattr__(self, 'index', index)
        cfg = copy.copy(env.cfg); cfg.approved_profile = copy.deepcopy(env.cfg.approved_profile)
        face = np.asarray(cfg.approved_profile['button_rest_front_xyz']) + env._terrain.env_origins[index].cpu().numpy()
        cfg.approved_profile['button_rest_front_xyz'] = face.tolist()
        object.__setattr__(self, 'cfg', cfg)

    def __getattr__(self, name):
        if name in self.STATE:
            if name not in self.env.expert_lanes[self.index]:
                raise AttributeError(name)
            return self.env.expert_lanes[self.index][name]
        value = getattr(self.env, name)
        return value[self.index:self.index + 1] if name in self.FIELDS else value

    def __setattr__(self, name, value):
        if name not in self.STATE:
            raise AttributeError('Only per-lane expert state may be written')
        self.env.expert_lanes[self.index][name] = value

    def actual_fl_world(self):
        from isaaclab.utils.math import quat_apply
        e = self.env
        return (quat_apply(e.base_quat, e.ee_pos_b[:, 0]) + e.base_pos_w)[self.index].detach().cpu().numpy().copy()


def expert_command(env, index, time):
    from ...common.press_button_expert import command
    return command(PressLaneView(env, index), time)
