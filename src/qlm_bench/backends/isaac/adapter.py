"""Explicit bindings bridge the existing runtime without importing it on metadata paths.

The callbacks must supply actual physical clock/sensor/controller evidence. This
adapter is not a network transport or a learned-policy server. No default reset,
state extraction or physics advance is guessed from an arbitrary observation dict.
"""
from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from typing import Callable

from qlm_bench.evaluation import StepResult, TerminalSnapshot
from qlm_bench.policy_interface import ExecutionAck, Native9Command, StateChannels
from qlm_bench.policy_interface.physical import ROOT_FIELDS


@dataclass(frozen=True)
class RuntimeBindings:
    reset_case: Callable
    observe_channels: Callable
    advance: Callable
    capture_terminal: Callable

    def __post_init__(self):
        if not all(callable(getattr(self, name)) for name in
                   ("reset_case", "observe_channels", "advance", "capture_terminal")):
            raise ValueError("Explicit reconstruction, state extraction, execution and terminal bindings required")


class RuntimeAdapter:
    def __init__(self, environment, bindings: RuntimeBindings):
        self.environment = environment
        self.bindings = bindings
        self._identity = None

    @classmethod
    def from_config(cls, config, *, bindings: RuntimeBindings, task_id: str):
        # Factory owns approved task/controller setup; ordinary imports stay CPU-only.
        from rambo.tasks.common.environment_factory import make_environment
        return cls(make_environment(config, task_id=task_id, wrapper=True), bindings)

    def reset(self, case):
        self.bindings.reset_case(self.environment, case)
        channels = self.observe()
        self._identity = (channels.episode_uid, channels.reset_epoch)

    def observe(self):
        packet = self.bindings.observe_channels(self.environment)
        if not isinstance(packet, StateChannels):
            raise ValueError("Observation binding must explicitly separate all three state channels")
        return packet

    def step(self, command: Native9Command):
        if (command.episode_uid, command.reset_epoch) != self._identity:
            raise ValueError("Stale command/reset identity")
        # Use the existing single-command conversion, never its WAM chunk ledger.
        from rambo.contracts_v2.runtime import prepare_command
        env = getattr(self.environment, "unwrapped", self.environment)
        prepared = prepare_command(command.requested, command.command_id, int(env.episode_tick))
        if tuple(prepared["filtered"]) != command.execution:
            raise ValueError("Runtime conversion differs from public native9 execution")
        env.submit_native9_command(prepared)
        result = self.bindings.advance(self.environment, prepared)
        if not isinstance(result, StepResult):
            raise ValueError("Advance binding must supply actual interval acknowledgement")
        return result

    def terminal(self, *, reason=None):
        snapshot = self.bindings.capture_terminal(self.environment, reason)
        if not isinstance(snapshot, TerminalSnapshot):
            raise ValueError("Terminal binding must preserve the actual pre-reset snapshot")
        return snapshot

    def close(self):
        self.environment.close()


class ControllerRuntimeAdapter:
    """Existing fixed RAMBO controller execution exposed to any native9 provider.

Case reconstruction stays an explicit callback: the adapter cannot substitute a
nominal reset for a case's goal/object initialization or claim reconstruction passed.
State field values are copied without changing frames, units or model normalizers.
"""
    def __init__(self, controller_runtime, *, reconstruct: Callable):
        if not callable(reconstruct):
            raise ValueError("Explicit EvalCase reconstruction binding required")
        self.runtime = controller_runtime
        self.reconstruct = reconstruct
        self._case = None
        self._identity = None
        self._terminal = None

    @classmethod
    def from_profile(cls, *, task_id, profile, resource_root, checkpoint_path,
                     seed, episode_length_s, device, use_fabric, reconstruct):
        from rambo.tasks.common.controller_runtime import ControllerRuntime
        runtime = ControllerRuntime(task_id, profile=profile, resource_root=resource_root,
                                    checkpoint_path=checkpoint_path, seed=seed,
                                    episode_length_s=episode_length_s, device=device,
                                    use_fabric=use_fabric)
        return cls(runtime, reconstruct=reconstruct)

    def reset(self, case):
        self.reconstruct(self.runtime, case)
        raw = self.runtime.state()
        self._case = case
        self._identity = (f"{case.case_id}/reset-{raw['reset_epoch']}", raw["reset_epoch"])
        self._terminal = None

    @staticmethod
    def _rgb(raw):
        # Alias only the already accepted RGB channels; no resizing/re-encoding.
        return {"go2_ego": raw["ego"].copy(), "d435i_rgb_task": raw["task_centric"].copy()}

    def observe(self):
        if self._case is None:
            raise ValueError("Reset the declared case before observing")
        raw = self.runtime.state()
        state = raw["state"]
        if raw["reset_epoch"] != self._identity[1]:
            raise ValueError("Runtime auto-reset must not become a new observation in the old rollout")
        root = {key: deepcopy(state[key]) for key in ROOT_FIELDS}
        controller = {key: deepcopy(value) for key, value in state.items()
                      if key.startswith("observation.state.") and key not in ROOT_FIELDS}
        evaluator = {key: deepcopy(value) for key, value in state.items() if key.startswith("task.")}
        evaluator["outcome"] = deepcopy(raw["outcome"])
        return StateChannels(self._identity[0], self._identity[1], raw["simulation_time_ns"],
                             self._rgb(raw["rgb"]), self._case.instruction, root, controller, evaluator)

    def step(self, command):
        if (command.episode_uid, command.reset_epoch) != self._identity:
            raise ValueError("Stale command/reset identity")
        from rambo.contracts_v2.runtime import prepare_command
        raw = self.runtime.state()
        prepared = prepare_command(command.requested, command.command_id, raw["physics_step"])
        if tuple(prepared["filtered"]) != command.execution:
            raise ValueError("Controller conversion differs from public execution")
        result = self.runtime.step(prepared)
        confirmation = result["command"]
        if confirmation["command_id"] != command.command_id:
            raise ValueError("Controller acknowledged another command")
        executed = confirmation["executed"] if result["completed_interval"] else confirmation["filtered"]
        acknowledgement = ExecutionAck(command.episode_uid, command.reset_epoch, command.command_id,
                                       raw["simulation_time_ns"], result["simulation_time_ns"],
                                       tuple(executed), result["completed_interval"])
        self._terminal = deepcopy(result["terminal"])
        return StepResult(acknowledgement, self._terminal is not None)

    def terminal(self, *, reason=None):
        snapshot = self._terminal
        if snapshot is None:
            raise ValueError("The runtime supplied no actual pre-reset terminal; explicit abort capture is required")
        if snapshot["reset_epoch"] != self._identity[1]:
            raise ValueError("Terminal belongs to another reset")
        outcome = "failure" if snapshot["fallen"] else \
                  "success" if snapshot["success"] else "timeout" if snapshot["timed_out"] else "error"
        return TerminalSnapshot(self._identity[0], self._identity[1], snapshot["simulation_time_ns"],
                                outcome, snapshot["reason"], deepcopy(snapshot["state"]),
                                self._rgb(snapshot["rgb"]), True)

    def close(self):
        self.runtime.close()
