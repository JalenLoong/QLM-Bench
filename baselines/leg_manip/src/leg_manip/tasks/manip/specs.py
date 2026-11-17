"""Task definitions: object, expert trajectory (object frame), success criterion.

The expert parameters are hand-designed like the paper's Fig. 3. They are a first
guess for Go2 and must be checked by running the expert open-loop with the trained
controller (``lm-collect --check-expert``) before collecting demonstrations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import mujoco
import torch

from leg_manip.assets.objects import button_panel_spec, dishwasher_spec
from leg_manip.tasks.manip.mdp import default_expert_vector


@dataclass(frozen=True)
class ManipTaskSpec:
    name: str
    task_id: str
    object_spec_fn: Callable[[], mujoco.MjSpec]
    expert_vector: tuple[float, ...]
    duration_s: float
    object_joint_range: tuple[float, float]
    """Initial object joint position range (e.g. door opening angle)."""
    success_mode: str
    """'max_above': joint exceeds threshold at any time (press).
    'final_below': joint below threshold at the end of the episode (close)."""
    success_threshold: float
    distance_range: tuple[float, float] = (1.0, 1.8)
    bearing_range_deg: tuple[float, float] = (-20.0, 20.0)
    object_yaw_range_deg: tuple[float, float] = (-15.0, 15.0)

    def success(self, joint_trace: torch.Tensor) -> torch.Tensor:
        """joint_trace: (T, N) object joint positions over an episode -> (N,) bool."""
        if self.success_mode == "max_above":
            return (joint_trace > self.success_threshold).any(0)
        if self.success_mode == "final_below":
            return joint_trace[-1] < self.success_threshold
        raise ValueError(self.success_mode)


# Press a hemispherical button (10 cm diameter) on a wall panel, center 0.25 m high.
# The front of the button is at x = -0.05. The foot approaches along the ground,
# rises to button height in front of it and pushes 2 cm into it.
PRESS_BUTTON = ManipTaskSpec(
    name="press_button",
    task_id="LegManip-PressButton-Go2",
    object_spec_fn=button_panel_spec,
    expert_vector=default_expert_vector(
        flag=0,
        ctrl=[
            (-0.70, 0.00, 0.03),
            (-0.45, 0.00, 0.05),
            (-0.30, 0.00, 0.25),
            (-0.15, 0.00, 0.25),
            (-0.03, 0.00, 0.25),
            (-0.03, 0.00, 0.25),
        ],
        weights=[1.0, 1.0, 5.0, 1.0, 10.0, 10.0],
        dir0=(0.5, 0.0, -0.85),
        dir1=(1.0, 0.0, 0.0),
    ),
    duration_s=10.0,
    object_joint_range=(0.0, 0.0),
    success_mode="max_above",
    success_threshold=0.005,
)

# Close a bottom-hinged dishwasher door (hinge 0.08 m high, 0.40 m long) that is
# open by 50-70 deg toward the robot. The foot gets under the outer face near the
# free edge and pushes it up along the door's arc until it is vertical.
CLOSE_DISHWASHER = ManipTaskSpec(
    name="close_dishwasher",
    task_id="LegManip-CloseDishwasher-Go2",
    object_spec_fn=dishwasher_spec,
    expert_vector=default_expert_vector(
        flag=0,
        ctrl=[
            (-0.75, 0.00, 0.03),
            (-0.50, 0.00, 0.08),
            (-0.40, 0.00, 0.16),
            (-0.27, 0.00, 0.27),
            (-0.12, 0.00, 0.38),
            (-0.04, 0.00, 0.40),
        ],
        weights=[1.0, 1.0, 3.0, 3.0, 3.0, 10.0],
        dir0=(0.5, 0.0, -0.85),
        dir1=(1.0, 0.0, 0.2),
    ),
    duration_s=12.0,
    object_joint_range=(0.87, 1.22),
    success_mode="final_below",
    success_threshold=0.087,
)

TASKS: dict[str, ManipTaskSpec] = {t.name: t for t in (PRESS_BUTTON, CLOSE_DISHWASHER)}
