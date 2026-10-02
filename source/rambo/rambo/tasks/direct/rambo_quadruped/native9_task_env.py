"""Shared fixed native9 task runtime without cross-task inheritance.

Push Box, Lift Basket and Press Button supply only their own assets/predicates.
The retained RAMBO controller remains in QPEnv.
"""
from __future__ import annotations
from collections.abc import Sequence
import copy
import numpy as np
import torch
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from rambo.utils.physx import assert_physx_environment
from rambo.tasks.common.episode import EpisodeRuntime
from rambo.tasks.common.snapshots import capture_state, capture_rgb
from .qp_env import QPEnv, QPEnvCfg


@configclass
class Native9TaskCfg(QPEnvCfg):
    """Retained deterministic Go2/FL/controller and mounted-camera settings."""

    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=1,
        env_spacing=10.0,
        replicate_physics=True,
    )
    episode_length_s = 300.0
    randomize_episode_progress = False
    randomize_initial_state = False
    enable_sampled_velocity_commands = False
    enable_sampled_pos_commands = False
    enable_sampled_force_commands = False
    obs_noise = False
    events = None

    qp_torque_optimizer_config = {
        "qp_debug_vis": False,
        "base_position_kp": np.array([50.0, 50.0, 50.0]),
        "base_position_kd": np.array([10.0, 10.0, 10.0]),
        "base_orientation_kp": np.array([50.0, 50.0, 50.0]),
        "base_orientation_kd": np.array([10.0, 10.0, 10.0]),
        "qp_weight_ddq": np.diag([1.0, 1.0, 1.0, 1.0, 1.0, 1.0]),
        "qp_weight_grf": 1e-4,
        "qp_weight_ee_force": 1.0,
        "qp_foot_friction_coef": 0.6,
    }
    velocity_debug_vis = False
    pos_debug_vis = False
    force_debug_vis = False

    # FL becomes the manipulator after one second; the remaining three legs
    # retain the checkpoint-compatible walking contact phases.
    contact_generator_config = {
        "contact_generator_debug_vis": False,
        "contact_sequence": {
            "FL": [["stance", 1.0, 0.0, 0.0, 0.0], ["swing", 299.0, 0.0, 0.0, 0.0]],
            "FR": [["stance", 1.0, 0.0, 0.0, 0.0], ["phase", 299.0, 0.0, 0.7, 0.8]],
            "RL": [["stance", 1.0, 0.0, 0.0, 0.0], ["phase", 299.0, 0.33, 0.7, 0.8]],
            "RR": [["stance", 1.0, 0.0, 0.0, 0.0], ["phase", 299.0, 0.67, 0.7, 0.8]],
        },
    }

    ee_default_command = (0.1934, 0.142, 0.05)
    # Compatibility camera profile name, independent of the active task predicate.
    task_kind = 'lift_basket'
    lift_camera_setup = None
    primary_position = (0.75, 0.15, 0.02)
    primary_orientation = (0., 0., 0., 1.)
    approved_asset_path = ''
    approved_profile = None
    pilot_max_physics_steps = 5000


class Native9TaskEnv(QPEnv):
    cfg: Native9TaskCfg

    def __init__(self, cfg, render_mode=None, **kwargs):
        self._episode_runtime = EpisodeRuntime()
        super().__init__(cfg, render_mode, **kwargs)
        self._physx_evidence = assert_physx_environment(self)
        self._primary_rest_pose = self.primary_pose_w.clone()
        self._primary_rest_vel = self._primary.data.default_root_vel.torch.clone()
        self._success = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)

    def _setup_task_assets(self):
        if self.scene.cfg.num_envs != 1:
            raise ValueError('Current native9 tasks support exactly one environment')

    def _setup_post_clone_task_assets(self):
        self._root = '/World/envs/env_0/LingBotTask'
        self._spawn_task_asset()
        if getattr(self.cfg, 'lift_camera_setup', None) == 'robot-dual-v3':
            from rambo.tasks.common.lift_camera_rig import spawn
            spawn(self)

    def _resolve_loco_manip_env_ids(
        self, env_ids: Sequence[int] | torch.Tensor | None
    ) -> torch.Tensor:
        """Normalize public command target indices without using QP internals."""

        if env_ids is None:
            return torch.arange(self.num_envs, dtype=torch.long, device=self.device)
        value = torch.as_tensor(env_ids, dtype=torch.long, device=self.device)
        if value.ndim != 1 or value.numel() != torch.unique(value).numel():
            raise ValueError("env_ids must be a one-dimensional unique index vector")
        if bool(torch.any(value < 0)) or bool(torch.any(value >= self.num_envs)):
            raise IndexError("env_ids are outside the active environment range")
        return value

    def set_loco_manip_commands(
        self,
        base_velocity: torch.Tensor,
        fl_position: torch.Tensor,
        fl_force: torch.Tensor,
        env_ids: Sequence[int] | torch.Tensor | None = None,
    ) -> None:
        """Set the unchanged public 9D command interface for one or more envs."""

        indices = self._resolve_loco_manip_env_ids(env_ids)
        expected = (indices.numel(), 3)
        for name, command, storage in (
            ("base_velocity", base_velocity, self._velocity_commands),
            ("fl_position", fl_position, self._ee_pos_commands),
            ("fl_force", fl_force, self._ee_force_commands),
        ):
            if not isinstance(command, torch.Tensor) or tuple(command.shape) != expected:
                raise ValueError(f"{name} must have shape {expected}")
            if command.device != storage.device or command.dtype != storage.dtype:
                raise ValueError(f"{name} must use {storage.dtype} on {storage.device}")
            if not bool(torch.isfinite(command).all()):
                raise ValueError(f"{name} contains NaN or Inf")
            storage.index_copy_(0, indices, command)

    @property
    def manipulator_ready(self) -> torch.Tensor:
        """Report when the FL contact schedule has entered swing/manipulation."""

        return self.contact_generator.desired_contact_mode[:, 0] <= -0.5

    @property
    def primary_pose_w(self) -> torch.Tensor:
        return torch.cat(
            (
                self._primary.data.root_link_pos_w.torch,
                self._primary.data.root_link_quat_w.torch,
            ),
            dim=-1,
        ).clone()

    @property
    def primary_velocity_w(self) -> torch.Tensor:
        return torch.cat(
            (
                self._primary.data.root_link_lin_vel_w.torch,
                self._primary.data.root_link_ang_vel_w.torch,
            ),
            dim=-1,
        ).clone()

    @property
    def task_success(self) -> torch.Tensor:
        return self._success.clone()

    @property
    def episode_clock(self):
        return self._episode_runtime.clock

    @property
    def episode_tick(self):
        return self.episode_clock.tick(int(self._sim_step_counter))

    @property
    def simulation_time_ns(self):
        return self.episode_clock.time_ns(int(self._sim_step_counter))

    @property
    def task_outcome(self):
        return self._episode_runtime.outcome

    @property
    def terminal_snapshot(self):
        return self._episode_runtime.terminal

    @property
    def current_command_confirmation(self):
        return copy.deepcopy(self._episode_runtime.current_command)

    @property
    def executed_command_history(self):
        return self._episode_runtime.history

    @property
    def fallen(self):
        return (self.base_height < .1) | (torch.linalg.vector_norm(
            self.projected_gravity_b-torch.tensor([0.,0.,-1.],device=self.device),dim=-1) > .75)

    def actual_fl_world(self):
        from isaaclab.utils.math import quat_apply
        point=quat_apply(self.base_quat,self.ee_pos_b[:,0])+self.base_pos_w
        return point[0].detach().cpu().numpy().copy()

    def submit_native9_command(self, prepared):
        self._episode_runtime.submit(prepared, int(self._sim_step_counter))
        cmd=torch.as_tensor([prepared['filtered']],device=self.device,dtype=torch.float32)
        self.set_loco_manip_commands(cmd[:,:3],cmd[:,3:6],cmd[:,6:])

    def _validate_episode_command(self):
        row=self._episode_runtime.current_command
        if row is None:
            return
        held=torch.cat((self._velocity_commands[0],self._ee_pos_commands[0],self._ee_force_commands[0]))
        expected=torch.as_tensor(row['filtered'],device=held.device,dtype=held.dtype)
        if not torch.equal(held,expected):
            raise ValueError('Runtime native9 command differs from submitted execution values')

    def _confirm_episode_control(self):
        self._episode_runtime.confirm_control(int(self._sim_step_counter))

    def _finish_task_outcome(self, success, fallen):
        self._success=torch.full_like(fallen,success)
        timed_out=self.episode_tick>=self.cfg.pilot_max_physics_steps
        self._episode_runtime.set_outcome(success=bool(success),fallen=bool(fallen[0]),timed_out=timed_out)
        timeout=torch.full_like(fallen,timed_out)
        return fallen|self._success,timeout&~self._success

    def capture_terminal_snapshot(self):
        rgb,hashes,frames=capture_rgb(self)
        outcome=self.task_outcome
        snapshot=dict(simulation_time_ns=self.simulation_time_ns,physics_step=self.episode_tick,
                      reset_epoch=self.episode_clock.reset_epoch,state=capture_state(self),
                      task_review=self.review_diagnostics(),rgb=rgb,rgb_hashes=hashes,
                      sensor_frame_ids=frames,reason=outcome['termination_reason'],
                      partial_interval=self.episode_tick%10!=0,
                      executed_history=self.executed_command_history,
                      command_confirmation=copy.deepcopy(self._episode_runtime.current_command),**outcome)
        self._episode_runtime.seal_terminal(snapshot)
        return self.terminal_snapshot

    @property
    def task_metrics(self):
        # Scalar task diagnostics remain evaluator-private.
        diagnostics=self.review_diagnostics()
        return {key:torch.as_tensor([value],device=self.device)
                for key,value in diagnostics.items() if isinstance(value,(int,float,bool))}

    def _reset_idx(self, env_ids):
        super()._reset_idx(env_ids)
        self._episode_runtime.reset(int(self._sim_step_counter))
        if hasattr(self,'_success_hold'):
            self._success_hold.reset()
        # Expert state is separate from the policy-visible history.
        for key in (
            '_expert_start_world','_expert_stage','_expert_push_start','_expert_finish_start',
            '_expert_finish_base','_expert_finish_foot','_expert_lateral_comp','_corner_recovery',
            '_lift_phase','_lift_phase_start','_lift_anchor','_lift_start_target','_lift_body_goal',
            '_lift_comp','_lift_through_count','_lift_near_seen','_lift_raise_progress',
            '_press_expert','_press_integral',
        ):
            if hasattr(self,key):
                delattr(self,key)
        self._expert_diagnostics=None
        if not hasattr(self,'_primary_rest_pose'):
            return
        if env_ids is None:
            env_ids=torch.arange(self.num_envs,dtype=torch.long,device=self.device)
        env_ids=torch.as_tensor(env_ids,dtype=torch.long,device=self.device)
        sim_env_ids=env_ids.to(dtype=torch.int32)
        self._primary.reset(env_ids=env_ids)
        self._primary.write_root_pose_to_sim_index(
            root_pose=self._primary_rest_pose.index_select(0,env_ids),env_ids=sim_env_ids)
        self._primary.write_root_velocity_to_sim_index(
            root_velocity=self._primary_rest_vel.index_select(0,env_ids),env_ids=sim_env_ids)
        self._success[env_ids]=False
        default=torch.as_tensor(self.cfg.ee_default_command,dtype=self._ee_pos_commands.dtype,
                                device=self.device).expand(env_ids.numel(),-1)
        zeros=torch.zeros((env_ids.numel(),3),dtype=self._velocity_commands.dtype,device=self.device)
        self.set_loco_manip_commands(zeros,default,zeros,env_ids=env_ids)
