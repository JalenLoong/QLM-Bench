"""Numerical RAMBO implementation extracted from the retained source; no simulator imports."""
import torch
import numpy as np
from . import math as math_utils
from .math import quat_error as rambo_quat_error, xyzw_to_wxyz
from .tensor import to_torch
class JointPositionController:

    def __init__(self, env):
        self._env = env
        self._desired_foot_clearance = self._env.cfg.joint_position_controller_config['desired_foot_clearance']
        self._desired_foot_height = self._env.cfg.joint_position_controller_config['desired_foot_height']
        self._desired_joint_pos_stance = torch.stack([torch.tensor(self._env.cfg.joint_position_controller_config['desired_joint_pos_stance'], device=self._env.device, dtype=torch.float32)] * self._env.num_envs, dim=0)
        self._desired_joint_pos_swing = torch.stack([torch.tensor(self._env.cfg.joint_position_controller_config['desired_joint_pos_swing'], device=self._env.device, dtype=torch.float32)] * self._env.num_envs, dim=0)
        self._hip_positions_in_body_frame = torch.stack([torch.tensor(self._env.cfg.joint_position_controller_config['hip_positions_in_body_frame'], device=self._env.device, dtype=torch.float32)] * self._env.num_envs, dim=0)
        self._current_contact_state = torch.ones_like(self._env.contact_generator.desired_contact_state)
        self._desired_contact_state = self._env.contact_generator.desired_contact_state
        self._desired_contact_phase = self._env.contact_generator.desired_contact_phase
        self._desired_contact_mode = self._env.contact_generator.desired_contact_mode
        self._phase_switch_foot_positions = torch.matmul(self._env.base_rot_mat_rp, self._env.ee_pos_b.transpose(1, 2)).transpose(1, 2)
        self._phase_switch_foot_positions[:, :, 2] += self._env.base_height.unsqueeze(-1)
        self._desired_foot_positions = torch.zeros_like(self._phase_switch_foot_positions)
        self._desired_joint_positions = torch.zeros_like(self._desired_joint_pos_stance)
        self._bezier_num_points = 10
        self._bezier_trajectories = torch.zeros(self._env.num_envs, 4, self._bezier_num_points, 3, device=self._env.device)
        self._phase_switch_foot_positions_w = torch.zeros_like(self._phase_switch_foot_positions)
        self._desired_foot_positions_w = torch.zeros_like(self._desired_foot_positions)
        self._bezier_trajectories_w = torch.zeros_like(self._bezier_trajectories)
        self.debug_vis = False
        self.joint_position_controller_vis_handle = None

    def reset_idx(self, env_ids):
        self._desired_contact_state[env_ids] = self._env.contact_generator.desired_contact_state[env_ids]
        self._desired_contact_phase[env_ids] = self._env.contact_generator.desired_contact_phase[env_ids]
        self._desired_contact_mode[env_ids] = self._env.contact_generator.desired_contact_mode[env_ids]
        self._current_contact_state[env_ids] = self._env.foot_contacts[env_ids]
        self._phase_switch_foot_positions[env_ids] = torch.matmul(self._env.base_rot_mat_rp[env_ids], self._env.ee_pos_b[env_ids].transpose(1, 2)).transpose(1, 2)
        self._phase_switch_foot_positions[env_ids, :, 2] += self._env.base_height[env_ids].unsqueeze(-1)
        desired_contact_mode_expand = self._desired_contact_mode[env_ids].repeat(1, 3)
        desired_contact_state_expand = self._desired_contact_state[env_ids].repeat(1, 3)
        idx = desired_contact_mode_expand >= 0.5
        self._desired_joint_positions[env_ids] = torch.where(idx, self._desired_joint_pos_stance[env_ids], self._desired_joint_positions[env_ids])
        idx = desired_contact_mode_expand <= -0.5
        self._desired_joint_positions[env_ids] = torch.where(idx, self._desired_joint_pos_swing[env_ids], self._desired_joint_positions[env_ids])
        desired_FL_positions = self._env._ee_pos_commands[env_ids]
        d_fl_position = desired_FL_positions.clone()
        d_fl_position[:, 2] -= self._env.base_height[env_ids]
        fl_position_local = torch.matmul(self._env.base_rot_mat_rp_t[env_ids], d_fl_position.unsqueeze(-1)).squeeze(-1)
        desired_joint_position_fl = self._env.get_motor_angles_from_foot_positions_fl(fl_position_local)
        self._desired_joint_positions[env_ids, 0] = torch.where(idx[:, 0], desired_joint_position_fl[:, 0], self._desired_joint_positions[env_ids, 0])
        self._desired_joint_positions[env_ids, 4] = torch.where(idx[:, 4], desired_joint_position_fl[:, 1], self._desired_joint_positions[env_ids, 4])
        self._desired_joint_positions[env_ids, 8] = torch.where(idx[:, 8], desired_joint_position_fl[:, 2], self._desired_joint_positions[env_ids, 8])
        idx = torch.logical_and(desired_contact_mode_expand < 0.5, desired_contact_mode_expand > -0.5)
        self._desired_foot_positions[env_ids] = compute_desired_foot_positions(self._env.base_rot_mat_rp[env_ids], self._env.base_lin_vel_b[env_ids], self._env.base_ang_vel_b[env_ids], self._hip_positions_in_body_frame[env_ids], self._desired_foot_height, self._desired_foot_clearance, self._env.contact_generator.stance_duration[env_ids], self._env.contact_generator.normalized_phase[env_ids], self._phase_switch_foot_positions[env_ids])
        d_foot_position = self._desired_foot_positions[env_ids].clone()
        d_foot_position[:, :, 2] -= self._env.base_height[env_ids].unsqueeze(1)
        foot_position_local = torch.bmm(self._env.base_rot_mat_rp_t[env_ids], d_foot_position.transpose(1, 2)).transpose(1, 2)
        desired_joint_position_in_phase_s = self._env.get_motor_angles_from_foot_positions(foot_position_local)
        idx_c = torch.logical_and(idx, desired_contact_state_expand)
        self._desired_joint_positions[env_ids] = torch.where(idx_c, self._env.joint_pos[env_ids], self._desired_joint_positions[env_ids])
        idx_s = torch.logical_and(idx, torch.logical_not(desired_contact_state_expand))
        self._desired_joint_positions[env_ids] = torch.where(idx_s, desired_joint_position_in_phase_s, self._desired_joint_positions[env_ids])
        return self._desired_joint_positions[env_ids]

    def update(self):
        new_leg_state = self._env.foot_contacts
        new_foot_positions = torch.matmul(self._env.base_rot_mat_rp, self._env.ee_pos_b.transpose(1, 2)).transpose(1, 2)
        new_foot_positions[:, :, 2] += self._env.base_height.unsqueeze(-1)
        self._phase_switch_foot_positions = torch.where(torch.tile((self._current_contact_state == new_leg_state)[:, :, None], [1, 1, 3]), self._phase_switch_foot_positions, new_foot_positions)
        self._current_contact_state = new_leg_state
        self._desired_contact_state = self._env.contact_generator.desired_contact_state
        self._desired_contact_phase = self._env.contact_generator.desired_contact_phase
        self._desired_contact_mode = self._env.contact_generator.desired_contact_mode
        desired_contact_mode_expand = self._desired_contact_mode.repeat(1, 3)
        desired_contact_state_expand = self._desired_contact_state.repeat(1, 3)
        idx = desired_contact_mode_expand >= 0.5
        self._desired_joint_positions = torch.where(idx, self._desired_joint_pos_stance, self._desired_joint_positions)
        idx = desired_contact_mode_expand <= -0.5
        self._desired_joint_positions = torch.where(idx, self._desired_joint_pos_swing, self._desired_joint_positions)
        desired_FL_positions = self._env._ee_pos_commands
        d_fl_position = desired_FL_positions.clone()
        d_fl_position[:, 2] -= self._env.base_height
        fl_position_local = torch.matmul(self._env.base_rot_mat_rp_t, d_fl_position.unsqueeze(-1)).squeeze(-1)
        desired_joint_position_fl = self._env.get_motor_angles_from_foot_positions_fl(fl_position_local)
        self._desired_joint_positions[:, 0] = torch.where(idx[:, 0], desired_joint_position_fl[:, 0], self._desired_joint_positions[:, 0])
        self._desired_joint_positions[:, 4] = torch.where(idx[:, 4], desired_joint_position_fl[:, 1], self._desired_joint_positions[:, 4])
        self._desired_joint_positions[:, 8] = torch.where(idx[:, 8], desired_joint_position_fl[:, 2], self._desired_joint_positions[:, 8])
        idx = torch.logical_and(desired_contact_mode_expand < 0.5, desired_contact_mode_expand > -0.5)
        self._desired_foot_positions = compute_desired_foot_positions(self._env.base_rot_mat_rp, self._env.base_lin_vel_b, self._env.base_ang_vel_b, self._hip_positions_in_body_frame, self._desired_foot_height, self._desired_foot_clearance, self._env.contact_generator.stance_duration, self._env.contact_generator.normalized_phase, self._phase_switch_foot_positions)
        d_foot_position = self._desired_foot_positions.clone()
        d_foot_position[:, :, 2] -= self._env.base_height.unsqueeze(1)
        foot_position_local = torch.bmm(self._env.base_rot_mat_rp_t, d_foot_position.transpose(1, 2)).transpose(1, 2)
        desired_joint_position_in_phase_s = self._env.get_motor_angles_from_foot_positions(foot_position_local)
        idx_c = torch.logical_and(idx, desired_contact_state_expand)
        self._desired_joint_positions = torch.where(idx_c, self._env.joint_pos, self._desired_joint_positions)
        idx_s = torch.logical_and(idx, torch.logical_not(desired_contact_state_expand))
        self._desired_joint_positions = torch.where(idx_s, desired_joint_position_in_phase_s, self._desired_joint_positions)
        return self._desired_joint_positions

@torch.jit.script
def cubic_bezier_z(x0: torch.Tensor, x1: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
    progress = t ** 3 + 3 * t ** 2 * (1 - t)
    return x0 + progress * (x1 - x0)

@torch.jit.script
def cubic_bezier_xy(x0: torch.Tensor, x1: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
    progress = 2 * ((t / 2) ** 3 + 3 * (t / 2) ** 2 * (1 - t / 2))
    return x0 + progress * (x1 - x0)

@torch.jit.script
def cubic_bezier_xy_inv(x0: torch.Tensor, x1: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
    progress = 2 * ((t / 2 + 0.5) ** 3 + 3 * (t / 2 + 0.5) ** 2 * (1 - (t / 2 + 0.5)) - 0.5)
    return x0 + progress * (x1 - x0)

@torch.jit.script
def _gen_swing_foot_trajectory(input_phase: torch.Tensor, start_pos: torch.Tensor, mid_pos: torch.Tensor, end_pos: torch.Tensor) -> torch.Tensor:
    cutoff = 0.5
    input_phase_xy = torch.stack([input_phase] * 2, dim=-1)
    input_phase_z = input_phase
    xy = torch.where(input_phase_xy < cutoff, cubic_bezier_xy(start_pos[:, :, :2], mid_pos[:, :, :2], input_phase_xy / cutoff), cubic_bezier_xy_inv(mid_pos[:, :, :2], end_pos[:, :, :2], (input_phase_xy - cutoff) / (1 - cutoff)))
    z = torch.where(input_phase_z < cutoff, cubic_bezier_z(start_pos[:, :, 2], mid_pos[:, :, 2], input_phase_z / cutoff), cubic_bezier_z(mid_pos[:, :, 2], end_pos[:, :, 2], (input_phase_z - cutoff) / (1 - cutoff)))
    return torch.cat([xy, z.unsqueeze(-1)], dim=-1)

@torch.jit.script
def cross_quad(v1, v2):
    """Assumes v1 is nx3, v2 is nx4x3"""
    v1 = torch.stack([v1, v1, v1, v1], dim=1)
    shape = v1.shape
    v1 = v1.reshape((-1, 3))
    v2 = v2.reshape((-1, 3))
    return torch.linalg.cross(v1, v2).reshape((shape[0], shape[1], 3))

@torch.jit.script
def compute_desired_foot_positions(base_rot_mat_rp, base_velocity_body_frame, base_angular_velocity_body_frame, hip_positions_in_body_frame, desired_foot_height: float, desired_foot_clearance: float, stance_duration, normalized_phase, phase_switch_foot_positions):
    hip_position = torch.matmul(base_rot_mat_rp, hip_positions_in_body_frame.transpose(1, 2)).transpose(1, 2)
    mid_position = torch.clone(hip_position)
    mid_position[..., 2] = desired_foot_height
    base_velocity_b = base_velocity_body_frame
    hip_velocity_b = base_velocity_b[:, None, :] + cross_quad(base_angular_velocity_body_frame, hip_positions_in_body_frame)
    hip_velocity = torch.matmul(base_rot_mat_rp, hip_velocity_b.transpose(1, 2)).transpose(1, 2)
    land_position = hip_velocity * stance_duration.unsqueeze(-1) / 2
    land_position[..., 0] = torch.clip(land_position[..., 0], -0.2, 0.2)
    land_position[..., 1] = torch.clip(land_position[..., 1], -0.2, 0.2)
    land_position += hip_position
    land_position[..., 2] = desired_foot_clearance
    switch_foot_position = phase_switch_foot_positions.clone()
    switch_foot_position[:, :, 2] += desired_foot_clearance
    foot_position = _gen_swing_foot_trajectory(normalized_phase, switch_foot_position, mid_position, land_position)
    return foot_position
