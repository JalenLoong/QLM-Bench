"""Demonstration file format (pure numpy / zarr, importable without a simulator).

Layout (DP3 style): data/{point_cloud, state, action} stacked over all frames, and
meta/episode_ends with the cumulative frame count of each episode.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import zarr


def write_zarr(path: Path, episodes: list[dict[str, np.ndarray]], attrs: dict) -> None:
    """DP3-style layout: data/{point_cloud,state,action}, meta/episode_ends."""
    root = zarr.open_group(str(path), mode="w")
    data = root.create_group("data")
    meta = root.create_group("meta")
    for key in ("point_cloud", "state", "action"):
        arr = np.concatenate([e[key] for e in episodes], axis=0).astype(np.float32)
        chunks = (min(100, arr.shape[0]),) + arr.shape[1:]
        data.create_dataset(key, data=arr, chunks=chunks)
    ends = np.cumsum([len(e["action"]) for e in episodes]).astype(np.int64)
    meta.create_dataset("episode_ends", data=ends)
    root.attrs.update(attrs)
