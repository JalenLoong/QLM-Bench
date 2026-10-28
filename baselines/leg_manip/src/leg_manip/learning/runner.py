"""Use the project cloud logger without patching installed rsl_rl/mjlab packages."""

from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo

import torch
from mjlab.rl import MjlabOnPolicyRunner


class ControllerRunner(MjlabOnPolicyRunner):
    def __init__(self, env, train_cfg, log_dir=None, device="cpu"):
        cfg = deepcopy(train_cfg)
        if cfg.get("logger") == "wandb" and log_dir is not None:
            name = cfg.get("run_name") or (
                f"leg-manip-controller-go2-seed{cfg.get('seed', 0)}-"
                + datetime.now(ZoneInfo("Australia/Sydney")).strftime("%Y%m%d-%H%M%S")
            )
            cfg["logger"] = {
                "class_name": "leg_manip.learning.cloud_logging:CloudLogWriter",
                "project_name": cfg["wandb_project"],
                "entity": os.getenv("WANDB_ENTITY") or os.getenv("WANDB_USERNAME"),
                "run_name": name,
                "hf_repo": os.getenv("LEG_MANIP_HF_REPO"),
                "metadata_dir": os.getenv("LEG_MANIP_RUN_DIR"),
                "tags": cfg.get("wandb_tags", ()),
            }
        super().__init__(env, cfg, log_dir, device)
        if cfg.get("init_checkpoint"):
            loaded = torch.load(
                cfg["init_checkpoint"], weights_only=False, map_location=device
            )
            self.alg.warm_start(loaded, cfg.get("init_noise_std"))
