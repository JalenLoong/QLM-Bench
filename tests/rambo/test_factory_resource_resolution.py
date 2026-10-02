"""Distinct resource IDs may share USD entry bytes but have different textures."""
import hashlib
from pathlib import Path
import pytest
from qlm_bench import assets
from rambo.tasks.common.environment_factory import resolve_task_asset


def descriptor(data):return {'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


@pytest.fixture
def resources(tmp_path,monkeypatch):
    manifests={}
    for name,entry,texture in [('red',b'same entry',b'red texture'),
                               ('blue',b'same entry',b'blue texture'),
                               ('unique',b'unique entry',b'grey texture')]:
        manifest={'asset_id':name,'entrypoint':'scene.usda','cache_subdir':name+'/v1/runtime',
                  'files':{'scene.usda':descriptor(entry),'textures/color.png':descriptor(texture)}}
        manifests[name]=manifest
        for relative,data in [('scene.usda',entry),('textures/color.png',texture)]:
            path=tmp_path/manifest['cache_subdir']/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    def manifest(name):
        if name not in manifests:raise ValueError('Unknown resource ID')
        return manifests[name]
    monkeypatch.setattr(assets,'load_manifest',manifest)
    monkeypatch.setattr(assets,'load_registry',lambda:{'resources':[{'asset_id':name} for name in manifests]})
    return tmp_path,manifests


def test_explicit_id_precedes_profile_id_with_duplicate_entry_sha(resources):
    root,manifests=resources
    profile={'asset_sha256':manifests['blue']['files']['scene.usda']['sha256'],'asset_id':'red'}
    selected=resolve_task_asset(profile,root,asset_id='blue')
    assert selected==root/manifests['blue']['cache_subdir']/'scene.usda'
    assert (selected.parent/'textures/color.png').read_bytes()==b'blue texture'


def test_profile_id_resolves_duplicate_entry_sha_and_ambiguous_legacy_profile_is_rejected(resources):
    root,manifests=resources
    profile={'asset_sha256':manifests['blue']['files']['scene.usda']['sha256'],'asset_id':'blue'}
    assert resolve_task_asset(profile,root).parent==root/manifests['blue']['cache_subdir']
    del profile['asset_id']
    with pytest.raises(ValueError,match='one registry entry'):resolve_task_asset(profile,root)
    profile['asset_sha256']=manifests['unique']['files']['scene.usda']['sha256']
    assert resolve_task_asset(profile,root).parent==root/manifests['unique']['cache_subdir']


@pytest.mark.parametrize('explicit',[False,True])
def test_wrong_entry_sha_is_rejected_even_with_an_explicit_resource_id(resources,explicit):
    root,manifests=resources
    profile={'asset_sha256':'0'*64,'asset_id':'red'}
    with pytest.raises(ValueError,match='reviewed task profile'):
        resolve_task_asset(profile,root,asset_id='blue' if explicit else None)


@pytest.mark.parametrize('identity',['profile','legacy'])
def test_texture_corruption_is_rejected_for_profile_and_unique_legacy_identity(resources,identity):
    root,manifests=resources
    name='blue' if identity=='profile' else 'unique'
    profile={'asset_sha256':manifests[name]['files']['scene.usda']['sha256']}
    if identity=='profile':profile['asset_id']=name
    texture=root/manifests[name]['cache_subdir']/'textures/color.png';texture.write_bytes(b'changed')
    with pytest.raises(ValueError,match='payload changed or missing'):resolve_task_asset(profile,root)


def test_reviewed_texture_hash_prevents_switching_material_variant(resources):
    root,manifests=resources
    profile={'asset_sha256':manifests['red']['files']['scene.usda']['sha256'],
             'asset_bundle_sha256':{'textures/color.png':manifests['red']['files']['textures/color.png']['sha256']}}
    with pytest.raises(ValueError,match='inventory differs'):resolve_task_asset(profile,root,asset_id='blue')
    profile['asset_bundle_sha256']['conversion.json']='a'*64
    assert resolve_task_asset(profile,root,asset_id='red').is_file()
    profile['asset_bundle_sha256']['textures/missing.png']='a'*64
    with pytest.raises(ValueError,match='missing from the runtime inventory'):resolve_task_asset(profile,root,asset_id='red')
