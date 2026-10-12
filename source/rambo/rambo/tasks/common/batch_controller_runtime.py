from __future__ import annotations
import copy
from .controller_runtime import ControllerRuntime


class BatchControllerRuntime(ControllerRuntime):
    def __init__(self, task_id, *, num_envs, **kwargs):
        from .environment_factory import registration_for_gym
        from qlm_bench.tasks.registration import resolve_symbol
        row = registration_for_gym(task_id)
        if not row.get('batch_environment'):
            raise ValueError('Task must implement its opt-in batch environment plug-in')
        super().__init__(task_id, num_envs=num_envs, environment_type=resolve_symbol(row['batch_environment']), **kwargs)

    def state(self):
        return [self.base_env.lane_snapshot(i) for i in range(self.base_env.num_envs)]

    def prime_render(self, max_renders=24):
        """Refresh actual RGB after products attach, without advancing physics."""
        import numpy as np
        import torch
        env = self.base_env
        before = int(env._sim_step_counter)
        with torch.inference_mode():
            for _ in range(max_renders):
                env.sim.render()
                for sensor in (env.front_camera, env.task_camera):
                    sensor.update(dt=0., force_recompute=True)
                snapshots = self.state()
                if all(any(float(np.asarray(pixels)[:, :, :3].std()) > 3
                           for pixels in row['rgb'].values()) for row in snapshots):
                    if int(env._sim_step_counter) != before:
                        raise ValueError('Render priming must not advance physics')
                    return snapshots
        raise RuntimeError('Batch scene RGB is not ready after bounded render priming')

    def expert_commands(self):
        import torch
        from .environment_factory import registration_for_gym
        from qlm_bench.tasks.registration import resolve_symbol
        registration = registration_for_gym(self.task_id)
        if not registration.get("batch_expert"):
            raise ValueError("Task must declare a batch expert")
        command = resolve_symbol(registration["batch_expert"])
        env = self.base_env
        with torch.inference_mode():
            return [command(env, i, env.lane_tick(i) / 500) if env.lane_active[i] else (None, None)
                    for i in range(env.num_envs)]

    def step(self, commands):
        import torch
        env = self.base_env
        epochs = [lane.clock.reset_epoch for lane in env.lanes]
        with torch.inference_mode():
            env.submit_native9_batch(commands)
            for _ in range(2):
                action = self.controller(self.observations)
                if not torch.isfinite(action).all():
                    raise ValueError('Nonfinite batch controller residual')
                self.observations, _, _, _ = self.env.step(action)
            return [dict(env_index=i, terminal=copy.deepcopy(lane.terminal) if lane.clock.reset_epoch != epochs[i] else None,
                         command=copy.deepcopy(lane.current_command), reset_epoch=lane.clock.reset_epoch)
                    for i, lane in enumerate(env.lanes)]
