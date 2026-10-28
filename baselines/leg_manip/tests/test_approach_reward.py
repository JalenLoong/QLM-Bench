"""Dense locomotion and heading signals toward the commanded foot target."""

import math
from types import SimpleNamespace

import pytest
import torch

from leg_manip.tasks.track.env_cfg import make_track_env_cfg
from leg_manip.tasks.track.mdp import rewards


def approach_env(target_xy, base_vel_xy, foot_xy=(0.0, 0.0)):
    n = len(target_xy)
    cmd = SimpleNamespace(
        target_pos_w=torch.tensor([[x, y, 0.2] for x, y in target_xy]),
        ee_pos_w=lambda: torch.tensor([[*foot_xy, 0.02]] * n),
        robot=SimpleNamespace(
            data=SimpleNamespace(
                root_link_lin_vel_w=torch.tensor([[x, y, 0.0] for x, y in base_vel_xy])
            )
        ),
    )
    return SimpleNamespace(command_manager=SimpleNamespace(get_term=lambda _: cmd))


def test_far_target_rewards_only_base_speed_toward_it():
    env = approach_env(
        [(1.0, 0.0)] * 5,
        [(0.0, 0.0), (0.15, 0.0), (0.3, 0.0), (0.6, 0.0), (-0.3, 0.0)],
    )
    r = rewards.base_approach_velocity(env, "foot_traj", speed=0.3, reach=0.25)
    torch.testing.assert_close(r, torch.tensor([0.0, 0.5, 1.0, 1.0, 0.0]))


def test_sideways_motion_earns_nothing_and_direction_follows_target():
    env = approach_env([(1.0, 0.0), (0.0, -1.0)], [(0.0, 0.3), (0.0, -0.3)])
    r = rewards.base_approach_velocity(env, "foot_traj", speed=0.3, reach=0.25)
    torch.testing.assert_close(r, torch.tensor([0.0, 1.0]))


def test_target_within_reach_needs_no_walking():
    env = approach_env([(0.2, 0.1)], [(0.0, 0.0)], foot_xy=(0.05, 0.05))
    r = rewards.base_approach_velocity(env, "foot_traj", speed=0.3, reach=0.25)
    assert r.item() == 1


@pytest.mark.parametrize("make", [make_track_env_cfg])
def test_approach_term_is_registered_with_positive_weight(make):
    terms = [
        t for t in make().rewards.values() if t.func is rewards.base_approach_velocity
    ]
    assert len(terms) == 1 and terms[0].weight > 0


def test_fine_position_term_separates_centimetre_errors():
    # The coarse xy/z Gaussians pay ~97% at 8.5 cm; the fine term must not.
    cfg = make_track_env_cfg().rewards["ee_pos_fine"]
    values = []
    for err in (0.10, 0.05, 0.02, 0.0):
        cmd = SimpleNamespace(
            target_pos_w=torch.tensor([[err, 0.0, 0.2]]),
            ee_pos_w=lambda: torch.tensor([[0.0, 0.0, 0.2]]),
        )
        manager = SimpleNamespace(get_term=lambda _, cmd=cmd: cmd)
        env = SimpleNamespace(command_manager=manager)
        values.append(cfg.func(env, **cfg.params).item())
    assert values[0] < 0.1 and values[1] < 0.5 and values[2] > 0.8 and values[3] == 1
    assert cfg.weight > 0


def heading_env(target_xy, yaw, flag=0, base_xy=(0.0, 0.0)):
    n = len(target_xy)
    half = torch.as_tensor(yaw, dtype=torch.float32) / 2
    quat = torch.stack(
        [torch.cos(half), torch.zeros(n), torch.zeros(n), torch.sin(half)], -1
    )
    cmd = SimpleNamespace(
        target_pos_w=torch.tensor([[x, y, 0.2] for x, y in target_xy]),
        flag_index=torch.full((n,), flag, dtype=torch.long),
        robot=SimpleNamespace(
            data=SimpleNamespace(
                root_link_pos_w=torch.tensor([[*base_xy, 0.25]] * n),
                root_link_quat_w=quat,
            )
        ),
    )
    return SimpleNamespace(command_manager=SimpleNamespace(get_term=lambda _: cmd))


def heading(env):
    return rewards.base_heading_to_target(
        env, "foot_traj", reference=(0.19, 0.14), std=0.5, blend_dist=0.1
    )


def test_heading_is_measured_from_the_manipulating_foot():
    # Straight ahead of the FL rest point: aligned, though the base bearing is ~10 deg.
    fl = heading(heading_env([(0.8, 0.14), (0.8, -0.14)], [0.0, 0.0], flag=0))
    fr = heading(heading_env([(0.8, 0.14), (0.8, -0.14)], [0.0, 0.0], flag=1))
    torch.testing.assert_close(fl[0], torch.tensor(1.0))
    torch.testing.assert_close(fr[1], torch.tensor(1.0))
    assert fl[1] < 0.9 and fr[0] < 0.9


def test_side_on_and_behind_targets_earn_little():
    side = math.exp(-((math.pi / 2) ** 2) / 0.25)
    r = heading(heading_env([(0.19, 1.14), (-0.81, 0.14), (1.19, 0.14)], [0.0] * 3))
    torch.testing.assert_close(r, torch.tensor([side, 0.0, 1.0]), atol=1e-6, rtol=0)


def test_foot_held_beside_the_trunk_is_not_aligned():
    # Measured side-on contact of the pilot 4 controller: target ~(0.05, 0.17).
    assert heading(heading_env([(0.05, 0.17)], [0.0])).item() < 0.01


def test_heading_follows_base_yaw_and_position():
    # Base at (2, 3) facing +y: the FL rest point is at (2 - 0.14, 3.19).
    env = heading_env([(2.0 - 0.14, 4.0)], [math.pi / 2], base_xy=(2.0, 3.0))
    assert heading(env).item() == pytest.approx(1.0, abs=1e-6)
    env = heading_env([(2.0 - 0.14, 4.0)], [0.0], base_xy=(2.0, 3.0))
    assert heading(env).item() < 0.01


def test_bearing_fades_out_at_the_rest_point():
    # Directly behind the rest point: 0 when far, half at 5 cm, 1 at the point.
    r = heading(heading_env([(-0.81, 0.14), (0.14, 0.14), (0.19, 0.14)], [0.0] * 3))
    torch.testing.assert_close(r, torch.tensor([0.0, 0.5, 1.0]), atol=1e-6, rtol=0)


def test_heading_terms_are_registered_with_positive_weight():
    cfg = make_track_env_cfg().rewards
    bearing, along_dir = cfg["base_heading"], cfg["base_heading_dir"]
    assert bearing.func is rewards.base_heading_to_target and bearing.weight > 0
    assert along_dir.func is rewards.base_heading_along_dir and along_dir.weight > 0


def dir_env(dir_xyz, yaw, foot_xy=(1.0, 2.0)):
    n = len(dir_xyz)
    half = torch.as_tensor(yaw, dtype=torch.float32) / 2
    quat = torch.stack(
        [torch.cos(half), torch.zeros(n), torch.zeros(n), torch.sin(half)], -1
    )
    cmd = SimpleNamespace(
        target_pos_w=torch.tensor([[1.0, 2.0, 0.3]] * n),
        target_dir_w=torch.nn.functional.normalize(torch.tensor(dir_xyz), dim=-1),
        ee_pos_w=lambda: torch.tensor([[*foot_xy, 0.3]] * n),
        robot=SimpleNamespace(data=SimpleNamespace(root_link_quat_w=quat)),
    )
    return SimpleNamespace(command_manager=SimpleNamespace(get_term=lambda _: cmd))


def dir_heading(env):
    return rewards.base_heading_along_dir(
        env, "foot_traj", std=0.5, reach=0.25, min_horizontal=0.3
    )


def test_side_on_contact_earns_little_for_dir_heading():
    # Dishwasher heading pilots: calf commanded along +x, base facing +-y.
    side = math.exp(-((math.pi / 2) ** 2) / 0.25)
    env = dir_env([(1.0, 0.0, 0.2)] * 3, [0.0, math.pi / 2, -math.pi / 2])
    expected = torch.tensor([1.0, side, side])
    torch.testing.assert_close(dir_heading(env), expected, atol=1e-6, rtol=0)


def test_dir_heading_follows_yaw_across_the_wrap():
    # Facing +3.1 rad, calf toward -3.1 rad: 0.08 rad apart, not 6.2.
    back = (math.cos(-3.1), math.sin(-3.1), -0.5)
    r = dir_heading(dir_env([(0.0, 1.0, 0.0), back], [math.pi / 2, 3.1]))
    expected = math.exp(-((2 * math.pi - 6.2) ** 2) / 0.25)
    torch.testing.assert_close(r, torch.tensor([1.0, expected]), atol=1e-5, rtol=0)


def test_dir_heading_fades_out_for_a_vertical_calf():
    # Backward calf: 0 when tilted 45 deg, half with xy norm 0.15, 1 straight down.
    dirs = [(-1.0, 0.0, -1.0), (-0.15, 0.0, -math.sqrt(1 - 0.15**2)), (0.0, 0.0, -1.0)]
    r = dir_heading(dir_env(dirs, [0.0] * 3))
    torch.testing.assert_close(r, torch.tensor([0.0, 0.5, 1.0]), atol=1e-6, rtol=0)


def test_dir_heading_pays_only_near_the_target():
    env = dir_env([(1.0, 0.0, 0.0)] * 2, [0.0] * 2, foot_xy=(1.0, 2.3))
    torch.testing.assert_close(dir_heading(env), torch.zeros(2))
