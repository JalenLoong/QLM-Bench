"""One authoritative physics state and explicit robot adapter for RAMBO."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import time
import json

import mujoco
import numpy as np
import torch

from qlm_bench.controllers.rambo.core import JOINT_ORDER, BODY_ORDER
from .resources import resource_closure, model_parameter_identity


class MuJoCoPhysics:
    def __init__(self, model_path, *, count=1, backend="native", device="cuda:0", cache_reads=True):
        if backend not in ("native","mjwarp") or count < 1:
            raise ValueError("Explicit native/mjwarp backend and positive world count required")
        self.model_path=Path(model_path)
        self.resource_profile=resource_closure(self.model_path)
        self.model=mujoco.MjModel.from_xml_path(str(self.model_path))
        self.model.vis.global_.offwidth=1280
        self.model.vis.global_.offheight=720
        if self.model.opt.timestep != .002:
            raise ValueError("Physics timestep must remain2ms")
        self.count,self.backend,self.device=count,backend,device
        self.cache_reads=bool(cache_reads);self._host_valid=False;self._read_cache={}
        profile_path=self.model_path.with_suffix('.task.json')
        task_profile=json.loads(profile_path.read_text()) if profile_path.exists() else {}
        self.capacity=task_profile.get('mjwarp_capacity',{'nconmax':128,'njmax':512})
        if any(type(self.capacity.get(k)) is not int or self.capacity[k]<=0 for k in ('nconmax','njmax')):
            raise ValueError('Explicit positive MJWarp contact/constraint capacities required')
        self.model_identity=self.resource_profile['identity']
        self.model_parameters_identity=model_parameter_identity(self.model)
        self.full_model_identity=model_parameter_identity(self.model,full=True)
        self.backend_options={'backend':backend,'device':str(device),'iterations':int(self.model.opt.iterations),
            'ls_iterations':int(self.model.opt.ls_iterations),'effective_tolerance':float(self.model.opt.tolerance),
            'model_tolerance':float(self.model.opt.tolerance),'precision':'float64' if backend=='native' else 'float32'}
        self.transfer_metrics={'synchronization_s':0.,'state_readback_s':0.,'calls':0}
        self.data=[mujoco.MjData(self.model) for _ in range(count)]
        self.ticks=np.zeros(count,dtype=np.int64)
        self.epochs=np.full(count,-1,dtype=np.int64)
        self.joint_ids=np.array([mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_JOINT,n) for n in JOINT_ORDER])
        self.body_ids=np.array([mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_BODY,n) for n in BODY_ORDER])
        if np.any(self.joint_ids<0) or np.any(self.body_ids<0):
            raise ValueError("Named RAMBO joint/body mapping is incomplete")
        self.qadr=self.model.jnt_qposadr[self.joint_ids]
        self.vadr=self.model.jnt_dofadr[self.joint_ids]
        actuator_joint=self.model.actuator_trnid[:,0]
        self.actuator_ids=np.array([np.flatnonzero(actuator_joint==j).item() for j in self.joint_ids])
        self.joint_limits=torch.tensor(self.model.jnt_range[self.joint_ids],dtype=torch.float32)[None].repeat(count,1,1)
        self.root_id=int(self.body_ids[0])
        self.foot_geom_ids=np.array([mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_GEOM,n) for n in ("FL","FR","RL","RR")])
        self.contact_history=np.zeros((count,3,4,3),dtype=np.float64)
        self.contact_history_tick=np.full(count,-1,dtype=np.int64)
        self.reset()

    def validate_initial_states(self,ids,states):
        """Validate every requested state before any lane is mutated."""
        if states is None:return {}
        if not isinstance(states,dict) or set(states)!=set(ids) or any(isinstance(i,(bool,np.bool_)) or not isinstance(i,(int,np.integer)) for i in states):
            raise ValueError('Initial states must cover exactly the selected world indices')
        result={}
        for index,spec in states.items():
            if not isinstance(spec,dict) or set(spec)!={'schema','model_identity','qpos','qvel'}:
                raise ValueError('Explicit complete initial-state schema required')
            if spec['schema']!='qlm-mujoco-initial-state-v1' or spec['model_identity']!=self.model_identity:
                raise ValueError('Initial-state resource identity/schema mismatch')
            qpos=np.asarray(spec['qpos'],dtype=np.float64);qvel=np.asarray(spec['qvel'],dtype=np.float64)
            if qpos.shape!=(self.model.nq,) or qvel.shape!=(self.model.nv,) or not np.isfinite(qpos).all() or not np.isfinite(qvel).all():
                raise ValueError('Initial-state arrays must be complete and finite')
            for joint in range(self.model.njnt):
                kind=self.model.jnt_type[joint];adr=int(self.model.jnt_qposadr[joint])
                if kind in (mujoco.mjtJoint.mjJNT_FREE,mujoco.mjtJoint.mjJNT_BALL):
                    offset=3 if kind==mujoco.mjtJoint.mjJNT_FREE else 0
                    if abs(np.linalg.norm(qpos[adr+offset:adr+offset+4])-1)>1e-6:
                        raise ValueError('Initial-state quaternion must already be normalized')
                elif self.model.jnt_limited[joint] and not self.model.jnt_range[joint,0]-1e-6<=qpos[adr]<=self.model.jnt_range[joint,1]+1e-6:
                    raise ValueError('Initial-state joint lies outside frozen limits')
            result[index]=(qpos.copy(),qvel.copy())
        return result

    def reset(self, ids=None, *,initial_states=None):
        ids=list(range(self.count)) if ids is None else list(ids)
        if any(isinstance(i,(bool,np.bool_)) or not isinstance(i,(int,np.integer)) or i<0 or i>=self.count for i in ids) or len(ids)!=len(set(ids)):
            raise ValueError('Reset requires unique valid world indices')
        prepared=self.validate_initial_states(ids,initial_states)
        if not ids:return
        self._host_valid=False;self._read_cache={}
        for index in ids:
            d=self.data[index]
            mujoco.mj_resetData(self.model,d)
            d.qpos[:7]=[0.,0.,.4,1.,0.,0.,0.]
            d.qpos[self.qadr]=[0.]*4+[.8]*4+[-1.5]*4
            d.qvel[:]=0
            if index in prepared:
                d.qpos[:],d.qvel[:]=prepared[index]
            d.ctrl[:]=0
            mujoco.mj_forward(self.model,d)
            self.ticks[index]=0;self.epochs[index]+=1
            self.contact_history[index]=0;self.contact_history_tick[index]=-1
        if self.backend=="mjwarp":
            import warp as wp
            import mujoco_warp as mjw
            with wp.ScopedDevice(self.device):
                if not hasattr(self,'warp_data'):
                    self.warp_model=mjw.put_model(self.model)
                    # The pinned ROCm fork otherwise silently caps this at10.
                    # Preserve the declared solver budget on both GPU backends.
                    self.warp_model.opt.ls_iterations=int(self.model.opt.ls_iterations)
                    if self.warp_model.opt.iterations!=self.model.opt.iterations:
                        raise RuntimeError('MJWarp changed the declared solver iteration budget')
                    gpu=wp.get_device(self.device)
                    tolerance=np.asarray(self.warp_model.opt.tolerance.numpy()).reshape(-1)
                    if tolerance.size!=1:raise RuntimeError('Unexpected per-world solver tolerance profile')
                    self.backend_options.update(ls_iterations=int(self.warp_model.opt.ls_iterations),
                        effective_tolerance=float(tolerance[0]),
                        graph_conditional=bool(self.warp_model.opt.graph_conditional),
                        device_name=gpu.name,is_hip=bool(getattr(gpu,'is_hip',False)),
                        note='MJWarp float32 tolerance floor is explicit; line-search budget is restored from model profile')
                    self.warp_data=mjw.make_data(self.model,nworld=self.count,**self.capacity)
                else:
                    mask=np.zeros(self.count,dtype=bool);mask[ids]=True
                    mjw.reset_data(self.warp_model,self.warp_data,
                                   reset=wp.array(mask,dtype=wp.bool,device=self.device))
                # Preserve unselected worlds. Only selected initial qpos/qvel and clock reset.
                qpos=self.warp_data.qpos.numpy();qvel=self.warp_data.qvel.numpy()
                for index in ids:
                    qpos[index]=self.data[index].qpos;qvel[index]=self.data[index].qvel
                wp.copy(self.warp_data.qpos,wp.array(qpos,dtype=wp.float32,device=self.device))
                wp.copy(self.warp_data.qvel,wp.array(qvel,dtype=wp.float32,device=self.device))
                times=self.warp_data.time.numpy()
                times[ids]=0
                wp.copy(self.warp_data.time,wp.array(times,dtype=wp.float32,device=self.device))
                mjw.forward(self.warp_model,self.warp_data)
            self.sync()

    def sync(self):
        if self.backend=="mjwarp":
            if self.cache_reads and self._host_valid:return
            import warp as wp
            import mujoco_warp as mjw
            started=time.monotonic()
            wp.synchronize_device(self.device)
            synchronized=time.monotonic()
            if self.warp_data.nacon.numpy()[0]>self.warp_data.naconmax or np.any(self.warp_data.nefc.numpy()>self.warp_data.njmax):
                raise RuntimeError("MJWarp contact/constraint capacity exceeded")
            for index,d in enumerate(self.data):
                mjw.get_data_into(d,self.model,self.warp_data,world_id=index)
                self._check_state(d,index)
            self.transfer_metrics['synchronization_s']+=synchronized-started
            self.transfer_metrics['state_readback_s']+=time.monotonic()-synchronized
            self.transfer_metrics['calls']+=1
            self._host_valid=True

    def step(self, efforts):
        self._host_valid=False;self._read_cache={}
        value=np.asarray(efforts,dtype=np.float32)
        if value.shape!=(self.count,12) or not np.isfinite(value).all():
            raise ValueError("Finite twelve motor efforts per world required")
        for index,d in enumerate(self.data):
            self._check_state(d,index)
            d.ctrl[self.actuator_ids]=value[index]
        if self.backend=="native":
            for index,d in enumerate(self.data):
                mujoco.mj_step(self.model,d)
                mujoco.mj_forward(self.model,d)  # Refresh at completed qpos/time; no integration.
                self._check_state(d,index)
        else:
            import warp as wp
            import mujoco_warp as mjw
            with wp.ScopedDevice(self.device):
                wp.copy(self.warp_data.ctrl,wp.array(np.stack([d.ctrl for d in self.data]),dtype=wp.float32,device=self.device))
                mjw.step(self.warp_model,self.warp_data)
                mjw.forward(self.warp_model,self.warp_data)
            self.sync()
        self.ticks+=1

    @staticmethod
    def _check_state(data,index):
        for field in ('qpos','qvel','qacc','act','ctrl'):
            if not np.isfinite(getattr(data,field)).all():
                raise FloatingPointError(f'Nonfinite {field} in world{index}; no automatic recovery is accepted')
        if not np.isfinite(data.time):raise FloatingPointError(f'Nonfinite physical time in world{index}')
        for warning in (mujoco.mjtWarning.mjWARN_BADQPOS,mujoco.mjtWarning.mjWARN_BADQVEL,
                        mujoco.mjtWarning.mjWARN_BADQACC,mujoco.mjtWarning.mjWARN_BADCTRL):
            if data.warning[int(warning)].number:
                raise FloatingPointError(f'Physics instability warning{int(warning)} in world{index}; attempt must fail closed')

    def read(self, device="cpu"):
        self.sync()
        # Include actual host state to preserve Native diagnostic state edits;
        # GPU state can only be changed through this owner's step/reset methods.
        h=hashlib.sha256(self.ticks.tobytes()+self.epochs.tobytes())
        for d in self.data:
            for key in ('qpos','qvel','ctrl','qfrc_applied','efc_force'):h.update(getattr(d,key).tobytes())
        key=(str(device),h.digest())
        if self.cache_reads and key in self._read_cache:
            return SimpleNamespace(**{k:v.clone() for k,v in self._read_cache[key].items()})
        values={k:[] for k in ('q','qd','position','quaternion_xyzw','linear_velocity_world','angular_velocity_world','foot_contacts','gravity_torque')}
        for index,d in enumerate(self.data):
            jp=np.zeros((3,self.model.nv));jr=np.zeros_like(jp)
            mujoco.mj_jacBody(self.model,d,jp,jr,self.root_id)
            values['q'].append(d.qpos[self.qadr]);values['qd'].append(d.qvel[self.vadr])
            values['position'].append(d.xpos[self.root_id]);q=d.xquat[self.root_id]
            values['quaternion_xyzw'].append(q[[1,2,3,0]])
            values['linear_velocity_world'].append(jp@d.qvel);values['angular_velocity_world'].append(jr@d.qvel)
            forces=np.zeros((4,3))
            for cid,c in enumerate(d.contact[:d.ncon]):
                wrench=np.zeros(6);mujoco.mj_contactForce(self.model,d,cid,wrench)
                normal=c.frame.reshape(3,3)[0]*wrench[0]
                for foot,geom in enumerate(self.foot_geom_ids):
                    if geom==c.geom[0]:forces[foot]-=normal
                    elif geom==c.geom[1]:forces[foot]+=normal
            # Retained controller consumes three fresh normal-force samples at
            # controller boundaries; repeated reads may not shift sensor history.
            if self.ticks[index]%5==0 and self.contact_history_tick[index]!=self.ticks[index]:
                self.contact_history[index,:2]=self.contact_history[index,1:].copy()
                self.contact_history[index,2]=forces
                self.contact_history_tick[index]=self.ticks[index]
            contacts=np.any(np.linalg.norm(self.contact_history[index],axis=-1)>0,axis=0)
            values['foot_contacts'].append(contacts)
            gravity=np.zeros(12)
            for body in self.body_ids[1:]:
                mujoco.mj_jacBodyCom(self.model,d,jp,jr,int(body))
                gravity+=jp[:,self.vadr].T@np.array([0.,0.,9.81*self.model.body_mass[body]])
            values['gravity_torque'].append(gravity)
        result={k:torch.tensor(np.stack(v),device=device,dtype=torch.bool if k=='foot_contacts' else torch.float32)
                for k,v in values.items()}
        if self.cache_reads:self._read_cache={key:result}
        return SimpleNamespace(**{k:v.clone() for k,v in result.items()})

    def snapshot(self,index=0):
        if isinstance(index,(bool,np.bool_)) or not isinstance(index,(int,np.integer)) or not 0<=index<self.count:
            raise ValueError('Snapshot requires a valid world index')
        self.assert_frozen_model()
        self.sync();d=self.data[index]
        return dict(model_identity=self.model_identity,world_id=index,reset_epoch=int(self.epochs[index]),
            model_parameters_identity=self.model_parameters_identity,
            physics_step=int(self.ticks[index]),simulation_time_ns=int(self.ticks[index])*2_000_000,
            qpos=d.qpos.copy(),qvel=d.qvel.copy(),mocap_pos=d.mocap_pos.copy(),mocap_quat=d.mocap_quat.copy(),
            act=d.act.copy(),eq_active=d.eq_active.copy(),time=float(d.time))

    def assert_frozen_model(self,*,full=False):
        expected=self.full_model_identity if full else self.model_parameters_identity
        if model_parameter_identity(self.model,full=full)!=expected:
            raise RuntimeError('Physics model parameters changed outside the frozen profile; create a new explicit runtime')

    def close(self):
        self.assert_frozen_model(full=True)
