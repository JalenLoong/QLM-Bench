"""One source-bound local attempt; success filtering never removes failed attempts."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Mapping

TASK_PREFIXES = {"push_box": "push-box-", "lift_basket": "lift-basket-", "press_button": "press-button-"}
INSTRUCTIONS = {"push_box": "Push the box into the target area.", "lift_basket": "Lift the basket.",
                "press_button": "Press the button."}


def _write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_identity(root=None):
    """Actual checkout identity, including dirty source; installed packages use version + code hashes."""
    root = Path(root).resolve() if root else Path(__file__).resolve().parents[3]
    own = Path(__file__).resolve()
    implementation = {str(path.relative_to(own.parent)): _sha(path) for path in sorted(own.parent.glob("*.py"))}
    from qlm_bench import __version__
    result = {"package": "qlm_bench", "version": __version__, "implementation": implementation,
              "source_commit": None, "source_dirty": None, "dirty_source_sha256": None}
    try:
        def git(*args):
            return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)
        if Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve() != root:
            return result
        result["source_commit"] = git("rev-parse", "HEAD").decode().strip()
        result["branch"] = git("branch", "--show-current").decode().strip()
        result["source_dirty"] = bool(git("status", "--porcelain"))
        dirty = hashlib.sha256(git("diff", "--binary", "HEAD"))
        for relative in sorted(git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0")):
            if not relative:
                continue
            path = root / relative.decode()
            if path.is_file():
                dirty.update(relative + b"\0" + _sha(path).encode() + b"\0")
        result["dirty_source_sha256"] = dirty.hexdigest()
    except (OSError, subprocess.CalledProcessError):
        pass
    return result


@dataclass(frozen=True)
class CollectionConfig:
    task: str
    profile: Mapping
    resource_root: Path
    output_dir: Path
    ffmpeg: str
    ffprobe: str
    data_python: str
    episode_length_s: float
    seed: int
    diagnostic_only: bool
    device: str

    def __post_init__(self):
        if self.task not in TASK_PREFIXES or not isinstance(self.profile, Mapping) or \
                not str(self.profile.get("task_profile_version", "")).startswith(TASK_PREFIXES[self.task]):
            raise ValueError("An explicit matching profile for one of the three current tasks is required")
        expected = {"policy_fps": 50, "policy_rgb_fps": 50, "controller_fps": 100,
                    "physics_fps": 500, "force_zero": True}
        if any(self.profile.get(key) != value for key, value in expected.items()):
            raise ValueError("Collection retains native9 force-zero and the accepted physical rates")
        asset_hash = self.profile.get("asset_sha256", "")
        if len(asset_hash) != 64 or any(c not in "0123456789abcdef" for c in asset_hash):
            raise ValueError("Explicit task asset hash required")
        if type(self.seed) is not int or self.seed < 0 or type(self.diagnostic_only) is not bool:
            raise ValueError("Explicit seed and diagnostic status required")
        if isinstance(self.episode_length_s, bool) or not math.isfinite(self.episode_length_s) or \
                self.episode_length_s <= 0 or not math.isclose(self.episode_length_s * 50,
                                                              round(self.episode_length_s * 50), abs_tol=1e-8):
            raise ValueError("Explicit horizon must contain complete 50 Hz command intervals")
        resources, output = Path(self.resource_root).resolve(), Path(self.output_dir).resolve()
        if resources == output or resources.is_relative_to(output) or output.is_relative_to(resources):
            raise ValueError("Attempt output and immutable resources must be separate")
        if output.exists():
            raise FileExistsError("Use a new output directory; past attempts are immutable")
        if not resources.is_dir():
            raise FileNotFoundError("Prepared resource root required")
        for tool in (self.ffmpeg, self.ffprobe, self.data_python):
            if not isinstance(tool, str) or not Path(tool).is_absolute():
                raise ValueError("Explicit resolved media tool and data Python paths required")
        observer = self.profile.get("observer", {})
        if observer.get("fps") != 25 or observer.get("model_input") is not False:
            raise ValueError("Observer remains 25 Hz diagnostic-only")
        for field in ("position", "look_at"):
            values = observer.get(field, ())
            if len(values) != 3 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
                raise ValueError("Explicit observer geometry required")
        object.__setattr__(self, "resource_root", resources)
        object.__setattr__(self, "output_dir", output)
        object.__setattr__(self, "profile", deepcopy(dict(self.profile)))

    @property
    def max_commands(self):
        return round(self.episode_length_s * 50)


def _validated_packaging(validations, *, actions, diagnostic_only):
    raw, canonical = validations["raw"], validations["canonical"]
    expected_episode = {"episode_index": 0, "rows": actions, "terminal_action_count": 0,
                        "boundary_observations": actions + 1}
    if raw.get("contract_valid") is not True or canonical.get("contract_valid") is not True or \
            raw.get("raw_actions") != actions or raw.get("raw_boundaries") != actions + 1 or \
            raw.get("physics_steps") != 10 * actions or raw.get("controller_steps") != 2 * actions or \
            raw.get("video_validation") != "passed" or canonical.get("video_validation") != "passed" or \
            canonical.get("dataset_schema_version") != "wam-quadruped-v2.1.0" or \
            canonical.get("episodes") != [expected_episode] or \
            raw.get("diagnostic_only") is not diagnostic_only or canonical.get("diagnostic_only") is not diagnostic_only:
        raise ValueError("Complete frozen Raw/Canonical contract and actual media validation are required")


def legacy_capture_status(outcome):
    """Frozen Canonical status has two values; detailed termination stays in attempt metadata."""
    if outcome not in ("success", "failure", "timeout", "error"):
        raise ValueError("Unknown completed collection outcome")
    return "success" if outcome == "success" else "failure"


def collect_attempt(config: CollectionConfig, *, runtime_factory, recorder_factory,
                    prepare_command, validate_runtime, packager, resources: Mapping,
                    source: Mapping, evidence_kind: str):
    """Orchestrate real execution or explicitly local CPU fixtures with the same lifecycle."""
    if evidence_kind not in ("actual_runtime", "engineering_fixture"):
        raise ValueError("Explicit runtime evidence kind required")
    if not source.get("source_commit") and not source.get("version"):
        raise ValueError("Actual Git identity or installed package version required")
    if not {"task_asset", "controller"} <= set(resources):
        raise ValueError("Task asset and fixed controller identities required")
    from qlm_bench.contracts import physical_contract
    physical = physical_contract()
    out = config.output_dir
    out.mkdir(parents=True, exist_ok=False)
    raw = out / "raw" / out.name
    raw.mkdir(parents=True)
    report = {"schema": "qlm-collection-attempt-v1", "attempt_id": out.name,
              "episode_uid": raw.name, "task": config.task, "seed": config.seed,
              "profile_id": config.profile["task_profile_version"],
              "profile_sha256": hashlib.sha256(json.dumps(config.profile, sort_keys=True,
              separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
              "source": dict(source), "resources": deepcopy(dict(resources)),
              "physical_contract": {key: physical[key] for key in ("protocol", "source_action_schema", "rates_hz")},
              "evidence_kind": evidence_kind, "publication_status": "local_only",
              "action_source": {"kind": "scripted_expert", "privileged_simulator_state": True},
              "diagnostic_only": config.diagnostic_only, "eligible_demonstration": False,
              "status": "error", "passed": False, "terminal_before_reset": False,
              "task_outcome": None, "termination_reason": None,
              "raw_validation": None, "canonical_validation": None, "error": None,
              "raw_root": "raw/" + out.name, "canonical_root": "canonical", "max_commands": config.max_commands,
              "episode_length_s": config.episode_length_s, "runtime": None,
              "data_python": config.data_python,
              "not_run": ["training", "remote_publication", "learned_policy_closed_loop"]}
    _write(out / "attempt.json", report)
    runtime = recorder = None
    closed = False
    started = time.monotonic()
    capture = None
    try:
        def on_environment_ready(ready_runtime):
            nonlocal runtime, recorder
            if recorder is not None:
                raise ValueError("Environment-ready callback must run once before the initial reset")
            runtime = ready_runtime
            report["runtime"] = validate_runtime(ready_runtime)
            recorder = recorder_factory(ready_runtime, raw, config.ffmpeg, config.profile)
            ready_runtime.base_env._v2_recorder = recorder

        # The factory calls this hook before its original initial reset/PPO sequence.
        # Extra resets would consume new motor-lag RNG and change the accepted rollout.
        runtime = runtime_factory(config, on_environment_ready=on_environment_ready)
        if recorder is None:
            raise ValueError("Runtime factory did not attach the recorder before its original reset")
        recorder.begin()
        initial_geometry = deepcopy(runtime.base_env.review_diagnostics())
        for index in range(config.max_commands):
            requested, expert = runtime.expert_command()
            prepared = prepare_command(requested, f"{out.name}:{index}", runtime.base_env.episode_tick)
            prepared["extensions"]["expert"] = expert
            recorder.submit(prepared)
            step = runtime.step(prepared)
            if step["terminal"] is not None:
                break
            recorder.capture_boundary()
        if recorder.terminal is None:
            raise ValueError("No actual pre-reset terminal was captured within the explicit horizon")
        terminal = recorder.terminal
        report["terminal_before_reset"] = True
        report["terminal_simulation_time_ns"] = terminal["simulation_time_ns"]
        report["partial_interval"] = bool(terminal["partial_interval"])
        owned = step["terminal"]
        report["status"] = "failure" if owned["fallen"] else "success" if owned["success"] else \
                           "timeout" if owned["timed_out"] else "error"
        report["termination_reason"] = terminal["reason"]
        report["task_outcome"] = {"outcome": report["status"], "success": bool(owned["success"]),
                                  "fallen": bool(owned["fallen"]), "timed_out": bool(owned["timed_out"]),
                                  "termination_reason": terminal["reason"],
                                  "simulation_time_ns": terminal["simulation_time_ns"],
                                  "partial_interval": bool(terminal["partial_interval"])}
        if owned["simulation_time_ns"] != terminal["simulation_time_ns"] or \
                owned["rgb_hashes"] != terminal["rgb_hashes"]:
            raise ValueError("Recorder terminal does not match the owned environment snapshot")
        full = not terminal["partial_interval"] and len(recorder.commands) > 0 and \
               len(recorder.boundaries) == len(recorder.commands) + 1
        report["passed"] = full
        report["n_actions"], report["n_boundaries"] = len(recorder.commands), len(recorder.boundaries)
        extra = {"work_id": "SIM-001", "work_id_role": "implementation_origin",
                 "scenario": {"id": out.name, "seed": config.seed, "task": config.task},
                 "mode": "engineering_diagnostic" if config.diagnostic_only else "scripted_generation",
                 "diagnostic_only": config.diagnostic_only or evidence_kind == "engineering_fixture",
                 "profile": dict(config.profile), "implementation": source.get("implementation", {}),
                 "source_commit": source.get("source_commit") or "installed-package:" + source["version"],
                 "source_identity": dict(source), "checkpoint_sha256": runtime.contract.sha256,
                 "status": legacy_capture_status(report["status"]),
                 "task_outcome": report["task_outcome"], "termination_reason": report["termination_reason"],
                 "invalid": not full, "task_text": config.profile.get("instruction", INSTRUCTIONS[config.task]),
                 "initial_geometry": initial_geometry, "publication_status": "local_only",
                 "action_source": report["action_source"], "evidence_kind": evidence_kind}
        capture = recorder.close(extra)
        closed = True
        _write(raw / "summary.json", report)
        if full:
            validations = packager(raw, out / "canonical", ffmpeg=config.ffmpeg, ffprobe=config.ffprobe)
            report["raw_validation"] = validations["raw"]
            report["canonical_validation"] = validations["canonical"]
            _validated_packaging(validations, actions=len(recorder.commands),
                                 diagnostic_only=config.diagnostic_only or evidence_kind == "engineering_fixture")
            report["passed"] = True
            report["eligible_demonstration"] = evidence_kind == "actual_runtime" and \
                not config.diagnostic_only and report["status"] == "success" and report["passed"]
        else:
            report["packaging_status"] = "invalid_partial_or_incomplete_attempt"
    except KeyboardInterrupt:
        report.update(status="interrupted", passed=False, eligible_demonstration=False,
                      error={"type": "KeyboardInterrupt", "message": "Collection interrupted"})
    except Exception as error:
        report.update(status="error", passed=False, eligible_demonstration=False,
                      error={"type": type(error).__name__, "message": str(error)})
    finally:
        if recorder is not None and not closed:
            try:
                capture = recorder.close({"invalid": True, "task": config.task,
                                          "profile": dict(config.profile), "source_identity": dict(source),
                                          "diagnostic_only": True, "publication_status": "local_only"})
            except Exception as error:
                report["recorder_close_error"] = {"type": type(error).__name__, "message": str(error)}
        if runtime is not None:
            try:
                runtime.close()
            except Exception as error:
                report.update(status="error", passed=False, eligible_demonstration=False,
                              runtime_close_error={"type": type(error).__name__, "message": str(error)})
        report["wall_time_s"] = time.monotonic() - started
        report["capture_retained"] = capture is not None
        _write(out / "attempt.json", report)
        _write(raw / "summary.json", report)
    return report
