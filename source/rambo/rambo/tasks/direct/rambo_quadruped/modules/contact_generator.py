import torch
import numpy as np
import omni.kit.app
import weakref
import isaaclab.utils.math as math_utils
import isaaclab.sim as sim_utils
from isaaclab.markers import VisualizationMarkers
from isaaclab.markers.config import BLUE_ARROW_X_MARKER_CFG, GREEN_ARROW_X_MARKER_CFG
from isaaclab.markers.visualization_markers import VisualizationMarkersCfg
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR


from qlm_bench.controllers.rambo.contact_generator import ContactGenerator as CoreContactGenerator

class ContactGenerator(CoreContactGenerator):
    def __init__(self, env):
        super().__init__(env)
        self.debug_vis = bool(env.cfg.contact_generator_config["contact_generator_debug_vis"])
        self._set_contact_generator_vis(self.debug_vis)

    def _set_contact_generator_vis(self, debug_vis):
        self._set_contact_generator_vis_impl(debug_vis)
        if debug_vis:
            if self.contact_generator_vis_handle is None:
                app_interface = omni.kit.app.get_app_interface()
                self.contact_generator_vis_handle = app_interface.get_post_update_event_stream().create_subscription_to_pop(lambda event, obj=weakref.proxy(self): obj._contact_generator_vis_callback(event))
        elif self.contact_generator_vis_handle is not None:
            self.contact_generator_vis_handle.unsubscribe()
            self.contact_generator_vis_handle = None
        return True

    def _set_contact_generator_vis_impl(self, debug_vis):
        if debug_vis:
            if not hasattr(self, 'contact_generator_visualizer'):
                self.contact_generator_visualizer = []
                self.current_time_visualizer = []
                self.phase_visualizer = []
                marker_cfg = GREEN_ARROW_X_MARKER_CFG.copy()
                marker_cfg.prim_path = '/Visuals/orientation'
                marker_cfg.markers['arrow'].scale = (0.1, 0.2, 0.2)
                self.orientation_visualizer = VisualizationMarkers(marker_cfg)
                for i in range(self._env.num_feet):
                    marker_cfg = CYLINDER_TIME_MARKER_CFG.copy()
                    marker_cfg.prim_path = '/Visuals/timing_foot_' + str(i)
                    marker_cfg.markers['current_time'].scale = (0.05, 0.05, 1.0)
                    self.current_time_visualizer.append(VisualizationMarkers(marker_cfg))
                    marker_cfg = BLUE_ARROW_X_MARKER_CFG.copy()
                    marker_cfg.prim_path = '/Visuals/phase_' + str(i)
                    marker_cfg.markers['arrow'].scale = (0.1, 0.1, 0.3)
                    self.phase_visualizer.append(VisualizationMarkers(marker_cfg))
                    contact_generator_visualizer_per_foot = []
                    for j in range(self._contact_max_index[i]):
                        if self._contact_mode[i, j] > 0.5:
                            marker_cfg = CYLINDER_STANCE_MARKER_CFG.copy()
                        elif self._contact_mode[i, j] < -0.5:
                            marker_cfg = CYLINDER_SWING_MARKER_CFG.copy()
                        else:
                            marker_cfg = CYLINDER_PHASE_MARKER_CFG.copy()
                        marker_cfg.prim_path = '/Visuals/contact_plan_foot_' + str(i) + '_mode' + str(j)
                        marker_cfg.markers['contact_plan'].scale = (0.04, 0.04, self._contact_timing_percentage[i, j] * 0.2)
                        contact_generator_visualizer_per_foot.append(VisualizationMarkers(marker_cfg))
                    self.contact_generator_visualizer.append(contact_generator_visualizer_per_foot)
            for i in range(len(self.current_time_visualizer)):
                self.current_time_visualizer[i].set_visibility(True)
            for i in range(len(self.phase_visualizer)):
                self.phase_visualizer[i].set_visibility(True)
            for i in range(len(self.contact_generator_visualizer)):
                for j in range(len(self.contact_generator_visualizer[i])):
                    self.contact_generator_visualizer[i][j].set_visibility(True)
            self.orientation_visualizer.set_visibility(True)
        elif hasattr(self, 'contact_generator_visualizer'):
            for i in range(len(self.current_time_visualizer)):
                self.current_time_visualizer[i].set_visibility(False)
            for i in range(len(self.phase_visualizer)):
                self.phase_visualizer[i].set_visibility(False)
            for i in range(len(self.contact_generator_visualizer)):
                for j in range(len(self.contact_generator_visualizer[i])):
                    self.contact_generator_visualizer[i][j].set_visibility(False)
            self.orientation_visualizer.set_visibility(False)

    def _contact_generator_vis_callback(self, event):
        arrow_pos_w = self._env._robot.data.root_link_pos_w.torch.clone()
        arrow_pos_w[:, 2] += 1.0
        offset_mode = np.array([[0.2, 0.2, 0.0], [0.2, -0.2, 0.0], [-0.2, 0.2, 0.0], [-0.2, -0.2, 0.0]])
        offset_phase = np.array([[0.1, 0.1, 0.0], [0.1, -0.1, 0.0], [-0.1, 0.1, 0.0], [-0.1, -0.1, 0.0]])
        self.orientation_visualizer.visualize(arrow_pos_w)
        for i in range(4):
            pos_w = arrow_pos_w.clone()
            pos_w[:, 0] += offset_mode[i, 0]
            pos_w[:, 1] += offset_mode[i, 1]
            pos_w_time = pos_w.clone()
            scale_time = torch.clip(self._time_since_reset / self._contact_timing_total[i], max=1.0) / 5.0
            pos_w_time[:, 2] += scale_time / 2.0
            scale_time = torch.cat((torch.ones_like(scale_time).unsqueeze(1), torch.ones_like(scale_time).unsqueeze(1), scale_time.unsqueeze(1)), dim=1)
            self.current_time_visualizer[i].visualize(pos_w_time, scales=scale_time)
            pow_w_phase = pos_w.clone()
            pow_w_phase[:, 0] += offset_phase[i, 0]
            pow_w_phase[:, 1] += offset_phase[i, 1]
            pitch = self._current_contact_phase[:, i] * 2.0 * np.pi
            quat = math_utils.quat_from_euler_xyz(torch.zeros_like(pitch), pitch, torch.zeros_like(pitch))
            in_phase = torch.logical_and(self._current_contact_mode[:, i] < 0.5, self._current_contact_mode[:, i] > -0.5)
            scale_phase = torch.cat((torch.ones_like(in_phase).unsqueeze(1), torch.ones_like(in_phase).unsqueeze(1), in_phase.unsqueeze(1)), dim=1)
            self.phase_visualizer[i].visualize(pow_w_phase, quat, scales=scale_phase)
            for j in range(self._contact_max_index[i]):
                pos_w_contact = pos_w.clone()
                if j == 0:
                    pos_w_contact[:, 2] += self._contact_timing_percentage[i][j] * 0.1
                elif j > 0:
                    pos_w_contact[:, 2] += self._contact_timing_cumsum_percentage[i][j - 1] * 0.2 + 0.1 * self._contact_timing_percentage[i][j]
                self.contact_generator_visualizer[i][j].visualize(pos_w_contact)
