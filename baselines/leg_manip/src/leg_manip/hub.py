"""Hugging Face Hub transfer of datasets and planner checkpoints.

The NVIDIA machine and the AMD cluster never talk to each other directly: demos
go up as a dataset repo, planner checkpoints come back as a model repo. A zarr
directory (thousands of small files) is uploaded as a single ``.zarr.zip``.

    uv run lm-hub upload data/demos/press_button.zarr --repo <user>/legmanip-demos
    uv run lm-hub download --repo <user>/legmanip-demos --filename press_button.zarr.zip
    uv run lm-hub upload outputs/planner/press_button/seed0 \
        --repo <user>/legmanip-dp3 --repo-type model --path-in-repo press_button/seed0
    uv run lm-hub download-dir --repo <user>/legmanip-dp3 --pattern "press_button/*"
"""

from __future__ import annotations

import fcntl
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import tyro
from huggingface_hub import HfApi, hf_hub_download, snapshot_download

DEFAULT_CACHE = Path("data/hub")


def _zip_dir(src: Path, dst_zip: Path) -> None:
    with zipfile.ZipFile(dst_zip, "w", compression=zipfile.ZIP_STORED) as zf:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(src.parent))


def upload(
    local: Path,
    repo: str,
    repo_type: str = "dataset",
    path_in_repo: str | None = None,
    private: bool = True,
    message: str | None = None,
) -> str:
    """Upload a file or folder; ``*.zarr`` folders are zipped first.

    Returns the commit sha (record it in W&B for provenance).
    """
    api = HfApi()
    api.create_repo(repo, repo_type=repo_type, private=private, exist_ok=True)
    local = Path(local)
    if local.is_dir() and local.suffix == ".zarr":
        with tempfile.TemporaryDirectory() as tmp:
            zpath = Path(tmp) / f"{local.name}.zip"
            _zip_dir(local, zpath)
            info = api.upload_file(
                path_or_fileobj=str(zpath),
                path_in_repo=path_in_repo or zpath.name,
                repo_id=repo,
                repo_type=repo_type,
                commit_message=message or f"upload {zpath.name}",
            )
    elif local.is_dir():
        info = api.upload_folder(
            folder_path=str(local),
            path_in_repo=path_in_repo or local.name,
            repo_id=repo,
            repo_type=repo_type,
            commit_message=message or f"upload {local.name}",
        )
    else:
        info = api.upload_file(
            path_or_fileobj=str(local),
            path_in_repo=path_in_repo or local.name,
            repo_id=repo,
            repo_type=repo_type,
            commit_message=message or f"upload {local.name}",
        )
    sha = getattr(info, "oid", None) or str(info).rsplit("/", 1)[-1]
    print(f"uploaded {local} -> {repo} ({repo_type}) commit {sha}")
    return sha


def download(
    repo: str,
    filename: str,
    repo_type: str = "dataset",
    revision: str | None = None,
    out_dir: Path = DEFAULT_CACHE,
) -> tuple[Path, str]:
    """Download one file; ``*.zarr.zip`` is unpacked. Returns (path, commit sha)."""
    api = HfApi()
    sha = api.repo_info(repo, repo_type=repo_type, revision=revision).sha
    cached = Path(hf_hub_download(repo, filename, repo_type=repo_type, revision=sha))
    relative = PurePosixPath(filename)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Hub filename must be a repository-relative path")
    out_dir = Path(out_dir) / repo.replace("/", "__") / sha[:12]
    is_zarr = filename.endswith(".zarr.zip")
    target = out_dir / (relative.with_suffix("") if is_zarr else relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Cluster seeds share this cache. Never expose a partially extracted dataset.
    with (target.parent / f".{target.name}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        marker = target / ".legmanip-complete"
        if is_zarr:
            if marker.is_file() and marker.read_text() == sha:
                return target, sha
            with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
                with zipfile.ZipFile(cached) as zf:
                    members = [PurePosixPath(n) for n in zf.namelist()]
                    if any(n.is_absolute() or ".." in n.parts for n in members):
                        raise ValueError("Invalid path in Zarr archive")
                    roots = {n.parts[0] for n in members if n.parts}
                    if len(roots) != 1:
                        raise ValueError("Expected one Zarr directory in archive")
                    zf.extractall(tmp)
                extracted = Path(tmp) / roots.pop()
                if not (extracted / ".zgroup").is_file():
                    raise ValueError("Archive does not contain a Zarr v2 group")
                (extracted / ".legmanip-complete").write_text(sha)
                if target.exists():
                    shutil.rmtree(target)
                extracted.replace(target)
        elif not target.exists():
            with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
                copied = Path(tmp) / "download"
                shutil.copyfile(cached, copied)
                copied.replace(target)
    return target, sha


def download_dir(
    repo: str,
    pattern: str = "*",
    repo_type: str = "model",
    revision: str | None = None,
    out_dir: Path = DEFAULT_CACHE,
) -> tuple[Path, str]:
    """Download the files matching `pattern`. Returns (local root, commit sha)."""
    api = HfApi()
    sha = api.repo_info(repo, repo_type=repo_type, revision=revision).sha
    root = Path(out_dir) / repo.replace("/", "__") / sha[:12]
    snapshot_download(
        repo,
        repo_type=repo_type,
        revision=sha,
        allow_patterns=[pattern],
        local_dir=str(root),
    )
    return root, sha


@dataclass
class UploadCmd:
    local: Path
    repo: str
    repo_type: str = "dataset"
    path_in_repo: str | None = None
    public: bool = False


@dataclass
class DownloadCmd:
    repo: str
    filename: str
    repo_type: str = "dataset"
    revision: str | None = None
    out_dir: Path = DEFAULT_CACHE


@dataclass
class DownloadDirCmd:
    repo: str
    pattern: str = "*"
    repo_type: str = "model"
    revision: str | None = None
    out_dir: Path = DEFAULT_CACHE


def main() -> None:
    cmd = tyro.extras.subcommand_cli_from_dict(
        {"upload": UploadCmd, "download": DownloadCmd, "download-dir": DownloadDirCmd}
    )
    if isinstance(cmd, UploadCmd):
        upload(
            cmd.local, cmd.repo, cmd.repo_type, cmd.path_in_repo, private=not cmd.public
        )
    elif isinstance(cmd, DownloadCmd):
        path, sha = download(
            cmd.repo, cmd.filename, cmd.repo_type, cmd.revision, cmd.out_dir
        )
        print(f"{path} (commit {sha})")
    else:
        root, sha = download_dir(
            cmd.repo, cmd.pattern, cmd.repo_type, cmd.revision, cmd.out_dir
        )
        print(f"{root} (commit {sha})")


if __name__ == "__main__":
    main()
