"""One fixed RAMBO execution path shared by native9 action providers.

Construct only after AppLauncher has initialized the accepted PhysX runtime.
This is controller inference, not learned high-level policy inference.
"""
from __future__ import annotations
import copy
from pathlib import Path
from typing import Callable

from .environment_factory import make_task_config, make_environment, TASK_IDS


class ControllerRuntime:
    def __init__(self, task_id: str, *, profile: dict, resource_root: str | Path,
                 checkpoint_path: str | Path | None = None, seed: int = 42,
                 episode_length_s: float = 24., view: str = 'third-person',
                 device: str = 'cuda:0', use_fabric: bool = True,
                 asset_id: str | None = None,
                 on_environment_ready: Callable[[ControllerRuntime], None] | None = None):
        import torch
        from crl2.algorithms import PPO
        from qlm_bench.assets import resolve_asset
        from rambo.utils.registry import load_cfg_from_registry
        from rambo.validation.checkpoints import contract_for_task, load_verified_checkpoint, restore_runner

        if task_id not in TASK_IDS:
            raise ValueError('Unsupported task')
        self.task_id = task_id
        self.cfg = make_task_config(task_id, profile=profile, resource_root=resource_root,
                                    seed=seed, episode_length_s=episode_length_s, view=view,
                                    device=device, use_fabric=use_fabric, asset_id=asset_id)
        self.env = make_environment(self.cfg, task_id=task_id)
        self.base_env = self.env.unwrapped
        if hasattr(self.base_env, 'configure_foot_geometry'):
            self.base_env.configure_foot_geometry()
        if on_environment_ready is not None:
            # Attach optional observer/Recorder before the accepted first reset.
            # The callback does not own physics advancement or episode reset.
            clock = (self.base_env.episode_clock.reset_epoch, self.base_env.episode_tick)
            on_environment_ready(self)
            if clock != (self.base_env.episode_clock.reset_epoch, self.base_env.episode_tick):
                raise ValueError('Environment-ready callback may only attach observation/recording components')
        # Match the accepted collector's order: reset/render before constructing
        # PPO. Actuator lag reset and PPO initialization both consume Torch RNG.
        self.reset()
        self.contract = contract_for_task(task_id)
        checkpoint = load_verified_checkpoint(checkpoint_path or resolve_asset('rambo-go2-controller', resource_root), self.contract)
        agent_cfg = load_cfg_from_registry(task_id, 'crl2_cfg_entry_point')
        agent_cfg['general']['num_envs'] = 1
        agent_cfg['seed'] = seed
        self.runner = PPO(task=task_id, env=self.env, agent_cfg=agent_cfg,
                          train=False, device=self.base_env.device)
        restore_runner(self.runner, checkpoint, load_values=False, verify=True)
        self.controller = self.runner.get_inference_policy(device=self.base_env.device)

    def reset(self):
        import torch
        # Actuator delay buffers can be inference tensors after a controller step.
        # Reset and sensor refresh must use the same execution context as stepping.
        with torch.inference_mode():
            self.observations, _ = self.env.reset()
            # Populate the unchanged dual RGB sensors without advancing PhysX.
            for _ in range(4):
                self.base_env.sim.render()
            return self.state()

    def state(self):
        import torch
        from .snapshots import capture_state, capture_rgb
        with torch.inference_mode():
            env = self.base_env
            rgb, hashes, frames = capture_rgb(env)
            return dict(simulation_time_ns=env.simulation_time_ns,reset_epoch=env.episode_clock.reset_epoch,
                        physics_step=env.episode_tick, state=capture_state(env),
                        rgb=rgb, rgb_hashes=hashes, sensor_frame_ids=frames,
                        outcome=env.task_outcome, executed_history=env.executed_command_history)

    def step(self, prepared: dict):
        import torch
        with torch.inference_mode():
            env = self.base_env
            env.submit_native9_command(prepared)
            command = None
            terminal = None
            for _ in range(2):
                action = self.controller(self.observations)
                if not torch.isfinite(action).all():
                    raise ValueError('Nonfinite fixed RAMBO controller residual')
                self.observations, _, done, _ = self.env.step(action)
                if done.any():
                    terminal = env.terminal_snapshot
                    command = terminal['command_confirmation']
                    break
            if terminal is None:
                command = env.current_command_confirmation
            return dict(command=copy.deepcopy(command), terminal=terminal,
                        completed_interval=command['status'] == 'completed',
                        simulation_time_ns=terminal['simulation_time_ns'] if terminal else env.simulation_time_ns)

    def expert_command(self):
        import torch
        with torch.inference_mode():
            if 'Push-Box' in self.task_id:
                from .push_box_expert import command
            elif 'Lift-Basket' in self.task_id:
                from .lift_basket_expert import command
            else:
                from .press_button_expert import command
            return command(self.base_env, self.base_env.simulation_time_ns/1e9)

    def close(self):
        self.env.close()
