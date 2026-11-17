"""Approved executor bindings of the six articulated tasks (from references/approved-six-task-bindings.json)."""
import importlib.util
import json
from pathlib import Path

from qlm_bench.backends.mujoco.articulated_tasks import TASKS
from qlm_bench.synthesis.references import BINDINGS, REFERENCES, resolve


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolved(value):
    if isinstance(value, dict):
        return {k: _resolved(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolved(v) for v in value]
    return resolve(value)


def binding(task_id):
    if task_id not in TASKS:
        raise ValueError('Not an articulated task: ' + str(task_id))
    result = _resolved(next(t for t in json.loads(BINDINGS.read_text())['tasks'] if t['task_id'] == task_id))
    if task_id == 'pull_open_drawer':
        # The binding names the nominal class; the approved scope adapter (randomized frame) is in the proposal.
        evidence = json.loads(Path(result['scope_evidence']).read_text())
        scope = json.loads(Path(resolve(evidence['proposal'])).read_text())
        result.update(scope_executor=resolve(scope['executor']), scope_class_name=scope['executor_class'])
    return result
