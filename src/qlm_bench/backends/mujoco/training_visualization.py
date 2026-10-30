"""One fixed held-out episode for the learner's periodic closed-loop prediction video.

The episode runs against the learner's visualization policy endpoint with the same native CPU
physics, RAMBO controller and dual policy cameras as training. The evaluation observer camera
(never a policy input) is saved at the policy's 0.08 s observation ticks. This module is not a
training-runtime file: it never touches the training pool schedule or producer streams.
"""
import argparse
import json
import math
from pathlib import Path

CASE = Path(__file__).with_name('training_visualization_case.json')


def run(pool_path, port, output, *, case_path=CASE, rpc_timeout_s=600.):
    from PIL import Image
    from .training_live import SEMANTICS, select_cpu_environment
    from .training_pool import under
    select_cpu_environment()
    import torch
    torch.set_num_threads(1)
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.live import RPCClient, SynchronousDriver
    # The learner already admitted this pool; read only the scene/controller this case needs.
    pool, root = json.loads(Path(pool_path).read_text()), Path(pool_path).parent
    case = json.loads(Path(case_path).read_text())
    resource = pool['resources'].get(case['resource_identity'])
    if resource is None:
        raise ValueError('Visualization case scene is not part of this train pool')
    out = Path(output)
    (out / 'observer').mkdir(parents=True, exist_ok=False)
    clip = []
    def save(snapshot):
        tick, image = int(snapshot['physics_step']), snapshot.get('observer_rgb')
        if image is not None and tick % 40 == 0:
            Image.fromarray(image).resize((640, 360), Image.BILINEAR).save(out / 'observer' / f'{tick:08d}.jpg', quality=90)
        # Render the 720p observer only for the next 0.08 s policy tick, not every 25 Hz boundary.
        runtime.renderer.observer_clip = clip[0] if (tick + 10) % 40 == 0 else None
    runtime = create_runtime(case['task'], 'native', model_path=under(root, resource['entrypoint']),
                             checkpoint=under(root, pool['controller']), device='cpu', seed=case['seed'], trace_only=False,
                             rgb_profile='dual-rgb-360p-v1', profile_override={**case['goal_overlay'], 'horizon_s': case['horizon_s']})
    try:
        if runtime.physics.model_identity != case['resource_identity']:
            raise ValueError('Visualization scene differs from the held-out reset binding')
        runtime.renderer.evaluation_observer = True
        clip.append(runtime.renderer.observer_clip)
        if clip[0] is None:
            raise ValueError('Visualization scene has no observer camera')
        runtime.on_observation = save
        initial = runtime.reset(initial_state=case['initial_state'])
        driver = SynchronousDriver(runtime, RPCClient(port=port, timeout_s=rpc_timeout_s),
                                   session_id='opd4-visualization-' + case['episode_uid'], instruction=case['instruction'],
                                   task_id=case['task'], task_version=case['task_version'], timeout_s=rpc_timeout_s,
                                   state_semantics=SEMANTICS, max_groups=math.ceil(case['horizon_s'] / .32))
        driver.reset_episode(case['episode_uid'] + '-visualization', policy_seed=case['policy_seed'], initial_snapshot=initial)
        result = driver.run_episode()
        row = {'episode_uid': case['episode_uid'], 'split': case['split'], 'task': case['task'],
               'policy_seed': case['policy_seed'], 'outcome': dict(runtime.outcome),
               'termination_reason': result['termination_reason'], 'observer_view': 'evaluation_observer'}
    finally:
        runtime.close()
    (out / 'result.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pool', required=True); p.add_argument('--port', required=True, type=int)
    p.add_argument('--output', required=True); p.add_argument('--case', default=str(CASE))
    p.add_argument('--rpc-timeout-s', type=float, default=600.)
    a = p.parse_args(argv)
    print(json.dumps(run(a.pool, a.port, a.output, case_path=a.case, rpc_timeout_s=a.rpc_timeout_s)))


if __name__ == '__main__':
    main()
