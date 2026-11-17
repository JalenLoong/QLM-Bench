"""Task RL environment worker: arbitrary resets, chunk execution and rollout-state capture on any task scene.

One worker process serves one rollout stream over length-prefixed JSON frames on stdin/stdout
(``qlm_bench.task_rl.ipc``). Resets reconstruct ``t=0`` of an EvalCase exactly as Standard100 does
(``benchmark.suite.reconstruct``); commands go through the same 50 Hz native9 path; privileged rows feed
the reward on the client side; rollout states (``rollout_state`` / ``snapshot``) allow restarts from any
160-tick boundary of an earlier rollout.

Operations (schema ``qlm-task-rl-scene-ipc-v1``):
    reset {case, model, policy_seed?}     t=0 of an EvalCase; rebuilds the runtime when the scene changes
    restore_state {case, model, path}     rollout-state restore into a new session, same case
    execute {chunk, commands, ring}       16 native9 commands; ring=True keeps the post-chunk snapshot in memory
    capture_state {path}                  persist the live boundary
    persist_ring {chunk, path, origin}    persist a ring snapshot taken earlier in this session
    inspect {}
RGB returned is the policy dual-view 360p observation on the 80 ms grid (``samples`` every 40 ticks).
``--render-mode`` / ``$QLM_RENDER_MODE``: ``full`` (default) or ``sampled`` (accelerated; same policy frames).
"""
import argparse
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import sys

from qlm_bench.task_rl.ipc import protocol_stdout, read_frame, task_progress, write_frame

SCHEMA = 'qlm-task-rl-scene-ipc-v1'
PROPRIO_KEYS = ('observation.state.base.linear_velocity', 'observation.state.base.angular_velocity',
                'observation.state.projected_gravity', 'observation.state.fl_ee_position',
                'observation.state.fl_ee_velocity', 'observation.state.fl_contact_force',
                'observation.state.foot_contact')


def proprio(state):
    """Flat non-privileged body state (22 values) the actor may read, from the runtime's own channels."""
    out = []
    for key in PROPRIO_KEYS:
        out += [float(v) for v in state[key]]
    if not all(math.isfinite(v) for v in out):
        raise FloatingPointError('Nonfinite proprioceptive state')
    return out


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SceneWorker:
    def __init__(self, controller, state_root, render_mode=None):
        import torch
        from qlm_bench.backends.mujoco.runtime import render_mode as select_render_mode
        self.render_mode = select_render_mode(render_mode)
        torch.set_num_threads(1)
        self.controller = controller
        self.state_root = str(Path(state_root).resolve())
        self.runtime = None
        self.case_path = None
        self.binding = None
        self.session = None
        self.chunk = 0
        self.anchor_tick = 0
        self.ended = False
        self.ring = {}
        self.last_rgb = None
        self.seen = set()
        self.last_id = None
        self.last_response = None

    # ------------------------------------------------------------ envelope
    def handle(self, request):
        if set(request) != {'schema', 'id', 'operation', 'session', 'payload'} or request['schema'] != SCHEMA:
            raise ValueError('Invalid Task RL scene worker envelope')
        if request['id'] == self.last_id:
            return self.last_response
        if request['id'] in self.seen:
            raise ValueError('Response expired; never reexecute physical work')
        self.seen.add(request['id'])
        try:
            with contextlib.redirect_stdout(sys.stderr):
                response = {'ok': True, 'result': self._dispatch(request)}
        except Exception as exc:
            response = {'ok': False, 'error_type': type(exc).__name__, 'error': str(exc)}
        self.last_id, self.last_response = request['id'], response
        return response

    def _dispatch(self, request):
        op, payload, session = request['operation'], request['payload'], request['session']
        if op == 'reset':
            return self._reset(session, payload)
        if op == 'restore_state':
            return self._restore_state(session, payload)
        if session != self.session:
            raise ValueError('Operation belongs to a stale session')
        if op == 'execute':
            return self._execute(payload)
        if op == 'capture_state':
            return self._capture_state(payload)
        if op == 'persist_ring':
            return self._persist_ring(payload)
        if op == 'inspect':
            return {'absolute_tick': int(self.runtime.physics.ticks[0]), 'freeze': self.runtime.freeze_token()}
        raise ValueError('Unknown scene worker operation')

    # ------------------------------------------------------------ scene lifecycle
    def _load_case(self, case_path, model_path):
        from qlm_bench.benchmark import EvalCase
        case = EvalCase.from_record(json.loads(Path(case_path).read_text()))
        if self.case_path != str(case_path):
            if self.runtime is not None:
                self.runtime.close()
                self.runtime = None
            from qlm_bench.backends.factory import create_runtime
            overlay = {**case.scene.get('goal_overlay', {}), 'horizon_s': case.scene['horizon_s']}
            rt = create_runtime(case.task_id, 'native', model_path=model_path, checkpoint=self.controller, seed=case.seed,
                                device='cpu', trace_only=False, rgb_profile='dual-rgb-360p-v1', profile_override=overlay)
            from qlm_bench.backends.mujoco.runtime import apply_render_mode
            apply_render_mode(rt, self.render_mode)
            renderer = rt.renderer.gl_identity['renderer'].lower()
            software = any(k in renderer for k in ('llvmpipe', 'softpipe', 'swrast'))
            if os.environ.get('MUJOCO_GL') == 'egl' and software:
                rt.close()
                raise ValueError('Software EGL refused for the hardware-rendered worker')
            self.runtime, self.case_path = rt, str(case_path)
            self.binding = _sha(case_path)
        return case

    def _opened(self, session):
        self.session, self.chunk, self.ended, self.ring = session, 0, False, {}

    def _boundary(self):
        """Common restore/reset response for a live boundary."""
        from qlm_bench.task_rl import privileged
        rt = self.runtime
        raw = rt.state()
        self.last_rgb = raw['rgb']
        self.anchor_tick = int(rt.physics.ticks[0])
        return {'absolute_tick': self.anchor_tick, 'rgb': self.last_rgb, 'progress': task_progress(rt),
                'freeze': rt.freeze_token(), 'renderer': rt.renderer.gl_identity, 'proprio': proprio(raw['state']),
                'privileged': self._privileged([privileged.row(rt)]), 'privileged_static': privileged.static(rt),
                'instruction': rt.profile['instruction']}

    def _retire_unfinished_episode(self):
        """An episode that ended without a terminal (a local-horizon truncation) leaves the runtime executing, and the
        runtime refuses to reseed it; the next reset then starts the scene on a fresh runtime, as after a scene switch."""
        rt = self.runtime
        if rt is not None and rt.current is not None and rt.terminal is None:
            rt.close()
            self.runtime, self.case_path = None, None

    def _reset(self, session, payload):
        from qlm_bench.benchmark.suite import reconstruct
        self._retire_unfinished_episode()
        case = self._load_case(payload['case'], payload['model'])
        reconstruct(self.runtime, case)
        self._opened(session)
        return {**self._boundary(), 'case_id': case.case_id, 'case_seed': case.seed}

    def _restore_state(self, session, payload):
        from qlm_bench.task_rl import open_room_door as door, rollout_state as own_state
        self._load_case(payload['case'], payload['model'])
        path = own_state.resolve(self.state_root, payload['path'])
        state, record = own_state.load(path, binding_sha256=self.binding)
        door.restore(self.runtime, state)
        self._opened(session)
        return {**self._boundary(), 'own_state': str(path), 'origin': record['origin']}

    # ------------------------------------------------------------ physics
    def _privileged(self, rows, terminal=None):
        from qlm_bench.task_rl import privileged
        value = privileged.payload(self.runtime, rows)
        value['terminal'] = None if terminal is None else {
            'reason': terminal['reason'], 'tick': int(terminal['tick']),
            'code': privileged.TERMINAL_CODES.get(terminal['reason'], -1)}
        return value

    def _execute(self, payload):
        import numpy as np
        from qlm_bench.contracts.command.runtime import prepare_command
        from qlm_bench.task_rl import open_room_door as door, privileged
        rt = self.runtime
        actions = payload['commands']
        if len(actions) != 16 or payload['chunk'] != self.chunk or rt.terminal is not None or self.ended:
            raise ValueError('Exactly one ordered native9 chunk required')
        requested = np.asarray(actions, dtype=np.float64)
        if requested.shape != (16, 9) or not np.isfinite(requested).all():
            raise FloatingPointError('Nonfinite/malformed policy commands')
        start = int(rt.physics.ticks[0])
        if start % 160:
            raise ValueError('Chunks start on 160-tick boundaries')
        prepared = [prepare_command(x, f'{self.session}:{self.chunk}:{i}', start + i * 10) for i, x in enumerate(actions)]
        samples, rows, state_rows, terminal = [], [], [], None
        for command in prepared:
            try:
                outcome = rt.step(command)
            except FloatingPointError as exc:
                terminal = {'tick': int(rt.physics.ticks[0]), 'reason': 'physics_instability', 'policy_failure': True,
                            'task_terminal': False, 'success': False, 'fallen': False, 'timed_out': False, 'detail': str(exc)}
                break
            rows.append(outcome['command'])
            tick = int(rt.physics.ticks[0])
            state_rows.append(privileged.row(rt, completed=outcome['command']['status'] == 'completed',
                                             terminal_reason=None if outcome['terminal'] is None else outcome['terminal']['reason']))
            if tick % 40 == 0:
                samples.append({'tick': tick, 'simulation_time_ns': tick * 2_000_000, 'rgb': rt.state()['rgb']})
            if outcome['terminal'] is not None:
                terminal = {'tick': tick, 'reason': outcome['terminal']['reason'], **rt.outcome}
                break
        self.ended = terminal is not None
        rows += prepared[len(rows):]
        chunk = self.chunk
        self.chunk += 1
        body = None
        if terminal is None:
            raw = rt.state()
            body = proprio(raw['state'])
            if payload.get('ring'):
                self.ring[chunk] = (door.capture(rt), privileged.row(rt), int(rt.physics.ticks[0]))
        return {'schema': 'qlm-task-rl-execution-v1', 'session': self.session, 'chunk': chunk, 'start_tick': start,
                'end_tick': int(rt.physics.ticks[0]), 'commands': rows, 'completed_count': sum(x['status'] == 'completed' for x in rows),
                'samples': samples, 'terminal': terminal, 'progress': task_progress(rt), 'freeze': rt.freeze_token(),
                'proprio': body, 'privileged': self._privileged(state_rows, terminal)}

    # ------------------------------------------------------------ own state
    def _origin(self, origin):
        return {'case': self.case_path, 'session': self.session, 'anchor_tick': self.anchor_tick, **(origin or {})}

    def _capture_state(self, payload):
        from qlm_bench.task_rl import rollout_state as own_state, privileged
        rt = self.runtime
        if self.ended or rt.terminal is not None:
            raise ValueError('Rollout state requires a nonterminal episode')
        path = own_state.resolve(self.state_root, payload['path'])
        tick = int(rt.physics.ticks[0])
        record = own_state.save(rt, path, binding_sha256=self.binding, privileged_row=privileged.row(rt),
                                origin=self._origin({'chunk': self.chunk, 'relative_tick': tick - self.anchor_tick}))
        return {'path': str(path), 'absolute_tick': tick, 'snapshot_sha256': record['snapshot_sha256']}

    def _persist_ring(self, payload):
        from qlm_bench.task_rl import rollout_state as own_state
        chunk = payload['chunk']
        if chunk not in self.ring:
            raise ValueError(f'No ring snapshot for chunk {chunk}')
        state, row, tick = self.ring[chunk]
        path = own_state.resolve(self.state_root, payload['path'])
        record = own_state.save_snapshot(state, path, task_id=self.runtime.task.task, binding_sha256=self.binding, privileged_row=row,
                                         origin=self._origin({'chunk': chunk, **payload.get('origin', {})}))
        return {'path': str(path), 'absolute_tick': tick, 'snapshot_sha256': record['snapshot_sha256']}

    def close(self):
        if self.runtime is not None:
            self.runtime.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--controller', required=True)
    p.add_argument('--state-root', required=True)
    p.add_argument('--render-mode', choices=('full', 'sampled'), default=None,
                   help='full (default): render every command + observer; sampled: only the 80 ms sample points')
    a = p.parse_args()
    channel = protocol_stdout()
    with contextlib.redirect_stdout(sys.stderr):
        worker = SceneWorker(a.controller, a.state_root, render_mode=a.render_mode)
    try:
        while (request := read_frame(sys.stdin.buffer)) is not None:
            write_frame(channel, worker.handle(request))
    finally:
        worker.close()


if __name__ == '__main__':
    main()
