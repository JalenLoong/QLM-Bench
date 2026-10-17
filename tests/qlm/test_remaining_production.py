"""Fresh100 admission must preserve quotas/support and fail closed on metadata."""
import copy
from collections import Counter
from types import SimpleNamespace
import numpy as np
import pytest

from qlm_bench.backends.mujoco.remaining_tasks import TASKS
from qlm_bench.backends.mujoco.remaining_scenes import SUPPORT
from qlm_bench.backends.mujoco.remaining_production import candidates
from qlm_bench.backends.mujoco.native_production import NativeProductionQueue
from qlm_bench.backends.factory import backend_binding
from qlm_bench.compatibility.dataset_v2.pilot_rendition import load_remaining_profile,REMAINING_PRODUCTION_SCHEMA
from qlm_bench.compatibility.dataset_v2.validation import digest


@pytest.mark.parametrize('task',TASKS)
def test_fresh100_support_and_split_isolation(task):
    rows=candidates(task)
    assert len(rows)==100
    assert Counter((s['split'],s['difficulty']) for s in rows)=={
        ('train','clean'):16,('train','randomized'):64,('validation','clean'):2,
        ('validation','randomized'):8,('test','clean'):2,('test','randomized'):8}
    lo,hi,_=map(np.asarray,SUPPORT[task]);prior=[]
    for slot in rows:
        assert len(slot['candidates'])==5
        if slot['difficulty']=='clean':assert slot['appearance_preset']=='ap_00'
        for candidate in slot['candidates']:
            p=np.array(candidate['configuration_parameters'])
            assert np.all(p>=lo) and np.all(p<=hi) and candidate['seed']==42
            assert all(not np.array_equal(p,q) and (split==slot['split'] or not np.all(abs(p-q)<=(hi-lo)*.005)) for q,split in prior)
            prior.append((p,slot['split']))
    for split in ('train','validation','test'):
        p=np.array([s['candidates'][0]['configuration_parameters'] for s in rows if s['split']==split and s['difficulty']=='randomized'])
        # Each split spans both halves of each full ID interval.
        assert np.all(p.min(axis=0)<(lo+hi)/2) and np.all(p.max(axis=0)>(lo+hi)/2)
    assert rows[0]['difficulty']=='clean' and rows[1]['difficulty']=='randomized'


def test_zero_retained_pilots_count_and_backend_boundary():
    queue=SimpleNamespace(state={'retained_pilots':0,'slots':{'a':{'status':'accepted'},'b':{'status':'planned'}}})
    assert NativeProductionQueue.accepted(queue)==1
    for task in TASKS:
        assert backend_binding(task,'native')['approved_six']
        with pytest.raises(ValueError):backend_binding(task,'isaac')


def test_remaining_profile_requires_real_approval_and_whole_episode_membership():
    p=dict(schema=REMAINING_PRODUCTION_SCHEMA,task_id=TASKS[0],rgb_profile='dual-rgb-360p-v1',maximum_render_attempts=3,
        production_authorization=dict(remaining_six_approved=True,target_accepted=100),campaign_sha256='campaign',
        approval=dict(reference_quality_approved=True,retarget_scope_approved=True,evidence_sha256='receipt'),
        quality_policy='evidence-review-v1',slots=[dict(task_id=TASKS[0],difficulty='clean',appearance_preset='ap_00',
        split='test',review_status='approved_task_recipe_technical_quality',quality_review_sha256='actual-evidence')])
    def signed(d):d=copy.deepcopy(d);d['profile_sha256']=digest(d);return d
    assert load_remaining_profile(signed(p))['slots'][0]['split']=='test'
    for mutate in (lambda d:d['approval'].update(retarget_scope_approved=False),
                   lambda d:d['production_authorization'].update(target_accepted=90),
                   lambda d:d['slots'][0].update(appearance_preset='ap_01'),
                   lambda d:d['slots'][0].update(split='frame_split')):
        d=copy.deepcopy(p);mutate(d)
        with pytest.raises(ValueError):load_remaining_profile(signed(d))


@pytest.mark.parametrize('task',TASKS)
def test_actual_approved_executor_import_and_inheritance_before_physics(task):
    pytest.importorskip('torch')
    pytest.importorskip('mujoco')
    from qlm_bench.backends.mujoco.remaining_runtime import ApprovedExpert
    executor=ApprovedExpert(task)
    assert callable(executor.command) and callable(executor.reset)
    if task=='pull_open_drawer':
        assert 'DrawerFixtureExecutor' in [c.__name__ for c in type(executor).__mro__]
        assert type(executor).__name__=='DrawerFixtureHeadingExecutor'
    if task=='open_room_door':
        assert type(executor).__name__=='DoorSlowExpertApprovedV3'
