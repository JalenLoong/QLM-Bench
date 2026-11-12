"""sweep_block_to_zone recovery routine E* (sft-v1/QLM-SIM-003).

A subclass of the frozen production ``Sweep`` (``sweep_expert``; the frozen files and E0 in ``sweep_takeover`` are not changed) that
adds state feedback on the block during the entry and the sweep. Every term reads only the current privileged state, so the same
routine runs from a reset, from a demonstration state and from a student state; there are no scene-specific values.

Why the production sweep fails from a late student state (exploration set, E0 at point B). The FL foot is a swing leg riding a
three-legged trot (period ~0.72 s): it meets the block in short kicks, and during each kick it also travels along the pushed face
towards +x, so friction drags the block with it. With the face square to the sweep the block drifts 0.45-0.5 m sideways per metre
swept; the drift falls as the block turns clockwise (the push follows the face normal) and vanishes near -24 deg. The yaw in turn
is set by where on the face the kicks land: a foot behind the face centre (-x) turns the block counter-clockwise, which rotates the
push further into +x and leaves the foot further behind. Production stays on the good side of that balance because its long align
stage integrates a +1.5..2 cm foot-tracking bias before the first contact and the bias is then frozen. A takeover at B has ~3 s of
alignment, the bias is still near 0, the first stroke lands 3-5 cm behind centre, the block turns to +yaw and drifts 6-9 cm: past
the +x edge of the goal and out of the leg's forward reach, where the kicks fade and the episode times out. Independently, production
measures the contact depth from the block's extent along the sweep, which at 20 deg of yaw leaves the foot short of the face, and its
lower->sweep gate (two consecutive ticks within 8 mm and 4 cm/s on a foot that swings +-1 cm with the trot) opens by chance.

What E* adds (``DEFAULT_PARAMS``; with every term disabled the routine is E0, and from reset the production expert, command for
command):
  entry       E0's entry rule (``sweep_takeover.enter_midway``), then for an interaction entry: the base x goal never drops below
              the measured base x (no walk back to the entry anchor) and the coordinated advance to the push position starts at once.
  lower_gate  the sweep starts once the lowered foot has stayed beside the face for one gait cycle with its mean x on the block.
  steering    the contact point is defined on the pushed face in the block frame: ``overlap_m`` into the face, at an offset along it
              from the cascade lateral drift from the sweep line -> yaw reference -> offset. Replaces the production side target
              (extent-based depth, +-8 mm x steering) in every route of the sweep, including the x of the first small stroke.
  tracking    the foot-tracking bias keeps integrating during the sweep, on intended minus measured foot x, while the reference is
              not slewing.
  base_follow the base x goal follows the block's forward drift within the production clearance cap, so the foot stays in reach.
The stage machine (raise/align/lower, first stroke, body shift, final sweep), heights, speeds, heading law and base y logic are the
frozen production ones.
"""
import collections
import contextlib
import copy
import os
from pathlib import Path
import time as wall

import numpy as np

from qlm_bench.sft_v1 import sweep_expert, sweep_takeover as st, takeover as tk

TASK = st.TASK
VERSION = 'sweep_recovery-v1'
KIND = 'sweep_recovery'
DEFAULT_PARAMS = {
    'schema': 'qlm-sft-v1-sweep-recovery-params-v1', 'version': VERSION,
    'entry': {'rule': copy.deepcopy(st.E0_PARAMS), 'base_x_floor': True, 'advance_at_once': True},
    'tracking': {'enabled': True, 'gain_per_s': 1.0, 'rate_m_s': 0.01, 'limit_m': 0.04, 'settled_m': 0.01,
                 'routes': ['acquire_first_side_contact', 'first_small_stroke_body_held', 'reacquire_final_side_contact_body_held',
                            'final_sweep_body_held']},
    'steering': {'enabled': True, 'neutral_m': 0.0, 'k_yaw_m_per_rad': 0.12, 'face_margin_m': 0.025, 'overlap_m': 0.012,
                 'k_lateral_rad_per_m': 10.0, 'yaw_bias_deg': -14.0, 'yaw_ref_deg': [-24.0, 5.0], 'slew_m_s': 0.03},
    'base_follow': {'enabled': True, 'gain': 1.0, 'limit_m': 0.08},
    'lower_gate': {'enabled': True, 'window_s': 0.72, 'mean_x_m': 0.012, 'max_x_m': 0.03, 'max_foot_z_m': 0.09, 'min_gap_m': 0.005},
}


def params_sha256(params):
    return st.params_sha256(params)


_CLASS = None


def recovery_class():
    """The E* class, a subclass of the frozen production ``Sweep`` (built once per process)."""
    global _CLASS
    if _CLASS is not None:
        return _CLASS
    base = getattr(sweep_expert.module(), 'Sweep')

    class Recovery(base):
        def __init__(self, config=None, params=None):
            super().__init__(config)
            self.rec = copy.deepcopy(DEFAULT_PARAMS if params is None else params)

        def configure(self):
            self.rec_ready = False
            super().configure()
            m, d = self.runtime.physics.model, self.runtime.physics.data[0]
            gid = m.geom('sw_block').id
            R = d.geom_xmat[gid].reshape(3, 3)
            dots = [float(R[:2, k] @ -self.direction) for k in (0, 1)]
            k = int(np.argmax(np.abs(dots)))
            self.rec_axis, self.rec_sign = k, float(np.sign(dots[k]))  # Pushed face: the block axis closest to -direction at reset.
            self.rec_face_half = float(m.geom_size[gid][1 - k])
            self.rec_lateral = np.array([-self.direction[1], self.direction[0]])  # Across the sweep, ~ +x.
            self.rec_tangent_sign = float(np.sign(R[:2, 1 - k] @ self.rec_lateral)) or 1.
            self.rec_block0 = d.geom_xpos[gid][:2].copy()
            self.rec_floor_x = None
            self.rec_offset = 0.
            self.rec_lower = collections.deque()
            self.rec_gate_s = None
            self.rec_log = []
            self.rec_ready = True
            self.update_reach_goal()

        # ---- measurements
        def rec_measure(self):
            m, d = self.runtime.physics.model, self.runtime.physics.data[0]
            gid = m.geom('sw_block').id
            p, R = d.geom_xpos[gid], d.geom_xmat[gid].reshape(3, 3)
            normal = self.rec_sign * R[:2, self.rec_axis]
            back = -self.direction
            yaw = float(np.arctan2(back[0] * normal[1] - back[1] * normal[0], back @ normal))  # Face normal vs -direction, CCW +.
            lateral = float((p[:2] - self.rec_block0) @ self.rec_lateral)
            return p, yaw, lateral

        # ---- base goal
        def update_reach_goal(self):
            super().update_reach_goal()
            if not getattr(self, 'rec_ready', False):
                return
            x = float(self.base_goal[0])
            follow = self.rec['base_follow']
            if follow['enabled'] and getattr(self, 'entry_stage', 'raise') == 'sweep':
                p = self.runtime.task.geometric_center(0)
                x += float(np.clip(follow['gain'] * (p[0] - self.rec_block0[0]), 0., follow['limit_m']))
            if self.rec_floor_x is not None and getattr(self, 'route', 'entry') == 'entry':
                x = max(x, self.rec_floor_x)
            self.base_goal[0] = min(x, float(self.base_x_cap))

        # ---- contact point
        def rec_steer(self, dt):
            """Lateral drift -> yaw reference -> contact position along the pushed face (block frame), slewed."""
            s = self.rec['steering']
            p, yaw, lateral = self.rec_measure()
            yaw_ref = float(np.clip(np.deg2rad(s['yaw_bias_deg']) - s['k_lateral_rad_per_m'] * lateral, *np.deg2rad(s['yaw_ref_deg'])))
            limit = max(0., self.rec_face_half - s['face_margin_m'])  # Keep the foot on the face.
            wanted = float(np.clip(s['neutral_m'] + s['k_yaw_m_per_rad'] * (yaw - yaw_ref), -limit, limit))
            if self.entry_stage != 'sweep':
                wanted = 0.
            step = s['slew_m_s'] * dt
            self.rec_offset += float(np.clip(wanted - self.rec_offset, -step, step))
            return yaw, yaw_ref, lateral

        def rec_contact(self):
            """World xy where the foot centre is meant to be: ``rec_offset`` along the pushed face, pressed ``overlap`` into it."""
            m, d = self.runtime.physics.model, self.runtime.physics.data[0]
            gid = m.geom('sw_block').id
            p, R, half = d.geom_xpos[gid], d.geom_xmat[gid].reshape(3, 3), m.geom_size[gid]
            normal = self.rec_sign * R[:2, self.rec_axis]
            tangent = self.rec_tangent_sign * R[:2, 1 - self.rec_axis]
            radius = float(m.geom_size[m.geom('FL').id, 0])
            return p[:2] + tangent * self.rec_offset + normal * (float(half[self.rec_axis]) + radius - self.rec['steering']['overlap_m'])

        def rec_track(self, dt, intended_x, commanded_x):
            """Foot-tracking bias during the sweep: integrates intended minus measured foot x while the reference is not slewing."""
            k = self.rec['tracking']
            if not k['enabled'] or self.route not in k['routes'] or abs(float(self.last_target[0]) - commanded_x) > k['settled_m']:
                return
            foot = self.runtime.physics.data[0].geom_xpos[self.runtime.physics.model.geom('FL').id]
            rate = float(np.clip(k['gain_per_s'] * (intended_x - foot[0]), -k['rate_m_s'], k['rate_m_s']))
            self.entry_x_bias = float(np.clip(self.entry_x_bias + rate * dt, -k['limit_m'], k['limit_m']))

        def state(self):
            p, foot, side, stable, stopped, gap = super().state()
            if self.rec['steering']['enabled']:
                side = side.copy()
                side[:2] = self.rec_contact()
                side[0] += self.entry_x_bias
            return p, foot, side, stable, stopped, gap

        def interaction(self, age, t, dt):
            yaw, yaw_ref, lateral = self.rec_steer(dt)
            if self.entry_stage == 'sweep' and self.rec['steering']['enabled']:
                intended = self.rec_contact()
                self.rec_track(dt, float(intended[0]), float(intended[0]) + self.entry_x_bias)
                if self.route == 'first_small_stroke_body_held' and self.first_endpoint is not None:
                    self.first_endpoint[0] = float(intended[0]) + self.entry_x_bias  # The stroke keeps its length; its x follows the face.
            self.rec_now = (yaw, yaw_ref, lateral)
            return super().interaction(age, t, dt)

        def rec_lower_gate(self, t):
            """Start the sweep once the lowered foot has stayed beside the face, centred on the block on average, for one gait cycle.

            The production gate asks for two consecutive ticks within 8 mm and 4 cm/s; the foot rides the trot (+-1 cm, ~1.4 Hz), so
            that gate opens by chance, often only through the 6 s escape. Same switch as the production gate and escape."""
            g = self.rec['lower_gate']
            if not g['enabled'] or self.entry_stage != 'lower':
                self.rec_lower.clear()
                return
            m, d = self.runtime.physics.model, self.runtime.physics.data[0]
            gid, f = m.geom('sw_block').id, m.geom('FL').id
            p, foot, R, half = d.geom_xpos[gid], d.geom_xpos[f], d.geom_xmat[gid].reshape(3, 3), m.geom_size[gid]
            support = sum(abs(self.direction @ R[:2, k]) * half[k] for k in (0, 1))
            gap = float((foot[:2] - p[:2]) @ (-self.direction)) - support - float(m.geom_size[f, 0])
            self.rec_lower.append((float(foot[0] - p[0]), float(foot[2]), gap))
            n = int(round(g['window_s'] / .02))
            while len(self.rec_lower) > n:
                self.rec_lower.popleft()
            if len(self.rec_lower) < n:
                return
            w = np.asarray(self.rec_lower)
            if (abs(w[:, 0].mean()) <= g['mean_x_m'] and np.abs(w[:, 0]).max() <= g['max_x_m'] and w[:, 1].max() <= g['max_foot_z_m']
                    and w[:, 2].min() >= g['min_gap_m']):
                self.rec_gate_s = t
                self.entry_stage = 'sweep'
                self.entry_completion = t
                self.last_target = self.entry_target.copy()
                self.enter('acquire_first_side_contact', t)
                self.rec_lower.clear()

        def command(self):
            self.rec_now = None
            values, diag = super().command()
            t = float(self.runtime.physics.ticks[0]) * .002
            self.rec_lower_gate(t)
            now = self.rec_now or (np.nan, np.nan, np.nan)
            wanted = diag.get('unprojected_world_target')
            diag['commanded_contact_point'] = wanted if wanted is not None else diag.get('world_target')
            self.rec_log.append([t, *now, self.rec_offset, self.entry_x_bias, *self.base_goal, *diag['world_target']])
            return values, diag

    _CLASS = Recovery
    return _CLASS


LOG_COLUMNS = ('t_s', 'face_yaw_rad', 'yaw_ref_rad', 'lateral_m', 'offset_m', 'tracking_bias_m', 'base_goal_x', 'base_goal_y',
               'reference_x', 'reference_y', 'reference_z')


def make(rt, ec, params=None):
    """E* configured on this runtime at the case's initial state (call right after ``reconstruct``)."""
    params = copy.deepcopy(DEFAULT_PARAMS if params is None else params)
    expert = recovery_class()(sweep_expert.recipe(), params)
    with contextlib.redirect_stdout(open(os.devnull, 'w')):
        expert.reset(rt, st.scene_of(ec))
    m, d = rt.physics.model, rt.physics.data[0]
    gid = m.geom('sw_block').id
    expert.sft_v1_initial_block_xy = d.geom_xpos[gid][:2].copy()
    expert.sft_v1_initial_block_yaw = st._yaw(d.geom_xmat[gid].reshape(3, 3))
    config = {'kind': KIND, 'version': VERSION, 'frozen_expert': sweep_expert.verify(),
              'recipe_sha256': params_sha256(sweep_expert.recipe()), 'recovery_params': params,
              'recovery_params_sha256': params_sha256(params)}
    return expert, config


def enter_midway(expert, rt):
    """E0's entry rule on the restored state, then E*'s own entry terms; returns the decision record."""
    entry = expert.rec['entry']
    record = st.enter_midway(expert, rt, entry['rule'])
    if entry['base_x_floor'] and record['decision'].startswith('interaction'):
        expert.rec_floor_x = float(expert.core.robot.position[0, 0].cpu())
        if entry['advance_at_once'] and expert.coord_lower_start is None:
            # The coordinated base advance (a 2 s ramp that production starts with the align stage) counts as done: the base heads
            # for the push position from the takeover on instead of waiting at its present x.
            expert.coord_lower_start = record['t_s'] - 2.
        expert.update_reach_goal()
    record['base_x_floor'] = expert.rec_floor_x
    return record


def _finish(expert, arrays):
    arrays['recovery_log'] = np.asarray(expert.rec_log, np.float64).reshape(-1, len(LOG_COLUMNS))
    arrays['recovery_log_columns'] = np.asarray(LOG_COLUMNS)
    return arrays


def from_reset(cache, *, case, model, params=None, name='reset', max_seconds=None):
    from qlm_bench.backends.mujoco.suite import reconstruct
    rt, ec, _ = cache.get(case, model)
    if rt.task.task != TASK:
        raise ValueError('sweep_recovery is for sweep_block_to_zone')
    reconstruct(rt, ec)
    expert, config = make(rt, ec, params)
    started = wall.monotonic()
    arrays, outcome = st._loop(rt, expert, name, max_seconds)
    start = {'mode': 'reset', 'case_seed': ec.seed}
    return _finish(expert, arrays), tk._summary(ec, case, model, cache.controller, start, config, outcome, wall.monotonic() - started)


def takeover(cache, *, case, model, state, params=None, name='takeover', max_seconds=None):
    from qlm_bench.backends.mujoco.rl_v2 import snapshot as snap
    from qlm_bench.backends.mujoco.suite import reconstruct
    from qlm_bench.rl_v3 import own_state
    rt, ec, binding = cache.get(case, model)
    if rt.task.task != TASK:
        raise ValueError('sweep_recovery is for sweep_block_to_zone')
    reconstruct(rt, ec)
    expert, config = make(rt, ec, params)
    stored, record = own_state.load(Path(state), binding_sha256=binding)
    snap.restore(rt, stored)
    config['entry'] = enter_midway(expert, rt)
    started = wall.monotonic()
    arrays, outcome = st._loop(rt, expert, name, max_seconds)
    start = {'mode': 'takeover', 'state': str(Path(state).resolve()), 'state_sha256': record['snapshot_sha256'],
             'absolute_tick': record['absolute_tick'], 'origin': record['origin']}
    return _finish(expert, arrays), tk._summary(ec, case, model, cache.controller, start, config, outcome, wall.monotonic() - started)
