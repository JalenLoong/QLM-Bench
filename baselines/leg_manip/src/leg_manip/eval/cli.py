"""Part 4: closed-loop evaluation (planner at 10 Hz + controller at 50 Hz).

    uv run lm-eval --task press_button --controller model.pt \
        --planner outputs/planner/press_button/seed0/epoch0250 \
                  outputs/planner/press_button/seed0/epoch0500
    # expert upper bound (ground-truth parameters, no planner):
    uv run lm-eval --task press_button --controller model.pt --expert

Each planner checkpoint is evaluated on `num_episodes` episodes (paper: objects in a
sector in front of the robot; success as defined in the task spec). Results go to
outputs/eval/<task>/ as JSON and optionally to W&B.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import mjlab  # noqa: F401  (configures Warp and mujoco GL before use)
import torch
import tyro
from mjlab.envs import ManagerBasedRlEnv

from leg_manip.collect.rollout import run_episode
from leg_manip.controller import load_controller, resolve_checkpoint
from leg_manip.planner.policy import PlannerPolicy
from leg_manip.tasks.manip.env_cfg import make_manip_env_cfg
from leg_manip.tasks.manip.specs import TASKS


@dataclass
class EvalArgs:
    task: str
    controller: str | None = None
    controller_wandb_run: str | None = None
    planner: tuple[str, ...] = ()
    """Planner checkpoint directories (each with config.json + model.safetensors)."""
    expert: bool = False
    """Evaluate the ground-truth expert parameters instead of a planner."""
    num_episodes: int = 100
    num_envs: int = 100
    seed: int = 1000
    """Evaluation seed, kept apart from the collection seeds."""
    device: str = "cuda:0"
    out_dir: Path = Path("outputs/eval")
    wandb_project: str | None = None
    """Log results to this W&B project if set."""
    wandb_entity: str | None = None


def evaluate(
    env, wrapped, controller, spec, planner_fn, num_episodes: int, *, seed: int = 1000
) -> dict:
    """Replay a fixed sequence of batch-reset seeds for every checkpoint.

    Seeding occurs immediately before each reset, after checkpoint construction
    and any previous inference. All reset events (including robot joints) thus
    receive the same RNG state. Batch width must be kept fixed for comparisons.
    """
    successes, alive, n, visible = 0, 0, 0, 0.0
    per_round = []
    while n < num_episodes:
        if planner_fn is not None and hasattr(planner_fn, "reset"):
            planner_fn.reset()
        reset_seed = seed + n
        batch = run_episode(
            env, wrapped, controller, spec, planner_fn=planner_fn, reset_seed=reset_seed
        )
        take = min(env.num_envs, num_episodes - n)
        s = int(batch.success[:take].sum())
        a = int(batch.alive[:take].sum())
        # Planner frames in which the head camera sees the object at all.
        v = float(batch.num_visible[:, :take].gt(0).float().mean())
        successes, alive, n = successes + s, alive + a, n + take
        visible += v * take
        per_round.append(
            {
                "episodes": take,
                "success": s,
                "alive": a,
                "object_visible_fraction": v,
                "reset_seed": reset_seed,
            }
        )
        print(f"  {n}/{num_episodes} episodes, success so far {successes / n:.1%}")
    return {
        "episodes": n,
        "success_rate": successes / n,
        "fall_rate": 1 - alive / n,
        "object_visible_fraction": visible / n,
        "rounds": per_round,
    }


def main() -> None:
    args = tyro.cli(EvalArgs)
    if not args.expert and not args.planner:
        raise SystemExit("Give --planner <dir> ... or --expert.")
    spec = TASKS[args.task]
    torch.manual_seed(args.seed)
    ckpt = resolve_checkpoint(args.controller, args.controller_wandb_run)
    cfg = make_manip_env_cfg(spec, planner=not args.expert)
    cfg.scene.num_envs = min(args.num_envs, args.num_episodes)
    cfg.seed = args.seed
    env = ManagerBasedRlEnv(cfg=cfg, device=args.device)
    wrapped, controller = load_controller(env, ckpt, device=args.device)

    targets = ["expert"] if args.expert else list(args.planner)
    out_dir = args.out_dir / spec.name
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for target in targets:
        t0 = time.time()
        print(f"[eval] {spec.name}: {target}")
        planner_fn = None if target == "expert" else PlannerPolicy(target, args.device)
        res = evaluate(
            env,
            wrapped,
            controller,
            spec,
            planner_fn,
            args.num_episodes,
            seed=args.seed,
        )
        res.update(
            {
                "task": spec.name,
                "target": target,
                "controller": str(ckpt),
                "planner_info": getattr(planner_fn, "meta", {}).get("info"),
                "seed": args.seed,
                "seconds": round(time.time() - t0, 1),
            }
        )
        results[target] = res
        print(
            f"[eval] {target}: success {res['success_rate']:.1%}, "
            f"falls {res['fall_rate']:.1%}"
        )
        name = (
            "expert"
            if target == "expert"
            else Path(target).as_posix().replace("/", "__")
        )
        (out_dir / f"{name}_seed{args.seed}.json").write_text(json.dumps(res, indent=2))

    if args.wandb_project:
        import wandb

        run = wandb.init(
            project=args.wandb_project,
            entity=args.wandb_entity,
            job_type="eval",
            group=f"eval-{spec.name}",
            config=asdict(args),
        )
        table = wandb.Table(columns=["target", "success_rate", "fall_rate", "episodes"])
        for t, r in results.items():
            table.add_data(t, r["success_rate"], r["fall_rate"], r["episodes"])
        run.log({"eval/results": table})
        run.finish()


if __name__ == "__main__":
    main()
