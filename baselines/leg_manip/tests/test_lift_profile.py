"""Sampling and behavior gates for the bounded near-foot training stage."""

from types import SimpleNamespace

import pytest
import torch


@pytest.mark.parametrize("leg", [0, 1])
def test_lift_sampling_uses_selected_fresh_foot_and_only_resets_requested_envs(leg):
    from leg_manip.tasks.track.lift import LiftTrajectoryCommandCfg

    n = 3
    feet = torch.tensor(
        [
            [[0.2, 0.1, 0.03], [0.2, -0.1, 0.02]],
            [[10.2, 20.1, 5.03], [10.2, 19.9, 5.02]],
            [[-2.8, -3.9, 0.04], [-2.8, -4.1, 0.03]],
        ]
    )
    robot = SimpleNamespace(
        data=SimpleNamespace(
            site_pos_w=feet,
            body_link_pos_w=feet + torch.tensor([0.0, 0.0, 0.2]),
            root_link_pos_w=torch.zeros(n, 3),
            root_link_quat_w=torch.tensor([[1.0, 0.0, 0.0, 0.0]]).repeat(n, 1),
        ),
        find_sites=lambda names, preserve_order: ([0, 1], list(names)),
        find_bodies=lambda names, preserve_order: ([0, 1], list(names)),
    )
    scene = type("Scene", (dict,), {})(robot=robot)
    scene.env_origins = torch.tensor(
        [[0.0, 0.0, 0.0], [10.0, 20.0, 5.0], [-3.0, -4.0, 0.0]]
    )
    env = SimpleNamespace(scene=scene, num_envs=n, device="cpu", max_episode_length=500)
    cfg = LiftTrajectoryCommandCfg(
        forced_leg=leg, resampling_time_range=(1e9, 1e9), lift_range=(0.08, 0.08)
    )
    cmd = cfg.build(env)
    cmd.params.ctrl.fill_(-99.0)
    ids = torch.tensor([1])
    cmd._resample_command(ids)
    # Sampling must happen after forward kinematics, not in the reset callback.
    feet[1, leg] += torch.tensor([0.02, 0.01, 0.005])
    cmd._update_command(ids)
    # Resets spawn the robot above its standing height, so the fresh foot can
    # still be airborne. The lift starts on the ground below it.
    start = feet[1, leg].clone()
    start[2] = 5.0 + cfg.foot_rest_height
    torch.testing.assert_close(cmd.params.ctrl[1, 0], start)
    torch.testing.assert_close(
        cmd.params.ctrl[1, -1], start + torch.tensor([0.0, 0.0, 0.08])
    )
    # The calf direction still comes from the fresh foot, not the ground start.
    knee = robot.data.body_link_pos_w[1, leg]
    direction = torch.nn.functional.normalize(feet[1, leg] - knee, dim=0)
    torch.testing.assert_close(cmd.params.dir0[1], direction)
    assert cmd.params.flag[1].item() == leg
    assert (cmd.params.ctrl[[0, 2]] == -99).all()
    cmd.phase_time[1] = 8.0
    cmd._update_command(ids)
    torch.testing.assert_close(cmd.target_pos_w[1], cmd.params.ctrl[1, -1])


def test_lift_gate_rejects_grounded_or_wrong_leg_despite_low_position_error():
    from leg_manip.eval.lift import summarize_lift

    error = torch.full((100, 10), 0.02)
    z_error = torch.full_like(error, 0.01)
    fell = torch.zeros(10, dtype=torch.bool)
    clear = torch.zeros_like(error, dtype=torch.bool)
    assert summarize_lift(error, z_error, clear, fell)["passed"]
    assert not summarize_lift(error, z_error, ~clear, fell)["passed"]


def test_lift_gate_counts_failed_envs_instead_of_hiding_them_in_mean():
    from leg_manip.eval.lift import summarize_lift

    error = torch.full((100, 10), 0.01)
    error[:, :2] = 0.15  # Batch mean is only 0.038 m; two envs still fail.
    r = summarize_lift(
        error,
        torch.zeros_like(error),
        torch.zeros_like(error, dtype=torch.bool),
        torch.zeros(10, dtype=torch.bool),
    )
    assert not r["passed"] and r["successful_envs"] == 8


def test_lift_gate_rejects_nonfinite_measurements_and_falls():
    from leg_manip.eval.lift import summarize_lift

    error = torch.zeros(20, 10)
    contact = torch.zeros_like(error, dtype=torch.bool)
    fell = torch.zeros(10, dtype=torch.bool)
    fell[0] = True
    assert not summarize_lift(error, error.clone(), contact, fell)["passed"]
    fell[:] = False
    error[0, 0] = float("nan")
    r = summarize_lift(error, torch.zeros_like(error), contact, fell)
    assert not r["passed"] and r["nonfinite_envs"] == 1


def test_lift_gate_requires_a_nonempty_time_window():
    from leg_manip.eval.lift import summarize_lift

    with pytest.raises(ValueError):
        summarize_lift(
            torch.empty(0, 10),
            torch.empty(0, 10),
            torch.empty(0, 10, dtype=torch.bool),
            torch.zeros(10, dtype=torch.bool),
        )


def test_lift_gate_accepts_exact_success_and_fall_boundaries():
    from leg_manip.eval.lift import summarize_lift

    error = torch.zeros(20, 20)
    error[:, 1] = 0.15
    fell = torch.zeros(20, dtype=torch.bool)
    fell[0] = True
    r = summarize_lift(
        error, torch.zeros_like(error), torch.zeros_like(error, dtype=torch.bool), fell
    )
    assert r["successful_envs"] == 18 and r["passed"]


@pytest.mark.parametrize("reset_at_horizon", [False, True])
def test_evaluation_continues_after_early_fall_without_counting_replacement(
    monkeypatch, tmp_path, reset_at_horizon
):
    from leg_manip.eval import lift

    # Characterize mjlab's "must reset before stepping again" contract at the
    # physics boundary. The actual evaluator and success accounting remain real.
    cfg = SimpleNamespace(scene=SimpleNamespace(num_envs=20), seed=0, auto_reset=True)
    monkeypatch.setattr(lift, "make_lift_env_cfg", lambda **_: cfg)
    failed = torch.zeros(20, dtype=torch.bool)
    cmd = SimpleNamespace(
        target_pos_w=torch.zeros(20, 3), ee_pos_w=lambda: torch.zeros(20, 3)
    )
    contact = torch.ones(20, 4)
    contact[:, 0] = 0
    env = SimpleNamespace(
        max_episode_length=5,
        step_dt=0.1,
        reset_terminated=failed,
        seed=lambda _: None,
        close=lambda: None,
        command_manager=SimpleNamespace(get_term=lambda _: cmd),
        scene={lift.FEET_SENSOR: SimpleNamespace(data=SimpleNamespace(found=contact))},
    )
    count = 0

    def step(_):
        nonlocal count
        if failed.any() and not cfg.auto_reset:
            raise RuntimeError("reset terminated environments before stepping")
        count += 1
        failed[:] = False
        if count == 1:
            failed[0] = True
        if count == 5 and reset_at_horizon:
            # A horizon reset installs a new command, which must not be scored
            # as a sample from the episode that just finished.
            cmd.target_pos_w.fill_(1.0)
        return None, None, None, None

    wrapped = SimpleNamespace(reset=lambda: (None, None), step=step)
    monkeypatch.setattr(lift, "ManagerBasedRlEnv", lambda *a, **kw: env)
    monkeypatch.setattr(
        lift, "load_controller", lambda *a, **kw: (wrapped, lambda _: None)
    )
    args = lift.LiftEvalArgs(
        checkpoint=tmp_path / "unused.pt", num_envs=20, device="cpu"
    )
    result = lift.evaluate_leg(args, 0)
    assert count == 5
    assert result["fall_rate"] == 0.05
    assert result["successful_envs"] == 19 and result["passed"]
