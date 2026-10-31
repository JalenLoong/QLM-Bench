"""Held-out membership, reset provenance and (case, seed) rollout bookkeeping checks; no simulation."""
import copy
import json
from pathlib import Path
import pytest
from qlm_bench.rl_v2.validation import read_cases,parse_rollouts
from qlm_bench.backends.mujoco.rl_v2.storage import sha256


def fixture(tmp_path,task='push_box',seeds=None):
    """seeds None writes a v1 record (policy_seed 42); a list writes a v2 record (policy_seeds)."""
    payload=tmp_path/'payload';manifest=payload/'releases/push/manifest.json';manifest.parent.mkdir(parents=True)
    cases=[];rows=[]
    for i in range(10):
        uid=f'val-{i}';trace=payload/'physical'/uid/'source-trace-manifest.json';trace.parent.mkdir(parents=True)
        model=trace.parent/'scene.xml';model.write_text('<mujoco/>')
        from qlm_bench.backends.mujoco.resources import resource_closure
        scene={'model':'/retired/host/scene.xml','seed':i}
        trace.write_text(json.dumps({'scene':scene,'model_identity':resource_closure(model)['identity']}))
        rows.append({'episode_uid':uid,'task':task,'split':'validation','snapshot_bundle':f'physical/{uid}/bundle.json','source_trace_manifest_sha256':sha256(trace)})
        cases.append({'demo_uid':uid,'scene':scene,'model':str(model),'instruction':'Push','split':'validation'})
    manifest.write_text(json.dumps({'episodes':rows}))
    split=tmp_path/'split.json';split.write_text(json.dumps({'episodes':{'train':['train'],'validation':[c['demo_uid'] for c in cases],'test':['test']}}))
    prompt=tmp_path/'prompt.json';prompt.write_text(json.dumps({'prompts':{task:'Push'}}))
    record={'schema':'qlm-rl-v2-validation-v1','task_id':task,'episodes':cases,'policy_seed':42,'horizon_seconds':60,
            'split_path':str(split),'split_sha256':sha256(split),'release_manifest':str(manifest),'release_manifest_sha256':sha256(manifest),
            'prompt_path':str(prompt),'prompt_sha256':sha256(prompt)}
    if seeds is not None:del record['policy_seed'];record.update(schema='qlm-rl-v2-validation-v2',policy_seeds=seeds)
    p=tmp_path/'validation.json';p.write_text(json.dumps(record));return p,record


def fake_run_case(record,case,controller,port,seed,**kw):
    success=case['scene']['seed']%2==0 if seed==42 else case['scene']['seed']<3
    return {'demo_uid':case['demo_uid'],'policy_seed':seed,'outcome':{'success':success,'fallen':False,'timed_out':False,'progress':.1},'simulation_time_ns':1,'renderer':{}}


def test_exact_held_out_membership(tmp_path):
    p,r=fixture(tmp_path);record=read_cases(p);assert len(record['episodes'])==10 and record['policy_seeds']==[42] and record['policy_seed']==42


def test_v2_record_normalises_distinct_policy_seeds_starting_at_42(tmp_path):
    p,r=fixture(tmp_path,seeds=[42,7,1234]);record=read_cases(p)
    assert record['policy_seeds']==[42,7,1234] and 'policy_seed' not in record and record['schema']=='qlm-rl-v2-validation-v2'
    for seeds in ([7,42],[42,42],[42,7,7],[42,-1],[42,'7'],[42,True],[42,7.],[],None,42):
        r['policy_seeds']=seeds;p.write_text(json.dumps(r))
        with pytest.raises(ValueError):read_cases(p)
    del r['policy_seeds'];p.write_text(json.dumps(r))
    with pytest.raises(ValueError):read_cases(p)
    r['policy_seeds']=[42,7];r['horizon_seconds']=30;p.write_text(json.dumps(r))
    with pytest.raises(ValueError):read_cases(p)
    r['horizon_seconds']=60;r['schema']='qlm-rl-v2-validation-v3';p.write_text(json.dumps(r))
    with pytest.raises(ValueError):read_cases(p)


@pytest.mark.parametrize('change',['train','duplicate','scene','prompt','seed'])
def test_invalid_validation_identity_rejected(tmp_path,change):
    p,r=fixture(tmp_path)
    if change=='train':r['episodes'][0]['demo_uid']='train'
    if change=='duplicate':r['episodes'][0]=copy.deepcopy(r['episodes'][1])
    if change=='scene':r['episodes'][0]['scene']['seed']=999
    if change=='prompt':r['episodes'][0]['instruction']='Other task'
    if change=='seed':r['policy_seed']=43
    p.write_text(json.dumps(r))
    with pytest.raises(ValueError):read_cases(p)


def test_sweep_membership_cannot_be_read_as_push(tmp_path):
    p,r=fixture(tmp_path,task='sweep_block_to_zone')
    assert read_cases(p)['task_id']=='sweep_block_to_zone'
    r['task_id']='push_box';p.write_text(json.dumps(r))
    with pytest.raises((ValueError,KeyError)):read_cases(p)


def test_run_case_binds_the_seed_to_the_session_and_row(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from qlm_bench.rl_v2 import validation
    p,r=fixture(tmp_path,seeds=[42,7]);record=read_cases(p);seen=[]
    case={**record['episodes'][0],'scene':{**record['episodes'][0]['scene'],'initial_state':{'qpos':[0.]}}}
    class Runtime:
        profile={'asset_profile':'x'};outcome={'success':True,'fallen':False,'timed_out':False,'progress':.2}
        renderer=SimpleNamespace(observer_clip=1,evaluation_observer=False,gl_identity={'renderer':'llvmpipe (LLVM)'})
        def set_case_seed(self,seed):self.case_seed=seed
        def reset(self,initial_state=None):self.initial_state=initial_state
        def state(self):return {'physics_step':0,'simulation_time_ns':0,'reset_epoch':1}
        def close(self):self.closed=True
    class Driver:
        def __init__(self,rt,client,**kw):seen.append(kw['session_id'])
        def reset_episode(self,episode_id,*,policy_seed,initial_snapshot=None):seen.append((episode_id,policy_seed))
        def run_episode(self):return {'task_terminal':True,'simulation_time_ns':640_000_000}
    monkeypatch.setattr('qlm_bench.backends.factory.create_runtime',lambda *a,**k:Runtime())
    monkeypatch.setattr('qlm_bench.live.SynchronousDriver',Driver);monkeypatch.setattr('qlm_bench.live.RPCClient',lambda port:port)
    rows=[validation.run_case(record,case,'ctrl',5,seed) for seed in (42,7)]
    assert seen==['rl-validation-val-0-s42',('val-0',42),'rl-validation-val-0-s7',('val-0',7)]
    assert [set(x) for x in rows]==[{'demo_uid','policy_seed','outcome','simulation_time_ns','renderer'}]*2
    assert [x['policy_seed'] for x in rows]==[42,7] and rows[0]['outcome']['progress']==.2 and rows[0]['simulation_time_ns']==640_000_000


def test_rollouts_write_per_seed_rows_and_result_only_for_the_full_set(tmp_path,monkeypatch):
    from qlm_bench.rl_v2 import validation
    p,r=fixture(tmp_path,seeds=[42,7]);monkeypatch.setattr(validation,'_cpu_only',lambda:None);monkeypatch.setattr(validation,'run_case',fake_run_case)
    subset=validation.run(p,'ctrl',1,tmp_path/'subset',[(7,7),(3,42)])
    assert sorted(x.name for x in (tmp_path/'subset').iterdir())==['subset.json','val-3-seed42.json','val-7-seed7.json']
    assert subset['schema']=='qlm-rl-v2-validation-subset-v2' and subset['rollouts']==[[7,7],[3,42]] and subset['task_id']=='push_box'
    assert [(o['demo_uid'],o['policy_seed']) for o in subset['outcomes']]==[('val-7',7),('val-3',42)] and subset['cases_sha256']==sha256(p)
    assert set(subset)=={'schema','task_id','rollouts','outcomes','cases_sha256'} and json.loads((tmp_path/'subset/subset.json').read_text())==subset
    row=json.loads((tmp_path/'subset/val-7-seed7.json').read_text())
    assert set(row)=={'demo_uid','policy_seed','outcome','simulation_time_ns','renderer'} and row['policy_seed']==7 and row['demo_uid']=='val-7'
    full=validation.run(p,'ctrl',1,tmp_path/'full')
    names=sorted(x.name for x in (tmp_path/'full').iterdir())
    assert names==sorted(['result.json']+[f'val-{i}-seed{s}.json' for s in (42,7) for i in range(10)])
    assert set(full)=={'passed','schema','task_id','split','GT_actor_visible','cases_sha256','policy_seeds','outcomes','success_rate','per_seed_success_rate'}
    assert full['passed'] is True and full['schema']=='qlm-rl-v2-validation-result-v2' and full['split']=='validation' and full['GT_actor_visible'] is False
    assert full['policy_seeds']==[42,7] and full['cases_sha256']==sha256(p) and full['task_id']=='push_box'
    assert [(o['policy_seed'],o['demo_uid']) for o in full['outcomes']]==[(s,f'val-{i}') for s in (42,7) for i in range(10)]
    assert full['success_rate']==.4 and full['per_seed_success_rate']=={'42':.5,'7':.3}
    assert json.loads((tmp_path/'full/result.json').read_text())==full
    shuffled=[(i,s) for i in range(9,-1,-1) for s in (7,42)]
    explicit=validation.run(p,'ctrl',1,tmp_path/'explicit',shuffled)
    assert explicit==full and (tmp_path/'explicit/result.json').is_file() and not (tmp_path/'explicit/subset.json').exists()


def test_single_seed_record_still_uses_seed_suffixed_rows(tmp_path,monkeypatch):
    from qlm_bench.rl_v2 import validation
    p,r=fixture(tmp_path);monkeypatch.setattr(validation,'_cpu_only',lambda:None);monkeypatch.setattr(validation,'run_case',fake_run_case)
    full=validation.run(p,'ctrl',1,tmp_path/'full')
    names=sorted(x.name for x in (tmp_path/'full').iterdir())
    assert names==sorted(['result.json']+[f'val-{i}-seed42.json' for i in range(10)]) and 'val-0.json' not in names
    assert full['policy_seeds']==[42] and full['success_rate']==.5 and full['per_seed_success_rate']=={'42':.5} and [o['policy_seed'] for o in full['outcomes']]==[42]*10
    subset=validation.run(p,'ctrl',1,tmp_path/'subset',[(7,42),(3,42)])
    assert subset['rollouts']==[[7,42],[3,42]] and sorted(x.name for x in (tmp_path/'subset').iterdir())==['subset.json','val-3-seed42.json','val-7-seed42.json']


def test_case_indices_alias_and_invalid_rollouts_fail_before_output(tmp_path,monkeypatch):
    from qlm_bench.rl_v2 import validation
    p,r=fixture(tmp_path,seeds=[42,7]);monkeypatch.setattr(validation,'_cpu_only',lambda:None);monkeypatch.setattr(validation,'run_case',fake_run_case)
    subset=validation.run(p,'ctrl',1,tmp_path/'alias',case_indices=[7,3])
    assert subset['rollouts']==[[7,42],[3,42],[7,7],[3,7]] and len(list((tmp_path/'alias').iterdir()))==5
    assert validation.run(p,'ctrl',1,tmp_path/'alias-full',case_indices=list(range(10)))['schema']=='qlm-rl-v2-validation-result-v2'
    for i,bad in enumerate(([],[(3,42),(3,42)],[(10,42)],[('3',42)],[(-1,42)],[(3,5)],[(3,True)],[(3,'42')],[(3,)],[3],[(3,42,7)])):
        with pytest.raises(ValueError):validation.run(p,'ctrl',1,tmp_path/f'bad{i}',bad)
    for i,bad in enumerate(([],[3,3],[10],['3'],[-1])):
        with pytest.raises(ValueError):validation.run(p,'ctrl',1,tmp_path/f'badalias{i}',case_indices=bad)
    with pytest.raises(ValueError):validation.run(p,'ctrl',1,tmp_path/'both',[(3,42)],case_indices=[3])
    assert not any(x.name.startswith('bad') or x.name=='both' for x in tmp_path.iterdir())


def test_visualize_runs_the_first_seed_with_the_observer(tmp_path,monkeypatch):
    from qlm_bench.rl_v2 import validation
    p,r=fixture(tmp_path,seeds=[42,7]);monkeypatch.setattr(validation,'_cpu_only',lambda:None);seen=[]
    def fake(record,case,controller,port,seed,*,on_observation=None,observer=False):
        seen.append((case['demo_uid'],seed,observer,on_observation is not None));return fake_run_case(record,case,controller,port,seed)
    monkeypatch.setattr(validation,'run_case',fake)
    row=validation.visualize(p,3,'ctrl',1,tmp_path/'vis')
    assert seen==[('val-3',42,True,True)] and row['policy_seed']==42 and row['case_index']==3 and row['observer_view']=='evaluation_observer'
    assert json.loads((tmp_path/'vis/result.json').read_text())==row and (tmp_path/'vis/observer').is_dir()


def test_cli_rollouts_and_case_indices_alias(monkeypatch,capsys):
    from qlm_bench.rl_v2 import validation
    calls=[];monkeypatch.setattr(validation,'run',lambda *a,**k:calls.append((a,k)))
    base=['validation','--cases','v.json','--controller','c','--port','5','--output','o']
    monkeypatch.setattr('sys.argv',base+['--rollouts','0:42,4:7,9:0']);validation.main()
    monkeypatch.setattr('sys.argv',base+['--case-indices','0,4']);validation.main()
    monkeypatch.setattr('sys.argv',base);validation.main()
    assert calls==[(('v.json','c',5,'o',[(0,42),(4,7),(9,0)]),{'case_indices':None}),(('v.json','c',5,'o',None),{'case_indices':[0,4]}),(('v.json','c',5,'o',None),{'case_indices':None})]
    assert parse_rollouts('3:42')==[(3,42)]
    for bad in ('','0:42,','0:42,x','0-42','0:42;1:42','0:42, 1:42','a:b','0:','01:42','0:042','0:4 2','0:-1','+0:42','0:42:7'):
        with pytest.raises(ValueError,match='Malformed rollout'):parse_rollouts(bad)
        monkeypatch.setattr('sys.argv',base+['--rollouts',bad])
        with pytest.raises(SystemExit):validation.main()
        assert 'Malformed rollout' in capsys.readouterr().err
    for extra in (['--rollouts','0:42','--case-indices','0'],['--case-indices','0,x'],['--case-indices',''],['--visualize-case','1','--rollouts','0:42'],['--visualize-case','1','--case-indices','0']):
        monkeypatch.setattr('sys.argv',base+extra)
        with pytest.raises(SystemExit):validation.main()
    assert len(calls)==3
    shown=[];monkeypatch.setattr(validation,'visualize',lambda *a:shown.append(a))
    monkeypatch.setattr('sys.argv',base+['--visualize-case','2']);validation.main();assert shown==[('v.json',2,'c',5,'o')]
