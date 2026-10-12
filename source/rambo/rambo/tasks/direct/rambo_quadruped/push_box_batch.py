"""Independent Push lanes over unchanged controller and source box physics."""
from __future__ import annotations
import copy
import numpy as np
import torch
import isaaclab.sim as sim
from isaaclab.assets import RigidObject, RigidObjectCfg
from .push_box_v2 import PushBoxV2Env, asset_geometry
from ...common.batch_native9 import BatchNative9Mixin
from ...common.push_box_geometry import source_geometry, world_geometry, fully_inside, PolicySuccessHold
from ...common.push_box_scenarios import goal_markers


class PushBoxBatchEnv(BatchNative9Mixin, PushBoxV2Env):
    def _setup_post_clone_task_assets(self):
        low, high = asset_geometry(self.cfg.approved_asset_path)
        definitions = self.cfg.approved_profile['scaleup_lane_cases']
        if len(definitions) != self.num_envs:
            raise ValueError('Explicit case definition per Push lane required')
        self.lane_profiles = []
        self.lane_geometry = []
        self.initial_centers = []
        for index, case in enumerate(definitions):
            p = copy.deepcopy(case['profile'])
            origin = self._terrain.env_origins[index].cpu().numpy()
            p['goal_x'] = [x + float(origin[0]) for x in p['goal_x']]
            p['goal_y'] = [y + float(origin[1]) for y in p['goal_y']]
            p['canonical_goal_position'] = [sum(p['goal_x']) / 2, sum(p['goal_y']) / 2, 0.]
            p['environment_origin'] = origin.tolist()
            self.lane_profiles.append(p)
            geom = source_geometry(low, high, face=case['selected_face'])
            self.lane_geometry.append(geom)
            pose = np.r_[np.asarray(case['position']) + origin, case['orientation']]
            self.initial_centers.append(world_geometry(geom, pose)['center'][0])
            p['initial_center_x_world'] = self.initial_centers[-1]
            root = f'/World/envs/env_{index}/LingBotTask'
            spawn = sim.UsdFileCfg(usd_path=self.cfg.approved_asset_path)
            spawn.func(root + '/box', spawn, translation=tuple(case['position']), orientation=tuple(case['orientation']))
            for number, (pos, size) in enumerate(goal_markers(case['profile'])):
                marker = sim.CuboidCfg(size=size, visual_material=sim.PreviewSurfaceCfg(diffuse_color=tuple(case['profile'].get('goal_color', (.05,.8,.15)))))
                marker.func(root + f'/Goal_{number}', marker, translation=pos)
        self._primary = RigidObject(RigidObjectCfg(prim_path='/World/envs/env_.*/LingBotTask/box',
            init_state=RigidObjectCfg.InitialStateCfg(pos=tuple(definitions[0]['position']), rot=tuple(definitions[0]['orientation']))))
        self.scene.rigid_objects['box'] = self._primary
        self._box_geometry = self.lane_geometry[0]
        self._box_center_local_np = np.asarray(self._box_geometry['center'])
        self._initial_center_x = self.initial_centers[0]
        self._success_hold = PolicySuccessHold(3)
        self._success_holds = [PolicySuccessHold(3) for _ in self.lanes]
        if self.cfg.lift_camera_setup == 'robot-dual-v3':
            from ...common.lift_camera_rig import spawn
            spawn(self)

    def _setup_scene(self):
        super()._setup_scene()
        import omni.usd
        from pxr import UsdLux, Gf
        preset = self.cfg.approved_profile['scaleup_appearance']
        light = UsdLux.DomeLight(omni.usd.get_context().get_stage().GetPrimAtPath('/World/Light'))
        light.GetIntensityAttr().Set(float(preset['intensity']))
        light.GetColorAttr().Set(Gf.Vec3f(*preset['color']))

    def geometry_lane(self, index):
        return world_geometry(self.lane_geometry[index], self.primary_pose_w[index].detach().cpu().numpy())

    def profile_for_lane(self, index):
        return copy.deepcopy(self.lane_profiles[index])

    def task_fields_for_lane(self, index):
        geometry = self.geometry_lane(index)
        return {'task.goal.position': self.lane_profiles[index]['canonical_goal_position'],
                'task.progress': [geometry['center'][0] - self.initial_centers[index]]}

    def review_lane(self, index):
        g = self.geometry_lane(index); p = self.lane_profiles[index]
        return dict(**g, box_fully_inside=fully_inside(g['footprint_xy'], p['goal_x'], p['goal_y']),
                    actual_fl_eef_world=self.actual_fl_world(index).tolist(),
                    success_count=self._success_holds[index].count,
                    first_fully_inside_policy_ns=self._success_holds[index].first_inside_ns,
                    expert=self.expert_lanes[index].get('_expert_diagnostics'))

    def _get_dones(self):
        fallen = self.fallen; terminated = torch.zeros_like(fallen); timeout = torch.zeros_like(fallen)
        for index, lane in enumerate(self.lanes):
            if not self.lane_active[index]:
                continue
            g = self.geometry_lane(index); p = self.lane_profiles[index]; tick = self.lane_tick(index)
            inside = fully_inside(g['footprint_xy'], p['goal_x'], p['goal_y'])
            success = self._success_holds[index].update(tick, inside, not bool(fallen[index]))
            expired = tick >= self.cfg.pilot_max_physics_steps
            self._success[index] = success
            lane.set_outcome(success=success, fallen=bool(fallen[index]), timed_out=expired)
            terminated[index] = bool(fallen[index]) or success
            timeout[index] = expired and not success
        return terminated, timeout


class PushLaneView:
    FIELDS = {'base_pos_w', 'base_quat', 'base_quat_rp', 'primary_pose_w'}
    def __init__(self, env, index):
        object.__setattr__(self, 'env', env); object.__setattr__(self, 'index', index)
        cfg = copy.copy(env.cfg); cfg.approved_profile = env.lane_profiles[index]
        object.__setattr__(self, 'cfg', cfg)
        object.__setattr__(self, '_box_geometry', env.lane_geometry[index])

    def __getattr__(self, name):
        if name.startswith('_expert') or name.startswith('_corner') or name.startswith('_scaleup'):
            if name not in self.env.expert_lanes[self.index]:raise AttributeError(name)
            return self.env.expert_lanes[self.index][name]
        value = getattr(self.env, name)
        return value[self.index:self.index+1] if name in self.FIELDS else value

    def __setattr__(self, name, value):
        if not (name.startswith('_expert') or name.startswith('_corner') or name.startswith('_scaleup')):
            raise AttributeError('Only lane-local expert state may be written')
        self.env.expert_lanes[self.index][name] = value

    def geometry_world(self):return self.env.geometry_lane(self.index)
    def actual_fl_world(self):return self.env.actual_fl_world(self.index)
    def base_velocity_world(self):return self.env._robot.data.root_link_lin_vel_w.torch[self.index].detach().cpu().numpy()


def expert_command(env, index, time):
    from ...common.push_box_scaleup_expert import command
    return command(PushLaneView(env, index), time)
