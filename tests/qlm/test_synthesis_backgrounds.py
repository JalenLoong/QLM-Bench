"""Background profile checks protect physics/camera while allowing appearance."""
import importlib.util
from pathlib import Path

import pytest

mujoco=pytest.importorskip('mujoco')


def validator():
    path=Path(__file__).resolve().parents[2]/'scripts/mujoco/synthesis/prepare_backgrounds.py'
    spec=importlib.util.spec_from_file_location('background_preparation',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.validate_nonvisual


def test_background_color_only_preserves_physics_and_camera(tmp_path):
    xml='<mujoco><worldbody><camera name="cam" pos="1 0 1"/><geom name="floor" type="plane" size="4 4 .1" rgba=".3 .4 .5 1"/><body pos="0 0 1"><freejoint/><geom size=".1" mass="1"/></body></worldbody></mujoco>'
    a=tmp_path/'a.xml';b=tmp_path/'b.xml';a.write_text(xml);b.write_text(xml.replace('.3 .4 .5 1','.5 .4 .3 1'))
    assert validator()(a,b)['passed']


@pytest.mark.parametrize('before,after', [('mass="1"','mass="2"'),('pos="1 0 1"','pos="2 0 1"'),('size="4 4 .1"','size="4 3 .1"')])
def test_background_cannot_hide_physics_or_camera_changes(tmp_path,before,after):
    xml='<mujoco><worldbody><camera name="cam" pos="1 0 1"/><geom name="floor" type="plane" size="4 4 .1"/><body pos="0 0 1"><freejoint/><geom size=".1" mass="1"/></body></worldbody></mujoco>'
    a=tmp_path/'a.xml';b=tmp_path/'b.xml';a.write_text(xml);b.write_text(xml.replace(before,after))
    with pytest.raises(ValueError,match='Nonvisual'):validator()(a,b)
