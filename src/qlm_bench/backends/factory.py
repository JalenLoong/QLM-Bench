"""Create a MuJoCo runtime for one of the ten QLM-Bench tasks (simulator imports happen on creation)."""
import json
from pathlib import Path

from qlm_bench.tasks.registration import ARTICULATED_TASKS, OBJECT_TASKS, load_registration


def load_model_profile(model, *, task_id=None):
    """The scene's `.task.json` profile with the current task instruction applied."""
    from qlm_bench.tasks.prompts import current_instruction_profile
    profile = json.loads(Path(model).with_suffix('.task.json').read_text())
    actual = profile.get('task_id')
    if actual not in OBJECT_TASKS + ARTICULATED_TASKS or (task_id is not None and task_id != actual):
        raise ValueError(f'Scene profile task {actual!r} differs from the requested task {task_id!r}')
    registration = load_registration(actual)
    if profile.get('instruction') not in [registration['instruction'], *registration.get('previous_instructions', [])]:
        raise ValueError('Scene profile instruction differs from the registered task')
    return current_instruction_profile(profile)


def create_runtime(task_id, backend='native', *, model_path, **kwargs):
    """backend: 'native' (MuJoCo CPU, float64; used for Standard100 and all training) or 'mjwarp' (GPU)."""
    if backend not in ('native', 'mjwarp'):
        raise ValueError('MuJoCo backend must be native or mjwarp')
    model = Path(model_path).resolve(strict=True)
    load_model_profile(model, task_id=task_id)
    if task_id in ARTICULATED_TASKS:
        from qlm_bench.backends.mujoco.articulated_tasks import articulated_runtime
        return articulated_runtime(model, backend=backend, **kwargs)
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    return MuJoCoRuntime(model, backend=backend, **kwargs)
