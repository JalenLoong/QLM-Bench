"""Historical production/expert bindings; learned runtime never imports this module."""
import hashlib
import importlib.util
import json
from pathlib import Path
from .remaining_tasks import TASKS

WORKSPACE = next((p for p in Path(__file__).resolve().parents if (p / 'workspace.env').is_file()), None)
BINDINGS = (WORKSPACE or Path('/unavailable-qlm-production-workspace')) / 'runs/audit/remaining-six-handoff-20261016-v1/approved-six-task-bindings.json'



def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def binding(task_id):
    if task_id not in TASKS:
        raise ValueError('Unknown approved remaining task')
    result = next(t for t in json.loads(BINDINGS.read_text())['tasks'] if t['task_id'] == task_id)
    if task_id == 'pull_open_drawer':
        # The handoff names the nominal class; qualification-v5 names the
        # already approved randomized-frame adapter. Preserve both identities.
        qualification = Path(result['scope_evidence'])
        evidence = json.loads(qualification.read_text())
        proposal = Path(evidence['proposal'])
        if hashlib.sha256(proposal.read_bytes()).hexdigest() != evidence['proposal_sha256']:
            raise ValueError('Drawer scope proposal changed')
        scope = json.loads(proposal.read_text())
        if not evidence['all16_actual_success']:
            raise ValueError('Drawer complete scope qualification required')
        result.update(scope_executor=scope['executor'], scope_class_name=scope['executor_class'],
                      scope_executor_sha256=scope['executor_sha256'],
                      scope_binding_files=[str(qualification), str(proposal)])
    return result

