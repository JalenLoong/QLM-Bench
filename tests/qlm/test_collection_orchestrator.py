"""CPU collection orchestration fixtures remain local and ineligible demonstrations."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import venv

import pytest

from qlm_bench.collection import CollectionConfig, collect_attempt, source_identity
from qlm_bench.collection.orchestrator import legacy_capture_status
from qlm_bench.collection.isaac import _resources, _tool, main, package_with_data_python, preflight_data_python
from qlm_bench.compatibility.contracts_v2.runtime import prepare_command


def profile(task="push_box"):
    prefix = {"push_box": "push-box-", "lift_basket": "lift-basket-", "press_button": "press-button-"}[task]
    return {"task_profile_version": prefix + "fixture", "asset_sha256": "a" * 64,
            "policy_fps": 50, "policy_rgb_fps": 50, "controller_fps": 100,
            "physics_fps": 500, "force_zero": True,
            "observer": {"fps": 25, "model_input": False, "position": [1, 2, 3], "look_at": [0, 0, 0]}}


def config(tmp_path, *, task="push_box", diagnostic=True):
    resources = tmp_path / "resources"
    resources.mkdir(exist_ok=True)
    return CollectionConfig(task, profile(task), resources, tmp_path / "attempt-01", "/usr/bin/ffmpeg",
                            "/usr/bin/ffprobe", sys.executable, .04, 19, diagnostic, "cpu")


class Base:
    def __init__(self):
        self.episode_tick = 0

    def review_diagnostics(self):
        return {"engineering_fixture": True, "not_fallen": True}


class Runtime:
    def __init__(self, *, status="success", partial=False, error=False):
        self.base_env = Base()
        self.contract = SimpleNamespace(sha256="b" * 64)
        self.closed = False
        self.reset_count = 0
        self.status = status
        self.partial = partial
        self.error = error

    def reset(self):
        self.reset_count += 1
        self.base_env.episode_tick = 0

    def expert_command(self):
        if self.error:
            raise ValueError("Expert failed")
        return [0] * 9, {"phase": "engineering_fixture"}

    def step(self, prepared):
        rec = self.base_env._v2_recorder
        duration = 5 if self.partial else 10
        self.base_env.episode_tick += duration
        command = deepcopy(prepared)
        command.update(status="partial" if self.partial else "completed",
                       executed_until_tick=self.base_env.episode_tick,
                       executed=None if self.partial else prepared["filtered"])
        if not self.partial:
            rec.commands.append(command)
        terminal = None
        if self.base_env.episode_tick >= 20 or self.partial:
            rec.capture_boundary()
            rec.terminal = deepcopy(rec.boundaries[-1])
            rec.terminal.update(partial_interval=self.partial, reason=self.status)
            terminal = {**rec.terminal, "fallen": self.status == "failure", "success": self.status == "success",
                        "timed_out": self.status == "timeout"}
            rec.active = False
            self.base_env.episode_tick = 0  # auto-reset isolation is required by the recorder
        return {"command": command, "terminal": terminal, "completed_interval": not self.partial}

    def close(self):
        self.closed = True


class Recorder:
    def __init__(self, runtime, out):
        self.env = runtime.base_env
        self.out = out
        self.terminal = None
        self.commands = []
        self.boundaries = []
        self.active = False
        self.closed = False
        self.submitted = []

    def begin(self):
        assert self.env.episode_tick == 0
        self.active = True
        self.capture_boundary()

    def submit(self, prepared):
        self.submitted.append(deepcopy(prepared))

    def capture_boundary(self):
        if self.boundaries and self.boundaries[-1]["physics_step"] == self.env.episode_tick:
            return
        self.boundaries.append({"physics_step": self.env.episode_tick,
                                "simulation_time_ns": self.env.episode_tick * 2_000_000,
                                "state": {"fixture": True}, "rgb_hashes": {"fixture": "c" * 64}})

    def close(self, extra):
        assert not self.closed
        self.closed = True
        capture = {"boundaries": self.boundaries, "commands": self.commands,
                   "terminal": self.terminal, **extra}
        (self.out / "capture.json").write_text(json.dumps(capture))
        return capture


def execute(conf, runtime, *, packager=None):
    def validated(*args, **kwargs):
        return {"raw": {"contract_valid": True, "raw_actions": 2, "raw_boundaries": 3,
                        "physics_steps": 20, "controller_steps": 4, "diagnostic_only": True,
                        "video_validation": "passed", "published": False},
                "canonical": {"contract_valid": True, "diagnostic_only": True,
                              "dataset_schema_version": "wam-quadruped-v2.1.0",
                              "episodes": [{"episode_index": 0, "rows": 2, "terminal_action_count": 0,
                                            "boundary_observations": 3}], "video_validation": "passed",
                              "release_validation": "not_run", "published": False}}
    def factory(config, *, on_environment_ready):
        on_environment_ready(runtime)
        runtime.reset()  # exactly the one existing constructor reset; orchestrator must not add another
        return runtime
    return collect_attempt(conf, runtime_factory=factory,
        recorder_factory=lambda runtime, raw, ffmpeg, profile: Recorder(runtime, raw),
        prepare_command=prepare_command, validate_runtime=lambda runtime: {"evidence": "engineering_fixture"},
        packager=packager or validated,
        resources={"task_asset": {"asset_id": "fixture", "version": "v1"},
                   "controller": {"asset_id": "fixture-controller", "version": "v1"}},
        source={"version": "fixture-version", "source_commit": None, "implementation": {}},
        evidence_kind="engineering_fixture")


@pytest.mark.parametrize("task", ["push_box", "lift_basket", "press_button"])
def test_three_task_orchestration_owns_terminal_and_never_admits_fixtures(tmp_path, task):
    conf = config(tmp_path, task=task, diagnostic=False)
    runtime = Runtime()
    report = execute(conf, runtime)
    assert report["passed"] and report["status"] == "success"
    assert report["terminal_before_reset"] and report["terminal_simulation_time_ns"] == 40_000_000
    assert not report["eligible_demonstration"] and report["publication_status"] == "local_only"
    assert runtime.closed and runtime.reset_count == 1
    raw = conf.output_dir / report["raw_root"]
    cap = json.loads((raw / "capture.json").read_text())
    assert len(cap["commands"]) == 2 and len(cap["boundaries"]) == 3
    assert cap["diagnostic_only"] and cap["commands"][0]["extensions"]["expert"]["phase"] == "engineering_fixture"
    assert report["episode_uid"] == conf.output_dir.name


def test_partial_attempt_kept_without_packaging_or_eligibility(tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("Partial attempt must not be packaged as usable data")
    conf = config(tmp_path)
    report = execute(conf, Runtime(partial=True), packager=forbidden)
    assert report["partial_interval"] and not report["passed"] and not report["eligible_demonstration"]
    assert report["capture_retained"] and report["raw_validation"] is None
    assert (conf.output_dir / report["raw_root"] / "capture.json").is_file()


@pytest.mark.parametrize("status", ["failure", "timeout"])
def test_unsuccessful_full_attempt_remains_in_attempt_inventory(tmp_path, status):
    conf = config(tmp_path, diagnostic=False)
    report = execute(conf, Runtime(status=status))
    assert report["status"] == status and not report["eligible_demonstration"]
    assert report["capture_retained"] and (conf.output_dir / "attempt.json").is_file()
    cap = json.loads((conf.output_dir / report["raw_root"] / "capture.json").read_text())
    assert cap["status"] == "failure" and cap["task_outcome"]["outcome"] == status
    assert cap["termination_reason"] == status and report["task_outcome"]["outcome"] == status


def test_expert_error_closes_recorder_and_preserves_failure_metadata(tmp_path):
    runtime = Runtime(error=True)
    conf = config(tmp_path)
    report = execute(conf, runtime)
    assert report["status"] == "error" and report["error"]["type"] == "ValueError"
    assert report["capture_retained"] and runtime.closed and not report["passed"]
    assert not report["terminal_before_reset"] and not report["eligible_demonstration"]


def test_packager_failure_does_not_erase_attempt_or_claim_validation(tmp_path):
    def failure(*args, **kwargs):
        raise ValueError("Raw media validation failed")
    conf = config(tmp_path)
    report = execute(conf, Runtime(), packager=failure)
    assert report["status"] == "error" and report["raw_validation"] is None
    assert report["capture_retained"] and not report["eligible_demonstration"]
    assert json.loads((conf.output_dir / "attempt.json").read_text())["error"]["message"] == "Raw media validation failed"
    assert report["task_outcome"]["outcome"] == "success"  # packaging failure does not erase physical outcome


def test_output_must_be_fresh_and_separate_from_resources(tmp_path):
    conf = config(tmp_path)
    with pytest.raises(ValueError):
        replace(conf, output_dir=conf.resource_root / "attempt")
    conf.output_dir.mkdir()
    with pytest.raises(FileExistsError):
        replace(conf)
    with pytest.raises(ValueError):
        replace(conf, output_dir=tmp_path / "other", episode_length_s=.011)


def test_plain_import_and_help_never_load_isaac_or_models():
    code = """import sys
import qlm_bench.collection
from qlm_bench.collection.isaac import main
assert main(['--help']) == 0
assert not any(n == x or n.startswith(x + '.') for n in sys.modules
  for x in ('isaaclab', 'isaacsim', 'omni', 'torch', 'rambo', 'wam_policy', 'transformers'))
"""
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)


def test_cli_bad_profile_fails_before_simulator_import(tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile()))
    resources = tmp_path / "resources"
    resources.mkdir()
    with pytest.raises(SystemExit):
        main(["--task", "push_box", "--profile", str(profile_path), "--resource-root", str(resources),
              "--output-dir", str(tmp_path / "out"), "--ffmpeg", "/missing/ffmpeg",
              "--data-python", sys.executable,
              "--episode-length-s", ".04", "--seed", "0", "--viz", "none"])
    assert not (tmp_path / "out").exists()


def test_source_binding_detects_actual_git_dirty_content(tmp_path):
    repo = tmp_path / "repo"
    source_repo = Path(__file__).resolve().parents[2]
    # Reuse local objects without checking out payloads or making any commits.
    subprocess.run(["git", "clone", "--quiet", "--shared", "--no-checkout", str(source_repo), str(repo)], check=True)
    before = source_identity(repo)
    (repo / "source.py").write_text("first\n")
    after = source_identity(repo)
    assert before["source_commit"] == after["source_commit"]
    assert after["source_dirty"]
    assert before["dirty_source_sha256"] != after["dirty_source_sha256"]


def test_passed_boolean_is_not_a_raw_contract_validation(tmp_path):
    conf = config(tmp_path)
    report = execute(conf, Runtime(), packager=lambda *a, **kw: {"raw": {"passed": True},
                                                               "canonical": {"passed": True}})
    assert report["status"] == "error" and not report["passed"]
    assert not report["eligible_demonstration"] and report["capture_retained"]


def test_cpu_data_interpreter_preflight_imports_frozen_compatibility_without_models():
    data_python = os.environ.get("QLM_DATA_PYTHON")
    if not data_python:
        if any(importlib.util.find_spec(module) is None for module in ("numpy", "PIL", "pyarrow", "av")):
            pytest.skip("Set QLM_DATA_PYTHON to the independent CPU data environment")
        data_python = sys.executable
    selected = _tool(data_python, resolve_symlinks=False)
    receipt = preflight_data_python(selected)
    assert set(receipt["compatibility_locks"]) == {"contracts_v2", "dataset_v2"}
    assert receipt["pyarrow"] and receipt["av"] and receipt["qlm_version"]
    import qlm_bench
    tools = Path(qlm_bench.__file__).parent / "data/tools.py"
    assert receipt["data_code_sha256"]["data/tools.py"] == hashlib.sha256(tools.read_bytes()).hexdigest()


def test_python_tool_preserves_venv_executable_link_and_prefix(tmp_path):
    environment = tmp_path / "isolated-venv"
    venv.EnvBuilder(with_pip=False, symlinks=True).create(environment)
    executable = environment / "bin/python"
    assert executable.is_symlink()
    selected = _tool(str(executable), resolve_symlinks=False)
    assert selected == str(executable.absolute()) and Path(selected).is_symlink()
    preserved = subprocess.check_output([selected, "-c", "import sys;print(sys.prefix)"], text=True).strip()
    assert Path(preserved) == environment
    base = _tool(str(executable))  # media resolution behavior may still resolve symbolic links
    base_prefix = subprocess.check_output([base, "-c", "import sys;print(sys.prefix)"], text=True).strip()
    assert Path(base_prefix) != environment


def test_cli_uses_preserved_data_python_path_before_preflight(tmp_path, monkeypatch):
    import qlm_bench.collection.isaac as entry
    data_python = os.environ.get("QLM_DATA_PYTHON")
    if not data_python:
        if any(importlib.util.find_spec(module) is None for module in ("numpy", "PIL", "pyarrow", "av")):
            pytest.skip("Set QLM_DATA_PYTHON to the independent CPU data environment")
        data_python = sys.executable
    class StopBeforeSimulator(Exception):
        pass
    reached = []
    original_preflight = entry.preflight_data_python
    def preflight(selected):
        assert selected == os.path.abspath(shutil.which(data_python) or data_python)
        reached.append(original_preflight(selected))
        raise StopBeforeSimulator()
    monkeypatch.setattr(entry, "preflight_data_python", preflight)
    monkeypatch.setattr(entry, "_resources", lambda *a, **kw: {"task_asset": {}, "controller": {}})
    conf = config(tmp_path)
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(conf.profile))
    with pytest.raises(StopBeforeSimulator):
        main(["--task", "push_box", "--profile", str(profile_path), "--resource-root", str(conf.resource_root),
              "--output-dir", str(conf.output_dir), "--ffmpeg", "/usr/bin/true", "--ffprobe", "/usr/bin/true",
              "--data-python", data_python, "--episode-length-s", ".04", "--seed", "0", "--viz", "none"])
    assert reached[0]["pyarrow"] and reached[0]["av"]
    assert not conf.output_dir.exists()


def test_data_preflight_rejects_missing_cpu_dependencies(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(
        returncode=1, stdout="", stderr="ModuleNotFoundError: No module named 'pyarrow'"))
    with pytest.raises(ValueError, match="Data Python preflight failed.*pyarrow"):
        preflight_data_python("/fixture/python-without-data-packages")


def test_packaging_uses_explicit_cpu_python_and_retains_stderr(tmp_path, monkeypatch):
    out = tmp_path / "attempt"
    raw = out / "raw" / "episode"
    raw.mkdir(parents=True)
    calls = []
    def process(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout=json.dumps({"raw": {"contract_valid": True},
                              "canonical": {"contract_valid": True}}), stderr="fixture diagnostic")
    monkeypatch.setattr(subprocess, "run", process)
    result = package_with_data_python("/explicit/cpu/python", raw, out / "canonical",
                                     ffmpeg="/explicit/ffmpeg", ffprobe="/explicit/ffprobe")
    assert calls[0][:5] == ["/explicit/cpu/python", "-m", "qlm_bench.cli", "data", "convert"]
    assert result["raw"]["contract_valid"] and (out / "packager.stderr.log").read_text() == "fixture diagnostic"
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=1, stdout="", stderr="failed"))
    with pytest.raises(RuntimeError, match="logs are retained"):
        package_with_data_python("/explicit/cpu/python", raw, out / "canonical",
                                 ffmpeg="/explicit/ffmpeg", ffprobe="/explicit/ffprobe")
    assert raw.is_dir() and (out / "packager.stderr.log").read_text() == "failed"


def test_explicit_button_variant_disambiguates_equal_entrypoint_hashes(tmp_path, monkeypatch):
    from qlm_bench import assets
    manifest = assets.load_manifest("industrial-button-green")
    entry_hash = manifest["files"][manifest["entrypoint"]]["sha256"]
    matches = [assets.load_manifest(f"industrial-button-{color}") for color in ("blue", "green", "orange")]
    assert len({m["files"][m["entrypoint"]]["sha256"] for m in matches}) == 1
    calls = []
    monkeypatch.setattr(assets, "resolve_asset", lambda asset_id, root: calls.append(asset_id))
    chosen = _resources({"asset_id": "industrial-button-green", "asset_sha256": entry_hash},
                        tmp_path, task="press_button")
    assert chosen["task_asset"]["asset_id"] == "industrial-button-green"
    assert chosen["task_asset"]["files"] == manifest["files"]
    assert calls == ["industrial-button-green", "rambo-go2-controller"]
    calls.clear()
    with pytest.raises(ValueError, match="Ambiguous entrypoint hash"):
        _resources({"asset_sha256": entry_hash}, tmp_path, task="press_button")
    assert calls == []
    with pytest.raises(ValueError, match="task usage"):
        _resources({"asset_id": "industrial-button-green", "asset_sha256": entry_hash},
                   tmp_path, task="push_box")
    with pytest.raises(ValueError, match="source hash"):
        _resources({"asset_id": "industrial-button-green", "asset_sha256": "0" * 64},
                   tmp_path, task="press_button")


def test_callback_is_required_and_attaches_recorder_before_original_reset(tmp_path):
    conf = config(tmp_path)
    events = []
    runtime = Runtime()
    def factory(config, *, on_environment_ready):
        events.append("environment_constructed")
        on_environment_ready(runtime)
        assert runtime.base_env._v2_recorder is not None
        events.append("recorder_attached")
        runtime.reset()
        events.append("original_reset")
        return runtime
    def recording(runtime, raw, ffmpeg, profile):
        rec = Recorder(runtime, raw)
        original = rec.begin
        def begin():
            events.append("recording_begin")
            original()
        rec.begin = begin
        return rec
    report = collect_attempt(conf, runtime_factory=factory, recorder_factory=recording,
        prepare_command=prepare_command, validate_runtime=lambda r: {},
        packager=lambda *a, **kw: (_ for _ in ()).throw(ValueError("Fixture does not package actual data")),
        resources={"task_asset": {}, "controller": {}}, source={"version": "fixture"},
        evidence_kind="engineering_fixture")
    assert events == ["environment_constructed", "recorder_attached", "original_reset", "recording_begin"]
    assert runtime.reset_count == 1 and report["capture_retained"]


def test_actual_timeout_capture_converts_to_legacy_failure_without_source_changes(tmp_path):
    source_value = os.environ.get("QLM_TIMEOUT_CAPTURE")
    if not source_value:
        pytest.skip("Set QLM_TIMEOUT_CAPTURE to an immutable actual full-interval timeout capture")
    source = Path(source_value)
    data_python = os.environ.get("QLM_DATA_PYTHON", sys.executable)
    ffmpeg = os.environ.get("QLM_FFMPEG") or shutil.which("ffmpeg")
    ffprobe = os.environ.get("QLM_FFPROBE") or shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        pytest.skip("Explicit local ffmpeg/ffprobe required for the actual conversion regression")
    def inventory(root):
        return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in root.rglob("*") if path.is_file()}
    before = inventory(source)
    capture = json.loads((source / "capture.json").read_text())
    assert capture["diagnostic_only"] and capture["status"] == "timeout"
    terminal = capture["terminal"]
    count = len(capture["commands"])
    assert terminal["reason"] == "timeout" and not terminal["partial_interval"]
    assert count > 0 and len(capture["boundaries"]) == count + 1
    assert all(command["status"] == "completed" for command in capture["commands"])
    raw = tmp_path / "raw" / source.name
    shutil.copytree(source, raw, ignore=shutil.ignore_patterns("manifest.json", "raw-validation.json", "streams", "metadata"))
    capture["status"] = legacy_capture_status("timeout")
    capture["termination_reason"] = terminal["reason"]
    capture["task_outcome"] = {"outcome": "timeout", "success": False, "fallen": False,
                               "timed_out": True, "termination_reason": terminal["reason"]}
    (raw / "capture.json").write_text(json.dumps(capture, indent=2))
    summary = json.loads((raw / "summary.json").read_text())
    # The original failure is packaging, while complete physical-capture evidence is retained.
    summary["passed"] = count > 0 and len(capture["boundaries"]) == count + 1 and not terminal["partial_interval"]
    summary["terminal_before_reset"] = capture["boundaries"][-1]["simulation_time_ns"] == terminal["simulation_time_ns"]
    summary["status"] = "timeout"
    (raw / "summary.json").write_text(json.dumps(summary, indent=2))
    canonical = tmp_path / "canonical"
    result = package_with_data_python(_tool(data_python, resolve_symlinks=False), raw, canonical,
                                     ffmpeg=_tool(ffmpeg), ffprobe=_tool(ffprobe))
    assert result["raw"]["contract_valid"] and result["canonical"]["contract_valid"]
    manifest = json.loads((canonical / "meta/contract.json").read_text())
    assert manifest["episodes"][0]["status"] == "failure"
    assert manifest["episodes"][0]["length"] == count and result["canonical"]["episodes"][0]["terminal_action_count"] == 0
    assert json.loads((raw / "capture.json").read_text())["task_outcome"]["outcome"] == "timeout"
    assert inventory(source) == before
