"""Read the actual original Isaac robot into an immutable alignment dossier."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
import time
import traceback


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


def main():
    from isaaclab.app import AppLauncher
    p=argparse.ArgumentParser();p.add_argument('--reference-source',required=True);p.add_argument('--output',required=True)
    AppLauncher.add_app_launcher_args(p);args=p.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[2];ref=Path(args.reference_source)
    compare=load('alignment_original_source_guard',root/'scripts/rambo/compare_controller_isaac.py')
    source=compare.source_identity(ref)
    (out/'attempt.json').write_text(json.dumps({'work_id':'QLM-SIM-005','kind':'original_Isaac_reference_export',
        'args':vars(args),'source':source,'entry_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'started_unix':time.time(),'eula':'user explicitly authorized task EULAs; process scoped'},indent=2)+'\n')
    helper=load('alignment_original_smoke',ref/'scripts/rambo/physx_quadruped_policy_smoke.py')
    app=None;env=None;result={}
    try:
        app=AppLauncher(args);runtime=helper._runtime_imports()
        import numpy as np
        import omni.usd
        from pxr import Usd,UsdPhysics
        usd=load('alignment_usd_reference',root/'scripts/mujoco/usd_reference.py')
        cfg=runtime['parse_env_cfg'](helper.TASK,device=args.device or 'cuda:0',num_envs=1,use_fabric=True)
        runtime['configure_physx'](cfg);helper._configure_deterministic_smoke(cfg,42,1)
        cfg.qp_torque_optimizer_config['qp_debug_vis']=False
        env=runtime['Crl2VecEnvWrapper'](runtime['gym'].make(helper.TASK,cfg=cfg))
        helper._seed_everything(42,env,runtime['torch']);env.reset();base=env.unwrapped
        data=base._robot.data
        def tensor(v):return v.torch if hasattr(v,'torch') else v
        required=('body_mass','body_inertia','body_com_pose_b','body_link_pose_w','joint_pos','joint_vel',
                  'joint_armature','joint_stiffness','joint_damping','joint_friction_coeff',
                  'joint_dynamic_friction_coeff','joint_viscous_friction_coeff','joint_pos_limits',
                  'joint_vel_limits','joint_effort_limits','default_joint_pos','default_joint_vel')
        arrays={name:tensor(getattr(data,name)).detach().cpu().numpy() for name in required}
        view=base._robot.root_view
        for name,method in (('shape_material_properties','get_material_properties'),
                            ('shape_contact_offsets','get_contact_offsets'),('shape_rest_offsets','get_rest_offsets')):
            raw=getattr(view,method)()
            arrays[name]=raw.numpy() if hasattr(raw,'numpy') else np.asarray(raw)
        compliant,combination=view.get_compliant_material_properties()
        arrays['shape_compliant_material_properties']=compliant.numpy()
        arrays['shape_compliant_material_combination']=combination.numpy()
        np.savez_compressed(out/'robot_physics.npz',**arrays)
        stage=omni.usd.get_context().get_stage();robot_path='/World/envs/env_0/Robot'
        robot=stage.GetPrimAtPath(robot_path)
        paths={}
        for prim in Usd.PrimRange(robot,Usd.TraverseInstanceProxies()):
            if prim.HasAPI(UsdPhysics.RigidBodyAPI) and prim.GetName() in data.body_names:
                if prim.GetName() in paths:raise ValueError('Ambiguous rigid body '+prim.GetName())
                paths[prim.GetName()]=str(prim.GetPath())
        if set(paths)!=set(data.body_names):raise ValueError('Rigid body path mapping incomplete')
        before=(int(base._sim_step_counter),int(base.sim._physics_step_count))
        geometry=usd.inspect_stage(stage,robot_path,out/'robot_usd',body_paths=paths.values())
        assert before==(int(base._sim_step_counter),int(base.sim._physics_step_count))
        # Config dictionaries contain numpy/tensors/classes. Store explicit
        # physical scalars instead of stringifying a potentially lossy config.
        motors={name:{'class':type(m).__module__+'.'+type(m).__name__,
            'time_lags':m.time_lags.cpu().tolist(),'joint_names_expr':m.cfg.joint_names_expr,
            **{k:usd.value(getattr(m.cfg,k)) for k in ('stiffness','damping','effort_limit','saturation_effort','velocity_limit','min_delay','max_delay')}}
            for name,m in base._robot.actuators.items()}
        result={'schema':'qlm-original-robot-reference-v1','work_id':'QLM-SIM-005','status':'completed',
            'backend':runtime['assert_physx_environment'](env),'source_commit':source['reference_commit'],
            'robot_source_uri':cfg.robot.spawn.usd_path,'body_names':list(data.body_names),'body_paths':paths,
            'joint_names':list(data.joint_names),'total_mass_kg':float(arrays['body_mass'].sum()),
            'physics_arrays_sha256':compare.sha(out/'robot_physics.npz'),'usd_reference_sha256':compare.sha(out/'robot_usd/reference.json'),
            'motors':motors,'physics_steps_for_export':0,'renderer_or_policy_run':False,
            'shape_count':view.max_shapes,'material_columns':['static_friction','dynamic_friction','restitution'],
            'default_material':{k:usd.value(getattr(cfg.sim.physics_material,k)) for k in
                ('static_friction','dynamic_friction','restitution','friction_combine_mode','restitution_combine_mode')},
            'source_unchanged':compare.source_identity(ref)==source,
            'geometry_counts':{'geometries':len(geometry['geometries']),'joints':len(geometry['joints']),'materials':len(geometry['materials'])}}
    except BaseException as error:
        result={'status':'failed','error':type(error).__name__+': '+str(error),'traceback':traceback.format_exc()}
        print(result['traceback'],flush=True)
    finally:
        (out/'result.json').write_text(json.dumps(result,indent=2,default=str,allow_nan=False)+'\n')
        if env is not None:env.close()
        if app is not None:app.app.close()
    if result['status']!='completed':raise SystemExit(1)
    print(result,flush=True)


if __name__=='__main__':main()
