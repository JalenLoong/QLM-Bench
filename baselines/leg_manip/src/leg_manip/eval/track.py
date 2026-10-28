"""Bilateral full-range tracking acceptance with frozen weights; exits 2 on failure.

Random training-distribution curves (play config: no pushes or toe forces), one
20 s episode per environment, judged after the first `skip_s` seconds.
"""

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
from leg_manip.eval.gate import TRACK_LIMITS, summarize_gate
from leg_manip.tasks.track.env_cfg import CMD, FEET_SENSOR, make_track_env_cfg

LIFT_HEIGHT = 0.05
"""Targets above this height (env frame) require the foot off the ground, as in
the free_gait / manip_ground_contact rewards."""


@dataclass
class TrackEvalArgs:
    checkpoint: Path
    out: Path = Path("outputs/track-eval.json")
    num_envs: int = 64
    seed: int = 1000
    skip_s: float = 2.0
    """Initial transient excluded from the statistics (curves may start away
    from the foot)."""
    device: str = "cuda:0"


def evaluate_leg(args: TrackEvalArgs, leg: int) -> dict:
    cfg = make_track_env_cfg(play=True)
    cfg.commands[CMD].ranges.fr_prob = float(leg)
    cfg.scene.num_envs = args.num_envs
    cfg.seed = args.seed
    # Keep auto reset (see eval.lift): failures are latched in `fell`.
    cfg.auto_reset = True
    env = ManagerBasedRlEnv(cfg, device=args.device)
    try:
        wrapped, policy = load_controller(env, args.checkpoint, device=args.device)
        cmd = env.command_manager.get_term(CMD)
        origin_z = env.scene.env_origins[:, 2]
        steps = int(env.max_episode_length)
        skip = round(args.skip_s / env.step_dt)
        pos, z, contact, raised = [], [], [], []
        fell = torch.zeros(args.num_envs, dtype=torch.bool, device=args.device)
        with torch.inference_mode():
            env.seed(args.seed)
            obs, _ = wrapped.reset()
            for step in range(steps):
                # Sample before stepping: the final timeout resets the episode.
                if step >= skip:
                    err = cmd.ee_pos_w() - cmd.target_pos_w
                    pos.append(err.norm(dim=-1))
                    z.append(err[:, 2].abs())
                    found = env.scene[FEET_SENSOR].data.found
                    contact.append((found[:, leg] > 0).clone())
                    raised.append(cmd.target_pos_w[:, 2] - origin_z > LIFT_HEIGHT)
                obs, _, _, _ = wrapped.step(policy(obs))
                fell |= env.reset_terminated
        raised = torch.stack(raised)
        result = summarize_gate(
            torch.stack(pos),
            torch.stack(z),
            torch.stack(contact),
            fell,
            TRACK_LIMITS,
            contact_mask=raised,
        )
        result["raised_target_fraction"] = float(raised.float().mean())
        return result
    finally:
        env.close()


def main() -> None:
    args = tyro.cli(TrackEvalArgs)
    if args.num_envs < 1:
        raise ValueError("num_envs must be positive")
    sha = hashlib.sha256(args.checkpoint.read_bytes()).hexdigest()
    results = {name: evaluate_leg(args, leg) for leg, name in enumerate(("FL", "FR"))}
    report = {
        "passed": all(r["passed"] for r in results.values()),
        "task": "LegManip-Track-Go2",
        "seed": args.seed,
        "checkpoint": str(args.checkpoint.resolve()),
        "checkpoint_sha256": sha,
        "skip_seconds": args.skip_s,
        "limits": {
            "position_m": TRACK_LIMITS.position_m,
            "z_m": TRACK_LIMITS.z_m,
            "raised_contact_fraction": TRACK_LIMITS.contact_fraction,
            "success_rate_min": str(TRACK_LIMITS.success_rate),
            "fall_rate_max": str(TRACK_LIMITS.fall_rate),
        },
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
