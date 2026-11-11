"""Push-box recovery routine E* (sft-v1/QLM-SIM-001 skeleton; design 4.3 of task-specific-sft-design-20261110).

Same form as ``backends/mujoco/experts/push_box_expert.py``: ``command(env, time)`` reads the live simulator
through an ``ExpertAdapter`` and returns one 50 Hz native9 command ``[vx, vy, 0, fl_x, fl_y, fl_z, 0, 0, 0]``
(projected-COM frame, forces zero) plus a diagnostic dict.

Structure:

* ``configure(env, params)`` stores the versioned parameter set on the adapter and writes the regular-push
  options (``lateral_tracking_gain``, ``lateral_tracking_limit_m``, ``corner_recovery``) into the adapter's expert
  profile, exactly where ``push_box_expert`` reads them.
* ``enter_midway(env, time)`` is the mid-episode entry: stage ``straight_push``, push start = takeover time; settle
  and the approach phases are not replayed.
* Before the push stage (a run from reset) ``command`` delegates to the unmodified ``push_box_expert``.
* In the push stage it runs its own copy of the ``straight_push`` branch (regular push, design 4.3 item 1), then the
  steering hook (item 2), the existing ``corner_reference`` and the overshoot hook (item 3).

Only the regular push is implemented here. ``steer`` and ``overshoot_guard`` are placeholders owned by the
``tsft-synth`` session; with both disabled the output is bit-identical to ``push_box_expert`` under the same expert
profile (tests/qlm/test_sft_v1_takeover.py). Raise ``VERSION`` and record the frozen commit when the routine changes.
"""
import copy

import numpy as np

from qlm_bench.backends.mujoco.experts import push_box_expert
from qlm_bench.backends.mujoco.experts.push_box_corner_recovery import corner_reference

VERSION = 'push_box_recovery-v0-skeleton'
SCHEMA = 'qlm-sft-v1-push-box-recovery-params-v1'

# Regular-push options: the values the repository already uses for the scale-up push experts
# (rambo push_box_scenarios.py / push_box_scaleup_plan.py: gain 2.0, limit 0.015 m); corner_recovery on as in E0.
DEFAULT_PARAMS = {
    'schema': SCHEMA,
    'version': VERSION,
    'regular': {'lateral_tracking_gain': 2.0, 'lateral_tracking_limit_m': 0.015, 'corner_recovery': True},
    # Design 4.3 item 2 (owned by tsft-synth). Suggested fields; nothing reads them while disabled.
    'steering': {'enabled': False, 'theta_on_deg': None, 'theta_off_deg': None, 'k_yaw_m_per_rad': None,
                 'k_lateral': None, 'max_offset_m': None, 'vx_scale': None},
    # Design 4.3 item 3 (owned by tsft-synth).
    'overshoot': {'enabled': False},
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


def enter_midway(env, time):
    """Takeover entry at a restored chunk boundary: start in the push stage, push start = now."""
    env._expert_stage = 'straight_push'
    env._expert_push_start = float(time)
    env._recovery_entry_time = float(time)


# ------------------------------------------------------------------ hooks (tsft-synth)

def steer(env, time, geom, base, line_point, target, vx, vy, phase):
    """Design 4.3 item 2: turning push. Identity while disabled."""
    if not env._recovery_params['steering'].get('enabled'):
        return target, vx, vy, phase
    raise NotImplementedError('Turning push is implemented by tsft-synth (WP2)')


def overshoot_guard(env, time, geom, base, target, vx, vy, phase):
    """Design 4.3 item 3: overshoot protection. Identity while disabled."""
    if not env._recovery_params['overshoot'].get('enabled'):
        return target, vx, vy, phase
    raise NotImplementedError('Overshoot protection is implemented by tsft-synth (WP2)')


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
