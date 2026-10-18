"""Explicit NativeCPU producer entry for the approved six tasks."""
import sys
from pathlib import Path
from .runtime import MuJoCoRuntime
from .remaining_tasks import RemainingTaskState
from .trace import sha


class RemainingRuntime(MuJoCoRuntime):
    def __init__(self, model_path, checkpoint, *, seed=42, horizon_s=None, **kwargs):
        if kwargs.pop('backend', 'native') != 'native':
            raise ValueError('Current six-task production is qualified NativeCPU only')
        if kwargs.pop('device', 'cpu') != 'cpu':
            raise ValueError('Original RAMBO CPU route required')
        overlay = dict(kwargs.pop('profile_override', {}) or {})
        if horizon_s is not None: overlay['horizon_s'] = horizon_s
        super().__init__(model_path, checkpoint, seed=seed, backend='native', device='cpu',
                         trace_only=kwargs.pop('trace_only', True), task_state_factory=RemainingTaskState,
                         profile_override=overlay or None, **kwargs)


class ApprovedExpert:
    """Construct the exact approved executor, including all inherited defaults."""
    def __new__(cls, task_id, config=None):
        from .remaining_bindings import binding, load_module, WORKSPACE
        b = binding(task_id)
        if sha(b['nominal_executor']) != b['nominal_executor_sha256']:
            raise ValueError('Approved nominal executor changed')
        old = WORKSPACE / 'runs/audit/remaining-six-reference-20261016-v1'
        for p in (old, old / 'pairs/drawer-door', Path(b['nominal_executor']).parent):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
        path = b.get('scope_executor', b['nominal_executor'])
        if 'scope_executor_sha256' in b and sha(path) != b['scope_executor_sha256']:
            raise ValueError('Approved scope executor changed')
        module = load_module(path, 'approved_production_' + task_id)
        name = b.get('scope_class_name', b.get('class_name', 'Sweep'))
        if config is None:
            import json
            config = b.get('recipe_config', json.loads(Path(b['recipe']).read_text()) if 'recipe' in b else {})
        return getattr(module, name)(config)
