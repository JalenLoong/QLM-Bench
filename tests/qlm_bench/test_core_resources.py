"""Independent package identity, resource boundaries and typed local staging."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from qlm_bench.contracts import frozen_bundle, physical_contract
from qlm_bench.data import DatasetRef, load_catalog, resolve_release, safe_relative, verify_canonical_payload
from qlm_bench.assets import load_manifest, load_registry, validate_manifest, verify_payload
from qlm_bench.publication import check_inventory, describe, stage_catalogue, validate_cases, stage_cases, stage_results, stage_asset


def test_core_import_has_no_runtime_or_optional_dependencies():
    script = "import qlm_bench, qlm_bench.contracts, qlm_bench.data, qlm_bench.assets, qlm_bench.publication; import sys; assert not any(n.split('.')[0] in {'torch','numpy','PIL','pyarrow','rambo','crl2','isaaclab','isaacsim','transformers','diffusers'} for n in sys.modules)"
    subprocess.run([sys.executable, "-c", script], check=True)


def test_frozen_specs_keep_bytes_and_physical_interface_has_no_model_grouping():
    frozen_bundle("contracts_v2")
    profile = frozen_bundle("dataset_v2")["profile.json"]
    assert profile["model_sampling_stride"] == 4
    physical = physical_contract()
    assert physical["action"]["id"] == "rambo-native9-v2"
    assert "actions_per_latent" not in physical and "model_sampling_stride" not in physical
    assert physical["rates_hz"] == {"high_level": 50, "controller": 100, "physics": 500, "policy_rgb": 50, "observer_diagnostic": 25}


def test_catalogue_keeps_first_training_pin_and_excludes_added_tasks():
    catalog = load_catalog()
    push = resolve_release("DATA-006-20260916T075451Z", catalog)
    assert push.revision == "4b5e0ed9aa04cbc1143774798f63171b27d838a7"
    assert push.manifest_sha256 == "59793e0819476ab92fea902defb2394ff706191bc4fb146166bcc4d7827f31b3"
    assert {row["task"] for row in catalog["demonstrations"]} == {"push_box", "lift_basket", "press_button"}
    for row in catalog["demonstrations"][1:]:
        assert row["adaptation_usage"] == "publication_only"
        assert row["included_in_first_adaptation_training_evaluation"] == {"v2": False, "v3": False}
    for kwargs in [{"revision": "main"}, {"release": "other"}, {"manifest_sha256": ""}, {"canonical_root": "../data"}]:
        with pytest.raises(ValueError):
            replace(push, **kwargs)


@pytest.mark.parametrize("path", ["../secret", "/tmp/path", "a/../x", "a//b", ".", "a\\b"])
def test_portable_path_rejects_escape_and_aliases(path):
    with pytest.raises(ValueError):
        safe_relative(path)


def test_registry_preserves_controller_and_refuses_unverified_asset_publication():
    assert len(load_registry()["resources"]) == 14
    for asset in ["cardboard-box-05", "oasis-basket", "rambo-go2-controller"]:
        with pytest.raises(ValueError):
            validate_manifest(load_manifest(asset), for_publication=True)
    industrial = load_manifest("industrial-button")
    validate_manifest(industrial, for_publication=True)
    assert "Zeppelin" in industrial["license"]["attribution"]
    controller = load_manifest("rambo-go2-controller")
    assert controller["source"]["revision"] == "65fa7b035ad16af78c2af2d64a3ac4aed9c81fdc"
    assert controller["files"]["model_2000.pt"]["sha256"] == "1cc5f68fe15e37ccabae26060d79a26a8c078ed465a81f6f729c2009b67ca706"


def test_resource_verification_rejects_hash_change_and_missing_dependency(tmp_path):
    p = tmp_path / "asset.usda"
    p.write_bytes(b"source")
    manifest = {"entrypoint": "asset.usda", "files": {"asset.usda": {"size_bytes": 6, "sha256": hashlib.sha256(b"source").hexdigest()}}}
    assert verify_payload(manifest, tmp_path) == p
    p.write_bytes(b"other!")
    with pytest.raises(ValueError):
        verify_payload(manifest, tmp_path)
    p.unlink()
    with pytest.raises(ValueError):
        verify_payload(manifest, tmp_path)


def test_inventory_checks_exact_membership_and_mutation(tmp_path):
    stage = tmp_path / "stage"
    stage.mkdir()
    p = stage / "catalog.json"
    p.write_text("{}")
    inventory = {"files": {"catalog.json": describe(p)}}
    assert check_inventory(stage, inventory)["passed"]
    (stage / "unlisted").write_text("unexpected")
    with pytest.raises(ValueError, match="membership"):
        check_inventory(stage, inventory)
    (stage / "unlisted").unlink()
    p.write_text("[]")
    with pytest.raises(ValueError, match="changed"):
        check_inventory(stage, inventory)


def test_catalogue_stage_does_not_admit_or_rewrite_history(tmp_path):
    catalog = load_catalog()
    old = {"releases": [{"id": e["ref"]["release"], "canonical_root": e["ref"]["canonical_root"], "manifest": e["ref"]["manifest"], "split": e["split"], "episodes": e["episodes"], "actions": e["actions"]} for e in catalog["demonstrations"]]}
    inv = stage_catalogue(catalog, old, tmp_path / "stage")
    assert check_inventory(tmp_path / "stage", inv)["passed"]
    old["releases"][0]["split"] = {"train": 50}
    with pytest.raises(ValueError, match="rewritten"):
        stage_catalogue(catalog, old, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_case_publisher_refuses_seed_only_and_unverified_reconstruction():
    manifest = {"schema": "qlm-benchmark-manifest-v1", "benchmark_release": "test-only", "source_commit": "a" * 40, "case_ids": ["one"], "validation_status": "verified"}
    with pytest.raises(ValueError):
        validate_cases(manifest, [{"case_id": "one", "seed": 42}])
    case = {key: {} for key in ["task_profile", "assets", "robot_initialization", "object_initialization", "goal", "scene", "cameras", "runtime_profile", "controller", "reset_procedure", "source"]}
    case.update(case_id="one", task_id="push_box", seed=42, validation={"status": "unverified"})
    with pytest.raises(ValueError):
        validate_cases(manifest, [case])


def test_asset_stager_requires_frozen_license_evidence(tmp_path, monkeypatch):
    from qlm_bench import assets
    source = tmp_path / "source"
    source.mkdir()
    (source / "asset.usda").write_bytes(b"source")
    evidence = tmp_path / "license.json"
    evidence.write_text("{}")
    manifest = {"schema": "qlm-resource-manifest-v1", "kind": "asset", "asset_id": "test-fixture",
                "version": "v1", "entrypoint": "asset.usda", "cache_subdir": "test-fixture/v1/runtime",
                "source": {"kind": "test_fixture"}, "geometry": {}, "physics": {},
                "license": {"redistribution_status": "verified_source_declaration", "attribution": "test-only",
                            "source_evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()},
                "files": {"asset.usda": {"size_bytes": 6, "sha256": hashlib.sha256(b"source").hexdigest()}},
                "dependency_validation": {"closed": True}}
    monkeypatch.setattr(assets, "load_manifest", lambda _: manifest)
    inventory = stage_asset("test-fixture", source, tmp_path / "stage", license_evidence=evidence)
    assert check_inventory(tmp_path / "stage", inventory)["passed"]
    evidence.write_text("changed")
    with pytest.raises(ValueError, match="License evidence"):
        stage_asset("test-fixture", source, tmp_path / "bad", license_evidence=evidence)
    assert not (tmp_path / "bad").exists()


def test_result_stager_never_publishes_engineering_fixture(tmp_path, monkeypatch):
    pa = pytest.importorskip("pyarrow", reason="Run result/Parquet staging checks in the separate CPU data environment")
    from pyarrow import parquet
    from qlm_bench import evaluation
    source = tmp_path / "source"
    source.mkdir()
    (source / "run_manifest.json").write_text(json.dumps({"benchmark_release": "test-only", "submission_id": "fixture"}))
    parquet.write_table(pa.Table.from_pylist([{"outcome": "success"}, {"outcome": "failure"}]), source / "episodes.parquet")
    # Complete structural/semantic validation is tested with the actual runner
    # in tests/qlm; this boundary must enforce its negative publication verdict.
    monkeypatch.setattr(evaluation, "validate_result", lambda manifest, outcomes: {"passed": True, "publishable": False})
    with pytest.raises(ValueError, match="fixtures"):
        stage_results(source, tmp_path / "stage")
    assert not (tmp_path / "stage").exists()


def _payload_inventory(root):
    (root / "meta").mkdir(parents=True)
    (root / "data").mkdir()
    (root / "data/episode.parquet").write_bytes(b"test-only-payload")
    (root / "meta/info.json").write_text("{}")
    inventory = {"data/episode.parquet": hashlib.sha256(b"test-only-payload").hexdigest(),
                 "meta/info.json": hashlib.sha256(b"{}").hexdigest()}
    contents = json.dumps(inventory).encode()
    (root / "meta/checksums.json").write_bytes(contents)
    return inventory, hashlib.sha256(contents).hexdigest()


def test_canonical_payload_is_bound_to_external_inventory_digest(tmp_path):
    inventory, trusted = _payload_inventory(tmp_path)
    assert verify_canonical_payload(tmp_path, trusted)["files"] == 2
    (tmp_path / "data/episode.parquet").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="payload hash"):
        verify_canonical_payload(tmp_path, trusted)
    inventory["data/episode.parquet"] = hashlib.sha256(b"tampered").hexdigest()
    (tmp_path / "meta/checksums.json").write_text(json.dumps(inventory))
    with pytest.raises(ValueError, match="immutable revision"):
        verify_canonical_payload(tmp_path, trusted)


def test_canonical_payload_rejects_missing_or_extra_files(tmp_path):
    _, trusted = _payload_inventory(tmp_path)
    (tmp_path / "unlisted").write_text("unexpected")
    with pytest.raises(ValueError, match="membership"):
        verify_canonical_payload(tmp_path, trusted)
    (tmp_path / "unlisted").unlink()
    (tmp_path / "data/episode.parquet").unlink()
    with pytest.raises(ValueError, match="membership"):
        verify_canonical_payload(tmp_path, trusted)


def test_canonical_payload_rejects_empty_root_and_inventory_escape(tmp_path):
    with pytest.raises(ValueError, match="missing"):
        verify_canonical_payload(tmp_path, "a" * 64)
    (tmp_path / "meta").mkdir()
    contents = json.dumps({"../secret": "a" * 64}).encode()
    (tmp_path / "meta/checksums.json").write_bytes(contents)
    with pytest.raises(ValueError, match="Unsafe"):
        verify_canonical_payload(tmp_path, hashlib.sha256(contents).hexdigest())


def test_canonical_inventory_itself_cannot_escape_root(tmp_path):
    root = tmp_path / "canonical"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "checksums.json").write_text("{}")
    (root / "meta").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes resource root"):
        verify_canonical_payload(root, hashlib.sha256(b"{}").hexdigest())


def _case_stage_fixture(tmp_path):
    """Synthetic publisher input shapes; these temporary files are not runtime receipts."""
    from qlm_bench.evaluation import EvalCase
    from qlm_bench.policy_interface import ObservationProfile
    source = tmp_path / "source"
    (source / "validation").mkdir(parents=True)
    (source / "cases").mkdir()
    evidence = source / "validation/test-only-reset.json"
    evidence.write_text(json.dumps({"test_fixture": True, "reset_reconstruction_passed": True}))
    proof = hashlib.sha256(evidence.read_bytes()).hexdigest()
    profile = ObservationProfile("test-only-rgb", ("go2_ego", "d435i_rgb_task"), (), True, {})
    case = EvalCase("test-only-case", "push_box", "test-only-task-v1", "Push the box.", profile,
                   {"test-only-box": "v1"}, {"robot": [0, 0, 0], "object": [1, 0, 0]},
                   {"goal": [1, 0, 0]}, {"floor": "test-only-floor"},
                   {name: {"test_fixture": True} for name in profile.camera_keys}, 7,
                   "test-only-controller", "test-only-runtime", {"settle": "test-only-reset"},
                   {"evidence_kind": "actual_runtime", "reset_reconstruction_passed": True,
                    "evidence_sha256": proof}, "verified").record()
    (source / "cases/test-only-case.json").write_text(json.dumps(case))
    snapshot = source / "protocol_snapshot.json"
    snapshot.write_text(json.dumps({"source_identity": {"source_commit": "a" * 40,
                       "source_tree_sha256": "b" * 64, "dirty": False},
                       "spec": {"test_fixture": True, "scope": "engineering_diagnostic"}}))
    manifest = {"schema": "qlm-benchmark-manifest-v1", "benchmark_release": "test-only-publisher-shapes",
                "source_commit": "a" * 40, "case_ids": [case["case_id"]], "validation_status": "verified",
                "case_validation": {case["case_id"]: {"evidence_kind": "actual_runtime",
                    "reset_reconstruction_passed": True, "evidence_sha256": proof}},
                "snapshots": {"protocol_snapshot.json": hashlib.sha256(snapshot.read_bytes()).hexdigest()},
                "evidence_files": {"validation/test-only-reset.json": proof}}
    (source / "manifest.json").write_text(json.dumps(manifest))
    return source, manifest, case


def test_case_stage_freezes_corresponding_reconstruction_material(tmp_path):
    source, manifest, case = _case_stage_fixture(tmp_path)
    inventory = stage_cases(source, tmp_path / "stage")
    assert check_inventory(tmp_path / "stage", inventory)["passed"]
    prefix = "benchmarks/" + manifest["benchmark_release"]
    assert (tmp_path / "stage" / prefix / "validation/test-only-reset.json").read_bytes() == \
           (source / "validation/test-only-reset.json").read_bytes()
    assert inventory["kind"] == "benchmark_cases"


@pytest.mark.parametrize("mutation", ["case_evidence_mismatch", "absent_material", "material_changed"])
def test_case_stage_rejects_missing_mismatched_or_changed_validation_material(tmp_path, mutation):
    source, manifest, case = _case_stage_fixture(tmp_path)
    if mutation == "case_evidence_mismatch":
        manifest["case_validation"][case["case_id"]]["evidence_sha256"] = "c" * 64
    elif mutation == "absent_material":
        manifest["evidence_files"] = {}
    else:
        (source / "validation/test-only-reset.json").write_text("changed")
    (source / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="evidence"):
        stage_cases(source, tmp_path / "stage")
    assert not (tmp_path / "stage").exists()


def _catalogue_manifest_fixture(tmp_path):
    """Exercise actual release-manifest UID-list shape with test-only metadata."""
    from copy import deepcopy
    catalog = deepcopy(load_catalog())
    paths, manifests = {}, {}
    old = {"releases": []}
    for entry in catalog["demonstrations"]:
        ref = entry["ref"]
        uids = [entry["task"] + "-test-only-" + str(i) for i in range(entry["episodes"])]
        splits, offset = {}, 0
        for split, count in entry["split"].items():
            splits[split] = uids[offset:offset + count]
            offset += count
        manifest = {"repo_id": ref["repo_id"], "release": ref["release"], "dataset_schema_version": ref["schema"],
                    "canonical_root": ref["canonical_root"], "split": splits,
                    "episodes": [{"episode_uid": uid, "raw_path": f"raw/v2/{entry['task']}/test-only/{uid}"} for uid in uids]}
        path = tmp_path / (ref["release"] + ".json")
        path.write_text(json.dumps(manifest))
        ref["manifest_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        paths[ref["release"]], manifests[ref["release"]] = path, manifest
        old["releases"].append({"id": ref["release"], "canonical_root": ref["canonical_root"],
                                "manifest": ref["manifest"], "split": entry["split"],
                                "episodes": entry["episodes"], "actions": entry["actions"]})
    return catalog, old, paths, manifests


def test_catalogue_episode_index_reads_real_uid_list_shape(tmp_path):
    parquet = pytest.importorskip("pyarrow.parquet", reason="Run Parquet catalogue checks in the independent CPU data environment")
    catalog, old, paths, _ = _catalogue_manifest_fixture(tmp_path)
    inventory = stage_catalogue(catalog, old, tmp_path / "stage", release_manifests=paths)
    assert check_inventory(tmp_path / "stage", inventory)["passed"]
    rows = parquet.read_table(tmp_path / "stage/metadata/demonstration_index.parquet").to_pylist()
    assert len(rows) == 70
    assert len({(row["release"], row["episode_uid"]) for row in rows}) == 70
    assert {task: sum(row["task"] == task for row in rows) for task in ("push_box", "lift_basket", "press_button")} == \
           {"push_box": 50, "lift_basket": 10, "press_button": 10}


@pytest.mark.parametrize("mutation", ["duplicate_episode", "duplicate_split_member", "different_split_counts"])
def test_catalogue_rejects_uid_membership_or_split_mismatch(tmp_path, mutation):
    catalog, old, paths, manifests = _catalogue_manifest_fixture(tmp_path)
    entry = catalog["demonstrations"][0]
    release = entry["ref"]["release"]
    manifest = manifests[release]
    if mutation == "duplicate_episode":
        manifest["episodes"][-1]["episode_uid"] = manifest["episodes"][0]["episode_uid"]
    elif mutation == "duplicate_split_member":
        manifest["split"]["test"][-1] = manifest["split"]["train"][0]
    else:
        manifest["split"]["validation"].append(manifest["split"]["train"].pop())
    paths[release].write_text(json.dumps(manifest))
    entry["ref"]["manifest_sha256"] = hashlib.sha256(paths[release].read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="membership/split"):
        stage_catalogue(catalog, old, tmp_path / "stage", release_manifests=paths)
    assert not (tmp_path / "stage").exists()
