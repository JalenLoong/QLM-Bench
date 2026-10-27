import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from leg_manip.learning import cloud_logging as cloud


@pytest.fixture
def services(monkeypatch):
    run = SimpleNamespace(
        id="test-id",
        url="https://example.test/run",
        config={},
        summary={},
        log=Mock(),
        save=Mock(),
        finish=Mock(),
    )
    init = Mock(return_value=run)
    monkeypatch.setattr(cloud.wandb, "init", init)
    api = Mock()
    api.repo_info.return_value = SimpleNamespace(private=True)
    api.upload_file.return_value = SimpleNamespace(oid="commit-1")
    monkeypatch.setattr(cloud, "HfApi", Mock(return_value=api))
    return run, init, api


def _writer(tmp_path):
    return cloud.CloudLogWriter(
        str(tmp_path),
        project_name="WAM-Policy",
        entity="test-team",
        run_name="leg-manip-controller-go2-seed0-test",
        hf_repo="owner/weights",
    )


def test_init_uses_supported_settings_and_exact_name(tmp_path, services):
    run, init, api = services
    writer = _writer(tmp_path)
    kw = init.call_args.kwargs
    assert kw["name"] == "leg-manip-controller-go2-seed0-test"
    assert kw["project"] == "WAM-Policy" and kw["entity"] == "test-team"
    assert "settings" not in kw
    api.auth_check.assert_called_once_with(
        "owner/weights", repo_type="model", write=True
    )
    writer.add_scalar("Loss/value", 0.25, 3)
    run.log.assert_called_once_with({"Loss/value": 0.25}, step=3)
    writer.stop()
    assert list(tmp_path.glob("events.out.tfevents.*"))


def test_no_run_created_without_repo_write_access(tmp_path, services):
    _, init, api = services
    api.auth_check.side_effect = PermissionError("no permission")
    with pytest.raises(PermissionError):
        _writer(tmp_path)
    init.assert_not_called()


def test_user_selected_public_repo_is_allowed(tmp_path, services):
    _, init, api = services
    api.repo_info.return_value.private = False
    writer = _writer(tmp_path)
    init.assert_called_once()
    writer.stop()


def test_wallclock_series_does_not_change_wandb_iteration_step(tmp_path, services):
    run, _, _ = services
    writer = _writer(tmp_path)
    writer.add_scalar("Train/mean_reward", 1.0, 3)
    writer.add_scalar("Train/mean_reward/time", 1.0, 100)
    writer.add_scalar("Train/mean_episode_length/time", 2.0, 100)
    run.log.assert_called_once_with({"Train/mean_reward": 1.0}, step=3)
    writer.stop()


def test_checkpoint_sent_to_both_services_with_receipt(tmp_path, services):
    run, _, api = services
    p = tmp_path / "model_500.pt"
    p.write_bytes(b"checkpoint")
    writer = _writer(tmp_path)
    writer.save_model(str(p), 500)
    run.save.assert_called_once()
    kw = api.upload_file.call_args.kwargs
    assert kw["repo_type"] == "model" and kw["repo_id"] == "owner/weights"
    assert kw["path_in_repo"] == (
        "controller/leg-manip-controller-go2-seed0-test/model_500.pt"
    )
    receipt = json.loads((tmp_path / "upload-status.json").read_text())
    assert receipt["pending"] == []
    assert receipt["uploaded"]["model_500.pt"]["commit"] == "commit-1"
    assert len(receipt["uploaded"]["model_500.pt"]["sha256"]) == 64
    writer.stop()


def test_failed_upload_retried_and_never_reported_as_complete(tmp_path, services):
    _, _, api = services
    api.upload_file.side_effect = [OSError("offline"), SimpleNamespace(oid="retry")]
    p = tmp_path / "model_0.pt"
    p.write_bytes(b"checkpoint")
    writer = _writer(tmp_path)
    with pytest.warns(UserWarning):
        writer.save_model(str(p), 0)
    assert json.loads((tmp_path / "upload-status.json").read_text())["pending"]
    writer.stop()
    status = json.loads((tmp_path / "upload-status.json").read_text())
    assert status["pending"] == []
    assert status["uploaded"]["model_0.pt"]["commit"] == "retry"


def test_persistent_upload_failure_marks_wandb_failed(tmp_path, services):
    run, _, api = services
    api.upload_file.side_effect = OSError("offline")
    p = tmp_path / "model_500.pt"
    p.write_bytes(b"checkpoint")
    writer = _writer(tmp_path)
    with pytest.warns(UserWarning):
        writer.save_model(str(p), 500)
    with pytest.warns(UserWarning), pytest.raises(RuntimeError, match="HF"):
        writer.stop()
    run.finish.assert_called_once_with(exit_code=1)


def test_configuration_and_parameters_uploaded(tmp_path, services):
    run, _, api = services
    (tmp_path / "params").mkdir()
    (tmp_path / "params/agent.yaml").write_text("seed: 0\n")
    writer = _writer(tmp_path)
    writer.store_config({"step_dt": 0.02}, {"seed": 0})
    assert run.config["train_cfg"] == {"seed": 0}
    assert run.config["env_cfg"] == {"step_dt": 0.02}
    assert api.upload_file.call_args.kwargs["path_in_repo"].endswith(
        "params/agent.yaml"
    )
    writer.stop()


def test_runner_changes_only_logging(monkeypatch):
    from leg_manip.learning.runner import ControllerRunner, MjlabOnPolicyRunner

    captured = {}

    def capture(self, env, cfg, log_dir, device):
        captured.update(cfg)

    monkeypatch.setattr(MjlabOnPolicyRunner, "__init__", capture)
    monkeypatch.setenv("WANDB_ENTITY", "test-team")
    monkeypatch.setenv("LEG_MANIP_HF_REPO", "owner/weights")
    cfg = {
        "logger": "wandb",
        "wandb_project": "WAM-Policy",
        "run_name": "leg-manip-controller-go2-seed0-test",
        "seed": 0,
        "algorithm": {"learning_rate": 0.001},
    }
    ControllerRunner(None, cfg, "/tmp/log", "cpu")
    assert captured["logger"]["class_name"] == (
        "leg_manip.learning.cloud_logging:CloudLogWriter"
    )
    assert captured["logger"]["run_name"] == cfg["run_name"]
    assert captured["algorithm"] == {"learning_rate": 0.001}
    cfg["logger"] = "tensorboard"
    ControllerRunner(None, cfg, "/tmp/log", "cpu")
    assert captured["logger"] == "tensorboard"
