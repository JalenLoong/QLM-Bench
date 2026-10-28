"""Evaluation reset reproducibility, independent of inference RNG consumption."""

import json
from pathlib import Path

import torch
from test_rollout import make_cpu_rollout

from leg_manip.eval import cli
from leg_manip.eval.cli import evaluate
from leg_manip.tasks.manip.specs import PRESS_BUTTON


def test_evaluation_initializations_ignore_target_order_and_inference_rng(monkeypatch):
    env, wrapped = make_cpu_rollout(
        monkeypatch, PRESS_BUTTON, [[0.0, 0.0]] * 12, planner=True
    )
    initializations = {"A": [], "B": []}

    def run_target(name, draws):
        # Checkpoint construction consumes randomness before evaluation begins.
        torch.rand(draws)

        def planner(cloud, state, first):
            if first:
                initializations[name].append(
                    torch.cat([cloud[:, 0], state], -1).clone()
                )
            torch.randn(draws)
            return torch.tensor([PRESS_BUTTON.expert_vector] * env.num_envs)

        return evaluate(
            env, wrapped, lambda obs: torch.zeros(2, 12), PRESS_BUTTON, planner, 5
        )

    run_target("A", 1)
    run_target("B", 11)
    first_a = initializations["A"]
    initializations = {"A": [], "B": []}
    run_target("B", 37)
    result = run_target("A", 503)
    assert len(initializations["A"]) == 3
    for before, after in zip(first_a, initializations["A"], strict=True):
        torch.testing.assert_close(before, after, rtol=0, atol=0)
    # Different rounds still sample different initializations.
    assert not torch.equal(first_a[0], first_a[1])
    assert result["episodes"] == 5
    assert result["object_visible_fraction"] == 1
    assert [r["episodes"] for r in result["rounds"]] == [2, 2, 1]
    assert [r["reset_seed"] for r in result["rounds"]] == [1000, 1002, 1004]


def test_eval_cli_uses_custom_seed_for_each_batch(monkeypatch, tmp_path):
    env, wrapped = make_cpu_rollout(monkeypatch, PRESS_BUTTON, [[0.0, 0.0]] * 4)
    args = cli.EvalArgs(
        task="press_button",
        controller="unused.pt",
        expert=True,
        num_episodes=3,
        num_envs=2,
        seed=17,
        device="cpu",
        out_dir=tmp_path,
    )
    monkeypatch.setattr(cli.tyro, "cli", lambda _: args)
    monkeypatch.setattr(cli, "resolve_checkpoint", lambda *a: Path("unused.pt"))
    monkeypatch.setattr(cli, "ManagerBasedRlEnv", lambda **kw: env)
    monkeypatch.setattr(
        cli,
        "load_controller",
        lambda *a, **kw: (wrapped, lambda obs: torch.zeros(2, 12)),
    )
    cli.main()
    result = json.loads((tmp_path / "press_button/expert_seed17.json").read_text())
    assert [r["reset_seed"] for r in result["rounds"]] == [17, 19]
    assert result["episodes"] == 3
