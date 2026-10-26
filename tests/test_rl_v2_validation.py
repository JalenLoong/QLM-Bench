"""Held-out membership and reset provenance checks; no simulation."""
import copy
import json
from pathlib import Path
import pytest
from qlm_bench.rl_v2.validation import read_cases
from qlm_bench.backends.mujoco.rl_v2.storage import sha256


def fixture(tmp_path,task='push_box'):
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
    p=tmp_path/'validation.json';p.write_text(json.dumps(record));return p,record


def test_exact_held_out_membership(tmp_path):
    p,r=fixture(tmp_path);assert len(read_cases(p)['episodes'])==10


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
