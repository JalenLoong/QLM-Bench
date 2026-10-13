"""Fixed RAMBO controller driven by explicit tensor robot state, without a simulator."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import hashlib

import numpy as np
import torch
from torch import nn

from . import math
from .kinematics import motor_angles_from_foot_positions, motor_angles_from_foot_positions_fl
from .contact_generator import ContactGenerator
from .joint_position_controller import JointPositionController
from .qp_torque_optimizer import QPTorqueOptimizer
from .control import prepare_control_targets, update_observations
from .random import CaseRandomStreams

JOINT_ORDER = tuple(f"{leg}_{joint}_joint" for joint in ("hip", "thigh", "calf")
                    for leg in ("FL", "FR", "RL", "RR"))
BODY_ORDER = ("base",) + tuple(f"{leg}_{part}" for part in ("hip", "thigh", "calf", "foot")
                              for leg in ("FL", "FR", "RL", "RR"))
CHECKPOINT_SHA256 = "1cc5f68fe15e37ccabae26060d79a26a8c078ed465a81f6f729c2009b67ca706"


def controller_config():
    """Retained Native9TaskCfg and QPEnvCfg numerical contract; no backend config."""
    sequence = {"FL": [["stance", 1., 0., 0., 0.], ["swing", 299., 0., 0., 0.]]}
    sequence.update({leg: [["stance", 1., 0., 0., 0.], ["phase", 299., phase, .7, .8]]
                     for leg, phase in (("FR", 0.), ("RL", .33), ("RR", .67))})
    return SimpleNamespace(
        history_length=5, contact_generator_config={"contact_sequence": sequence,
                                                   "contact_generator_debug_vis": False},
        joint_position_controller_config={"joint_position_controller_debug_vis": False,
            "desired_joint_pos_stance": np.array([0.] * 4 + [.8] * 4 + [-1.5] * 4),
            "desired_joint_pos_swing": np.array([0.] * 4 + [1.1] * 4 + [-2.2] * 4),
            "desired_foot_clearance": 0., "desired_foot_height": .15,
            "hip_positions_in_body_frame": np.array([[.1934,.142,0.],[.1934,0.,0.],
                                                      [-.1934,.142,0.],[-.1934,-.142,0.]])},
        qp_torque_optimizer_config={"qp_debug_vis": False, "base_position_kp": np.array([50.] * 3),
            "base_position_kd": np.array([10.] * 3), "base_orientation_kp": np.array([50.] * 3),
            "base_orientation_kd": np.array([10.] * 3), "qp_weight_ddq": np.eye(6),
            "qp_weight_grf": 1e-4, "qp_weight_ee_force": 1., "qp_foot_friction_coef": .6},
        including_base_action=True, including_joint_action=True, joint_pos_limit_margin=.1,
        add_feedforward_torque=True, gravity_compensation_torque_for_swing_legs=True,
        use_actual_contact=False, pos_alpha=.5, tor_alpha=.5)


class FrozenActor(nn.Module):
    """Exact CRL2 deterministic ELU actor and empirical normalization inference."""
    def __init__(self, checkpoint, device):
        super().__init__()
        path = Path(checkpoint)
        if hashlib.sha256(path.read_bytes()).hexdigest() != CHECKPOINT_SHA256:
            raise ValueError("RAMBO checkpoint differs from the fixed quadruped policy")
        saved = torch.load(path, map_location=device, weights_only=False)
        if saved.get("iteration") != 2000 or saved.get("obs_normalizer_count") != 100003840:
            raise ValueError("RAMBO checkpoint iteration/normalizer identity mismatch")
        # Constructor initialization is overwritten by the strict checkpoint.
        # It must not consume a caller's random stream or affect case sampling.
        with torch.random.fork_rng(devices=[]):
            self.policy_latent_net = nn.Sequential(nn.Linear(405,512), nn.ELU(), nn.Linear(512,256),
                                                   nn.ELU(), nn.Linear(256,128), nn.ELU())
            self.action_mean_net = nn.Linear(128,18)
        self.log_std = nn.Parameter(torch.zeros(18))
        self.to(device).load_state_dict(saved["policy_dict"], strict=True)
        self.register_buffer("mean", saved["obs_normalizer"]["_mean"].to(device))
        self.register_buffer("std", saved["obs_normalizer"]["_std"].to(device))
        self.eval().requires_grad_(False)

    def forward(self, observations):
        return self.action_mean_net(self.policy_latent_net((observations-self.mean)/(self.std+1e-2)))


class DelayedMotor:
    """Original delayed position/velocity/feedforward command and DCMotor saturation."""
    def __init__(self, count, device, random_streams=None):
        self.count, self.device = count, device
        self.random_streams=random_streams
        self.history = torch.zeros((11,count,3,12), device=device)
        self.lags = torch.zeros((count,12), dtype=torch.long, device=device)
        self.age = torch.zeros(count, dtype=torch.long, device=device)
        self.cursor = 0
        self.effort = torch.tensor([21.33]*8+[40.887]*4, device=device)
        self.speed = torch.tensor([30.1]*8+[15.7]*4, device=device)

    def reset(self, ids):
        self.history[:,ids] = 0
        self.age[ids] = 0
        # Original calf then hip/thigh actuator groups sample one lag per world.
        if self.random_streams is None:
            self.lags[ids,8:] = torch.randint(0,11,(len(ids),1),device=self.device)
            self.lags[ids,:8] = torch.randint(0,11,(len(ids),1),device=self.device)
        else:
            sampled=self.random_streams.motor_delays(ids.tolist(),self.device)
            self.lags[ids,8:]=sampled[:,0,None];self.lags[ids,:8]=sampled[:,1,None]

    def compute(self, desired_pos, desired_vel, desired_effort, q, qd):
        value = torch.stack((desired_pos,desired_vel,desired_effort),dim=1)
        fresh = self.age == 0
        self.history[:,fresh] = value[fresh]
        self.history[self.cursor] = value
        lag = torch.minimum(self.lags,self.age[:,None])
        slots = (self.cursor-lag) % 11
        lanes = torch.arange(self.count,device=self.device)[:,None]
        joints = torch.arange(12,device=self.device)[None,:]
        delayed = torch.stack([self.history[slots,lanes,k,joints] for k in range(3)],dim=1)
        torque = 40.*(delayed[:,0]-q) + (delayed[:,1]-qd) + delayed[:,2]
        velocity = torch.clamp(qd,-2*self.speed,2*self.speed)
        upper = torch.minimum(self.effort*(1-velocity/self.speed), self.effort)
        lower = torch.maximum(self.effort*(-1-velocity/self.speed),-self.effort)
        self.cursor = (self.cursor+1) % 11
        self.age += 1
        return torch.clamp(torque,lower,upper)


class RAMBOCore:
    """Own controller state only; the supplied adapter owns robot state and physics."""
    def __init__(self, adapter, checkpoint, *, device="cpu", case_seeds=None):
        self.adapter, self.device = adapter, str(device)
        self.num_envs, self.num_feet = adapter.count, 4
        seeds=list(range(42,42+self.num_envs)) if case_seeds is None else list(case_seeds)
        if len(seeds)!=self.num_envs:raise ValueError('One case seed per robot lane required')
        self.case_rng=CaseRandomStreams(seeds)
        self.cfg = controller_config()
        tensor = lambda v: torch.as_tensor(v,device=self.device,dtype=torch.float32)
        self.hip_offset = tensor([[.1934,.0465,0.],[.1934,-.0465,0.],[-.1934,.0465,0.],[-.1934,-.0465,0.]])
        self.link_lengths = tensor([.0955,.213,.213])
        self.action_scale = tensor([5.]*6+[.15]*12)
        self.joint_torque_limit = tensor([23.7]*8+[45.43]*4)[None].repeat(self.num_envs,1)*.9
        self.default_joint_pos = tensor([0.]*4+[.8]*4+[-1.5]*4)[None].repeat(self.num_envs,1)
        self.default_joint_pos_limits = adapter.joint_limits.to(self.device)
        self.default_root_pose = tensor([0.,0.,.3,0.,0.,0.,1.])[None].repeat(self.num_envs,1)
        self._time_since_reset = torch.zeros(self.num_envs,device=self.device)
        self.control_ticks = torch.zeros(self.num_envs,dtype=torch.long,device=self.device)
        self._obs_history = torch.zeros((self.num_envs,5,81),device=self.device)
        self._last_action = torch.zeros((self.num_envs,18),device=self.device)
        self._velocity_commands = torch.zeros((self.num_envs,3),device=self.device)
        self._ee_pos_commands = tensor([.1934,.142,.05])[None].repeat(self.num_envs,1)
        self._ee_force_commands = torch.zeros_like(self._velocity_commands)
        self.desired_pos = self.default_joint_pos.clone()
        self.desired_vel = torch.zeros_like(self.desired_pos)
        self.desired_tor = torch.zeros_like(self.desired_pos)
        self._desired_joint_pos = torch.zeros_like(self.desired_pos)
        self.reset_buf = torch.ones(self.num_envs,dtype=torch.bool,device=self.device)
        self.refresh()
        self.contact_generator = ContactGenerator(self)
        self.joint_position_controller = JointPositionController(self)
        self.torque_optimizer = QPTorqueOptimizer(self)
        self.actor = FrozenActor(checkpoint,self.device)
        self.motor = DelayedMotor(self.num_envs,self.device,self.case_rng)
        self.reset(torch.arange(self.num_envs,device=self.device))

    def refresh(self):
        self.robot = self.adapter.read(self.device)

    def reset(self, ids, *, case_seeds=None):
        if ids.ndim!=1 or ids.dtype not in (torch.int32,torch.int64) or len(ids)!=len(torch.unique(ids)) or torch.any((ids<0)|(ids>=self.num_envs)):
            raise ValueError('Reset requires unique valid controller lane indices')
        if not len(ids):return self._obs_history.flatten(1).clone()
        if case_seeds is not None:self.case_rng.reset(ids.tolist(),case_seeds)
        untouched = torch.ones(self.num_envs,dtype=torch.bool,device=self.device)
        untouched[ids] = False
        previous_history = self._obs_history[untouched].clone()
        self.refresh()
        self._time_since_reset[ids] = 0
        self.control_ticks[ids] = 0
        self._obs_history[ids] = 0
        self._last_action[ids] = 0
        self._velocity_commands[ids] = 0
        self._ee_pos_commands[ids] = torch.tensor([.1934,.142,.05],device=self.device)
        self._ee_force_commands[ids] = 0
        self.desired_pos[ids] = self.default_joint_pos[ids]
        self.desired_vel[ids] = self.desired_tor[ids] = 0
        self.motor.reset(ids)
        self.contact_generator.reset_idx(ids)
        self._desired_joint_pos[ids] = self.joint_position_controller.reset_idx(ids)
        self.reset_buf[ids] = True
        update_observations(self)
        self._obs_history[untouched] = previous_history
        return self._obs_history.flatten(1)

    def submit(self, values):
        value = torch.as_tensor(values,dtype=torch.float32,device=self.device)
        if value.shape != (self.num_envs,9) or not torch.isfinite(value).all():
            raise ValueError("Finite native9 command per world required")
        self._velocity_commands[:] = value[:,:3]
        self._ee_pos_commands[:] = value[:,3:6]
        self._ee_force_commands[:] = 0

    @torch.no_grad()
    def begin_control(self):
        residual = self.actor(self._obs_history.flatten(1))
        if not torch.isfinite(residual).all():
            raise ValueError("Nonfinite RAMBO residual")
        prepare_control_targets(self,residual,self.default_root_pose)
        self.reset_buf[:] = False
        return residual

    def motor_effort(self):
        self.refresh()
        return self.motor.compute(self.desired_pos,self.desired_vel,self.desired_tor,
                                  self.joint_pos,self.joint_vel)

    def end_control(self, residual):
        self.refresh()
        self.control_ticks += 1
        self._time_since_reset = self.control_ticks * .002 * 5
        self.contact_generator.update()
        self._desired_joint_pos = self.joint_position_controller.update()
        self._last_action[:] = residual
        return update_observations(self)["policy"]

    @property
    def time_since_reset(self): return self._time_since_reset.clone()
    @property
    def joint_pos(self): return self.robot.q
    @property
    def joint_vel(self): return self.robot.qd
    @property
    def base_height(self): return self.robot.position[:,2]
    @property
    def base_quat(self): return self.robot.quaternion_xyzw
    @property
    def projected_gravity_b(self):
        return math.quat_apply_inverse(self.base_quat,torch.tensor([0.,0.,-1.],device=self.device).expand(self.num_envs,-1))
    @property
    def base_rot_mat_rp_t(self): return math.rp_rotation_from_gravity_b(self.projected_gravity_b)
    @property
    def base_rot_mat_rp(self): return self.base_rot_mat_rp_t.transpose(1,2)
    @property
    def base_quat_rp(self): return math.quat_from_matrix(self.base_rot_mat_rp)
    @property
    def base_lin_vel_b(self): return math.quat_apply_inverse(self.base_quat,self.robot.linear_velocity_world)
    @property
    def base_ang_vel_b(self): return math.quat_apply_inverse(self.base_quat,self.robot.angular_velocity_world)
    @property
    def foot_contacts(self): return self.robot.foot_contacts

    def get_motor_angles_from_foot_positions(self, value):
        return motor_angles_from_foot_positions(value,self.hip_offset,self.link_lengths,self.device)

    def get_motor_angles_from_foot_positions_fl(self, value):
        return motor_angles_from_foot_positions_fl(value,self.hip_offset,self.link_lengths,self.device)

    def get_gravity_compensation_torques(self): return self.robot.gravity_torque


    @property
    def ee_pos_b(self):
        theta_hip = self.joint_pos[:, 0:4]
        theta_thigh = self.joint_pos[:, 4:8]
        theta_knee = self.joint_pos[:, 8:12]
        l_hip = torch.tensor([1, -1, 1, -1], device=self.device) * self.link_lengths[0]
        l_up = self.link_lengths[1]
        l_low = self.link_lengths[2]
        leg_distance = torch.sqrt(l_up ** 2 + l_low ** 2 + 2 * l_up * l_low * torch.cos(theta_knee))
        eff_swing = theta_thigh + theta_knee / 2
        off_x_hip = -(leg_distance * torch.sin(eff_swing)).view(self.num_envs, 4)
        off_z_hip = -(leg_distance * torch.cos(eff_swing)).view(self.num_envs, 4)
        off_y_hip = l_hip.unsqueeze(0).repeat(self.num_envs, 1)
        off_x = off_x_hip
        off_y = torch.cos(theta_hip.view(self.num_envs, 4)) * off_y_hip - torch.sin(theta_hip.view(self.num_envs, 4)) * off_z_hip
        off_z = torch.sin(theta_hip.view(self.num_envs, 4)) * off_y_hip + torch.cos(theta_hip.view(self.num_envs, 4)) * off_z_hip
        ee_pos_hip = torch.stack([off_x, off_y, off_z], dim=2)
        cal_ee_pos_b = ee_pos_hip + self.hip_offset.unsqueeze(0)
        return cal_ee_pos_b

    @property
    def all_foot_jacobian(self):
        theta_hip = self.joint_pos[:, 0:4]
        theta_thigh = self.joint_pos[:, 4:8]
        theta_knee = self.joint_pos[:, 8:12]
        l_hip = torch.tensor([1, -1, 1, -1], device=self.device) * self.link_lengths[0]
        l_up = self.link_lengths[1]
        l_low = self.link_lengths[2]
        l_eff = torch.sqrt(l_up ** 2 + l_low ** 2 + 2 * l_up * l_low * torch.cos(theta_knee))
        t_eff = theta_thigh + theta_knee / 2
        J = torch.zeros((self.num_envs, 4, 3, 3), device=self.device)
        J[:, :, 0, 0] = 0
        J[:, :, 0, 1] = -l_eff * torch.cos(t_eff)
        J[:, :, 0, 2] = l_low * l_up * torch.sin(theta_knee) * torch.sin(t_eff) / l_eff - l_eff * torch.cos(t_eff) / 2
        J[:, :, 1, 0] = -l_hip * torch.sin(theta_hip) + l_eff * torch.cos(theta_hip) * torch.cos(t_eff)
        J[:, :, 1, 1] = -l_eff * torch.sin(theta_hip) * torch.sin(t_eff)
        J[:, :, 1, 2] = -l_low * l_up * torch.sin(theta_hip) * torch.sin(theta_knee) * torch.cos(t_eff) / l_eff - l_eff * torch.sin(theta_hip) * torch.sin(t_eff) / 2
        J[:, :, 2, 0] = l_hip * torch.cos(theta_hip) + l_eff * torch.sin(theta_hip) * torch.cos(t_eff)
        J[:, :, 2, 1] = l_eff * torch.sin(t_eff) * torch.cos(theta_hip)
        J[:, :, 2, 2] = l_low * l_up * torch.sin(theta_knee) * torch.cos(theta_hip) * torch.cos(t_eff) / l_eff + l_eff * torch.sin(t_eff) * torch.cos(theta_hip) / 2
        flattened_jacobian = torch.zeros((self.num_envs, 12, 12), device=self.device)
        flattened_jacobian[:, 0:3, [0, 4, 8]] = J[:, 0]
        flattened_jacobian[:, 3:6, [1, 5, 9]] = J[:, 1]
        flattened_jacobian[:, 6:9, [2, 6, 10]] = J[:, 2]
        flattened_jacobian[:, 9:12, [3, 7, 11]] = J[:, 3]
        return flattened_jacobian
