"""Original residual/QP/smoothing and observation ordering, shared by backends."""
import torch

def prepare_control_targets(self, action, default_root_pose):
    scaled_action = action * self.action_scale.unsqueeze(0)
    scaled_action = torch.clip(scaled_action, -self.action_scale.unsqueeze(0) * 2, self.action_scale.unsqueeze(0) * 2)
    self.torque_optimizer.desired_base_position = default_root_pose[:, 0:3]
    self.torque_optimizer.desired_base_orientation_quat = default_root_pose[:, 3:7]
    self.torque_optimizer.desired_linear_velocity = torch.stack((self._velocity_commands[:, 0], self._velocity_commands[:, 1], torch.zeros_like(self._velocity_commands[:, 1])), dim=1)
    self.torque_optimizer.desired_angular_velocity = torch.stack((torch.zeros_like(self._velocity_commands[:, 2]), torch.zeros_like(self._velocity_commands[:, 2]), self._velocity_commands[:, 2]), dim=1)
    if self.cfg.including_base_action:
        self.torque_optimizer.desired_linear_acceleration = scaled_action[:, 0:3]
        self.torque_optimizer.desired_angular_acceleration = scaled_action[:, 3:6]
        if self.cfg.including_joint_action:
            desired_motor_position = self._desired_joint_pos + scaled_action[:, 6:]
        else:
            desired_motor_position = self._desired_joint_pos
    else:
        self.torque_optimizer.desired_linear_acceleration = torch.zeros_like(self.torque_optimizer.desired_linear_acceleration)
        self.torque_optimizer.desired_angular_acceleration = torch.zeros_like(self.torque_optimizer.desired_angular_acceleration)
        if self.cfg.including_joint_action:
            desired_motor_position = self._desired_joint_pos + scaled_action
        else:
            desired_motor_position = self._desired_joint_pos
    desired_motor_position = torch.clamp(desired_motor_position, self.default_joint_pos_limits[:, :, 0] + self.cfg.joint_pos_limit_margin, self.default_joint_pos_limits[:, :, 1] - self.cfg.joint_pos_limit_margin)
    if self.cfg.add_feedforward_torque:
        grf, qp_cost, _, _ = self.torque_optimizer.get_grf()
        stance_motor_torques = -torch.bmm(grf[:, None, :], self.all_foot_jacobian)[:, 0]
        if self.cfg.gravity_compensation_torque_for_swing_legs:
            swing_motor_torques = self.get_gravity_compensation_torques()
        else:
            swing_motor_torques = torch.zeros_like(stance_motor_torques)
        if self.cfg.use_actual_contact:
            contact_state_expanded = torch.tile(self.foot_contacts, (1, 3))
        else:
            contact_state_expanded = torch.tile(self.contact_generator.desired_contact_state, (1, 3))
        contact_state_expanded[:, 0] = 1.0
        contact_state_expanded[:, 4] = 1.0
        contact_state_expanded[:, 8] = 1.0
        desired_joint_torque = swing_motor_torques + torch.where(contact_state_expanded, stance_motor_torques, torch.zeros_like(stance_motor_torques))
    else:
        qp_cost = torch.zeros(self.num_envs, device=self.device)
        desired_joint_torque = torch.zeros_like(desired_motor_position)
    desired_joint_torque = torch.clamp(desired_joint_torque, -self.joint_torque_limit, self.joint_torque_limit)
    self.desired_pos = self.cfg.pos_alpha * desired_motor_position + (1 - self.cfg.pos_alpha) * self.desired_pos
    self.desired_vel = torch.zeros_like(self.joint_vel)
    self.desired_tor = self.cfg.tor_alpha * desired_joint_torque + (1 - self.cfg.tor_alpha) * self.desired_tor
    reset_env_ids = self.reset_buf.nonzero(as_tuple=False).squeeze(-1)
    if len(reset_env_ids) > 0:
        self.desired_pos[reset_env_ids] = desired_motor_position[reset_env_ids]
        self.desired_vel[reset_env_ids] = torch.zeros_like(self.joint_vel[reset_env_ids])
        self.desired_tor[reset_env_ids] = desired_joint_torque[reset_env_ids]
    return qp_cost

def update_observations(self) -> dict:
    latest_obs = torch.cat((self.base_height.unsqueeze(-1), self.projected_gravity_b, self.base_lin_vel_b, self.base_ang_vel_b, self.joint_pos - self.default_joint_pos, self.joint_vel, self.contact_generator.desired_contact_phase, self.contact_generator.desired_contact_mode, self._desired_joint_pos - self.default_joint_pos, self._velocity_commands, self._ee_pos_commands, self._ee_force_commands, self._last_action), dim=-1)
    if self.cfg.history_length > 1:
        self._obs_history = torch.cat((self._obs_history[:, 1:], latest_obs.unsqueeze(1)), dim=1)
    else:
        self._obs_history = latest_obs.unsqueeze(1)
    return {'policy': self._obs_history.view(self.num_envs, -1)}
