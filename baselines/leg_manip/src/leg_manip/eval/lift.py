"""Bilateral lift acceptance with frozen weights; exits 2 on a failed gate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import mjlab  # noqa: F401 (initializes Warp/GL before simulator imports)
import torch
import tyro
from mjlab.envs import ManagerBasedRlEnv

from leg_manip.controller import load_controller
from leg_manip.eval.gate import LIFT_LIMITS, summarize_gate
from leg_manip.tasks.track.env_cfg import CMD, FEET_SENSOR
from leg_manip.tasks.track.lift import make_lift_env_cfg


def summarize_lift(
    position_error: torch.Tensor,
    z_error: torch.Tensor,
    ground_contact: torch.Tensor,
    fell: torch.Tensor,
) -> dict:
    """Accept >=90% of environments on each leg and <=5% early terminations.

    Inputs cover the last two seconds (T,N). Each successful environment must
    have mean 3D error <=5cm, z error <=3cm and ground contact <=10% of samples.
    All nonfinite or negative error values fail the whole gate.
    """
    return summarize_gate(position_error, z_error, ground_contact, fell, LIFT_LIMITS)


@dataclass
class LiftEvalArgs:
    checkpoint: Path
    out: Path = Path("outputs/lift-eval.json")
    num_envs: int = 64
    seed: int = 1000
    device: str = "cuda:0"


def evaluate_leg(args: LiftEvalArgs, leg: int) -> dict:
    cfg = make_lift_env_cfg(play=True, forced_leg=leg)
    cfg.scene.num_envs = args.num_envs
    cfg.seed = args.seed
    # mjlab requires terminated worlds to reset before the next step. Preserve
    # the original failure mask so replacement episodes cannot qualify a policy.
    cfg.auto_reset = True
    env = ManagerBasedRlEnv(cfg, device=args.device)
    try:
        wrapped, policy = load_controller(env, args.checkpoint, device=args.device)
        cmd = env.command_manager.get_term(CMD)
        steps = int(env.max_episode_length)
        window = round(2.0 / env.step_dt)
        pos, z, contact = [], [], []
        fell = torch.zeros(args.num_envs, dtype=torch.bool, device=args.device)
        with torch.inference_mode():
            env.seed(args.seed)
            obs, _ = wrapped.reset()
            for step in range(steps):
                # Sample before stepping: the final timeout may replace the
                # command and robot state with the next episode's reset state.
                if step >= steps - window:
                    err = cmd.ee_pos_w() - cmd.target_pos_w
                    pos.append(err.norm(dim=-1))
                    z.append(err[:, 2].abs())
                    found = env.scene[FEET_SENSOR].data.found
                    contact.append((found[:, leg] > 0).clone())
                obs, _, _, _ = wrapped.step(policy(obs))
                fell |= env.reset_terminated
        return summarize_lift(
            torch.stack(pos), torch.stack(z), torch.stack(contact), fell
        )
    finally:
        env.close()


def main() -> None:
    args = tyro.cli(LiftEvalArgs)
    if args.num_envs < 1:
        raise ValueError("num_envs must be positive")
    sha = hashlib.sha256(args.checkpoint.read_bytes()).hexdigest()
    results = {name: evaluate_leg(args, leg) for leg, name in enumerate(("FL", "FR"))}
    report = {
        "passed": all(r["passed"] for r in results.values()),
        "task": "LegManip-Lift-Go2",
        "seed": args.seed,
        "checkpoint": str(args.checkpoint.resolve()),
        "checkpoint_sha256": sha,
        "window_seconds": 2.0,
        "legs": results,
    }
    if hashlib.sha256(args.checkpoint.read_bytes()).hexdigest() != sha:
        raise RuntimeError("Checkpoint changed during evaluation")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps(report, indent=2, allow_nan=False))
    raise SystemExit(0 if report["passed"] else 2)


if __name__ == "__main__":
    main()
