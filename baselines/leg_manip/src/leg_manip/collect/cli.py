"""Part 3: collect expert demonstrations (or check the expert open-loop).

    # Expert success rate with the trained controller, nothing saved:
    uv run lm-collect --task press_button --controller model.pt --check-expert

    # 100 successful demonstrations of 200 frames each -> data/demos/press_button.zarr
    uv run lm-collect --task press_button --controller model.pt --num-demos 100

Only successful, non-terminated episodes are kept (paper: 100 trajectories per
task, 200 timesteps each).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import mjlab  # noqa: F401  (configures Warp and mujoco GL before use)
import numpy as np
import torch
import tyro
from mjlab.envs import ManagerBasedRlEnv

from leg_manip.collect.rollout import run_episode
from leg_manip.controller import load_controller, resolve_checkpoint
from leg_manip.demo_io import write_zarr
from leg_manip.tasks.manip.env_cfg import make_manip_env_cfg
from leg_manip.tasks.manip.specs import TASKS


@dataclass
class CollectArgs:
    task: str
    """Task name: press_button | close_dishwasher."""
    controller: str | None = None
    """Low-level controller checkpoint (model_*.pt)."""
    controller_wandb_run: str | None = None
    """Alternatively, a W&B run path of the controller training (entity/project/id)."""
    num_demos: int = 100
    num_envs: int = 100
    """Parallel envs per round; lower it on a 16 GB GPU."""
    max_rounds: int = 20
    out: Path | None = None
    """Output zarr (default data/demos/<task>.zarr)."""
    check_expert: bool = False
    """Only report the expert success rate; save nothing."""
    keep_failed: bool = False
    """Debug only: also keep unsuccessful (but not fallen) episodes, e.g. to smoke
    test the planner pipeline before the controller is trained."""
    seed: int = 0
    device: str = "cuda:0"
    num_points: int = 768
    extra_attrs: dict[str, str] = field(default_factory=dict)


def main() -> None:
    args = tyro.cli(CollectArgs)
    spec = TASKS[args.task]
    torch.manual_seed(args.seed)
    ckpt = resolve_checkpoint(args.controller, args.controller_wandb_run)

    cfg = make_manip_env_cfg(spec)
    cfg.scene.num_envs = args.num_envs
    cfg.seed = args.seed
    env = ManagerBasedRlEnv(cfg=cfg, device=args.device)
    wrapped, policy = load_controller(env, ckpt, device=args.device)

    kept: list[dict[str, np.ndarray]] = []
    stats = {"episodes": 0, "success": 0, "terminated": 0}
    t0 = time.time()
    for rnd in range(args.max_rounds):
        batch = run_episode(env, wrapped, policy, spec, num_points=args.num_points)
        stats["episodes"] += args.num_envs
        stats["success"] += int(batch.success.sum())
        stats["terminated"] += int((~batch.alive).sum())
        rate = stats["success"] / stats["episodes"]
        print(
            f"[round {rnd}] success {int(batch.success.sum())}/{args.num_envs} "
            f"(total {rate:.1%}), fell {int((~batch.alive).sum())}, "
            f"object visible in {batch.num_visible.gt(0).float().mean():.1%} of frames"
        )
        if args.check_expert:
            continue
        keep = batch.alive if args.keep_failed else batch.success
        for i in keep.nonzero().flatten().tolist():
            kept.append(
                {
                    "point_cloud": batch.point_cloud[:, i].cpu().numpy(),
                    "state": batch.state[:, i].cpu().numpy(),
                    "action": batch.action[:, i].cpu().numpy(),
                }
            )
        if len(kept) >= args.num_demos:
            break

    summary = {
        **stats,
        "success_rate": stats["success"] / max(stats["episodes"], 1),
        "seconds": round(time.time() - t0, 1),
    }
    print("summary:", json.dumps(summary))
    if args.check_expert:
        return
    if not kept:
        raise SystemExit("No demonstrations to save (check the controller / expert).")
    if len(kept) < args.num_demos:
        print(f"[WARN] only {len(kept)} demos after {args.max_rounds} rounds")
    out = args.out or Path("data/demos") / f"{args.task}.zarr"
    out.parent.mkdir(parents=True, exist_ok=True)
    attrs = {
        "task": spec.name,
        "num_episodes": min(len(kept), args.num_demos),
        "frames_per_episode": int(kept[0]["action"].shape[0]) if kept else 0,
        "planner_hz": 10,
        "duration_s": spec.duration_s,
        "expert_vector": list(spec.expert_vector),
        "controller_checkpoint": str(ckpt),
        "keep_failed": args.keep_failed,
        "collection": summary,
        **args.extra_attrs,
    }
    write_zarr(out, kept[: args.num_demos], attrs)
    print(f"wrote {out} ({attrs['num_episodes']} episodes)")


if __name__ == "__main__":
    main()
