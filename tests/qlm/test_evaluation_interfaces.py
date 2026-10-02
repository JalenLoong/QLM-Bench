"""CPU engineering evidence only; fake runtime outcomes are never benchmark scores."""
from copy import deepcopy
from dataclasses import replace
import json
import subprocess
import sys

import numpy as np
import pytest

from qlm_bench.evaluation import (
    EvalCase, EvaluationProtocol, EvaluationRunner, StepResult, TerminalSnapshot,
    TrialSpec, load_case, validate_result, write_result,
)
from qlm_bench.policy_interface import (
    ExecutionAck, ExecutionHistory, Native9Command, ObservationProfile, StateChannels,
    build_observation,
)
from qlm_bench.policy_interface.physical import ROOT_FIELDS
from qlm_bench.tasks import TaskSpec
from qlm_bench.backends.isaac import ControllerRuntimeAdapter, RuntimeAdapter, RuntimeBindings


def profile(state=False):
    semantics = {"reference": "root_link", "quaternion": "xyzw", "velocity_frame": "world",
                 "projected_gravity_frame": "body", "ground_z": 0.,
                 "ground_reference": "push-box-v2-plane-world-z0"} if state else {}
    return ObservationProfile("root-state" if state else "dual-rgb", ("go2_ego", "d435i_rgb_task"),
                              ROOT_FIELDS if state else (), True, semantics)


def case(case_id="case-1", task_id="push_box", status="engineering_fixture"):
    evidence = {"evidence_kind": "actual_runtime", "reset_reconstruction_passed": True,
                "evidence_sha256": "b" * 64} if status == "verified" else {"kind": "engineering_fixture"}
    return EvalCase(case_id, task_id, "accepted-profile", "Push the box", profile(), {"object": "fixture-asset-v1"},
                    {"robot": [0, 0, 0], "object": [0, 1, 0]}, {"fixture_goal": [1, 2]},
                    {"floor": "fixture-floor"}, {key: {"profile": "fixed"} for key in profile().camera_keys},
                    17, "fixed-rambo", "fixed-isaac", {"settle": "explicit-fixture-reset"},
                    evidence, status)


def protocol(trials=None, *, scope="engineering_diagnostic", error_policy="count_as_failure",
             retry_selection="first_attempt", status="draft", budget=3):
    return EvaluationProtocol("test-protocol", "fixture-suite", "fixture-cases", "fixed-isaac", "fixed-rambo",
                              budget, error_policy, retry_selection, scope, status,
                              tuple(trials or [TrialSpec("trial-1", "case-1", "push_box", 23)]),
                              {"source_commit": "a" * 40 if scope == "benchmark" else "fixture-source",
                               "spec_sha256": "a" * 64})


def packet(time_ns=0, *, epoch=1, uid="episode-1"):
    state = dict(zip(ROOT_FIELDS, ([0, 0, .3], [0, 0, 0, 1], [1, 2, 3], [4, 5, 6], [0, 0, -1])))
    state["task.object.pose"] = [99, 99, 99]
    return StateChannels(uid, epoch, time_ns,
                         {key: np.zeros((2, 3, 3), np.uint8) for key in profile().camera_keys},
                         "Push the box", state, {"actor_history": [99]}, {"goal": [99], "object": [99]})


def command(**changes):
    values = {"episode_uid": "episode-1", "reset_epoch": 1, "command_id": "command-1"}
    values.update(changes)
    return Native9Command.from_values([.1, 0, 0, .3, .2, -.1, 0, 0, 0], **values)


def ack(cmd, start=0, *, partial=False):
    return ExecutionAck(cmd.episode_uid, cmd.reset_epoch, cmd.command_id, start,
                        start + (10_000_000 if partial else 20_000_000), cmd.execution, not partial)


def test_plain_imports_do_not_load_model_or_simulator():
    source = """import sys
import qlm_bench.evaluation, qlm_bench.tasks, qlm_bench.backends.isaac
assert not any(n == x or n.startswith(x + '.') for n in sys.modules
               for x in ('rambo', 'isaaclab', 'isaacsim', 'omni', 'torch', 'transformers', 'wam_policy'))
"""
    subprocess.run([sys.executable, "-c", source], check=True)


def test_public_observation_excludes_private_fields_and_owns_rgb():
    channels = packet()
    obs = build_observation(channels, profile(), ExecutionHistory("episode-1", 1))
    assert not obs.proprioception and not obs.state_semantics
    assert not hasattr(obs, "controller_private") and not hasattr(obs, "evaluator_private")
    channels.rgb["go2_ego"][:] = 1
    assert not obs.rgb["go2_ego"].any() and not obs.rgb["go2_ego"].flags.writeable
    state_obs = build_observation(packet(), profile(True), ExecutionHistory("episode-1", 1))
    assert set(state_obs.proprioception) == set(ROOT_FIELDS)
    assert state_obs.state_semantics["reference"] == "root_link"
    assert state_obs.proprioception[ROOT_FIELDS[2]] == (1., 2., 3.)  # still world-frame, adapter derives body


@pytest.mark.parametrize("field,value", [("reference", "com"), ("quaternion", "wxyz"),
                                        ("velocity_frame", "body"), ("ground_z", float("nan"))])
def test_state_profile_cannot_silently_change_frame(field, value):
    original = profile(True)
    wrong = dict(original.state_semantics, **{field: value})
    with pytest.raises(ValueError):
        replace(original, state_semantics=wrong)


def test_native9_is_single_command_float32_and_explicit_force_zero():
    original = [.1, 0, 0, .3, .2, -.1, 3, 4, 5]
    cmd = Native9Command.from_values(original, episode_uid="episode-1", reset_epoch=1, command_id="one")
    assert cmd.requested == tuple(original)
    assert cmd.execution[:6] == tuple(np.asarray(original, np.float32).astype(float)[:6])
    assert cmd.execution[6:] == (0., 0., 0.)
    assert original[6:] == [3, 4, 5]


@pytest.mark.parametrize("values", [[0] * 6, [False] * 9, ["0"] * 9,
                                   [float("nan")] * 9, [1e100] * 9])
def test_invalid_physical_command_rejected(values):
    with pytest.raises(ValueError):
        Native9Command.from_values(values, episode_uid="e", reset_epoch=0, command_id="one")


def test_history_ack_partial_duplicate_and_reset_boundaries():
    history = ExecutionHistory("episode-1", 1)
    first = command()
    history.accept(first, ack(first))
    assert len(history.completed) == 1
    with pytest.raises(ValueError):
        history.accept(first, ack(first))
    stale = command(command_id="stale", reset_epoch=0)
    with pytest.raises(ValueError):
        history.validate_command(stale)
    second = command(command_id="partial")
    history.accept(second, ack(second, 20_000_000, partial=True))
    assert len(history.completed) == 1
    fresh = ExecutionHistory("episode-2", 2)
    assert not fresh.completed
    with pytest.raises(ValueError):
        build_observation(packet(), profile(), fresh)


def test_case_loader_requires_more_than_seed_and_has_no_task_defaults(tmp_path):
    original = case()
    path = tmp_path / "case.json"
    path.write_text(json.dumps(original.record()))
    assert load_case(path).record() == original.record()
    with pytest.raises(ValueError):
        replace(original, initial_state={})
    with pytest.raises(ValueError):
        replace(original, validation_status="ready")
    with pytest.raises(ValueError):
        replace(original, validation_status="verified")
    with pytest.raises(ValueError):
        replace(protocol(), max_commands=0)
    with pytest.raises(ValueError):
        TaskSpec("biped", "v1", ("x",), ("a",), ("s",), "success", "failure")
    spec = TaskSpec("lift_basket", "accepted-profile", ("Lift basket",), ("basket",),
                    ("minimum_world_z", "fallen"), "accepted-clearance-predicate", "accepted-fall")
    assert not hasattr(spec, "minimum_clearance_m")  # values belong to accepted profile, no new default


class Provider:
    def reset(self, context):
        assert not hasattr(context, "goal") and not hasattr(context, "initial_state")
        assert context.policy_seed == 23
        self.count = 0

    def command(self, obs):
        self.count += 1
        return Native9Command.from_values([0] * 9, episode_uid=obs.episode_uid,
                                         reset_epoch=obs.reset_epoch, command_id=str(self.count))


class FakeRuntime:
    def __init__(self, *, outcome="success", partial=False):
        self.outcome = outcome
        self.partial = partial
        self.time = 0
        self.closed = False

    def reset(self, case):
        self.time = 0

    def observe(self):
        return packet(self.time)

    def step(self, cmd):
        evidence = ack(cmd, self.time, partial=self.partial)
        self.time = evidence.end_ns
        return StepResult(evidence, self.outcome is not None)

    def terminal(self, *, reason=None):
        outcome = self.outcome if reason is None else "timeout"
        return TerminalSnapshot("episode-1", 1, self.time, outcome, outcome,
                                {"fixture": True}, packet().rgb, True)

    def close(self):
        self.closed = True


def runner(proto=None, *, factory=None, provider_factory=None, cases=None, evidence="engineering_fixture"):
    return EvaluationRunner(proto or protocol(), cases or {"case-1": case()},
                            runtime_factory=factory or (lambda _: FakeRuntime()),
                            provider_factory=provider_factory or (lambda _: Provider()),
                            source_commit="b" * 40 if evidence == "actual_runtime" else "fixture-source", policy_identity={"code": "fixture",
                            "adapter": "test-provider", "observation_profile": "dual-rgb"},
                            evidence_kind=evidence)


def test_runner_diagnostic_has_no_formal_score_and_records_partial():
    runtime = FakeRuntime(partial=True)
    result = runner(factory=lambda _: runtime).run(submission_id="local-test")
    assert runtime.closed
    row = result["outcomes"][0]
    assert row["outcome"] == "success" and row["executed_commands"] == 0
    assert row["partial_intervals"] == 1 and row["terminal_before_reset"]
    assert not result["validation"]["formal_score_available"]
    assert not result["validation"]["publishable"]
    assert result["validation"]["metrics"]["per_task"]["push_box"]["success_rate"] is None


def test_command_budget_is_explicit_timeout():
    result = runner(protocol(budget=2), factory=lambda _: FakeRuntime(outcome=None)).run(submission_id="budget-test")
    assert result["outcomes"][0]["outcome"] == "timeout"
    assert result["outcomes"][0]["executed_commands"] == 2
    assert result["outcomes"][0]["simulation_time_ns"] == 40_000_000


def test_stale_action_is_rejected_before_runtime_execution():
    class Stale(Provider):
        def command(self, obs):
            return command(reset_epoch=0)
    runtime = FakeRuntime()
    result = runner(factory=lambda _: runtime, provider_factory=lambda _: Stale()).run(submission_id="stale")
    assert result["outcomes"][0]["outcome"] == "error" and runtime.time == 0


def test_errors_and_interruptions_keep_complete_expected_trial_table():
    trials = [TrialSpec(f"trial-{i}", "case-1", "push_box", 23) for i in (1, 2, 3)]
    class Interrupted(Provider):
        def command(self, obs):
            raise KeyboardInterrupt()
    result = runner(protocol(trials), provider_factory=lambda _: Interrupted()).run(submission_id="interrupt")
    assert [row["outcome"] for row in result["outcomes"]] == ["error", "not_run", "not_run"]
    assert result["validation"]["expected_trials"] == 3
    incomplete = result["outcomes"][:-1]
    with pytest.raises(ValueError, match="Missing expected trials"):
        validate_result(result["run_manifest"], incomplete)


def formal_result(*, error_policy="count_as_failure", retry_selection="first_attempt"):
    proto = protocol(scope="benchmark", status="verified", error_policy=error_policy,
                     retry_selection=retry_selection)
    return runner(proto, cases={"case-1": case(status="verified")}, evidence="actual_runtime").run(
        submission_id="unit-test-only", benchmark_release="unit-test-fixture-do-not-publish")


def test_formal_metric_schema_preserves_failure_denominator_and_retry_chain():
    result = formal_result()
    manifest, rows = result["run_manifest"], deepcopy(result["outcomes"])
    rows[0].update(outcome="failure", termination_reason="fall")
    retry = dict(rows[0], attempt_id="retry-2", retry_of=rows[0]["attempt_id"], outcome="success",
                 termination_reason="success")
    rows.append(retry)
    report = validate_result(manifest, rows)
    assert report["metrics"]["per_task"]["push_box"]["success_rate"] == 0
    manifest["protocol"]["retry_selection"] = "last_attempt"
    assert validate_result(manifest, rows)["metrics"]["per_task"]["push_box"]["success_rate"] == 1
    rows[1]["retry_of"] = None
    with pytest.raises(ValueError):
        validate_result(manifest, rows)


@pytest.mark.parametrize("error_policy,status", [("count_as_failure", "scored"), ("invalidate", "invalid_error")])
def test_declared_error_policy_controls_scoring(error_policy, status):
    result = formal_result(error_policy=error_policy)
    result["outcomes"][0].update(outcome="error", termination_reason="controller_error")
    assert validate_result(result["run_manifest"], result["outcomes"])["metrics"]["status"] == status


def test_unverified_cases_and_fixture_publication_cannot_become_formal():
    with pytest.raises(ValueError):
        runner(protocol(scope="benchmark", status="verified"))
    result = runner().run(submission_id="fixture")
    result["run_manifest"]["publication_status"] = "staged"
    with pytest.raises(ValueError):
        validate_result(result["run_manifest"], result["outcomes"])


def test_actual_engineering_runtime_does_not_become_a_benchmark_publication():
    result = runner(evidence="actual_runtime").run(submission_id="diagnostic-real-runtime")
    report = validate_result(result["run_manifest"], result["outcomes"])
    assert report["metrics"]["status"] == "engineering_diagnostic"
    assert not report["formal_score_available"]
    assert not report["publishable"]


def test_local_artifact_writes_real_parquet_and_roundtrips(tmp_path):
    pq = pytest.importorskip("pyarrow.parquet")
    result = runner().run(submission_id="fixture-artifact")
    root = tmp_path / "new"
    report = write_result(root, result["run_manifest"], result["outcomes"])
    assert not report["publishable"]
    loaded = pq.read_table(root / "episodes.parquet").to_pylist()
    assert validate_result(json.loads((root / "run_manifest.json").read_text()), loaded)["passed"]
    with pytest.raises(FileExistsError):
        write_result(root, result["run_manifest"], result["outcomes"])


def test_lazy_adapter_uses_actual_confirmed_native_runtime_history():
    from rambo.tasks.common.episode import EpisodeRuntime
    class Environment:
        def __init__(self):
            self.runtime = EpisodeRuntime()
            self.tick = 0
            self.closed = False

        @property
        def episode_tick(self):
            return self.runtime.clock.tick(self.tick)

        def submit_native9_command(self, prepared):
            self.runtime.submit(prepared, self.tick)

        def close(self):
            self.closed = True

    env = Environment()
    def reset(env, case):
        env.tick = 0
        env.runtime.reset(0)

    def observe(env):
        return packet(env.runtime.clock.time_ns(env.tick), epoch=env.runtime.clock.reset_epoch)

    def advance(env, prepared):
        start = env.runtime.clock.time_ns(env.tick)
        for _ in range(2):
            env.tick += 5
            env.runtime.confirm_control(env.tick)
        completed = env.runtime.history[-1]
        return StepResult(ExecutionAck("episode-1", env.runtime.clock.reset_epoch, completed["command_id"],
                                      start, env.runtime.clock.time_ns(env.tick),
                                      tuple(completed["executed"]), True), True)

    def terminal(env, reason):
        return TerminalSnapshot("episode-1", env.runtime.clock.reset_epoch,
                                env.runtime.clock.time_ns(env.tick), "success", "task_success",
                                {"test_fixture": True}, packet().rgb, True)

    bindings = RuntimeBindings(reset, observe, advance, terminal)
    result = runner(factory=lambda _: RuntimeAdapter(env, bindings)).run(submission_id="adapter-test")
    assert result["outcomes"][0]["outcome"] == "success"
    assert result["outcomes"][0]["executed_commands"] == 1
    assert env.closed and len(env.runtime.history) == 1


def test_result_manifest_binds_case_assets_and_action_semantics():
    result = runner().run(submission_id="identity")
    for key in ("case_identity", "action_scheduling"):
        bad = deepcopy(result["run_manifest"])
        bad.pop(key)
        with pytest.raises(ValueError):
            validate_result(bad, result["outcomes"])
    bad_rows = deepcopy(result["outcomes"])
    bad_rows[0]["terminal_evidence"] = None
    with pytest.raises(ValueError, match="terminal task state"):
        validate_result(result["run_manifest"], bad_rows)


def test_controller_adapter_preserves_terminal_when_environment_auto_resets():
    from rambo.tasks.common.episode import EpisodeRuntime
    class Controller:
        def __init__(self):
            self.runtime = EpisodeRuntime()
            self.tick = 0
            self.closed = False

        def reset(self):
            self.tick = 0
            self.runtime.reset(0)

        def state(self):
            p = packet()
            return {"simulation_time_ns": self.runtime.clock.time_ns(self.tick),
                    "physics_step": self.tick, "reset_epoch": self.runtime.clock.reset_epoch,
                    "state": deepcopy(dict(p.root_state)),
                    "rgb": {"ego": p.rgb["go2_ego"], "task_centric": p.rgb["d435i_rgb_task"]},
                    "outcome": self.runtime.outcome}

        def step(self, prepared):
            self.runtime.submit(prepared, self.tick)
            for _ in range(2):
                self.tick += 5
                self.runtime.confirm_control(self.tick)
            terminal = {**self.state(), "success": True, "fallen": False,
                        "timed_out": False, "reason": "task_success"}
            completed = self.runtime.history[-1]
            self.reset()  # actual environment auto-reset must not overwrite terminal evidence
            return {"command": completed, "terminal": terminal,
                    "simulation_time_ns": terminal["simulation_time_ns"], "completed_interval": True}

        def close(self):
            self.closed = True

    controller = Controller()
    runtime = ControllerRuntimeAdapter(controller, reconstruct=lambda runtime, case: runtime.reset())
    result = runner(factory=lambda _: runtime).run(submission_id="auto-reset-fixture")
    row = result["outcomes"][0]
    assert row["outcome"] == "success" and row["simulation_time_ns"] == 20_000_000
    assert row["terminal_before_reset"] and row["executed_commands"] == 1
    assert controller.closed and controller.runtime.history == []
    with pytest.raises(ValueError, match="auto-reset"):
        runtime.observe()
