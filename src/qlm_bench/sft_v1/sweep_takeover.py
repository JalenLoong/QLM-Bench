"""sweep_block_to_zone expert runs from reset and mid-way takeover E0 (sft-v1/QLM-SIM-003).

Uses the takeover tool unchanged (``takeover.RuntimeCache`` trace-only NativeCPU runtime, ``run_loop``, ``save``); only the expert
differs. The expert is the frozen production ``Sweep`` (``sweep_expert.build()``), whose interface is ``reset(runtime, scene)`` +
``command()`` (production ``collect_trace`` convention) instead of ``ExpertAdapter``.

``from_reset``: ``suite.reconstruct`` (Standard100 reset of the EvalCase), ``expert.reset``, one command per 50 Hz tick to the
runtime's terminal. Same steps as the production trace, so the requested native9 must equal the production ``commands.jsonl``.

``takeover`` (E0): the expert must keep the geometry it would have had from reset (the sweep direction, contact/end points,
fixed base y, coordinated anchors, retarget translation and the workspace bounds are all computed by ``configure`` from the *initial*
block pose; at a displaced block ``retarget_executor.configure`` would even refuse the scene). So the runtime is first reset to the
case's initial state, ``expert.reset`` configures it exactly as in production, and only then is the own state restored into the same
runtime (the restore is complete, as the push takeovers already rely on). ``enter_midway`` then sets the expert's internal stage from
the current privileged state by the rule below, and the loop runs to the terminal (success with the 3-tick hold, fall, or the 40 s
horizon on the restored absolute clock).

E0 entry rule (``E0_PARAMS``, version ``sweep-e0-v2``; all quantities from the restored state in the expert's frame: d = its sweep
direction, face gap = foot offset along -d beyond the block support plus foot radius, side target = the point the production sweep
stage tracks, i.e. block centre - d*(support + foot radius - overlap) plus its x bias, at contact height):
  1. t < settle_seconds: leave the reset stage (settle).
  2. sweep-ready (foot z <= 0.075 m, -0.015 <= face gap <= 0.030 m, |foot x - side target x| <= 0.025 m): interaction, entry stage
     ``sweep``, route ``entry`` (becomes ``acquire_first_side_contact`` on the first command), base x ramp already completed.
  3. lower-ready (foot z >= 0.05 m, 0.005 <= face gap <= 0.060 m, |foot x - block x| <= 0.025 m): interaction, entry stage ``lower``,
     ramp completed.
  4. block disturbed (centre moved > 1 cm or |yaw change| > 3 deg) or foot within 0.15 m (xy) of the entry's outer point: interaction,
     entry stage ``raise`` (raise above the block at the current foot xy, align outside the face, lower, then sweep).
  5. otherwise by the base error to the range the interaction stage accepts (x between the entry anchor and the coordinated push x,
     both capped as ``update_reach_goal`` caps them; y = the expert's fixed base y): > 0.05 m ``approach_base``; > 0.025 m
     ``stabilize_base``; else interaction ``raise``.
In every case the reference joints restart from the measured FL joints (as the production carry entry does), the commanded base
velocity and yaw rate start from the measured ones (clipped to the stage caps), filters and counters start empty.
"""
import contextlib
import copy
import hashlib
import json
import os
from pathlib import Path
import time as wall

import numpy as np

from qlm_bench.sft_v1 import sweep_expert, takeover as tk

TASK = 'sweep_block_to_zone'
E0_VERSION = 'sweep-e0-v2'
E0_PARAMS = {
    'schema': 'qlm-sft-v1-sweep-e0-params-v1', 'version': E0_VERSION,
    'sweep_ready': {'max_foot_z_m': 0.075, 'face_gap_m': [-0.015, 0.030], 'max_x_to_side_target_m': 0.025},
    'lower_ready': {'min_foot_z_m': 0.05, 'face_gap_m': [0.005, 0.060], 'max_x_to_block_m': 0.025},
    'disturbed': {'translation_m': 0.01, 'yaw_deg': 3.0},
    'near_outer_xy_m': 0.15,
    'base_error_m': {'approach_above': 0.05, 'stabilize_above': 0.025},
    'initial_velocity': 'measured_clipped', 'initial_yaw_rate': 'measured_clipped',
}


def params_sha256(params):
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()


def scene_of(ec):
    return {'initial_state': copy.deepcopy(ec.initial_state), 'seed': ec.seed, 'case_id': ec.case_id}


def _yaw(R):
    return float(np.arctan2(R[1, 0], R[0, 0]))


def geometry(expert, rt):
    """Privileged quantities the entry rule reads (expert frame)."""
    m, d = rt.physics.model, rt.physics.data[0]
    gid, f = m.geom('sw_block').id, m.geom('FL').id
    p, foot = d.geom_xpos[gid].copy(), d.geom_xpos[f].copy()
    R, half, radius = d.geom_xmat[gid].reshape(3, 3), m.geom_size[gid], float(m.geom_size[f, 0])
    direction = np.asarray(expert.direction)
    support = sum(abs(direction @ R[:2, k]) * half[k] for k in (0, 1))
    side = p.copy()
    side[:2] -= direction * (support + radius - expert.config['contact_overlap_m'])
    goal_x = float(np.mean(rt.profile['goal_x']))
    side[0] += float(np.clip(.15 * (p[0] - goal_x), -.008, .008)) + expert.entry_x_bias
    side[2] = expert.config['contact_height_m']
    outer = p[:2] - direction * (support + radius + .025)
    gap = float((foot[:2] - p[:2]) @ (-direction)) - support - radius
    block0, yaw0 = expert.sft_v1_initial_block_xy, expert.sft_v1_initial_block_yaw
    return {'block': p, 'foot': foot, 'side_target': side, 'outer': outer, 'face_gap': gap, 'support': support,
            'block_translation': float(np.linalg.norm(p[:2] - block0)),
            'block_yaw_change_deg': float(np.rad2deg(np.arctan2(np.sin(_yaw(R) - yaw0), np.cos(_yaw(R) - yaw0))))}


def make(rt, ec):
    """Frozen production expert configured on this runtime at the case's initial state (call right after reconstruct)."""
    expert = sweep_expert.build()
    with contextlib.redirect_stdout(open(os.devnull, 'w')):
        expert.reset(rt, scene_of(ec))
    m, d = rt.physics.model, rt.physics.data[0]
    gid = m.geom('sw_block').id
    expert.sft_v1_initial_block_xy = d.geom_xpos[gid][:2].copy()  # Recorded at the reset state, before any restore.
    expert.sft_v1_initial_block_yaw = _yaw(d.geom_xmat[gid].reshape(3, 3))
    config = {'kind': None, 'frozen_expert': sweep_expert.verify(), 'recipe_sha256': params_sha256(sweep_expert.recipe())}
    return expert, config


def _measured_velocity(rt):
    v = rt.core.robot.linear_velocity_world[0].cpu().numpy().astype(float)
    w = rt.core.robot.angular_velocity_world[0].cpu().numpy().astype(float)
    return v[:2], float(w[2])


def enter_midway(expert, rt, params=None):
    """Set the expert's internal stage at the restored state; returns the decision record."""
    params = copy.deepcopy(E0_PARAMS if params is None else params)
    t = float(rt.physics.ticks[0]) * .002
    g = geometry(expert, rt)
    record = {'t_s': t, 'params_sha256': params_sha256(params),
              'geometry': {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in g.items()}}
    if t < expert.config['settle_seconds']:
        record['decision'] = 'settle_unchanged'
        return record
    core = expert.core
    # Reference joints restart from the measured FL joints, as the production settle->carry entry does.
    expert.filtered_joints = core.joint_pos[0, [0, 4, 8]].cpu().numpy().astype(float)
    expert.output_body = core.ee_pos_b[0, 0].cpu().numpy()
    expert.carry_start = expert.output_body.copy()
    expert.time = None
    expert.base_feedback = None
    expert.lateral_integral = 0.
    expert.stable_since = None
    expert.yaw_time = None
    v, w = _measured_velocity(rt)
    sr, lr, dist = params['sweep_ready'], params['lower_ready'], params['disturbed']
    foot, block = g['foot'], g['block']
    expert.update_reach_goal()  # route 'entry', no coordinated ramp yet: x goal = capped entry anchor
    base = core.robot.position[0].cpu().numpy()
    x_entry, y_goal, cap = float(expert.base_goal[0]), float(expert.base_goal[1]), float(expert.base_x_cap)
    x_push = min(float(expert.config['coordinated_push_base_x_m']), cap)
    lo, hi = min(x_entry, x_push), max(x_entry, x_push)
    base_error = max(lo - float(base[0]), float(base[0]) - hi, 0., abs(y_goal - float(base[1])))
    record['base_error_m'] = base_error
    record['interaction_base_range'] = {'x': [lo, hi], 'y': y_goal}
    disturbed = g['block_translation'] > dist['translation_m'] or abs(g['block_yaw_change_deg']) > dist['yaw_deg']
    near = float(np.linalg.norm(foot[:2] - g['outer'])) <= params['near_outer_xy_m']
    if (foot[2] <= sr['max_foot_z_m'] and sr['face_gap_m'][0] <= g['face_gap'] <= sr['face_gap_m'][1]
            and abs(float(foot[0] - g['side_target'][0])) <= sr['max_x_to_side_target_m']):
        decision, entry = 'interaction_sweep', 'sweep'
    elif (foot[2] >= lr['min_foot_z_m'] and lr['face_gap_m'][0] <= g['face_gap'] <= lr['face_gap_m'][1]
          and abs(float(foot[0] - block[0])) <= lr['max_x_to_block_m']):
        decision, entry = 'interaction_lower', 'lower'
    elif disturbed or near:
        decision, entry = 'interaction_raise', 'raise'
    elif base_error > params['base_error_m']['approach_above']:
        decision, entry = 'approach_base', None
    elif base_error > params['base_error_m']['stabilize_above']:
        decision, entry = 'stabilize_base', None
    else:
        decision, entry = 'interaction_raise', 'raise'
    record.update(decision=decision, disturbed=bool(disturbed), near_outer=bool(near))
    cap = expert.config['base_speed_m_s'] if decision == 'approach_base' else .035
    expert.velocity = np.clip(v, -cap, cap) if params['initial_velocity'] == 'measured_clipped' else np.zeros(2)
    ymax = float(expert.config.get('yaw_rate_max_rad_s', .25))
    expert.yaw_rate = float(np.clip(w, -ymax, ymax)) if params['initial_yaw_rate'] == 'measured_clipped' else 0.
    if entry is None:
        expert.transition(decision, t)
        return record
    if entry in ('lower', 'sweep'):
        expert.velocity[1] = float(np.clip(expert.velocity[1], -.02, .02))  # v9 interaction y cap
    expert.transition('interaction', t)
    expert.interaction_start = t
    expert.interaction_world_start = expert.phase_world_start.copy()
    expert.entry_stage = entry
    if entry in ('lower', 'sweep'):
        expert.coord_lower_start = t - 2.  # The base x ramp (2 s) of the coordinated entry is complete, as in production at this stage.
        expert.entry_target = foot.copy()
        expert.entry_start = foot.copy()
        expert.last_target = foot.copy()
    if entry == 'sweep':
        expert.entry_completion = t
    expert.update_reach_goal()
    return record


def _loop(rt, expert, name, max_seconds=None):
    with contextlib.redirect_stdout(open(os.devnull, 'w')):  # The chain prints 1 Hz diagnostics.
        return tk.run_loop(rt, expert, lambda ex, t: ex.command(), name=name, max_seconds=max_seconds)


def from_reset(cache, *, case, model, name='reset', max_seconds=None):
    from qlm_bench.backends.mujoco.suite import reconstruct
    rt, ec, _ = cache.get(case, model)
    if rt.task.task != TASK:
        raise ValueError('sweep_takeover is for sweep_block_to_zone')
    reconstruct(rt, ec)
    expert, config = make(rt, ec)
    config['kind'] = 'sweep_expert'
    started = wall.monotonic()
    arrays, outcome = _loop(rt, expert, name, max_seconds)
    start = {'mode': 'reset', 'case_seed': ec.seed}
    return arrays, tk._summary(ec, case, model, cache.controller, start, config, outcome, wall.monotonic() - started)


def takeover(cache, *, case, model, state, params=None, name='takeover', max_seconds=None):
    from qlm_bench.backends.mujoco.rl_v2 import snapshot as snap
    from qlm_bench.backends.mujoco.suite import reconstruct
    from qlm_bench.rl_v3 import own_state
    rt, ec, binding = cache.get(case, model)
    if rt.task.task != TASK:
        raise ValueError('sweep_takeover is for sweep_block_to_zone')
    reconstruct(rt, ec)
    expert, config = make(rt, ec)
    stored, record = own_state.load(Path(state), binding_sha256=binding)
    snap.restore(rt, stored)
    config['kind'] = 'sweep_e0'
    config['e0_params'] = copy.deepcopy(E0_PARAMS if params is None else params)
    config['entry'] = enter_midway(expert, rt, params)
    started = wall.monotonic()
    arrays, outcome = _loop(rt, expert, name, max_seconds)
    start = {'mode': 'takeover', 'state': str(Path(state).resolve()), 'state_sha256': record['snapshot_sha256'],
             'absolute_tick': record['absolute_tick'], 'origin': record['origin']}
    return arrays, tk._summary(ec, case, model, cache.controller, start, config, outcome, wall.monotonic() - started)
