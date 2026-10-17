"""Review-stage Push reference candidate: bounded Base/FL lateral coordination.

This version is not a production recipe. It composes the retained staged Push
template, leaves its FL world progression intact, and replaces only base vy during
manipulation. No integral, actor, IK, physics, camera or success-rule change.
"""
import numpy as np

from .template import PushTemplateExecutor, quat_matrix


def lateral_reference_command(values, *, phase, elapsed, working_y=.12,
                              gain=1., maximum_vy=.05, blend_s=.4):
    values = np.asarray(values, dtype=np.float64)
    if values.shape != (9,) or not np.isfinite(values).all():
        raise ValueError('Finite native9 required')
    parameters = np.asarray([elapsed, working_y, gain, maximum_vy, blend_s])
    if not np.isfinite(parameters).all() or elapsed < 0 or not (.05 <= working_y <= .20) or not (
            0 < gain <= 2 and 0 < maximum_vy <= .08 and blend_s > 0):
        raise ValueError('Invalid bounded reference coordination')
    result = values.copy()
    if phase == 'straight_push':
        # The native target already uses the heading-aligned projected-COM frame.
        # A target too far inboard calls for rightward base movement (negative vy).
        desired = np.clip(gain * (values[4] - working_y), -maximum_vy, maximum_vy)
        ratio = min(1., elapsed / blend_s)
        smooth = ratio * ratio * (3. - 2. * ratio)
        result[1] = (1. - smooth) * values[1] + smooth * desired
    return result.tolist()


class ReviewPushExecutor(PushTemplateExecutor):
    def __init__(self, bundle, *, working_y=.12, gain=1., maximum_vy=.05):
        super().__init__(bundle)
        self.coordination = dict(working_y=working_y, gain=gain, maximum_vy=maximum_vy)
        lateral_reference_command([0.]*9, phase='settle', elapsed=0., **self.coordination)

    def reset(self, runtime, scene):
        super().reset(runtime, scene)
        self.push_entry_s = None

    def command(self):
        values, diagnostic = super().command()
        t = float(self.runtime.physics.ticks[0]) * .002
        if diagnostic['phase'] == 'straight_push' and self.push_entry_s is None:
            self.push_entry_s = t
        elapsed = 0. if self.push_entry_s is None else t - self.push_entry_s
        adjusted = lateral_reference_command(values, phase=diagnostic['phase'], elapsed=elapsed, **self.coordination)
        diagnostic.update(reference_recipe='push-lateral-coordination-review-v1',
                          base_vy_before_coordination=values[1],
                          base_vy_after_coordination=adjusted[1],
                          coordination=self.coordination, reference_review_required=True)
        return adjusted, diagnostic


def bounded_cross_track_offset(cross_track, previous, *, dt=.02, gain=2., limit=.10, rate=.15):
    """Bounded contact-line correction; never a task-success predicate."""
    parameters=np.asarray([cross_track,previous,dt,gain,limit,rate],dtype=float)
    if not np.isfinite(parameters).all() or min(dt,gain,limit,rate)<=0:
        raise ValueError('Finite positive correction parameters required')
    target=float(np.clip(gain*cross_track,-limit,limit))
    return float(previous+np.clip(target-previous,-rate*dt,rate*dt))


def continuous_world_target(target, previous, maximum_step):
    target=np.asarray(target,dtype=float)
    if target.shape!=(3,) or not np.isfinite(target).all() or not np.isfinite(maximum_step) or maximum_step<=0:
        raise ValueError('Finite world target and positive step required')
    if previous is None:return target.copy()
    previous=np.asarray(previous,dtype=float)
    if previous.shape!=(3,) or not np.isfinite(previous).all():raise ValueError('Invalid previous world target')
    delta=target-previous;distance=float(np.linalg.norm(delta))
    return previous+delta*min(1.,maximum_step/max(distance,1e-12))


class ContactAwarePushExecutor(ReviewPushExecutor):
    """Review-stage v2 retarget follows actual lateral object progress.

    The longitudinal reference progression and accepted base/FL working lane stay
    intact. A bounded contact offset steers against cross-track drift before the
    footprint leaves the unchanged goal. The same rule applies to every seed.
    """
    def __init__(self,bundle,*,maximum_world_step=None,**kwargs):
        super().__init__(bundle,**kwargs)
        self.maximum_world_step=maximum_world_step

    def reset(self,runtime,scene):
        super().reset(runtime,scene)
        self.line_start=runtime.task.geometric_center(0)[:2].copy()
        goal=np.array([np.mean(scene['goal_x']),np.mean(scene['goal_y'])])
        direction=goal-self.line_start
        if np.linalg.norm(direction)<.1:raise ValueError('No meaningful push distance')
        direction/=np.linalg.norm(direction)
        self.lateral=np.array([-direction[1],direction[0]])
        self.contact_offset=0.
        self.previous_target_world=None

    def command(self):
        from qlm_bench.controllers.rambo.math import quat_mul,quat_inv
        values,diagnostic=PushTemplateExecutor.command(self)
        rt=self.runtime;t=float(rt.physics.ticks[0])*.002
        cross=float((rt.task.geometric_center(0)[:2]-self.line_start)@self.lateral)
        if diagnostic['phase']=='straight_push':
            if self.push_entry_s is None:self.push_entry_s=t
            self.contact_offset=bounded_cross_track_offset(cross,self.contact_offset)
            target=np.asarray(diagnostic['commanded_contact_point']).copy()
            target[:2]+=self.lateral*self.contact_offset
            projected=quat_mul(rt.core.base_quat,quat_inv(rt.core.base_quat_rp))[0].cpu().numpy()
            R=quat_matrix(projected);origin=rt.core.robot.position[0].cpu().numpy().copy();origin[2]=0.
            values[3:6]=(R.T@(target-origin)).tolist()
            diagnostic['commanded_contact_point']=target.tolist()
        if self.maximum_world_step is not None:
            target=continuous_world_target(diagnostic['commanded_contact_point'],
                                           self.previous_target_world,self.maximum_world_step)
            self.previous_target_world=target.copy()
            projected=quat_mul(rt.core.base_quat,quat_inv(rt.core.base_quat_rp))[0].cpu().numpy()
            R=quat_matrix(projected);origin=rt.core.robot.position[0].cpu().numpy().copy();origin[2]=0.
            values[3:6]=(R.T@(target-origin)).tolist()
            diagnostic['commanded_contact_point']=target.tolist()
        elapsed=0. if self.push_entry_s is None else t-self.push_entry_s
        adjusted=lateral_reference_command(values,phase=diagnostic['phase'],elapsed=elapsed,**self.coordination)
        projected=quat_mul(rt.core.base_quat,quat_inv(rt.core.base_quat_rp))[0].cpu().numpy()
        R=quat_matrix(projected)
        diagnostic.update(reference_recipe=('push-contact-cross-track-smooth-review-v3' if self.maximum_world_step else 'push-contact-cross-track-review-v2'),
                          template_world_velocity_before_coordination=diagnostic['commanded_world_base_velocity'],
                          commanded_world_base_velocity=(R@np.array([adjusted[0],adjusted[1],0.])).tolist(),
                          object_cross_track_m=cross,contact_offset_m=self.contact_offset,
                          maximum_world_target_step_m=self.maximum_world_step,
                          coordination=self.coordination,reference_review_required=True)
        return adjusted,diagnostic
