import torch
from . import math as math_utils

@torch.jit.script
def motor_angles_from_foot_positions_fl(foot_local_positions, hip_offset, link_lengths, device: str='cuda'):
    foot_positions_in_hip_frame = foot_local_positions - hip_offset[0]
    l_hip = link_lengths[0]
    l_up = link_lengths[1]
    l_low = link_lengths[2]
    x = foot_positions_in_hip_frame[:, 0]
    y = foot_positions_in_hip_frame[:, 1]
    z = foot_positions_in_hip_frame[:, 2]
    theta_calf = -torch.arccos(torch.clip((x ** 2 + y ** 2 + z ** 2 - l_hip ** 2 - l_low ** 2 - l_up ** 2) / (2 * l_low * l_up), -1, 1))
    l = torch.sqrt(torch.clip(l_up ** 2 + l_low ** 2 + 2 * l_up * l_low * torch.cos(theta_calf), 1e-07, 1))
    theta_thigh = torch.arcsin(torch.clip(-x / l, -1, 1)) - theta_calf / 2
    c1 = l_hip * y - l * torch.cos(theta_thigh + theta_calf / 2) * z
    s1 = l * torch.cos(theta_thigh + theta_calf / 2) * y + l_hip * z
    theta_hip = torch.arctan2(s1, c1)
    joint_angles = torch.stack([theta_hip[:, None], theta_thigh[:, None], theta_calf[:, None]], dim=-1)
    return math_utils.wrap_to_pi(joint_angles.reshape((-1, 3)))

@torch.jit.script
def motor_angles_from_foot_positions(foot_local_positions, hip_offset, link_lengths, device: str='cuda'):
    foot_positions_in_hip_frame = foot_local_positions - hip_offset
    l_hip = link_lengths[0] * torch.tensor([1, -1, 1, -1], device=device)
    l_up = link_lengths[1]
    l_low = link_lengths[2]
    x = foot_positions_in_hip_frame[:, :, 0]
    y = foot_positions_in_hip_frame[:, :, 1]
    z = foot_positions_in_hip_frame[:, :, 2]
    theta_calf = -torch.arccos(torch.clip((x ** 2 + y ** 2 + z ** 2 - l_hip ** 2 - l_low ** 2 - l_up ** 2) / (2 * l_low * l_up), -1, 1))
    l = torch.sqrt(torch.clip(l_up ** 2 + l_low ** 2 + 2 * l_up * l_low * torch.cos(theta_calf), 1e-07, 1))
    theta_thigh = torch.arcsin(torch.clip(-x / l, -1, 1)) - theta_calf / 2
    c1 = l_hip * y - l * torch.cos(theta_thigh + theta_calf / 2) * z
    s1 = l * torch.cos(theta_thigh + theta_calf / 2) * y + l_hip * z
    theta_hip = torch.arctan2(s1, c1)
    joint_angles = torch.stack([theta_hip[:, 0, None], theta_hip[:, 1, None], theta_hip[:, 2, None], theta_hip[:, 3, None], theta_thigh[:, 0, None], theta_thigh[:, 1, None], theta_thigh[:, 2, None], theta_thigh[:, 3, None], theta_calf[:, 0, None], theta_calf[:, 1, None], theta_calf[:, 2, None], theta_calf[:, 3, None]], dim=-1)
    return math_utils.wrap_to_pi(joint_angles.reshape((-1, 12)))
