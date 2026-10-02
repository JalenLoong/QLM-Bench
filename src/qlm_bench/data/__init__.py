"""Pinned release resolution and explicit Canonical reading; no recursive scan."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


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


def verify_canonical_payload(canonical_root, expected_inventory_sha256):
    """Bind local bytes to an independently pinned Canonical inventory digest.

    A mutable self-generated checksum JSON is insufficient: callers must supply
    the digest verified at their immutable dataset revision. Every file, including
    metadata/terminal media, must match and no unlisted payload is accepted.
    """
    if not isinstance(expected_inventory_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_inventory_sha256):
        raise ValueError("Independently pinned Canonical inventory SHA256 required")
    root = Path(canonical_root).resolve()
    inventory_path = under(root, "meta/checksums.json")
    if not inventory_path.is_file():
        raise ValueError("Canonical inventory is missing")
    contents = inventory_path.read_bytes()
    if hashlib.sha256(contents).hexdigest() != expected_inventory_sha256:
        raise ValueError("Canonical inventory does not match its immutable revision")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate Canonical inventory path")
            result[key] = value
        return result
    inventory = json.loads(contents, object_pairs_hook=pairs)
    if not isinstance(inventory, dict) or not inventory:
        raise ValueError("Nonempty Canonical file inventory required")
    for name, expected in inventory.items():
        safe_relative(name)
        if name == "meta/checksums.json" or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("Invalid Canonical payload hash declaration")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p != inventory_path}
    if actual != set(inventory):
        raise ValueError("Canonical payload membership differs from its immutable inventory")
    total = 0
    for name, expected in inventory.items():
        path = under(root, name)
        h = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                h.update(block)
        if h.hexdigest() != expected:
            raise ValueError(f"Canonical payload hash mismatch: {name}")
        total += path.stat().st_size
    return {"passed": True, "inventory_sha256": expected_inventory_sha256, "files": len(inventory), "bytes": total}


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
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repo_id):
            raise ValueError("Explicit Hub dataset repo_id required")
        if not re.fullmatch(r"[0-9a-f]{40}", self.revision):
            raise ValueError("Immutable 40-character Hub revision required; main is not accepted")
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
        if not re.fullmatch(r"[0-9a-f]{64}", self.manifest_sha256):
            raise ValueError("Explicit release manifest SHA256 required")

    @classmethod
    def from_dict(cls, value):
        return cls(**{k: value[k] for k in cls.__dataclass_fields__})

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
    """Read one explicit release in a Hub-layout local snapshot.

    The release manifest is verified independently of Canonical metadata. Offline
    row reads require the data extra; metadata inspection uses only the stdlib.
    """
    def __init__(self, ref: DatasetRef, snapshot_root):
        self.ref = ref
        self.snapshot_root = Path(snapshot_root).resolve()
        self.root = under(self.snapshot_root, ref.canonical_root)
        manifest_path = under(self.snapshot_root, ref.manifest)
        if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != ref.manifest_sha256:
            raise ValueError("Release manifest SHA256 mismatch")
        self.manifest = json.loads(manifest_path.read_text())
        self.contract = json.loads((self.root / "meta/contract.json").read_text())
        self.info = json.loads((self.root / "meta/info.json").read_text())
        self.split = json.loads((self.root / "meta/split.json").read_text())["episodes"]
        if (self.manifest["repo_id"] != ref.repo_id or self.manifest["release"] != ref.release or self.manifest["canonical_root"] != ref.canonical_root
                or self.manifest["dataset_schema_version"] != ref.schema
                or self.contract["dataset_schema_version"] != ref.schema):
            raise ValueError("Local snapshot release/schema mismatch")
        self._episodes = {e["episode_uid"]: e for e in self.contract["episodes"]}
        uids = [e["episode_uid"] for e in self.contract["episodes"]]
        if len(self._episodes) != len(uids) or set(uids) != {e["episode_uid"] for e in self.manifest["episodes"]}:
            raise ValueError("Episode identity/membership mismatch")
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
        from qlm_bench.compatibility.dataset_v2.validation import validate_canonical
        return validate_canonical(self.root, check_media=check_media, tools=tools)

    def verify_payload(self, expected_inventory_sha256):
        return verify_canonical_payload(self.root, expected_inventory_sha256)
