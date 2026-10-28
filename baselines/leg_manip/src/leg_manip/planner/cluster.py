"""AMD MI355X job driver: all DP3 planner runs of one tag in one SLURM job.

Started by ``scripts/amd/planner.sbatch`` inside the project venv:

    python -m leg_manip.planner.cluster run --tag dp3-20261029 --work <dir>
    python -m leg_manip.planner.cluster publish --tag dp3-20261029 --work <dir>

Stages of ``run`` (each recorded in a W&B pipeline run and in
``<work>/runs/<tag>/job_report.json``):

- environment: torch/HIP build, visible GPUs vs. the SLURM allocation, a matmul on
  every GPU, package versions.
- credentials: W&B login (the pipeline run itself) and HF write access to the
  upload repo. Missing HF access does not stop training; publish reports it.
- data: the pinned dataset revision, zip SHA-256 and DemoDataset fingerprints.
- tests: the simulator-free unit tests.
- preflight: a short training run on real data, then EMA reload and sampling.
- train: every task x seed run in parallel, one subprocess per run, runs spread
  over the visible GPUs.
- publish: EMA exports, logs and the report to the HF model repo, verified by
  SHA-256 against the remote listing.

A tag is idempotent: finished runs are skipped and interrupted runs resume from
latest.pt, so resubmitting the same tag continues the job. No simulator is
imported here.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path

import torch
import tyro

from leg_manip import hub

DATA_REPO = "Ethan-Xu-Deng/legmanip-demo"
DATA_REVISION = "f096ba95637029f70b712abe7db5811081f5aaf7"
UPLOAD_REPO = "Ethan-Xu-Deng/legmanip-weights"
# Published 2026-10-28 (see TRAINING_RUN.md); SHA-256 of each zip and the
# DemoDataset fingerprint of its contents.
DATASETS = {
    "press_button": (
        "f5f5c2545b892036de6de5493d709ae3f4648a5353a27ed108890119b2a1ecba",
        "c0f1a92c174a56e960efec39abb65893bc1148a3abe1d9981fe13ec0e0f85e8c",
    ),
    "close_dishwasher": (
        "83ebd1ab12e7963f810d3df4b853b753bd84bf38600c10795b8125a00f09daa4",
        "b5362a3c9a6265d0e14d1c29e0a2df054e34f827dc6b48a0845967564d2f27f4",
    ),
}
TEST_FILES = (
    "tests/test_traj.py",
    "tests/test_planner_dataset.py",
    "tests/test_planner_training.py",
    "tests/test_planner_is_sim_free.py",
    "tests/test_hub.py",
    "tests/test_cluster.py",
)
PACKAGES = (
    "numpy",
    "zarr",
    "numcodecs",
    "diffusers",
    "huggingface_hub",
    "safetensors",
    "wandb",
    "einops",
    "tyro",
    "leg-manip",
)
# Published files, relative to <work>/runs/<tag>: EMA exports, run summaries and
# logs. Full training states (*.pt) and W&B scratch directories stay on the
# cluster. job_report.json changes until the end and is uploaded last, unverified.
PUBLISH_FILE = re.compile(
    r"[a-z_]+/seed\d+/(epoch\d{4}/(model\.safetensors|config\.json)"
    r"|train_summary\.json|wandb_runs\.jsonl)"
    r"|logs/[\w.-]+\.log"
)
EPOCH_LINE = re.compile(r"\[planner\] epoch (\d+)/(\d+)")


@dataclass
class JobArgs:
    tag: str
    """Job name; outputs go to <work>/runs/<tag> and HF planner/<tag>."""
    work: Path
    """Shared work directory (venv, runs)."""
    scratch: Path = Path("/tmp/legmanip")
    """Node-local directory for the HF cache, extracted data and preflight."""
    tasks: tuple[str, ...] = tuple(DATASETS)
    seeds: tuple[int, ...] = (0, 1, 2)
    num_epochs: int = 500
    checkpoint_every: int = 50
    """Full training state (about 4 GB) every this many epochs."""
    preflight_epochs: int = 2
    require_rocm: bool = True
    run_tests: bool = True
    upload: str = "hf"
    """hf | dryrun | none"""
    upload_repo: str = UPLOAD_REPO
    wandb_entity: str = "junlinlong-the-university-of-sydney"
    wandb_project: str = "WAM-Policy"
    wandb_mode: str = "online"
    """online | offline | disabled"""
    expect_wandb_user: str | None = "dengxu1207"
    """Stop before training if W&B is logged in as anyone else (online mode)."""
    poll_seconds: float = 60.0


@dataclass
class RunSpec:
    task: str
    seed: int
    gpu: int
    out_dir: Path
    log: Path
    action: str
    """fresh | resume | done"""


class StageFailed(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def package_versions() -> dict[str, str | None]:
    versions = {}
    for name in PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def slurm_gpu_count() -> int | None:
    """GPUs SLURM allocated on this node, if the job says so."""
    value = os.environ.get("SLURM_GPUS_ON_NODE", "")
    return int(value) if value.isdigit() else None


def hf_can_write(whoami: dict, repo: str, repo_type: str = "model") -> bool:
    """Whether the token behind ``whoami`` may push to ``repo``.

    Classic write tokens may write wherever the user can (own namespace or an
    org). Fine-grained tokens need repo.write on that repo or on its namespace.
    """
    namespace = repo.split("/")[0]
    token = whoami.get("auth", {}).get("accessToken", {})
    role = token.get("role")
    if role == "write":
        owners = {whoami.get("name")} | {o.get("name") for o in whoami.get("orgs", [])}
        return namespace in owners
    if role != "fineGrained":
        return False
    for scope in token.get("fineGrained", {}).get("scoped", []):
        entity = scope.get("entity", {})
        if "repo.write" not in scope.get("permissions", []):
            continue
        if entity.get("type") == repo_type and entity.get("name") == repo:
            return True
        if entity.get("type") in ("user", "org") and entity.get("name") == namespace:
            return True
    return False


def plan_runs(args: JobArgs, runs_root: Path, num_gpus: int) -> list[RunSpec]:
    """Assign runs round-robin to GPUs and decide fresh / resume / done."""
    specs = []
    for i, (task, seed) in enumerate(
        (task, seed) for task in args.tasks for seed in args.seeds
    ):
        out_dir = runs_root / task / f"seed{seed}"
        if (out_dir / "train_summary.json").is_file():
            action = "done"
        elif (out_dir / "latest.pt").is_file():
            action = "resume"
        else:
            action = "fresh"
        specs.append(
            RunSpec(
                task=task,
                seed=seed,
                gpu=i % num_gpus,
                out_dir=out_dir,
                log=runs_root / "logs" / f"{task}-seed{seed}.log",
                action=action,
            )
        )
    return specs


def train_command(args: JobArgs, spec: RunSpec, runs_root: Path) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "leg_manip.planner.train",
        "--hf-repo",
        DATA_REPO,
        "--hf-file",
        f"{spec.task}.zarr.zip",
        "--hf-revision",
        DATA_REVISION,
        "--seed",
        str(spec.seed),
        "--num-epochs",
        str(args.num_epochs),
        "--checkpoint-every",
        str(args.checkpoint_every),
        "--out-root",
        str(runs_root),
        "--device",
        f"cuda:{spec.gpu}",
        "--wandb-entity",
        args.wandb_entity,
        "--wandb-project",
        args.wandb_project,
        "--wandb-mode",
        args.wandb_mode,
        "--wandb-group",
        f"planner-{args.tag}",
        "--wandb-tags",
        "dp3",
        "amd",
        args.tag,
        "--run-name",
        f"planner-{spec.task}-seed{spec.seed}-{args.tag}",
    ]
    if spec.action == "resume":
        cmd += ["--resume", str(spec.out_dir / "latest.pt")]
    return cmd


def last_epoch(log: Path) -> int:
    """Last epoch printed by train.py (prints every val_every epochs)."""
    if not log.is_file():
        return 0
    with log.open("rb") as stream:
        stream.seek(max(0, log.stat().st_size - 65536))
        tail = stream.read().decode(errors="replace")
    found = EPOCH_LINE.findall(tail)
    return int(found[-1][0]) if found else 0


def run_epoch(spec: RunSpec) -> int:
    """Epochs a run has completed: exact once finished, else from its log."""
    summary = spec.out_dir / "train_summary.json"
    if summary.is_file():
        return int(json.loads(summary.read_text())["epochs"])
    return last_epoch(spec.log)


def tail_text(path: Path, lines: int = 40) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(errors="replace").splitlines()
    return "\n".join(text[-lines:])


def remote_digest(entry) -> tuple[int | None, str | None]:
    """(size, LFS sha256) of a list_repo_tree entry across hub versions."""
    lfs = getattr(entry, "lfs", None)
    sha = getattr(lfs, "sha256", None)
    if sha is None and isinstance(lfs, dict):
        sha = lfs.get("sha256")
    return getattr(entry, "size", None), sha


class Pipeline:
    """Job report on disk plus a W&B pipeline run; both updated after each stage."""

    def __init__(self, args: JobArgs, runs_root: Path, mode: str) -> None:
        self.args = args
        self.runs_root = runs_root
        self.report_path = runs_root / "job_report.json"
        self.report = {"tag": args.tag, "mode": mode, "stages": {}, "runs": {}}
        if self.report_path.is_file():
            previous = json.loads(self.report_path.read_text())
            self.report["previous_attempts"] = previous.get("previous_attempts", [])
            self.report["previous_attempts"].append(
                {k: previous.get(k) for k in ("slurm_job_id", "stages", "status")}
            )
        self.report["slurm_job_id"] = os.environ.get("SLURM_JOB_ID")
        self.report["args"] = json.loads(json.dumps(asdict(args), default=str))
        self.wandb_run = None
        self.wandb_error = None
        self.wandb_user = None
        self.identity_problem = None
        self._start_wandb(mode)
        self.save()

    def _start_wandb(self, mode: str) -> None:
        import wandb

        settings = {
            "project": self.args.wandb_project,
            "entity": self.args.wandb_entity,
            "group": f"planner-{self.args.tag}",
            "job_type": f"amd-pipeline-{mode}",
            "name": f"dp3-pipeline-{self.args.tag}-{mode}",
            "tags": ["dp3", "amd", self.args.tag],
            "config": self.report["args"],
            "dir": str(self.runs_root),
        }
        if self.args.wandb_mode == "online" and self.args.expect_wandb_user:
            # Check the account before creating any run under it.
            try:
                self.wandb_user = getattr(wandb.Api().viewer, "username", None)
            except Exception as exc:
                self.wandb_error = f"{type(exc).__name__}: {exc}"
            self.identity_problem = wandb_user_problem(
                self.wandb_user, self.args.expect_wandb_user
            )
            if self.identity_problem is not None:
                self.wandb_run = wandb.init(mode="disabled", **settings)
                return
        try:
            self.wandb_run = wandb.init(mode=self.args.wandb_mode, **settings)
        except Exception as exc:
            # Keep a local record; the training runs fall back the same way.
            self.wandb_error = f"{type(exc).__name__}: {exc}"
            print(f"[cluster] W&B unavailable, logging offline: {exc}", flush=True)
            if self.args.wandb_mode == "online":
                self.args.wandb_mode = "offline"
                self.wandb_run = wandb.init(mode="offline", **settings)

    def save(self) -> None:
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.report_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(self.report, indent=2, default=str))
        os.replace(temporary, self.report_path)

    def log(self, values: dict) -> None:
        if self.wandb_run is not None:
            self.wandb_run.log(values)

    def summary(self, values: dict) -> None:
        if self.wandb_run is not None:
            self.wandb_run.summary.update(values)

    @contextmanager
    def stage(self, name: str) -> Iterator[dict]:
        """Time a stage; record passed / failed (with traceback) and re-raise."""
        detail: dict = {}
        record = {"status": "running", "detail": detail}
        self.report["stages"][name] = record
        self.save()
        start = time.time()
        print(f"[cluster] stage {name}", flush=True)
        try:
            yield detail
        except BaseException as exc:
            record["status"] = "failed"
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["traceback"] = traceback.format_exc()[-4000:]
            self.summary(
                {
                    f"stage/{name}": "failed",
                    "failure/stage": name,
                    "failure/type": type(exc).__name__,
                    "failure/message": str(exc)[:2000],
                }
            )
            raise
        else:
            record["status"] = detail.pop("_status", "passed")
            self.summary({f"stage/{name}": record["status"]})
        finally:
            record["seconds"] = round(time.time() - start, 1)
            self.save()

    def finish(self, status: str) -> None:
        self.report["status"] = status
        self.save()
        self.summary({"pipeline/status": status})
        if self.wandb_run is not None:
            self.wandb_run.finish(exit_code=0 if status == "passed" else 1)


def stage_environment(args: JobArgs, detail: dict, need_gpu: bool) -> int:
    detail.update(
        host=socket.gethostname(),
        python=platform.python_version(),
        torch=torch.__version__,
        hip=torch.version.hip,
        cuda=torch.version.cuda,
        packages=package_versions(),
        source_commit=os.environ.get("LEGMANIP_SOURCE_COMMIT"),
        env_setup=os.environ.get("LEGMANIP_ENV_SETUP"),
        cleared_vars=os.environ.get("LEGMANIP_CLEARED_VARS", "").split(),
        visible_devices={
            key: os.environ.get(key)
            for key in (
                "ROCR_VISIBLE_DEVICES",
                "HIP_VISIBLE_DEVICES",
                "CUDA_VISIBLE_DEVICES",
                "SLURM_JOB_GPUS",
                "SLURM_GPUS_ON_NODE",
            )
        },
    )
    if not need_gpu:
        return 0
    if args.require_rocm and not torch.version.hip:
        raise StageFailed("torch is not a ROCm build (torch.version.hip is None)")
    if not torch.cuda.is_available():
        raise StageFailed("torch sees no GPU")
    count = torch.cuda.device_count()
    allocated = slurm_gpu_count()
    detail["device_count"] = count
    if allocated is not None and count != allocated:
        raise StageFailed(
            f"torch sees {count} GPUs but SLURM allocated {allocated}; "
            "set ROCR_VISIBLE_DEVICES to the job's GPUs"
        )
    names = []
    for index in range(count):
        device = torch.device("cuda", index)
        x = torch.randn(1024, 1024, device=device)
        value = (x @ x).sum().item()
        if not torch.isfinite(torch.tensor(value)):
            raise StageFailed(f"non-finite matmul on GPU {index}")
        names.append(torch.cuda.get_device_name(index))
    detail["device_names"] = names
    return count


def wandb_user_problem(user: str | None, expected: str | None) -> str | None:
    """Why the W&B login is not the expected account; None if it is or unknown."""
    if expected is None or user is None or user == expected:
        return None
    return (
        f"W&B is logged in as {user!r}, expected {expected!r}; "
        "check LEGMANIP_SECRETS (runs must be logged under the submitter)"
    )


def stage_credentials(args: JobArgs, pipeline: Pipeline, detail: dict) -> bool:
    """W&B account and HF write access; returns whether HF upload can work."""
    detail["secret_keys"] = os.environ.get("LEGMANIP_SECRET_KEYS", "").split()
    detail["wandb_mode"] = args.wandb_mode
    detail["wandb_user"] = pipeline.wandb_user
    detail["wandb_error"] = pipeline.wandb_error
    if pipeline.identity_problem is not None:
        raise StageFailed(pipeline.identity_problem)
    if pipeline.wandb_run is not None and args.wandb_mode == "online":
        detail["wandb_url"] = pipeline.wandb_run.url
    if args.upload != "hf":
        detail["hf_write"] = None
        return False
    from huggingface_hub import HfApi

    try:
        info = hub.with_retries(lambda: HfApi().whoami(), "whoami")
    except Exception as exc:
        detail["hf_error"] = f"{type(exc).__name__}: {exc}"
        detail["hf_write"] = False
    else:
        detail["hf_user"] = info.get("name")
        detail["hf_write"] = hf_can_write(info, args.upload_repo)
    if not detail["hf_write"]:
        detail["_status"] = "warning"
        print(
            f"[cluster] WARNING: HF token cannot write {args.upload_repo}; "
            "training continues, publish will fail until the token is fixed",
            flush=True,
        )
    return detail["hf_write"]


def stage_data(args: JobArgs, detail: dict) -> dict[str, Path]:
    from huggingface_hub import hf_hub_download

    from leg_manip.planner.dataset import DemoDataset

    paths = {}
    for task in args.tasks:
        zip_sha, fingerprint = DATASETS[task]
        path, revision = hub.download(
            DATA_REPO,
            f"{task}.zarr.zip",
            revision=DATA_REVISION,
            out_dir=args.scratch / hub.DEFAULT_CACHE,
        )
        if revision != DATA_REVISION:
            raise StageFailed(f"{task}: resolved revision {revision}")
        archive = Path(
            hub.with_retries(
                lambda task=task: hf_hub_download(
                    DATA_REPO,
                    f"{task}.zarr.zip",
                    repo_type="dataset",
                    revision=DATA_REVISION,
                ),
                f"download {task}",
            )
        )
        got_zip = sha256_file(archive)
        ds = DemoDataset(path, 4, 2, 1, device="cpu")
        detail[task] = {
            "path": str(path),
            "zip_sha256": got_zip,
            "fingerprint": ds.fingerprint,
            "episodes": ds.num_episodes,
            "train_windows": len(ds.train_index),
        }
        if got_zip != zip_sha or ds.fingerprint != fingerprint:
            raise StageFailed(f"{task}: dataset checksum mismatch")
        paths[task] = path
    return paths


def stage_tests(detail: dict, log: Path) -> None:
    project = Path(__file__).resolve().parents[3]
    files = [f for f in TEST_FILES if (project / f).is_file()]
    detail["files"] = files
    if not files:
        detail["_status"] = "skipped"
        return
    env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    with log.open("w") as stream:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *files],
            cwd=project,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        )
    detail["tail"] = tail_text(log, 5)
    if result.returncode != 0:
        raise StageFailed(f"unit tests failed (exit {result.returncode}); see {log}")


def stage_preflight(args: JobArgs, data: dict[str, Path], detail: dict, log: Path):
    from leg_manip.planner.dataset import DemoDataset
    from leg_manip.planner.policy import PlannerPolicy

    task = args.tasks[0]
    root = args.scratch / "preflight" / args.tag
    shutil.rmtree(root, ignore_errors=True)
    cmd = [
        sys.executable,
        "-m",
        "leg_manip.planner.train",
        "--data",
        str(data[task]),
        "--num-epochs",
        str(args.preflight_epochs),
        "--checkpoint-fractions",
        "1.0",
        "--val-every",
        "1",
        "--out-root",
        str(root),
        "--device",
        "cuda:0",
        "--wandb-mode",
        "disabled",
    ]
    start = time.time()
    with log.open("w") as stream:
        result = subprocess.run(
            cmd, stdout=stream, stderr=subprocess.STDOUT, check=False, timeout=3600
        )
    detail["seconds_train"] = round(time.time() - start, 1)
    detail["tail"] = tail_text(log, 6)
    if result.returncode != 0:
        raise StageFailed(f"preflight training failed (exit {result.returncode})")
    ckpt = root / task / "seed0" / f"epoch{args.preflight_epochs:04d}"
    policy = PlannerPolicy(ckpt, device="cuda:0")
    ds = DemoDataset(data[task], 4, 2, 1, device="cuda:0")
    frames = ds.train_index[:16, 0]
    first = policy(ds.data["point_cloud"][frames], ds.data["state"][frames], True)
    second = policy(ds.data["point_cloud"][frames], ds.data["state"][frames], False)
    target = ds.data["action"][frames]
    if first.shape != target.shape or not (
        torch.isfinite(first).all() and torch.isfinite(second).all()
    ):
        raise StageFailed(f"bad planner output {tuple(first.shape)}")
    detail["sample_mae"] = (first - target).abs().mean().item()
    shutil.rmtree(root, ignore_errors=True)


def stage_train(
    args: JobArgs, pipeline: Pipeline, runs_root: Path, num_gpus: int, detail: dict
) -> list[RunSpec]:
    specs = plan_runs(args, runs_root, num_gpus)
    (runs_root / "logs").mkdir(parents=True, exist_ok=True)
    procs: dict[str, tuple[RunSpec, subprocess.Popen, object]] = {}
    for spec in specs:
        key = f"{spec.task}-seed{spec.seed}"
        record = {"action": spec.action, "gpu": spec.gpu}
        pipeline.report["runs"][key] = record
        if spec.action == "done":
            record.update(status="done", epoch=run_epoch(spec))
            continue
        if spec.action == "fresh" and spec.out_dir.exists():
            # Died before its first checkpoint; keep it for inspection.
            stamp = int(time.time())
            aside = spec.out_dir.with_name(f"{spec.out_dir.name}.failed-{stamp}")
            spec.out_dir.rename(aside)
            record["moved_aside"] = str(aside)
        miopen = args.scratch / "miopen" / key
        miopen.mkdir(parents=True, exist_ok=True)
        env = {
            **os.environ,
            "PYTHONUNBUFFERED": "1",
            "MIOPEN_USER_DB_PATH": str(miopen),
            "MIOPEN_CUSTOM_CACHE_DIR": str(miopen),
        }
        stream = spec.log.open("a")
        stream.write(f"\n=== {time.strftime('%F %T')} {spec.action} ===\n")
        stream.flush()
        proc = subprocess.Popen(
            train_command(args, spec, runs_root),
            cwd=args.scratch,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
        procs[key] = (spec, proc, stream)
        record["status"] = "running"
        record["pid"] = proc.pid
    pipeline.save()

    def stop_children(signum, frame):
        for _, proc, _ in procs.values():
            if proc.poll() is None:
                proc.terminate()
        raise KeyboardInterrupt(f"signal {signum}")

    signal.signal(signal.SIGTERM, stop_children)
    start = time.time()
    while any(proc.poll() is None for _, proc, _ in procs.values()):
        time.sleep(args.poll_seconds)
        progress = {}
        for key, (spec, _, _) in procs.items():
            epoch = last_epoch(spec.log)
            pipeline.report["runs"][key]["epoch"] = epoch
            progress[f"progress/{key}"] = epoch / args.num_epochs
        progress["progress/minutes"] = (time.time() - start) / 60
        pipeline.log(progress)
        pipeline.save()
    failed = []
    for key, (spec, proc, stream) in procs.items():
        stream.close()
        record = pipeline.report["runs"][key]
        record["exit_code"] = proc.returncode
        record["epoch"] = run_epoch(spec)
        if proc.returncode == 0 and (spec.out_dir / "train_summary.json").is_file():
            record["status"] = "done"
        else:
            record["status"] = "failed"
            record["tail"] = tail_text(spec.log, 30)
            failed.append(key)
    detail["minutes"] = round((time.time() - start) / 60, 1)
    detail["failed"] = failed
    if failed:
        raise StageFailed(f"runs failed: {', '.join(failed)}")
    return specs


def publish_files(runs_root: Path) -> list[str]:
    """Paths under runs_root that are published (see PUBLISH_FILE)."""
    return sorted(
        name
        for path in runs_root.rglob("*")
        if path.is_file()
        and PUBLISH_FILE.fullmatch(name := path.relative_to(runs_root).as_posix())
    )


def scan_runs(args: JobArgs, runs_root: Path) -> dict[str, dict]:
    """Run status from disk, for publish jobs that did not train."""
    runs = {}
    for spec in plan_runs(args, runs_root, num_gpus=1):
        runs[f"{spec.task}-seed{spec.seed}"] = {
            "status": "done" if spec.action == "done" else "incomplete",
            "epoch": run_epoch(spec),
        }
    return runs


def write_manifest(runs_root: Path, pipeline: Pipeline) -> dict[str, str]:
    """SHA-256 of every published file (manifest.json included), by path."""
    files = {name: sha256_file(runs_root / name) for name in publish_files(runs_root)}
    manifest = {
        "tag": pipeline.args.tag,
        "dataset": {"repo": DATA_REPO, "revision": DATA_REVISION},
        "runs": pipeline.report["runs"],
        "files": files,
    }
    (runs_root / "manifest.json").write_text(json.dumps(manifest, indent=2))
    files["manifest.json"] = sha256_file(runs_root / "manifest.json")
    return files


def stage_publish(args: JobArgs, pipeline: Pipeline, runs_root: Path, detail: dict):
    files = write_manifest(runs_root, pipeline)
    exports = sorted({str(Path(name).parent) for name in files if "/epoch" in name})
    detail.update(files=len(files), exports=exports)
    detail["bytes"] = sum((runs_root / name).stat().st_size for name in files)
    if not exports:
        raise StageFailed("no EMA exports to publish")
    prefix = f"planner/{args.tag}"
    if args.upload != "hf":
        detail["_status"] = "skipped" if args.upload == "none" else "dryrun"
        detail["target"] = f"{args.upload_repo}/{prefix}"
        return
    from huggingface_hub import HfApi

    api = HfApi()
    commit = hub.with_retries(
        lambda: api.upload_folder(
            folder_path=str(runs_root),
            path_in_repo=prefix,
            repo_id=args.upload_repo,
            repo_type="model",
            allow_patterns=sorted(files),
            commit_message=f"DP3 planner {args.tag} (AMD MI355X)",
        ),
        f"upload {args.upload_repo}/{prefix}",
    )
    sha = getattr(commit, "oid", None) or str(commit).rsplit("/", 1)[-1]
    detail["commit"] = sha
    remote = {
        entry.path: remote_digest(entry)
        for entry in hub.with_retries(
            lambda: list(
                api.list_repo_tree(
                    args.upload_repo,
                    path_in_repo=prefix,
                    recursive=True,
                    expand=True,
                    revision=sha,
                )
            ),
            "list_repo_tree",
        )
    }
    mismatched = []
    for name, local_sha in files.items():
        size, lfs_sha = remote.get(f"{prefix}/{name}", (None, None))
        if size != (runs_root / name).stat().st_size:
            mismatched.append(name)
        elif lfs_sha is not None and lfs_sha != local_sha:
            mismatched.append(name)
        elif lfs_sha is None:
            from huggingface_hub import hf_hub_download

            copy = hub.with_retries(
                lambda name=name: hf_hub_download(
                    args.upload_repo, f"{prefix}/{name}", revision=sha
                ),
                f"verify {name}",
            )
            if sha256_file(Path(copy)) != local_sha:
                mismatched.append(name)
    detail["verified_files"] = len(files) - len(mismatched)
    detail["url"] = f"https://huggingface.co/{args.upload_repo}/tree/{sha}/{prefix}"
    if mismatched:
        raise StageFailed(f"uploaded files differ: {mismatched[:5]}")
    print(f"[cluster] published {len(files)} files: {detail['url']}", flush=True)


def upload_report(args: JobArgs, runs_root: Path) -> None:
    """Best effort: the final job report next to the published runs."""
    from huggingface_hub import HfApi

    try:
        hub.with_retries(
            lambda: HfApi().upload_file(
                path_or_fileobj=str(runs_root / "job_report.json"),
                path_in_repo=f"planner/{args.tag}/job_report.json",
                repo_id=args.upload_repo,
                repo_type="model",
                commit_message=f"DP3 planner {args.tag} job report",
            ),
            "upload job_report.json",
        )
    except Exception as exc:
        print(f"[cluster] job report not uploaded: {exc}", flush=True)


def run_pipeline(args: JobArgs, mode: str) -> int:
    runs_root = args.work / "runs" / args.tag
    runs_root.mkdir(parents=True, exist_ok=True)
    args.scratch.mkdir(parents=True, exist_ok=True)
    (runs_root / "logs").mkdir(exist_ok=True)
    pipeline = Pipeline(args, runs_root, mode)
    status = "failed"
    try:
        with pipeline.stage("environment") as detail:
            num_gpus = stage_environment(args, detail, need_gpu=mode == "run")
        with pipeline.stage("credentials") as detail:
            stage_credentials(args, pipeline, detail)
        train_error = None
        if mode == "run":
            with pipeline.stage("data") as detail:
                data = stage_data(args, detail)
            if args.run_tests:
                with pipeline.stage("tests") as detail:
                    stage_tests(detail, runs_root / "logs" / "tests.log")
            with pipeline.stage("preflight") as detail:
                log = runs_root / "logs" / "preflight.log"
                stage_preflight(args, data, detail, log)
            try:
                with pipeline.stage("train") as detail:
                    stage_train(args, pipeline, runs_root, num_gpus, detail)
            except StageFailed as exc:
                # Publish whatever finished; the job still exits non-zero.
                train_error = exc
        else:
            pipeline.report["runs"] = scan_runs(args, runs_root)
        with pipeline.stage("publish") as detail:
            stage_publish(args, pipeline, runs_root, detail)
        status = "failed" if train_error else "passed"
    except (Exception, KeyboardInterrupt) as exc:
        print(f"[cluster] FAILED: {type(exc).__name__}: {exc}", flush=True)
        status = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
    finally:
        pipeline.finish(status)
        published = pipeline.report["stages"].get("publish", {}).get("status")
        if args.upload == "hf" and published == "passed":
            upload_report(args, runs_root)
        print(f"[cluster] {mode} {status}; report {pipeline.report_path}", flush=True)
    return 0 if status == "passed" else 1


def main() -> None:
    commands = {"run": JobArgs, "publish": JobArgs}
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in commands:
        raise SystemExit("usage: python -m leg_manip.planner.cluster {run|publish} ...")
    args = tyro.cli(JobArgs, args=sys.argv[2:], prog=f"cluster {mode}")
    if args.upload not in ("hf", "dryrun", "none"):
        raise SystemExit("--upload must be hf, dryrun or none")
    unknown = set(args.tasks) - set(DATASETS)
    if unknown:
        raise SystemExit(f"unknown tasks: {sorted(unknown)}")
    sys.exit(run_pipeline(args, mode))


if __name__ == "__main__":
    main()
