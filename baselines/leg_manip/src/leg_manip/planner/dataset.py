"""Demonstration dataset for DP3, held entirely on the training device.

Pure PyTorch / numpy / zarr: runs on the AMD cluster (no simulator imports).

Each sample is an observation window of ``n_obs_steps`` frames and an action window
of ``horizon`` frames starting at the same time step, with edge padding at episode
boundaries (same convention as DP3's SequenceSampler with pad_before =
n_obs_steps - 1 and pad_after = n_action_steps - 1).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import torch
import zarr

KEYS = ("point_cloud", "state", "action")


class DemoDataset:
    """Validate demos before device transfer and split whole episodes.

    Targets must be finite 31D vectors with binary flags and unit calf directions
    (absolute norm tolerance 1e-3). ``fingerprint`` hashes the validated float32
    arrays, episode boundaries and attributes for training-resume compatibility.
    """

    def __init__(
        self,
        path: str | Path,
        horizon: int,
        n_obs_steps: int,
        n_action_steps: int,
        val_ratio: float = 0.04,
        seed: int = 0,
        device: str = "cuda",
    ) -> None:
        if min(horizon, n_obs_steps, n_action_steps) < 1:
            raise ValueError("horizon and observation/action steps must be positive")
        if n_obs_steps - 1 + n_action_steps > horizon:
            raise ValueError("observation/action steps exceed horizon")
        if not 0 <= val_ratio < 1:
            raise ValueError("val_ratio must be in [0, 1)")
        root = zarr.open_group(str(path), mode="r")
        self.attrs = dict(root.attrs)
        arrays = {
            k: np.ascontiguousarray(root["data"][k][:], dtype=np.float32) for k in KEYS
        }
        action = arrays["action"]
        if action.ndim != 2 or action.shape[1] != 31 or len(action) == 0:
            raise ValueError("action shape must be (nonzero frames, 31)")
        n_frames = len(action)
        cloud = arrays["point_cloud"]
        if arrays["state"].shape != (n_frames, 17):
            raise ValueError("state shape must be (action frames, 17)")
        if (
            cloud.ndim != 3
            or cloud.shape[0] != n_frames
            or cloud.shape[1] < 1
            or cloud.shape[2] != 3
        ):
            raise ValueError("point_cloud shape must be (action frames, points > 0, 3)")
        for key, value in arrays.items():
            if not np.isfinite(value).all():
                raise ValueError(f"{key} must contain only finite values")
        if not np.isin(action[:, 0], (0.0, 1.0)).all():
            raise ValueError("action flag must be 0 (FL) or 1 (FR)")
        directions = action[:, 25:31].reshape(-1, 2, 3)
        if not np.allclose(np.linalg.norm(directions, axis=-1), 1.0, atol=1e-3, rtol=0):
            raise ValueError("action must contain unit directions for both endpoints")
        ends = np.asarray(root["meta"]["episode_ends"][:])
        if (
            ends.ndim != 1
            or len(ends) == 0
            or not np.issubdtype(ends.dtype, np.integer)
            or ends[0] <= 0
            or np.any(np.diff(ends) <= 0)
            or ends[-1] != n_frames
        ):
            raise ValueError(
                "episode_ends must increase strictly and end at frame count"
            )
        ends = ends.astype(np.int64)
        digest = hashlib.sha256(json.dumps(self.attrs, sort_keys=True).encode())
        for key, value in {**arrays, "episode_ends": ends}.items():
            digest.update(f"{key}:{value.shape}:{value.dtype}".encode())
            digest.update(memoryview(value).cast("B"))
        self.fingerprint = digest.hexdigest()
        self.data = {k: torch.from_numpy(v).to(device) for k, v in arrays.items()}
        starts = np.concatenate([[0], ends[:-1]])
        n_ep = len(ends)
        rng = np.random.default_rng(seed)
        n_val = int(round(val_ratio * n_ep)) if n_ep > 1 else 0
        n_val = min(max(n_val, 1 if n_ep > 1 and val_ratio > 0 else 0), n_ep - 1)
        val_eps = set(rng.choice(n_ep, size=n_val, replace=False).tolist())
        self.horizon, self.n_obs_steps = horizon, n_obs_steps
        train_idx, val_idx = [], []
        train_frames = np.zeros(n_frames, dtype=bool)
        pad_before, pad_after = n_obs_steps - 1, n_action_steps - 1
        for e in range(n_ep):
            s, t = int(starts[e]), int(ends[e])
            if e not in val_eps:
                train_frames[s:t] = True
            for i in range(s - pad_before, t - horizon + pad_after + 1):
                obs_i = np.clip(np.arange(i, i + n_obs_steps), s, t - 1)
                act_i = np.clip(np.arange(i, i + horizon), s, t - 1)
                (val_idx if e in val_eps else train_idx).append(
                    np.concatenate([obs_i, act_i])
                )
        if not train_idx:
            raise ValueError("Dataset has no training windows for these temporal sizes")
        self.train_frame_mask = torch.as_tensor(train_frames, device=device)
        self.train_index = torch.as_tensor(
            np.array(train_idx), dtype=torch.long, device=device
        )
        self.val_index = (
            torch.as_tensor(np.array(val_idx), device=device) if val_idx else None
        )
        self.num_episodes = n_ep
        self.num_val_episodes = n_val

    @property
    def shape_meta(self) -> dict:
        return {
            "obs": {
                "point_cloud": {"shape": list(self.data["point_cloud"].shape[1:])},
                "agent_pos": {"shape": list(self.data["state"].shape[1:])},
            },
            "action": {"shape": list(self.data["action"].shape[1:])},
        }

    def batch(self, rows: torch.Tensor) -> dict:
        """rows: (B, n_obs_steps + horizon) frame indices -> DP3 batch dict."""
        o, h = self.n_obs_steps, self.horizon
        obs_rows, act_rows = rows[:, :o], rows[:, o : o + h]
        return {
            "obs": {
                "point_cloud": self.data["point_cloud"][obs_rows],
                "agent_pos": self.data["state"][obs_rows],
            },
            "action": self.data["action"][act_rows],
        }

    def normalizer_data(self) -> dict[str, torch.Tensor]:
        """Unpadded training-episode frames only; validation never affects fitting."""
        return {
            "action": self.data["action"][self.train_frame_mask],
            "agent_pos": self.data["state"][self.train_frame_mask],
            "point_cloud": self.data["point_cloud"][self.train_frame_mask],
        }
