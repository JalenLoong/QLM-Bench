"""One physical 50 Hz command at a time, with explicit terminal and trial evidence."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import time
from typing import Mapping, Protocol

from qlm_bench.policy_interface import (
    ExecutionAck, ExecutionHistory, Native9Command, ProviderContext, StateChannels, build_observation,
)
from qlm_bench.policy_interface.physical import ACTION_SCHEMA, COMMAND_INTERVAL_NS, identity, timestamp
from .cases import EvalCase, EvaluationProtocol
from .results import RESULT_SCHEMA, validate_result


@dataclass(frozen=True)
class StepResult:
    ack: ExecutionAck
    terminal: bool

    def __post_init__(self):
        if not isinstance(self.ack, ExecutionAck) or type(self.terminal) is not bool:
            raise ValueError("Step requires a physical execution acknowledgement and explicit terminal flag")
        if not self.ack.completed_interval and not self.terminal:
            raise ValueError("A partial interval stops this rollout; it cannot silently replan")


@dataclass(frozen=True)
class TerminalSnapshot:
    episode_uid: str
    reset_epoch: int
    simulation_time_ns: int
    outcome: str
    termination_reason: str
    evaluator_state: Mapping
    rgb: Mapping
    captured_before_reset: bool

    def __post_init__(self):
        identity(self.episode_uid, "episode UID")
        timestamp(self.reset_epoch)
        timestamp(self.simulation_time_ns)
        identity(self.termination_reason, "termination reason")
        if self.outcome not in ("success", "failure", "timeout", "error") or \
                self.captured_before_reset is not True:
            raise ValueError("Terminal outcome requires an owned pre-reset snapshot")
        object.__setattr__(self, "evaluator_state", deepcopy(dict(self.evaluator_state)))
        object.__setattr__(self, "rgb", deepcopy(dict(self.rgb)))


class Runtime(Protocol):
    def reset(self, case: EvalCase) -> None: ...
    def observe(self) -> StateChannels: ...
    def step(self, command: Native9Command) -> StepResult: ...
    def terminal(self, *, reason: str | None = None) -> TerminalSnapshot: ...
    def close(self) -> None: ...


def _terminal_record(snapshot):
    if not snapshot.evaluator_state or not snapshot.rgb:
        raise ValueError("Terminal task state and policy RGB evidence are required")
    hashes = {}
    for key, rgb in snapshot.rgb.items():
        if not hasattr(rgb, "tobytes") or str(getattr(rgb, "dtype", None)) != "uint8" or \
                len(getattr(rgb, "shape", ())) != 3 or rgb.shape[-1] != 3 or \
                rgb.shape[0] < 1 or rgb.shape[1] < 1:
            raise ValueError("Terminal RGB must be actual uint8 HWC image arrays")
        hashes[key] = {"sha256": hashlib.sha256(rgb.tobytes()).hexdigest(),
                       "shape": list(rgb.shape), "dtype": str(rgb.dtype)}
    return {"evaluator_state": deepcopy(dict(snapshot.evaluator_state)), "rgb": hashes}


def _capture_abort(runtime, history, row):
    if runtime is None or history is None:
        return
    try:
        terminal = runtime.terminal(reason=row["termination_reason"])
        if (terminal.episode_uid, terminal.reset_epoch) != (history.episode_uid, history.reset_epoch):
            raise ValueError("Abort snapshot reset identity mismatch")
        row.update(simulation_time_ns=terminal.simulation_time_ns, terminal_before_reset=True,
                   terminal_evidence=_terminal_record(terminal))
    except Exception:
        # An unavailable abort snapshot is explicit missing evidence, never a fabricated terminal.
        row["terminal_before_reset"] = False


class EvaluationRunner:
    def __init__(self, protocol: EvaluationProtocol, cases: Mapping[str, EvalCase], *,
                 runtime_factory, provider_factory, source_commit: str,
                 policy_identity: Mapping, evidence_kind: str):
        self.protocol = protocol
        self.cases = dict(cases)
        self.runtime_factory = runtime_factory
        self.provider_factory = provider_factory
        self.source_commit = identity(source_commit, "source commit")
        self.policy_identity = deepcopy(dict(policy_identity))
        self.evidence_kind = evidence_kind
        for trial in protocol.expected_trials:
            case = self.cases[trial.case_id]
            if trial.task_id != case.task_id or \
                    (case.runtime_profile, case.controller_profile) != \
                    (protocol.runtime_profile, protocol.controller_profile):
                raise ValueError("Case does not match declared task/runtime/controller")
            if case.observation_profile.profile_id != self.policy_identity.get("observation_profile"):
                raise ValueError("Policy observation profile identity differs from case")
            if protocol.scope == "benchmark" and case.validation_status != "verified":
                raise ValueError("Formal benchmark cases require actual reset/reconstruction validation")

    def run(self, *, submission_id: str, benchmark_release: str | None = None):
        identity(submission_id, "submission ID")
        if self.protocol.scope == "benchmark":
            identity(benchmark_release, "benchmark release")
        rows = []
        interrupted = False
        for trial in self.protocol.expected_trials:
            row = {"trial_id": trial.trial_id, "attempt_id": trial.trial_id + "/attempt-001",
                   "case_id": trial.case_id, "task_id": trial.task_id,
                   "policy_seed": trial.policy_seed, "outcome": "not_run",
                   "termination_reason": "interrupted" if interrupted else "not_started",
                   "simulation_time_ns": 0, "wall_time_s": 0., "executed_commands": 0,
                   "retry_of": None, "terminal_before_reset": False,
                   "terminal_evidence": None, "error_type": None, "error_message": None,
                   "requested_executed_differences": 0, "partial_intervals": 0}
            if interrupted:
                rows.append(row)
                continue
            runtime = None
            history = None
            observed = None
            started = time.monotonic()
            try:
                case = self.cases[trial.case_id]
                runtime = self.runtime_factory(case)
                provider = self.provider_factory(trial)
                runtime.reset(case)
                observed = runtime.observe()
                if observed.simulation_time_ns != 0:
                    raise ValueError("Reset must provide an episode-local initial observation at time zero")
                history = ExecutionHistory(observed.episode_uid, observed.reset_epoch)
                # A reset callback must not leak EvalCase goal/initial evaluator state.
                provider.reset(ProviderContext(observed.episode_uid, observed.reset_epoch,
                                              case.observation_profile.profile_id,
                                              observed.instruction, trial.policy_seed))
                for _ in range(self.protocol.max_commands):
                    observation = build_observation(observed, case.observation_profile, history)
                    command = provider.command(observation)
                    if not isinstance(command, Native9Command):
                        raise ValueError("Action provider must return one physical native9 command")
                    history.validate_command(command)
                    step = runtime.step(command)
                    if not isinstance(step, StepResult) or step.ack.start_ns != observation.simulation_time_ns:
                        raise ValueError("Execution acknowledgement is not aligned to the current physical observation")
                    history.accept(command, step.ack)
                    row["simulation_time_ns"] = step.ack.end_ns
                    row["requested_executed_differences"] += int(command.requested != step.ack.executed)
                    row["partial_intervals"] += int(not step.ack.completed_interval)
                    if step.terminal:
                        terminal = runtime.terminal()
                        break
                    observed = runtime.observe()
                    if observed.simulation_time_ns != step.ack.end_ns:
                        raise ValueError("Observation timestamp differs from the actual completed interval")
                else:
                    terminal = runtime.terminal(reason="protocol_command_budget")
                    if terminal.outcome != "timeout":
                        raise ValueError("Protocol command-budget exhaustion requires an explicit timeout outcome")
                if (terminal.episode_uid, terminal.reset_epoch) != (history.episode_uid, history.reset_epoch) or \
                        terminal.simulation_time_ns != row["simulation_time_ns"]:
                    raise ValueError("Terminal belongs to another reset or physical boundary")
                if not set(case.observation_profile.camera_keys) <= set(terminal.rgb):
                    raise ValueError("Terminal lacks a declared policy camera")
                row.update(outcome=terminal.outcome, termination_reason=terminal.termination_reason,
                           terminal_before_reset=True, terminal_evidence=_terminal_record(terminal))
            except KeyboardInterrupt:
                interrupted = True
                row.update(outcome="error", termination_reason="interrupted", error_type="KeyboardInterrupt")
            except Exception as error:
                row.update(outcome="error", termination_reason="runtime_or_provider_error",
                           error_type=type(error).__name__, error_message=str(error))
            finally:
                row["executed_commands"] = len(history.completed) if history is not None else 0
                if row["outcome"] == "error":
                    _capture_abort(runtime, history, row)
                row["wall_time_s"] = time.monotonic() - started
                if runtime is not None:
                    try:
                        runtime.close()
                    except Exception as error:
                        row.update(outcome="error", termination_reason="runtime_close_error",
                                   error_type=type(error).__name__, error_message=str(error))
            rows.append(row)
        manifest = {"schema": RESULT_SCHEMA, "scope": self.protocol.scope,
                    "benchmark_release": benchmark_release, "submission_id": submission_id,
                    "source_commit": self.source_commit, "evidence_kind": self.evidence_kind,
                    "publication_status": "local_only", "policy_identity": self.policy_identity,
                    "protocol": self.protocol.record(),
                    "expected_trials": self.protocol.record()["expected_trials"],
                    "case_validation": {key: value.validation_status for key, value in self.cases.items()},
                    "case_identity": {key: {"task_id": value.task_id, "task_version": value.task_version,
                                            "assets": dict(value.assets), "seed": value.seed,
                                            "runtime_profile": value.runtime_profile,
                                            "controller_profile": value.controller_profile,
                                            "observation_profile": value.observation_profile.profile_id,
                                            "camera_keys": list(value.observation_profile.camera_keys),
                                            "provenance": dict(value.provenance)}
                                      for key, value in self.cases.items()},
                    "action_scheduling": {"schema": ACTION_SCHEMA, "command_interval_ns": COMMAND_INTERVAL_NS,
                                          "mode": "synchronous_single_command", "desired_force": "zero"},
                    "not_run": ["learned_policy_closed_loop", "formal_benchmark_score"]
                               if self.protocol.scope == "engineering_diagnostic" else []}
        return {"run_manifest": manifest, "outcomes": rows,
                "validation": validate_result(manifest, rows)}
