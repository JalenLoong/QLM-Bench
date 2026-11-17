"""QLM-Bench demonstrations: the release catalogue and a reader for the LeRobot v2.1 canonical releases.

The catalogue (``spec/catalog.json``) lists the ten MuJoCo releases (100 demonstrations each, 80/10/10
train/validation/test). ``download_demonstrations`` fetches them from the Hugging Face dataset.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path, PurePosixPath
import re
from qlm_bench.config import dataset_repo_id


def safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("A nonempty portable path is required")
    p = PurePosixPath(value)
    if p.is_absolute() or not p.parts or ".." in p.parts or str(p) != value:
        raise ValueError(f"Unsafe portable path: {value}")
    return value


def under(root, relative):
    root = Path(root).resolve()
    path = root / safe_relative(relative)
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Path escapes resource root: {relative}")
    return path


@dataclass(frozen=True)
class DatasetRef:
    repo_id: str
    revision: str
    release: str
    canonical_root: str
    schema: str
    manifest: str
    manifest_sha256: str

    def __post_init__(self):
        if "/" in safe_relative(self.release):
            raise ValueError("Release identity must be one component")
        if self.canonical_root != f"canonical/lerobot_v2_1/{self.release}":
            raise ValueError("Canonical root does not match release identity")
        if self.manifest != f"releases/{self.release}/manifest.json":
            raise ValueError("Release manifest identity does not match release")
        safe_relative(self.canonical_root)
        safe_relative(self.manifest)
        if self.schema != "wam-quadruped-v2.1.0":
            raise ValueError("Unsupported dataset schema")

    @classmethod
    def from_dict(cls, value):
        return cls(**{k: value[k] for k in cls.__dataclass_fields__})

    @property
    def hub_repo_id(self):
        """Download address; the catalogue writes ``@DATASET_REPO@`` and the site configuration fills it in."""
        return dataset_repo_id(None if self.repo_id == "@DATASET_REPO@" else self.repo_id)

    def to_dict(self):
        return asdict(self)


def load_catalog(path=None):
    path = Path(path) if path is not None else Path(__file__).with_name("spec") / "catalog.json"
    catalog = json.loads(path.read_text())
    if catalog.get("schema") != "qlm-catalog-v1":
        raise ValueError("Unsupported catalogue schema")
    entries = catalog["demonstrations"]
    refs = [DatasetRef.from_dict(e["ref"]) for e in entries]
    if len({r.release for r in refs}) != len(refs):
        raise ValueError("Duplicate demonstration release")
    return catalog


def resolve_release(release, catalog=None):
    catalog = load_catalog() if catalog is None else catalog
    matches = [e for e in catalog["demonstrations"] if e["ref"]["release"] == release]
    if len(matches) != 1:
        raise ValueError(f"Release must appear exactly once: {release}")
    return DatasetRef.from_dict(matches[0]["ref"])


class CanonicalDataset:
    """Read one release in a local snapshot with the Hugging Face dataset layout.

    Row reads need the ``data`` extra (pyarrow); metadata inspection uses only the stdlib.
    """
    def __init__(self, ref: DatasetRef, snapshot_root):
        self.ref = ref
        self.snapshot_root = Path(snapshot_root).resolve()
        self.root = under(self.snapshot_root, ref.canonical_root)
        manifest_path = under(self.snapshot_root, ref.manifest)
        self.manifest = json.loads(manifest_path.read_text())
        self.contract = json.loads((self.root / "meta/contract.json").read_text())
        self.info = json.loads((self.root / "meta/info.json").read_text())
        self.split = json.loads((self.root / "meta/split.json").read_text())["episodes"]
        if (self.manifest["release"] != ref.release or self.manifest["canonical_root"] != ref.canonical_root
                or self.manifest["dataset_schema_version"] != ref.schema
                or self.contract["dataset_schema_version"] != ref.schema):
            raise ValueError("Local snapshot release/schema differs from the catalogue entry")
        self._episodes = {e["episode_uid"]: e for e in self.contract["episodes"]}
        uids = [e["episode_uid"] for e in self.contract["episodes"]]
        if len(self._episodes) != len(uids) or set(uids) != {e["episode_uid"] for e in self.manifest["episodes"]}:
            raise ValueError("Episode membership differs between contract and manifest")
        split_uids = [uid for values in self.split.values() for uid in values]
        if len(set(split_uids)) != len(split_uids) or set(split_uids) != set(uids) or self.split != self.manifest["split"]:
            raise ValueError("Episode split mismatch")

    def episodes(self, split=None):
        if split is None:
            return list(self._episodes.values())
        return [self._episodes[uid] for uid in self.split[split]]

    def rows(self, episode_uid, columns=None):
        from pyarrow import parquet
        episode = self._episodes[episode_uid]
        index = episode["episode_index"]
        relative = self.info["data_path"].format(episode_chunk=index // self.info["chunks_size"], episode_index=index)
        return parquet.read_table(under(self.root, relative), columns=columns)

    def terminal(self, episode_uid):
        return self._episodes[episode_uid]["terminal"]

    def validate(self, *, check_media=False, tools=None):
        from qlm_bench.data.lerobot.validation import validate_canonical
        return validate_canonical(self.root, check_media=check_media, tools=tools)


def download_demonstrations(local_dir, *, releases=None, repo_id=None, revision=None, include_physical=False):
    """Download canonical releases (default: all ten) into ``local_dir`` with the Hugging Face layout."""
    from huggingface_hub import snapshot_download
    from qlm_bench.config import dataset_revision
    catalog = load_catalog()
    refs = [DatasetRef.from_dict(e['ref']) for e in catalog['demonstrations']]
    if releases is not None:
        refs = [r for r in refs if r.release in set(releases)]
    patterns = [p for r in refs for p in (r.canonical_root + '/**', r.manifest)]
    if include_physical:
        patterns += [f'physical/v1/*/{r.release}/**' for r in refs]
    return snapshot_download(dataset_repo_id(repo_id), repo_type='dataset',
                             revision=dataset_revision(revision), local_dir=str(local_dir), allow_patterns=patterns)
