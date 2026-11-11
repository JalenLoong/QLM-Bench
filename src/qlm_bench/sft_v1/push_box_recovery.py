"""Push-box recovery routine E* (sft-v1/QLM-SIM-001 skeleton, sft-v1/QLM-SIM-002 turning push and overshoot protection;
design 4.3 of task-specific-sft-design-20261110).

Same form as ``backends/mujoco/experts/push_box_expert.py``: ``command(env, time)`` reads the live simulator
through an ``ExpertAdapter`` and returns one 50 Hz native9 command ``[vx, vy, 0, fl_x, fl_y, fl_z, 0, 0, 0]``
(projected-COM frame, forces zero) plus a diagnostic dict.

Structure:

* ``configure(env, params)`` stores the versioned parameter set on the adapter and writes the regular-push
  options (``lateral_tracking_gain``, ``lateral_tracking_limit_m``, ``corner_recovery``) into the adapter's expert
  profile, exactly where ``push_box_expert`` reads them.
* ``enter_midway(env, time)`` is the mid-episode entry: stage ``straight_push``, push start = takeover time; settle
  and the approach phases are not replayed. The foot reference starts at the measured foot.
* Before the push stage (a run from reset) ``command`` delegates to the unmodified ``push_box_expert``.
* In the push stage it runs its own copy of the ``straight_push`` branch (regular push, design 4.3 item 1), then
  ``steer`` (item 2), the existing ``corner_reference`` (only if the regular option is on) and ``overshoot_guard``
  (item 3).

What the two hooks do, and why (exploration record: workspace
runs/audit/tsft-push-gate-20261111-v1/exploration/README.md):

* The student's failure is a +yaw box pushed at the *middle* of its near face: the face normal then points to +y and
  the box drifts +y without turning back. The regular push (foot on the +x ray through the box centre) already lands on
  the +y half of that face, but past about 29 deg the ray leaves the near face for the long side face and the moment
  changes sign. ``steer`` therefore picks the contact point on the near face in the box's own frame, clipped to the
  usable face, moves the foot there off the box when the move is large (pull back, shift, re-plant), lets the body
  follow sideways and slows the push.
* ``overshoot_guard`` acts when the box's +y edge is still outside and there is no forward room left (or turning
  cannot help): brake, sidestep, side nudge toward -y, then return behind the box.

With both hooks disabled the output is bit-identical to ``push_box_expert`` under the same expert profile
(tests/qlm/test_sft_v1_takeover.py). Idle (no deviation seen, nothing to slew) the hooks return the regular push
unchanged. Raise ``VERSION`` and record the frozen commit when the routine changes.
"""
import copy

import numpy as np

from qlm_bench.backends.mujoco.experts import push_box_expert
from qlm_bench.backends.mujoco.experts.push_box_corner_recovery import corner_reference

VERSION = 'push_box_recovery-v1'
SCHEMA = 'qlm-sft-v1-push-box-recovery-params-v1'
DT = 0.02  # one native9 command per 50 Hz tick

# Regular-push options: the values the repository already uses for the scale-up push experts
# (rambo push_box_scenarios.py / push_box_scaleup_plan.py: gain 2.0, limit 0.015 m). corner_recovery is off because the
# overshoot guard below covers its trigger region (box inside in x, +y overflow) with a closed-loop version.
DEFAULT_PARAMS = {
    'schema': SCHEMA,
    'version': VERSION,
    'regular': {'lateral_tracking_gain': 2.0, 'lateral_tracking_limit_m': 0.015, 'corner_recovery': False},
    # Design 4.3 item 2: turning push (contact point chosen on the near face, in the box's own frame).
    'steering': {
        'enabled': True,
        'theta_on_deg': 20.0, 'theta_off_deg': 10.0, 'dwell_s': 0.3,  # near-face yaw hysteresis; on only after dwell_s
        'margin_on_m': 0.03, 'margin_off_m': 0.05,                    # box edge to goal y edge
        'k_yaw_m_per_rad': 0.25, 'face_margin_m': 0.025,              # contact offset along the near face
        'margin_ref_m': 0.10, 'k_lateral_rad_per_m': 3.0, 'yaw_bias_max_deg': 12.0, 'bias_travel_ref_m': 0.15,
        'lateral_slew_mps': 0.08, 'forward_slew_mps': 0.10,
        'replant_on_m': 0.05, 'replant_off_m': 0.008, 'deficit_on_m': 0.015, 'deficit_off_m': 0.01, 'retract_m': 0.05, 'retract_slew_mps': 0.15, 'free_slew_mps': 0.15,
        'vx_scale': 0.6, 'vx_gap_scale': 0.3, 'gap_ref_m': 0.04, 'vx_pivot_scale': 0.35,
        'reach_min_m': 0.03, 'reach_max_m': 0.205,
        'body_band_m': [0.10, 0.16], 'handback_reach_m': 0.17, 'k_body_per_s': 2.0, 'vy_min_mps': -0.055, 'vy_max_mps': 0.03,
    },
    # Design 4.3 item 3: overshoot protection. With no forward room left (or a box that is not turned +yaw, so that
    # turning it cannot help) and the +y edge still out: brake, sidestep, side nudge toward -y, return and push on.
    'overshoot': {
        'enabled': True,
        'margin_pre_m': 0.03, 'margin_y_m': 0.01, 'margin_x_m': 0.01, 'rho': 0.25,
        'pivot_yaw_deg': 5.0, 'room_stop_m': 0.015,
        'brake_s': 0.3, 'retract_m': [-0.05, 0.0, 0.03], 'foot_slew_mps': 0.15,
        'clear_exit_m': 0.025, 'max_cycles': 3,
        'side_clear_m': 0.04, 'hover_dz_m': 0.03, 'rear_clearance_m': 0.37,
        'stroke_reach_m': [0.10, 0.195], 'reach_x_m': [0.20, 0.53],
        'nudge_mps': 0.04, 'stroke_max_m': 0.16, 'lower_s': 0.3, 'retreat_s': 0.3,
        'vx_min_mps': -0.02, 'vx_max_mps': 0.05, 'vy_min_mps': -0.055, 'vy_max_mps': 0.03, 'phase_timeout_s': 6.0,
    },
}
REGULAR_KEYS = ('lateral_tracking_gain', 'lateral_tracking_limit_m', 'corner_recovery')


def merged_params(params=None):
    """DEFAULT_PARAMS updated section by section; unknown sections or regular keys are refused."""
    out = copy.deepcopy(DEFAULT_PARAMS)
    for key, value in (params or {}).items():
        if key in ('schema', 'version'):
            out[key] = value
        elif key in out and isinstance(value, dict):
            if key == 'regular' and set(value) - set(REGULAR_KEYS):
                raise ValueError(f'Unknown regular-push parameter: {sorted(set(value) - set(REGULAR_KEYS))}')
            out[key].update(copy.deepcopy(value))
        else:
            raise ValueError(f'Unknown recovery parameter section: {key}')
    if out['schema'] != SCHEMA:
        raise ValueError('Recovery parameter schema mismatch')
    return out


def configure(env, params=None):
    """Bind a parameter set to a fresh ExpertAdapter; returns the effective parameters."""
    if hasattr(env, '_recovery_params'):
        raise ValueError('Recovery routine already configured on this adapter')
    value = merged_params(params)
    expert = env.cfg.approved_profile['expert']
    for key in REGULAR_KEYS:
        expert.pop(key, None)
    regular = value['regular']
    if regular.get('lateral_tracking_gain') is not None:
        expert['lateral_tracking_gain'] = float(regular['lateral_tracking_gain'])
        expert['lateral_tracking_limit_m'] = float(regular['lateral_tracking_limit_m'])
    expert['corner_recovery'] = bool(regular.get('corner_recovery', False))
    env._recovery_params = value
    return copy.deepcopy(value)


def _state(env):
    state = getattr(env, '_recovery_state', None)
    if state is None:
        state = env._recovery_state = {'mode': 'idle', 'y_cmd': None, 'x_cmd': None, 'comp': 0., 'guard': None, 'cycles': 0,
                                       'lift': False, 'replanting': False, 'dwell': 0.}
    return state


def enter_midway(env, time):
    """Takeover entry at a restored chunk boundary: start in the push stage, push start = now.

    The foot reference starts at the measured foot and is slewed to the routine's target, so the takeover itself never
    commands a lateral jump against the box face.
    """
    env._expert_stage = 'straight_push'
    env._expert_push_start = float(time)
    env._recovery_entry_time = float(time)
    params = env._recovery_params
    if params['steering'].get('enabled') or params['overshoot'].get('enabled'):
        state = _state(env)
        _rearm(env, state)


def _rearm(env, state):
    """Restart the foot reference from the measured foot (takeover entry and return from the guard)."""
    actual = np.asarray(env.actual_fl_world(), dtype=float)
    base = env.base_pos_w[0].detach().cpu().numpy()
    state.update(mode='release', y_cmd=float(actual[1]), x_cmd=float(actual[0] - base[0]), comp=0., lift=False, replanting=False, dwell=0.)
    env._expert_lateral_comp = 0.


# ------------------------------------------------------------------ geometry helpers

def _smooth(t):
    u = float(np.clip(t, 0., 1.))
    return u * u * (3 - 2 * u)


def _heading(env):
    """Yaw of the projected-COM frame (the frame native9 foot targets and velocities are expressed in)."""
    import torch
    from qlm_bench.controllers.rambo.math import quat_apply, quat_mul, quat_inv
    projected = quat_mul(env.base_quat, quat_inv(env.base_quat_rp))
    axis = quat_apply(projected, torch.tensor([[1., 0., 0.]], device=env.device, dtype=torch.float32))[0]
    return float(np.arctan2(float(axis[1]), float(axis[0])))


def _clamp_reach(env, base, target, x_range, y_range):
    """Clamp a world foot target to a box in the projected-COM frame; returns the clamped world target and local xy."""
    h = _heading(env);c, s = np.cos(h), np.sin(h)
    dx, dy = target[0] - base[0], target[1] - base[1]
    lx = float(np.clip(c * dx + s * dy, *x_range));ly = float(np.clip(-s * dx + c * dy, *y_range))
    out = np.array([base[0] + c * lx - s * ly, base[1] + s * lx + c * ly, target[2]])
    return out, lx, ly


def _slew(current, goal, step):
    current = np.asarray(current, dtype=float);delta = np.asarray(goal, dtype=float) - current
    norm = float(np.linalg.norm(delta))
    return current + delta if norm <= step else current + delta * (step / norm)


def _box(env, geom):
    """Box state against the goal rectangle and the near face (the face whose outward normal is closest to -x).

    yaw is the near-face yaw in (-45, 45] deg; depth is the distance from the box centre to the near face and width the
    half-width of that face. A point of the near face at face coordinate yl (positive toward the box's own +y side
    of that face) lies at world y = centre_y - depth * sin(yaw) + yl * cos(yaw).
    """
    profile = env.cfg.approved_profile;gx, gy = profile['goal_x'], profile['goal_y']
    pts = np.asarray(geom['footprint_xy'], dtype=float);lo = pts.min(0);hi = pts.max(0)
    centre = np.asarray(geom['center'], dtype=float)
    raw = float(geom['yaw_rad']);quarter = int(np.round(raw / (np.pi / 2)));yaw = raw - quarter * np.pi / 2
    if hasattr(env, '_box_geometry'):
        half = np.asarray(env._box_geometry['dimensions'], dtype=float)[:2] / 2
    else:
        half = np.asarray(env.task.profile['half_extent'], dtype=float)[:2]
    depth, width = (half[0], half[1]) if quarter % 2 == 0 else (half[1], half[0])
    return dict(lo=lo, hi=hi, centre=centre, yaw=float(yaw), depth=float(depth), width=float(width),
                e_y=float(centre[1] - (gy[0] + gy[1]) / 2), room=float(gx[1] - hi[0]), need=float(gx[0] - lo[0]),
                over_hi=float(hi[1] - gy[1]), over_lo=float(gy[0] - lo[1]))


def _face_y(box, yl):
    return float(box['centre'][1] - box['depth'] * np.sin(box['yaw']) + yl * np.cos(box['yaw']))


def _face_coord(box, y):
    return float((y - box['centre'][1] + box['depth'] * np.sin(box['yaw'])) / np.cos(box['yaw']))


def _contact_y(env, box):
    """World y for the foot centre so that the foot sphere touches the near face at the desired contact coordinate (the
    sphere touches a turned face radius * sin(yaw) to the side of its centre line)."""
    radius = float(env.physics.model.geom('FL').size[0])
    return _face_y(box, _contact_offset(env, box)) - radius * float(np.sin(box['yaw']))


def _contact_offset(env, box):
    """Desired contact coordinate on the near face: k_yaw * (yaw - yaw_bias), clipped to the usable face.

    yaw_bias leans the box away from a goal y edge it is close to (a box near the +y edge is turned to -yaw so that the
    face normal, and with it the push, points toward -y).
    """
    p = env._recovery_params['steering']
    d_hi = max(0., p['margin_ref_m'] + box['over_hi']);d_lo = max(0., p['margin_ref_m'] + box['over_lo'])
    limit = np.radians(p['yaw_bias_max_deg'])
    bias = float(np.clip(-p['k_lateral_rad_per_m'] * (d_hi - d_lo), -limit, limit))
    if bias * box['yaw'] > 0:
        # A bias on the side the box is already turned to would keep it turned. That only pays off over forward travel;
        # close to the goal a straight box (smallest footprint) is better. A bias against the present yaw is kept: it
        # carries the box quickly through straight.
        bias *= float(np.clip(box['need'] / p['bias_travel_ref_m'], 0., 1.))
    usable = box['width'] - p['face_margin_m']
    return float(np.clip(p['k_yaw_m_per_rad'] * (box['yaw'] - bias), -usable, usable))


def _left_boundary(geom, x):
    """Largest y of the box's ground outline on the vertical line at world x (x clamped into the outline)."""
    pts = np.asarray(geom.get('projected_box_corners', geom['footprint_xy']), dtype=float)
    centre = pts.mean(0)
    order = np.argsort(np.arctan2(pts[:, 1] - centre[1], pts[:, 0] - centre[0]))
    hull = pts[order]
    x = float(np.clip(x, pts[:, 0].min() + .005, pts[:, 0].max() - .005))
    best = -np.inf
    for a, b in zip(hull, np.roll(hull, -1, axis=0)):
        if abs(b[0] - a[0]) < 1e-9:
            continue
        u = (x - a[0]) / (b[0] - a[0])
        if -1e-9 <= u <= 1 + 1e-9:
            best = max(best, float(a[1] + u * (b[1] - a[1])))
    return (float(pts[:, 1].max()) if not np.isfinite(best) else best), x


# ------------------------------------------------------------------ hooks

def steer(env, time, geom, base, line_point, target, vx, vy, phase):
    """Design 4.3 item 2: turning push.

    Idle, it returns the regular push unchanged. It switches on, with hysteresis, when for dwell_s the near-face yaw
    stays past theta_on or a box edge stays within margin_on of a goal y edge. While on,
    the foot's lateral target is a point of the near face at face coordinate k_yaw * (yaw - yaw_bias), clipped to the
    usable face: for a +yaw box the push point sits on the +y end of the near face (a -yaw moment), never past the
    corner onto the side face. The body follows the foot laterally (vy) and the push is slowed (vx).
    """
    p = env._recovery_params['steering']
    if not p.get('enabled'):
        return target, vx, vy, phase
    state = _state(env)
    if state['guard'] is not None or phase != 'straight_push':
        return target, vx, vy, phase
    box = _box(env, geom)
    regular_y = float(target[1])
    yaw_deg = abs(np.degrees(box['yaw']));margin = -max(box['over_hi'], box['over_lo'])
    on = yaw_deg >= p['theta_on_deg'] or margin <= p['margin_on_m']
    off = yaw_deg < p['theta_off_deg'] and margin > p['margin_off_m']
    if state['mode'] != 'active':
        state['dwell'] = state['dwell'] + DT if on else 0.
        if state['dwell'] >= p['dwell_s']:
            if state['mode'] == 'idle':
                state.update(y_cmd=regular_y, x_cmd=float(target[0] - base[0]), comp=float(getattr(env, '_expert_lateral_comp', 0.)))
            state.update(mode='active', dwell=0.)
        elif state['mode'] == 'idle':
            return target, vx, vy, phase
    elif off:
        state.update(mode='release', dwell=0.)
    foot_x = float(target[0] - base[0])
    y_des = _contact_y(env, box) if state['mode'] == 'active' else float(line_point[1])
    # What the foot can reach from where the body is now; the body follows below.
    wanted = np.array([base[0] + foot_x, y_des, target[2]])
    reachable, _, _ = _clamp_reach(env, base, wanted, (-9, 9), (p['reach_min_m'], p['reach_max_m']))
    deficit = abs(float(wanted[1] - reachable[1]))
    gap = abs(float(reachable[1]) - state['y_cmd'])
    # Large lateral moves are made off the box: pull the foot back, move it sideways in free space, re-plant it. The foot
    # also waits off the box while the contact point is out of reach and the body is still moving over.
    if not state['lift'] and (gap > p['replant_on_m'] or deficit > p['deficit_on_m']):
        state.update(lift=True, replanting=True)
    elif state['lift'] and gap < p['replant_off_m'] and deficit < p['deficit_off_m']:
        state['lift'] = False
    x_goal = foot_x - (p['retract_m'] if state['lift'] else 0.)
    x_rate = p['retract_slew_mps'] if state['lift'] else p['forward_slew_mps']
    state['x_cmd'] += float(np.clip(x_goal - state['x_cmd'], -x_rate * DT, x_rate * DT))
    backed = (foot_x - state['x_cmd']) >= 0.7 * p['retract_m']
    y_rate = (p['free_slew_mps'] if backed else 0.) if state['lift'] else p['lateral_slew_mps']
    state['y_cmd'] += float(np.clip(float(reachable[1]) - state['y_cmd'], -y_rate * DT, y_rate * DT))
    gap = abs(float(reachable[1]) - state['y_cmd'])
    # The body follows the wanted contact point, not the clamped one.
    ly = _clamp_reach(env, base, wanted, (-9, 9), (-9, 9))[2]
    if state['mode'] == 'release' and gap < 1e-3 and ly <= p['handback_reach_m'] and abs(foot_x - state['x_cmd']) < 1e-3:
        # Hand back to the regular push (which does not move the body sideways) once the foot is on its line with
        # lateral reach to spare; its integrator continues from the steering one.
        state.update(mode='idle', y_cmd=None, x_cmd=None, dwell=0., lift=False, replanting=False)
        env._expert_lateral_comp = state['comp']
        return target, vx, vy, phase
    # The regular push's bounded tracking compensation, applied to the slewed reference.
    expert = env.cfg.approved_profile['expert']
    if 'lateral_tracking_gain' in expert and not state['lift']:
        limit = expert['lateral_tracking_limit_m']
        error = state['y_cmd'] - float(env.actual_fl_world()[1])
        state['comp'] = float(np.clip(state['comp'] + DT * expert['lateral_tracking_gain'] * error, -limit, limit))
    env._expert_lateral_comp = state['comp']
    out = np.array([base[0] + state['x_cmd'], state['y_cmd'] + state['comp'], target[2]])
    out, _, _ = _clamp_reach(env, base, out, (-9, 9), (p['reach_min_m'], p['reach_max_m']))
    lo, hi = p['body_band_m']
    follow = p['k_body_per_s'] * ((ly - hi) if ly > hi else (ly - lo) if ly < lo else 0.)
    vy = vy + float(np.clip(follow, p['vy_min_mps'], p['vy_max_mps']))
    behind = foot_x - state['x_cmd']
    if state['replanting'] and not state['lift'] and behind < 0.005:
        state['replanting'] = False
    scale = p['vx_scale'] if state['mode'] == 'active' else 1.
    if state['mode'] == 'active' and _urgency(env, box) > 0:
        scale = p['vx_pivot_scale']
    scale *= 1. - min(1., gap / p['gap_ref_m']) * (1. - p['vx_gap_scale'])
    # No push while the foot is off the box or short of the contact point it wants.
    scale *= 0. if state['lift'] else float(np.clip(1. - (behind - 0.02) / max(p['retract_m'] - 0.02, 1e-6), 0., 1.))
    scale *= float(np.clip(1. - (deficit - p['deficit_off_m']) / 0.02, 0., 1.))
    name = 'steer_replant' if state['replanting'] else 'steer_push' if state['mode'] == 'active' else 'steer_release'
    return out, vx * scale, vy, name


def _urgency(env, box):
    """> 0 when the +y correction the box still needs exceeds rho times the forward room left (pushing on would carry
    it through the goal before it fits)."""
    p = env._recovery_params['overshoot']
    return (box['over_hi'] + p['margin_pre_m']) - p['rho'] * max(box['room'] - p['margin_x_m'], 0.)


def overshoot_guard(env, time, geom, base, target, vx, vy, phase):
    """Design 4.3 item 3: overshoot protection.

    Armed when the box's +y edge is past the goal's +y edge (less margin_y) and either there is no forward room left
    before the far goal edge, or the box is not turned +yaw (so the turning push cannot shrink its footprint) and the
    correction it needs exceeds rho times the forward room. Then: brake and pull the foot back, sidestep to the +y
    side, place the foot beside the box's +y face at the box centre's x, nudge it toward -y until it clears the edge,
    and either repeat or return behind the box and resume the (turning) push.
    """
    p = env._recovery_params['overshoot']
    if not p.get('enabled'):
        return target, vx, vy, phase
    state = _state(env)
    box = _box(env, geom)
    sp = env._recovery_params['steering']
    actual = np.asarray(env.actual_fl_world(), dtype=float)
    g = state['guard']
    if g is None:
        if phase not in ('straight_push', 'steer_push', 'steer_release', 'steer_replant') or box['room'] < -0.02:
            return target, vx, vy, phase
        overflow = box['over_hi'] + p['margin_y_m'];room = box['room'] - p['margin_x_m']
        pivoting = np.degrees(box['yaw']) > p['pivot_yaw_deg']
        if not (overflow > 0 and state['cycles'] < p['max_cycles'] and (room < p['room_stop_m'] or (not pivoting and overflow > p['rho'] * max(room, 0.)))):
            return target, vx, vy, phase
        g = state['guard'] = dict(stage='brake', start=time, foot=actual.copy(), vx=float(vx), ref=actual.copy())
    x_range = tuple(p['reach_x_m']);y_range = (sp['reach_min_m'], sp['reach_max_m'])
    centre = box['centre'];elapsed = time - g['start']
    z_contact = max(.06, float(centre[2]));z_hover = z_contact + p['hover_dz_m']

    def go(stage):
        g.update(stage=stage, start=time)

    def plan():
        x_c = float(np.clip(centre[0], base[0] + x_range[0], base[0] + x_range[1] - .01))
        y_face, x_c = _left_boundary(geom, x_c)
        return x_c, y_face + p['side_clear_m']

    stage = g['stage'];out = g['ref'];vx_out = 0.;vy_out = 0.
    if stage == 'brake':
        u = _smooth(elapsed / p['brake_s'])
        out = g['foot'] + np.asarray(p['retract_m'], dtype=float) * u;vx_out = g['vx'] * (1 - u)
        g['ref'] = out
        if elapsed >= p['brake_s']:
            go('sidestep')
    elif stage == 'sidestep':
        x_c, y_side = plan()
        hover = np.array([min(float(box['lo'][0]) - .03, base[0] + .40), y_side, z_hover])
        g['ref'] = _slew(g['ref'], hover, p['foot_slew_mps'] * DT);out = g['ref']
        lo, hi = p['stroke_reach_m']
        ly = _clamp_reach(env, base, np.array([x_c, y_side, z_hover]), (-9, 9), (-9, 9))[2]
        vy_out = float(np.clip(2.0 * ((ly - hi) if ly > hi else (ly - lo) if ly < lo else 0.), p['vy_min_mps'], p['vy_max_mps']))
        base_x_goal = float(box['lo'][0]) - p['rear_clearance_m']
        vx_out = float(np.clip(1.0 * (base_x_goal - base[0]), p['vx_min_mps'], p['vx_max_mps']))
        if (lo - .01 <= ly <= hi + .01 and abs(base_x_goal - base[0]) < .03) or elapsed > p['phase_timeout_s']:
            go('reposition')
    elif stage == 'reposition':
        x_c, y_side = plan()
        via = np.array([min(float(box['lo'][0]) - .03, base[0] + .40), y_side, z_hover])
        point = np.array([x_c, y_side, z_hover])
        goal = point if abs(g['ref'][1] - y_side) < .01 else via   # sideways first, then forward along the side face
        g['ref'] = _slew(g['ref'], goal, p['foot_slew_mps'] * DT);out = g['ref']
        if np.linalg.norm(point - g['ref']) < .005 or elapsed > p['phase_timeout_s']:
            g.update(side=point.copy());go('lower')
    elif stage == 'lower':
        u = _smooth(elapsed / p['lower_s'])
        out = g['side'] + np.array([0., 0., (z_contact - z_hover) * u]);g['ref'] = out
        if elapsed >= p['lower_s']:
            g.update(stroke=0.);go('nudge')
    elif stage == 'nudge':
        g['stroke'] += p['nudge_mps'] * DT
        out = np.array([g['side'][0], g['side'][1] - g['stroke'], z_contact]);g['ref'] = out
        _, _, ly = _clamp_reach(env, base, out, x_range, (-9, 9))
        if box['over_hi'] <= -p['clear_exit_m'] or g['stroke'] >= p['stroke_max_m'] or ly <= y_range[0] or elapsed > p['phase_timeout_s']:
            g.update(foot=actual.copy());go('retreat')
    elif stage == 'retreat':
        u = _smooth(elapsed / p['retreat_s'])
        out = g['foot'] + np.array([0., .03, p['hover_dz_m']]) * u;g['ref'] = out
        if elapsed >= p['retreat_s']:
            state['cycles'] += 1
            if box['over_hi'] > -p['margin_y_m'] and state['cycles'] < p['max_cycles']:
                go('sidestep')
            else:
                go('return_back')
    elif stage == 'return_back':
        point = np.array([min(float(box['lo'][0]) - .04, g['ref'][0]), g['ref'][1], z_hover])
        g['ref'] = _slew(g['ref'], point, p['foot_slew_mps'] * DT);out = g['ref']
        if np.linalg.norm(point - g['ref']) < .005 or elapsed > p['phase_timeout_s']:
            go('return_centre')
    elif stage == 'return_centre':
        point = np.array([float(box['lo'][0]) - .04, _contact_y(env, box), z_contact])
        g['ref'] = _slew(g['ref'], point, p['foot_slew_mps'] * DT);out = g['ref']
        if np.linalg.norm(point - g['ref']) < .005 or elapsed > p['phase_timeout_s']:
            state['guard'] = None
            _rearm(env, state)
    out, _, _ = _clamp_reach(env, base, out, x_range, y_range)
    return out, vx_out, vy_out, 'guard_' + stage


# ------------------------------------------------------------------ command

def _line(env, geom):
    """Push-line point and face normal, exactly as push_box_expert computes them."""
    face = np.asarray(geom['face_center']);normal = np.asarray(geom['face_normal']);center = np.asarray(geom['center'])
    line_point = face.copy();line_point[1] = center[1]
    if 'episode_scenario' in env.cfg.approved_profile:
        from qlm_bench.backends.mujoco.experts.push_box_geometry import forward_face_ray
        line_point, normal = forward_face_ray(env._box_geometry, env.primary_pose_w[0].detach().cpu().numpy())
    else:
        line_point[0] = face[0] - normal[1] * (line_point[1] - face[1]) / normal[0]
    return face, normal, line_point


def _regular_push(env, time, geom, base, line_point):
    """Copy of push_box_expert's straight_push/leg_finish target (regular push, design 4.3 item 1)."""
    expert = env.cfg.approved_profile['expert']
    phase = env._expert_stage
    foot_x = expert['push_foot_x'];vx = expert['push_base_speed']
    if 'motion' in expert:
        duration = expert['transition_s'];u = np.clip((time - env._expert_push_start) / duration, 0., 1.);u = u * u * (3 - 2 * u)
        foot_x = expert['approach_foot_x'] * (1 - u) + foot_x * u;vx *= u
        remaining = env.cfg.approved_profile['goal_x'][0] - min(x[0] for x in geom['footprint_xy'])
        lateral = all(env.cfg.approved_profile['goal_y'][0] <= x[1] <= env.cfg.approved_profile['goal_y'][1] for x in geom['footprint_xy'])
        if expert['motion'] == 'leg_finish' and not hasattr(env, '_expert_finish_start') and u >= 1 and lateral and 0 < remaining <= .03 and expert['leg_finish_max_x'] - foot_x >= remaining + .01:
            env._expert_finish_start = time;env._expert_finish_base = float(base[0]);env._expert_finish_foot = foot_x
        if hasattr(env, '_expert_finish_start'):
            v = np.clip((time - env._expert_finish_start) / duration, 0., 1.);v = v * v * (3 - 2 * v)
            foot_x = env._expert_finish_foot + (expert['leg_finish_max_x'] - env._expert_finish_foot) * v
            vx = expert['push_base_speed'] * (1 - v);phase = 'leg_finish'
    target = np.array([base[0] + foot_x, line_point[1], line_point[2]])
    if 'lateral_tracking_gain' in expert:
        error = line_point[1] - env.actual_fl_world()[1]
        limit = expert['lateral_tracking_limit_m']
        env._expert_lateral_comp = float(np.clip(getattr(env, '_expert_lateral_comp', 0.) + .02 * expert['lateral_tracking_gain'] * error, -limit, limit))
        target[1] += env._expert_lateral_comp
    return target, vx, phase


def command(env, time):
    if not hasattr(env, '_recovery_params'):
        raise ValueError('configure(env, params) required before command')
    if getattr(env, '_expert_stage', None) != 'straight_push':
        # Settle and approach from reset: the unmodified expert (it also performs the switch to straight_push).
        result, diag = push_box_expert.command(env, time)
        diag = {**diag, 'recovery_version': env._recovery_params['version'], 'recovery_branch': 'delegated'}
        env._expert_diagnostics = diag
        return result, diag
    import torch
    from qlm_bench.controllers.rambo.math import quat_apply_inverse, quat_mul, quat_inv
    geom = env.geometry_world()
    face, normal, line_point = _line(env, geom)
    base = env.base_pos_w[0].detach().cpu().numpy()
    projected = quat_mul(env.base_quat, quat_inv(env.base_quat_rp))
    target, vx, phase = _regular_push(env, time, geom, base, line_point)
    vy = 0.
    target, vx, vy, phase = steer(env, time, geom, base, line_point, target, vx, vy, phase)
    if phase in ('straight_push', 'leg_finish') or hasattr(env, '_corner_recovery'):
        target, vx, corner_vy, recovery_phase = corner_reference(env, time, geom, base, target, vx)
        vy += corner_vy
        if recovery_phase is not None:
            phase = recovery_phase
    target, vx, vy, phase = overshoot_guard(env, time, geom, base, target, vx, vy, phase)
    origin = env.base_pos_w[0].clone();origin[2] = 0
    point = torch.as_tensor(target, device=env.device, dtype=torch.float32)[None] - origin[None]
    local = quat_apply_inverse(projected, point)[0]
    velocity = quat_apply_inverse(projected, torch.tensor([[vx, vy, 0.]], device=env.device, dtype=torch.float32))[0]
    result = [float(velocity[0]), float(velocity[1]), 0., *local.cpu().tolist(), 0., 0., 0.]
    diag = dict(phase=phase, intended_face_center=face.tolist(), intended_face_normal=normal.tolist(),
                commanded_contact_point=target.tolist(), centerline_face_intersection=line_point.tolist(),
                commanded_world_base_velocity=[vx, vy, 0.], actual_fl_eef_world=env.actual_fl_world().tolist(),
                box_pose=env.primary_pose_w[0].detach().cpu().tolist(), box_yaw_rad=geom['yaw_rad'], contact_evidence='unknown_diagnostic_only',
                lateral_tracking_compensation_m=getattr(env, '_expert_lateral_comp', 0.),
                recovery_version=env._recovery_params['version'], recovery_branch='own')
    env._expert_diagnostics = diag
    return result, diag
