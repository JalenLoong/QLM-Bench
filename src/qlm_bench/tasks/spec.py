"""Pure task identity and evaluator dependencies, independent of Isaac and models."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from qlm_bench.policy_interface.physical import identity

TASK_IDS = ("push_box", "lift_basket", "press_button")


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
        if self.task_id not in TASK_IDS:
            raise ValueError("Task is outside the current Go2 three-task registry")
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
    if task_id not in TASK_IDS:
        raise ValueError("Task is outside the current three-task registry")
    root = Path(__file__).with_name("spec")
    registry = json.loads((root / "registry.json").read_text())
    entry = registry["tasks"][task_id]
    path = root / entry["file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        raise ValueError("Task declaration identity mismatch")
    value = json.loads(path.read_text())
    return TaskSpec(**{key: value[key] for key in TaskSpec.__dataclass_fields__})
