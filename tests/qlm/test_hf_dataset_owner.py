"""Offline regressions: every live Hub request uses the transferred namespace."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType,SimpleNamespace
import pytest
from qlm_bench.hub import DATASET_REPO_ID,LEGACY_DATASET_REPO_ID,dataset_repo_id


@pytest.fixture
def hub(monkeypatch):
    calls=[];store={}
    class File:
        def __init__(self,path,content):
            self.path=path;self.size=len(content);self.lfs=None
            self.blob_id=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
    class API:
        def dataset_info(self,repo_id,**kwargs):calls.append(('dataset_info',repo_id));return SimpleNamespace(sha='a'*40,private=False)
        def list_repo_tree(self,repo_id,**kwargs):calls.append(('list_repo_tree',repo_id));return [File(n,b) for n,b in store.items()]
        def create_commit(self,repo_id,**kwargs):
            calls.append(('create_commit',repo_id))
            for op in kwargs['operations']:store[op.path_in_repo]=Path(op.path_or_fileobj).read_bytes()
            return SimpleNamespace(oid='b'*40)
    def download(repo_id,name,**kwargs):
        calls.append(('download',repo_id));path=Path(kwargs['local_dir'])/name
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{"case_ids":[]}');return str(path)
    api=API();module=ModuleType('huggingface_hub');sub=ModuleType('huggingface_hub.hf_api')
    module.HfApi=lambda **kwargs:api;module.hf_hub_download=download;module.CommitOperationAdd=lambda **kwargs:SimpleNamespace(**kwargs)
    sub.RepoFile=File;module.hf_api=sub
    monkeypatch.setitem(sys.modules,'huggingface_hub',module);monkeypatch.setitem(sys.modules,'huggingface_hub.hf_api',sub)
    return SimpleNamespace(api=api,calls=calls,store=store)


def test_hub_inspect_default_explicit_legacy_and_cli_route_to_new_owner(hub,capsys):
    from qlm_bench.publication import REPO_ID,read_hub_state
    from qlm_bench.cli import main
    assert REPO_ID==DATASET_REPO_ID
    assert read_hub_state()['repo_id']==DATASET_REPO_ID
    assert read_hub_state(LEGACY_DATASET_REPO_ID)['repo_id']==DATASET_REPO_ID
    main(['hub-inspect'])
    assert json.loads(capsys.readouterr().out)['repo_id']==DATASET_REPO_ID
    assert all(repo==DATASET_REPO_ID for _,repo in hub.calls)


@pytest.mark.parametrize('requested',[DATASET_REPO_ID,LEGACY_DATASET_REPO_ID])
def test_case_fetch_uses_new_owner_and_keeps_revision(tmp_path,hub,requested):
    from qlm_bench.backends.mujoco.suite import fetch_case
    with pytest.raises(ValueError,match='outside the frozen suite'):
        fetch_case('a'*40,'fixture',tmp_path/'download',repo_id=requested)
    assert hub.calls==[('download',DATASET_REPO_ID)]


def test_old_staged_inventory_upload_routes_to_new_owner_without_rewriting_payload(tmp_path,hub,monkeypatch):
    from qlm_bench.publication import legacy_core as publisher
    stage=tmp_path/'stage';stage.mkdir();payload=stage/'payload.json';payload.write_text('{"historical":"unchanged"}')
    inventory=tmp_path/'inventory.json';inventory.write_text(json.dumps({'repo_id':LEGACY_DATASET_REPO_ID,'release':'fixture',
        'work_id':'DATA-012','files':{'payload.json':publisher.describe(payload)}}))
    before=inventory.read_bytes();report=tmp_path/'report.json'
    monkeypatch.setattr(sys,'argv',['publisher','upload','--stage',str(stage),'--inventory',str(inventory),'--report',str(report)])
    publisher.main()
    assert ('create_commit',DATASET_REPO_ID) in hub.calls and all(repo==DATASET_REPO_ID for _,repo in hub.calls)
    assert inventory.read_bytes()==before and hub.store['payload.json']==payload.read_bytes()
    assert json.loads(report.read_text())['repo_id']==DATASET_REPO_ID


def test_new_staging_targets_current_repo_but_keeps_catalog_bytes(tmp_path):
    from qlm_bench.publication import _inventory
    stage=tmp_path/'stage';stage.mkdir();(stage/'payload.json').write_text('{}')
    value=_inventory(stage,kind='catalogue',identity='fixture',repo_id=LEGACY_DATASET_REPO_ID,work_id='DATA-012')
    assert value['repo_id']==DATASET_REPO_ID
    from qlm_bench.data import load_catalog,resolve_release
    catalog=load_catalog();ref=resolve_release('DATA-006-20260916T075451Z',catalog)
    assert catalog['repo_id']==LEGACY_DATASET_REPO_ID
    assert ref.repo_id==LEGACY_DATASET_REPO_ID and ref.hub_repo_id==DATASET_REPO_ID
    assert replace(ref,repo_id=DATASET_REPO_ID).hub_repo_id==DATASET_REPO_ID
    assert dataset_repo_id('another/QLM-Bench')=='another/QLM-Bench'


def test_owner_alias_accepts_old_manifest_for_new_location_but_rejects_unrelated_repo(tmp_path):
    from qlm_bench.data import DatasetRef,CanonicalDataset
    release='fixture';canonical=tmp_path/'canonical/lerobot_v2_1'/release;meta=canonical/'meta';meta.mkdir(parents=True)
    split={'train':['episode'],'validation':[],'test':[]}
    manifest={'repo_id':LEGACY_DATASET_REPO_ID,'release':release,'canonical_root':'canonical/lerobot_v2_1/'+release,
        'dataset_schema_version':'wam-quadruped-v2.1.0','episodes':[{'episode_uid':'episode'}],'split':split}
    path=tmp_path/'releases'/release/'manifest.json';path.parent.mkdir(parents=True);path.write_text(json.dumps(manifest))
    (meta/'contract.json').write_text(json.dumps({'dataset_schema_version':manifest['dataset_schema_version'],'episodes':manifest['episodes']}))
    (meta/'info.json').write_text('{}');(meta/'split.json').write_text(json.dumps({'episodes':split}))
    raw=path.read_bytes();ref=DatasetRef(DATASET_REPO_ID,'a'*40,release,manifest['canonical_root'],manifest['dataset_schema_version'],
        'releases/'+release+'/manifest.json',hashlib.sha256(raw).hexdigest())
    assert CanonicalDataset(ref,tmp_path).episodes('train')==[{'episode_uid':'episode'}]
    assert path.read_bytes()==raw
    with pytest.raises(ValueError,match='release/schema'):CanonicalDataset(replace(ref,repo_id='another/QLM-Bench'),tmp_path)


def test_license_owner_alias_does_not_grant_other_repository_scope():
    from qlm_bench.assets import load_manifest,validate_manifest
    original=load_manifest('rambo-go2-controller');value=deepcopy(original)
    validate_manifest(value,for_publication=True)
    value['license']['scope']='private:'+DATASET_REPO_ID;validate_manifest(value,for_publication=True)
    value['license']['scope']='private:another/QLM-Bench'
    with pytest.raises(ValueError,match='scoped'):validate_manifest(value,for_publication=True)
    assert original['license']['scope']=='private:'+LEGACY_DATASET_REPO_ID
