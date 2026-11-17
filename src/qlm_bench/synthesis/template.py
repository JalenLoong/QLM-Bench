"""Staged push_box reference retargeting (the approved push template); commands remain native9."""
import json
from pathlib import Path
import numpy as np
from qlm_bench.synthesis.trace import verify_trace,write_json,sha,CandidateRejected


def rotation_z(yaw):
    c,s=np.cos(yaw),np.sin(yaw)
    return np.array([[c,-s,0.],[s,c,0.],[0.,0.,1.]])


def quat_matrix(q):
    x,y,z,w=np.asarray(q,float)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
        [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
        [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


class PushTemplateExecutor:
    def __init__(self,bundle):
        self.root=Path(bundle);self.template=json.loads((self.root/'template.json').read_text())
        if sha(self.root/'paths.npz')!=self.template['paths_sha256']:raise ValueError('Template paths changed')
        with np.load(self.root/'paths.npz',allow_pickle=False) as z:self.paths={k:z[k].copy() for k in z.files}
    def reset(self,runtime,scene):
        self.runtime=runtime;self.scene=scene;self.wait=0.;self.last_time=0.;self.last_phase='settle'
        source=self.template['source_scene'];profile=self.template['source_profile']
        import mujoco
        j=mujoco.mj_name2id(runtime.physics.model,mujoco.mjtObj.mjOBJ_JOINT,'object_free');a=runtime.physics.model.jnt_qposadr[j]
        initial=np.array(scene['initial_state']['qpos']);original=np.array(source['initial_state']['qpos'])
        self.origin=original[a:a+3];self.new_origin=initial[a:a+3]
        center=self.origin+quat_matrix(original[a+3:a+7][[1,2,3,0]])@np.array(profile['center_local'])
        new_center=self.new_origin+quat_matrix(initial[a+3:a+7][[1,2,3,0]])@np.array(profile['center_local'])
        old_goal=np.array([np.mean(source['goal_x']),np.mean(source['goal_y']),center[2]])
        goal=np.array([np.mean(scene['goal_x']),np.mean(scene['goal_y']),new_center[2]])
        self.angle=float(np.arctan2((goal-new_center)[1],(goal-new_center)[0])-np.arctan2((old_goal-center)[1],(old_goal-center)[0]))
        self.rotation=rotation_z(self.angle)
        self.scale=float(np.clip(np.linalg.norm((goal-new_center)[:2])/np.linalg.norm((old_goal-center)[:2]),.85,1.15))
        self.phase_entry={};self.manip_start=next(s['start_s'] for s in self.template['stages'] if s['phase']=='straight_push')
    def _sample(self,name,t):
        values=self.paths[name];times=self.paths['time_s']
        p=np.array([np.interp(t,times,values[:,k]) for k in range(3)])
        if t>times[-1] and name in ('base_world','commanded_fl_world'):
            p+=self.paths['world_base_velocity'][-1]*(t-times[-1])
        return p
    def command(self):
        from qlm_bench.controllers.rambo.math import quat_mul,quat_inv
        rt=self.runtime;t=float(rt.physics.ticks[0])*.002
        tau=max(0.,t-self.wait)
        stage=self.template['stages'][0]['phase']
        for s in self.template['stages']:
            if tau>=s['start_s']:stage=s['phase']
        if stage=='straight_push':
            _,_,corners=rt.task.geometry(0)
            # This recipe has forward contact progression and no pull/recovery planner.
            # Once the entire box has passed the far goal edge it cannot continue.
            if float(corners[:,0].min())>self.scene['goal_x'][1]+.02:
                raise CandidateRejected('Whole box passed far goal edge; forward template cannot continue')
        base=rt.core.robot.position[0].cpu().numpy()
        # Geometric stage prerequisites, with a bounded simulation-time wait.
        previous=self.last_phase
        if stage!=previous and stage in ('normal_approach','straight_push'):
            if stage=='normal_approach':
                p,r,_=rt.task.geometry(0)
                face=p+r@np.array(rt.profile['face_center_local'])
                ready=float((face-base)@(self.rotation@np.array([1.,0.,0.])))<=.43
            else:
                actual=quat_matrix(rt.core.base_quat[0].cpu().numpy())@rt.core.ee_pos_b[0,0].cpu().numpy()+base
                desired=self.new_origin+self.rotation@(self._sample('commanded_fl_world',tau)-self.origin)
                ready=np.linalg.norm(desired-actual)<=.12
            if not ready:
                self.wait+=.02
                if self.wait>self.template['executor']['transition_wait_budget_s']:
                    raise CandidateRejected('Template phase prerequisite wait budget exhausted')
                tau=max(0.,t-self.wait);stage=previous
        self.last_phase=stage
        ref_base=self._sample('base_world',tau)
        target_base=self.new_origin+self.rotation@(ref_base-self.origin)
        target=self.new_origin+self.rotation@(self._sample('commanded_fl_world',tau)-self.origin)
        velocity=self.rotation@self._sample('world_base_velocity',tau)
        if tau>=self.manip_start:
            entry_base=self._sample('base_world',self.manip_start)
            entry_fl=self._sample('commanded_fl_world',self.manip_start)
            target_base=self.new_origin+self.rotation@(entry_base-self.origin+(ref_base-entry_base)*self.scale)
            target=self.new_origin+self.rotation@(entry_fl-self.origin+(self._sample('commanded_fl_world',tau)-entry_fl)*self.scale)
            velocity*=self.scale
        if stage=='settle':
            values=[0.,0.,0.,.1934,.142,.05,0.,0.,0.]
            projected=quat_mul(rt.core.base_quat,quat_inv(rt.core.base_quat_rp))[0].cpu().numpy()
            origin=base.copy();origin[2]=0.
            target=origin+quat_matrix(projected)@np.array(values[3:6])
        else:
            # Bounded feedback is part of one frozen recipe, never per-seed code.
            velocity[:2]+=(target_base-base)[:2]*self.template['executor']['base_feedback_gain']
            if stage=='normal_approach':velocity[:2]=np.clip((target_base-base)[:2]*.15,-.02,.02)
            velocity[:2]=np.clip(velocity[:2],-.18,.18)
            projected=quat_mul(rt.core.base_quat,quat_inv(rt.core.base_quat_rp))[0].cpu().numpy()
            R=quat_matrix(projected);origin=base.copy();origin[2]=0.
            local=R.T@(target-origin);v=R.T@velocity
            current_yaw=np.arctan2(R[1,0],R[0,0]);error=np.arctan2(np.sin(self.angle-current_yaw),np.cos(self.angle-current_yaw))
            wz=float(np.clip(error*.4,-.12,.12))
            values=[float(v[0]),float(v[1]),wz,*local.tolist(),0.,0.,0.]
        measured_fl=rt.core.ee_pos_b[0,0].cpu().numpy()
        measured_world=quat_matrix(rt.core.base_quat[0].cpu().numpy())@measured_fl+base
        return values,{'phase':stage,'template_id':self.template['template_id'],'template_progress_s':tau,
            'commanded_contact_point':target.tolist(),'actual_fl_eef_world':measured_world.tolist(),
            'base_reference_world':target_base.tolist(),'commanded_world_base_velocity':velocity.tolist(),
            'retarget_angle_rad':self.angle,'goal_distance_scale':self.scale,'physics_state_used':True}
