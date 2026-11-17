"""Construct the approved (LLM-drafted, human-reviewed) high-level executor of an articulated task."""
import json
import sys
from pathlib import Path


class ApprovedExpert:
    """``ApprovedExpert(task_id)`` returns the executor instance with its approved recipe."""
    def __new__(cls, task_id, config=None):
        from qlm_bench.synthesis.bindings import binding, load_module, REFERENCES
        b = binding(task_id)
        old = REFERENCES / 'runs/audit/remaining-six-reference-20261016-v1'
        for p in (old, old / 'pairs/drawer-door', Path(b['nominal_executor']).parent):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
        module = load_module(b.get('scope_executor', b['nominal_executor']), 'approved_executor_' + task_id)
        name = b.get('scope_class_name', b.get('class_name', 'Sweep'))
        if config is None:
            config = b.get('recipe_config', json.loads(Path(b['recipe']).read_text()) if 'recipe' in b else {})
        return getattr(module, name)(config)
