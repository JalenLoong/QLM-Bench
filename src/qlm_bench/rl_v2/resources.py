"""Public scene-resource admission; this operation does not initialize simulation."""
from pathlib import Path


def verify_scene_resource(model, expected_identity):
    from qlm_bench.backends.mujoco.resources import resource_closure
    path=Path(model).resolve()
    if resource_closure(path,require_portable=True)['identity']!=expected_identity:
        raise ValueError('Scene resource differs from demonstration: '+str(path))
    return str(path)
