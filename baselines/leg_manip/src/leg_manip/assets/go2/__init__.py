"""Unitree Go2 entity for mjlab, following mjlab's Go1 constants.

The MJCF is derived from mujoco_menagerie (see the header of go2.xml). Actuator gains
use mjlab's recipe: reflected rotor inertia with a 10 Hz natural frequency and a
damping ratio of 2. Go2's rotor inertia is not published in menagerie, so the Go1
value is reused with Go2's gear ratios (6.33, knee x1.5).
"""

from __future__ import annotations

from pathlib import Path

import mujoco
from mjlab.actuator import BuiltinPositionActuatorCfg
from mjlab.entity import EntityArticulationInfoCfg, EntityCfg
from mjlab.utils.actuator import ElectricActuator, reflected_inertia
from mjlab.utils.spec_config import CollisionCfg

GO2_XML: Path = Path(__file__).parent / "go2.xml"

LEG_NAMES = ("FL", "FR", "RL", "RR")
FOOT_SITE_NAMES = tuple(f"{leg}_foot" for leg in LEG_NAMES)
FOOT_GEOM_NAMES = tuple(f"{leg}_foot_collision" for leg in LEG_NAMES)
# Manipulating forelimbs, indexed by the trajectory flag (0 = FL, 1 = FR).
MANIP_FOOT_SITES = ("FL_foot", "FR_foot")
MANIP_CALF_BODIES = ("FL_calf", "FR_calf")
BASE_BODY = "base"


def get_spec() -> mujoco.MjSpec:
    return mujoco.MjSpec.from_file(str(GO2_XML))


ROTOR_INERTIA = 0.000111842  # Go1 value, see module docstring.
HIP_GEAR_RATIO = 6.33
KNEE_GEAR_RATIO = HIP_GEAR_RATIO * 1.5

HIP_ACTUATOR = ElectricActuator(
    reflected_inertia=reflected_inertia(ROTOR_INERTIA, HIP_GEAR_RATIO),
    velocity_limit=30.1,
    effort_limit=23.7,
)
KNEE_ACTUATOR = ElectricActuator(
    reflected_inertia=reflected_inertia(ROTOR_INERTIA, KNEE_GEAR_RATIO),
    velocity_limit=15.7,
    effort_limit=45.43,
)

NATURAL_FREQ = 10 * 2.0 * 3.1415926535
DAMPING_RATIO = 2.0

STIFFNESS_HIP = HIP_ACTUATOR.reflected_inertia * NATURAL_FREQ**2
DAMPING_HIP = 2 * DAMPING_RATIO * HIP_ACTUATOR.reflected_inertia * NATURAL_FREQ
STIFFNESS_KNEE = KNEE_ACTUATOR.reflected_inertia * NATURAL_FREQ**2
DAMPING_KNEE = 2 * DAMPING_RATIO * KNEE_ACTUATOR.reflected_inertia * NATURAL_FREQ

GO2_HIP_ACTUATOR_CFG = BuiltinPositionActuatorCfg(
    target_names_expr=(".*_hip_joint", ".*_thigh_joint"),
    stiffness=STIFFNESS_HIP,
    damping=DAMPING_HIP,
    effort_limit=HIP_ACTUATOR.effort_limit,
    armature=HIP_ACTUATOR.reflected_inertia,
)
GO2_KNEE_ACTUATOR_CFG = BuiltinPositionActuatorCfg(
    target_names_expr=(".*_calf_joint",),
    stiffness=STIFFNESS_KNEE,
    damping=DAMPING_KNEE,
    effort_limit=KNEE_ACTUATOR.effort_limit,
    armature=KNEE_ACTUATOR.reflected_inertia,
)

INIT_STATE = EntityCfg.InitialStateCfg(
    pos=(0.0, 0.0, 0.30),
    joint_pos={
        ".*thigh_joint": 0.9,
        ".*calf_joint": -1.8,
        ".*R_hip_joint": 0.1,
        ".*L_hip_joint": -0.1,
    },
    joint_vel={".*": 0.0},
)

_foot_regex = "^[FR][LR]_foot_collision$"
_collision_regex = r".*_collision\d*"

# All collision geoms on; feet get condim 6 and priority so their friction wins.
FULL_COLLISION = CollisionCfg(
    geom_names_expr=(_collision_regex,),
    contype=1,
    conaffinity=1,
    solref=(0.01, 1),
    condim={_foot_regex: 6, _collision_regex: 1},
    priority={_foot_regex: 1, ".*": 0},
    friction={_foot_regex: (1, 5e-3, 5e-4)},
)

GO2_ARTICULATION = EntityArticulationInfoCfg(
    actuators=(GO2_HIP_ACTUATOR_CFG, GO2_KNEE_ACTUATOR_CFG),
    soft_joint_pos_limit_factor=0.9,
)


def get_go2_robot_cfg() -> EntityCfg:
    """Fresh Go2 entity config (a new instance each call to avoid shared mutation)."""
    return EntityCfg(
        init_state=INIT_STATE,
        collisions=(FULL_COLLISION,),
        spec_fn=get_spec,
        articulation=GO2_ARTICULATION,
    )


GO2_ACTION_SCALE: dict[str, float] = {}
for _a in GO2_ARTICULATION.actuators:
    assert isinstance(_a, BuiltinPositionActuatorCfg)
    assert _a.effort_limit is not None
    for _n in _a.target_names_expr:
        GO2_ACTION_SCALE[_n] = 0.25 * _a.effort_limit / _a.stiffness
