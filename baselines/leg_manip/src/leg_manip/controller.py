"""Load the trained low-level controller for use outside the training loop."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
from mjlab.tasks.registry import load_rl_cfg


def load_controller(
    env: ManagerBasedRlEnv,
    checkpoint: str | Path,
    task_id: str = "LegManip-Track-Go2",
    device: str = "cuda:0",
):
    """Wrap `env` for rsl_rl and load the controller checkpoint.

    Returns:
        (wrapped_env, policy) where ``policy(obs) -> actions`` runs the deterministic
        actor (with its state estimator) on the wrapped env's observations.
    """
    agent_cfg = load_rl_cfg(task_id)
    wrapped = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
    runner = MjlabOnPolicyRunner(
        wrapped, asdict(agent_cfg), log_dir=None, device=device
    )
    runner.load(
        str(checkpoint), load_cfg={"actor": True}, strict=True, map_location=device
    )
    return wrapped, runner.get_inference_policy(device=device)


def resolve_checkpoint(checkpoint: str | None, wandb_run_path: str | None) -> Path:
    """Local checkpoint path, or the latest model_*.pt of a W&B run."""
    if checkpoint is not None:
        path = Path(checkpoint)
        if not path.exists():
            raise FileNotFoundError(path)
        return path
    if wandb_run_path is None:
        raise ValueError("Give --controller or --controller-wandb-run.")
    from mjlab.utils.os import get_wandb_checkpoint_path

    path, _ = get_wandb_checkpoint_path(
        Path("logs/rsl_rl/legmanip_track_go2").resolve(), Path(wandb_run_path), None
    )
    return path
