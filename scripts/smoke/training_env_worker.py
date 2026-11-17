"""Smoke test of the streaming training environment: one real CPU episode fragment against a mock learner.

Runs the training worker (native MuJoCo CPU, RAMBO CPU, OSMesa) for a few 16-command chunks against an
in-process qlm-live-v1 mock learner that sends constant commands, then stops it. With ``--compare`` it runs
the same fragment in both render modes and checks that the policy frames are bit-identical.

    python scripts/smoke/training_env_worker.py --pool <train pool>/manifest.json --output <new dir> [--compare]
"""
import argparse
import hashlib
import json
from pathlib import Path
import threading


def fragment(pool, output, *, render_mode, chunks, task):
    from qlm_bench.training_env.worker import run_worker, select_cpu_environment
    select_cpu_environment()
    from qlm_bench.training_env.pool import load, sha
    from qlm_bench.training_env.schedule import EpisodeSchedule, prepare_profile, read_profile
    from qlm_bench.live import PolicyHistory, RPCServer, make_message

    class MockLearner:
        def __init__(self):
            self.history, self.chunks, self.resets, self.frames = PolicyHistory(), 0, 0, []

        def _frames(self, observation):
            for sample in observation['samples']:
                self.frames.append({k: hashlib.sha256(v.tobytes()).hexdigest() for k, v in sorted(sample['rgb'].items())})

        def __call__(self, request):
            method, payload = request['method'], request['payload']
            if method == 'reset':
                self.resets += 1
                self.history.reset(payload['reset'])
                self.history.observe(payload['observation']['observation'])
                self._frames(payload['observation'])
                return {'status': 'observed'}
            if method == 'predict':
                tick = self.history.tick
                chunk = make_message('ActionChunk', {'observation_id': self.history.observation_id, 'chunk_id': f'chunk:{tick}',
                                                     'start_tick': tick, 'action_period_ticks': 10,
                                                     'actions': [[0., 0., 0., .1934, .142, .05, 0., 0., 0.]] * 16},
                                     session_id=request['session_id'], episode_id=request['episode_id'],
                                     reset_epoch=request['reset_epoch'], message_id=f'action:{tick}')
                self.history.expect_chunk(chunk)
                return chunk
            if method == 'feedback':
                self.history.accept_ack(payload['ack'])
                if payload['observation'] is not None:
                    self.history.observe(payload['observation']['observation'])
                    self._frames(payload['observation'])
                self.chunks += 1
                return {'status': self.history.state, 'stop_after_feedback': self.chunks == chunks,
                        'training': {'student_version': 0, 'stop_reason': 'smoke_budget_end'}}
            return {'status': 'ended'}

    output = Path(output)
    control = output.with_name(output.name + '-control')
    control.mkdir(parents=True, exist_ok=False)
    profile = control / 'profile.json'
    prepare_profile(pool, profile, tasks=[task], max_active_per_task=1)
    EpisodeSchedule.create(control / 'schedule.sqlite', read_profile(profile, sha(pool)), load(pool), 'smoke')
    learner = MockLearner()
    server = RPCServer(learner, port=0, timeout_s=120)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = run_worker(pool, sha(pool), rank=0, world_size=1, port=server.address[1], output=output,
                            rpc_timeout_s=120, wall_timeout_s=1800, max_episodes=2, segment='smoke',
                            training_profile=profile, schedule_db=control / 'schedule.sqlite', render_mode=render_mode)
    finally:
        server.shutdown()
        server.close()
        thread.join(timeout=5)
    if learner.resets != 1 or learner.chunks != chunks:
        raise RuntimeError(f'Expected one episode of {chunks} chunks, got {learner.resets} resets / {learner.chunks} chunks')
    return {'render_mode': render_mode, 'chunks': learner.chunks, 'policy_frames': len(learner.frames),
            'frames_sha256': hashlib.sha256(json.dumps(learner.frames).encode()).hexdigest(),
            'elapsed_s': result['elapsed_s'], 'worker': result}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--pool', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--chunks', type=int, default=4)
    p.add_argument('--task', default='push_box')
    p.add_argument('--render-mode', choices=('full', 'sampled'), default='full')
    p.add_argument('--compare', action='store_true', help='Run full and sampled and compare the policy frames')
    a = p.parse_args()
    out = Path(a.output)
    modes = ('full', 'sampled') if a.compare else (a.render_mode,)
    runs = [fragment(a.pool, out / mode, render_mode=mode, chunks=a.chunks, task=a.task) for mode in modes]
    report = {'passed': True, 'runs': runs}
    if a.compare:
        report['policy_frames_identical'] = runs[0]['frames_sha256'] == runs[1]['frames_sha256']
        report['passed'] = report['policy_frames_identical']
    (out / 'smoke-result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'runs'} |
                     {'runs': [{k: r[k] for k in ('render_mode', 'chunks', 'policy_frames', 'frames_sha256', 'elapsed_s')} for r in runs]},
                     indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
