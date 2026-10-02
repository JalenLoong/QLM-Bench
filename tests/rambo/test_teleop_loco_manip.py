"""Current task keyboard and factory behavior without Kit or a GPU."""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
import os
import subprocess
import numpy as np
import pytest


def teleop_module():
    path=Path(__file__).resolve().parents[2]/'scripts/rambo/teleop_loco_manip.py'
    spec=importlib.util.spec_from_file_location('current_teleop',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_current_three_task_parser_and_help_are_simulator_independent():
    # Other CPU tests intentionally install Isaac stubs in sys.modules. Check
    # the actual import boundary in a fresh process rather than that shared state.
    root=Path(__file__).resolve().parents[2]
    code="""import importlib.util,sys
from pathlib import Path
path=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('current_teleop',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
parser=m._build_parser()
assert len(m.TASK_IDS)==3
assert 'Button-Go2-v0' not in parser.format_help()
assert 'gui-artifact' not in parser.format_help()
for task in m.TASK_IDS:
    args=parser.parse_args(['--task',task,'--viz','none','--resource-root','resources','--max-actions','2'])
    m._validate_args(parser,args)
assert 'isaaclab' not in sys.modules and 'omni.kit.app' not in sys.modules
"""
    env=dict(os.environ,PYTHONPATH=os.pathsep.join(str(root/p) for p in ['source/rambo','source/crl2','src']))
    run=subprocess.run([sys.executable,'-c',code,str(root/'scripts/rambo/teleop_loco_manip.py')],
                       env=env,cwd=root,text=True,capture_output=True)
    assert run.returncode==0,run.stderr


def test_key_names_accept_carb_enums_and_strings():
    m=teleop_module()
    assert m._keyboard_event_name(SimpleNamespace(input=SimpleNamespace(name='W')))=='W'
    assert m._keyboard_event_name(SimpleNamespace(input='SPACE'))=='SPACE'


def test_retained_keyboard_sensitivities_hold_release_and_reset(monkeypatch):
    m=teleop_module()
    class Base:
        def __init__(self,cfg):
            self.cfg=cfg;self._INPUT_KEY_MAPPING={'UP':np.array([.4,0,0],dtype=np.float32)}
            self._additional_callbacks={};self.reset()
        def reset(self):self._base_command=np.zeros(3,dtype=np.float32)
        def __str__(self):return 'Keyboard'
    monkeypatch.setitem(sys.modules,'carb',SimpleNamespace(input=SimpleNamespace(
        KeyboardEventType=SimpleNamespace(KEY_PRESS='press',KEY_RELEASE='release'))))
    monkeypatch.setitem(sys.modules,'isaaclab.devices',SimpleNamespace(Se2Keyboard=Base,Se2KeyboardCfg=lambda **kw:kw))
    args=m._build_parser().parse_args(['--viz','kit','--resource-root','resources'])
    keyboard=m._make_keyboard(SimpleNamespace(device='cpu'),args)
    assert keyboard.cfg['v_x_sensitivity']==.4 and keyboard.cfg['omega_z_sensitivity']==.4
    event=lambda key,kind:SimpleNamespace(input=key,type=kind)
    keyboard._on_keyboard_event(event('W','press'));keyboard._on_keyboard_event(event('W','press'))
    assert keyboard.leg_velocity()[0]==pytest.approx(.12)
    keyboard._on_keyboard_event(event('UP','press'))
    assert keyboard._base_command[0]==pytest.approx(.4)
    keyboard._on_keyboard_event(event('W','release'));assert not keyboard.leg_velocity().any()
    keyboard._on_keyboard_event(event('R','press'));keyboard._on_keyboard_event(event('L','press'))
    assert not keyboard.leg_velocity().any() and not keyboard._base_command.any()
    keyboard._on_keyboard_event(event('SPACE','press'))
    assert not keyboard.leg_velocity().any()


def test_factory_retains_deterministic_controller_schedule_and_mount_settings():
    from rambo.tasks.common.environment_factory import configure_environment,LIFT_BASKET_TASK_ID
    cfg=SimpleNamespace(scene=SimpleNamespace(),viewer=SimpleNamespace(),terminate_on_limb_contact=True,
        terminate_on_body_contact=True,contact_generator_config={'contact_sequence':{'FL':[['stance',1.],['swing',1.]]}})
    configure_environment(cfg,task_id=LIFT_BASKET_TASK_ID,seed=42,episode_length_s=24.)
    assert cfg.seed==42 and cfg.events is None and cfg.obs_noise is False
    assert cfg.terminate_on_limb_contact is False and cfg.terminate_on_body_contact is True
    assert sum(x[1] for x in cfg.contact_generator_config['contact_sequence']['FL'])==25.
    assert cfg.viewer.lookat==[.70,.10,.28]
    assert not cfg.enable_sampled_force_commands


def test_teleop_uses_runtime_50hz_native9_submission_and_zero_force():
    source=(Path(__file__).resolve().parents[2]/'scripts/rambo/teleop_loco_manip.py').read_text()
    assert 'runtime.step(prepared)' in source and 'prepare_command(request,' in source
    assert 'np.zeros(3, dtype=np.float32)' in source
    assert 'gui_keyboard_artifact' not in source
    assert 'smoke_press' not in source and 'set_loco_manip_commands(' not in source
