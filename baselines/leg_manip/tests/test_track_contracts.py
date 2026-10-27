"""CPU contract checks at the command and external-wrench simulator boundaries."""

from types import SimpleNamespace

import pytest
import torch

pytest.importorskip("mjlab")

from rsl_rl.models import MLPModel
from rsl_rl.storage import RolloutStorage
from tensordict import TensorDict

from leg_manip.learning.estimator import EstimatorActorModel, PPOWithEstimator
from leg_manip.tasks.track.env_cfg import CMD, make_track_env_cfg
from leg_manip.tasks.track.mdp.commands import (
    FootTrajectoryCommand,
    FootTrajectoryCommandCfg,
)
from leg_manip.tasks.track.mdp.observations import ee_pos_heading
from leg_manip.traj import TrajParams


def _env_and_command():
    # Deliberately noncontiguous calf IDs and reversed site IDs exercise mappings.
    data = SimpleNamespace(
        root_link_pos_w=torch.tensor([[1.0, 2.0, 0.3], [11.0, 22.0, 5.4]]),
        root_link_quat_w=torch.tensor(
            [[1.0, 0.0, 0.0, 0.0], [2**-0.5, 0.0, 0.0, 2**-0.5]]
        ),
        site_pos_w=torch.tensor(
            [[[1.2, 1.9, 0.1], [1.2, 2.1, 0.2]], [[11.1, 22.2, 5.1], [10.9, 22.2, 5.2]]]
        ),
        body_link_pos_w=torch.zeros(2, 5, 3),
        body_com_pos_w=torch.zeros(2, 5, 3),
        body_external_wrench=torch.zeros(2, 5, 6),
    )
    # FL has lever arm +Z; FR has lever arm +X. These make moments hand-checkable.
    data.body_com_pos_w[:, 3] = data.site_pos_w[:, 1] - torch.tensor([0.0, 0.0, 0.2])
    data.body_com_pos_w[:, 1] = data.site_pos_w[:, 0] - torch.tensor([0.1, 0.0, 0.0])
    data.body_link_pos_w.copy_(data.body_com_pos_w)

    def write_wrench(forces, torques, env_ids=None, body_ids=None):
        ids = torch.arange(2) if env_ids is None else torch.arange(2)[env_ids]
        bodies = torch.arange(5) if body_ids is None else torch.as_tensor(body_ids)
        data.body_external_wrench[ids[:, None], bodies, :3] = forces
        data.body_external_wrench[ids[:, None], bodies, 3:] = torques

    robot = SimpleNamespace(
        data=data,
        num_bodies=5,
        find_sites=lambda names, preserve_order: ([1, 0], list(names)),
        find_bodies=lambda names, preserve_order: ([3, 1], list(names)),
        write_external_wrench_to_sim=write_wrench,
    )
    # A dict-backed scene exposing the same origins property as mjlab.Scene.
    scene = type("SceneStub", (dict,), {})(robot=robot)
    scene.env_origins = torch.tensor([[0.0, 0.0, 0.0], [10.0, 20.0, 5.0]])
    env = SimpleNamespace(
        scene=scene, num_envs=2, device="cpu", step_dt=0.02, max_episode_length=1000
    )
    cfg = FootTrajectoryCommandCfg(resampling_time_range=(1e9, 1e9))
    cmd = FootTrajectoryCommand(cfg, env)
    cmd.params.flag[:] = torch.tensor([0.0, 1.0])
    env.command_manager = SimpleNamespace(get_term=lambda name: cmd)
    return env, cmd


def _force_event():
    env, cmd = _env_and_command()
    cfg = make_track_env_cfg().events["ee_force"]
    cfg.params["asset_cfg"].body_ids = [3, 1]
    cfg.params["force_range"] = (2.0, 2.0)
    cfg.params["duration_s"] = (0.06, 0.06)
    cfg.params["cooldown_s"] = (0.04, 0.04)
    # mjlab constructs event terms before command_manager exists.
    manager = env.command_manager
    del env.command_manager
    event = cfg.func(cfg, env)
    env.command_manager = manager
    return env, cmd, cfg, event


def _tick(env, cfg, event, n=1):
    for _ in range(n):
        event(env, None, **cfg.params)


def test_heading_commands_and_estimator_use_environment_absolute_height():
    env, cmd = _env_and_command()
    points = torch.tensor([[1.3, 2.2, 0.6], [10.8, 22.3, 5.6]])
    params = TrajParams(
        flag=torch.tensor([0.0, 1.0]),
        ctrl=points[:, None].repeat(1, 6, 1),
        log_w=torch.zeros(2, 6),
        dir0=torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
        dir1=torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
    )
    cmd.set_params(params, duration=10.0)
    expected = torch.tensor([[0.3, 0.2, 0.6], [0.3, 0.2, 0.6]])
    torch.testing.assert_close(
        cmd.command[:, 1:13].reshape(2, 4, 3), expected[:, None].expand(-1, 4, -1)
    )
    torch.testing.assert_close(
        cmd.command[:, 13:], torch.tensor([[1.0, 0.0, 0.0]]).repeat(2, 1)
    )
    torch.testing.assert_close(
        ee_pos_heading(env, CMD), torch.tensor([[0.2, 0.1, 0.2], [0.2, -0.1, 0.1]])
    )
    before = cmd.command.clone()
    env.scene["robot"].data.root_link_pos_w[:, 2] += 0.25
    cmd._update_command(None)
    torch.testing.assert_close(cmd.command, before)


def test_random_reference_heights_follow_environment_origin_not_base():
    env, cmd = _env_and_command()
    cmd.cfg.ranges.ctrl_x = (0.0, 0.0)
    cmd.cfg.ranges.ctrl_y = (0.0, 0.0)
    cmd.cfg.ranges.ctrl_z = (0.6, 0.6)
    cmd.cfg.ranges.start_at_foot_prob = 0.0
    params, _ = cmd._sample_random(torch.tensor([0, 1]))
    torch.testing.assert_close(
        params.ctrl[..., 2], torch.tensor([[0.6] * 6, [5.6] * 6])
    )
    cmd.cfg.ranges.start_at_foot_prob = 1.0
    cmd.cfg.ranges.fr_prob = 0.0
    cmd.reset(torch.tensor([1]))
    # Change kinematics after reset to model mj_forward refreshing the foot poses.
    env.scene["robot"].data.site_pos_w[1, 1] = torch.tensor([12.0, 23.0, 5.25])
    cmd.compute(0.0, torch.tensor([1]))
    torch.testing.assert_close(cmd.params.ctrl[1, 0], torch.tensor([12.0, 23.0, 5.25]))
    torch.testing.assert_close(cmd.command[1, 1:4], torch.tensor([1.0, -1.0, 0.25]))
    assert cmd.phase_time[1] == 0.0


def test_external_force_loads_only_selected_calf_at_toe():
    env, _, cfg, event = _force_event()
    _tick(env, cfg, event)
    assert not env.scene["robot"].data.body_external_wrench.any()
    _tick(env, cfg, event)
    wrench = env.scene["robot"].data.body_external_wrench
    torch.testing.assert_close(
        wrench[0, 3], torch.tensor([2.0, 2.0, 2.0, -0.4, 0.4, 0.0])
    )
    torch.testing.assert_close(
        wrench[1, 1], torch.tensor([2.0, 2.0, 2.0, 0.0, -0.2, 0.2])
    )
    assert not wrench[0, [0, 1, 2, 4]].any()
    assert not wrench[1, [0, 2, 3, 4]].any()


def test_external_force_refreshes_moment_and_clears_previous_manipulator():
    env, cmd, cfg, event = _force_event()
    _tick(env, cfg, event, 2)
    data = env.scene["robot"].data
    data.site_pos_w[0, 1] += torch.tensor([0.0, 0.0, 0.1])
    _tick(env, cfg, event)
    torch.testing.assert_close(
        data.body_external_wrench[0, 3, 3:], torch.tensor([-0.6, 0.6, 0.0])
    )
    cmd.params.flag[0] = 1.0
    _tick(env, cfg, event)
    assert not data.body_external_wrench[0, 3].any()
    torch.testing.assert_close(
        data.body_external_wrench[0, 1], torch.tensor([2.0, 2.0, 2.0, 0.0, -0.2, 0.2])
    )


def test_external_force_expiry_and_partial_reset_clear_wrenches():
    env, _, cfg, event = _force_event()
    _tick(env, cfg, event, 2)
    data = env.scene["robot"].data
    other = data.body_external_wrench[1].clone()
    event.reset(torch.tensor([0]))
    assert not data.body_external_wrench[0].any()
    torch.testing.assert_close(data.body_external_wrench[1], other)
    _tick(env, cfg, event)
    assert not data.body_external_wrench[0].any()
    _tick(env, cfg, event, 2)
    assert not data.body_external_wrench[1].any()
    event.reset()
    assert not data.body_external_wrench.any()
    _tick(env, cfg, event)
    assert not data.body_external_wrench.any()


def _estimator_algorithm():
    obs = TensorDict(
        {
            "actor": torch.zeros(2, 8),
            "critic": torch.zeros(2, 8),
            "estimator_target": torch.zeros(2, 6),
        },
        batch_size=[2],
    )
    groups = {name: [name] for name in obs.keys()}
    actor = EstimatorActorModel(
        obs,
        groups,
        "actor",
        12,
        hidden_dims=(8,),
        estimator_hidden_dims=(8,),
        obs_normalization=True,
        distribution_cfg={"class_name": "GaussianDistribution", "init_std": 1.0},
    )
    critic = MLPModel(obs, groups, "critic", 1, hidden_dims=(8,))
    storage = RolloutStorage("rl", 2, 1, obs, [12])
    return PPOWithEstimator(actor, critic, storage, num_mini_batches=1), obs


@pytest.mark.parametrize("marker", [None, torch.tensor(1), torch.tensor(999)])
@pytest.mark.parametrize("strict", [False, True])
@pytest.mark.parametrize("load_cfg", [None, {"actor": True}])
def test_controller_rejects_old_or_unknown_observation_contract(
    marker, strict, load_cfg
):
    alg, _ = _estimator_algorithm()
    saved = alg.save()
    actor_state = saved["actor_state_dict"]
    actor_state.pop("observation_contract_version", None)
    if marker is not None:
        actor_state["observation_contract_version"] = marker
    before = next(alg.actor.mlp.parameters()).detach().clone()
    # An incompatible checkpoint must be rejected before even partially copying weights.
    for name, value in list(actor_state.items()):
        if name.startswith("mlp."):
            actor_state[name] = torch.zeros_like(value)
    with pytest.raises(RuntimeError, match="observation contract.*[Rr]etrain"):
        alg.load(saved, load_cfg, strict=strict)
    torch.testing.assert_close(next(alg.actor.mlp.parameters()), before)


@pytest.mark.parametrize("load_cfg", [None, {"actor": True}])
def test_controller_new_observation_contract_checkpoint_round_trip(tmp_path, load_cfg):
    source, obs = _estimator_algorithm()
    # Include the auxiliary optimizer's nonempty state in the resume check.
    source.actor.estimator_loss(obs).backward()
    source.estimator_optimizer.step()
    path = tmp_path / "controller.pt"
    torch.save(source.save(), path)
    saved = torch.load(path, weights_only=False, map_location="cpu")
    assert saved["actor_state_dict"]["observation_contract_version"].item() == 2
    target, _ = _estimator_algorithm()
    target.load(saved, load_cfg, strict=True)
    torch.testing.assert_close(target.actor(obs), source.actor(obs))
    if load_cfg is None:
        source_state = source.estimator_optimizer.state_dict()["state"]
        target_state = target.estimator_optimizer.state_dict()["state"]
        for key in source_state:
            for name in ("step", "exp_avg", "exp_avg_sq"):
                torch.testing.assert_close(
                    target_state[key][name], source_state[key][name]
                )
