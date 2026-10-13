"""Native rendering mirror, synchronized to one completed authoritative state."""
from pathlib import Path
import hashlib
import os
import time
import json

import mujoco
import numpy as np
from .resources import resource_closure, model_parameter_identity


class RenderMirror:
    def __init__(self,model_path,*,world_id=0,width=1280,height=720):
        if (width,height)!=(1280,720):
            raise ValueError("Accepted source cameras remain1280x720")
        if os.environ.get('MUJOCO_GL') not in ('egl','osmesa'):
            raise ValueError("Select EGL/OSMesa explicitly before importing MuJoCo")
        self.resource_profile=resource_closure(model_path)
        self.identity=self.resource_profile['identity']
        self.world_id=world_id
        self.model=mujoco.MjModel.from_xml_path(str(model_path))
        self.data=mujoco.MjData(self.model)
        self.model.vis.global_.offwidth=width
        self.model.vis.global_.offheight=height
        self.model_parameters_identity=model_parameter_identity(self.model)
        self.full_model_identity=model_parameter_identity(self.model,full=True)
        self.renderer=mujoco.Renderer(self.model,height=height,width=width)
        from OpenGL import GL
        self.gl_identity={name:GL.glGetString(value).decode() for name,value in
                          (('vendor',GL.GL_VENDOR),('renderer',GL.GL_RENDERER),('version',GL.GL_VERSION))}
        self.audit_renderer=None
        self.last=None
        self.observer_clip=None
        if mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_CAMERA,'observer')>=0:
            profile=json.loads(Path(model_path).with_suffix('.task.json').read_text())
            self.observer_clip=profile['observer']['clipping_m']
            if not 0<self.observer_clip[0]<self.observer_clip[1]:raise ValueError('Invalid original Observer clipping')

    def capture(self,snapshot,*,terminal=False):
        start=time.monotonic()
        if snapshot['model_identity']!=self.identity or snapshot['world_id']!=self.world_id:
            raise ValueError("Render snapshot model/world identity mismatch")
        if snapshot.get('model_parameters_identity')!=self.model_parameters_identity or model_parameter_identity(self.model)!=self.model_parameters_identity:
            raise ValueError('Physics/render model parameters differ or changed outside the frozen profile')
        epoch,tick= snapshot['reset_epoch'],snapshot['physics_step']
        if type(epoch) is not int or type(tick) is not int or epoch<0 or tick<0:
            raise ValueError('Nonnegative integer reset/tick identity required')
        if not np.isfinite(snapshot['time']):raise ValueError('Nonfinite physical time')
        if snapshot['simulation_time_ns']!=tick*2_000_000:
            raise ValueError("Render snapshot clock mismatch")
        if self.last is not None and (epoch<self.last[0] or epoch==self.last[0] and tick<self.last[1]):
            raise ValueError("Stale render snapshot")
        if self.last is not None and epoch==self.last[0] and tick==self.last[1]:
            # Exact duplicate capture may repeat, conflicting contents may not.
            if self.last[2]!=self.fingerprint(snapshot):
                raise ValueError("Conflicting snapshot at same physical boundary")
        if self.last is not None and epoch>self.last[0]:
            # Reset mirror-local derived/cache state as well as the explicitly
            # copied snapshot. This never touches or steps the physics owner.
            mujoco.mj_resetData(self.model,self.data)
        for key in ('qpos','qvel','mocap_pos','mocap_quat','act','eq_active'):
            value=np.asarray(snapshot[key]);target=getattr(self.data,key)
            if value.shape!=target.shape or not np.isfinite(value).all():
                raise ValueError("Incomplete mirror state: "+key)
            target[:]=value
        self.data.time=snapshot['time']
        before=float(self.data.time)
        mujoco.mj_forward(self.model,self.data)
        transferred=time.monotonic()
        rgb={}
        for name in ('go2_ego','d435i_rgb_task'):
            self.update_scene(name)
            rgb[name]=self.renderer.render().copy()
        observer=None
        if self.observer_clip is not None and (tick%20==0 or terminal):
            self.update_scene('observer')
            observer=self.renderer.render().copy()
        if self.data.time!=before or not np.array_equal(self.data.qpos,snapshot['qpos']):
            raise RuntimeError("Rendering advanced physical state")
        self.last=(epoch,tick,self.fingerprint(snapshot))
        return {'rgb':rgb,'observer_rgb':observer,'simulation_time_ns':snapshot['simulation_time_ns'],'reset_epoch':epoch,
                'world_id':self.world_id,'model_identity':self.identity,
                'timing_s':{'mirror_refresh':transferred-start,'render_readback':time.monotonic()-transferred},
                'GL':self.gl_identity,'model_parameters_identity':self.model_parameters_identity,
                'mirror_physics_advanced':False,'render_backend':os.environ['MUJOCO_GL']}

    def update_scene(self,name):
        self.renderer.update_scene(self.data,camera=name)
        if name=='observer':
            if self.observer_clip is None:raise ValueError('No original Observer profile')
            # Change GL frustum only; frozen MjModel remains identical to physics.
            for camera in self.renderer.scene.camera:
                ratio=self.observer_clip[0]/camera.frustum_near
                for field in ('frustum_bottom','frustum_top','frustum_center','frustum_width'):
                    setattr(camera,field,getattr(camera,field)*ratio)
                camera.frustum_near,camera.frustum_far=self.observer_clip

    @staticmethod
    def fingerprint(snapshot):
        h=hashlib.sha256()
        h.update(np.asarray(snapshot['time'],dtype=np.float64).tobytes())
        for name in ('qpos','qvel','mocap_pos','mocap_quat','act','eq_active'):
            h.update(np.asarray(snapshot[name]).tobytes())
        return h.hexdigest()

    def close(self):
        try:
            if model_parameter_identity(self.model,full=True)!=self.full_model_identity:
                raise RuntimeError('Rendering mesh/texture/model changed outside the frozen resource profile')
        finally:
            self.renderer.close()
            if self.audit_renderer is not None:self.audit_renderer.close()

    def geometry_masks(self):
        """Audit-only segmentation; never a policy input or a physics update."""
        if self.last is None:raise ValueError('Capture an actual snapshot before geometry audit')
        result={}
        if self.audit_renderer is None:
            # Multisample color-ID interpolation creates spurious object IDs at
            # silhouettes. Disable MSAA only in the separate audit context.
            samples=self.model.vis.quality.offsamples
            self.model.vis.quality.offsamples=0
            try:self.audit_renderer=mujoco.Renderer(self.model,height=720,width=1280)
            finally:self.model.vis.quality.offsamples=samples
        self.audit_renderer.enable_segmentation_rendering()
        try:
            for name in ('go2_ego','d435i_rgb_task'):
                self.audit_renderer.update_scene(self.data,camera=name)
                result[name]=self.audit_renderer.render().copy()
        finally:self.audit_renderer.disable_segmentation_rendering()
        return result
