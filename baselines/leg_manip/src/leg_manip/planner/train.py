"""Part 4: train the DP3 planner on demonstrations (runs on NVIDIA or AMD/ROCm).

    uv run lm-train-planner --data data/demos/press_button.zarr --seed 0
    # or pull the dataset from a Hugging Face dataset repo first:
    uv run lm-train-planner --hf-repo <user>/legmanip-demos \
        --hf-file press_button.zarr.zip --seed 0

Saves EMA weights at fixed fractions of training (default 50 / 75 / 100 %) under
outputs/planner/<task>/seed<k>/epoch<E>/, to be evaluated in simulation on the
NVIDIA machine. Full training state is saved atomically to latest.pt every
checkpoint_every epochs, at those fractions, and at the final epoch. Fixed
fractions also retain training_epoch<E>.pt. No simulator is imported here.

Resume with the original data/model/training arguments plus
``--resume outputs/planner/<task>/seed<k>/latest.pt``. Resume continues at the
next epoch in the same run directory and original LR schedule; num_epochs is
the original total, not an additional epoch count. Dataset contents, split,
model, optimizer, validation cadence and backend must match. Logging settings
and checkpoint cadence may change. CPU and the selected CUDA/HIP device's torch
RNG states are restored. Inference-only EMA exports cannot resume training.
"""

from __future__ import annotations

import copy
import json
import math
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import torch
import tyro
from diffusers.optimization import get_scheduler

from leg_manip.planner.dataset import DemoDataset
from leg_manip.planner.dp3 import EMAModel, LinearNormalizer
from leg_manip.planner.model import PlannerModelCfg, build_policy, save_checkpoint

EMA_CONFIG = {
    "update_after_step": 0,
    "inv_gamma": 1.0,
    "power": 0.75,
    "min_value": 0.0,
    "max_value": 0.9999,
}


@dataclass
class TrainArgs:
    data: Path | None = None
    """Local zarr dataset."""
    hf_repo: str | None = None
    """Hugging Face dataset repo to download the dataset from."""
    hf_file: str | None = None
    hf_revision: str | None = None
    out_root: Path = Path("outputs/planner")
    resume: Path | None = None
    """Full training-state .pt file; repeat the original training arguments."""
    seed: int = 0
    device: str = "cuda"
    model: PlannerModelCfg = field(default_factory=PlannerModelCfg)
    batch_size: int = 128
    num_epochs: int = 500
    lr: float = 1e-4
    weight_decay: float = 1e-6
    warmup_steps: int = 500
    val_ratio: float = 0.04
    val_every: int = 10
    """Epochs between validation passes (loss and sampled-action error)."""
    checkpoint_fractions: tuple[float, ...] = (0.5, 0.75, 1.0)
    checkpoint_every: int = 10
    """Update latest.pt every this many completed epochs, also at fixed fractions."""
    wandb_project: str = "leg-manip"
    wandb_entity: str | None = None
    wandb_mode: str = "online"
    """online | offline | disabled"""
    wandb_group: str | None = None
    """Defaults to planner-<task>."""
    wandb_tags: tuple[str, ...] = ()
    run_name: str | None = None

    def validate(self) -> None:
        """Reject invalid schedules before creating a run or allocating a model."""
        self.model.validate()
        if (
            min(self.batch_size, self.num_epochs, self.val_every, self.checkpoint_every)
            < 1
        ):
            raise ValueError(
                "batch size, epochs and checkpoint/validation periods must be positive"
            )
        if self.warmup_steps < 0 or not math.isfinite(self.lr) or self.lr <= 0:
            raise ValueError("learning rate must be positive and warmup nonnegative")
        if not math.isfinite(self.weight_decay) or self.weight_decay < 0:
            raise ValueError("weight_decay must be finite and nonnegative")
        if any(not 0 < f <= 1 for f in self.checkpoint_fractions):
            raise ValueError("checkpoint fractions must be in (0, 1]")
        if torch.device(self.device).type not in ("cpu", "cuda"):
            raise ValueError("planner training supports CPU or one CUDA/HIP device")


def save_training_state(path: Path, state: dict) -> None:
    """Atomically replace one full checkpoint, keeping the old file on failure.

    Serialize to a sibling temporary file, flush/fsync it, then replace the
    destination. The payload uses tensors and plain containers, so resume uses
    torch.load(weights_only=True). This API does not export inference weights.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as stream:
            temporary = Path(stream.name)
            torch.save(state, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def training_signature(args: TrainArgs, ds: DemoDataset, task: str) -> dict:
    """Identity of the data and numerical training schedule required by resume."""
    fields = (
        "model",
        "seed",
        "batch_size",
        "num_epochs",
        "lr",
        "weight_decay",
        "warmup_steps",
        "val_ratio",
        "val_every",
        "checkpoint_fractions",
    )
    config = asdict(args)
    backend = "cpu"
    if torch.device(args.device).type == "cuda":
        backend = "hip" if torch.version.hip else "cuda"
    return {
        **{key: config[key] for key in fields},
        "ema": EMA_CONFIG,
        "dataset": ds.fingerprint,
        "shape_meta": ds.shape_meta,
        "task": task,
        "backend": backend,
    }


def load_training_state(
    path: Path, signature: dict, out_dir: Path, steps_per_epoch: int
) -> dict:
    """Load and validate a full epoch-boundary checkpoint before any output writes."""
    state = torch.load(path, map_location="cpu", weights_only=True)
    required = {
        "version",
        "signature",
        "run_dir",
        "policy",
        "ema_policy",
        "ema",
        "optimizer",
        "scheduler",
        "epoch",
        "step",
        "rng",
    }
    if (
        not isinstance(state, dict)
        or not required <= state.keys()
        or state["version"] != 1
    ):
        raise ValueError("Not a compatible full training checkpoint for resume")
    if state["signature"] != signature:
        raise ValueError("Incompatible resume dataset or training configuration")
    if state["run_dir"] != str(out_dir.resolve()) or not out_dir.is_dir():
        raise ValueError("Resume must use the original task/seed run directory")
    if (
        not 0 <= state["epoch"] <= signature["num_epochs"]
        or state["step"] != state["epoch"] * steps_per_epoch
        or state["ema"]["optimization_step"] != state["step"]
    ):
        raise ValueError("Inconsistent epoch/step/EMA counters in resume checkpoint")
    return state


def resolve_data(args: TrainArgs) -> tuple[Path, dict]:
    if args.data is not None:
        return args.data, {"source": str(args.data)}
    if args.hf_repo is None or args.hf_file is None:
        raise ValueError("Give --data, or --hf-repo and --hf-file.")
    from leg_manip.hub import download

    path, revision = download(
        args.hf_repo, args.hf_file, repo_type="dataset", revision=args.hf_revision
    )
    return path, {
        "hf_repo": args.hf_repo,
        "hf_file": args.hf_file,
        "hf_revision": revision,
    }


@torch.no_grad()
def validate(
    policy, ds: DemoDataset, max_batches: int = 4, batch_size: int = 128
) -> dict:
    if ds.val_index is None:
        return {}
    was_training = policy.training
    policy.eval()
    losses, errors = [], []
    o = ds.n_obs_steps
    for rows in ds.val_index.split(batch_size)[:max_batches]:
        batch = ds.batch(rows)
        loss, _ = policy.compute_loss(batch)
        losses.append(loss.item())
        pred = policy.predict_action(batch["obs"])["action"][:, 0]
        target = batch["action"][:, o - 1]
        errors.append((pred - target).abs().mean().item())
    policy.train(was_training)
    return {
        "val/loss": sum(losses) / len(losses),
        "val/action_mae": sum(errors) / len(errors),
    }


def write_summary(
    out_dir: Path, task: str, args: TrainArgs, step: int, seconds: float | None
) -> None:
    """Completion marker read by the AMD job driver; seconds is None if unknown."""
    save_epochs = sorted(
        {max(1, round(f * args.num_epochs)) for f in args.checkpoint_fractions}
    )
    summary = {
        "task": task,
        "epochs": args.num_epochs,
        "steps": step,
        "seconds": seconds,
        "saved_epochs": save_epochs,
    }
    (out_dir / "train_summary.json").write_text(json.dumps(summary, indent=2))


def runtime_info(device: str) -> dict:
    """Torch build and accelerator identity, logged to show where a run trained."""
    info = {
        "torch": torch.__version__,
        "hip": torch.version.hip,
        "cuda": torch.version.cuda,
        "device": device,
    }
    if torch.device(device).type == "cuda":
        info["device_name"] = torch.cuda.get_device_name(device)
    return info


def main() -> None:
    args = tyro.cli(TrainArgs)
    args.validate()
    torch.manual_seed(args.seed)
    device = torch.device(args.device)
    if device.type == "cuda":
        if device.index is not None:
            # Keep the implicit current device (and its context) on this GPU when
            # several runs share one job.
            torch.cuda.set_device(device)
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    data_path, data_info = resolve_data(args)
    m = args.model
    ds = DemoDataset(
        data_path,
        m.horizon,
        m.n_obs_steps,
        m.n_action_steps,
        val_ratio=args.val_ratio,
        seed=args.seed,
        device=args.device,
    )
    task = ds.attrs.get("task", Path(data_path).stem.replace(".zarr", ""))
    if not isinstance(task, str) or task in ("", ".", "..") or Path(task).name != task:
        raise ValueError("Dataset task must be one nonempty directory name")
    out_dir = args.out_root / task / f"seed{args.seed}"
    steps_per_epoch = math.ceil(len(ds.train_index) / args.batch_size)
    signature = training_signature(args, ds, task)
    save_epochs = sorted(
        {max(1, round(f * args.num_epochs)) for f in args.checkpoint_fractions}
    )
    resume_state = None
    if args.resume is not None:
        resume_state = load_training_state(
            args.resume, signature, out_dir, steps_per_epoch
        )
        # Partial checkpoint writes left by a killed run (see save_training_state).
        for stale in out_dir.glob(".*.pt.*"):
            stale.unlink()
        if resume_state["epoch"] == args.num_epochs:
            print(f"[planner] run already complete: {out_dir}")
            if not (out_dir / "train_summary.json").is_file():
                write_summary(out_dir, task, args, resume_state["step"], None)
            return
    else:
        try:
            out_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise FileExistsError(
                f"Run directory exists: {out_dir}; use --resume or another --out-root"
            ) from exc
    print(
        f"[planner] task={task} episodes={ds.num_episodes} (val {ds.num_val_episodes}) "
        f"train samples={len(ds.train_index)} out={out_dir}"
    )

    policy = build_policy(m, ds.shape_meta)
    if resume_state is None:
        normalizer = LinearNormalizer()
        normalizer.fit(ds.normalizer_data(), last_n_dims=1, mode="limits")
        policy.set_normalizer(normalizer)
    else:
        policy.load_state_dict(resume_state["policy"])
    policy.to(args.device)
    ema_policy = copy.deepcopy(policy)
    if resume_state is not None:
        ema_policy.load_state_dict(resume_state["ema_policy"])
        ema_policy.to(args.device)
    ema = EMAModel(ema_policy, **EMA_CONFIG)

    total_steps = steps_per_epoch * args.num_epochs
    optimizer = torch.optim.AdamW(
        policy.parameters(),
        lr=args.lr,
        betas=(0.95, 0.999),
        eps=1e-8,
        weight_decay=args.weight_decay,
    )
    lr_sched = get_scheduler(
        "cosine",
        optimizer=optimizer,
        num_warmup_steps=args.warmup_steps,
        num_training_steps=total_steps,
    )
    start_epoch, step = 0, 0
    if resume_state is not None:
        optimizer.load_state_dict(resume_state["optimizer"])
        lr_sched.load_state_dict(resume_state["scheduler"])
        ema.optimization_step = resume_state["ema"]["optimization_step"]
        ema.decay = resume_state["ema"]["decay"]
        start_epoch, step = resume_state["epoch"], resume_state["step"]
    import wandb

    run = wandb.init(
        project=args.wandb_project,
        entity=args.wandb_entity,
        mode=args.wandb_mode,
        group=args.wandb_group or f"planner-{task}",
        tags=list(args.wandb_tags),
        name=args.run_name or f"planner-{task}-seed{args.seed}",
        config={
            "args": asdict(args),
            "data": data_info,
            "dataset_attrs": ds.attrs,
            "dataset_fingerprint": ds.fingerprint,
            "runtime": runtime_info(args.device),
        },
        dir=str(out_dir),
    )
    # One line per (re)start, so resumed runs keep the earlier W&B links.
    with (out_dir / "wandb_runs.jsonl").open("a") as stream:
        record = {
            "id": getattr(run, "id", None),
            "url": getattr(run, "url", None),
            "mode": args.wandb_mode,
            "start_epoch": start_epoch,
        }
        stream.write(json.dumps(record) + "\n")

    # Initialization may consume RNG. Restore only after all components/logging
    # are initialized so the next permutation and diffusion noise match exactly.
    if resume_state is not None:
        torch.set_rng_state(resume_state["rng"]["cpu"])
        if torch.device(args.device).type == "cuda":
            torch.cuda.set_rng_state(resume_state["rng"]["device"], args.device)
        del resume_state
    t0 = time.time()
    policy.train()
    for epoch in range(start_epoch + 1, args.num_epochs + 1):
        perm = ds.train_index[torch.randperm(len(ds.train_index), device=args.device)]
        epoch_loss = 0.0
        for rows in perm.split(args.batch_size):
            loss, _ = policy.compute_loss(ds.batch(rows))
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            lr_sched.step()
            ema.step(policy)
            epoch_loss += loss.item()
            step += 1
        log = {
            "train/loss": epoch_loss / steps_per_epoch,
            "train/lr": lr_sched.get_last_lr()[0],
            "epoch": epoch,
            "step": step,
        }
        if epoch % args.val_every == 0 or epoch in save_epochs:
            log.update(validate(ema_policy, ds, batch_size=args.batch_size))
        if epoch in save_epochs:
            ckpt = out_dir / f"epoch{epoch:04d}"
            info = {
                "task": task,
                "epoch": epoch,
                "step": step,
                "seed": args.seed,
                "data": data_info,
            }
            save_checkpoint(ckpt, ema_policy, m, ds.shape_meta, info)
            print(f"[planner] saved {ckpt}")
        if (
            epoch % args.checkpoint_every == 0
            or epoch in save_epochs
            or epoch == args.num_epochs
        ):
            state = {
                "version": 1,
                "signature": signature,
                "run_dir": str(out_dir.resolve()),
                "data": data_info,
                "policy": policy.state_dict(),
                "ema_policy": ema_policy.state_dict(),
                "ema": {"optimization_step": ema.optimization_step, "decay": ema.decay},
                "optimizer": optimizer.state_dict(),
                "scheduler": lr_sched.state_dict(),
                "epoch": epoch,
                "step": step,
                "rng": {
                    "cpu": torch.get_rng_state(),
                    "device": torch.cuda.get_rng_state(args.device)
                    if torch.device(args.device).type == "cuda"
                    else None,
                },
            }
            if epoch in save_epochs:
                save_training_state(out_dir / f"training_epoch{epoch:04d}.pt", state)
            save_training_state(out_dir / "latest.pt", state)
            del state
        run.log(log, step=step)
        if epoch % max(1, args.val_every) == 0 or epoch == 1:
            print(
                f"[planner] epoch {epoch}/{args.num_epochs} "
                + " ".join(
                    f"{k}={v:.4g}" for k, v in log.items() if isinstance(v, float)
                )
                + f" ({time.time() - t0:.0f}s)"
            )
    write_summary(out_dir, task, args, step, round(time.time() - t0, 1))
    run.finish()


if __name__ == "__main__":
    main()
