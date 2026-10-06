"""One synchronous physical chunk, actual command acknowledgements and fresh RGB.

Only execute_chunk() calls runtime.step(). Network requests and model waits cannot
advance physics or controller inference. The existing environment owns task outcomes
and retains its pre-reset terminal snapshot even if the low-level env auto-resets.
"""
from __future__ import annotations

from copy import deepcopy
from collections import deque
import hashlib
import time

from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
from qlm_bench.compatibility.contracts_v2.validation import digest, validate_record, validate_profiles
from qlm_bench.policy_interface import ExecutionAck, ExecutionHistory, Native9Command
from .history import PolicyHistory
from .protocol import (GROUP_COMMANDS, GROUP_TICKS, PHYSICS_STEP_NS, SAMPLE_TICKS,
                       make_message, make_observation)


class ExecutionUncertain(RuntimeError):
    """Physical side effect cannot be proven; reset is mandatory, never re-execute."""


def snapshot_receipt(snapshot):
    """Physical diagnostics with compact image identities; no policy-private values."""
    if snapshot is None:
        return None
    result = {key: deepcopy(value) for key, value in snapshot.items() if key != 'rgb'}
    result['rgb'] = {key: {'sha256': hashlib.sha256(image.tobytes(order='C')).hexdigest(),
                           'shape': list(image.shape), 'dtype': str(image.dtype)}
                     for key, image in snapshot.get('rgb', {}).items()}
    return result


class SynchronousDriver:
    def __init__(self, runtime, client, *, session_id, instruction, task_id='push_box',
                 task_version='push-box-v2-2', timeout_s=600., state_semantics=None,
                 on_event=None, max_groups=1000):
        if type(max_groups) is not int or max_groups < 1:
            raise ValueError('Explicit positive engineering group bound required')
        self.runtime = runtime
        self.client = client
        self.session_id = session_id
        self.instruction = instruction
        self.task_id = task_id
        self.task_version = task_version
        self.timeout_s = timeout_s
        self.state_semantics = dict(state_semantics or {})
        self.on_event = on_event or (lambda kind, payload: None)
        self.max_groups = max_groups
        self.identity = None
        self.history = None
        self.policy_history = PolicyHistory()
        self._chunks = {}
        self._chunk_ids = {}
        self._cached_chunk_ids = deque()
        self._failed = False
        self.ended = False
        self.last_snapshot = None
        self.observation = None

    def _emit(self, event, payload):
        self.on_event(event, payload)

    def _clock(self):
        # state() captures sensors and never steps; kept independent of private env API.
        snapshot = self.runtime.state()
        return snapshot['reset_epoch'], snapshot['physics_step'], snapshot['simulation_time_ns']

    def _rpc(self, method, payload, request_id):
        before = self._clock()
        start = time.monotonic()
        try:
            result = self.client.call(method, payload, request_id=request_id, session_id=self.session_id,
                                      episode_id=self.identity[1], reset_epoch=self.identity[2])
        finally:
            after = self._clock()
            self._emit('wait', {'method': method, 'request_id': request_id,
                               'wall_time_s': time.monotonic()-start, 'before': before, 'after': after,
                               'simulation_frozen': before == after})
            if before != after:
                self._failed = True
                raise ExecutionUncertain('Simulation/controller advanced while awaiting policy')
        return result

    def reset_episode(self, episode_id, *, policy_seed):
        if type(policy_seed) is not int or policy_seed < 0:
            raise ValueError('Explicit nonnegative policy seed required')
        snapshot = self.runtime.reset()
        if snapshot['physics_step'] != 0 or snapshot['simulation_time_ns'] != 0:
            raise ValueError('Initial observation must be at the reset origin')
        epoch = snapshot['reset_epoch']
        if self.identity is not None and epoch <= self.identity[2]:
            raise ValueError('Physical reset epoch did not advance')
        self.identity = (self.session_id, episode_id, epoch)
        self.history = ExecutionHistory(episode_id, epoch)
        self._chunks = {}
        self._chunk_ids = {}
        self._cached_chunk_ids = deque()
        self._failed = False
        self.ended = False
        self.last_snapshot = snapshot
        ids = dict(session_id=self.session_id, episode_id=episode_id, reset_epoch=epoch)
        reset = make_message('ResetRequest', dict(timeout_s=self.timeout_s, origin_sim_ns=0,
                             task=dict(id=self.task_id, version=self.task_version,
                                       instruction=self.instruction, language='en')),
                             message_id=f'reset:{epoch}', extensions={'policy_seed': policy_seed}, **ids)
        observation = make_observation([snapshot], message_id=f'obs:{epoch}:0',
                                       instruction=self.instruction, executed_history=[],
                                       state_semantics=self.state_semantics, **ids)
        self.policy_history.reset(reset)
        self.policy_history.observe(observation['observation'])
        self.observation = observation
        self._emit('reset', {'reset': reset, 'snapshot': snapshot_receipt(snapshot)})
        try:
            response = self._rpc('reset', {'reset': reset, 'observation': observation}, f'reset:{epoch}')
            self._emit('policy_reset', {'response': response, 'policy_seed': policy_seed,
                                        'episode_id': episode_id, 'reset_epoch': epoch})
            return response
        except BaseException:
            self._failed = True
            raise

    def execute_chunk(self, message):
        """Return cached exact duplicates; a conflicting or uncertain chunk never runs."""
        validate_record('ActionChunk', message)
        validate_profiles(message['profiles'])
        ident = tuple(message[k] for k in ('session_id', 'episode_id', 'reset_epoch'))
        if ident != self.identity:
            raise ValueError('Stale ActionChunk epoch')
        sha = digest(message)
        chunk_id = message['body']['chunk_id']
        message_id = message['message_id']
        if chunk_id in self._chunk_ids:
            old_sha, result = self._chunk_ids[chunk_id]
            if old_sha != sha:
                raise ValueError('Conflicting duplicate ActionChunk')
            if result is None:
                raise ExecutionUncertain('Chunk execution is unconfirmed; reset required')
            if result is False:
                raise ExecutionUncertain('Known completed chunk feedback expired; reset required')
            return deepcopy(result)
        if message_id in self._chunks:
            raise ValueError('ActionChunk message identity reused')
        if self._failed or self.ended:
            raise ExecutionUncertain('Episode ended/failed; reset required')
        body = message['body']
        if len(body['actions']) != GROUP_COMMANDS:
            raise ValueError('Synchronous live profile executes exactly sixteen native9 commands')
        if len(self._chunks) >= self.max_groups:
            raise ValueError('Explicit engineering group bound exhausted')
        self.policy_history.expect_chunk(message)
        rows = [prepare_command(action, f'{chunk_id}:{index}', body['start_tick']+10*index)
                for index, action in enumerate(body['actions'])]
        self._chunks[message_id] = sha
        self._chunk_ids[chunk_id] = (sha, None)  # Reserve before any physical side effect.
        samples = []
        terminal = None
        try:
            current = self.runtime.state()
            if current['reset_epoch'] != ident[2] or current['physics_step'] != body['start_tick']:
                raise ValueError('ActionChunk does not start at the actual physical boundary')
            end_tick = body['start_tick']
            for index, prepared in enumerate(rows):
                command = Native9Command.from_values(prepared['requested'], episode_uid=ident[1],
                            reset_epoch=ident[2], command_id=prepared['command_id'])
                self.history.validate_command(command)
                result = self.runtime.step(deepcopy(prepared))
                actual = result['command']
                # Confirm the runtime really retained the submitted request and transform.
                for key in ('command_id', 'start_tick', 'end_tick', 'requested', 'transformed', 'filtered'):
                    if actual[key] != prepared[key]:
                        raise ValueError('Runtime confirmation differs from submitted command: ' + key)
                validate_record('command', actual)
                if actual['status'] not in ('completed', 'partial') or \
                        result['simulation_time_ns'] != actual['executed_until_tick']*PHYSICS_STEP_NS:
                    raise ValueError('Runtime did not confirm a physical execution interval')
                completed = actual['status'] == 'completed'
                if completed != result['completed_interval']:
                    raise ValueError('Runtime completed-interval flag disagrees with command')
                ack = ExecutionAck(ident[1], ident[2], command.command_id,
                         actual['start_tick']*PHYSICS_STEP_NS,
                         actual['executed_until_tick']*PHYSICS_STEP_NS,
                         tuple(actual['executed'] if completed else actual['filtered']), completed)
                self.history.accept(command, ack)
                rows[index] = deepcopy(actual)
                end_tick = actual['executed_until_tick']
                terminal = result['terminal']
                if terminal is not None:
                    if terminal['physics_step'] != end_tick or terminal['reset_epoch'] != ident[2] or \
                            terminal['simulation_time_ns'] != ack.end_ns:
                        raise ValueError('Terminal snapshot is not from the pre-reset execution boundary')
                    self.last_snapshot = terminal
                    break
                if not completed:
                    raise ExecutionUncertain('Partial physical interval requires terminal evidence')
                if end_tick % SAMPLE_TICKS == 0:
                    snapshot = self.runtime.state()
                    if snapshot['physics_step'] != end_tick or snapshot['reset_epoch'] != ident[2]:
                        raise ValueError('RGB capture skipped the completed command boundary')
                    samples.append(snapshot)
                    self.last_snapshot = snapshot
            reason = terminal['reason'] if terminal is not None else 'completed'
            ack_message = make_message('ExecutionAck', dict(chunk_id=chunk_id, start_tick=body['start_tick'],
                             end_tick=end_tick, completed_count=sum(row['status']=='completed' for row in rows),
                             commands=rows, reason=reason), session_id=ident[0], episode_id=ident[1],
                             reset_epoch=ident[2], message_id=f'ack:{ident[2]}:{chunk_id}')
            self.policy_history.accept_ack(ack_message)
            observation = None
            if terminal is None:
                observation = make_observation(samples, session_id=ident[0], episode_id=ident[1],
                               reset_epoch=ident[2], message_id=f'obs:{ident[2]}:{end_tick}',
                               instruction=self.instruction, executed_history=self.policy_history.records,
                               state_semantics=self.state_semantics)
                self.policy_history.observe(observation['observation'])
                self.observation = observation
            else:
                self.ended = True
            feedback = {'ack': ack_message, 'observation': observation,
                        'terminal': None if terminal is None else {
                            'tick': terminal['physics_step'], 'reset_epoch': ident[2],
                            'simulation_time_ns': terminal['simulation_time_ns'],
                            'reason': terminal['reason'], 'captured_before_reset': True,
                            'success': bool(terminal.get('success', False)),
                            'fallen': bool(terminal.get('fallen', False)),
                            'timed_out': bool(terminal.get('timed_out', False)),
                            'rgb': snapshot_receipt(terminal)['rgb']}}
            # A terminal tail is diagnostic only; it is never padded into a model group.
            self._emit('execution', {'requested': message, 'ack': ack_message,
                         'sample_ticks': [sample['physics_step'] for sample in samples],
                         'samples': [snapshot_receipt(sample) for sample in samples],
                         'terminal': snapshot_receipt(terminal)})
            self._chunk_ids[chunk_id] = (sha, deepcopy(feedback))
            self._cached_chunk_ids.append(chunk_id)
            while len(self._cached_chunk_ids) > 2:
                expired = self._cached_chunk_ids.popleft()
                self._chunk_ids[expired] = (self._chunk_ids[expired][0], False)
            return feedback
        except BaseException:
            self._failed = True
            self._emit('execution_error', {'chunk_id': chunk_id, 'completed_commands':
                       [ack.__dict__ for ack in self.history.completed],
                       'state': 'execution_uncertain_reset_required'})
            raise

    def run_episode(self):
        if self.identity is None or self._failed:
            raise ValueError('Reset a policy episode first')
        groups = 0
        try:
            while not self.ended and groups < self.max_groups:
                observation_id = self.observation['observation']['message_id']
                chunk = self._rpc('predict', {'observation_id': observation_id},
                                  f'predict:{self.identity[2]}:{observation_id}')
                feedback = self.execute_chunk(chunk)
                self._rpc('feedback', feedback, f'feedback:{self.identity[2]}:{chunk["body"]["chunk_id"]}')
                groups += 1
            reason = self.last_snapshot.get('reason') if self.ended else 'engineering_group_budget'
            self._rpc('end', {'reason': reason}, f'end:{self.identity[2]}')
            self.ended = True
            result = dict(schema='qlm-live-engineering-result-v1', session_id=self.identity[0],
                          episode_id=self.identity[1], reset_epoch=self.identity[2], groups=groups,
                          completed_commands=len(self.history.completed),
                          simulation_time_ns=self.last_snapshot['simulation_time_ns'],
                          termination_reason=reason, task_terminal='reason' in self.last_snapshot,
                          terminal=snapshot_receipt(self.last_snapshot), publication_status='local_only',
                          formal_benchmark_score=None)
            self._emit('result', result)
            return result
        except BaseException:
            self._failed = True
            raise
