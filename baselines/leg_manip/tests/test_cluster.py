"""CPU checks of the AMD job driver: retries, permissions, run planning, publish set."""

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import tyro

from leg_manip import hub
from leg_manip.planner import cluster, train


def _http_error(status):
    error = RuntimeError(f"HTTP {status}")
    error.response = SimpleNamespace(status_code=status)
    return error


class ConnectError(Exception):
    """Same name as httpx.ConnectError."""


@pytest.mark.parametrize(
    ("exc", "transient"),
    [
        (_http_error(429), True),
        (_http_error(503), True),
        (_http_error(404), False),
        (_http_error(403), False),
        (ConnectError("refused"), True),
        (TimeoutError(), True),
        (ValueError("bad input"), False),
    ],
)
def test_transient_errors_are_classified(exc, transient):
    assert hub.is_transient(exc) is transient


def test_retries_transient_errors_then_succeeds(monkeypatch):
    sleeps = []
    monkeypatch.setattr(hub.time, "sleep", sleeps.append)
    calls = iter([_http_error(502), ConnectError("reset"), "ok"])

    def call():
        value = next(calls)
        if isinstance(value, Exception):
            raise value
        return value

    assert hub.with_retries(call, "test") == "ok"
    assert sleeps == [hub.RETRY_BASE_DELAY, 2 * hub.RETRY_BASE_DELAY]


def test_permanent_errors_and_exhausted_retries_raise(monkeypatch):
    monkeypatch.setattr(hub.time, "sleep", lambda _: None)
    attempts = []

    def missing():
        attempts.append(1)
        raise _http_error(404)

    with pytest.raises(RuntimeError, match="404"):
        hub.with_retries(missing, "test")
    assert len(attempts) == 1

    def flaky():
        attempts.append(1)
        raise _http_error(500)

    attempts.clear()
    with pytest.raises(RuntimeError, match="500"):
        hub.with_retries(flaky, "test")
    assert len(attempts) == hub.RETRY_ATTEMPTS


WEIGHTS = "Ethan-Xu-Deng/legmanip-weights"


def _whoami(token, name="Ethan-Xu-Deng", orgs=()):
    return {
        "name": name,
        "orgs": [{"name": o} for o in orgs],
        "auth": {"accessToken": token},
    }


def _scoped(entity_type, entity_name, permissions):
    return {
        "role": "fineGrained",
        "fineGrained": {
            "scoped": [
                {
                    "entity": {"type": entity_type, "name": entity_name},
                    "permissions": permissions,
                }
            ]
        },
    }


@pytest.mark.parametrize(
    ("info", "allowed"),
    [
        (_whoami({"role": "write"}), True),
        (_whoami({"role": "write"}, name="someone-else"), False),
        (_whoami({"role": "write"}, name="other", orgs=("Ethan-Xu-Deng",)), True),
        (_whoami({"role": "read"}), False),
        (_whoami(_scoped("model", WEIGHTS, ["repo.write"])), True),
        (_whoami(_scoped("model", WEIGHTS, ["repo.content.read"])), False),
        (
            _whoami(_scoped("dataset", "Ethan-Xu-Deng/legmanip-demo", ["repo.write"])),
            False,
        ),
        (_whoami(_scoped("user", "Ethan-Xu-Deng", ["repo.write"])), True),
    ],
)
def test_hf_write_permission(info, allowed):
    assert cluster.hf_can_write(info, WEIGHTS) is allowed


def _args(tmp_path, **kw):
    return cluster.JobArgs(tag="t1", work=tmp_path, scratch=tmp_path / "s", **kw)


def test_runs_are_spread_over_gpus_and_resume_from_disk(tmp_path):
    args = _args(tmp_path)
    root = tmp_path / "runs" / "t1"
    done = root / "press_button" / "seed1"
    done.mkdir(parents=True)
    (done / "train_summary.json").write_text("{}")
    partial = root / "close_dishwasher" / "seed0"
    partial.mkdir(parents=True)
    (partial / "latest.pt").write_bytes(b"")
    specs = cluster.plan_runs(args, root, num_gpus=4)
    assert [(s.task, s.seed, s.gpu, s.action) for s in specs] == [
        ("press_button", 0, 0, "fresh"),
        ("press_button", 1, 1, "done"),
        ("press_button", 2, 2, "fresh"),
        ("close_dishwasher", 0, 3, "resume"),
        ("close_dishwasher", 1, 0, "fresh"),
        ("close_dishwasher", 2, 1, "fresh"),
    ]


def test_train_command_parses_as_train_args(tmp_path):
    args = _args(tmp_path, num_epochs=500, checkpoint_every=50)
    root = tmp_path / "runs" / "t1"
    spec = cluster.RunSpec(
        "close_dishwasher", 2, 5, root / "close_dishwasher" / "seed2", Path(), "resume"
    )
    cmd = cluster.train_command(args, spec, root)
    assert cmd[1:3] == ["-m", "leg_manip.planner.train"]
    parsed = tyro.cli(train.TrainArgs, args=cmd[3:])
    assert parsed.hf_repo == cluster.DATA_REPO
    assert parsed.hf_file == "close_dishwasher.zarr.zip"
    assert parsed.hf_revision == cluster.DATA_REVISION
    assert (parsed.seed, parsed.device, parsed.num_epochs) == (2, "cuda:5", 500)
    assert parsed.checkpoint_every == 50
    assert parsed.out_root == root
    assert parsed.resume == spec.out_dir / "latest.pt"
    assert parsed.wandb_entity == "junlinlong-the-university-of-sydney"
    assert parsed.wandb_project == "WAM-Policy"
    assert parsed.wandb_tags == ("dp3", "amd", "t1")
    # The model and schedule stay at the training defaults.
    assert parsed.model == train.TrainArgs().model
    assert parsed.checkpoint_fractions == (0.5, 0.75, 1.0)


def test_publish_set_is_exports_summaries_and_logs_only(tmp_path):
    root = tmp_path / "runs" / "t1"
    keep = [
        "press_button/seed0/epoch0250/model.safetensors",
        "press_button/seed0/epoch0250/config.json",
        "press_button/seed0/train_summary.json",
        "press_button/seed0/wandb_runs.jsonl",
        "logs/press_button-seed0.log",
    ]
    skip = [
        "press_button/seed0/latest.pt",
        "press_button/seed0/training_epoch0250.pt",
        "press_button/seed0/wandb/run-1/files/output.log",
        "press_button/seed0.failed-1/epoch0250/model.safetensors",
        "wandb/latest-run/logs/debug.log",
        "job_report.json",
    ]
    for name in keep + skip:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(name)
    assert cluster.publish_files(root) == sorted(keep)


def test_dryrun_publish_writes_manifest_without_network(tmp_path):
    args = _args(tmp_path, upload="dryrun")
    root = tmp_path / "runs" / "t1"
    export = root / "press_button" / "seed0" / "epoch0004" / "model.safetensors"
    export.parent.mkdir(parents=True)
    export.write_bytes(b"weights")
    pipeline = SimpleNamespace(args=args, report={"runs": {"press_button-seed0": {}}})
    detail = {}
    cluster.stage_publish(args, pipeline, root, detail)
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["dataset"]["revision"] == cluster.DATA_REVISION
    assert manifest["files"] == {
        "press_button/seed0/epoch0004/model.safetensors": cluster.sha256_file(export)
    }
    assert detail["_status"] == "dryrun"
    assert detail["exports"] == ["press_button/seed0/epoch0004"]
    assert detail["target"] == "Ethan-Xu-Deng/legmanip-weights/planner/t1"


def test_progress_is_read_from_the_training_log(tmp_path):
    log = tmp_path / "run.log"
    assert cluster.last_epoch(log) == 0
    log.write_text(
        "[planner] epoch 1/500 train/loss=0.1 (5s)\n"
        "noise\n[planner] epoch 230/500 train/loss=0.01 (900s)\n"
    )
    assert cluster.last_epoch(log) == 230


def test_known_datasets_match_the_published_revision():
    assert set(cluster.DATASETS) == {"press_button", "close_dishwasher"}
    for zip_sha, fingerprint in cluster.DATASETS.values():
        assert len(zip_sha) == len(fingerprint) == 64
    assert len(cluster.DATA_REVISION) == 40


def test_finished_runs_report_their_final_epoch(tmp_path):
    out = tmp_path / "press_button" / "seed0"
    out.mkdir(parents=True)
    log = tmp_path / "run.log"
    log.write_text("[planner] epoch 490/500 train/loss=0.01 (900s)\n")
    spec = cluster.RunSpec("press_button", 0, 0, out, log, "fresh")
    assert cluster.run_epoch(spec) == 490
    (out / "train_summary.json").write_text(json.dumps({"epochs": 500}))
    assert cluster.run_epoch(spec) == 500


@pytest.mark.parametrize(
    ("user", "problem"),
    [("dengxu1207", False), ("teammate", True), (None, False)],
)
def test_wandb_runs_must_be_logged_under_the_submitter(user, problem):
    message = cluster.wandb_user_problem(user, "dengxu1207")
    assert (message is not None) is problem
    assert cluster.wandb_user_problem("teammate", None) is None


AMD = Path(__file__).resolve().parents[1] / "scripts" / "amd"


def _bash(script, *args, env=None):
    return subprocess.run(
        ["bash", "-c", script, "bash", *args],
        capture_output=True,
        text=True,
        env={"PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/tmp")}
        | (env or {}),
        check=False,
    )


def test_secrets_file_overrides_ambient_tokens_without_printing(tmp_path):
    secrets = tmp_path / "legmanip.env"
    secrets.write_text(
        "# submitter credentials\n"
        'export HF_TOKEN="hf_user_secret"\n'
        "WANDB_API_KEY=wandb_user_secret\n"
        "\n"
        "OTHER=ignored\n"
    )
    secrets.chmod(0o600)
    out = _bash(
        f'. {AMD / "load_secrets.sh"}; legmanip_load_secrets "$1" || exit 9; '
        'printf "%s|%s|%s|%s\\n" "$HF_TOKEN" "$WANDB_API_KEY" "${OTHER:-}" '
        '"$LEGMANIP_SECRET_KEYS"',
        str(secrets),
        env={"HF_TOKEN": "hf_team", "WANDB_API_KEY": "wandb_team"},
    )
    assert out.returncode == 0, out.stderr
    log, values = out.stdout.splitlines()
    assert values == "hf_user_secret|wandb_user_secret||HF_TOKEN WANDB_API_KEY"
    for value in ("hf_user_secret", "wandb_user_secret"):
        assert value not in log and value not in out.stderr


def test_secrets_file_readable_by_others_is_refused(tmp_path):
    secrets = tmp_path / "legmanip.env"
    secrets.write_text("HF_TOKEN=hf_user_secret\n")
    secrets.chmod(0o644)
    out = _bash(
        f'. {AMD / "load_secrets.sh"}; legmanip_load_secrets "$1"; '
        'echo "rc=$? token=${HF_TOKEN:-unset}"',
        str(secrets),
    )
    assert "rc=1 token=unset" in out.stdout
    assert "chmod 600" in out.stderr


def test_job_stops_before_setup_without_submitter_credentials(tmp_path):
    env_setup = tmp_path / "rocm.sh"
    env_setup.write_text("export PYTHONPATH=/elsewhere/site-packages\n")
    project = str(AMD.parents[1])
    out = _bash(
        f"bash {AMD / 'job.sh'} run",
        env={
            "LEGMANIP_PROJECT_DIR": project,
            "LEGMANIP_ENV_SETUP": str(env_setup),
            "LEGMANIP_WORK": str(tmp_path / "work"),
        },
    )
    assert out.returncode == 1
    assert "cleared PYTHONPATH" in out.stdout
    assert "FAILED at secrets" in out.stdout
    assert not (tmp_path / "work").exists()
