"""CPU regressions for recoverable, isolated planner training jobs."""

import dataclasses
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import torch
import zarr

from leg_manip.demo_io import write_zarr
from leg_manip.planner import train
from leg_manip.planner.dataset import DemoDataset
from leg_manip.planner.dp3 import EMAModel, LinearNormalizer
from leg_manip.planner.model import PlannerModelCfg, build_policy, load_checkpoint


@pytest.fixture
def training_args(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    rng = np.random.default_rng(4)
    episodes = []
    for e in range(3):
        action = np.zeros((6, 31), dtype=np.float32)
        action[:, 0] = e % 2
        action[:, 1:19] = rng.normal(0, 0.1, (6, 18))
        action[:, 27] = action[:, 30] = -1
        episodes.append(
            {
                "point_cloud": rng.normal(size=(6, 8, 3)).astype(np.float32),
                "state": rng.normal(size=(6, 17)).astype(np.float32),
                "action": action,
            }
        )
    path = tmp_path / "demo.zarr"
    write_zarr(path, episodes, {"task": "unit"})
    # The only external integration is disabled; model/optimizer/I/O stay real.
    run = SimpleNamespace(log=lambda *a, **kw: None, finish=lambda: None)
    monkeypatch.setitem(sys.modules, "wandb", SimpleNamespace(init=lambda **kw: run))
    return train.TrainArgs(
        data=path,
        out_root=tmp_path / "runs",
        device="cpu",
        seed=3,
        model=PlannerModelCfg(down_dims=(8, 16, 32), num_inference_steps=2),
        batch_size=4,
        num_epochs=4,
        warmup_steps=1,
        val_ratio=0.34,
        val_every=1,
        checkpoint_fractions=(0.5, 1.0),
        wandb_mode="disabled",
    )


def _run(args, monkeypatch):
    monkeypatch.setattr(train.tyro, "cli", lambda _: args)
    train.main()


def _run_dir(args):
    return args.out_root / "unit" / f"seed{args.seed}"


def _equal_tree(left, right):
    if isinstance(left, torch.Tensor):
        torch.testing.assert_close(left, right, rtol=0, atol=0)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            _equal_tree(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            _equal_tree(a, b)
    else:
        assert left == right


def test_existing_run_directory_is_never_reused_implicitly(training_args, monkeypatch):
    root = _run_dir(training_args)
    root.mkdir(parents=True)
    marker = root / "existing.txt"
    marker.write_text("keep")
    with pytest.raises(FileExistsError, match="resume|exist"):
        _run(training_args, monkeypatch)
    assert list(root.iterdir()) == [marker]


def test_resume_matches_uninterrupted_training(training_args, monkeypatch):
    _run(training_args, monkeypatch)
    complete_path = _run_dir(training_args) / "latest.pt"
    assert complete_path.exists(), "Full resumable training state was not saved"
    complete = torch.load(complete_path, weights_only=True)

    interrupted = dataclasses.replace(
        training_args, out_root=training_args.out_root.parent / "interrupted"
    )

    def interrupt(log, step):
        if log["epoch"] == 2:
            raise InterruptedError("simulated preemption")

    run = SimpleNamespace(log=interrupt, finish=lambda: None)
    monkeypatch.setitem(sys.modules, "wandb", SimpleNamespace(init=lambda **kw: run))
    with pytest.raises(InterruptedError, match="preemption"):
        _run(interrupted, monkeypatch)
    latest = _run_dir(interrupted) / "latest.pt"
    saved = torch.load(latest, weights_only=True)
    assert saved["epoch"] == 2
    assert saved["step"] == saved["ema"]["optimization_step"] == 4
    assert saved["optimizer"]["state"]
    assert saved["rng"]["cpu"].dtype == torch.uint8
    assert "device" in saved["rng"]
    assert (_run_dir(interrupted) / "training_epoch0002.pt").exists()

    # Deliberately disturb RNG; resume must restore it after initialization.
    torch.manual_seed(99)
    run.log = lambda *a, **kw: None
    resumed = dataclasses.replace(interrupted, resume=latest)
    _run(resumed, monkeypatch)
    final = torch.load(latest, weights_only=True)
    for key in (
        "policy",
        "ema_policy",
        "ema",
        "optimizer",
        "scheduler",
        "epoch",
        "step",
        "rng",
    ):
        _equal_tree(complete[key], final[key])
    policy, meta = load_checkpoint(_run_dir(resumed) / "epoch0004", device="cpu")
    _equal_tree(policy.state_dict(), final["ema_policy"])
    assert meta["info"]["epoch"] == 4
    assert final["epoch"] == 4
    # Resuming an already completed run does not advance or overwrite its state.
    original_bytes = latest.read_bytes()
    _run(resumed, monkeypatch)
    assert latest.read_bytes() == original_bytes


@pytest.mark.parametrize("change", ["lr", "num_epochs", "seed", "model", "data"])
def test_resume_rejects_incompatible_inputs(training_args, monkeypatch, change):
    _run(training_args, monkeypatch)
    latest = _run_dir(training_args) / "latest.pt"
    assert latest.exists(), "Full resumable training state was not saved"
    before = latest.read_bytes()
    resumed = dataclasses.replace(training_args, resume=latest)
    if change == "data":
        root = zarr.open_group(str(resumed.data), mode="a")
        root["data"]["action"][0, 1] += 0.1
    elif change == "model":
        resumed.model = dataclasses.replace(resumed.model, encoder_output_dim=128)
    else:
        setattr(resumed, change, getattr(resumed, change) + 1)
    with pytest.raises(ValueError, match="resume|compatible"):
        _run(resumed, monkeypatch)
    assert latest.read_bytes() == before


def test_atomic_state_save_preserves_previous_checkpoint(tmp_path, monkeypatch):
    assert hasattr(train, "save_training_state"), "Atomic training-state save missing"
    path = tmp_path / "latest.pt"
    train.save_training_state(path, {"epoch": 1, "tensor": torch.ones(2)})
    original = path.read_bytes()

    def failed_save(state, stream):
        stream.write(b"incomplete checkpoint")
        raise OSError("disk full")

    monkeypatch.setattr(torch, "save", failed_save)
    with pytest.raises(OSError, match="disk full"):
        train.save_training_state(path, {"epoch": 2})
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


def test_task_seed_outputs_are_independent(training_args, monkeypatch):
    _run(training_args, monkeypatch)
    first = _run_dir(training_args) / "latest.pt"
    assert first.exists(), "Full resumable training state was not saved"
    original = first.read_bytes()
    second = dataclasses.replace(training_args, seed=4)
    _run(second, monkeypatch)
    assert (_run_dir(second) / "latest.pt").exists()
    root = zarr.open_group(str(training_args.data), mode="a")
    root.attrs["task"] = "another_task"
    _run(training_args, monkeypatch)
    assert (training_args.out_root / "another_task" / "seed3" / "latest.pt").exists()
    assert first.read_bytes() == original


def test_latest_is_saved_between_fixed_fractions(training_args, monkeypatch):
    args = dataclasses.replace(
        training_args, checkpoint_every=1, checkpoint_fractions=(1.0,)
    )

    def interrupt(log, step):
        if log["epoch"] == 1:
            raise InterruptedError("preemption")

    run = SimpleNamespace(log=interrupt, finish=lambda: None)
    monkeypatch.setitem(sys.modules, "wandb", SimpleNamespace(init=lambda **kw: run))
    with pytest.raises(InterruptedError):
        _run(args, monkeypatch)
    state = torch.load(_run_dir(args) / "latest.pt", weights_only=True)
    assert state["epoch"] == 1
    assert not list(_run_dir(args).glob("training_epoch*.pt"))
    assert not list(_run_dir(args).glob("epoch*"))


def test_validation_preserves_ema_eval_mode(training_args):
    ds = DemoDataset(training_args.data, 4, 2, 1, device="cpu")
    policy = build_policy(training_args.model, ds.shape_meta)
    normalizer = LinearNormalizer()
    normalizer.fit(ds.normalizer_data())
    policy.set_normalizer(normalizer)
    ema = EMAModel(policy)
    train.validate(ema.averaged_model, ds)
    assert not ema.averaged_model.training
    assert all(not p.requires_grad for p in ema.averaged_model.parameters())
