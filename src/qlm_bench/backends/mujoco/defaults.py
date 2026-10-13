"""CPU-only default resource selection; assets remain outside the installed wheel."""
import json
import os
from pathlib import Path


def default_model_set():
    return json.loads(Path(__file__).with_name('default-models.json').read_text())


def add_model_arguments(parser):
    parser.add_argument('--model', help='Explicit resource override for historical replay or diagnostics')
    parser.add_argument('--model-root', help='MuJoCo resource root; defaults to QLM_MUJOCO_MODEL_ROOT')
    parser.add_argument('--task', choices=tuple(default_model_set()['tasks']),
                        help='Required for default model selection; explicit --model may infer its task')


def resolve_model(model=None, *, task_id=None, model_root=None):
    """Select only the accepted LOD; missing assets never fall back to old rigs."""
    if model is not None:
        return Path(model).resolve(strict=True)
    profile = default_model_set()
    if task_id not in profile['tasks']:
        raise ValueError('Default MuJoCo model selection requires an implemented --task')
    root = model_root or os.environ.get('QLM_MUJOCO_MODEL_ROOT')
    if not root:
        raise ValueError('Set --model-root or QLM_MUJOCO_MODEL_ROOT for the accepted LOD assets')
    root = Path(root).resolve(strict=True)
    path = (root / profile['tasks'][task_id]['model']).resolve(strict=True)
    if not path.is_relative_to(root):
        raise ValueError('Default MuJoCo model escapes the declared resource root')
    return path


def validate_default_identity(model, resources):
    """Also enforce the accepted pin when an explicit path selects a default pack."""
    path = Path(model)
    for task in default_model_set()['tasks'].values():
        expected = Path(task['model'])
        if (path.parent.name, path.name) == (expected.parent.name, expected.name):
            if resources['identity'] != task['resource_identity']:
                raise ValueError('Default LOD resource identity differs from the accepted model set')
            return
