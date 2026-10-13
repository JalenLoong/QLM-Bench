import torch
import omni.kit.app
import weakref
import isaaclab.sim as sim_utils
import isaaclab.utils.math as math_utils
from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg


from qlm_bench.controllers.rambo.joint_position_controller import JointPositionController as CoreJointPositionController

class JointPositionController(CoreJointPositionController):
    def __init__(self, env):
        super().__init__(env)
        self.debug_vis = bool(env.cfg.joint_position_controller_config["joint_position_controller_debug_vis"])
        self._set_joint_position_controller_vis(self.debug_vis)

    def _set_joint_position_controller_vis(self, debug_vis: bool) -> bool:
        self._set_joint_position_controller_vis_impl(debug_vis)
        if debug_vis:
            if self.joint_position_controller_vis_handle is None:
                app_interface = omni.kit.app.get_app_interface()
                self.joint_position_controller_vis_handle = app_interface.get_post_update_event_stream().create_subscription_to_pop(lambda event, obj=weakref.proxy(self): obj._joint_position_controller_vis_callback(event))
        elif self.joint_position_controller_vis_handle is not None:
            self.joint_position_controller_vis_handle.unsubscribe()
            self.joint_position_controller_vis_handle = None
        return True

    def _set_joint_position_controller_vis_impl(self, debug_vis: bool):
        if debug_vis:
            if not hasattr(self, 'phase_switched_foot_visualizer'):
                self.phase_switched_foot_visualizer = []
                self.desired_foot_position_visualizer = []
                self.bezier_trajectories_visualizer = []
                for i in range(self._env.num_feet):
                    marker_cfg = phase_switched_foot_MARKER_CFG.copy()
                    marker_cfg.prim_path = '/Visuals/phase_switched_foot_' + str(i)
                    self.phase_switched_foot_visualizer.append(VisualizationMarkers(marker_cfg))
                    marker_cfg = desired_foot_position_MARKER_CFG.copy()
                    marker_cfg.prim_path = '/Visuals/desired_foot_position_' + str(i)
                    self.desired_foot_position_visualizer.append(VisualizationMarkers(marker_cfg))
                    for j in range(self._bezier_num_points):
                        marker_cfg = bezier_trajectories_MARKER_CFG.copy()
                        marker_cfg.prim_path = '/Visuals/bezier_trajectories_' + str(i) + '_' + str(j)
                        self.bezier_trajectories_visualizer.append(VisualizationMarkers(marker_cfg))
            for i in range(self._env.num_feet):
                self.phase_switched_foot_visualizer[i].set_visibility(True)
                self.desired_foot_position_visualizer[i].set_visibility(True)
                for j in range(self._bezier_num_points):
                    self.bezier_trajectories_visualizer[i * self._bezier_num_points + j].set_visibility(True)
        elif hasattr(self, 'phase_switched_foot_visualizer'):
            for i in range(self._env.num_feet):
                self.phase_switched_foot_visualizer[i].set_visibility(False)
                self.desired_foot_position_visualizer[i].set_visibility(False)
                for j in range(self._bezier_num_points):
                    self.bezier_trajectories_visualizer[i * self._bezier_num_points + j].set_visibility(False)

    def _joint_position_controller_vis_callback(self, event):
        for i in range(self._env.num_feet):
            in_phase = torch.logical_and(self._desired_contact_mode[:, i] < 0.5, self._desired_contact_mode[:, i] > -0.5)
            in_swing = torch.logical_not(self._desired_contact_state[:, i])
            in_phase_swing = torch.logical_and(in_phase, in_swing)
            scales = torch.stack([in_phase_swing.to(torch.float)] * 3, dim=-1)
            self.phase_switched_foot_visualizer[i].visualize(self._phase_switch_foot_positions_w[:, i, :], scales=scales)
            self.desired_foot_position_visualizer[i].visualize(self._desired_foot_positions_w[:, i, :], scales=scales)
            for j in range(self._bezier_num_points):
                self.bezier_trajectories_visualizer[i * self._bezier_num_points + j].visualize(self._bezier_trajectories_w[:, i, j, :], scales=scales)

    def update(self):
        result = super().update()
        if self.debug_vis:
            for i in range(self._bezier_num_points):
                self._bezier_trajectories[:, :, i, :] = compute_desired_foot_positions(self._env.base_rot_mat_rp, self._env.base_lin_vel_b, self._env.base_ang_vel_b, self._hip_positions_in_body_frame, self._desired_foot_height, self._desired_foot_clearance, self._env.contact_generator.stance_duration, torch.ones_like(self._env.contact_generator.normalized_phase) * (i + 1) / self._bezier_num_points, self._phase_switch_foot_positions)
                temp = self._bezier_trajectories[:, :, i, :].clone()
                temp = torch.matmul(math_utils.matrix_from_quat(math_utils.yaw_quat(self._env._robot.data.root_link_quat_w.torch)), temp.transpose(1, 2)).transpose(1, 2)
                self._bezier_trajectories_w[:, :, i, :] = temp
                self._bezier_trajectories_w[:, :, i, :2] += self._env._robot.data.root_link_pos_w.torch[:, :2].unsqueeze(1)
            temp = self._phase_switch_foot_positions.clone()
            temp = torch.matmul(math_utils.matrix_from_quat(math_utils.yaw_quat(self._env._robot.data.root_link_quat_w.torch)), temp.transpose(1, 2)).transpose(1, 2)
            self._phase_switch_foot_positions_w = temp
            self._phase_switch_foot_positions_w[:, :, :2] += self._env._robot.data.root_link_pos_w.torch[:, :2].unsqueeze(1)
            temp = self._desired_foot_positions.clone()
            temp = torch.matmul(math_utils.matrix_from_quat(math_utils.yaw_quat(self._env._robot.data.root_link_quat_w.torch)), temp.transpose(1, 2)).transpose(1, 2)
            self._desired_foot_positions_w = temp
            self._desired_foot_positions_w[:, :, :2] += self._env._robot.data.root_link_pos_w.torch[:, :2].unsqueeze(1)
        return result

from qlm_bench.controllers.rambo.joint_position_controller import cubic_bezier_z, cubic_bezier_xy, cubic_bezier_xy_inv, _gen_swing_foot_trajectory, cross_quad, compute_desired_foot_positions
