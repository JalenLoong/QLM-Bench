"""Declarative native9 physical identity, with no simulator/model dependency."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROTOCOL_ID = "qlm-native9-physical-v1"
DATASET_SCHEMA = "wam-quadruped-v2.1.0"


def frozen_bundle(kind="contracts_v2"):
    """Return a byte-verified legacy bundle without importing its implementation."""
    if kind not in {"contracts_v2", "dataset_v2"}:
        raise ValueError("Unknown compatibility bundle")
    root = Path(__file__).parents[1] / "compatibility" / kind / "spec"
    lock = json.loads((root / "lock.json").read_text())
    for name, expected in lock["files"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Frozen specification changed: {kind}/{name}")
    return {name: json.loads((root / name).read_text()) for name in lock["files"]}


def physical_contract():
    """Describe physical execution; no latent/chunk or WAM sampling requirement."""
    action = frozen_bundle()["action.json"]
    return {"protocol": PROTOCOL_ID, "source_action_schema": action["id"],
            "action": action, "rates_hz": {"high_level": 50, "controller": 100,
            "physics": 500, "policy_rgb": 50, "observer_diagnostic": 25},
            "policy_camera_keys": ["observation.images.ego", "observation.images.task_centric"],
            "history": "Only completed high-level hold intervals",
            "terminal": "Pre-reset state and RGB; no dummy terminal command",
            "proprioception": "Explicit observation profile; model derivations are consumer-owned"}

