"""Push-owned explicit budget renewal without resetting historical attempts."""
from __future__ import annotations
import json
from pathlib import Path
from qlm_bench.scaleup import SlotAttempts


def renewal_for(root, metadata):
    path = Path(root) / 'retry-budget-renewal.json'
    if not path.exists():
        return None
    value = json.loads(path.read_text())
    if value.get('schema') != 'push-box-retry-renewal-v1' or value.get('authorization') != 'user_continue_retry':
        raise ValueError('Explicit user retry renewal required')
    row = value['slots'].get(metadata['episode_uid'])
    if row is None:
        return None
    if row['metadata'] != metadata or row['base_attempt_index'] != 4 or row['additional_attempts'] != 3:
        raise ValueError('Renewal must preserve the frozen slot and explicit three-attempt budget')
    return row


def attempt_limit(root, metadata):
    row = renewal_for(root, metadata)
    return row['base_attempt_index'] + row['additional_attempts'] if row else 4


def realization_ordinal(root, metadata, index):
    if type(index) is not int or not 1 <= index <= attempt_limit(root, metadata):
        raise ValueError('Attempt outside the explicitly authorized budget')
    row = renewal_for(root, metadata)
    return index - row['base_attempt_index'] if row and index > row['base_attempt_index'] else index


class PushSlotAttempts(SlotAttempts):
    def __init__(self, metadata, log_path, *, limit=4):
        if limit not in (4, 7):
            raise ValueError('Unsupported Push retry limit')
        self.limit = limit
        super().__init__(metadata, log_path)

    def begin(self):
        if self.pending or self.accepted or self.index >= self.limit:
            raise ValueError('Attempt pending, accepted or exhausted')
        self.index += 1
        self.pending = True
        self._append(dict(task_id=self.metadata['task_id'], episode_slot=self.metadata['episode_uid'],
                          attempt_index=self.index, status='running', short_failure_reason='', attempt_limit=self.limit))
        return f"{self.metadata['episode_uid']}__a{self.index:02d}"

    def finish(self, outcome, *, validation_passed=False, reason=''):
        if not self.pending or outcome not in ('success', 'timeout', 'fall', 'task_failure', 'runtime_error', 'interrupted'):
            raise ValueError('Pending attempt and explicit outcome required')
        self.pending = False
        self.accepted = outcome == 'success' and validation_passed is True
        if outcome == 'success' and not self.accepted:
            outcome = 'runtime_error'
            reason = reason or 'validation failed'
        exhausted = not self.accepted and self.index >= self.limit
        archive = 'local_full_failure' if outcome in ('timeout', 'fall', 'task_failure') else 'lightweight_log'
        if exhausted:
            archive = 'local_failure_video_and_report'
        row = dict(task_id=self.metadata['task_id'], episode_slot=self.metadata['episode_uid'],
                   attempt_index=self.index, outcome=outcome, short_failure_reason=reason, attempt_limit=self.limit,
                   status='accepted' if self.accepted else ('exhausted' if exhausted else 'retry'),
                   archive=archive, eligible_demonstration=self.accepted, report_to_user=exhausted)
        self._append(row)
        return row
