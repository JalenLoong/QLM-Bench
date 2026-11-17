"""Offline audit of an articulated-task physical trace: reconstruct every boundary and re-check success."""
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from qlm_bench.backends.mujoco.articulated_tasks import ArticulatedTaskState, PREDICATES


def audit_articulated_trace(path):
    """Reconstruct every actual boundary; never step physics or load RAMBO."""
    import mujoco
    from types import SimpleNamespace
    from qlm_bench.synthesis.trace import verify_trace, sha, SNAPSHOT_ARRAYS
    from qlm_bench.backends.mujoco.resources import resource_closure
    from qlm_bench.synthesis.quality import contact_evidence
    from qlm_bench.data.lerobot.validation import digest
    m, arrays, telemetry, commands, terminal = verify_trace(path)
    task = m['profile']['task_id']
    model_path = m['scene']['model']
    if resource_closure(model_path, require_portable=True)['identity'] != m['model_identity']:
        raise ValueError('Physical model resource changed')
    model = mujoco.MjModel.from_xml_path(model_path)
    data = mujoco.MjData(model)
    profile = json.loads(Path(model_path).with_suffix('.task.json').read_text())
    # Horizon is explicitly selected at runtime; all task geometry remains exact.
    for key in ('primary_joint', 'canonical_goal_position', 'goal_x', 'goal_y', 'sweep_direction_xy',
                'initial_center_xy', 'closed_tolerance_rad', 'target_min_rad', 'target_extension_m',
                'task_success_profile', 'target_open_rad', 'bolt_joint', 'lever_joint', 'unlock_lever_max_rad'):
        if key in profile and m['profile'].get(key) != profile[key]:
            raise ValueError('Trace task geometry/profile differs: ' + key)
    physics = SimpleNamespace(model=model, data=[data], count=1, ticks=np.zeros(1, np.int64))
    state = ArticulatedTaskState(physics, m['profile'])
    base = model.body('base').id
    first = None
    hold = 0
    for k in ('qpos', 'qvel'):
        np.testing.assert_array_equal(arrays[k][0], m['scene']['initial_state'][k])
    for i, boundary in enumerate(telemetry['boundaries']):
        for key in SNAPSHOT_ARRAYS:
            getattr(data, key)[:] = arrays[key][i]
        data.time = float(arrays['time'][i])
        mujoco.mj_forward(model, data)
        physics.ticks[0] = i * 10
        observed = boundary['state']
        np.testing.assert_allclose(observed['task.object.position'], data.xpos[state.body], rtol=0, atol=1e-7)
        np.testing.assert_allclose(observed['task.object.orientation'], data.xquat[state.body][[1, 2, 3, 0]], rtol=0, atol=1e-7)
        np.testing.assert_allclose(observed['task.goal.position'], profile['canonical_goal_position'], rtol=0, atol=1e-7)
        np.testing.assert_allclose(observed['task.progress'], [state.progress(0)], rtol=0, atol=1e-7)
        inside = state.condition(0)
        notfallen = data.xpos[base, 2] >= .1 and np.linalg.norm(-data.xmat[base].reshape(3, 3)[2, :] - [0, 0, -1]) <= .75
        hold = hold + 1 if i >= 105 and inside and notfallen else 0
        if hold >= 3 and first is None:
            first = i
    if first != m['n_actions'] or terminal['success'] is not True or not m['terminal_before_reset']:
        raise ValueError('Original success predicate/first-success terminal mismatch')
    evidence = contact_evidence(telemetry['boundaries'])
    quality = {k: evidence[k] for k in ('fl_contact_boundaries', 'body_contact_boundaries')}
    if quality != m['quality']:
        raise ValueError('Captured contact counts differ')
    quality.update({PREDICATES[task]: True, 'not_fallen': True})
    h = hashlib.sha256()
    for k in ('qpos', 'qvel', 'simulation_time_ns'):
        h.update(k.encode()); h.update(arrays[k].tobytes())
    h.update(np.asarray([c['executed'] for c in commands], np.float32).tobytes())
    return dict(manifest_sha256=sha(Path(path) / 'manifest.json'), trajectory_sha256=h.hexdigest(),
                model_identity=m['model_identity'], source_identity_sha256=digest(m['batch_identity']),
                quality=quality, n_actions=m['n_actions'], n_boundaries=m['n_boundaries'],
                task_id=task, physical_source=copy.deepcopy(m['batch_identity']), scene=copy.deepcopy(m['scene']))
