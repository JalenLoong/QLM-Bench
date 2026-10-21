from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import pytest
from qlm_bench.scaleup import EpisodeMetadata, make_slots, check_slots, SlotAttempts
from qlm_bench.tasks.registration import SCALEUP_TASK_IDS, registrations, load_registration


@pytest.mark.parametrize('count', [2, 3])
def test_slot_quota_pilot_and_split(count):
    for task in SCALEUP_TASK_IDS:
        plan = make_slots(task, [f'asset_{i}' for i in range(count)], seed=42, recovery_types=['contact_loss', 'miss'])
        assert check_slots(plan)['passed']
        assert plan == make_slots(task, plan['asset_pool'], seed=42, recovery_types=plan['recovery_types'])
        assert len({r['environment_seed'] for r in plan['slots']}) == 100


def test_invalid_labels_quota_and_duplicate_source_rejected():
    plan = make_slots('push_box', ['box01', 'box05'], seed=42, recovery_types=['contact_loss'])
    bad = deepcopy(plan); bad['slots'][0]['trajectory_type'] = 'recovery'
    with pytest.raises(ValueError):
        check_slots(bad)
    bad = deepcopy(plan); bad['slots'][0]['difficulty'] = 'randomized'
    with pytest.raises(ValueError, match='Quota'):
        check_slots(bad)
    accepted = [{'episode_uid': row['episode_uid'], 'metadata': row, 'status': 'success', 'validation_passed': True,
                 'source_identity_sha256': f'{i:064x}'} for i, row in enumerate(plan['slots'])]
    assert check_slots(plan, accepted=accepted)['accepted_complete']
    accepted[-1]['source_identity_sha256'] = accepted[0]['source_identity_sha256']
    with pytest.raises(ValueError, match='Unique'):
        check_slots(plan, accepted=accepted)


def test_retry_four_attempts_stable_uid_archive_and_exhaustion(tmp_path):
    metadata = make_slots('press_button', ['industrial', 'emergency'], seed=42, recovery_types=['miss'])['slots'][0]
    attempts = SlotAttempts(metadata, tmp_path / 'collection.jsonl')
    for i in range(1, 5):
        assert attempts.begin() == 'press_button__ep0001__a' + f'{i:02d}'
        row = attempts.finish('runtime_error', reason='renderer error')
        assert not row['eligible_demonstration']
        assert row['report_to_user'] == (i == 4)
    assert row['archive'] == 'local_failure_video_and_report'
    with pytest.raises(ValueError, match='exhausted'):
        attempts.begin()
    assert len((tmp_path / 'collection.jsonl').read_text().splitlines()) == 8


def test_retry_restart_preserves_budget_and_metadata(tmp_path):
    metadata = make_slots('press_button', ['industrial', 'emergency'], seed=42, recovery_types=['miss'])['slots'][0]
    log = tmp_path / 'log.jsonl'
    attempts = SlotAttempts(metadata, log)
    attempts.begin()
    restarted = SlotAttempts(metadata, log)
    assert restarted.index == 1
    assert restarted.begin().endswith('__a02')
    changed = dict(metadata, asset_id='another')
    with pytest.raises(ValueError, match='frozen slot'):
        SlotAttempts(changed, log)


def test_true_failure_local_and_success_needs_validation(tmp_path):
    metadata = make_slots('press_button', ['industrial', 'emergency'], seed=42, recovery_types=['miss'])['slots'][0]
    attempts = SlotAttempts(metadata, tmp_path / 'log.jsonl')
    attempts.begin(); assert attempts.finish('fall')['archive'] == 'local_full_failure'
    attempts.begin(); assert attempts.finish('success')['status'] == 'retry'
    attempts.begin(); assert attempts.finish('success', validation_passed=True)['eligible_demonstration']
    with pytest.raises(ValueError):
        attempts.begin()


def test_planned_tasks_fail_closed_without_importing_simulator():
    rows = registrations()
    assert len(rows) == 10
    assert sum(r['status'] == 'ready' for r in rows.values()) == 3
    with pytest.raises(ValueError, match='planned'):
        load_registration('turn_valve', ready=True)
    code = "from qlm_bench.tasks.registration import registrations; from qlm_bench.scaleup import make_slots; import sys; assert not set(sys.modules)&{'torch','isaaclab','isaacsim','omni','wam_policy'}"
    subprocess.run([sys.executable, '-c', code], check=True)


def test_frozen_snapshot_roundtrip(tmp_path):
    from qlm_bench.scaleup.source import freeze_snapshot, apply_snapshot
    root = tmp_path / 'source'; root.mkdir()
    subprocess.run(['git', '-C', str(root), 'init', '-q'], check=True)
    (root / 'tracked.txt').write_text('base')
    subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(root), '-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], check=True)
    (root / 'tracked.txt').write_text('changed')
    (root / 'new.txt').write_text('new')
    snapshot = tmp_path / 'snapshot'; record = freeze_snapshot(root, snapshot)
    other = tmp_path / 'other'
    subprocess.run(['git', 'clone', '-q', str(root), str(other)], check=True)
    assert apply_snapshot(other, snapshot)['passed']
    assert (other / 'new.txt').read_text() == 'new'
    assert (other / 'tracked.txt').read_text() == 'changed'
