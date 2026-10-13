"""Actual Native rendering at original Isaac state and RTX matrix comparison.

This imports a fixed reference state for camera/asset QA. It is not a physical
rollout, a demonstration, or an image reconstructed as evidence of old inference.
"""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation

from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.render import RenderMirror
from qlm_bench.backends.mujoco.tasks import TaskState


def main():
    parser=argparse.ArgumentParser()
    for name in ('model','reference','output'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--reference-frame',choices=('reset','step1','step2'))
    args=parser.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    ref=json.loads(Path(args.reference).read_text());profile=json.loads(Path(args.model).with_suffix('.task.json').read_text())
    if args.reference_frame:
        row=next(r for r in ref['rows'] if r['label']==args.reference_frame)
        ref={'initial_state':row['state'],'renderer_camera_parameters':{**profile['renderer_camera_parameters'],**row['matrices']},
             'simulation_time_ns':row['simulation_time_ns']}
    physics=MuJoCoPhysics(args.model);m=physics.model;d=physics.data[0]
    state=ref['initial_state'];d.qpos[:3]=state['observation.state.base.position']
    d.qpos[3:7]=Rotation.from_quat(state['observation.state.base.orientation']).as_quat()[[3,0,1,2]]
    d.qpos[physics.qadr]=state['observation.state.joint_position']
    if profile['task_id']!='press_button':
        address=m.joint('object_free').qposadr[0]
        d.qpos[address:address+3]=state['task.object.position']
        d.qpos[address+3:address+7]=Rotation.from_quat(state['task.object.orientation']).as_quat()[[3,0,1,2]]
    tick=ref.get('simulation_time_ns',0)//2_000_000;physics.ticks[0]=tick;d.time=tick*.002
    d.qvel[:]=0;mujoco.mj_forward(m,d)
    mirror=RenderMirror(args.model);result={}
    try:
        frame=mirror.capture(physics.snapshot(),terminal=True)
        image_map={'ego':frame['rgb']['go2_ego'],'task_centric':frame['rgb']['d435i_rgb_task'],'observer':frame['observer_rgb']}
        for name,image in image_map.items():
            if image is None or image.shape!=(720,1280,3) or image.std()<1:raise ValueError('Missing/uniform actual RGB '+name)
            Image.fromarray(image).save(out/(name+'.png'))
        matrices={}
        points=np.concatenate([d.xpos[physics.body_ids],TaskState(physics,profile).geometry(0)[2]])
        for role,name in [('ego','go2_ego'),('task_centric','d435i_rgb_task'),('observer','observer')]:
            camera=m.camera(name);cid=camera.id
            expected=ref['renderer_camera_parameters'][role]
            source_view=np.asarray(expected['cameraViewTransform']).reshape(4,4).T
            source_projection=np.asarray(expected['cameraProjection']).reshape(4,4).T
            world=np.eye(4);world[:3,:3]=d.cam_xmat[cid].reshape(3,3);world[:3,3]=d.cam_xpos[cid]
            actual_view=np.linalg.inv(world)
            mirror.update_scene(name);gl=mirror.renderer.scene.camera[0]
            fy=720*gl.frustum_near/(gl.frustum_top-gl.frustum_bottom);fx=fy
            expected_focal=np.array([1280*source_projection[0,0]/2,720*source_projection[1,1]/2])
            error=float(np.max(np.abs(np.array([fx,fy])-expected_focal)))
            pose_error=float(np.max(np.abs(actual_view-source_view)))
            local=np.c_[points,np.ones(len(points))]@actual_view.T
            visible=local[:,2]<-.1
            projected=np.c_[640+fx*local[visible,0]/(-local[visible,2]),360-fy*local[visible,1]/(-local[visible,2])]
            clip=np.c_[points[visible],np.ones(visible.sum())]@source_view.T@source_projection.T
            uv=(clip[:,:2]/clip[:,3:4]+1)*[640,360];uv[:,1]=720-uv[:,1]
            pixel_error=float(np.max(np.abs(projected-uv))) if len(uv) else 0.
            # Actual RTX float geometry and MuJoCo float GL frustum, not inferred
            # equality from two copies of the same nominal config.
            passed=error<.001 and pose_error<2e-5 and pixel_error<.05
            matrices[role]={'passed':passed,'focal_error_px':error,'view_matrix_error':pose_error,
                            'projected_point_max_error_px':pixel_error,'points_in_front':int(visible.sum()),
                            'near_m':float(gl.frustum_near),'far_m':float(gl.frustum_far),
                            'expected_focal_px':expected_focal.tolist(),'actual_focal_px':[fx,fy],
                            'mujoco_world_matrix':world.tolist(),'Isaac_view_matrix':source_view.tolist()}
        result={'work_id':'QLM-SIM-005','kind':'fixed_original_state_render_and_camera_QA','passed':all(v['passed'] for v in matrices.values()),
                'cameras':matrices,'GL':mirror.gl_identity,'profile_identity':physics.resource_profile,
                'source_reference_sha256':hashlib.sha256(Path(args.reference).read_bytes()).hexdigest(),
                'reference_frame':args.reference_frame,'source_simulation_time_ns':ref.get('simulation_time_ns',0),
                'RGB_sha256':{k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in image_map.items()},
                'physics_steps':0,'task_success_claimed':False,'pixel_photometry_equivalence_claimed':False}
    finally:
        mirror.close();physics.close()
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed']:raise ValueError('Original runtime camera comparison failed')
    print('Passed original-state camera QA',profile['task_id'],flush=True)


if __name__=='__main__':main()
