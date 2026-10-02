"""Public scripted generation after explicit runtime/resource selection; no internal approval gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .orchestrator import CollectionConfig, TASK_PREFIXES, collect_attempt, source_identity

TASK_IDS = {"push_box": "Isaac-RAMBO-Quadruped-Push-Box-V2-Go2-v0",
            "lift_basket": "Isaac-RAMBO-Quadruped-Lift-Basket-Go2-v0",
            "press_button": "Isaac-RAMBO-Quadruped-Press-Button-V2-Go2-v0"}


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--task", choices=tuple(TASK_PREFIXES), required=True)
    result.add_argument("--profile", type=Path, required=True)
    result.add_argument("--resource-root", type=Path, required=True)
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--ffmpeg", required=True)
    result.add_argument("--ffprobe", help="Defaults only to ffprobe beside the explicitly selected ffmpeg")
    result.add_argument("--data-python", required=True,
                        help="Independent CPU data environment with QLM, numpy/Pillow/pyarrow/av installed")
    result.add_argument("--episode-length-s", type=float, required=True)
    result.add_argument("--seed", type=int, required=True)
    result.add_argument("--diagnostic-only", action="store_true")
    return result


def _tool(value, *, resolve_symlinks=True):
    located = shutil.which(value)
    selected = located if located else value
    # Python locates pyvenv.cfg through its invoked executable path. Resolving a
    # venv/bin/python link would silently select the bare base interpreter.
    path = Path(selected).resolve() if resolve_symlinks else Path(os.path.abspath(selected))
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError("Executable tool unavailable: " + str(path))
    return str(path)


def _resources(profile, root, *, task):
    from qlm_bench.assets import load_registry, load_manifest, resolve_asset
    registry = load_registry()
    explicit = profile.get("asset_id")
    if explicit is not None:
        asset = load_manifest(explicit, registry)
    else:
        matches = []
        for row in registry["resources"]:
            manifest = load_manifest(row["asset_id"], registry)
            if manifest["kind"] == "asset" and \
                    manifest["files"][manifest["entrypoint"]]["sha256"] == profile["asset_sha256"]:
                matches.append(manifest)
        if len(matches) != 1:
            raise ValueError("Ambiguous entrypoint hash; profile.asset_id must select the full resource manifest")
        asset = matches[0]
    if asset["kind"] != "asset" or task not in asset["tasks"] or \
            asset["files"][asset["entrypoint"]]["sha256"] != profile["asset_sha256"]:
        raise ValueError("Explicit asset identity does not match task usage and profile source hash")
    controller = load_manifest("rambo-go2-controller", registry)
    for manifest in (asset, controller):
        resolve_asset(manifest["asset_id"], root)
    def record(manifest):
        return {"asset_id": manifest["asset_id"], "version": manifest["version"],
                "manifest_sha256": next(row["manifest_sha256"] for row in registry["resources"]
                                        if row["asset_id"] == manifest["asset_id"]),
                "files": manifest["files"],
                "entrypoint_sha256": manifest["files"][manifest["entrypoint"]]["sha256"],
                "source": manifest["source"]}
    return {"task_asset": record(asset), "controller": record(controller)}


def preflight_data_python(data_python):
    script = """import hashlib, json, sys
from pathlib import Path
import qlm_bench, numpy, PIL, pyarrow, av
from qlm_bench.data import tools
root = Path(qlm_bench.__file__).parent
locks = {name: hashlib.sha256((root / 'compatibility' / name / 'spec/lock.json').read_bytes()).hexdigest()
         for name in ('contracts_v2', 'dataset_v2')}
code_files = [root / 'cli.py', root / 'data/tools.py']
for name in ('contracts_v2', 'dataset_v2'):
    code_files.extend((root / 'compatibility' / name).glob('*.py'))
code_hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in sorted(code_files)}
assert not any(name == prefix or name.startswith(prefix + '.') for name in sys.modules
               for prefix in ('torch', 'isaaclab', 'isaacsim', 'omni', 'wam_policy'))
print(json.dumps({'python': sys.version.split()[0], 'qlm_version': qlm_bench.__version__,
                  'numpy': numpy.__version__, 'Pillow': PIL.__version__, 'pyarrow': pyarrow.__version__,
                  'av': av.__version__, 'compatibility_locks': locks, 'data_code_sha256': code_hashes}))
"""
    completed = subprocess.run([data_python, "-c", script], capture_output=True, text=True)
    if completed.returncode:
        raise ValueError("Data Python preflight failed: " + completed.stderr[-2000:])
    receipt = json.loads(completed.stdout)
    from qlm_bench import __version__
    root = Path(__file__).resolve().parents[1]
    expected = {name: hashlib.sha256((root / "compatibility" / name / "spec/lock.json").read_bytes()).hexdigest()
                for name in ("contracts_v2", "dataset_v2")}
    code_files = [root / "cli.py", root / "data/tools.py"]
    for name in ("contracts_v2", "dataset_v2"):
        code_files.extend((root / "compatibility" / name).glob("*.py"))
    code_hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in sorted(code_files)}
    if receipt["qlm_version"] != __version__ or receipt["compatibility_locks"] != expected or \
            receipt["data_code_sha256"] != code_hashes:
        raise ValueError("Data Python uses a different QLM compatibility package")
    return receipt


def package_with_data_python(data_python, raw, canonical, *, ffmpeg, ffprobe):
    command = [data_python, "-m", "qlm_bench.cli", "data", "convert", "--raw", str(raw),
               "--canonical", str(canonical), "--ffmpeg", ffmpeg, "--ffprobe", ffprobe]
    completed = subprocess.run(command, capture_output=True, text=True)
    logs = Path(raw).parents[1]
    (logs / "packager.stdout.log").write_text(completed.stdout)
    (logs / "packager.stderr.log").write_text(completed.stderr)
    if completed.returncode:
        raise RuntimeError("CPU Raw packaging failed; the attempt and packager logs are retained")
    result = json.loads(completed.stdout)
    if not isinstance(result, dict) or not {"raw", "canonical"} <= set(result):
        raise ValueError("CPU packager returned no explicit Raw/Canonical validation")
    return result


def main(argv=None):
    raw_args = list(sys.argv[1:] if argv is None else argv)
    command_parser = parser()
    # Help is available on ordinary Python. Required local inputs are checked before loading Isaac.
    if "--help" in raw_args or "-h" in raw_args:
        command_parser.add_argument("--viz", choices=("none", "kit"), required=True)
        command_parser.print_help()
        return 0
    preliminary, _ = command_parser.parse_known_args(raw_args)
    try:
        profile = json.loads(preliminary.profile.read_text())
        ffmpeg = _tool(preliminary.ffmpeg)
        ffprobe = _tool(preliminary.ffprobe or str(Path(ffmpeg).with_name("ffprobe")))
        data_python = _tool(preliminary.data_python, resolve_symlinks=False)
        config = CollectionConfig(preliminary.task, profile, preliminary.resource_root,
                                  preliminary.output_dir, ffmpeg, ffprobe, data_python,
                                  preliminary.episode_length_s, preliminary.seed,
                                  preliminary.diagnostic_only, "cuda:0")
        resources = _resources(profile, config.resource_root, task=config.task)
        data_environment = preflight_data_python(data_python)
    except (OSError, ValueError, TypeError) as error:
        command_parser.error(str(error))
    from isaaclab.app import AppLauncher
    from rambo.utils.physx import assert_physx_environment, validate_rambo_visualizer_args
    AppLauncher.add_app_launcher_args(command_parser)
    args = command_parser.parse_args(raw_args)
    validate_rambo_visualizer_args(command_parser, args, raw_args)
    args.enable_cameras = True
    # Explicit runtime options cannot change the fixed physical contract.
    config = CollectionConfig(config.task, config.profile, config.resource_root, config.output_dir,
                              config.ffmpeg, config.ffprobe, config.data_python, config.episode_length_s, config.seed,
                              config.diagnostic_only, getattr(args, "device", "cuda:0"))
    app = None
    code = 1
    launch_source = source_identity()
    try:
        app = AppLauncher(args)
        from rambo.tasks.common.controller_runtime import ControllerRuntime
        from rambo.contracts_v2.runtime import prepare_command
        from rambo.recording_v2 import Recorder
        import omni.replicator.core as rep
        import importlib.metadata
        import torch

        observer_handles = []
        def recorder_factory(runtime, raw, ffmpeg, profile):
            geometry = profile["observer"]
            camera = rep.create.camera(position=geometry["position"], look_at=geometry["look_at"], focal_length=24)
            product = rep.create.render_product(camera, (1280, 720))
            rgb = rep.AnnotatorRegistry.get_annotator("rgb", device="cpu")
            rgb.attach(product)
            observer_handles.extend([camera, product, rgb])
            return Recorder(runtime.base_env, raw, ffmpeg, rgb)

        def runtime_factory(config, *, on_environment_ready):
            return ControllerRuntime(TASK_IDS[config.task], profile=dict(config.profile),
                                     resource_root=config.resource_root, asset_id=resources["task_asset"]["asset_id"],
                                     seed=config.seed, episode_length_s=config.episode_length_s, device=config.device,
                                     on_environment_ready=on_environment_ready)

        def runtime_validation(runtime):
            receipt = assert_physx_environment(runtime.env)
            receipt["torch"] = torch.__version__
            receipt["data_environment"] = data_environment
            receipt["packages"] = {}
            for name in ("isaacsim", "isaaclab", "isaaclab_physx"):
                try:
                    receipt["packages"][name] = importlib.metadata.version(name)
                except importlib.metadata.PackageNotFoundError:
                    receipt["packages"][name] = "source-package; identity recorded by checkout"
            return receipt

        after_startup_source = source_identity()
        for field in ("source_commit", "dirty_source_sha256", "implementation", "version"):
            if after_startup_source.get(field) != launch_source.get(field):
                raise RuntimeError("Source changed during simulator startup; use a fresh unambiguous attempt")

        report = collect_attempt(config, runtime_factory=runtime_factory, recorder_factory=recorder_factory,
                                 prepare_command=prepare_command,
                                 validate_runtime=runtime_validation,
                                 packager=lambda raw, canonical, **tools: package_with_data_python(
                                     config.data_python, raw, canonical, **tools),
                                 resources=resources, source=launch_source,
                                 evidence_kind="actual_runtime")
        print(json.dumps(report, allow_nan=False), flush=True)
        code = 0 if report["passed"] else 1
    except (Exception, KeyboardInterrupt) as error:
        # Startup failures also remain an explicit local attempt, with no successful capture claim.
        if not config.output_dir.exists():
            config.output_dir.mkdir(parents=True)
        (config.output_dir / "startup-error.json").write_text(json.dumps({
            "schema": "qlm-collection-startup-error-v1", "task": config.task, "source": source_identity(),
            "publication_status": "local_only", "eligible_demonstration": False,
            "error_type": type(error).__name__, "error_message": str(error)}, indent=2) + "\n")
        print(f"Collection failed: {type(error).__name__}: {error}", file=sys.stderr)
    finally:
        if app is not None:
            app.app.close(exit_code=code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
