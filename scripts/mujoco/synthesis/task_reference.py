"""Bounded real Press reference development, separate from formal admission."""
import argparse
import json
from pathlib import Path
import subprocess
import time

import torch

from qlm_bench.backends.mujoco.expert_adapter import ExpertAdapter
from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
from qlm_bench.backends.mujoco.trace import collect_trace, sha, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('model', 'checkpoint', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--work-id', default='QLM-DATA-017')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--expert-profile')
    parser.add_argument('--recipe', choices=('retained-expert', 'smooth-body-approach-v2'), default='retained-expert')
    parser.add_argument('--recipe-config')
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().parents[3]
    torch.set_num_threads(1)
    profile = json.loads(Path(args.model).with_suffix('.task.json').read_text())
    if profile['task_id'] != 'press_button':
        raise ValueError('This reference entry currently admits only Press Button')
    identity = {
        'work_id': args.work_id,
        'kind': 'actual_reference_development_not_formal_demonstration',
        'formal_pilot': False,
        'args': vars(args),
        'source_commit': subprocess.check_output(
            ['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_dirty_status': subprocess.check_output(
            ['git', '-C', str(source), 'status', '--porcelain'], text=True),
        'entry_sha256': sha(Path(__file__)),
        'checkpoint_sha256': sha(args.checkpoint),
        'started_at_unix_s': time.time(),
        'WAM_execution': 'not_run',
    }
    if args.expert_profile:
        identity['expert_override'] = json.loads(Path(args.expert_profile).read_text())
        identity['expert_override_sha256'] = sha(args.expert_profile)
    if args.recipe_config:
        identity['recipe_config'] = json.loads(Path(args.recipe_config).read_text())
        identity['recipe_config_sha256'] = sha(args.recipe_config)
    write_json(output / 'attempt.json', identity)
    runtime = MuJoCoRuntime(args.model, args.checkpoint, trace_only=True, seed=args.seed)

    class Nominal:
        def reset(self, rt, scene):
            if args.recipe == 'smooth-body-approach-v2':
                from qlm_bench.backends.mujoco.press_reference_smooth import SmoothPressExecutor
                if args.expert_profile:
                    raise ValueError('Smooth reference has its own explicit recipe config')
                self.expert = SmoothPressExecutor(identity.get('recipe_config'))
                self.expert.reset(rt, scene)
            else:
                self.expert = ExpertAdapter(rt.physics, rt.core, rt.task)
                if args.expert_profile:
                    self.expert.apply_profile_override(identity['expert_override'])
            self.last_second = -1

        def command(self):
            values, diagnostic = self.expert.command()
            second = int(runtime.physics.ticks[0]) // 500
            if second != self.last_second:
                self.last_second = second
                print(json.dumps({'simulation_s': second, 'phase': diagnostic['phase'],
                    'button_displacement_m': diagnostic['button_displacement_m'],
                    'actual_fl_eef_world': diagnostic['actual_fl_eef_world'],
                    'FL_joint_position_deg': (runtime.core.joint_pos[0, [0, 4, 8]].cpu() * (180 / 3.141592653589793)).tolist(),
                    'base_world_position': runtime.core.robot.position[0].cpu().tolist()}), flush=True)
            return values, diagnostic

    try:
        snapshot = runtime.physics.snapshot()
        scene = {'candidate_id': output.name, 'task_id': profile['task_id'], 'seed': args.seed,
            'initial_state': {'schema': 'qlm-mujoco-initial-state-v1',
                'model_identity': snapshot['model_identity'],
                'qpos': snapshot['qpos'].tolist(), 'qvel': snapshot['qvel'].tolist()},
            'appearance_preset': profile.get('appearance_preset', 'ap_00'), 'difficulty': 'reference_development',
            'asset_id': profile['asset_id']}
        result = collect_trace(runtime, Nominal(), scene, output / 'trace',
            batch_identity={**identity, 'reference_id': output.name},
            reference=True, quality_policy='evidence-review-v1')
        write_json(output / 'result.json', result)
        print(json.dumps(result), flush=True)
    finally:
        runtime.close()


if __name__ == '__main__':
    main()
