"""CPU-only backend discovery, with simulator imports confined to explicit creation."""
import json
from pathlib import Path

from qlm_bench.tasks.registration import load_registration

MUJOCO_TASKS=('push_box','press_button','lift_basket')


def backend_binding(task_id,backend):
    registration=load_registration(task_id)
    declared=registration.get('backends',{}).get(backend)
    if declared is not None:
        if declared.get('status')!='ready':raise ValueError('Backend production admission is not ready')
        return dict(task_id=task_id,backend=backend,**declared)
    registration=load_registration(task_id,ready=True)
    if backend=='isaac':
        return {'task_id':task_id,'backend':backend,'status':'reference',
                'runtime':'rambo.tasks.common.controller_runtime:ControllerRuntime',
                'expert':registration['expert'],'converter':registration['converter']}
    if backend not in ('native','mjwarp') or task_id not in MUJOCO_TASKS:
        raise ValueError('No implemented backend binding for this task')
    return {'task_id':task_id,'backend':backend,'status':'engineering',
            'runtime':'qlm_bench.backends.mujoco.runtime:MuJoCoRuntime',
            'expert':'qlm_bench.backends.mujoco.expert_adapter:ExpertAdapter',
            'converter':'qlm_bench.compatibility.dataset_v2.conversion:convert'}


def load_model_profile(model,*,task_id=None):
    path=Path(model)
    profile=json.loads(path.with_suffix('.task.json').read_text())
    actual=profile.get('task_id')
    from .mujoco.remaining_tasks import TASKS
    if actual in TASKS:
        if task_id is not None and task_id!=actual:raise ValueError('Declared task and model profile differ')
        if profile.get('schema')!='qlm-mujoco-task-candidate-v1' or profile.get('instruction') not in [load_registration(actual)['instruction'],*load_registration(actual).get('previous_instructions',[])]:
            raise ValueError('Approved six-task resource profile/instruction required')
        backend_binding(actual,'native')
        from qlm_bench.tasks.prompts import current_instruction_profile
        return current_instruction_profile(profile)
    if actual not in MUJOCO_TASKS or (task_id is not None and task_id!=actual):
        raise ValueError('Declared task and model profile differ')
    if profile.get('schema')!='qlm-mujoco-original-task-v1':
        raise ValueError('Public MuJoCo entry requires an explicit original-asset resource profile')
    if profile.get('instruction') not in [load_registration(actual,ready=True)['instruction'],*load_registration(actual,ready=True).get('previous_instructions',[])]:
        raise ValueError('Model profile instruction differs from the registered task')
    from qlm_bench.tasks.prompts import current_instruction_profile
    return current_instruction_profile(profile)


def create_runtime(task_id,backend,**kwargs):
    binding=backend_binding(task_id,backend)
    if binding.get('approved_six'):
        from qlm_bench.tasks.registration import resolve_symbol
        load_model_profile(kwargs['model_path'],task_id=task_id)
        return resolve_symbol(binding['runtime'])(**kwargs)
    if backend=='isaac':
        # Caller owns AppLauncher lifecycle; the original environment factory is
        # still the only Isaac scene/controller construction path.
        from rambo.tasks.common.controller_runtime import ControllerRuntime
        return ControllerRuntime(load_registration(task_id,ready=True)['gym_id'],**kwargs)
    from .mujoco.defaults import resolve_model,validate_default_identity
    model=resolve_model(kwargs.pop('model_path',None),task_id=task_id,model_root=kwargs.pop('model_root',None))
    load_model_profile(model,task_id=task_id)
    from .mujoco.resources import resource_closure
    resources=resource_closure(model,require_portable=True)
    validate_default_identity(model,resources)
    from .mujoco.runtime import MuJoCoRuntime
    return MuJoCoRuntime(model,backend=backend,**kwargs)
