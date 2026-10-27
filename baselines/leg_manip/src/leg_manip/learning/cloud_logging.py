"""Controller metrics and checkpoints in W&B and the selected HF repository."""

from __future__ import annotations

import hashlib
import json
import warnings
from dataclasses import asdict, is_dataclass
from pathlib import Path

import wandb
from huggingface_hub import HfApi
from rsl_rl.utils.log_writer import LogWriter
from torch.utils.tensorboard import SummaryWriter


class CloudLogWriter(SummaryWriter, LogWriter):
    """Keep TensorBoard locally and publish each saved checkpoint to both services.

    HF failures leave a local pending receipt and are retried on the next save
    and at shutdown. A run cannot finish successfully while uploads are pending.
    Credentials are read by the SDKs, never stored in the receipt or config.
    """

    def __init__(
        self,
        log_dir: str,
        project_name: str,
        entity: str | None,
        run_name: str,
        hf_repo: str | None = None,
        metadata_dir: str | None = None,
        tags: tuple[str, ...] = (),
    ) -> None:
        if not run_name.startswith("leg-manip-") or "/" in run_name or "\\" in run_name:
            raise ValueError(
                "run_name must start with leg-manip- and contain no slashes"
            )
        self.root = Path(log_dir)
        self.hf_repo = hf_repo
        self.hf_prefix = f"controller/{run_name}"
        self.metadata_dir = Path(metadata_dir) if metadata_dir else None
        self.api = HfApi() if hf_repo else None
        if self.api is not None:
            self.api.auth_check(hf_repo, repo_type="model", write=True)
        super().__init__(log_dir=log_dir, flush_secs=10)
        try:
            # W&B 0.31 removed Settings(start_method=...). Use supported defaults.
            self.run = wandb.init(
                project=project_name,
                entity=entity,
                name=run_name,
                group="leg-manip-controller",
                tags=list(dict.fromkeys(("leg-manip", "go2", "controller", *tags))),
                config={"hf_repo": hf_repo, "hf_prefix": self.hf_prefix},
                dir=str(self.root),
                resume="never",
            )
        except Exception:
            self.close()
            raise
        self.pending: dict[str, Path] = {}
        self.uploaded: dict[str, dict[str, str]] = {}
        self.errors: dict[str, str] = {}
        self.videos: set[str] = set()
        (self.root / "wandb-run.json").write_text(
            json.dumps(
                {"id": self.run.id, "url": self.run.url, "name": run_name}, indent=2
            )
        )
        self._receipt()

    def add_scalar(
        self, tag, scalar_value, global_step=None, walltime=None, new_style=False
    ) -> None:
        super().add_scalar(tag, scalar_value, global_step, walltime, new_style)
        # RSL also emits these with elapsed seconds as their step. Mixing that
        # axis with iteration steps makes W&B discard later training metrics.
        if tag in ("Train/mean_reward/time", "Train/mean_episode_length/time"):
            return
        self.run.log({tag: scalar_value}, step=global_step)

    def store_config(self, env_cfg, train_cfg) -> None:
        env_config = asdict(env_cfg) if is_dataclass(env_cfg) else env_cfg
        self.run.config.update(
            json.loads(
                json.dumps({"env_cfg": env_config, "train_cfg": train_cfg}, default=str)
            )
        )
        for path in sorted((self.root / "params").glob("*.yaml")):
            self._record_file(path, f"params/{path.name}")
        if self.metadata_dir:
            for name in ("run.json", "source-manifest.json", "source.tar.gz"):
                path = self.metadata_dir / name
                if path.is_file():
                    self._record_file(path, f"provenance/{name}")
        self._sync_hf()

    def _record_file(self, path: Path, relative: str) -> None:
        self.run.save(str(path), base_path=str(path.parent), policy="now")
        if self.api is not None:
            self.pending[relative] = path

    def save_model(self, model_path: str, it: int) -> None:
        path = Path(model_path)
        self._record_file(path, path.name)
        self.run.summary["checkpoint_iteration"] = it
        self._sync_hf()

    def save_file(self, path: str) -> None:
        file = Path(path)
        self._record_file(file, f"provenance/{file.name}")
        self._sync_hf()

    def save_video(self, video: Path, it: int) -> None:
        if str(video) not in self.videos:
            self.run.log({"video": wandb.Video(str(video), format="mp4")}, step=it)
            self.videos.add(str(video))

    def _sync_hf(self) -> None:
        for relative, path in list(self.pending.items()):
            try:
                info = self.api.upload_file(
                    path_or_fileobj=str(path),
                    path_in_repo=f"{self.hf_prefix}/{relative}",
                    repo_id=self.hf_repo,
                    repo_type="model",
                    commit_message=f"Upload {self.hf_prefix}/{relative}",
                )
                self.uploaded[relative] = {
                    "commit": info.oid,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
                del self.pending[relative]
                self.errors.pop(relative, None)
                self.run.summary["hf_last_commit"] = info.oid
            except Exception as exc:
                self.errors[relative] = type(exc).__name__
                warnings.warn(
                    f"HF upload pending for {relative}: {type(exc).__name__}",
                    stacklevel=2,
                )
        self._receipt()

    def _receipt(self) -> None:
        status = {
            "repo": self.hf_repo,
            "prefix": self.hf_prefix,
            "pending": sorted(self.pending),
            "uploaded": self.uploaded,
            "errors": self.errors,
            "wandb_url": self.run.url,
        }
        temporary = self.root / "upload-status.json.tmp"
        temporary.write_text(json.dumps(status, indent=2))
        temporary.replace(self.root / "upload-status.json")

    def stop(self) -> None:
        self._sync_hf()
        failed = bool(self.pending)
        self.flush()
        try:
            self.run.finish(exit_code=1 if failed else 0)
        finally:
            self.close()
        if failed:
            raise RuntimeError("HF uploads remain pending; see upload-status.json")
