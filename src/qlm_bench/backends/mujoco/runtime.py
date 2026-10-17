"""Native9 command runtime compatible with the existing synchronous QLM driver."""
from pathlib import Path
import copy
import json
import time

import numpy as np
import torch
import mujoco

from qlm_bench.compatibility.contracts_v2.validation import validate_record
from qlm_bench.contracts.episode import EpisodeRuntime
from qlm_bench.controllers.rambo.core import RAMBOCore
from qlm_bench.controllers.rambo.math import quat_apply, rp_rotation_from_gravity_b
from .physics import MuJoCoPhysics
from .tasks import TaskState


class MuJoCoRuntime:
    def __init__(self,model_path,checkpoint,*,backend='mjwarp',device='cuda:0',seed=42,
                 trace_only=False,profile_override=None,rgb_profile="dual-rgb-360p-v1",task_state_factory=None):
        from qlm_bench.tasks.prompts import current_instruction_profile
        self.profile=current_instruction_profile(json.loads(Path(model_path).with_suffix('.task.json').read_text()))
        if profile_override:
            if set(profile_override)-{'goal_x','goal_y','canonical_goal_position','horizon_s'}:
                raise ValueError('Only explicit episode goal/horizon overlay allowed')
            self.profile.update(copy.deepcopy(profile_override))
        self.physics=MuJoCoPhysics(model_path,backend=backend,device=device)
        self.core=RAMBOCore(self.physics,checkpoint,device=device,case_seeds=[seed])
        self.case_seed=seed;self._next_case_seed=seed
        self.rgb_profile=rgb_profile
        self.trace_only=bool(trace_only)
        self.renderer=None
        if not self.trace_only:
            from .render import RenderMirror
            self.renderer=RenderMirror(model_path,rgb_profile=rgb_profile)
        self.task=(task_state_factory or TaskState)(self.physics,self.profile)
        self.lifecycle=EpisodeRuntime()
        self.history=[];self.current=None;self.terminal=None;self.cached=None
        self.outcome=dict(success=False,fallen=False,timed_out=False)
        self.on_physics=None;self.on_control=None
        self.on_observation=None;self.on_terminal=None
        self.controller_reference_command_id=None;self.controller_reference_tick=0
        self.capture_index=0
        self.timing={k:0. for k in ('controller_s','physics_s','observation_s','mirror_refresh_s','render_readback_s','recorder_callback_s')}

    def set_case_seed(self,seed):
        if self.current is not None and self.terminal is None:raise ValueError('Cannot reseed an executing episode')
        self._next_case_seed=self.core.case_rng.validate_seed(seed)

    def reset(self,*,initial_state=None):
        self.physics.reset(initial_states=None if initial_state is None else {0:initial_state})
        self.core.reset(torch.tensor([0],device=self.core.device),case_seeds=[self._next_case_seed])
        self.case_seed=self._next_case_seed;self._next_case_seed+=1
        self.lifecycle.reset(0)
        if self.lifecycle.clock.reset_epoch!=self.physics.epochs[0]:raise RuntimeError('Lifecycle/backend epoch mismatch')
        self.task.reset()
        self.history=[];self.current=None;self.terminal=None;self.cached=None
        self.controller_reference_command_id=None;self.controller_reference_tick=0
        self.capture_index=0
        self.outcome=dict(success=False,fallen=False,timed_out=False,progress=self.task.progress(0))
        return self.state()

    def state(self):
        tick=int(self.physics.ticks[0]);epoch=int(self.physics.epochs[0])
        if self.cached is not None and (epoch,tick)==(self.cached['reset_epoch'],self.cached['physics_step']):
            return copy.deepcopy(self.cached)
        started=time.monotonic()
        self.core.refresh();robot=self.core.robot;snapshot=self.physics.snapshot()
        if self.trace_only:
            # Same numeric observation/refresh path as online, without GL or images.
            state=self.state_channels()
            self.cached=dict(simulation_time_ns=tick*2_000_000,reset_epoch=epoch,
                physics_step=tick,state=state,case_seed=self.case_seed,
                outcome=copy.deepcopy(self.outcome),executed_history=copy.deepcopy(self.history),
                backend_profile=self.profile['asset_profile'],physical_snapshot=snapshot)
            if self.on_observation is not None:self.on_observation(self.cached)
            self.timing['observation_s']+=time.monotonic()-started
            return copy.deepcopy(self.cached)
        before=(self.physics.ticks.copy(),self.physics.epochs.copy())
        capture=self.renderer.capture(snapshot,terminal=any(self.outcome.get(k,False) for k in ('success','fallen','timed_out')))
        self.timing['mirror_refresh_s']+=capture['timing_s']['mirror_refresh']
        self.timing['render_readback_s']+=capture['timing_s']['render_readback']
        if not np.array_equal(before[0],self.physics.ticks) or not np.array_equal(before[1],self.physics.epochs):
            raise RuntimeError('Sensor observation advanced physics')
        state=self.state_channels()
        rgb={'ego':capture['rgb']['go2_ego'],'task_centric':capture['rgb']['d435i_rgb_task']}
        import hashlib
        self.cached=dict(simulation_time_ns=tick*2_000_000,reset_epoch=epoch,physics_step=tick,state=state,rgb=rgb,
            case_seed=self.case_seed,
            observer_rgb=capture['observer_rgb'],rgb_spatial_profile=self.rgb_profile,
            rgb_hashes={k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in rgb.items()},
            sensor_frame_ids={k:self.capture_index for k in rgb},outcome=copy.deepcopy(self.outcome),
            executed_history=copy.deepcopy(self.history),backend_profile=self.profile['asset_profile'])
        self.capture_index+=1
        if self.on_observation is not None:self.on_observation(self.cached)
        self.timing['observation_s']+=time.monotonic()-started
        return copy.deepcopy(self.cached)

    def state_channels(self):
        self.core.refresh();robot=self.core.robot
        p,r,corners=self.task.geometry(0);object_q=self.physics.data[0].xquat[self.task.body][[1,2,3,0]]
        foot=(self.core.base_rot_mat_rp@self.core.ee_pos_b[:,0,:,None]).squeeze(-1)
        foot[:,2]+=self.core.base_height
        body_velocity=(self.core.all_foot_jacobian[:,:3]@self.core.joint_vel[:,:,None]).squeeze(-1)
        gravity=self.core.projected_gravity_b
        gravity1=gravity-1e-4*torch.linalg.cross(self.core.base_ang_vel_b,gravity,dim=-1)
        gravity1=gravity1/torch.linalg.vector_norm(gravity1,dim=-1,keepdim=True)
        rotation1=rp_rotation_from_gravity_b(gravity1).transpose(1,2)
        velocity=(self.core.base_rot_mat_rp@body_velocity[:,:,None]).squeeze(-1)+\
                 ((rotation1-self.core.base_rot_mat_rp)/1e-4@self.core.ee_pos_b[:,0,:,None]).squeeze(-1)
        velocity[:,2]+=robot.linear_velocity_world[:,2]
        d=self.physics.data[0];m=self.physics.model
        jp=np.zeros((3,m.nv));jr=np.zeros_like(jp)
        mujoco.mj_jacBody(m,d,jp,jr,self.task.body)
        object_v=jp@d.qvel;object_w=jr@d.qvel
        foot_forces=np.zeros((4,3))
        fl_object=False;body_object=False
        for index,contact in enumerate(d.contact[:d.ncon]):
            g1,g2=map(int,contact.geom)
            wrench=np.zeros(6);mujoco.mj_contactForce(m,d,index,wrench)
            world_force=contact.frame.reshape(3,3)[0]*wrench[0]
            for leg,foot_geom in enumerate(self.physics.foot_geom_ids):
                if foot_geom in (g1,g2):
                    foot_forces[leg]+=world_force if g2==foot_geom else -world_force
            b1,b2=int(m.geom_bodyid[g1]),int(m.geom_bodyid[g2])
            if self.task.body in (b1,b2):
                fl_object|=self.physics.foot_geom_ids[0] in (g1,g2)
                body_object|=self.physics.root_id in (b1,b2)
        state={'observation.state.base.position':robot.position[0].cpu().tolist(),
            'observation.state.base.orientation':robot.quaternion_xyzw[0].cpu().tolist(),
            'observation.state.base.linear_velocity':robot.linear_velocity_world[0].cpu().tolist(),
            'observation.state.base.angular_velocity':robot.angular_velocity_world[0].cpu().tolist(),
            'observation.state.projected_gravity':self.core.projected_gravity_b[0].cpu().tolist(),
            'observation.state.joint_position':robot.q[0].cpu().tolist(),
            'observation.state.joint_velocity':robot.qd[0].cpu().tolist(),
            'observation.state.fl_ee_position':foot[0].cpu().tolist(),
            'observation.state.fl_ee_velocity':velocity[0].cpu().tolist(),
            'observation.state.fl_contact_force':foot_forces[0].tolist(),
            'observation.state.foot_contact':(np.linalg.norm(foot_forces,axis=-1)>0).tolist(),
            'task.object.position':p.tolist(),'task.object.orientation':object_q.tolist(),
            'task.object.linear_velocity':object_v.tolist(),'task.object.angular_velocity':object_w.tolist(),
            'task.goal.position':self.profile.get('canonical_goal_position',[1.15,.15,0.] if self.task.task=='push_box' else [.75,.15,.02] if self.task.task=='lift_basket' else [.572,.1,.3]),
            'task.progress':[self.task.progress(0)],
            'task.success':[bool(self.outcome['success'])],
            'task.contact.fl_object':[bool(fl_object)],'task.contact.body_object':[bool(body_object)]}
        return state

    def step(self,prepared):
        if self.terminal is not None:raise ValueError('Terminal episode requires explicit reset')
        self.physics.assert_frozen_model()
        validate_record('command',prepared)
        tick=int(self.physics.ticks[0])
        if prepared['start_tick']!=tick or prepared['end_tick']!=tick+10 or prepared['status']!='not_executed':
            raise ValueError('Command identity/physical boundary mismatch')
        self.lifecycle.submit(prepared,tick)
        self.current=copy.deepcopy(self.lifecycle.current_command)
        self.core.submit([prepared['filtered']])
        for _ in range(2):
            started=time.monotonic()
            residual=self.core.begin_control()
            self.timing['controller_s']+=time.monotonic()-started
            if self.on_control is not None:
                started=time.monotonic();self.on_control(self,residual)
                self.timing['recorder_callback_s']+=time.monotonic()-started
            for _ in range(5):
                started=time.monotonic()
                efforts=self.core.motor_effort().cpu().numpy()
                self.timing['controller_s']+=time.monotonic()-started
                started=time.monotonic()
                self.physics.step(efforts)
                self.timing['physics_s']+=time.monotonic()-started
                if self.on_physics is not None:
                    started=time.monotonic();self.on_physics(self,efforts)
                    self.timing['recorder_callback_s']+=time.monotonic()-started
            started=time.monotonic()
            self.core.end_control(residual)
            self.timing['controller_s']+=time.monotonic()-started
            self.controller_reference_command_id=self.current['command_id']
            self.controller_reference_tick=int(self.physics.ticks[0])
            self.lifecycle.confirm_control(int(self.physics.ticks[0]))
            self.current=copy.deepcopy(self.lifecycle.current_command)
            if self.current['status']=='completed':
                self.history=self.lifecycle.history
                self.outcome=self.task.evaluate(0,self.core)
            else:
                g=self.core.projected_gravity_b[0].cpu().numpy()
                self.outcome['fallen']=bool(self.core.base_height[0]<.1 or np.linalg.norm(g-[0,0,-1])>.75)
            self.cached=None
            if self.outcome['success'] or self.outcome['fallen'] or self.outcome['timed_out']:
                reason='robot_fall' if self.outcome['fallen'] else 'task_success' if self.outcome['success'] else 'timeout'
                self.terminal=self.state();self.terminal.update(self.outcome,reason=reason,
                    partial_interval=self.current['status']=='partial',command_confirmation=copy.deepcopy(self.current))
                self.lifecycle.set_outcome(success=self.outcome['success'],fallen=self.outcome['fallen'],timed_out=self.outcome['timed_out'])
                self.lifecycle.seal_terminal(self.terminal)
                if self.on_terminal is not None:self.on_terminal(self.terminal)
                break
            if self.current['status']=='completed':
                self.state()  # Actual dualRGB50Hz; model consumes the80ms subset.
        return dict(command=copy.deepcopy(self.current),terminal=copy.deepcopy(self.terminal),
                    completed_interval=self.current['status']=='completed',
                    simulation_time_ns=int(self.physics.ticks[0])*2_000_000)

    def close(self):
        try:
            if self.renderer is not None:self.renderer.close()
        finally:self.physics.close()

    def abort(self,reason='explicit_abort'):
        if self.terminal is not None:return copy.deepcopy(self.terminal)
        before=self.physics.ticks.copy()
        snapshot=self.state()
        if self.renderer is not None and snapshot.get('observer_rgb') is None and self.renderer.observer_clip is not None:
            # An abort can occur between25Hz observer frames. Capture a separate
            # terminal image at the real boundary without changing policy frame
            # IDs, cadence or the already completed interval history.
            snapshot['observer_rgb']=self.renderer.capture(self.physics.snapshot(),terminal=True)['observer_rgb']
        snapshot.update(reason=reason,success=False,fallen=bool(self.outcome.get('fallen',False)),
                        timed_out=False,partial_interval=bool(self.current and self.current['status']=='partial'),
                        command_confirmation=copy.deepcopy(self.current))
        self.lifecycle.abort(snapshot,reason)
        if not np.array_equal(before,self.physics.ticks):raise RuntimeError('Abort advanced physics')
        self.terminal=copy.deepcopy(snapshot)
        if self.on_terminal is not None:self.on_terminal(self.terminal)
        return copy.deepcopy(self.terminal)

    def freeze_token(self):
        """Non-stepping local evidence of physics and controller stability."""
        import hashlib
        snapshot=self.physics.snapshot();h=hashlib.sha256()
        for key in ('qpos','qvel','act','mocap_pos','mocap_quat','eq_active'):h.update(snapshot[key].tobytes())
        h.update(np.asarray(snapshot['time'],dtype=np.float64).tobytes())
        controller=hashlib.sha256()
        for value in (self.core._obs_history,self.core._last_action,self.core._desired_joint_pos,
                      self.core.desired_pos,self.core.desired_vel,self.core.desired_tor,
                      self.core._velocity_commands,self.core._ee_pos_commands,self.core._ee_force_commands,
                      self.core.motor.history,self.core.motor.age,self.core.motor.lags):
            controller.update(value.cpu().numpy().tobytes())
        return {'physics_sha256':h.hexdigest(),'controller_sha256':controller.hexdigest(),
                'control_ticks':self.core.control_ticks.cpu().tolist(),'controller_time':self.core.time_since_reset.cpu().tolist(),
                'rng':self.core.case_rng.identity()['state_sha256']}
