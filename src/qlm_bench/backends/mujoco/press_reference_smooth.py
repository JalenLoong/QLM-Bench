"""High-level Press trajectory with a carried leg during base motion.

All output remains native9. Original RAMBO IK/FK is read only; no motor target,
controller history, object state, physics parameter or internal gain is changed.
"""
import copy
import numpy as np


DEFAULT = {
    'recipe_id': 'press-body-carry-v2', 'carry_body_xyz_m': [.24, .17, -.16],
    'working_lateral_m': .17, 'working_forward_m': .36,
    'carry_seconds': 1.2, 'base_speed_m_s': .05, 'base_acceleration_m_s2': .12,
    'base_goal_gain': 1.0, 'base_tolerance_m': .008, 'base_stable_seconds': .6,
    'base_feedback_smoothing_s': .2, 'lateral_integral_gain': .2, 'lateral_integral_limit_m_s': .03,
    'present_seconds': 1.8, 'press_seconds': 2., 'contact_z_offset_m': -.01,
    'joint_reference_rate_deg_s': [60., 90., 90.],
    'press_tracking_gain': .7, 'press_tracking_limit_m': .03,
    'servo_entry_m': .008, 'servo_goal_m': .015,
}


def blend(t):
    t = float(np.clip(t, 0., 1.))
    return t*t*(3.-2.*t)


def limited_step(current, target, rate, dt):
    return np.asarray(current) + np.clip(np.asarray(target)-current, -np.asarray(rate)*dt, np.asarray(rate)*dt)


def retained_fk(joints, hip_offset, link_lengths):
    """Same analytical FL endpoint convention used by RAMBOCore.ee_pos_b."""
    hip, thigh, calf = np.asarray(joints)
    lhip, upper, lower = np.asarray(link_lengths)
    distance = np.sqrt(upper**2 + lower**2 + 2*upper*lower*np.cos(calf))
    angle = thigh + calf/2
    x = -distance*np.sin(angle); z = -distance*np.cos(angle)
    return np.asarray(hip_offset) + [x, np.cos(hip)*lhip - np.sin(hip)*z,
                                    np.sin(hip)*lhip + np.cos(hip)*z]


class SmoothPressExecutor:
    def __init__(self, config=None):
        self.config = copy.deepcopy(DEFAULT)
        if config is not None:
            if set(config) - set(DEFAULT):
                raise ValueError('Unknown explicit reference configuration')
            self.config.update(copy.deepcopy(config))
        numeric = [v for v in self.config.values() if isinstance(v, (int, float))]
        if not np.isfinite(numeric).all():
            raise ValueError('Nonfinite reference configuration')

    def reset(self, runtime, scene):
        self.runtime = runtime; self.core = runtime.core
        p = runtime.profile['source_profile']
        self.legacy = p['expert']; self.face = np.asarray(p['button_rest_front_xyz'], float)
        self.phase = 'settle'; self.phase_start = 0.; self.velocity = np.zeros(2)
        self.filtered_joints = None; self.press_integral_x = 0.; self.servo_x = None
        self.base_goal = np.array([self.face[0] + self.legacy['press_center_beyond_face_m'] - self.config['working_forward_m'],
                                   self.face[1] - self.config['working_lateral_m']])
        self.goal = self.face.copy(); self.goal[0] += self.legacy['press_center_beyond_face_m']
        self.goal[2] += self.config['contact_z_offset_m']
        self.time = None; self.stable_since = None
        self.base_feedback = None; self.lateral_integral = 0.
        self.joint_lower = self.core.default_joint_pos_limits[0, [0, 4, 8], 0].cpu().numpy() + .1
        self.joint_upper = self.core.default_joint_pos_limits[0, [0, 4, 8], 1].cpu().numpy() - .1

    def world_body_point(self, body):
        from qlm_bench.controllers.rambo.math import quat_apply
        import torch
        return (quat_apply(self.core.base_quat,
            torch.tensor(np.asarray(body)[None], dtype=torch.float32, device=self.core.device)) + self.core.robot.position)[0].cpu().numpy()

    def actual_world_point(self):
        return self.world_body_point(self.core.ee_pos_b[0, 0].cpu().numpy())

    def transition(self, phase, time):
        self.phase = phase; self.phase_start = time
        self.phase_world_start = self.world_body_point(self.output_body) if self.filtered_joints is not None else self.actual_world_point()

    def command(self):
        import torch
        from qlm_bench.controllers.rambo.math import quat_mul, quat_inv, quat_apply_inverse
        time = float(self.runtime.physics.ticks[0]) * .002
        dt = .02 if self.time is None else time-self.time
        if not 0 < dt <= .020001:
            raise ValueError('Reference must run once at each50Hz completed boundary')
        self.time = time; base = self.core.robot.position[0].cpu().numpy(); actual = self.actual_world_point()
        if self.base_feedback is None:
            self.base_feedback = base[:2].copy()
        else:
            self.base_feedback += (1-np.exp(-dt/self.config['base_feedback_smoothing_s']))*(base[:2]-self.base_feedback)
        if self.phase == 'settle' and time >= self.legacy['settle_s']:
            self.filtered_joints = self.core.joint_pos[0, [0, 4, 8]].cpu().numpy().astype(float)
            self.output_body = self.core.ee_pos_b[0, 0].cpu().numpy()
            self.carry_start = self.output_body.copy(); self.transition('carry', time)
        age = time-self.phase_start; wanted_velocity = np.zeros(2); wanted_world = None
        if self.phase == 'settle':
            values = [0., 0., 0., .1934, .142, .05, 0., 0., 0.]
            return values, {'phase': 'settle', 'button_displacement_m': float(self.runtime.task.progress(0)),
                'actual_fl_eef_world': actual.tolist(), 'commanded_world_fl_position': None,
                'commanded_world_base_velocity': [0., 0., 0.], 'recipe': self.config['recipe_id']}
        if self.phase == 'carry':
            wanted_body = self.carry_start + (np.asarray(self.config['carry_body_xyz_m']) - self.carry_start) * blend(age/self.config['carry_seconds'])
            if age >= self.config['carry_seconds']:
                self.transition('approach_base', time)
        elif self.phase in ('approach_base', 'stabilize_base'):
            wanted_body = np.asarray(self.config['carry_body_xyz_m'])
            error = self.base_goal - self.base_feedback
            self.lateral_integral = float(np.clip(self.lateral_integral + dt*self.config['lateral_integral_gain']*error[1],
                -self.config['lateral_integral_limit_m_s'], self.config['lateral_integral_limit_m_s']))
            speed = self.config['base_speed_m_s'] if self.phase == 'approach_base' else .02
            wanted_velocity = np.clip(self.config['base_goal_gain']*error, -speed, speed)
            wanted_velocity[1] = np.clip(wanted_velocity[1]+self.lateral_integral, -self.config['base_speed_m_s'], self.config['base_speed_m_s'])
            if self.phase == 'approach_base' and np.max(abs(error)) <= self.config['base_tolerance_m']:
                self.transition('stabilize_base', time)
            elif self.phase == 'stabilize_base':
                if np.max(abs(error)) <= .015:
                    if self.stable_since is None:
                        self.stable_since = time
                    if time-self.stable_since >= self.config['base_stable_seconds']:
                        self.transition('present', time)
                else:
                    self.stable_since = None
        else:
            error = self.base_goal - self.base_feedback
            self.lateral_integral = float(np.clip(self.lateral_integral + dt*self.config['lateral_integral_gain']*error[1],
                -self.config['lateral_integral_limit_m_s'], self.config['lateral_integral_limit_m_s']))
            wanted_velocity = np.clip(.7*error, -.02, .02)
            wanted_velocity[1] = np.clip(wanted_velocity[1]+self.lateral_integral, -.04, .04)
            if self.phase == 'present':
                end = self.goal.copy(); end[0] = self.face[0] - self.legacy['standoff_from_eef_m']
                wanted_world = self.phase_world_start + (end - self.phase_world_start)*blend(age/self.config['present_seconds'])
                if age >= self.config['present_seconds']:
                    self.transition('press', time)
            else:
                wanted_world = self.phase_world_start + (self.goal - self.phase_world_start)*blend(age/self.config['press_seconds'])
                displacement = float(self.runtime.task.progress(0))
                if displacement < self.config['servo_entry_m'] and self.servo_x is None:
                    self.press_integral_x = float(np.clip(self.press_integral_x + dt*self.config['press_tracking_gain']*(wanted_world[0]-actual[0]),
                        -self.config['press_tracking_limit_m'], self.config['press_tracking_limit_m']))
                    wanted_world[0] += self.press_integral_x
                else:
                    if self.servo_x is None:
                        self.servo_x = float(self.last_world_target[0])
                    self.servo_x += dt*float(np.clip(2.*(self.config['servo_goal_m']-displacement), -.006, .012))
                    wanted_world[0] = self.servo_x
            wanted_body = quat_apply_inverse(self.core.base_quat,
                torch.tensor((wanted_world-base)[None], dtype=torch.float32, device=self.core.device))[0].cpu().numpy()
        # Reference projection uses the unchanged original inverse/forward geometry.
        ideal = self.core.get_motor_angles_from_foot_positions_fl(torch.tensor(wanted_body[None], dtype=torch.float32, device=self.core.device))[0].cpu().numpy()
        ideal = np.clip(ideal, self.joint_lower, self.joint_upper)
        rate = np.deg2rad(self.config['joint_reference_rate_deg_s'])
        self.filtered_joints = limited_step(self.filtered_joints, ideal, rate, dt)
        self.output_body = retained_fk(self.filtered_joints, self.core.hip_offset[0].cpu().numpy(), self.core.link_lengths.cpu().numpy())
        world = self.world_body_point(self.output_body); self.last_world_target = world.copy()
        self.velocity = limited_step(self.velocity, wanted_velocity, self.config['base_acceleration_m_s2'], dt)
        projected = quat_mul(self.core.base_quat, quat_inv(self.core.base_quat_rp))
        origin = self.core.robot.position[0].clone(); origin[2] = 0.
        native = quat_apply_inverse(projected, torch.tensor(world[None], dtype=torch.float32, device=self.core.device)-origin[None])[0]
        native_velocity = quat_apply_inverse(projected, torch.tensor([[*self.velocity, 0.]], dtype=torch.float32, device=self.core.device))[0]
        values = [float(native_velocity[0]), float(native_velocity[1]), 0., *native.cpu().tolist(), 0., 0., 0.]
        diagnostic = {'phase': self.phase, 'recipe': self.config['recipe_id'],
            'commanded_world_fl_position': world.tolist(), 'unprojected_world_goal': None if wanted_world is None else wanted_world.tolist(),
            'actual_fl_eef_world': actual.tolist(), 'reference_body_point': self.output_body.tolist(),
            'reference_geometric_joints_rad': self.filtered_joints.tolist(),
            'commanded_world_base_velocity': [*self.velocity.tolist(), 0.], 'base_goal_xy': self.base_goal.tolist(),
            'base_world_position': base.tolist(), 'button_displacement_m': float(self.runtime.task.progress(0)),
            'base_feedback_xy': self.base_feedback.tolist(), 'lateral_integral_velocity_m_s': self.lateral_integral,
            'trajectory_projection_scope': 'high-level native9 target only; original RAMBO internals unchanged',
            'contact': 'actual evidence recorded separately'}
        return values, diagnostic
