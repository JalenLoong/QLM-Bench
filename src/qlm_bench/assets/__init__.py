"""Hash-verified resources; no implicit download, geometry rebuild or weight mirror."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from qlm_bench.data import safe_relative, under


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_registry(path=None):
    root = Path(__file__).with_name("manifests")
    value = json.loads((Path(path) if path else root / "registry.json").read_text())
    if value.get("schema") != "qlm-resource-registry-v1":
        raise ValueError("Unsupported resource registry")
    ids = [r["asset_id"] for r in value["resources"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate asset IDs")
    return value


def load_manifest(asset_id, registry=None):
    registry = load_registry() if registry is None else registry
    rows = [r for r in registry["resources"] if r["asset_id"] == asset_id]
    if len(rows) != 1:
        raise ValueError(f"Resource must appear exactly once: {asset_id}")
    row = rows[0]
    path = under(Path(__file__).with_name("manifests"), row["manifest"])
    if sha256(path) != row["manifest_sha256"]:
        raise ValueError("Resource manifest hash mismatch")
    manifest = json.loads(path.read_text())
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest, *, for_publication=False):
    if manifest.get("schema") != "qlm-resource-manifest-v1":
        raise ValueError("Unsupported resource manifest")
    for key in ("asset_id", "version", "entrypoint", "cache_subdir", "source", "geometry", "physics", "license", "files"):
        if key not in manifest:
            raise ValueError(f"Resource manifest missing {key}")
    if "/" in safe_relative(manifest["asset_id"]) or "/" in safe_relative(manifest["version"]):
        raise ValueError("Asset/version identity must be a single component")
    safe_relative(manifest["cache_subdir"])
    files = manifest["files"]
    if not files or manifest["entrypoint"] not in files:
        raise ValueError("Resource file inventory/entrypoint required")
    for name, item in files.items():
        safe_relative(name)
        if type(item.get("size_bytes")) is not int or item["size_bytes"] < 0:
            raise ValueError("Resource size missing")
        if not isinstance(item.get("sha256"), str) or len(item["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in item["sha256"]):
            raise ValueError("Resource SHA256 missing")
    if for_publication:
        if manifest.get("kind") != "asset":
            raise ValueError("Controller weights are external dependencies; mirroring is not supported")
        if manifest["license"].get("redistribution_status") != "verified_source_declaration":
            raise ValueError("Resource redistribution license is unverified")
        if not manifest.get("dependency_validation", {}).get("closed"):
            raise ValueError("Resource dependency closure is not verified")
        if not manifest["license"].get("attribution") or not manifest["license"].get("source_evidence_sha256"):
            raise ValueError("License attribution/source evidence required")
    return manifest


def verify_payload(manifest, directory):
    directory = Path(directory).resolve()
    for name, expected in manifest["files"].items():
        path = under(directory, name)
        if not path.is_file() or path.stat().st_size != expected["size_bytes"] or sha256(path) != expected["sha256"]:
            raise ValueError(f"Resource payload changed or missing: {name}")
    return directory / manifest["entrypoint"]


def resolve_asset(asset_id, resource_root, *, verify=True):
    """Resolve an explicitly prepared cache; never falls back to a private path."""
    manifest = load_manifest(asset_id)
    root = under(resource_root, manifest["cache_subdir"])
    if verify:
        return verify_payload(manifest, root)
    return under(root, manifest["entrypoint"])


def prepare_asset(asset_id, source_root, resource_root):
    """Copy exact reviewed bytes from an explicitly acquired source into the cache.

    Acquisition URLs/identities are in each manifest. Authenticated third-party
    downloads remain operator-owned; this function never handles credentials.
    """
    manifest = load_manifest(asset_id)
    source = Path(source_root).resolve()
    verify_payload(manifest, source)
    destination = under(resource_root, manifest["cache_subdir"])
    if destination.exists():
        verify_payload(manifest, destination)
        return destination / manifest["entrypoint"]
    # Reject symlinks even when they happen to resolve inside the source root.
    if Path(source_root).is_symlink() or any(under(source, name).is_symlink() for name in manifest["files"]):
        raise ValueError("Source resource symlinks are not accepted")
    destination.mkdir(parents=True)
    for name in manifest["files"]:
        target = under(destination, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(under(source, name), target)
    verify_payload(manifest, destination)
    return destination / manifest["entrypoint"]

