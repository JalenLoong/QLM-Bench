from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import pytest
from qlm_bench.backends.mujoco.training_control import EpisodeSchedule,profile,read_profile,TRAIN_HORIZONS
from qlm_bench.backends.mujoco.training_pool import TASKS,HORIZONS


def make(tmp_path,name='schedule.sqlite'):
    pool={'episodes':[{'task':t,'episode_uid':t+'-'+str(i)} for t in TASKS for i in range(80)]}
    return EpisodeSchedule.create(tmp_path/name,profile('pool'),pool,'segment'),pool


def test_concurrent_reservations_confirmed_starts_and_cap(tmp_path):
    s,_=make(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as workers:
        tickets=list(workers.map(lambda rank:s.reserve('segment',rank,0),range(8)))
    assert len({v['task'] for v in tickets})==8
    assert sum(s.snapshot()['confirmed'].values())==0
    for v in tickets:
        assert s.reserve('segment',v['stream'],0)==v
        s.confirm(v['id']);s.confirm(v['id'])
    assert sum(s.snapshot()['confirmed'].values())==8
    s.finish(tickets[0]['id'],natural=True)
    t=s.reserve('segment',tickets[0]['stream'],1)
    assert t['task'] not in {v['task'] for v in tickets}
    # Global selection uses confirmed starts, not rank-strided indices.
    s.confirm(t['id']);s.finish(t['id'],natural=True)
    t2=s.reserve('segment',tickets[0]['stream'],2)
    assert t2['task'] not in {v['task'] for v in tickets}|{t['task']}
    with pytest.raises(ValueError,match='Stale'):s.reserve('old',0,3)
    capped,_=make(tmp_path,'cap.sqlite')
    for i in range(20):capped.reserve('segment',i,0)
    assert all(sum(v['task']==t for v in capped.snapshot()['tickets'].values())==2 for t in TASKS)
    with pytest.raises(RuntimeError,match='eligible'):capped.reserve('segment',20,0)


def test_cancel_does_not_consume_deck_stop_and_portable_resume(tmp_path):
    s,pool=make(tmp_path)
    a=s.reserve('segment',0,0);b=s.reserve('segment',1,0)
    s.confirm(a['id']);s.cancel(b['id'])
    assert sum(s.snapshot()['confirmed'].values())==1
    assert b['episode_uid'] not in s.snapshot()['used'][b['task']]
    pending=s.reserve('segment',2,0)
    snapshot=s.snapshot();s.stop()
    with pytest.raises(ValueError,match='stopped'):s.reserve('segment',3,0)
    results=[]
    for name in ('moved-a.sqlite','moved-b.sqlite'):
        target=EpisodeSchedule.create(tmp_path/name,profile('pool'),pool,'new')
        target.restore(json.loads(json.dumps(snapshot)),'new')
        recovered=target.snapshot()
        assert recovered['confirmed']==snapshot['confirmed']
        assert all(t['status'] not in ('active','reserved') for t in recovered['tickets'].values())
        assert recovered['tickets'][pending['id']]['status']=='cancelled'
        choices=[]
        for i in range(25):
            t=target.reserve('new',0,i);choices.append((t['task'],t['episode_uid']))
            target.confirm(t['id']);target.finish(t['id'],natural=True)
        results.append(choices)
    assert results[0]==results[1]
    with pytest.raises(ValueError,match='profile'):s.validate({**snapshot,'profile_sha256':'wrong'})


def test_profile_horizons_are_separate_from_immutable_pool(tmp_path):
    assert (HORIZONS['push_box'],HORIZONS['close_oven_door'],HORIZONS['open_room_door'])==(24,60,60)
    assert (TRAIN_HORIZONS['push_box'],TRAIN_HORIZONS['close_oven_door'],TRAIN_HORIZONS['open_room_door'])==(19.2,32,40)
    p=tmp_path/'profile.json';p.write_text(json.dumps(profile('pool')))
    assert read_profile(p,'pool')==profile('pool')
    with pytest.raises(ValueError,match='profile'):read_profile(p,'other')
    changed=deepcopy(profile('pool'));changed['training_horizons_s']['push_box']=24;p.write_text(json.dumps(changed))
    with pytest.raises(ValueError,match='horizons'):read_profile(p,'pool')


def test_shuffle_deck_consumption_no_repeat_before_cycle(tmp_path):
    s,_=make(tmp_path)
    seen={t:set() for t in TASKS}
    for i in range(810):
        t=s.reserve('segment',0,i);before=s.snapshot()
        assert t['task']==min(TASKS,key=lambda name:before['confirmed'][name]) or before['confirmed'][t['task']]==min(before['confirmed'].values())
        if t['cycle']==0:
            assert t['episode_uid'] not in seen[t['task']];seen[t['task']].add(t['episode_uid'])
        s.confirm(t['id']);s.finish(t['id'],natural=True)
    assert all(len(v)==80 for v in seen.values())
    assert set(s.snapshot()['confirmed'].values())=={81}


def _reserve_process(args):
    path,rank=args
    return EpisodeSchedule(path,profile('pool')).reserve('segment',rank,0)


def test_eight_processes_share_one_ledger(tmp_path):
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    s,_=make(tmp_path)
    with ProcessPoolExecutor(max_workers=8,mp_context=multiprocessing.get_context('spawn')) as workers:
        tickets=list(workers.map(_reserve_process,[(str(s.path),rank) for rank in range(8)]))
    assert len({t['task'] for t in tickets})==8
    assert len({t['episode_uid'] for t in tickets})==8
    for ticket in tickets:s.confirm(ticket['id'])
    assert sum(s.snapshot()['confirmed'].values())==8


def test_pending_last_candidate_does_not_abort_other_stream(tmp_path):
    s,_=make(tmp_path)
    # Reach the real 80-item deck boundary with one task still at 79 starts.
    for i in range(799):
        ticket=s.reserve('segment',0,i)
        s.confirm(ticket['id']);s.finish(ticket['id'],natural=True)
    pending=s.reserve('segment',0,799)
    assert s.snapshot()['confirmed'][pending['task']]==79
    # A second worker arrives while the last reset RPC is outstanding. Other
    # tasks can start their next cycle, so this must not terminate training.
    other=s.reserve('segment',1,0)
    assert other['task']!=pending['task']
    assert other['cycle']==1
    assert s.snapshot()['confirmed'][pending['task']]==79
    # Failed reset leaves that candidate available; no start is invented.
    s.cancel(pending['id'])
    retry=s.reserve('segment',0,800)
    assert (retry['task'],retry['episode_uid'])==(pending['task'],pending['episode_uid'])
    s.confirm(retry['id']);s.confirm(other['id'])
    s.validate(s.snapshot())
