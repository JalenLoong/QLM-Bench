"""Export original three-task runtime physics, rig and camera references, without actions."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


def main():
    from isaaclab.app import AppLauncher
    parser=argparse.ArgumentParser()
    for name in ('reference-source','resource-root','output','task'):
        parser.add_argument('--'+name,required=True)
    AppLauncher.add_app_launcher_args(parser);args=parser.parse_args()
    if args.task not in ('push_box','press_button','lift_basket'):
        raise ValueError('Only original three-task reference export is authorized here')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[2];ref=Path(args.reference_source).resolve()
    guard=load('original_task_source_guard',root/'scripts/rambo/compare_controller_isaac.py')
    source=guard.source_identity(ref)
    profile_path=ref/'configs/collection'/(args.task+'.json')
    attempt={'work_id':'QLM-SIM-005','kind':'original_task_runtime_reference_not_rollout',
             'args':vars(args),'original_source':source,'entry_sha256':guard.sha(__file__),
             'profile_sha256':guard.sha(profile_path),'started_unix':time.time(),
             'EULA':'user explicitly authorized all task EULAs; process scoped'}
    (out/'attempt.json').write_text(json.dumps(attempt,indent=2)+'\n')
    app=None;env=None;result={}
    try:
        args.enable_cameras=True
        app=AppLauncher(args)
        import numpy as np
        import torch
        import omni.usd
        from pxr import Usd,UsdGeom,UsdUtils,PhysicsSchemaTools
        from rambo.tasks.common.environment_factory import make_task_config,make_environment
        from qlm_bench.tasks.registration import load_registration
        from rambo.tasks.common.lift_camera_rig import RIG_PATH
        from rambo.utils.physx import assert_physx_environment
        from rambo.tasks.common.snapshots import capture_state,capture_rgb
        usd=load('original_task_usd_reference',root/'scripts/mujoco/usd_reference.py')
        torch.set_num_threads(1);torch.manual_seed(42)
        profile=json.loads(profile_path.read_text())
        task_id=load_registration(args.task,ready=True)['gym_id']
        cfg=make_task_config(task_id,profile=profile,resource_root=args.resource_root,seed=42,
                             episode_length_s=24.,device=args.device or 'cuda:0')
        env=make_environment(cfg,task_id=task_id);env.reset();base=env.unwrapped
        before=(int(base.episode_tick),int(base.sim._physics_step_count))
        import omni.replicator.core as rep
        observer_config=cfg.approved_profile['observer']
        observer=rep.create.camera(name='alignment_original_observer',position=observer_config['position'],
                                   look_at=observer_config['look_at'],focal_length=24)
        observer_product=rep.create.render_product(observer,(1280,720))
        observer_rgb=rep.AnnotatorRegistry.get_annotator('rgb',device='cpu');observer_rgb.attach(observer_product)
        parameter_annotators={}
        untiled_products={role:rep.create.render_product(str(sensor._sensor_prims[0].GetPath()),(1280,720))
                          for role,sensor in [('ego',base.front_camera),('task_centric',base.task_camera)]}
        for role,product in [('observer',observer_product),*untiled_products.items()]:
            annotator=rep.AnnotatorRegistry.get_annotator('CameraParams',device='cpu')
            annotator.attach(product);parameter_annotators[role]=annotator
        base.sim.forward()
        for _ in range(4):base.sim.render()
        rgb,hashes,frame_ids=capture_rgb(base)
        from PIL import Image
        for name,image in rgb.items():Image.fromarray(image).save(out/(name+'.png'))
        observer_image=np.asarray(observer_rgb.get_data())
        if observer_image.shape[:2]!=(720,1280) or observer_image.std()<1:
            raise ValueError('Original Observer RGB unavailable or uniform')
        Image.fromarray(observer_image[:,:,:3]).save(out/'observer.png')
        state=capture_state(base)
        stage=omni.usd.get_context().get_stage()
        task_root='/World/envs/env_0/LingBotTask'
        geometry=usd.inspect_stage(stage,task_root,out/'task_usd')
        # Read the original PhysX convex decomposition. No alternative cooker
        # or primitive replacement is used, and this request does not step time.
        from omni.physx import get_physx_cooking_interface
        from omni.physx.bindings._physx import PhysxCollisionRepresentationResult
        cooking=get_physx_cooking_interface();cooked_arrays={};cooked_records=[]
        for g in geometry['geometries']:
            if not g['collision_enabled'] or g['type']!='Mesh':continue
            received=[]
            def receive(status,hulls):
                if status!=PhysxCollisionRepresentationResult.RESULT_VALID:
                    raise ValueError('Original PhysX collision representation unavailable: '+str(status))
                for i,hull in enumerate(hulls):
                    key=g['id']+'_h'+str(i)
                    vertices=np.asarray([[v.x,v.y,v.z] for v in hull.vertices],dtype=np.float64)
                    counts=np.asarray([p.num_vertices for p in hull.polygons],dtype=np.int32)
                    indices=np.concatenate([np.asarray(hull.indices[p.index_base:p.index_base+p.num_vertices],dtype=np.int32) for p in hull.polygons])
                    if len(vertices)<4 or len(counts)<4 or not np.isfinite(vertices).all():
                        raise ValueError('Invalid original convex hull')
                    cooked_arrays[key+'_vertices']=vertices;cooked_arrays[key+'_counts']=counts;cooked_arrays[key+'_indices']=indices
                    received.append({'id':key,'vertices':key+'_vertices','face_counts':key+'_counts','face_indices':key+'_indices',
                                     'vertex_count':len(vertices),'polygon_count':len(counts)})
            cooking.request_convex_collision_representation(stage_id=UsdUtils.StageCache.Get().GetId(stage).ToLongInt(),
                collision_prim_id=PhysicsSchemaTools.sdfPathToInt(g['path']),run_asynchronously=False,on_result=receive)
            if not received:raise ValueError('No original convex collision returned: '+g['path'])
            cooked_records.append({'source_geometry':g['id'],'source_path':g['path'],'body':g['body'],
                                   'body_transform_row_major':g['body_transform_row_major'],
                                   'physics_material':g.get('physics_material'),'hulls':received})
        np.savez_compressed(out/'cooked_collision.npz',**cooked_arrays)
        (out/'cooked_collision.json').write_text(json.dumps({'schema':'qlm-original-physx-convex-v1',
            'method':'PhysX request_convex_collision_representation on original runtime stage',
            'coordinate_frame':'source collision mesh local coordinates before USD local-to-world transform',
            'shapes':cooked_records,'arrays_sha256':guard.sha(out/'cooked_collision.npz')},indent=2)+'\n')
        rig=usd.inspect_stage(stage,RIG_PATH,out/'camera_rig_usd')
        extras={}
        for prim in stage.GetPrimAtPath('/World').GetChildren():
            if prim.GetName().startswith(('ButtonMount','ButtonBracket','Goal_')):
                name=prim.GetName()
                usd.inspect_stage(stage,str(prim.GetPath()),out/('extra_'+name))
                extras[name]={'root':str(prim.GetPath()),'reference_sha256':guard.sha(out/('extra_'+name)/'reference.json')}
        cache=UsdGeom.XformCache()
        cameras=[]
        for prim in Usd.PrimRange(stage.GetPrimAtPath('/World/envs/env_0/Robot')):
            if prim.IsA(UsdGeom.Camera):
                cameras.append({'path':str(prim.GetPath()),'attributes':usd.attributes(prim),
                                'world_transform_row_major':np.asarray(cache.GetLocalToWorldTransform(prim)).tolist()})
        observer_prims=[prim for prim in stage.Traverse() if prim.IsA(UsdGeom.Camera) and 'alignment_original_observer' in prim.GetName()]
        if len(observer_prims)!=1:raise ValueError('Cannot uniquely resolve original Observer')
        observer_prim=observer_prims[0]
        observer_reference={'attributes':usd.attributes(observer_prim),
                            'world_transform_row_major':np.asarray(cache.GetLocalToWorldTransform(observer_prim)).tolist(),
                            'source_config':observer_config,'rgb_sha256':guard.sha(out/'observer.png')}
        renderer_camera_parameters={role:usd.value(annotator.get_data()) for role,annotator in parameter_annotators.items()}
        if any('cameraProjection' not in v or 'cameraViewTransform' not in v for v in renderer_camera_parameters.values()):
            raise ValueError('Actual RTX camera matrices unavailable')
        arrays={}
        view=base._primary.root_view
        for name,method in [('mass','get_masses'),('inertia','get_inertias'),('com','get_coms'),
                            ('pose','get_transforms'),('velocity','get_velocities'),
                            ('shape_material','get_material_properties'),('contact_offset','get_contact_offsets'),
                            ('rest_offset','get_rest_offsets')]:
            value=getattr(view,method)();arrays[name]=value.numpy() if hasattr(value,'numpy') else np.asarray(value)
        if hasattr(view,'get_compliant_material_properties'):
            compliant,combination=view.get_compliant_material_properties()
            arrays['compliant']=compliant.numpy();arrays['compliant_combination']=combination.numpy()
        np.savez_compressed(out/'task_physics.npz',**arrays)
        if before!=(int(base.episode_tick),int(base.sim._physics_step_count)):
            raise ValueError('Reference extraction advanced physics')
        result={'schema':'qlm-original-task-runtime-reference-v1','work_id':'QLM-SIM-005','status':'completed',
                'task':args.task,'original_source_commit':source['reference_commit'],'source_unchanged':guard.source_identity(ref)==source,
                'profile':cfg.approved_profile,'primary_position':list(cfg.primary_position),
                'primary_orientation':list(cfg.primary_orientation),'initial_state':state,
                'original_runtime_geometry':base.geometry_world() if hasattr(base,'geometry_world') else base.review_diagnostics(),
                'backend':assert_physx_environment(env),'policy_actions':0,'physics_steps_during_extraction':0,
                'geometry_count':len(geometry['geometries']),'rig_geometry_count':len(rig['geometries']),
                'cooked_convex_hulls':sum(len(g['hulls']) for g in cooked_records),
                'cooked_collision_sha256':guard.sha(out/'cooked_collision.json'),
                'cameras':cameras,'extras':extras,'actual_rgb_hashes':hashes,'frame_ids':frame_ids,
                'observer':observer_reference,
                'renderer_camera_parameters':renderer_camera_parameters,
                'camera_matrix_reference_method':'ordinary render products attached to the original mounted prims; sim.forward refreshes Fabric without stepping; original policy sensors retained',
                'physics_arrays_sha256':guard.sha(out/'task_physics.npz'),
                'task_usd_sha256':guard.sha(out/'task_usd/reference.json'),
                'rig_usd_sha256':guard.sha(out/'camera_rig_usd/reference.json'),
                'clock':list(before),'conversion_acceptance':False}
        # All physical/geometry scalars remain arrays/lists, not repr strings.
        result=usd.value(result)
    except BaseException as error:
        result={'status':'failed','error':repr(error),'traceback':traceback.format_exc()}
        print(result['traceback'],flush=True)
    finally:
        (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        if env is not None:env.close()
        if app is not None:app.app.close()
    if result['status']!='completed':raise SystemExit(1)
    print('Exported original task reference:',args.task,flush=True)


if __name__=='__main__':main()
