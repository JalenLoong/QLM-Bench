"""Original-source camera reset/first-step diagnostic with the original RAMBO actor."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import traceback


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m


def main():
    from isaaclab.app import AppLauncher
    p=argparse.ArgumentParser()
    for n in ('reference-source','resource-root','checkpoint','output'):p.add_argument('--'+n,required=True)
    p.add_argument('--sync-usd',action='store_true')
    AppLauncher.add_app_launcher_args(p);a=p.parse_args();a.enable_cameras=True
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);root=Path(__file__).resolve().parents[2]
    ref=Path(a.reference_source);guard=load('original_camera_guard',root/'scripts/rambo/compare_controller_isaac.py')
    identity=guard.source_identity(ref);app=None;runtime=None;result={};rows=[]
    (out/'attempt.json').write_text(json.dumps({'work_id':'QLM-SIM-005','source':identity,'entry_sha256':guard.sha(__file__),
        'purpose':'original camera reset versus first two actual command intervals; not task success evaluation'},indent=2)+'\n')
    try:
        app=AppLauncher(a)
        import numpy as np
        import torch
        import omni.replicator.core as rep
        from PIL import Image
        from rambo.tasks.common.controller_runtime import ControllerRuntime
        from rambo.tasks.common.environment_factory import PUSH_BOX_TASK_ID
        from rambo.contracts_v2.runtime import prepare_command
        usd=load('original_camera_values',root/'scripts/mujoco/usd_reference.py')
        torch.set_num_threads(1);torch.manual_seed(42)
        profile=json.loads((ref/'configs/collection/push_box.json').read_text())
        annotators={}
        def ready(rt):
            for role,sensor in [('ego',rt.base_env.front_camera),('task_centric',rt.base_env.task_camera)]:
                product=rep.create.render_product(str(sensor._sensor_prims[0].GetPath()),(1280,720))
                params=rep.AnnotatorRegistry.get_annotator('CameraParams',device='cpu');params.attach(product)
                annotators[role]=params
        runtime=ControllerRuntime(PUSH_BOX_TASK_ID,profile=profile,resource_root=a.resource_root,
                                  checkpoint_path=a.checkpoint,seed=42,episode_length_s=24.,device=a.device or 'cuda:0',on_environment_ready=ready)
        sync_evidence=None
        if a.sync_usd:
            import omni.physx
            import warp as wp
            base=runtime.base_env
            before=(base.episode_tick,int(base.sim._physics_step_count))
            physical_before=runtime.state()['state']
            base.sim.forward()
            omni.physx.get_physx_interface().update_transformations(True,True,False,False)
            for sensor in (base.front_camera,base.task_camera):wp.to_torch(sensor._is_outdated).fill_(True)
            base.sim.render()
            physical_after=runtime.state()['state']
            unchanged=all(np.array_equal(physical_before[k],physical_after[k]) for k in physical_before)
            sync_evidence={'clock_before':list(before),'clock_after':[base.episode_tick,int(base.sim._physics_step_count)],
                           'physical_state_unchanged':unchanged,'method':'PhysX update_transformations fast cache and USD; no simulation step'}
            if not unchanged or tuple(sync_evidence['clock_after'])!=before:raise ValueError('Camera sync changed physics state/time')
        def capture(label):
            packet=runtime.state()
            matrices={role:usd.value(annotator.get_data()) for role,annotator in annotators.items()}
            for role,rgb in packet['rgb'].items():Image.fromarray(rgb).save(out/(label+'-'+role+'.png'))
            row={'label':label,'state':packet['state'],'simulation_time_ns':packet['simulation_time_ns'],
                 'RGB_hashes':packet['rgb_hashes'],'matrices':matrices,'camera_world_position':{}}
            for role,m in matrices.items():
                row['camera_world_position'][role]=np.linalg.inv(np.asarray(m['cameraViewTransform']).reshape(4,4))[3,:3].tolist()
            rows.append(row)
        capture('reset')
        for i in range(2):
            runtime.step(prepare_command([0.,0.,0.,.1934,.142,.05,0.,0.,0.],f'reference:{i}',i*10))
            capture('step'+str(i+1))
        result={'status':'completed','rows':rows,'original_source_unchanged':guard.source_identity(ref)==identity,
                'reset_visual_sync':sync_evidence,
                'actual_controller_calls':4,'actual_physics_ticks':20,'source_checkpoint_sha256':guard.sha(a.checkpoint)}
    except BaseException as e:
        result={'status':'failed','error':repr(e),'traceback':traceback.format_exc(),'rows':rows};print(result['traceback'],flush=True)
    finally:
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        if runtime is not None:runtime.close()
        if app is not None:app.app.close()
    if result['status']!='completed':raise SystemExit(1)


if __name__=='__main__':main()
