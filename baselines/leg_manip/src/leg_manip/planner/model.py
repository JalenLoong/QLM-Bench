"""DP3 planner construction and checkpoint I/O (pure PyTorch, no simulator)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from diffusers.schedulers.scheduling_ddim import DDIMScheduler
from safetensors.torch import load_file, save_file

from leg_manip.planner.dp3 import DP3

CONFIG_NAME = "config.json"
WEIGHTS_NAME = "model.safetensors"


@dataclass
class PlannerModelCfg:
    """DP3 hyper-parameters; defaults follow DP3's dp3.yaml except the horizon."""

    horizon: int = 4
    """Action window. Our action (trajectory parameters) is nearly constant within an
    episode, so a short window suffices; must be divisible by 4 (two downsamplings)."""
    n_obs_steps: int = 2
    n_action_steps: int = 1
    down_dims: tuple[int, ...] = (512, 1024, 2048)
    diffusion_step_embed_dim: int = 128
    encoder_output_dim: int = 64
    kernel_size: int = 5
    n_groups: int = 8
    num_train_timesteps: int = 100
    num_inference_steps: int = 10
    pointcloud_encoder_cfg: dict = field(
        default_factory=lambda: {
            "in_channels": 3,
            "out_channels": 64,
            "use_layernorm": True,
            "final_norm": "layernorm",
            "normal_channel": False,
        }
    )

    def validate(self) -> None:
        """Reject windows the UNet cannot represent or return as executable actions."""
        if min(self.horizon, self.n_obs_steps, self.n_action_steps) < 1:
            raise ValueError("horizon and observation/action steps must be positive")
        if self.n_obs_steps - 1 + self.n_action_steps > self.horizon:
            raise ValueError("observation/action steps exceed horizon")
        if not self.down_dims or self.horizon % 2 ** (len(self.down_dims) - 1):
            raise ValueError(
                "horizon must be divisible by the UNet downsampling factor"
            )
        if not 1 <= self.num_inference_steps <= self.num_train_timesteps:
            raise ValueError("inference steps must be in [1, num_train_timesteps]")


def make_scheduler(cfg: PlannerModelCfg) -> DDIMScheduler:
    return DDIMScheduler(
        num_train_timesteps=cfg.num_train_timesteps,
        beta_start=0.0001,
        beta_end=0.02,
        beta_schedule="squaredcos_cap_v2",
        clip_sample=True,
        set_alpha_to_one=True,
        steps_offset=0,
        prediction_type="sample",
    )


def build_policy(cfg: PlannerModelCfg, shape_meta: dict) -> DP3:
    """Build a validated DP3 with one authoritative point-cloud encoder width."""
    cfg.validate()
    return DP3(
        shape_meta=shape_meta,
        noise_scheduler=make_scheduler(cfg),
        horizon=cfg.horizon,
        n_action_steps=cfg.n_action_steps,
        n_obs_steps=cfg.n_obs_steps,
        num_inference_steps=cfg.num_inference_steps,
        obs_as_global_cond=True,
        diffusion_step_embed_dim=cfg.diffusion_step_embed_dim,
        down_dims=tuple(cfg.down_dims),
        kernel_size=cfg.kernel_size,
        n_groups=cfg.n_groups,
        condition_type="film",
        use_down_condition=True,
        use_mid_condition=True,
        use_up_condition=True,
        encoder_output_dim=cfg.encoder_output_dim,
        use_pc_color=False,
        pointnet_type="pointnet",
        pointcloud_encoder_cfg={
            **cfg.pointcloud_encoder_cfg,
            "out_channels": cfg.encoder_output_dim,
        },
    )


def save_checkpoint(
    out_dir: Path, policy: DP3, cfg: PlannerModelCfg, shape_meta: dict, info: dict
) -> None:
    """Weights (safetensors, including the fitted normalizer) + config.json."""
    out_dir.mkdir(parents=True, exist_ok=True)
    state = {k: v.detach().contiguous().cpu() for k, v in policy.state_dict().items()}
    save_file(state, str(out_dir / WEIGHTS_NAME))
    meta = {"model": asdict(cfg), "shape_meta": shape_meta, "info": info}
    (out_dir / CONFIG_NAME).write_text(json.dumps(meta, indent=2, default=str))


def load_checkpoint(ckpt_dir: str | Path, device: str = "cuda") -> tuple[DP3, dict]:
    ckpt_dir = Path(ckpt_dir)
    meta = json.loads((ckpt_dir / CONFIG_NAME).read_text())
    model_cfg = PlannerModelCfg(
        **{**meta["model"], "down_dims": tuple(meta["model"]["down_dims"])}
    )
    policy = build_policy(model_cfg, meta["shape_meta"])
    state = load_file(str(ckpt_dir / WEIGHTS_NAME))
    policy.load_state_dict(state)
    policy.to(device).eval()
    return policy, meta
