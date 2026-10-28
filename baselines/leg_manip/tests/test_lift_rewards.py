"""Regression for the observed wrong-leg tripod reward loophole."""

from types import SimpleNamespace

import pytest
import torch

from leg_manip.tasks.track.env_cfg import make_track_env_cfg
from leg_manip.tasks.track.mdp import rewards


def reward_env(contact, flag=0, target_height=0.2, origin_height=0.0, load=None):
    scene = type("Scene", (dict,), {})()
    scene.env_origins = torch.tensor([[0.0, 0.0, origin_height]])
    if load is None:
        load = [40.0 * c for c in contact]
    # Net foot forces from the terrain; the sign of z depends on the sensor frame.
    force = torch.tensor([[[0.5, -0.2, -fz] for fz in load]])
    scene["feet"] = SimpleNamespace(
        data=SimpleNamespace(found=torch.tensor([contact]), force=force)
    )
    cmd = SimpleNamespace(
        flag_index=torch.tensor([flag]),
        target_pos_w=torch.tensor([[0.0, 0.0, origin_height + target_height]]),
        ee_pos_w=lambda: torch.tensor([[0.0, 0.0, origin_height + 0.01]]),
    )
    return SimpleNamespace(
        scene=scene, command_manager=SimpleNamespace(get_term=lambda _: cmd)
    )


@pytest.mark.parametrize("flag", [0, 1])
@pytest.mark.parametrize("hind", [2, 3])
def test_raising_a_hind_leg_cannot_earn_support_bonus(flag, hind):
    contacts = [1, 1, 1, 1]
    contacts[hind] = 0
    env = reward_env(contacts, flag)
    assert rewards.free_gait(env, "foot_traj", "feet").item() == 0


@pytest.mark.parametrize("flag", [0, 1])
def test_correct_stationary_tripod_can_earn_support_bonus(flag):
    contacts = [1, 1, 1, 1]
    contacts[flag] = 0
    env = reward_env(contacts, flag)
    assert rewards.free_gait(env, "foot_traj", "feet").item() == 1


@pytest.mark.parametrize("origin_height", [0.0, 5.0, -2.0])
def test_ground_commands_keep_contact_allowed_at_any_env_origin(origin_height):
    env = reward_env([1, 1, 1, 0], target_height=0.03, origin_height=origin_height)
    assert rewards.free_gait(env, "foot_traj", "feet").item() == 1
    assert rewards.manip_foot_ground_contact(env, "foot_traj", "feet").item() == 0


def test_airborne_robot_cannot_earn_support_bonus():
    assert rewards.free_gait(reward_env([0, 0, 0, 0]), "foot_traj", "feet").item() == 0


@pytest.mark.parametrize("flag,contacts", [(0, [1, 0, 1, 1]), (1, [0, 1, 1, 1])])
def test_contact_penalty_tracks_selected_front_leg(flag, contacts):
    assert (
        rewards.manip_foot_ground_contact(
            reward_env(contacts, flag), "foot_traj", "feet"
        ).item()
        == 1
    )
    contacts[flag] = 0
    assert (
        rewards.manip_foot_ground_contact(
            reward_env(contacts, flag), "foot_traj", "feet"
        ).item()
        == 0
    )


def test_height_tracking_has_signal_at_large_errors_and_rewards_improvement():
    cfg = make_track_env_cfg().rewards["ee_pos_z"]
    values = []
    for height in (0.41, 0.25, 0.11, 0.01):
        env = reward_env([1, 1, 1, 0], target_height=height)
        values.append((cfg.weight * cfg.func(env, **cfg.params)).item())
    assert values[0] > 0.01
    assert all(a < b for a, b in zip(values, values[1:], strict=False))


def test_requested_lift_contact_is_penalized_by_registered_environment():
    cfg = make_track_env_cfg()
    candidates = [
        term
        for term in cfg.rewards.values()
        if term.func is rewards.manip_foot_ground_contact
    ]
    assert len(candidates) == 1
    term = candidates[0]
    env = reward_env([1, 1, 1, 0])
    env.scene[term.params["sensor_name"]] = env.scene["feet"]
    assert (term.weight * term.func(env, **term.params)).item() < 0


@pytest.mark.parametrize("flag", [0, 1])
def test_load_share_falls_as_weight_shifts_off_the_selected_foreleg(flag):
    # The contact flag stays set until the foot is fully unloaded, so only this
    # term rewards the weight shift that has to happen before lift-off.
    values = []
    for manip_load in (60.0, 20.0, 5.0, 0.0):
        load = [40.0, 40.0, 40.0, 40.0]
        load[flag] = manip_load
        contact = [1, 1, 1, 1]
        contact[flag] = int(manip_load > 0)
        env = reward_env(contact, flag, load=load)
        values.append(rewards.manip_foot_load_share(env, "foot_traj", "feet").item())
    assert values[0] == pytest.approx(60.0 / 180.0)
    assert all(a > b for a, b in zip(values, values[1:], strict=False))
    assert values[-1] == 0


def test_load_share_ignores_the_other_foreleg_and_low_targets():
    env = reward_env([1, 1, 1, 1], flag=0, load=[0.0, 90.0, 30.0, 30.0])
    assert rewards.manip_foot_load_share(env, "foot_traj", "feet").item() == 0
    env = reward_env([1, 1, 1, 1], flag=0, target_height=0.03)
    assert rewards.manip_foot_load_share(env, "foot_traj", "feet").item() == 0


def test_load_share_is_finite_when_airborne():
    env = reward_env([0, 0, 0, 0], load=[0.0, 0.0, 0.0, 0.0])
    assert rewards.manip_foot_load_share(env, "foot_traj", "feet").item() == 0


def test_requested_lift_load_is_penalized_by_registered_environment():
    cfg = make_track_env_cfg()
    candidates = [
        term
        for term in cfg.rewards.values()
        if term.func is rewards.manip_foot_load_share
    ]
    assert len(candidates) == 1
    term = candidates[0]
    env = reward_env([1, 1, 1, 1])
    env.scene[term.params["sensor_name"]] = env.scene["feet"]
    assert (term.weight * term.func(env, **term.params)).item() < 0
