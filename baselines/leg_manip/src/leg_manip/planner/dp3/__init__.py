"""Core of 3D Diffusion Policy (DP3), vendored from
https://github.com/YanjieZe/3D-Diffusion-Policy (commit 47385d9, MIT License,
see LICENSE in this directory).

Only the policy, point cloud encoder, conditional UNet, normalizer and EMA are kept.
Changes from upstream: package paths flattened; the unused pytorch3d / torchvision /
termcolor imports removed; configs are plain dicts instead of OmegaConf (dp3.py builds
the obs shape dict directly, pointnet_extractor.py copies the encoder config).
"""

from leg_manip.planner.dp3.dp3 import DP3
from leg_manip.planner.dp3.ema_model import EMAModel
from leg_manip.planner.dp3.normalizer import LinearNormalizer, SingleFieldLinearNormalizer

__all__ = ["DP3", "EMAModel", "LinearNormalizer", "SingleFieldLinearNormalizer"]
