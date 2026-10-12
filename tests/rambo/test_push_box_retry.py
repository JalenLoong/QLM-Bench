import json
import pytest
from qlm_bench.scaleup import make_slots, SlotAttempts
from rambo.tasks.common.push_box_retry import PushSlotAttempts, attempt_limit, realization_ordinal


def test_renewal_preserves_old_evidence_and_caps_additional_attempts(tmp_path):
    metadata=make_slots('push_box',['box01','box04'],seed=42,recovery_types=['miss'])['slots'][0]
    log=tmp_path/'collection-log.jsonl';original=SlotAttempts(metadata,log)
    for _ in range(4):
        original.begin();original.finish('runtime_error',reason='asset missing before actions')
    prior=log.read_bytes()
    with pytest.raises(ValueError):realization_ordinal(tmp_path,metadata,5)
    (tmp_path/'retry-budget-renewal.json').write_text(json.dumps({
        'schema':'push-box-retry-renewal-v1','authorization':'user_continue_retry',
        'slots':{metadata['episode_uid']:{'metadata':metadata,'base_attempt_index':4,'additional_attempts':3}}}))
    assert attempt_limit(tmp_path,metadata)==7
    assert realization_ordinal(tmp_path,metadata,5)==1
    assert realization_ordinal(tmp_path,metadata,7)==3
    for index in (5,6,7):
        # Real process restarts continue the same append-only ledger.
        renewed=PushSlotAttempts(metadata,log,limit=attempt_limit(tmp_path,metadata))
        assert renewed.begin().endswith(f'__a{index:02d}')
        report=renewed.finish('timeout')
        assert report['report_to_user']==(index==7)
        assert not report['eligible_demonstration']
    assert log.read_bytes().startswith(prior)
    with pytest.raises(ValueError,match='exhausted'):renewed.begin()
    with pytest.raises(ValueError):realization_ordinal(tmp_path,metadata,8)
    with pytest.raises(ValueError,match='frozen slot'):attempt_limit(tmp_path,dict(metadata,asset_id='changed'))


def test_renewed_success_still_needs_validation_and_is_terminal(tmp_path):
    metadata=make_slots('push_box',['box01','box04'],seed=42,recovery_types=['miss'])['slots'][0]
    log=tmp_path/'collection-log.jsonl';attempt=PushSlotAttempts(metadata,log,limit=7)
    for _ in range(4):attempt.begin();attempt.finish('runtime_error')
    attempt.begin();assert attempt.finish('success')['status']=='retry'
    attempt.begin();assert attempt.finish('success',validation_passed=True)['status']=='accepted'
    restarted=PushSlotAttempts(metadata,log,limit=7)
    with pytest.raises(ValueError):restarted.begin()
