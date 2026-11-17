"""The ten QLM-Bench tasks: instruction, scene-profile prefix and task family (no simulator imports)."""
import json
from pathlib import Path

TASK_IDS = ('push_box', 'press_button', 'lift_basket', 'kick_ball_to_goal', 'sweep_block_to_zone',
            'close_fridge_door', 'close_oven_door', 'turn_valve', 'pull_open_drawer', 'open_room_door')
# object tasks use per-task state machines (object_tasks.py); the six authored-scene tasks share
# articulated_tasks.py (sweep_block_to_zone is grouped there although its object is free).
OBJECT_TASKS = TASK_IDS[:4]
ARTICULATED_TASKS = TASK_IDS[4:]
ROOT = Path(__file__).with_name('registrations')


def load_registration(task_id):
    if task_id not in TASK_IDS:
        raise ValueError('Unknown QLM-Bench task: ' + str(task_id))
    data = json.loads((ROOT / (task_id + '.json')).read_text())
    if data.get('task_id') != task_id or not str(data.get('instruction', '')).strip():
        raise ValueError('Invalid task registration: ' + task_id)
    return data


def registrations():
    return {task: load_registration(task) for task in TASK_IDS}
