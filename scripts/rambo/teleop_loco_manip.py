#!/usr/bin/env python3
"""Keyboard native9 teleoperation for the three current Go2/FL tasks."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np
from rambo.tasks.common.environment_factory import TASK_IDS, PUSH_BOX_TASK_ID, LIFT_BASKET_TASK_ID, PRESS_BUTTON_TASK_ID

EE_MIN = np.array([0.1934, 0.0, 0.0], dtype=np.float32)
EE_MAX = np.array([0.50, 0.20, 0.40], dtype=np.float32)
EE_DEFAULT = np.array([0.1934, 0.142, 0.05], dtype=np.float32)
PROFILE_FILES = {PUSH_BOX_TASK_ID: 'push_box_v2.json', LIFT_BASKET_TASK_ID: 'lift_basket_v2.json',
                 PRESS_BUTTON_TASK_ID: 'press_button_v2.json'}


def _keyboard_event_name(event: Any) -> str:
    key = event.input
    return key.name if hasattr(key, 'name') else str(key)


def _make_keyboard(base_env, args):
    """Use the retained Se2 keyboard and FL velocity controls."""
    import carb
    from isaaclab.devices import Se2Keyboard, Se2KeyboardCfg

    class ManipulatorKeyboard(Se2Keyboard):
        _LEG_KEYS = {'W': (0, 1.), 'S': (0, -1.), 'A': (1, 1.), 'D': (1, -1.),
                     'R': (2, 1.), 'F': (2, -1.)}

        def __init__(self):
            self._held_leg_keys = set()
            self._fl_speeds = np.array([args.fl_x_speed, args.fl_y_speed, args.fl_z_speed], dtype=np.float32)
            super().__init__(Se2KeyboardCfg(v_x_sensitivity=args.vx_sensitivity,
                                            v_y_sensitivity=args.vy_sensitivity,
                                            omega_z_sensitivity=args.wz_sensitivity,
                                            sim_device=str(base_env.device)))

        def reset(self):
            super().reset()
            self._held_leg_keys.clear()

        def leg_velocity(self):
            velocity = np.zeros(3, dtype=np.float32)
            for key in self._held_leg_keys:
                axis, sign = self._LEG_KEYS[key]
                velocity[axis] += sign*self._fl_speeds[axis]
            return velocity

        def _on_keyboard_event(self, event, *args, **kwargs):
            key = _keyboard_event_name(event)
            if key in self._LEG_KEYS:
                if event.type == carb.input.KeyboardEventType.KEY_PRESS:
                    self._held_leg_keys.add(key)
                elif event.type == carb.input.KeyboardEventType.KEY_RELEASE:
                    self._held_leg_keys.discard(key)
                return True
            if event.type == carb.input.KeyboardEventType.KEY_PRESS:
                if key == 'L':
                    self.reset()
                elif key in self._INPUT_KEY_MAPPING:
                    self._base_command += self._INPUT_KEY_MAPPING[key]
                if key in self._additional_callbacks:
                    self._additional_callbacks[key]()
            elif event.type == carb.input.KeyboardEventType.KEY_RELEASE and key in self._INPUT_KEY_MAPPING:
                self._base_command -= self._INPUT_KEY_MAPPING[key]
            return True

        def __str__(self):
            return super().__str__()+'\nFL W/S: forward/back; A/D: lateral; R/F: up/down; L: stop commands'

    return ManipulatorKeyboard()


class _NeutralInput:
    def reset(self): pass
    def advance(self): return np.zeros(3, dtype=np.float32)
    def leg_velocity(self): return np.zeros(3, dtype=np.float32)


def _select_mounted_view(view):
    from isaacsim.core.rendering_manager import ViewportManager
    from rambo.tasks.common.lift_camera_rig import CAMERAS
    path = '/OmniverseKit_Persp' if view == 'third-person' else CAMERAS[view]['path']
    ViewportManager.set_camera(path)
    if str(ViewportManager.get_camera().GetPath()) != path:
        raise RuntimeError(f'Viewport failed to select {path}')


def _build_parser(app_launcher=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', choices=TASK_IDS, default=PUSH_BOX_TASK_ID)
    parser.add_argument('--profile', type=Path, help='Reviewed task profile; default is the selected task profile')
    parser.add_argument('--resource-root', type=Path, default=os.environ.get('QLM_RESOURCE_ROOT'))
    parser.add_argument('--checkpoint', type=Path, help='Optional exact fixed-controller path; otherwise resolve the registry ID')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--episode-length-s', type=float, default=24.)
    parser.add_argument('--max-actions', type=int, default=0, help='50 Hz commands; 0 continues until GUI closes')
    parser.add_argument('--view', choices=('third-person', 'ego', 'task'), default='third-person')
    for name, default in [('vx-sensitivity', .4), ('vy-sensitivity', .2), ('wz-sensitivity', .4),
                          ('fl-x-speed', .12), ('fl-y-speed', .08), ('fl-z-speed', .10)]:
        parser.add_argument('--'+name, type=float, default=default)
    parser.add_argument('--disable-fabric', action='store_true')
    if app_launcher is None:
        parser.add_argument('--viz', choices=('none', 'kit'), required=True)
    else:
        app_launcher.add_app_launcher_args(parser)
    return parser


def _validate_args(parser, args):
    if args.resource_root is None:
        parser.error('--resource-root or QLM_RESOURCE_ROOT is required')
    if args.max_actions < 0:
        parser.error('--max-actions must be nonnegative')
    for name in ('episode_length_s', 'vx_sensitivity', 'vy_sensitivity', 'wz_sensitivity',
                 'fl_x_speed', 'fl_y_speed', 'fl_z_speed'):
        if not math.isfinite(getattr(args, name)) or getattr(args, name) <= 0:
            parser.error(name+' must be finite and positive')


def _run(args, simulation_app):
    import torch
    from rambo.torch_runtime import ensure_cuda_linalg_loaded
    from rambo.contracts_v2.runtime import prepare_command
    from rambo.tasks.common.controller_runtime import ControllerRuntime

    ensure_cuda_linalg_loaded()
    profile_path = args.profile or Path(__file__).resolve().parents[2]/'configs'/PROFILE_FILES[args.task]
    profile = json.loads(profile_path.read_text())
    runtime = ControllerRuntime(args.task, profile=profile, resource_root=args.resource_root,
                                checkpoint_path=args.checkpoint, seed=args.seed,
                                episode_length_s=args.episode_length_s, view=args.view,
                                use_fabric=not args.disable_fabric)
    env = runtime.base_env
    headless = args.rambo_visualizer == ['none']
    keyboard = _NeutralInput() if headless else _make_keyboard(env, args)
    keyboard.reset()
    if not headless:
        keyboard.add_callback('F6', lambda: _select_mounted_view('ego'))
        keyboard.add_callback('F7', lambda: _select_mounted_view('task'))
        keyboard.add_callback('F8', lambda: _select_mounted_view('third-person'))
        _select_mounted_view(args.view)
        print(keyboard, flush=True)
    leg_target = EE_DEFAULT.copy()
    count = 0
    try:
        while simulation_app.is_running() and (args.max_actions == 0 or count < args.max_actions):
            base = keyboard.advance()
            if hasattr(base, 'detach'):
                base = base.detach().cpu().numpy()
            base = np.asarray(base, dtype=np.float32)
            if bool(env.manipulator_ready[0]):
                # Preserve the existing operator target limits. The action contract itself is unchanged.
                leg_target = np.clip(leg_target+keyboard.leg_velocity()*.02, EE_MIN, EE_MAX)
            request = np.concatenate((base, leg_target, np.zeros(3, dtype=np.float32)))
            prepared = prepare_command(request, f'teleop:{count}', env.episode_tick)
            result = runtime.step(prepared)
            count += 1
            if result['terminal'] is not None:
                print('[TERMINAL] '+result['terminal']['reason'], flush=True)
                keyboard.reset()
                leg_target = EE_DEFAULT.copy()
    finally:
        runtime.close()
    return 0


def main():
    if '--help' in sys.argv[1:] or '-h' in sys.argv[1:]:
        _build_parser().print_help()
        return 0
    from isaaclab.app import AppLauncher
    from rambo.utils.physx import validate_rambo_visualizer_args
    parser = _build_parser(AppLauncher)
    args = parser.parse_args()
    _validate_args(parser, args)
    args.rambo_visualizer = validate_rambo_visualizer_args(parser, args, sys.argv[1:])
    if args.rambo_visualizer == ['none'] and args.max_actions == 0:
        parser.error('--viz none requires a finite --max-actions')
    args.enable_cameras = True
    app = AppLauncher(args).app
    exit_code = 1
    try:
        exit_code = _run(args, app)
        return exit_code
    finally:
        app.close(exit_code=exit_code)


if __name__ == '__main__':
    raise SystemExit(main())
