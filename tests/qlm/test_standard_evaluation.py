"""Regression of held-out suite scheduling and error-only recovery."""
from copy import deepcopy
from dataclasses import replace
import pytest
from test_evaluation_interfaces import case, protocol, runner, FakeRuntime
from qlm_bench.evaluation import validate_result


def test_all_ten_tasks_admit_explicit_cases():
    from qlm_bench.tasks.registration import SCALEUP_TASK_IDS
    for task in SCALEUP_TASK_IDS:
        assert case(task_id=task).task_id == task


def test_task_command_budget_controls_actual_execution():
    p=replace(protocol(budget=8),task_command_budgets={'push_box':2})
    result=runner(p,factory=lambda _:FakeRuntime(outcome=None)).run(submission_id='budget')
    assert result['outcomes'][0]['executed_commands']==2
    assert result['outcomes'][0]['outcome']=='timeout'
    with pytest.raises(ValueError):replace(p,task_command_budgets={'press_button':2})


def test_error_recovery_keeps_error_and_first_valid_failure():
    p=protocol(scope='benchmark',status='verified',error_policy='exclude_and_retry',retry_selection='first_non_error_attempt')
    c=case(status='verified')
    class Broken(FakeRuntime):
        def step(self,command):raise RuntimeError('infrastructure')
    result=runner(p,cases={'case-1':c},factory=lambda _:Broken(),evidence='actual_runtime').run(submission_id='error',benchmark_release='test')
    assert result['validation']['metrics']['status']=='incomplete'
    assert result['validation']['metrics']['per_task']['push_box']['success_rate'] is None
    resumed=runner(p,cases={'case-1':c},factory=lambda _:FakeRuntime(outcome='failure'),evidence='actual_runtime').run(
        submission_id='retry',benchmark_release='test',previous_outcomes=result['outcomes'])
    assert len(resumed['outcomes'])==2
    assert resumed['outcomes'][1]['retry_of']==resumed['outcomes'][0]['attempt_id']
    assert resumed['validation']['metrics']['per_task']['push_box']['success_rate']==0
    final=runner(p,cases={'case-1':c},evidence='actual_runtime').run(submission_id='again',benchmark_release='test',previous_outcomes=resumed['outcomes'])
    assert len(final['outcomes'])==2
    extra=deepcopy(final['outcomes'][-1]);extra.update(attempt_id='selected-success',retry_of=extra['attempt_id'],outcome='success')
    with pytest.raises(ValueError,match='cannot be retried'):
        validate_result(final['run_manifest'],final['outcomes']+[extra])


def test_chunk_execution_strategy_preserves_public_result_checks():
    from qlm_bench.policy_interface import ExecutionHistory
    calls=[]
    def execute(runtime,case,trial,budget):
        calls.append((case.case_id,budget))
        return dict(terminal=runtime.terminal(),history=ExecutionHistory('episode-1',1),simulation_time_ns=0,
                    closed_loop_status='PARTIAL_CLOSED_LOOP')
    r=runner();r.episode_executor=execute
    result=r.run(submission_id='strategy')
    assert calls==[('case-1',3)]
    assert result['run_manifest']['action_scheduling']['mode']=='synchronous_chunk16'
    assert result['outcomes'][0]['closed_loop_status']=='PARTIAL_CLOSED_LOOP'


def test_private_controller_publication_requires_scoped_evidence():
    from qlm_bench.assets import validate_manifest
    m=dict(schema='qlm-resource-manifest-v1',kind='controller',asset_id='controller',version='v1',
        entrypoint='model.pt',cache_subdir='controller/v1',source={},geometry={},physics={},
        files={'model.pt':{'size_bytes':1,'sha256':'a'*64}},dependency_validation={'closed':True},
        license={'redistribution_status':'user_confirmed_private_dataset','scope':'private:dontKnow23456/QLM-Bench',
                 'attribution':'upstream','source_evidence_sha256':'b'*64})
    validate_manifest(m,for_publication=True)
    m['license']['scope']='public'
    with pytest.raises(ValueError):validate_manifest(m,for_publication=True)
