"""Shared rollout loop for expert data collection and planner evaluation.

All envs start together, run one 20 s episode (1000 control steps at 50 Hz) and
record a planner frame every 5 steps (10 Hz, 200 frames). An env that terminates
early (falls) is marked failed; mjlab auto-resets it, and the rest of its episode
is ignored.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import torch
from mjlab.envs import ManagerBasedRlEnv

from leg_manip.tasks.manip.mdp import ExpertTrajectoryCommand
from leg_manip.tasks.manip.perception import object_point_cloud, robot_state
from leg_manip.tasks.manip.recording import OBJECT_JOINT_RECORDER, ObjectJointRecorder
from leg_manip.tasks.manip.specs import ManipTaskSpec
from leg_manip.tasks.track.env_cfg import CMD
from leg_manip.traj import TrajParams

PLANNER_PERIOD = 5  # control steps per planner step (50 Hz / 10 Hz)


@dataclass
class EpisodeBatch:
    point_cloud: torch.Tensor  # (T, N, P, 3), env frame
    state: torch.Tensor  # (T, N, 17)
    action: torch.Tensor  # (T, N, 31), trajectory parameters in the env frame
    joint: torch.Tensor  # (steps, N) post-action joint, before any auto-reset
    alive: torch.Tensor  # (N,) no early termination
    success: torch.Tensor  # (N,)
    num_visible: torch.Tensor  # (T, N) object pixels seen


def params_env_frame(
    cmd: ExpertTrajectoryCommand, env: ManagerBasedRlEnv
) -> torch.Tensor:
    """Current world-frame parameters shifted into each env's frame -> (N, 31)."""
    p = cmd.params
    shifted = TrajParams(
        p.flag, p.ctrl - env.scene.env_origins.unsqueeze(1), p.log_w, p.dir0, p.dir1
    )
    return shifted.to_vector()


def run_episode(
    env: ManagerBasedRlEnv,
    wrapped_env,
    policy,
    spec: ManipTaskSpec,
    planner_fn: Callable[[torch.Tensor, torch.Tensor, bool], torch.Tensor]
    | None = None,
    num_points: int = 768,
    reset_seed: int | None = None,
) -> EpisodeBatch:
    """Run one synchronized episode in every env.

    Args:
        planner_fn: None for the expert. Otherwise called every 0.1 s with
            (point_cloud, state, first) and must return env-frame parameter vectors
            (N, 31); they are written into the command with `set_params`.
        reset_seed: If set, seed mjlab immediately before the batch reset. This
            isolates evaluation initializations from earlier inference RNG draws.

    Requires the observation and recorder terms from ``make_manip_env_cfg``.
    """
    cmd: ExpertTrajectoryCommand = env.command_manager.get_term(CMD)  # type: ignore
    recorder: ObjectJointRecorder = env.recorder_manager.get_term(OBJECT_JOINT_RECORDER)
    n = env.num_envs
    steps = int(round(env.max_episode_length))
    alive = torch.ones(n, dtype=torch.bool, device=env.device)
    clouds, states, actions, visible, joint = [], [], [], [], []
    start_step = env.common_step_counter
    last_frame_step = -1

    def prepare_frame() -> None:
        nonlocal last_frame_step
        step = env.common_step_counter - start_step
        if step >= steps or step % PLANNER_PERIOD or step == last_frame_step:
            return
        cloud, num_valid = object_point_cloud(env, num_points=num_points)
        state = robot_state(env)
        if planner_fn is not None:
            vec = planner_fn(cloud, state, step == 0)
            p = TrajParams.from_vector(vec)
            p.ctrl = p.ctrl + env.scene.env_origins.unsqueeze(1)
            cmd.set_params(p, duration=spec.duration_s)
        clouds.append(cloud)
        states.append(state)
        actions.append(params_env_frame(cmd, env))
        visible.append(num_valid)
        last_frame_step = step

    # Reset inside inference mode too: buffers created during the previous episode
    # are inference tensors and must not be updated in place outside of it.
    with torch.inference_mode():
        previous_callback = cmd.before_observation
        cmd.before_observation = prepare_frame
        try:
            if reset_seed is not None:
                env.seed(reset_seed)
            obs, _ = wrapped_env.reset()
            for step in range(steps):
                obs, _, dones, _ = wrapped_env.step(policy(obs))
                joint.append(recorder.joint.clone())
                # A fall and the horizon timeout can both be true on the last step.
                # The wrapper's OR-ed dones cannot recover the independent fall bit.
                alive &= ~env.reset_terminated
                if step < steps - 1:
                    alive &= ~dones.bool()
        finally:
            cmd.before_observation = previous_callback
    joint_t = torch.stack(joint)
    success = spec.success(joint_t) & alive
    return EpisodeBatch(
        point_cloud=torch.stack(clouds),
        state=torch.stack(states),
        action=torch.stack(actions),
        joint=joint_t,
        alive=alive,
        success=success,
        num_visible=torch.stack(visible),
    )
