"""Actual same-state camera/physics and OSMesa RGB before/after rig comparison."""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial.transform import Rotation

from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.render import RenderMirror

TASKS=('push_box','press_button','lift_basket')
MOUNT_FROM_GL=np.array([[0,0,1],[-1,0,0],[0,-1,0]])@np.diag([1.,-1.,-1.])


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def camera_state(model,data):
    c=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_CAMERA,'d435i_rgb_task')
    local_gl=Rotation.from_quat(model.cam_quat[c][[1,2,3,0]]).as_matrix()
    local_mount=local_gl@MOUNT_FROM_GL.T
    world_mount=data.cam_xmat[c].reshape(3,3)@MOUNT_FROM_GL.T
    vfov=float(model.cam_fovy[c]);hfov=float(np.degrees(2*np.arctan(np.tan(np.radians(vfov/2))*1280/720)))
    focal=float(360/np.tan(np.radians(vfov/2)))
    return {'mount_position_base_m':model.cam_pos[c].tolist(),
            'mount_quaternion_base_xyzw':Rotation.from_matrix(local_mount).as_quat().tolist(),
            'mount_rotation_base_matrix':local_mount.tolist(),
            'position_world_m':data.cam_xpos[c].tolist(),
            'mount_quaternion_world_xyzw':Rotation.from_matrix(world_mount).as_quat().tolist(),
            'world_rotation_matrix':world_mount.tolist(),
            'camera_rotation_GL_world_matrix':data.cam_xmat[c].reshape(3,3).tolist(),
            'vertical_fov_deg':vfov,'horizontal_fov_deg':hfov,
            'RGB_size':[1280,720],'intrinsics_pixels':[[focal,0.,640.],[0.,focal,360.],[0.,0.,1.]],
            'clipping_m':[float(model.vis.map.znear*model.stat.extent),float(model.vis.map.zfar*model.stat.extent)]}


def invariants(a,b):
    rig=np.array([i for i in range(a.ngeom) if (mujoco.mj_id2name(a,mujoco.mjtObj.mjOBJ_GEOM,i) or '').startswith('original_camera_rig_')])
    nonrig=np.array([i for i in range(a.ngeom) if i not in rig])
    checked=[]; visual_diffs={}; derived_diffs={}
    for name in sorted(dir(a)):
        if name.startswith('_'):continue
        x=getattr(a,name);y=getattr(b,name)
        if not isinstance(x,np.ndarray):continue
        if x.shape!=y.shape:raise ValueError('Model shape changed: '+name)
        if name.startswith('geom_') and x.shape and x.shape[0]==a.ngeom:
            np.testing.assert_array_equal(x[nonrig],y[nonrig],err_msg='Non-rig geometry changed: '+name)
            if not np.array_equal(x,y):
                if name not in ('geom_pos','geom_quat','geom_size','geom_rgba','geom_aabb','geom_rbound'):
                    raise ValueError('Unexpected rig physics/identity change: '+name)
                visual_diffs[name]=float(np.max(np.abs(x.astype(float)-y.astype(float))))
            checked.append(name)
        elif name=='dof_length':
            # Compiler geometry-size normalization reflects source double vs
            # exported USD float32 rig bounds; actual mass/inertia stays exact.
            np.testing.assert_allclose(x,y,atol=3e-9,rtol=0,err_msg='Geometry normalization drift')
            derived_diffs[name]=float(np.max(np.abs(x-y)));checked.append(name)
        elif name.startswith(('body_','jnt_','dof_','actuator_','eq_','tendon_','pair_','exclude_','cam_','light_','mat_','mesh_','tex_')) or name in ('qpos0','qpos_spring'):
            np.testing.assert_array_equal(x,y,err_msg='Physics/camera/resource changed: '+name)
            checked.append(name)
    if a.opt.timestep!=b.opt.timestep or a.stat.extent!=b.stat.extent:raise ValueError('Timing/extent changed')
    if not all(a.geom_contype[i]==b.geom_contype[i]==0 and a.geom_conaffinity[i]==b.geom_conaffinity[i]==0 for i in rig):
        raise ValueError('Camera rig acquired collision')
    derived_diffs['stat.meansize']=float(abs(a.stat.meansize-b.stat.meansize))
    return {'passed':True,'arrays_checked':len(checked),'checked':checked,'visual_array_max_differences':visual_diffs,
            'compiler_geometry_normalization_differences':derived_diffs,
            'robot_mass_before_kg':float(a.body_subtreemass[mujoco.mj_name2id(a,mujoco.mjtObj.mjOBJ_BODY,'base')]),
            'robot_mass_after_kg':float(b.body_subtreemass[mujoco.mj_name2id(b,mujoco.mjtObj.mjOBJ_BODY,'base')]),
            'rig_mass_modeled':False,'rig_collision':False,'non_rig_geometries_identical':True}


def main():
    p=argparse.ArgumentParser();p.add_argument('--model-root',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=False);reports={}
    for task in TASKS:
        current=out/task;current.mkdir()
        paths=[Path(args.model_root)/f'original-{task}-v1-{suffix}/scene.xml' for suffix in ('a03','ethan-rig-a01')]
        owners=[MuJoCoPhysics(path) for path in paths]
        mirrors=[]
        try:
            mirrors=[RenderMirror(path) for path in paths]
            physics_check=invariants(owners[0].model,owners[1].model)
            states=[]
            for name in ('reset','translated_yaw_roll_pitch'):
                for owner in owners:
                    owner.reset()
                    if name!='reset':
                        d=owner.data[0];d.qpos[:3]=[.25,-.1,.45]
                        q=Rotation.from_euler('xyz',[8.,-5.,30.],degrees=True).as_quat()
                        d.qpos[3:7]=q[[3,0,1,2]]
                        d.qpos[owner.qadr[0]]=.12
                        mujoco.mj_forward(owner.model,d)
                    owner._host_valid=False;owner._read_cache={}
                np.testing.assert_array_equal(owners[0].data[0].qpos,owners[1].data[0].qpos)
                measured=[];images=[];rgb_metrics={}
                for label,owner,mirror in zip(('before','after'),owners,mirrors):
                    clock=owner.data[0].time;qpos=owner.data[0].qpos.copy()
                    capture=mirror.capture(owner.snapshot(),terminal=True)
                    if owner.data[0].time!=clock or not np.array_equal(owner.data[0].qpos,qpos):raise ValueError('Render advanced physics')
                    measured.append(camera_state(owner.model,owner.data[0]));images.append(capture)
                    for view,rgb in [*capture['rgb'].items(),('observer',capture['observer_rgb'])]:
                        Image.fromarray(rgb).save(current/(name+'-'+label+'-'+view+'.png'))
                old,new=measured
                position_diff=float(np.linalg.norm(np.asarray(old['position_world_m'])-new['position_world_m']))
                rot=Rotation.from_matrix(np.asarray(old['world_rotation_matrix']).T@new['world_rotation_matrix'])
                angle_diff=float(np.degrees(rot.magnitude()))
                fov_diff=max(abs(old[k]-new[k]) for k in ('vertical_fov_deg','horizontal_fov_deg'))
                if position_diff>1e-12 or angle_diff>1e-10 or fov_diff>1e-12:raise ValueError('Frozen camera contract changed')
                for view in ('go2_ego','d435i_rgb_task','observer'):
                    a=images[0]['observer_rgb'] if view=='observer' else images[0]['rgb'][view]
                    b=images[1]['observer_rgb'] if view=='observer' else images[1]['rgb'][view]
                    delta=np.abs(a.astype(np.int16)-b.astype(np.int16))
                    rgb_metrics[view]={'MAE_255':float(delta.mean()),'max_abs_255':int(delta.max()),
                                       'changed_pixels_fraction':float(np.any(delta!=0,axis=2).mean()),
                                       'before_std':float(a.std()),'after_std':float(b.std())}
                    if a.std()<1 or b.std()<1:raise ValueError('Invalid scene RGB')
                    if float(delta.mean())>.05:raise ValueError('Unexpected visual/occlusion difference')
                canvas=Image.new('RGB',(960,425),(20,24,30));draw=ImageDraw.Draw(canvas)
                draw.text((8,5),task+' / '+name+' / BEFORE above, ETHAN rig below',fill='white')
                for col,view in enumerate(('go2_ego','d435i_rgb_task','observer')):
                    draw.text((col*320+8,24),view,fill='white')
                    for row,label in enumerate(('before','after')):
                        im=Image.open(current/(name+'-'+label+'-'+view+'.png')).resize((320,180))
                        canvas.paste(im,(col*320,45+row*190))
                canvas.save(current/(name+'-comparison.png'))
                states.append({'fixture':name,'before':old,'after':new,'world_position_delta_m':position_diff,
                               'world_rotation_delta_deg':angle_diff,'FoV_delta_deg':fov_diff,'RGB':rgb_metrics,
                               'physics_advanced':False,'completed_physics_ticks':[int(o.ticks[0]) for o in owners]})
            reports[task]={'passed':True,'before_model':str(paths[0]),'after_model':str(paths[1]),
                           'physics_and_nonrig_invariants':physics_check,'states':states,'GL':mirrors[0].gl_identity}
            (current/'result.json').write_text(json.dumps(reports[task],indent=2)+'\n')
            print(task,'camera/physics/RGB comparison passed',flush=True)
        finally:
            for mirror in mirrors:mirror.close()
            for owner in owners:owner.close()
    result={'passed':True,'work_id':'QLM-SIM-006','kind':'same-state-render-fixture-not-rollout',
            'tasks':reports,'script_sha256':sha(__file__),
            'scope':'Native OSMesa actual RGB; same compiled MJCF is consumed by CUDA-MJWarp, no GPU/AMD rollout run'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    cards=[]
    for task in TASKS:
        for fixture in ('reset','translated_yaw_roll_pitch'):
            cards.append(f'<h2>{task} — {fixture}</h2><img src="{task}/{fixture}-comparison.png" width="960">')
    (out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Ethan camera rig comparison</title>'
        '<style>body{background:#15191f;color:#eee;font:16px sans-serif;max-width:1000px;margin:24px auto}img{max-width:100%}h2{font-size:19px}</style>'
        '<h1>Camera rig: before / collaborator definition</h1><p>Actual OSMesa RGB at identical physics states. Each panel: original above, collaborator-source rig below. No physics steps.</p>'+'\n'.join(cards))


if __name__=='__main__':main()
