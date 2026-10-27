"""CPU regressions using mjlab's real rollout ordering and observation history."""

from collections import UserDict
from types import SimpleNamespace

import pytest
import torch
from mjlab.entity.data import EntityData
from mjlab.envs import ManagerBasedRlEnv
from mjlab.managers.command_manager import CommandManager
from mjlab.managers.observation_manager import (
    ObservationGroupCfg,
    ObservationManager,
    ObservationTermCfg,
)
from mjlab.managers.recorder_manager import RecorderManager
from mjlab.managers.termination_manager import TerminationManager, TerminationTermCfg
from mjlab.rl import RslRlVecEnvWrapper

from leg_manip.collect import rollout
from leg_manip.tasks.manip.env_cfg import make_manip_env_cfg
from leg_manip.tasks.manip.mdp import reset_robot_and_object
from leg_manip.tasks.manip.specs import CLOSE_DISHWASHER, PRESS_BUTTON
from leg_manip.tasks.track.env_cfg import CMD


def make_cpu_rollout(monkeypatch, spec, samples, *, planner=False, fall_steps=None):
    """Replace only physics/sensing; keep the actual mjlab lifecycle and managers.

    Each row in samples is the object qpos after one physical substep. There are
    two substeps per control step, so terminal samples must include the last one.
    """
    samples = torch.as_tensor(samples, dtype=torch.float32)
    if samples.ndim == 1:
        samples = samples[:, None]
    n = samples.shape[1]
    cfg = make_manip_env_cfg(spec, planner=planner)
    cfg.scene.num_envs = n
    cfg.decimation = 2
    cfg.sim.mujoco.timestep = 0.01
    cfg.episode_length_s = len(samples) * 0.01
    env = ManagerBasedRlEnv.__new__(ManagerBasedRlEnv)
    env.cfg = cfg
    env._sim_step_counter = 0
    env.common_step_counter = 0
    env.episode_length_buf = torch.zeros(n, dtype=torch.long)
    env._manual_reset_pending = torch.zeros(n, dtype=torch.bool)
    env._command_dt = torch.zeros(n)
    env.extras = {}
    env.obs_buf = {}

    obj_data = EntityData.__new__(EntityData)
    obj_data.indexing = SimpleNamespace(joint_q_adr=torch.tensor([0]), root_body_id=0)
    obj_data.data = SimpleNamespace(
        qpos=torch.zeros(n, 1),
        xpos=torch.zeros(n, 1, 3),
        xquat=torch.tensor([1.0, 0.0, 0.0, 0.0]).repeat(n, 1, 1),
    )
    robot_data = SimpleNamespace(
        default_root_state=torch.zeros(n, 13),
        root_link_pos_w=torch.zeros(n, 3),
        root_link_quat_w=torch.tensor([1.0, 0.0, 0.0, 0.0]).repeat(n, 1),
        site_pos_w=torch.zeros(n, 2, 3),
        body_link_pos_w=torch.zeros(n, 2, 3),
        joint_pos=torch.zeros(n, 12),
    )

    def write_robot(root, env_ids):
        robot_data.root_link_pos_w[env_ids] = root[:, :3]
        robot_data.root_link_quat_w[env_ids] = root[:, 3:7]

    def write_object(pose, env_ids):
        obj_data.data.xpos[env_ids, 0] = pose[:, :3]
        obj_data.data.xquat[env_ids, 0] = pose[:, 3:7]

    def write_joint(pos, vel, env_ids):
        obj_data.data.qpos[env_ids] = pos

    env.scene = UserDict(
        robot=SimpleNamespace(
            data=robot_data,
            find_sites=lambda *a, **kw: ([0, 1], []),
            find_bodies=lambda *a, **kw: ([0, 1], []),
            write_root_state_to_sim=write_robot,
        ),
        object=SimpleNamespace(
            data=obj_data,
            write_mocap_pose_to_sim=write_object,
            write_joint_state_to_sim=write_joint,
        ),
    )
    env.scene.num_envs = n
    env.scene.env_origins = torch.zeros(n, 3)
    env.scene.write_data_to_sim = lambda: None
    env.scene.update = lambda **kw: None

    def physics_step():
        obj_data.data.qpos[:, 0] = samples[(env._sim_step_counter - 1) % len(samples)]

    env.sim = SimpleNamespace(
        device="cpu", step=physics_step, forward=lambda: None, sense=lambda: None
    )
    env.action_manager = SimpleNamespace(
        process_action=lambda action: None, apply_action=lambda: None
    )
    env.reward_manager = SimpleNamespace(compute=lambda **kw: torch.zeros(n))
    env.metrics_manager = SimpleNamespace(
        compute=lambda: None, compute_substep=lambda: None
    )
    env.event_manager = SimpleNamespace(available_modes=[])
    fall_steps = torch.tensor(fall_steps or [100000] * n)
    env.termination_manager = TerminationManager(
        {
            "timeout": TerminationTermCfg(
                func=lambda e: e.episode_length_buf >= e.max_episode_length,
                time_out=True,
            ),
            "fall": TerminationTermCfg(
                func=lambda e: e.episode_length_buf >= fall_steps
            ),
        },
        env,
    )
    env.command_manager = CommandManager(cfg.commands, env)
    # Preserve real term-level histories, but expose their dimensions to assertions.
    env.observation_manager = ObservationManager(
        {
            "actor": ObservationGroupCfg(
                terms={
                    "clock": ObservationTermCfg(
                        func=lambda e: torch.full((n, 1), float(e.common_step_counter))
                    ),
                    "command": cfg.observations["actor"].terms["command"],
                },
                history_length=15,
                flatten_history_dim=False,
                concatenate_terms=False,
            )
        },
        env,
    )
    env.recorder_manager = RecorderManager(cfg.recorders, env)

    def reset_indices(env_ids):
        reset_robot_and_object(
            env,
            env_ids,
            robot_yaw_range=(0.0, 0.0),
            object_joint_range=spec.object_joint_range,
        )
        robot_data.joint_pos[env_ids] = torch.rand(len(env_ids), 12)
        env.observation_manager.reset(env_ids)
        env.command_manager.reset(env_ids)
        env.termination_manager.reset(env_ids)
        env.episode_length_buf[env_ids] = 0
        env._manual_reset_pending[env_ids] = False

    env._reset_idx = reset_indices
    wrapped = RslRlVecEnvWrapper.__new__(RslRlVecEnvWrapper)
    wrapped.env, wrapped.num_envs, wrapped.clip_actions = env, n, None
    monkeypatch.setattr(
        rollout,
        "object_point_cloud",
        lambda e, num_points: (
            obj_data.root_link_pos_w[:, None].repeat(1, num_points, 1),
            torch.ones(n, dtype=torch.long),
        ),
    )
    return env, wrapped


@pytest.mark.parametrize(
    ("spec", "samples", "expected"),
    [
        (PRESS_BUTTON, [0.0, 0.0, 0.0, 0.01], True),
        (CLOSE_DISHWASHER, [0.2, 0.2, 0.2, 0.0], True),
        (CLOSE_DISHWASHER, [0.0, 0.0, 0.0, 0.2], False),
    ],
)
def test_success_uses_final_physics_sample_before_auto_reset(
    monkeypatch, spec, samples, expected
):
    env, wrapped = make_cpu_rollout(monkeypatch, spec, samples)
    batch = rollout.run_episode(env, wrapped, lambda obs: torch.zeros(1, 12), spec)
    assert batch.success.item() == expected
    assert batch.joint[-1, 0].item() == pytest.approx(samples[-1])
    assert batch.joint[:, 0].tolist() == pytest.approx(samples[1::2])
    # Automatic reset really occurred; the terminal sample must survive it.
    assert env.episode_length_buf.tolist() == [0]


def test_final_fall_and_timeout_remains_a_failure(monkeypatch):
    env, wrapped = make_cpu_rollout(
        monkeypatch, PRESS_BUTTON, [[0.01, 0.01]] * 4, fall_steps=[2, 100000]
    )
    batch = rollout.run_episode(
        env, wrapped, lambda obs: torch.zeros(2, 12), PRESS_BUTTON
    )
    assert env.reset_terminated.tolist() == [True, False]
    assert env.reset_time_outs.tolist() == [True, True]
    assert batch.alive.tolist() == [False, True]
    assert batch.success.tolist() == [False, True]


def test_replanning_updates_current_observation_without_extra_history(monkeypatch):
    env, wrapped = make_cpu_rollout(monkeypatch, PRESS_BUTTON, [0.0] * 24, planner=True)
    observed, predictions = [], []

    def planner(cloud, state, first):
        predictions.append((env.common_step_counter, first))
        vector = torch.tensor([PRESS_BUTTON.expert_vector])
        vector[:, 1:19] = 10.0 + env.common_step_counter
        return vector

    def controller(obs):
        observed.append({k: v.clone() for k, v in obs["actor"].items()})
        return torch.zeros(1, 12)

    batch = rollout.run_episode(env, wrapped, controller, PRESS_BUTTON, planner)
    assert predictions == [(0, True), (5, False), (10, False)]
    # Current command follows the new plan in the same control tick.
    assert observed[5]["command"][0, -1, 1].item() == pytest.approx(15.0)
    assert observed[10]["command"][0, -1, 1].item() == pytest.approx(20.0)
    assert batch.action[:, 0, 1].tolist() == [10.0, 15.0, 20.0]
    # No duplicated time sample and no erasure of earlier command history.
    assert observed[5]["clock"][0, :, 0].tolist() == [0.0] * 10 + [1, 2, 3, 4, 5]
    assert observed[6]["command"][0, -3:, 1].tolist() == pytest.approx([10, 15, 15])
    assert observed[10]["clock"][0, -6:, 0].tolist() == [5, 6, 7, 8, 9, 10]


def test_early_reset_does_not_requalify_a_failed_episode(monkeypatch):
    env, wrapped = make_cpu_rollout(
        monkeypatch, PRESS_BUTTON, [[0.01, 0.01]] * 12, fall_steps=[2, 100000]
    )
    batch = rollout.run_episode(
        env, wrapped, lambda obs: torch.zeros(2, 12), PRESS_BUTTON
    )
    assert batch.alive.tolist() == [False, True]
    assert batch.success.tolist() == [False, True]


def test_no_extra_planner_frame_at_horizon_and_phase_restarts_next_rollout(monkeypatch):
    env, wrapped = make_cpu_rollout(monkeypatch, PRESS_BUTTON, [0.0] * 20, planner=True)
    cmd = env.command_manager.get_term(CMD)
    predictions = []

    def planner(cloud, state, first):
        predictions.append((env.common_step_counter, first, cmd.phase_time.item()))
        return torch.tensor([PRESS_BUTTON.expert_vector])

    for _ in range(2):
        batch = rollout.run_episode(
            env, wrapped, lambda obs: torch.zeros(1, 12), PRESS_BUTTON, planner
        )
        assert batch.point_cloud.shape[0] == batch.action.shape[0] == 2
        assert cmd.before_observation is None
    assert [(t, first) for t, first, phase in predictions] == [
        (0, True),
        (5, False),
        (10, True),
        (15, False),
    ]
    assert [phase for t, first, phase in predictions] == pytest.approx([0, 0.1, 0, 0.1])


def test_retry_after_planner_error_does_not_reuse_old_terminal_samples(monkeypatch):
    samples = torch.arange(24, dtype=torch.float32)[:, None].repeat(1, 2) / 1000
    env, wrapped = make_cpu_rollout(
        monkeypatch, PRESS_BUTTON, samples, planner=True, fall_steps=[5, 100000]
    )

    def broken_planner(cloud, state, first):
        if not first:
            raise RuntimeError("planner failed after an auto-reset")
        return torch.tensor([PRESS_BUTTON.expert_vector] * 2)

    with pytest.raises(RuntimeError, match="planner failed"):
        rollout.run_episode(
            env, wrapped, lambda obs: torch.zeros(2, 12), PRESS_BUTTON, broken_planner
        )
    assert env.command_manager.get_term(CMD).before_observation is None
    # The interrupted step captured env 0's terminal qpos=0.009. After the new
    # explicit reset, the first completed step has fresh qpos=0.011 in both envs.
    batch = rollout.run_episode(
        env, wrapped, lambda obs: torch.zeros(2, 12), PRESS_BUTTON
    )
    assert batch.joint[0].tolist() == pytest.approx([0.011, 0.011])
