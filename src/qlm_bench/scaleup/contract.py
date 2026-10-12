from __future__ import annotations
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
import re
from qlm_bench.tasks.registration import SCALEUP_TASK_IDS


@dataclass(frozen=True)
class EpisodeMetadata:
    episode_uid: str
    task_id: str
    split: str
    difficulty: str
    trajectory_type: str
    recovery_type: str | None
    appearance_preset: str
    asset_id: str
    initial_condition_id: str
    goal_condition_id: str
    environment_seed: int

    def __post_init__(self):
        if self.task_id not in SCALEUP_TASK_IDS or not re.fullmatch(re.escape(self.task_id) + r'__ep(00[0-9][0-9]|0100)', self.episode_uid) or self.episode_uid.endswith('ep0000'):
            raise ValueError('Task-qualified immutable ep0001..ep0100 UID required')
        if self.split not in ('train', 'validation', 'test') or self.difficulty not in ('clean', 'randomized') or self.trajectory_type not in ('normal', 'recovery'):
            raise ValueError('Explicit split/difficulty/trajectory labels required')
        if (self.trajectory_type == 'normal' and self.recovery_type is not None) or (self.trajectory_type == 'recovery' and not self.recovery_type):
            raise ValueError('Recovery type must match trajectory type')
        for field in ('appearance_preset', 'asset_id', 'initial_condition_id', 'goal_condition_id'):
            value = getattr(self, field)
            if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_.-]+', value):
                raise ValueError('Manifest identifiers required: ' + field)
        if not re.fullmatch(r'ap_0[0-4]', self.appearance_preset):
            raise ValueError('Frozen ap_00..ap_04 appearance preset required')
        if type(self.environment_seed) is not int or self.environment_seed < 0:
            raise ValueError('Explicit nonnegative environment seed required')

    def record(self):
        return asdict(self)


def make_slots(task_id, asset_ids, *, seed, recovery_types):
    """Deterministic exact margins, stratified split and ten pilot slots.

    This is a plan, not a claim that any collection has run. Condition IDs must
    resolve through the task's frozen condition manifest before collection.
    """
    if task_id not in SCALEUP_TASK_IDS or not 2 <= len(asset_ids) <= 3 or len(set(asset_ids)) != len(asset_ids) or not recovery_types:
        raise ValueError('Task,2..3 unique assets and task-specific recovery enum required')
    if type(seed) is not int or seed < 0:
        raise ValueError('Nonnegative slot seed required')
    rng = random.Random(seed)
    # Each ten-slot block has8 normal/2 recovery and2 clean/8 randomized.
    # Four blocks contain clean recovery, yielding16/4/64/16 overall.
    values = []
    for block in range(10):
        labels = [('clean', 'normal'), ('clean', 'recovery' if block < 4 else 'normal')]
        labels += [('randomized', 'normal')] * (7 if block < 4 else 6)
        labels += [('randomized', 'recovery')] * (1 if block < 4 else 2)
        # Keep pilot's four bins; remaining order is reproducibly shuffled.
        if block:
            rng.shuffle(labels)
        for position, (difficulty, trajectory) in enumerate(labels):
            number = block * 10 + position + 1
            split = 'train' if block < 8 else ('validation' if block == 8 else 'test')
            values.append(EpisodeMetadata(f'{task_id}__ep{number:04d}', task_id, split, difficulty, trajectory,
                recovery_types[(number - 1) % len(recovery_types)] if trajectory == 'recovery' else None,
                'ap_00' if difficulty == 'clean' else f'ap_0{1 + (number - 1) % 3}',
                asset_ids[(number - 1) % len(asset_ids)], f'ic_{number:04d}', f'gc_{number:04d}', seed + number).record())
    return {'schema': 'qlm-scaleup-slot-plan-v1', 'task_id': task_id, 'seed': seed,
            'asset_pool': list(asset_ids), 'recovery_types': list(recovery_types),
            'status': 'planned', 'slots': values}


def check_slots(plan, *, accepted=None):
    rows = [EpisodeMetadata(**row).record() for row in plan['slots']]
    task = plan['task_id']
    if len(rows) != 100 or {r['episode_uid'] for r in rows} != {f'{task}__ep{i:04d}' for i in range(1, 101)} or any(r['task_id'] != task for r in rows):
        raise ValueError('Exactly100 unique task episode slots required')
    for field, target in [('difficulty', {'clean': 20, 'randomized': 80}), ('trajectory_type', {'normal': 80, 'recovery': 20}), ('split', {'train': 80, 'validation': 10, 'test': 10})]:
        if dict(Counter(r[field] for r in rows)) != target:
            raise ValueError('Quota mismatch: ' + field)
    for split, count in [('train', 80), ('validation', 10), ('test', 10)]:
        sub = [r for r in rows if r['split'] == split]
        if sum(r['trajectory_type'] == 'recovery' for r in sub) != count // 5 or sum(r['difficulty'] == 'clean' for r in sub) != count // 5:
            raise ValueError('Split margins must be stratified')
    pool = plan['asset_pool']
    if not 2 <= len(pool) <= 3 or len(set(pool)) != len(pool) or not set(r['asset_id'] for r in rows) <= set(pool):
        raise ValueError('Frozen2..3 asset pool required')
    pilot = [r for r in rows if int(r['episode_uid'].split('__ep')[1]) <= 10]
    if {r['asset_id'] for r in pilot} != set(pool) or sum(r['difficulty'] == 'clean' for r in pilot) != 2 or sum(r['trajectory_type'] == 'recovery' for r in pilot) != 2:
        raise ValueError('Ten pilot slots must cover assets and margins')
    enum = set(plan['recovery_types'])
    if any(r['recovery_type'] not in enum for r in rows if r['trajectory_type'] == 'recovery'):
        raise ValueError('Unknown task recovery type')
    if accepted is not None:
        if len(accepted) != 100 or {r['episode_uid'] for r in accepted} != {r['episode_uid'] for r in rows}:
            raise ValueError('Incomplete accepted dataset')
        identities = set()
        expected = {r['episode_uid']: r for r in rows}
        for result in accepted:
            uid = result['episode_uid']
            if result.get('status') != 'success' or result.get('validation_passed') is not True:
                raise ValueError('Only completely validated successful demonstrations are admitted')
            if result.get('metadata') != expected[uid]:
                raise ValueError('Accepted metadata differs from frozen slot')
            source = result.get('source_identity_sha256')
            if not re.fullmatch(r'[0-9a-f]{64}', str(source)) or source in identities:
                raise ValueError('Unique historical/new source hash required')
            identities.add(source)
    return {'passed': True, 'task_id': task, 'slots': 100, 'accepted_complete': accepted is not None}


class SlotAttempts:
    """Initial attempt plus three retries; logs are separate from demonstrations."""
    def __init__(self, metadata, log_path):
        self.metadata = EpisodeMetadata(**metadata).record()
        self.log_path = Path(log_path)
        self.index = 0
        self.accepted = False
        self.pending = False
        self.identity = hashlib.sha256(json.dumps(self.metadata, sort_keys=True).encode()).hexdigest()
        if self.log_path.exists():
            rows = [json.loads(line) for line in self.log_path.read_text().splitlines() if line]
            rows = [row for row in rows if row['episode_slot'] == self.metadata['episode_uid']]
            if any(row.get('slot_metadata_sha256') != self.identity for row in rows):
                raise ValueError('Retry cannot change frozen slot metadata')
            if rows:
                self.index = rows[-1]['attempt_index']
                self.accepted = rows[-1]['status'] == 'accepted'
                if rows[-1]['status'] == 'running':
                    self.pending = True
                    self.finish('interrupted', reason='previous process interrupted')

    def _append(self, row):
        row['slot_metadata_sha256'] = self.identity
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open('a') as stream:
            stream.write(json.dumps(row, allow_nan=False) + '\n')

    def begin(self):
        if self.pending or self.accepted or self.index >= 4:
            raise ValueError('Attempt pending, accepted or exhausted')
        self.index += 1
        self.pending = True
        self._append(dict(task_id=self.metadata['task_id'], episode_slot=self.metadata['episode_uid'],
                          attempt_index=self.index, status='running', short_failure_reason=''))
        return f"{self.metadata['episode_uid']}__a{self.index:02d}"

    def finish(self, outcome, *, validation_passed=False, reason=''):
        if not self.pending or outcome not in ('success', 'timeout', 'fall', 'task_failure', 'runtime_error', 'interrupted'):
            raise ValueError('Pending attempt and explicit outcome required')
        self.pending = False
        self.accepted = outcome == 'success' and validation_passed is True
        if outcome == 'success' and not self.accepted:
            outcome = 'runtime_error'
            reason = reason or 'validation failed'
        exhausted = not self.accepted and self.index == 4
        archive = 'local_full_failure' if outcome in ('timeout', 'fall', 'task_failure') else 'lightweight_log'
        if exhausted:
            archive = 'local_failure_video_and_report'
        row = dict(task_id=self.metadata['task_id'], episode_slot=self.metadata['episode_uid'],
                   attempt_index=self.index, outcome=outcome, short_failure_reason=reason,
                   status='accepted' if self.accepted else ('exhausted' if exhausted else 'retry'),
                   archive=archive, eligible_demonstration=self.accepted, report_to_user=exhausted)
        self._append(row)
        return row
