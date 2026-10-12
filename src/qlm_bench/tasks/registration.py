"""Per-task plug-ins: CPU discovery is separate from simulator admission."""
from __future__ import annotations
import importlib
import json
from pathlib import Path
import re

SCALEUP_TASK_IDS = ('push_box', 'lift_basket', 'press_button', 'kick_ball_to_goal',
                   'sweep_block_to_zone', 'close_fridge_door', 'close_oven_door',
                   'turn_valve', 'pull_open_drawer', 'open_room_door')
ROOT = Path(__file__).with_name('registrations')


def load_registration(task_id, *, ready=False):
    if task_id not in SCALEUP_TASK_IDS:
        raise ValueError('Unknown scale-up task')
    data = json.loads((ROOT / (task_id + '.json')).read_text())
    if data.get('schema') != 'qlm-task-plugin-v1' or data.get('task_id') != task_id or data.get('status') not in ('planned', 'ready'):
        raise ValueError('Invalid task plug-in identity/status')
    for field in ('instruction', 'profile_prefix'):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError('Explicit task instruction/profile prefix required')
    if data['status'] == 'ready':
        if not data.get('gym_id') or not data.get('task_spec'):
            raise ValueError('Ready task requires runtime and task-spec identities')
        for field in ('environment', 'config', 'expert', 'converter'):
            if not re.fullmatch(r'[a-zA-Z_][\w.]*:[a-zA-Z_]\w*', str(data.get(field))):
                raise ValueError('Explicit module:symbol binding required: ' + field)
            prefix = 'qlm_bench.' if field == 'converter' else 'rambo.tasks.'
            if not data[field].startswith(prefix):
                raise ValueError('Task plug-ins stay inside QLM/RAMBO: ' + field)
        for optional in ('configure_profile', 'batch_environment', 'batch_expert'):
            if data.get(optional) and (not data[optional].startswith('rambo.tasks.') or not re.fullmatch(r'[a-zA-Z_][\w.]*:[a-zA-Z_]\w*', data[optional])):
                raise ValueError('Invalid task-owned runtime hook: ' + optional)
        path = Path(data['task_spec'])
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Task spec must be package-relative')
    if ready and data['status'] != 'ready':
        raise ValueError(task_id + ' is planned; implement and validate its task plug-in first')
    return data


def registrations():
    return {task: load_registration(task) for task in SCALEUP_TASK_IDS}


def resolve_symbol(binding):
    module, name = binding.split(':', 1)
    return getattr(importlib.import_module(module), name)


def runtime_binding(task_id, field):
    """Caller must launch Isaac before resolving environment/config/expert."""
    return resolve_symbol(load_registration(task_id, ready=True)[field])
