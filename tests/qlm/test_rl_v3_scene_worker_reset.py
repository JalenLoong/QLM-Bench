"""Scene worker reset after an episode that ended without a terminal (rl-v3/QLM-SIM-004). No MuJoCo: the runtime and the case loader are stand-ins."""
from types import SimpleNamespace

from qlm_bench.rl_v3 import scene_worker


class StandInRuntime:
    def __init__(self, current, terminal):
        self.current, self.terminal, self.closed = current, terminal, False

    def close(self):
        self.closed = True


def worker_with(runtime):
    worker = scene_worker.SceneWorker.__new__(scene_worker.SceneWorker)  # no torch threads, no controller
    worker.runtime, worker.case_path = runtime, '/scene.json'
    return worker


def test_an_unfinished_episode_is_retired_before_a_reset():
    unfinished = StandInRuntime(current=object(), terminal=None)
    worker = worker_with(unfinished)
    worker._retire_unfinished_episode()
    assert unfinished.closed and worker.runtime is None and worker.case_path is None


def test_finished_or_fresh_runtimes_are_kept():
    for runtime in (StandInRuntime(current=object(), terminal={'reason': 'timeout'}), StandInRuntime(current=None, terminal=None)):
        worker = worker_with(runtime)
        worker._retire_unfinished_episode()
        assert not runtime.closed and worker.runtime is runtime and worker.case_path == '/scene.json'


def test_reset_loads_the_scene_after_retiring(monkeypatch):
    import qlm_bench.backends.mujoco.suite as suite
    unfinished = StandInRuntime(current=object(), terminal=None)
    worker = worker_with(unfinished)
    order = []
    def load_case(case_path, model_path):
        order.append(('load', worker.case_path, unfinished.closed))
        worker.runtime = StandInRuntime(current=None, terminal=None)
        return SimpleNamespace(case_id='c', seed=7)
    monkeypatch.setattr(worker, '_load_case', load_case)
    monkeypatch.setattr(worker, '_boundary', lambda: {'rgb': None})
    monkeypatch.setattr(suite, 'reconstruct', lambda runtime, case: order.append(('reconstruct', runtime is unfinished)))
    out = worker._reset('session', {'case': '/scene.json', 'model': '/model'})
    assert order == [('load', None, True), ('reconstruct', False)] and out['case_seed'] == 7 and worker.session == 'session'
