"""Minimal qlm-live-v1 policy server: answers every predict with a constant native9 chunk.

Use it to check an installation end to end before plugging in a learned policy:

    python examples/dummy_policy_server.py --port 8765 &
    python -m qlm_bench.benchmark run --resource-root <root> --policy-port 8765 --cases <case_id> --output <dir>

A real policy implements the same four calls: ``reset`` (first observation of an episode), ``predict``
(return a 16-step native9 ActionChunk for the current observation), ``feedback`` (the executed commands plus
the next observation: two 640x360 RGB views sampled every 80 ms, see ``qlm_bench.live.protocol``) and ``end``
(payload ``{reason}`` at the end of every episode).
"""
import argparse

from qlm_bench.live import PolicyHistory, RPCServer, make_message, validate_live_observation


class ConstantPolicy:
    def __init__(self, command):
        self.command = [float(x) for x in command]
        self.history = PolicyHistory()

    def __call__(self, request):
        method, payload = request['method'], request['payload']
        if method == 'reset':
            self.history.reset(payload['reset'])
            self.history.observe(payload['observation']['observation'])
            return {'status': 'observed'}
        if method == 'predict':
            tick = self.history.tick
            chunk = make_message('ActionChunk', dict(observation_id=self.history.observation_id, chunk_id=f'chunk:{tick}',
                                                     start_tick=tick, action_period_ticks=10,
                                                     actions=[list(self.command) for _ in range(16)]),
                                 session_id=request['session_id'], episode_id=request['episode_id'],
                                 reset_epoch=request['reset_epoch'], message_id=f'chunk:{tick}')
            self.history.expect_chunk(chunk)
            return chunk
        if method == 'feedback':
            self.history.accept_ack(payload['ack'])
            if payload['observation'] is not None:
                validate_live_observation(payload['observation'])
                self.history.observe(payload['observation']['observation'])
            return {'status': self.history.state}
        return {'status': 'ended'}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--port', type=int, default=8765)
    p.add_argument('--command', type=float, nargs=9, default=[0.] * 9, metavar='X',
                   help='The native9 command repeated at every 20 ms step (default: zeros)')
    a = p.parse_args()
    with RPCServer(ConstantPolicy(a.command), port=a.port, timeout_s=600) as server:
        print(f'dummy policy listening on 127.0.0.1:{a.port}', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
