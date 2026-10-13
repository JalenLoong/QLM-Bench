import torch
import numpy as np
import omni.kit.app
import weakref
import isaaclab.utils.math as math_utils
from isaaclab.markers import VisualizationMarkers
from isaaclab.markers.config import GREEN_ARROW_X_MARKER_CFG, BLUE_ARROW_X_MARKER_CFG

from qpth.qp import QPFunction, QPSolvers

from rambo.utils.math import quat_error as rambo_quat_error, xyzw_to_wxyz
from rambo.utils.tensor import to_torch


from qlm_bench.controllers.rambo.qp_torque_optimizer import QPTorqueOptimizer as CoreQPTorqueOptimizer

class QPTorqueOptimizer(CoreQPTorqueOptimizer):
    def __init__(self, env):
        super().__init__(env)
        self.debug_vis = bool(env.cfg.qp_torque_optimizer_config["qp_debug_vis"] and env.sim.has_gui)
        self._set_grf_vis(self.debug_vis)

    def _set_grf_vis(self, debug_vis):
        self._set_grf_vis_impl(debug_vis)
        if debug_vis:
            if self.grf_vis_handle is None:
                app_interface = omni.kit.app.get_app_interface()
                self.grf_vis_handle = app_interface.get_post_update_event_stream().create_subscription_to_pop(lambda event, obj=weakref.proxy(self): obj._vis_callback(event))
        elif self.grf_vis_handle is not None:
            self.grf_vis_handle.unsubscribe()
            self.grf_vis_handle = None
        return True

    def _set_grf_vis_impl(self, debug_vis):
        if debug_vis:
            if not hasattr(self, 'grf_visualizer'):
                self.grf_visualizer = []
                for i in range(self._env.num_feet):
                    marker_cfg = GREEN_ARROW_X_MARKER_CFG.copy()
                    marker_cfg.prim_path = '/Visuals/grf_' + str(i)
                    marker_cfg.markers['arrow'].scale = (0.2, 0.2, 0.2)
                    self.grf_visualizer.append(VisualizationMarkers(marker_cfg))
                marker_cfg = BLUE_ARROW_X_MARKER_CFG.copy()
                marker_cfg.prim_path = '/Visuals/desired_lin_acc'
                marker_cfg.markers['arrow'].scale = (0.3, 0.3, 0.3)
                self.desired_lin_acc_visualizer = VisualizationMarkers(marker_cfg)
                marker_cfg = GREEN_ARROW_X_MARKER_CFG.copy()
                marker_cfg.prim_path = '/Visuals/desired_ang_acc'
                marker_cfg.markers['arrow'].scale = (0.3, 0.3, 0.3)
                self.desired_ang_acc_visualizer = VisualizationMarkers(marker_cfg)
            for i in range(self._env.num_feet):
                self.grf_visualizer[i].set_visibility(True)
            self.desired_lin_acc_visualizer.set_visibility(True)
            self.desired_ang_acc_visualizer.set_visibility(True)
        elif hasattr(self, 'grf_visualizer'):
            for i in range(self._env.num_feet):
                self.grf_visualizer[i].set_visibility(False)
            self.desired_lin_acc_visualizer.set_visibility(False)
            self.desired_ang_acc_visualizer.set_visibility(False)

    def _vis_callback(self, event):
        grf_w = self.grf.reshape((-1, 4, 3)).clone()
        grf_w = torch.matmul(math_utils.matrix_from_quat(self._env._robot.data.root_link_quat_w.torch), grf_w.transpose(1, 2)).transpose(1, 2)
        ee_pos_w = self._env._robot.data.body_link_pos_w.torch[:, self._env.feet_ids].clone()
        for i in range(4):
            pos_w = ee_pos_w[:, i].clone()
            scale, quat = self._resolve_scale_and_quat_from_vector(self.grf_visualizer[i].cfg.markers['arrow'].scale, grf_w[:, i])
            self.grf_visualizer[i].visualize(pos_w, quat, scale)
        pos_acc = self._env._robot.data.root_link_pos_w.torch.clone()
        lin_acc_w = self.desired_acc[:, :3]
        lin_acc_w = torch.matmul(math_utils.matrix_from_quat(math_utils.yaw_quat(self._env._robot.data.root_link_quat_w.torch)), lin_acc_w.unsqueeze(-1)).squeeze(-1)
        scale, quat = self._resolve_scale_and_quat_from_vector(self.desired_lin_acc_visualizer.cfg.markers['arrow'].scale, lin_acc_w)
        self.desired_lin_acc_visualizer.visualize(pos_acc, quat, scale)
        ang_acc_w = self.desired_acc[:, 3:]
        ang_acc_w = torch.matmul(math_utils.matrix_from_quat(math_utils.yaw_quat(self._env._robot.data.root_link_quat_w.torch)), ang_acc_w.unsqueeze(-1)).squeeze(-1)
        scale, quat = self._resolve_scale_and_quat_from_vector(self.desired_ang_acc_visualizer.cfg.markers['arrow'].scale, ang_acc_w)
        self.desired_ang_acc_visualizer.visualize(pos_acc, quat, scale)

    def _resolve_scale_and_quat_from_vector(self, default_scale, vector):
        arrow_scale = torch.tensor(default_scale, device=vector.device).repeat(vector.shape[0], 1)
        arrow_scale[:, 0] *= torch.norm(vector, dim=-1) * 0.4
        directions = torch.nn.functional.normalize(vector)
        dir_x = directions[:, 0]
        dir_y = directions[:, 1]
        dir_z = directions[:, 2]
        yaw = torch.atan2(dir_y, dir_x)
        pitch = torch.atan2(-dir_z, torch.sqrt(dir_x ** 2 + dir_y ** 2))
        roll = torch.zeros_like(yaw)
        quaternions = math_utils.quat_from_euler_xyz(roll, pitch, yaw)
        return (arrow_scale, quaternions)

from qlm_bench.controllers.rambo.qp_torque_optimizer import compute_desired_acc, convert_to_skew_symmetric_batch, construct_mass_mat, solve_grf_qpth
