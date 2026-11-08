"""Compact per-command privileged task state for the RL-v3 reward (rl-v3/QLM-SIM-001).

Pure reads of the live MuJoCo/RAMBO runtime after a command: no physics step, no controller
refresh, no RGB. The arrays leave the worker through the public IPC as finite Python floats; the
reward itself is computed on the WAM side. This module lives outside the folders hashed by
``execution_source_identity()``, so prepared anchors keep their source identity.

Row layout (one row per stepped command, plus one row for a restore point) is described by the
``columns`` list in every payload. Corners are the official success-predicate geometry
(8 pose-transformed box/block corners for push/sweep; the single body point otherwise).
"""
import math

SCHEMA = 'qlm-rl-v3-privileged-v1'
TERMINAL_CODES = {None: 0, 'task_success': 1, 'robot_fall': 2, 'timeout': 3,
                  'physics_instability': 4, 'policy_command_rejected': 5}
GOAL_TASKS = ('push_box', 'sweep_block_to_zone')


def _f(value):
    value = float(value)
    if not math.isfinite(value):
        raise FloatingPointError('Nonfinite privileged state')
    return value


def _vec(values):
    return [_f(v) for v in values]


def corner_count(rt):
    return int(len(rt.task.geometry(0)[2]))


def columns(rt):
    """Column names of one row for this runtime's task."""
    task = rt.task.task
    names = ['tick', 'completed']
    names += [f'corner{i}_{a}' for i in range(corner_count(rt)) for a in 'xyz']
    if task in GOAL_TASKS:
        names += ['goal_x0', 'goal_x1', 'goal_y0', 'goal_y1']
    names += ['object_center_x', 'object_center_y', 'object_center_z',
              'object_qx', 'object_qy', 'object_qz', 'object_qw',
              'progress', 'fl_object_contact', 'body_object_contact', 'hold', 'button_displacement',
              'base_x', 'base_y', 'base_z', 'base_qx', 'base_qy', 'base_qz', 'base_qw',
              'fl_foot_x', 'fl_foot_y', 'fl_foot_z', 'fallen', 'success', 'terminal_code']
    return names


def static(rt):
    """Per-episode constants (scene goal, object extents, press axis) for the reward."""
    p = rt.profile
    keep = ('goal_x', 'goal_y', 'half_extent', 'bounds_local', 'center_local', 'sweep_direction_xy',
            'initial_center_xy', 'threshold_m', 'stroke_m', 'press_axis_world', 'button_rest_front_xyz',
            'horizon_s', 'canonical_goal_position')
    out = {'schema': SCHEMA, 'task_id': rt.task.task, 'columns': columns(rt), 'corner_count': corner_count(rt),
           'terminal_codes': {str(k): v for k, v in TERMINAL_CODES.items()},
           'tick_seconds': 0.002, 'command_ticks': 10}
    for key in keep:
        if key in p and p[key] is not None:
            value = p[key]
            out[key] = _f(value) if isinstance(value, (int, float)) else \
                [[_f(x) for x in row] for row in value] if value and isinstance(value[0], (list, tuple)) else _vec(value)
    return out


def contacts(rt):
    """FL-foot/object and robot-root/object contact at the current derived state (same rule as state_channels)."""
    d, m, body = rt.physics.data[0], rt.physics.model, rt.task.body
    fl_geom, root = int(rt.physics.foot_geom_ids[0]), int(rt.physics.root_id)
    fl_object = body_object = False
    for contact in d.contact[:d.ncon]:
        g1, g2 = int(contact.geom[0]), int(contact.geom[1])
        b1, b2 = int(m.geom_bodyid[g1]), int(m.geom_bodyid[g2])
        if body in (b1, b2):
            fl_object |= fl_geom in (g1, g2)
            body_object |= root in (b1, b2)
    return fl_object, body_object


def button_displacement(rt):
    if rt.task.task != 'press_button':
        return 0.
    import mujoco
    joint = mujoco.mj_name2id(rt.physics.model, mujoco.mjtObj.mjOBJ_JOINT, 'button_slide')
    return float(rt.physics.data[0].qpos[rt.physics.model.jnt_qposadr[joint]])


def row(rt, *, completed=True, terminal_reason=None):
    d = rt.physics.data[0]
    _, _, corners = rt.task.geometry(0)
    center = rt.task.geometric_center(0)
    fl, body = contacts(rt)
    root = int(rt.physics.root_id)
    foot = d.geom_xpos[int(rt.physics.foot_geom_ids[0])]
    task = rt.task.task
    values = [int(rt.physics.ticks[0]), 1. if completed else 0.]
    values += [c for corner in corners for c in corner]
    if task in GOAL_TASKS:
        values += [*rt.profile['goal_x'], *rt.profile['goal_y']]
    values += [*center, *d.xquat[rt.task.body][[1, 2, 3, 0]],
               rt.outcome.get('progress', rt.task.progress(0)), float(fl), float(body), int(rt.task.hold[0]),
               button_displacement(rt), *d.xpos[root], *d.xquat[root][[1, 2, 3, 0]], *foot,
               float(bool(rt.outcome.get('fallen', False))), float(bool(rt.outcome.get('success', False))),
               TERMINAL_CODES[terminal_reason]]
    return _vec(values)


def payload(rt, rows):
    return {'schema': SCHEMA, 'columns': columns(rt), 'rows': rows}
