"""Bounded real Lift reference, original expert/controller, no formal admission."""
import argparse
import json
from pathlib import Path
import subprocess
import time

import numpy as np
from scipy.spatial.transform import Rotation
import torch

from qlm_bench.backends.mujoco.expert_adapter import ExpertAdapter
from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
from qlm_bench.backends.mujoco.trace import collect_trace, sha, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('model', 'checkpoint', 'output'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--work-id', default='QLM-DATA-020')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--offset-x', type=float, default=0.)
    p.add_argument('--offset-y', type=float, default=0.)
    p.add_argument('--yaw-deg', type=float, default=0.)
    p.add_argument('--expert-profile')
    p.add_argument('--recipe',choices=('retained-lift-expert','lift-body-lane-geometry-v1','smooth-lift'),default='retained-lift-expert')
    p.add_argument('--recipe-config')
    args = p.parse_args()
    if not np.isfinite([args.offset_x, args.offset_y, args.yaw_deg]).all():
        raise ValueError('Finite explicit initial-state offsets required')
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().parents[3]
    torch.set_num_threads(1)
    profile = json.loads(Path(args.model).with_suffix('.task.json').read_text())
    if profile['task_id'] != 'lift_basket':
        raise ValueError('Lift Basket only')
    identity = {'work_id':args.work_id, 'kind':'actual_reference_development_not_formal_demonstration',
        'formal_pilot':False, 'args':vars(args), 'entry_sha256':sha(__file__),
        'checkpoint_sha256':sha(args.checkpoint), 'started_at_unix_s':time.time(),
        'source_commit':subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),
        'source_dirty_status':subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True),
        'WAM_execution':'not_run', 'recipe':args.recipe,
        'initial_perturbation_only':True, 'task_predicate_or_controller_changed':False}
    if args.expert_profile:
        identity['expert_override'] = json.loads(Path(args.expert_profile).read_text())
        identity['expert_override_sha256'] = sha(args.expert_profile)
    if args.recipe_config:
        identity['recipe_config']=json.loads(Path(args.recipe_config).read_text())
        identity['recipe_config_sha256']=sha(args.recipe_config)
        identity['recipe']=identity['recipe_config'].get('recipe_id',args.recipe)
    # Existing public episode-goal overlay: align the configured initial XY
    # reference with physical XY offsets. This never enters the Lift predicate,
    # original expert geometry or RAMBO observations and does not change a schema.
    overlay=None
    if args.offset_x or args.offset_y:
        nominal_goal=profile.get('canonical_goal_position',profile['source_profile']['lift_goal_position'])
        overlay={'canonical_goal_position':[nominal_goal[0]+args.offset_x,
            nominal_goal[1]+args.offset_y,nominal_goal[2]]}
        identity['episode_goal_metadata_overlay']=overlay
    write_json(out/'attempt.json', identity)
    rt = MuJoCoRuntime(args.model, args.checkpoint, trace_only=True, seed=args.seed,profile_override=overlay)

    class Nominal:
        def reset(self, runtime, scene):
            if args.recipe in ('lift-body-lane-geometry-v1','smooth-lift'):
                if args.expert_profile:raise ValueError('Use only explicit composed recipe config')
                from qlm_bench.backends.mujoco.lift_reference_smooth import SmoothLiftExecutor
                self.expert=SmoothLiftExecutor(identity.get('recipe_config'))
                self.expert.reset(runtime,scene)
            else:
                self.expert = ExpertAdapter(runtime.physics, runtime.core, runtime.task)
                if args.expert_profile:
                    self.expert.apply_profile_override(identity['expert_override'])
            self.last_second = -1

        def command(self):
            values, diagnostic = self.expert.command()
            second = int(rt.physics.ticks[0]) // 500
            if second != self.last_second:
                self.last_second = second
                print(json.dumps({'simulation_s':second,'phase':diagnostic['phase'],
                    'minimum_basket_world_z_m':rt.task.progress(0),
                    'completely_through':diagnostic['completely_through'],
                    'foot_rear_past_handle_far_side_m':diagnostic['foot_rear_past_handle_far_side_m'],
                    'FL_joint_position_deg':np.rad2deg(rt.core.joint_pos[0,[0,4,8]].cpu()).tolist(),
                    'base_world':rt.core.robot.position[0].cpu().tolist()}), flush=True)
            return values, diagnostic

    try:
        snapshot = rt.physics.snapshot()
        qpos = snapshot['qpos'].copy()
        adr = int(rt.physics.model.joint('object_free').qposadr[0])
        qpos[adr:adr+2] += [args.offset_x,args.offset_y]
        q = qpos[adr+3:adr+7][[1,2,3,0]]
        qpos[adr+3:adr+7] = (Rotation.from_euler('z',args.yaw_deg,degrees=True)*Rotation.from_quat(q)).as_quat()[[3,0,1,2]]
        scene = {'candidate_id':out.name,'task_id':'lift_basket','seed':args.seed,
            'initial_state':{'schema':'qlm-mujoco-initial-state-v1','model_identity':snapshot['model_identity'],
                'qpos':qpos.tolist(),'qvel':snapshot['qvel'].tolist()},
            'initial_perturbation':{'dx_m':args.offset_x,'dy_m':args.offset_y,'yaw_deg':args.yaw_deg},
            'appearance_preset':profile.get('appearance_preset','ap_00'),
            'difficulty':'reference_development','asset_id':profile['asset_id']}
        result = collect_trace(rt,Nominal(),scene,out/'trace',batch_identity={**identity,'reference_id':out.name},
            reference=True,quality_policy='evidence-review-v1')
        write_json(out/'result.json',result)
        print(json.dumps(result),flush=True)
        if not result['passed']:
            raise SystemExit(2)
    except BaseException as error:
        if not (out/'result.json').exists():
            write_json(out/'failure.json',{'passed':False,'error':str(error),'kind':'infrastructure_or_executor_failure',
                'task_outcome':rt.outcome,'formal_demonstration':False})
        raise
    finally:
        rt.close()


if __name__ == '__main__':
    main()
