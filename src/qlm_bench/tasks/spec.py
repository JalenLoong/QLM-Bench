"""Pure task identity and evaluator dependencies, independent of Isaac and models."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from qlm_bench.policy_interface.physical import identity

from .registration import SCALEUP_TASK_IDS, registrations, load_registration
TASK_IDS = tuple(key for key, row in registrations().items() if row["status"] == "ready")


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    version: str
    instructions: tuple[str, ...]
    asset_ids: tuple[str, ...]
    required_evaluator_fields: tuple[str, ...]
    success_predicate: str
    failure_predicate: str

    def __post_init__(self):
        if self.task_id not in SCALEUP_TASK_IDS:
            raise ValueError("Task is outside the scale-up Go2 task registry")
        for name in ("version", "success_predicate", "failure_predicate"):
            identity(getattr(self, name), name)
        for name in ("instructions", "asset_ids", "required_evaluator_fields"):
            values = tuple(getattr(self, name))
            if not values or len(set(values)) != len(values):
                raise ValueError("Explicit unique " + name + " required")
            for value in values:
                identity(value, name)
            object.__setattr__(self, name, values)


def load_task_spec(task_id):
    """Load an accepted task declaration without installing a simulator."""
    registration = load_registration(task_id, ready=True)
    root = Path(__file__).with_name('spec')
    registry = json.loads((root / 'registry.json').read_text())
    entry = registry['tasks'].get(task_id)
    if registration.get('task_spec_sha256'):
        path = Path(__file__).parent / registration['task_spec']
        expected = registration['task_spec_sha256']
    elif entry is not None:
        path, expected = root / entry['file'], entry['sha256']
    else:
        path = Path(__file__).parent / registration['task_spec']
        expected = registration.get('task_spec_sha256')
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Task declaration identity mismatch')
    value = json.loads(path.read_text())
    return TaskSpec(**{key: value[key] for key in TaskSpec.__dataclass_fields__})
