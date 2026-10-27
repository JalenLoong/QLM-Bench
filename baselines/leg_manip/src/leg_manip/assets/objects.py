"""Articulated task objects, built procedurally from MuJoCo primitives.

Object frame convention (shared by the expert trajectories): origin on the ground
at the center of the object's front face, +x points into the object, +z up. The
robot approaches from -x. mjlab wraps these fixed-base entities in a mocap body so
each env can place them independently.

Sizes are scaled from the paper's Aliengo setup to Go2 (roughly x0.75 in height).
"""

from __future__ import annotations

import mujoco

OBJECT_GEOM_GROUP = 1  # visible to the head camera; terrain is group 0.


def _box(body: mujoco.MjsBody, name: str, half: tuple, pos: tuple, rgba: tuple) -> None:
    body.add_geom(
        name=name,
        type=mujoco.mjtGeom.mjGEOM_BOX,
        size=half,
        pos=pos,
        rgba=rgba,
        group=OBJECT_GEOM_GROUP,
        condim=3,
        friction=(0.8, 0.005, 0.0001),
    )


def button_panel_spec(button_height: float = 0.25) -> mujoco.MjSpec:
    """Wall panel with a hemispherical push button (paper: 10 cm diameter).

    Joint ``button_joint`` (slide, +x into the panel): 0 = released, positive =
    pressed. A spring returns the button.
    """
    spec = mujoco.MjSpec()
    spec.compiler.degree = False
    panel = spec.worldbody.add_body(name="panel")
    _box(
        panel, "panel_geom", (0.03, 0.30, 0.25), (0.03, 0.0, 0.25), (0.8, 0.8, 0.75, 1)
    )
    button = panel.add_body(name="button", pos=(0.0, 0.0, button_height))
    button.add_joint(
        name="button_joint",
        type=mujoco.mjtJoint.mjJNT_SLIDE,
        axis=(1.0, 0.0, 0.0),
        range=(0.0, 0.03),
        stiffness=300.0,
        springref=0.0,
        damping=3.0,
    )
    button.add_geom(
        name="button_geom",
        type=mujoco.mjtGeom.mjGEOM_SPHERE,
        size=(0.05, 0, 0),
        rgba=(0.85, 0.1, 0.1, 1),
        mass=0.05,
        group=OBJECT_GEOM_GROUP,
        condim=3,
    )
    # The slider travels inside its housing. Exclude only this internal pair;
    # both geometries must still collide with the robot and other objects.
    spec.add_exclude(bodyname1="panel", bodyname2="button")
    return spec


def dishwasher_spec(
    hinge_height: float = 0.08, door_length: float = 0.40
) -> mujoco.MjSpec:
    """Cabinet with a bottom-hinged door that opens toward the robot.

    Joint ``door_joint`` (hinge about -y): 0 = closed (vertical), positive = open
    (top toward -x). Damping and dry friction hold the door where it is left.
    """
    spec = mujoco.MjSpec()
    spec.compiler.degree = False
    cab = spec.worldbody.add_body(name="cabinet")
    width = 0.24
    _box(
        cab, "cabinet_geom", (0.22, width, 0.25), (0.24, 0.0, 0.25), (0.7, 0.7, 0.72, 1)
    )
    door = cab.add_body(name="door", pos=(-0.012, 0.0, hinge_height))
    door.add_joint(
        name="door_joint",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=(0.0, -1.0, 0.0),
        range=(0.0, 1.45),
        damping=1.0,
        frictionloss=3.0,
    )
    door.add_geom(
        name="door_geom",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        size=(0.01, width - 0.01, door_length / 2),
        pos=(0.0, 0.0, door_length / 2),
        rgba=(0.55, 0.57, 0.6, 1),
        mass=0.6,
        group=OBJECT_GEOM_GROUP,
        condim=3,
        friction=(0.8, 0.005, 0.0001),
    )
    return spec
