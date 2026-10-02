"""Spawn the OASIS basket with its source-authored physics unchanged."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json


BASKET_ASSET_ROOT = (
    Path(__file__).resolve().parent / "third_party" / "oasis" / "lift_basket"
)
BASKET_USD_PATH = BASKET_ASSET_ROOT / "basket.usd"
BASKET_MASS_KG = 0.53
BASKET_ROOT_HEIGHT_ABOVE_BOTTOM_M = 0.0
# The source default prim ALREADY authors a +90 degree X rotation. UsdFileCfg
# replaces that root orientation, so compose it with the source-stage Y-up to
# task Z-up / +90 degree yaw conversion instead of discarding it. In XYZW:
# (0.5, 0.5, 0.5, 0.5) * (sqrt(.5), 0, 0, sqrt(.5)).
# The mesh's physical up axis in the rigid body's LOCAL frame is -Z, not +Y.
BASKET_INITIAL_ORIENTATION_XYZW = (2.0 ** -0.5, 2.0 ** -0.5, 0.0, 0.0)


def spawn_lift_basket_asset(
    prim_path: str,
    position: tuple[float, float, float],
    usd_path: str | Path | None = None,
) -> Any:
    """Spawn the audited OASIS USD as one source-authored rigid object.

    Simulator imports stay local so provenance and package-data tests can
    inspect this module without starting Kit.
    """

    selected = BASKET_USD_PATH if usd_path is None else Path(usd_path)
    if not selected.is_file():
        raise FileNotFoundError(f"LiftBasket visual asset is missing: {selected}")
    # Resource relocation must retain the reviewed source USD and textures.
    manifest = json.loads((BASKET_ASSET_ROOT / "asset_manifest.json").read_text())
    for relative, expected in manifest["files"].items():
        payload = selected.parent / relative
        h = hashlib.sha256()
        with payload.open("rb") as stream:
            for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                h.update(block)
        if payload.stat().st_size != expected["size_bytes"] or h.hexdigest() != expected["sha256"]:
            raise ValueError(f"LiftBasket source resource hash mismatch: {relative}")

    import isaaclab.sim as sim_utils
    from isaaclab.assets import RigidObject, RigidObjectCfg

    asset_cfg = sim_utils.UsdFileCfg(usd_path=str(selected))
    asset_cfg.func(
        prim_path,
        asset_cfg,
        translation=position,
        # Coordinate conversion only: rotate the source Y-up visual, collision
        # mesh, rigid body, mass properties, and physics material together.
        orientation=BASKET_INITIAL_ORIENTATION_XYZW,
    )

    return RigidObject(
        RigidObjectCfg(
            prim_path=prim_path,
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=position,
                rot=BASKET_INITIAL_ORIENTATION_XYZW,
            ),
        )
    )


__all__ = [
    "BASKET_ASSET_ROOT",
    "BASKET_MASS_KG",
    "BASKET_ROOT_HEIGHT_ABOVE_BOTTOM_M",
    "BASKET_USD_PATH",
    "BASKET_INITIAL_ORIENTATION_XYZW",
    "spawn_lift_basket_asset",
]
