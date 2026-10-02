"""Physical single-command interface; no model chunks, simulator or transport imports."""
from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Any, Mapping, Protocol, Sequence

ACTION_NAMES = ("base_vx", "base_vy", "base_yaw_rate", "fl_ee_x", "fl_ee_y",
                "fl_ee_z", "fl_ee_fx", "fl_ee_fy", "fl_ee_fz")
ACTION_SCHEMA = "rambo-native9-v2"
COMMAND_INTERVAL_NS = 20_000_000
CAMERAS = ("go2_ego", "d435i_rgb_task")
ROOT_FIELDS = (
    "observation.state.base.position", "observation.state.base.orientation",
    "observation.state.base.linear_velocity", "observation.state.base.angular_velocity",
    "observation.state.projected_gravity",
)


def identity(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Explicit " + label + " required")
    return value


def timestamp(value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("Authoritative nonnegative integer timestamp required")
    return value


def native9(values: Sequence[float]) -> tuple[float, ...]:
    if len(values) != 9:
        raise ValueError("Exactly nine physical command values required")
    if any(isinstance(value, (str, bytes, bool)) or type(value).__name__ == "bool_" for value in values):
        raise ValueError("Native9 values must be physical numbers, not booleans or strings")
    result = tuple(float(value) for value in values)
    if not all(math.isfinite(value) for value in result):
        raise ValueError("Finite native9 values required")
    return result


def float32(values: Sequence[float]) -> tuple[float, ...]:
    try:
        result = struct.unpack("<9f", struct.pack("<9f", *native9(values)))
    except (OverflowError, struct.error) as error:
        raise ValueError("Command cannot be represented as float32") from error
    if not all(math.isfinite(value) for value in result):
        raise ValueError("Command cannot be represented as finite float32")
    return result


@dataclass(frozen=True)
class Native9Command:
    episode_uid: str
    reset_epoch: int
    command_id: str
    requested: tuple[float, ...]
    execution: tuple[float, ...]

    def __post_init__(self):
        identity(self.episode_uid, "episode UID")
        identity(self.command_id, "command ID")
        timestamp(self.reset_epoch)
        object.__setattr__(self, "requested", native9(self.requested))
        converted = float32(self.requested)
        expected = converted[:6] + (0., 0., 0.)
        if tuple(self.execution) != expected:
            raise ValueError("Execution must be float32 requested command with zero desired force")
        object.__setattr__(self, "execution", expected)

    @classmethod
    def from_values(cls, values, *, episode_uid, reset_epoch, command_id):
        requested = native9(values)
        return cls(episode_uid, reset_epoch, command_id, requested,
                   float32(requested)[:6] + (0., 0., 0.))


@dataclass(frozen=True)
class ExecutionAck:
    episode_uid: str
    reset_epoch: int
    command_id: str
    start_ns: int
    end_ns: int
    executed: tuple[float, ...]
    completed_interval: bool

    def __post_init__(self):
        identity(self.episode_uid, "episode UID")
        identity(self.command_id, "command ID")
        timestamp(self.reset_epoch)
        timestamp(self.start_ns)
        timestamp(self.end_ns)
        if type(self.completed_interval) is not bool:
            raise ValueError("Explicit completed-interval flag required")
        duration = self.end_ns - self.start_ns
        if duration <= 0 or duration > COMMAND_INTERVAL_NS or \
                self.completed_interval != (duration == COMMAND_INTERVAL_NS):
            raise ValueError("Only a complete 20 ms interval is completed native9 history")
        values = float32(self.executed)
        if values != tuple(self.executed) or any(value != 0 for value in values[6:]):
            raise ValueError("Executed command must be float32 native9 with desired force zero")
        object.__setattr__(self, "executed", values)


class ExecutionHistory:
    """Episode-local confirmed commands; partial intervals stay outside training history."""
    def __init__(self, episode_uid: str, reset_epoch: int):
        self.episode_uid = identity(episode_uid, "episode UID")
        self.reset_epoch = timestamp(reset_epoch)
        self._completed: list[ExecutionAck] = []
        self._seen: set[str] = set()
        self._last_end: int | None = None

    @property
    def completed(self) -> tuple[ExecutionAck, ...]:
        return tuple(self._completed)

    def accept(self, command: Native9Command, ack: ExecutionAck):
        self.validate_command(command)
        for record in (command, ack):
            if (record.episode_uid, record.reset_epoch) != (self.episode_uid, self.reset_epoch):
                raise ValueError("Stale episode/reset identity")
        if ack.command_id != command.command_id or ack.command_id in self._seen:
            raise ValueError("Mismatched or duplicated command acknowledgement")
        if ack.executed != command.execution:
            raise ValueError("Acknowledgement differs from submitted physical command")
        if self._last_end is not None and ack.start_ns != self._last_end:
            raise ValueError("Execution intervals must be contiguous authoritative intervals")
        self._seen.add(ack.command_id)
        self._last_end = ack.end_ns
        if ack.completed_interval:
            self._completed.append(ack)

    def validate_command(self, command: Native9Command):
        if (command.episode_uid, command.reset_epoch) != (self.episode_uid, self.reset_epoch) or \
                command.command_id in self._seen:
            raise ValueError("Stale or duplicated command must not be submitted")


@dataclass(frozen=True)
class ObservationProfile:
    profile_id: str
    camera_keys: tuple[str, ...]
    proprioception_fields: tuple[str, ...]
    include_executed_history: bool
    state_semantics: Mapping[str, Any]

    def __post_init__(self):
        identity(self.profile_id, "observation profile")
        if not self.camera_keys or len(set(self.camera_keys)) != len(self.camera_keys) or \
                not set(self.camera_keys) <= set(CAMERAS):
            raise ValueError("Explicit supported policy RGB cameras required")
        if len(set(self.proprioception_fields)) != len(self.proprioception_fields) or \
                not set(self.proprioception_fields) <= set(ROOT_FIELDS):
            raise ValueError("Only declared root-link proprioception may be policy-visible")
        if type(self.include_executed_history) is not bool:
            raise ValueError("Explicit history visibility required")
        semantics = dict(self.state_semantics)
        if self.proprioception_fields:
            fixed = {"reference": "root_link", "quaternion": "xyzw", "velocity_frame": "world",
                     "projected_gravity_frame": "body"}
            if any(semantics.get(key) != value for key, value in fixed.items()) or \
                    not isinstance(semantics.get("ground_z"), (int, float)) or \
                    isinstance(semantics.get("ground_z"), bool) or not math.isfinite(semantics["ground_z"]):
                raise ValueError("Explicit root-link/xyzw/world-velocity/body-gravity/ground semantics required")
            identity(semantics.get("ground_reference"), "ground reference")
        elif semantics:
            raise ValueError("A profile without proprioception must not declare state inputs")
        object.__setattr__(self, "camera_keys", tuple(self.camera_keys))
        object.__setattr__(self, "proprioception_fields", tuple(self.proprioception_fields))
        object.__setattr__(self, "state_semantics", semantics)


@dataclass(frozen=True)
class StateChannels:
    """Owned runtime packet. Only the explicit physical fields below can reach a policy."""
    episode_uid: str
    reset_epoch: int
    simulation_time_ns: int
    rgb: Mapping[str, Any]
    instruction: str
    root_state: Mapping[str, Any]
    controller_private: Mapping[str, Any]
    evaluator_private: Mapping[str, Any]


@dataclass(frozen=True)
class PolicyObservation:
    episode_uid: str
    reset_epoch: int
    simulation_time_ns: int
    profile_id: str
    rgb: Mapping[str, Any]
    instruction: str
    proprioception: Mapping[str, tuple[float, ...]]
    state_semantics: Mapping[str, Any]
    executed_history: tuple[ExecutionAck, ...]


def build_observation(channels: StateChannels, profile: ObservationProfile,
                      history: ExecutionHistory) -> PolicyObservation:
    identity(channels.episode_uid, "episode UID")
    identity(channels.instruction, "instruction")
    timestamp(channels.reset_epoch)
    timestamp(channels.simulation_time_ns)
    if (channels.episode_uid, channels.reset_epoch) != (history.episode_uid, history.reset_epoch):
        raise ValueError("Observation reset identity mismatch")
    rgb = {}
    for key in profile.camera_keys:
        image = channels.rgb[key]
        if str(getattr(image, "dtype", None)) != "uint8" or \
                len(getattr(image, "shape", ())) != 3 or image.shape[-1] != 3 or \
                image.shape[0] < 1 or image.shape[1] < 1:
            raise ValueError("Policy cameras must contain uint8 HWC RGB frames")
        owned = image.copy()
        owned.setflags(write=False)
        rgb[key] = owned
    prop = {}
    for key in profile.proprioception_fields:
        values = tuple(float(value) for value in channels.root_state[key])
        width = 4 if key.endswith("orientation") else 3
        if len(values) != width or not all(math.isfinite(value) for value in values):
            raise ValueError("Malformed declared root-link state")
        prop[key] = values
    completed = history.completed if profile.include_executed_history else ()
    if completed and completed[-1].end_ns > channels.simulation_time_ns:
        raise ValueError("Observation precedes confirmed execution history")
    # Never expose either private mapping, nor undeclared fields from root_state/rgb.
    return PolicyObservation(channels.episode_uid, channels.reset_epoch,
                             channels.simulation_time_ns, profile.profile_id, rgb,
                             channels.instruction, prop, dict(profile.state_semantics), completed)


@dataclass(frozen=True)
class ProviderContext:
    episode_uid: str
    reset_epoch: int
    profile_id: str
    instruction: str
    policy_seed: int


class ActionProvider(Protocol):
    def reset(self, context: ProviderContext) -> None: ...
    def command(self, observation: PolicyObservation) -> Native9Command: ...
