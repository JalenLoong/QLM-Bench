"""Typed local staging and read-only Hub inspection.

The demonstrated immutable upload/hash/readback implementation is shared with
the old publisher. Staging is separate from external publication authorization.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import shutil

from qlm_bench.data import under, safe_relative
from .legacy_core import describe, digest, matches, pending_files

REPO_ID = "dontKnow23456/QLM-Bench"


def _read(path):
    return json.loads(Path(path).read_text())


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def _single(value):
    if "/" in safe_relative(value):
        raise ValueError("Artifact ID/version must be one path component")
    return value


def _new_stage(stage):
    stage = Path(stage)
    if stage.exists():
        raise ValueError("Refuse to overwrite an existing stage")
    stage.mkdir(parents=True)
    return stage


def _copy(source, root, relative):
    source = Path(source)
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"Missing or symlinked allowlisted source: {source}")
    destination = under(root, relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _inventory(stage, *, kind, identity, repo_id, work_id):
    if kind not in {"asset", "benchmark_cases", "evaluation_results", "catalogue"}:
        raise ValueError("Unknown publication artifact type")
    if not re.fullmatch(r"[A-Z]+-\d{3}", work_id):
        raise ValueError("Registered Work ID required")
    files = {p.relative_to(stage).as_posix(): describe(p)
             for p in sorted(stage.rglob("*")) if p.is_file()}
    if not files:
        raise ValueError("Empty artifact cannot be staged")
    return {"schema": "qlm-publication-inventory-v1", "kind": kind, "release": identity,
            "work_id": work_id, "repo_id": repo_id, "publication_status": "local_staged_not_uploaded", "files": files}


def check_inventory(stage, inventory):
    """Require exact local membership, safe paths and the original content hashes."""
    inventory = _read(inventory) if isinstance(inventory, (str, Path)) else inventory
    if Path(stage).is_symlink():
        raise ValueError("Symlinked stage is not accepted")
    stage = Path(stage).resolve()
    actual = {p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()}
    if actual != set(inventory["files"]):
        raise ValueError("Stage membership differs from explicit inventory")
    for name, expected in inventory["files"].items():
        path = under(stage, name)
        if path.is_symlink() or describe(path) != expected:
            raise ValueError(f"Stage content changed: {name}")
    return {"passed": True, "files": len(actual), "bytes": sum(v["size"] for v in inventory["files"].values()),
            "kind": inventory.get("kind", "legacy_demonstrations")}


def stage_asset(asset_id, source_root, stage, *, license_evidence, repo_id=REPO_ID, work_id="DATA-012"):
    """Stage only a license-evidenced, closed resource; never controller weights."""
    from qlm_bench.assets import load_manifest, validate_manifest, verify_payload, sha256
    manifest = load_manifest(asset_id)
    validate_manifest(manifest, for_publication=True)
    verify_payload(manifest, source_root)
    evidence = Path(license_evidence)
    if evidence.is_symlink() or sha256(evidence) != manifest["license"]["source_evidence_sha256"]:
        raise ValueError("License evidence identity mismatch")
    stage = _new_stage(stage)
    prefix = f"assets/{manifest['asset_id']}/{manifest['version']}"
    _write(under(stage, prefix + "/manifest.json"), manifest)
    for name in manifest["files"]:
        _copy(under(source_root, name), stage, prefix + "/runtime/" + name)
    verify_payload(manifest, under(stage, prefix + "/runtime"))
    _copy(evidence, stage, prefix + "/licenses/source-evidence" + evidence.suffix)
    _write(under(stage, prefix + "/licenses/attribution.json"), manifest["license"])
    return _inventory(stage, kind="asset", identity=asset_id + "/" + manifest["version"], repo_id=repo_id, work_id=work_id)


def validate_cases(manifest, cases, *, require_verified=True):
    from qlm_bench.evaluation import EvalCase
    if manifest.get("schema") != "qlm-benchmark-manifest-v1":
        raise ValueError("Unsupported benchmark manifest schema")
    _single(manifest["benchmark_release"])
    if not re.fullmatch(r"[0-9a-f]{40}", manifest.get("source_commit", "")):
        raise ValueError("Case snapshot requires exact QLM source commit")
    ids = [c.get("case_id") for c in cases]
    if not ids or len(ids) != len(set(ids)) or set(ids) != set(manifest.get("case_ids", [])):
        raise ValueError("Case set membership is incomplete or duplicate")
    for case in cases:
        try:
            parsed = EvalCase.from_record(case)
        except (TypeError, KeyError) as error:
            raise ValueError("Case is missing explicit physical reconstruction fields") from error
        _single(case["case_id"])
        validation = manifest.get("case_validation", {}).get(case["case_id"], {})
        if require_verified and (parsed.validation_status != "verified" or validation.get("evidence_kind") != "actual_runtime"
                or not validation.get("reset_reconstruction_passed") or not validation.get("evidence_sha256")):
            raise ValueError("Case reset/reconstruction is not actually verified")
        if require_verified:
            expected = validation["evidence_sha256"]
            if expected != parsed.provenance.get("evidence_sha256"):
                raise ValueError("Case and benchmark reconstruction evidence identities differ")
            if expected not in manifest.get("evidence_files", {}).values():
                raise ValueError("Verified case reconstruction evidence is not in the frozen validation inventory")
    if require_verified and manifest.get("validation_status") != "verified":
        raise ValueError("Unverified case set cannot become a benchmark release")
    return {"passed": True, "cases": len(cases), "verified": require_verified, "formal_score_available": False}


def stage_cases(source, stage, *, repo_id=REPO_ID, work_id="DATA-012", require_verified=True):
    """Copy a declared case set and generated source snapshots; no implicit suite."""
    source = Path(source)
    manifest = _read(source / "manifest.json")
    cases = [_read(under(source, f"cases/{_single(case_id)}.json")) for case_id in manifest["case_ids"]]
    validate_cases(manifest, cases, require_verified=require_verified)
    snapshots = manifest.get("snapshots", {})
    if not snapshots or "protocol_snapshot.json" not in snapshots:
        raise ValueError("Source-generated protocol snapshot identity required")
    for name, expected in snapshots.items():
        if digest(under(source, name)) != expected:
            raise ValueError("Case snapshot content hash mismatch")
        snapshot = _read(under(source, name))
        identity = snapshot.get("source_identity", {})
        if identity.get("source_commit") != manifest["source_commit"]:
            raise ValueError("Case snapshot belongs to another QLM source commit")
        if require_verified and (identity.get("dirty") is not False or not re.fullmatch(r"[0-9a-f]{64}", str(identity.get("source_tree_sha256", "")))):
            raise ValueError("Verified case publication requires a committed source snapshot identity")
    # Hash all evidence before creating a stage, so invalid inputs leave no payload.
    for name, expected in manifest.get("evidence_files", {}).items():
        if digest(under(source, name)) != expected:
            raise ValueError("Case validation evidence content hash mismatch")
    stage = _new_stage(stage)
    prefix = "benchmarks/" + manifest["benchmark_release"]
    _copy(source / "manifest.json", stage, prefix + "/manifest.json")
    for name in list(snapshots) + list(manifest.get("evidence_files", {})) + [f"cases/{c['case_id']}.json" for c in cases]:
        _copy(under(source, name), stage, prefix + "/" + name)
    inventory = _inventory(stage, kind="benchmark_cases", identity=manifest["benchmark_release"], repo_id=repo_id, work_id=work_id)
    if not require_verified:
        inventory["publication_eligibility"] = "unverified_local_only"
    return inventory


def stage_results(source, stage, *, repo_id=REPO_ID, work_id="DATA-012", include=()):
    from pyarrow import parquet
    from qlm_bench.evaluation import validate_result
    source = Path(source)
    manifest = _read(source / "run_manifest.json")
    original = {name: describe(source / name) for name in ("run_manifest.json", "episodes.parquet")}
    outcomes = parquet.read_table(source / "episodes.parquet").to_pylist()
    admission = deepcopy(manifest)
    admission["publication_status"] = "staged"
    report = validate_result(admission, outcomes)
    if not report.get("publishable"):
        raise ValueError("Engineering fixtures or unverified results cannot be published")
    protocol_identity = manifest.get("protocol", {}).get("source_identity", {})
    if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("source_commit", ""))) or \
            not re.fullmatch(r"[0-9a-f]{40}", str(protocol_identity.get("source_commit", ""))) or \
            not re.fullmatch(r"[0-9a-f]{64}", str(protocol_identity.get("spec_sha256", ""))):
        raise ValueError("Result publication requires exact code/protocol source hashes")
    benchmark = _single(manifest["benchmark_release"])
    submission = _single(manifest["submission_id"])
    included = [safe_relative(x) for x in include]
    if any(not name.startswith(("diagnostics/", "media/")) for name in included):
        raise ValueError("Optional result files must be explicit diagnostics/media")
    stage = _new_stage(stage)
    prefix = f"results/{benchmark}/{submission}"
    _copy(source / "run_manifest.json", stage, prefix + "/run_manifest.json")
    _copy(source / "episodes.parquet", stage, prefix + "/episodes.parquet")
    if any(describe(under(stage, prefix + "/" + name)) != expected for name, expected in original.items()):
        raise ValueError("Result source changed during staging")
    _write(under(stage, prefix + "/summary.json"), report)
    for name in included:
        _copy(under(source, name), stage, prefix + "/" + name)
    return _inventory(stage, kind="evaluation_results", identity=benchmark + "/" + submission, repo_id=repo_id, work_id=work_id)


def stage_catalogue(catalog, old_releases, stage, *, repo_id=REPO_ID, work_id="DATA-012", release_manifests=None):
    """Build discovery metadata without changing any original release entries."""
    from qlm_bench.data import DatasetRef
    catalog = _read(catalog) if isinstance(catalog, (str, Path)) else catalog
    old_releases = _read(old_releases) if isinstance(old_releases, (str, Path)) else old_releases
    by_id = {e["ref"]["release"]: e for e in catalog["demonstrations"]}
    if len(by_id) != len(catalog["demonstrations"]):
        raise ValueError("Duplicate catalogue release")
    for old in old_releases["releases"]:
        row = by_id.get(old["id"])
        if row is None:
            raise ValueError("Historical release missing from catalogue")
        ref = DatasetRef.from_dict(row["ref"])
        if ref.canonical_root != old["canonical_root"] or ref.manifest != old["manifest"] or row["split"] != old["split"]:
            raise ValueError("Historical release path/split rewritten")
        for key in ("episodes", "actions", "adaptation_usage", "included_in_first_adaptation_training_evaluation"):
            if key in old and row.get(key) != old[key]:
                raise ValueError("Historical release declaration rewritten")
    release_rows = [{"task": e["task"], **e["ref"], "episodes": e["episodes"], "actions": e["actions"],
                     "split": e["split"], "adaptation_usage": e["adaptation_usage"]} for e in catalog["demonstrations"]]
    rows = []
    for entry in catalog["demonstrations"] if release_manifests is not None else []:
        ref = DatasetRef.from_dict(entry["ref"])
        path = Path(release_manifests[ref.release])
        if digest(path) != ref.manifest_sha256:
            raise ValueError("Metadata index release manifest SHA256 mismatch")
        manifest = _read(path)
        split_counts = {name: len(uids) for name, uids in manifest["split"].items()}
        episode_uids = [episode["episode_uid"] for episode in manifest["episodes"]]
        split_uids = [uid for uids in manifest["split"].values() for uid in uids]
        if (split_counts != entry["split"] or len(episode_uids) != entry["episodes"]
                or len(set(episode_uids)) != len(episode_uids)
                or len(set(split_uids)) != len(split_uids) or set(split_uids) != set(episode_uids)):
            raise ValueError("Metadata index membership/split mismatch")
        for episode in manifest["episodes"]:
            uid = episode["episode_uid"]
            rows.append({"task": entry["task"], **ref.to_dict(), "episode_uid": uid,
                         "split": next(k for k, v in manifest["split"].items() if uid in v),
                         "adaptation_usage": entry["adaptation_usage"], "raw_path": episode["raw_path"]})
    stage = _new_stage(stage)
    _write(stage / "catalog.json", catalog)
    _write(stage / "metadata/release_index.json", release_rows)
    if rows:
        _write(stage / "metadata/demonstration_index.json", rows)
    # Do not claim that release-level rows are episode-level demonstrations.
    try:
        import pyarrow as pa
        from pyarrow import parquet
    except ImportError:
        pass
    else:
        if rows:
            parquet.write_table(pa.Table.from_pylist(rows), stage / "metadata/demonstration_index.parquet")
    return _inventory(stage, kind="catalogue", identity="catalogue-v1", repo_id=repo_id, work_id=work_id)


def read_hub_state(repo_id=REPO_ID, *, revision=None):
    """Read public Hub metadata at one observed/fixed commit; no implicit login."""
    from huggingface_hub import HfApi
    from huggingface_hub.hf_api import RepoFile
    api = HfApi(token=False)
    info = api.dataset_info(repo_id, revision=revision)
    files = [f for f in api.list_repo_tree(repo_id, repo_type="dataset", revision=info.sha, recursive=True) if isinstance(f, RepoFile)]
    return {"repo_id": repo_id, "revision": info.sha, "private": info.private,
            "files": {f.path: {"size": f.size, "git_blob": f.blob_id, "sha256": f.lfs.sha256 if f.lfs else None} for f in files},
            "read_only": True}


def generate_snapshots(destination, source_identity, *, protocol=None):
    """Generate snapshots from installed declarations, never edit a second spec.

    This local snapshot records both commit and source tree identity. A dirty
    source tree remains a local candidate; it is not a committed benchmark release.
    No protocol/suite is invented when protocol is omitted.
    """
    from qlm_bench import __version__
    from qlm_bench.contracts import physical_contract, frozen_bundle
    from qlm_bench.assets import load_registry
    for key, length in (("source_commit", 40), ("source_tree_sha256", 64)):
        if not re.fullmatch(r"[0-9a-f]{" + str(length) + "}", source_identity.get(key, "")):
            raise ValueError("Exact committed/tree source identity required")
    if type(source_identity.get("dirty")) is not bool:
        raise ValueError("Explicit dirty source status required")
    destination = _new_stage(destination)
    objects = {"physical_schema_snapshot.json": physical_contract(),
               "compatibility_profile_snapshot.json": frozen_bundle("dataset_v2"),
               "resource_registry_snapshot.json": load_registry()}
    if protocol is not None:
        objects["protocol_snapshot.json"] = protocol.record()
    for name, value in objects.items():
        _write(destination / name, {"source_identity": source_identity, "qlm_core_version": __version__, "spec": value})
    files = {name: digest(destination / name) for name in objects}
    _write(destination / "snapshot_manifest.json", {"schema": "qlm-spec-snapshots-v1",
           "source_identity": source_identity, "files": files,
           "publication_status": "local_candidate" if source_identity["dirty"] else "source_snapshot",
           "protocol_present": protocol is not None})
    return files
