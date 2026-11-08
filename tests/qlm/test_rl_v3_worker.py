"""rl-v3/QLM-SIM-001 privileged rows and rl-v3/QLM-SIM-002 own-state RPCs on the real CPU worker path.

The real tests drive ``AnchorWorker._dispatch`` on an actual NativeCPU/RAMBOCPU/OSMesa runtime with a
short prefix of a train demonstration (no whole-episode rollout). Inputs default to the local
RL-v2 configured Push binding and can be overridden by QLM_RLV3_BINDING / QLM_RAMBO_CHECKPOINT.
"""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from qlm_bench.rl_v2.worker import AnchorWorker

WORKSPACE = Path(__file__).resolve().parents[4]
BINDING = Path(os.environ.get('QLM_RLV3_BINDING', WORKSPACE / 'runs/audit/rl-v2-dual-task-20261026-v1/configured/push_box/pool/push100-20261014-036/binding.json'))
CONTROLLER = Path(os.environ.get('QLM_RAMBO_CHECKPOINT', WORKSPACE / 'checkpoints/rambo/go2/quadruped/model_2000.pt'))
REAL = pytest.mark.skipif(not BINDING.exists() or not CONTROLLER.exists() or os.environ.get('MUJOCO_GL') != 'osmesa',
                          reason='Local binding, RAMBO checkpoint and MUJOCO_GL=osmesa required')


def request(i, operation, payload, session='s1'):
    return {'schema': 'qlm-rl-v2-ipc-v1', 'id': i, 'operation': operation, 'session': session, 'payload': payload}


def resolved_binding():
    b = json.loads(BINDING.read_text())
    model = Path(b['model'])
    if not model.exists():  # Configured locator moved; the scene recorded by the demonstration is identical.
        b['model'] = b['scene']['model']
    return b


def real_worker(state_root=None):
    import torch
    from qlm_bench.backends.factory import create_runtime
    from qlm_bench.backends.mujoco.rl_v2.snapshot import load, restore
    from qlm_bench.backends.mujoco.rl_v2.storage import sha256
    torch.set_num_threads(1)
    b = resolved_binding();scene = b['scene']
    rt = create_runtime(b['episode']['task'], 'native', model_path=b['model'], checkpoint=str(CONTROLLER), trace_only=False,
                        device='cpu', seed=scene['seed'], rgb_profile='dual-rgb-360p-v1',
                        profile_override={k: scene[k] for k in ('goal_x', 'goal_y', 'canonical_goal_position') if k in scene})
    rt.renderer.observer_clip = None;rt.observation_ticks = 40
    rt.set_case_seed(scene['seed']);rt.reset(initial_state=scene['initial_state'])
    w = object.__new__(AnchorWorker)
    w.runtime = rt;w.load, w.restore = load, restore;w.seen = {};w.last_id = None;w.last_response = None
    w.session = 's0';w.poisoned = False;w.ended = False;w.anchor_tick = 0;w.chunk = 0;w.last_rgb = rt.state()['rgb']
    w.state_root = None if state_root is None else str(state_root);w.binding_sha256 = sha256(BINDING)
    commands = [json.loads(x)['requested'] for x in Path(b['commands']).read_text().splitlines()]
    return w, commands, b


def run_chunks(w, commands, first, count, session):
    out = []
    for k in range(first, first + count):
        r = w.handle(request(f'{session}-x{k}', 'execute', {'commands': commands[16 * k:16 * k + 16], 'chunk': k - first}, session))
        assert r['ok'], r
        out.append(r['result'])
    return out


@REAL
def test_privileged_rows_match_runtime_geometry_and_do_not_change_execution(monkeypatch):
    from qlm_bench.rl_v3 import privileged
    w, commands, b = real_worker()
    try:
        results = run_chunks(w, commands, 0, 3, 's0')
        rt = w.runtime
        names = results[0]['privileged']['columns'];col = {n: i for i, n in enumerate(names)}
        assert len(names) == 2 + 24 + 4 + 7 + 5 + 7 + 3 + 3 and names[-1] == 'terminal_code'
        for res in results:
            rows = np.asarray(res['privileged']['rows'])
            assert rows.shape == (16, len(names)) and np.isfinite(rows).all() and res['privileged']['terminal'] is None
            assert rows[:, col['tick']].tolist() == [c['end_tick'] for c in res['commands']]
            assert rows[-1, col['progress']] == res['progress'] and (rows[:, col['completed']] == 1).all()
            np.testing.assert_array_equal(rows[:, [col['goal_x0'], col['goal_x1'], col['goal_y0'], col['goal_y1']]],
                                          np.tile([*b['scene']['goal_x'], *b['scene']['goal_y']], (16, 1)))
        # Last row equals the live geometry, contact flags of state_channels and the root pose.
        last = np.asarray(results[-1]['privileged']['rows'][-1])
        np.testing.assert_array_equal(last[col['corner0_x']:col['corner7_z'] + 1], rt.task.geometry(0)[2].reshape(-1))
        ch = rt.state()['state']
        assert last[col['fl_object_contact']] == float(ch['task.contact.fl_object'][0])
        assert last[col['body_object_contact']] == float(ch['task.contact.body_object'][0])
        np.testing.assert_allclose(last[col['base_x']:col['base_z'] + 1], ch['observation.state.base.position'], atol=1e-6)
        np.testing.assert_allclose(last[col['object_center_x']:col['object_center_z'] + 1], rt.task.geometric_center(0))
        # A second identical run with the privileged reads stubbed out is bitwise identical (pure reads).
        reference = {'q': rt.physics.snapshot()['qpos'].copy(), 'freeze': results[-1]['freeze'],
                     'rgb': [s['rgb'] for r in results for s in r['samples']]}
    finally:
        w.close()
    monkeypatch.setattr(privileged, 'row', lambda rt, **kw: [0.])
    w, commands, _ = real_worker()
    try:
        plain = run_chunks(w, commands, 0, 3, 's0')
        assert plain[-1]['freeze'] == reference['freeze']
        np.testing.assert_array_equal(w.runtime.physics.snapshot()['qpos'], reference['q'])
        for a, s in zip(reference['rgb'], [s['rgb'] for r in plain for s in r['samples']]):
            for view in a:
                np.testing.assert_array_equal(a[view], s[view])
    finally:
        w.close()


def test_rejected_commands_report_terminal_reason_without_rows():
    class Runtime:
        terminal = None
        physics = SimpleNamespace(ticks=np.array([320]))
        outcome = {'success': False, 'fallen': False, 'timed_out': False, 'progress': .1}
        task = SimpleNamespace(task='press_button', geometry=lambda i: (None, None, np.zeros((1, 3))))
        def state(self): return {'rgb': {'ego': np.zeros((2, 2, 3), np.uint8)}}
        def freeze_token(self): return {'tick': 320}
    w = object.__new__(AnchorWorker);w.runtime = Runtime();w.poisoned = False;w.ended = False;w.session = 's';w.anchor_tick = 0;w.chunk = 0
    out = w._dispatch(request('1', 'execute', {'commands': np.full((16, 9), 1e100).tolist(), 'chunk': 0}, 's'))
    p = out['privileged']
    assert p['rows'] == [] and p['terminal'] == {'reason': 'policy_command_rejected', 'tick': 320, 'code': 5}
    assert p['columns'][0] == 'tick' and 'goal_x0' not in p['columns'] and 'button_displacement' in p['columns']
