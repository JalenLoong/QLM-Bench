"""Default-resource selection cannot silently restore obsolete rendering assets."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from qlm_bench.backends.mujoco.defaults import (
    add_model_arguments, default_model_set, resolve_model, validate_default_identity,
)


def test_default_pack_is_lod_and_missing_pack_does_not_fall_back(tmp_path, monkeypatch):
    monkeypatch.setenv('QLM_MUJOCO_MODEL_ROOT', str(tmp_path))
    for task, item in default_model_set()['tasks'].items():
        old = tmp_path / ('original-' + task + '-v1-step-rig-a01') / 'scene.xml'
        old.parent.mkdir(); old.touch()
        with pytest.raises(FileNotFoundError):
            resolve_model(task_id=task)
        path = tmp_path / item['model']
        path.parent.mkdir(); path.touch()
        assert resolve_model(task_id=task) == path
        assert path.parent.name.endswith('v1-step-rig-lod-a02')
        validate_default_identity(path, {'identity': item['resource_identity']})
        with pytest.raises(ValueError, match='identity'):
            validate_default_identity(path, {'identity': 'bad'})
        assert resolve_model(old, task_id=task) == old


def test_default_requires_task_and_root_and_rejects_escaping_pack(tmp_path, monkeypatch):
    monkeypatch.delenv('QLM_MUJOCO_MODEL_ROOT', raising=False)
    with pytest.raises(ValueError, match='--task'):
        resolve_model(model_root=tmp_path)
    with pytest.raises(ValueError, match='--model-root'):
        resolve_model(task_id='push_box')
    resource = tmp_path / 'root'; resource.mkdir()
    external = tmp_path / 'external'; external.mkdir(); (external / 'scene.xml').touch()
    item = default_model_set()['tasks']['push_box']
    (resource / Path(item['model']).parent).symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match='escapes'):
        resolve_model(task_id='push_box', model_root=resource)


def test_shared_cli_selection_and_cpu_import_boundary():
    parser = argparse.ArgumentParser(); add_model_arguments(parser)
    args = parser.parse_args(['--task', 'press_button', '--model-root', '/assets'])
    assert args.model is None and args.task == 'press_button'
    source = str(Path(__file__).resolve().parents[2] / 'src')
    check = subprocess.run([sys.executable, '-c', """
import sys
from qlm_bench.backends.factory import backend_binding
from qlm_bench.backends.mujoco.defaults import default_model_set
assert backend_binding('push_box','mjwarp')['status']=='engineering'
assert default_model_set()['profile_suffix']=='v1-step-rig-lod-a02'
assert not any(x in sys.modules for x in ('torch','mujoco','mujoco_warp','isaaclab','isaacsim'))
"""], env={**os.environ, 'PYTHONPATH': source}, capture_output=True, text=True)
    assert check.returncode == 0, check.stderr


def test_old_case_is_rejected_before_runtime_start(tmp_path, monkeypatch):
    from qlm_bench.backends.mujoco import evaluation, resources
    task = 'push_box'; item = default_model_set()['tasks'][task]
    model = tmp_path / item['model']; model.parent.mkdir(); model.touch()
    case = tmp_path / 'old-case.json'
    case.write_text(json.dumps({'cases': [{'task_id': task, 'scene': {'resource_identity': 'old'}}]}))
    monkeypatch.setattr(resources, 'resource_closure', lambda *args, **kwargs: {'identity': item['resource_identity']})
    monkeypatch.setattr(evaluation, 'load_model_profile', lambda *args, **kwargs: {'task_id': task})
    started = []
    monkeypatch.setattr(evaluation, 'run_bundle', lambda *args: started.append(True))
    with pytest.raises(ValueError, match='Case resource differs'):
        evaluation.main(['run', '--backend', 'native', '--model-root', str(tmp_path),
                         '--config', str(case), '--checkpoint', 'original.pt',
                         '--ffmpeg', 'ffmpeg', '--ffprobe', 'ffprobe', '--output', str(tmp_path / 'out')])
    assert not started and not (tmp_path / 'out').exists()


@pytest.mark.skipif(not os.environ.get('QLM_MUJOCO_MODEL_ROOT'), reason='Actual portable resources required')
def test_actual_default_resource_pins():
    from qlm_bench.backends.mujoco.resources import resource_closure
    for task in default_model_set()['tasks']:
        path = resolve_model(task_id=task)
        resources = resource_closure(path, require_portable=True)
        assert resources['declared_manifest_verified']
        validate_default_identity(path, resources)
