"""Detect resource substitution and model mutations which data-only sync misses."""
import json
from pathlib import Path
import shutil
import os

import mujoco
import pytest

from qlm_bench.backends.mujoco.resources import file_hash, model_parameter_identity, resource_closure


def pack(root):
    root.mkdir()
    (root/'shape.obj').write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\nf 1 2 3\nf 1 2 4\nf 1 3 4\nf 2 3 4\n')
    (root/'model.xml').write_text('<mujoco><asset><mesh name="shape" file="shape.obj"/></asset>'
        '<worldbody><geom type="mesh" mesh="shape"/></worldbody></mujoco>')
    files = {p.name:{'sha256':file_hash(p),'size_bytes':p.stat().st_size} for p in root.iterdir()}
    (root/'resource-manifest.json').write_text(json.dumps({'schema':'qlm-portable-mujoco-resource-v1','entrypoint':'model.xml','files':files}))
    return root/'model.xml'


def test_relocation_preserves_identity_and_mesh_substitution_fails(tmp_path):
    source = pack(tmp_path/'source')
    before = resource_closure(source,require_portable=True)
    shutil.copytree(source.parent,tmp_path/'relocated')
    assert resource_closure(tmp_path/'relocated/model.xml',require_portable=True) == before
    (tmp_path/'relocated/shape.obj').write_text('changed geometry')
    with pytest.raises(ValueError,match='checksum mismatch'):
        resource_closure(tmp_path/'relocated/model.xml')


def test_undeclared_dependency_and_absolute_resources_are_rejected(tmp_path):
    model = pack(tmp_path/'source')
    manifest_path = model.parent/'resource-manifest.json'
    manifest = json.loads(manifest_path.read_text());del manifest['files']['shape.obj']
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='dependency missing'):
        resource_closure(model)
    manifest_path.unlink()
    model.write_text(model.read_text().replace('file="shape.obj"',f'file="{model.parent}/shape.obj"'))
    assert not resource_closure(model)['portable']
    with pytest.raises(ValueError,match='not a portable'):
        resource_closure(model,require_portable=True)


@pytest.mark.parametrize('field', ['camera','light','material','clip','solver','mesh','headlight','shadow_quality'])
def test_frozen_model_mutations_are_detected(field):
    model = mujoco.MjModel.from_xml_string('<mujoco><asset><material name="mat" rgba=".2 .3 .4 1"/>'
        '<mesh name="mesh" vertex="0 0 0  1 0 0  0 1 0  0 0 1"/></asset>'
        '<worldbody><camera name="camera"/><light/><geom type="mesh" mesh="mesh" material="mat"/></worldbody></mujoco>')
    full = field == 'mesh'
    before = model_parameter_identity(model,full=full)
    if field == 'camera':model.cam_pos[0,0] += .1
    elif field == 'light':model.light_diffuse[0,0] = .1
    elif field == 'material':model.mat_rgba[0,0] = .1
    elif field == 'clip':model.vis.map.znear = .2
    elif field == 'solver':model.opt.solver = mujoco.mjtSolver.mjSOL_PGS
    elif field == 'mesh':model.mesh_vert[0,0] += .1
    elif field == 'headlight':model.vis.headlight.ambient[0] += .1
    elif field == 'shadow_quality':model.vis.quality.shadowsize *= 2
    assert before != model_parameter_identity(model,full=full)


def test_data_forward_does_not_change_model_identity():
    model = mujoco.MjModel.from_xml_string('<mujoco><worldbody><body><freejoint/><geom type="sphere" size=".1"/></body></worldbody></mujoco>')
    before = model_parameter_identity(model,full=True)
    data = mujoco.MjData(model)
    data.qpos[:3] = [.1,.2,.3]
    mujoco.mj_forward(model,data)
    assert before == model_parameter_identity(model,full=True)


@pytest.mark.skipif(not os.environ.get('QLM_MUJOCO_MODEL') or os.environ.get('MUJOCO_GL') not in ('egl','osmesa'),
                    reason='Explicit actual Go2 model and rendering context required')
def test_actual_render_mirror_rejects_model_mutation_and_preserves_physics():
    import numpy as np
    from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
    from qlm_bench.backends.mujoco.render import RenderMirror
    physics=MuJoCoPhysics(os.environ['QLM_MUJOCO_MODEL'])
    mirror=RenderMirror(os.environ['QLM_MUJOCO_MODEL'])
    try:
        snapshot=physics.snapshot();before=physics.data[0].qpos.copy()
        capture=mirror.capture(snapshot)
        assert all(v.shape==(720,1280,3) and v.std()>1 for v in capture['rgb'].values())
        assert capture['GL']['renderer'] and capture['GL']['vendor']
        np.testing.assert_array_equal(physics.data[0].qpos,before)
        assert physics.ticks[0]==0
        old=physics.model.cam_pos.copy()
        physics.model.cam_pos[0,0]+=.01
        with pytest.raises(RuntimeError,match='parameters changed'):
            physics.snapshot()
        physics.model.cam_pos[:]=old
        old=mirror.model.cam_pos.copy()
        mirror.model.cam_pos[0,0]+=.01
        with pytest.raises(ValueError,match='parameters differ'):
            mirror.capture(snapshot)
        mirror.model.cam_pos[:]=old
        with pytest.raises(ValueError,match='world identity'):
            mirror.capture({**snapshot,'world_id':1})
        mirror.capture({**snapshot,'physics_step':10,'simulation_time_ns':20_000_000,'time':.02})
        with pytest.raises(ValueError,match='Stale'):
            mirror.capture(snapshot)
    finally:
        mirror.close();physics.close()
