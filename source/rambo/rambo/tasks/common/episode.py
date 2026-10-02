"""Episode time, command confirmations and outcomes without recorder dependencies.

Time is derived only from the runtime's completed PhysX step counter.  The
retained profile is 500 Hz physics, 100 Hz controller and 50 Hz native9 commands.
This module imports no Isaac, Torch or model packages.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

PHYSICS_STEP_NS = 2_000_000
CONTROL_PHYSICS_STEPS = 5
COMMAND_PHYSICS_STEPS = 10


@dataclass
class EpisodeClock:
    origin_tick: int = 0
    reset_epoch: int = -1

    def reset(self, completed_physics_tick: int) -> None:
        if type(completed_physics_tick) is not int or completed_physics_tick < 0:
            raise ValueError("Expected a completed nonnegative physics tick")
        self.origin_tick = completed_physics_tick
        self.reset_epoch += 1

    def tick(self, completed_physics_tick: int) -> int:
        if type(completed_physics_tick) is not int or completed_physics_tick < self.origin_tick:
            raise ValueError("Runtime physics counter precedes the episode origin")
        return completed_physics_tick - self.origin_tick

    def time_ns(self, completed_physics_tick: int) -> int:
        return self.tick(completed_physics_tick) * PHYSICS_STEP_NS


class EpisodeRuntime:
    """Environment-owned lifecycle and confirmed executed-command history."""

    def __init__(self) -> None:
        self.clock = EpisodeClock()
        self._terminal = None
        self.reset(0)

    def reset(self, completed_physics_tick: int) -> None:
        # Keep the last owned terminal snapshot available across auto-reset.
        self.clock.reset(completed_physics_tick)
        self.current_command = None
        self._history = []
        self._outcome = dict(success=False, fallen=False, timed_out=False,
                             terminated=False, termination_reason=None)

    @property
    def history(self) -> list[dict]:
        return copy.deepcopy(self._history)

    @property
    def outcome(self) -> dict:
        return copy.deepcopy(self._outcome)

    @property
    def terminal(self) -> dict | None:
        return copy.deepcopy(self._terminal)

    def submit(self, prepared: dict, completed_physics_tick: int) -> None:
        from rambo.contracts_v2.validation import validate_command

        validate_command(prepared)
        tick = self.clock.tick(completed_physics_tick)
        if prepared['start_tick'] != tick or prepared['end_tick'] != tick + COMMAND_PHYSICS_STEPS:
            raise ValueError("Native9 command must begin at the current 50 Hz boundary")
        if prepared['status'] != 'not_executed' or prepared['executed'] is not None:
            raise ValueError("Cannot submit an already executed command")
        if self.current_command is not None and self.current_command['status'] != 'completed':
            raise ValueError("Previous native9 hold has not completed")
        if any(value != 0 for value in prepared['filtered'][6:]):
            raise ValueError("Retained runtime requires desired force zero")
        self.current_command = copy.deepcopy(prepared)

    def confirm_control(self, completed_physics_tick: int) -> None:
        if self.current_command is None:
            return  # Teleoperation may use the retained direct command setter.
        row = self.current_command
        tick = self.clock.tick(completed_physics_tick)
        if row['status'] == 'completed':
            raise ValueError("A completed command needs a new submission before advancing")
        if tick != row['executed_until_tick'] + CONTROL_PHYSICS_STEPS or tick > row['end_tick']:
            raise ValueError("Control acknowledgement differs from completed runtime steps")
        row['executed_until_tick'] = tick
        row['status'] = 'completed' if tick == row['end_tick'] else 'partial'
        if row['status'] == 'completed':
            row['executed'] = copy.deepcopy(row['filtered'])
            self._history.append(copy.deepcopy(row))

    def set_outcome(self, *, success: bool, fallen: bool, timed_out: bool) -> dict:
        # Fall takes precedence, matching the original terminal recorder.
        reason = 'robot_fall' if fallen else ('task_success' if success else ('timeout' if timed_out else None))
        self._outcome = dict(success=bool(success), fallen=bool(fallen),
                             timed_out=bool(timed_out and not success),
                             terminated=reason is not None, termination_reason=reason)
        return self.outcome

    def seal_terminal(self, snapshot: dict) -> None:
        if not self._outcome['terminated']:
            raise ValueError("Cannot seal a nonterminal episode")
        self._terminal = copy.deepcopy(snapshot)
