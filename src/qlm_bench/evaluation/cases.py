"""No implicit horizon, task admission, policy seeds or benchmark release."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from qlm_bench.policy_interface import ObservationProfile
from qlm_bench.policy_interface.physical import identity
from qlm_bench.tasks import TASK_IDS


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    task_id: str
    task_version: str
    instruction: str
    observation_profile: ObservationProfile
    assets: Mapping[str, str]
    initial_state: Mapping[str, Any]
    goal: Mapping[str, Any]
    scene: Mapping[str, Any]
    cameras: Mapping[str, Any]
    seed: int
    controller_profile: str
    runtime_profile: str
    reset_procedure: Mapping[str, Any]
    provenance: Mapping[str, Any]
    validation_status: str

    def __post_init__(self):
        if self.task_id not in TASK_IDS:
            raise ValueError("Unsupported task")
        for field in ("case_id", "task_version", "instruction", "controller_profile", "runtime_profile"):
            identity(getattr(self, field), field)
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("Explicit nonnegative case seed required")
        if not isinstance(self.observation_profile, ObservationProfile):
            raise ValueError("Explicit physical observation profile required")
        if self.validation_status not in ("draft", "verified", "engineering_fixture"):
            raise ValueError("Explicit case reconstruction status required")
        for field in ("assets", "initial_state", "goal", "scene", "cameras", "reset_procedure", "provenance"):
            value = getattr(self, field)
            if not isinstance(value, Mapping) or not value:
                raise ValueError("Explicit " + field + " required; seed alone is insufficient")
            object.__setattr__(self, field, deepcopy(dict(value)))
        for asset_id, version in self.assets.items():
            identity(asset_id, "asset ID")
            identity(version, "asset version")
            if Path(asset_id).is_absolute() or Path(version).is_absolute():
                raise ValueError("Cases reference asset identities, not private local resource paths")
        if not set(self.observation_profile.camera_keys) <= set(self.cameras):
            raise ValueError("Case does not configure its declared policy cameras")
        if self.validation_status == "verified" and \
                (self.provenance.get("evidence_kind") != "actual_runtime" or
                 self.provenance.get("reset_reconstruction_passed") is not True or
                 not re.fullmatch(r"[0-9a-f]{64}", str(self.provenance.get("evidence_sha256", "")))):
            raise ValueError("Verified cases require actual reset/reconstruction evidence identity")

    def record(self):
        return {"schema": "qlm-eval-case-v1", **asdict(self)}

    @classmethod
    def from_record(cls, record):
        try:
            values = deepcopy(dict(record))
            if values.pop("schema", None) != "qlm-eval-case-v1":
                raise ValueError("Unsupported evaluation case schema")
            profile = values["observation_profile"]
            profile["camera_keys"] = tuple(profile["camera_keys"])
            profile["proprioception_fields"] = tuple(profile["proprioception_fields"])
            values["observation_profile"] = ObservationProfile(**profile)
            return cls(**values)
        except (KeyError, TypeError) as error:
            raise ValueError("Incomplete or malformed evaluation case") from error


def load_case(path):
    return EvalCase.from_record(json.loads(Path(path).read_text()))


@dataclass(frozen=True)
class TrialSpec:
    trial_id: str
    case_id: str
    task_id: str
    policy_seed: int

    def __post_init__(self):
        identity(self.trial_id, "trial ID")
        identity(self.case_id, "case ID")
        if self.task_id not in TASK_IDS or type(self.policy_seed) is not int or self.policy_seed < 0:
            raise ValueError("Supported task and explicit policy seed required")


@dataclass(frozen=True)
class EvaluationProtocol:
    protocol_id: str
    suite_id: str
    case_set_id: str
    runtime_profile: str
    controller_profile: str
    max_commands: int
    error_policy: str
    retry_selection: str
    scope: str
    validation_status: str
    expected_trials: tuple[TrialSpec, ...]
    source_identity: Mapping[str, str]

    def __post_init__(self):
        for field in ("protocol_id", "suite_id", "case_set_id", "runtime_profile", "controller_profile"):
            identity(getattr(self, field), field)
        if type(self.max_commands) is not int or self.max_commands < 1:
            raise ValueError("Explicit positive command budget required")
        if self.error_policy not in ("count_as_failure", "invalidate") or \
                self.retry_selection not in ("first_attempt", "last_attempt"):
            raise ValueError("Explicit error denominator and retry selection required")
        if self.scope not in ("engineering_diagnostic", "benchmark") or \
                self.validation_status not in ("draft", "verified"):
            raise ValueError("Explicit protocol scope/validation required")
        if not self.expected_trials or not all(isinstance(t, TrialSpec) for t in self.expected_trials) or \
                len({t.trial_id for t in self.expected_trials}) != len(self.expected_trials):
            raise ValueError("Explicit unique expected trial set required")
        if not self.source_identity or not {"source_commit", "spec_sha256"} <= set(self.source_identity):
            raise ValueError("Protocol source commit and specification hash required")
        for key in ("source_commit", "spec_sha256"):
            identity(self.source_identity[key], key)
        if self.scope == "benchmark" and self.validation_status == "verified" and \
                (not re.fullmatch(r"[0-9a-f]{40}", self.source_identity["source_commit"]) or
                 not re.fullmatch(r"[0-9a-f]{64}", self.source_identity["spec_sha256"])):
            raise ValueError("Verified benchmark protocol requires immutable source commit and specification hash")
        object.__setattr__(self, "expected_trials", tuple(self.expected_trials))
        object.__setattr__(self, "source_identity", deepcopy(dict(self.source_identity)))

    def record(self):
        value = asdict(self)
        value["expected_trials"] = list(value["expected_trials"])
        return value
