"""CPU discovery/validation CLI. Mutating Hub operations have no CLI entrypoint."""
from __future__ import annotations
import argparse
import json


def main(argv=None):
    # Simulator code owns AppLauncher arguments and is loaded only on demand.
    import sys
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if raw_args and raw_args[0] == "live":
        from .live.isaac import main as live_main
        return live_main(raw_args[1:])
    if raw_args and raw_args[0] == "collect":
        from .collection.isaac import main as collect_main
        return collect_main(raw_args[1:])
    parser = argparse.ArgumentParser(prog="qlm")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("live", help="Synchronous physical client for a separately launched local policy")
    commands.add_parser("contract")
    commands.add_parser("catalog")
    commands.add_parser("assets")
    resolve = commands.add_parser("resolve-release")
    resolve.add_argument("release")
    asset = commands.add_parser("resolve-asset")
    asset.add_argument("asset_id")
    asset.add_argument("--resource-root", required=True)
    prepare = commands.add_parser("prepare-asset")
    prepare.add_argument("asset_id")
    prepare.add_argument("--source-root", required=True)
    prepare.add_argument("--resource-root", required=True)
    inventory = commands.add_parser("check-inventory")
    inventory.add_argument("stage")
    inventory.add_argument("inventory")
    hub = commands.add_parser("hub-inspect")
    hub.add_argument("--repo-id", default="dontKnow23456/QLM-Bench")
    hub.add_argument("--revision")
    collect = commands.add_parser("collect", help="Scripted collection in the separately installed Isaac runtime")
    collect.add_argument("--task", choices=["push_box", "lift_basket", "press_button"], required=True)
    collect.add_argument("--profile", required=True)
    collect.add_argument("--resource-root", required=True)
    collect.add_argument("--output-dir", required=True)
    collect.add_argument("--ffmpeg", required=True)
    collect.add_argument("--ffprobe")
    collect.add_argument("--data-python", required=True)
    collect.add_argument("--episode-length-s", type=float, required=True)
    collect.add_argument("--seed", type=int, required=True)
    collect.add_argument("--diagnostic-only", action="store_true")
    data = commands.add_parser("data", help="CPU Raw/Canonical conversion, validation, merge and replay")
    operations = data.add_subparsers(dest="data_operation", required=True)
    validate = operations.add_parser("validate")
    validate.add_argument("--config", required=True)
    validate.add_argument("--raw", action="store_true")
    convert = operations.add_parser("convert")
    convert.add_argument("--raw", required=True)
    convert.add_argument("--canonical", required=True)
    convert.add_argument("--ffmpeg", required=True)
    convert.add_argument("--ffprobe", required=True)
    merge = operations.add_parser("merge")
    merge.add_argument("--entries", required=True)
    merge.add_argument("--output", required=True)
    merge.add_argument("--ffmpeg", required=True)
    merge.add_argument("--ffprobe", required=True)
    merge.add_argument("--work-id", required=True)
    replay = operations.add_parser("replay")
    replay.add_argument("--canonical", required=True)
    replay.add_argument("--output", required=True)
    for command in ("stage-asset", "stage-cases", "stage-results", "stage-catalogue"):
        sub = commands.add_parser(command)
        sub.add_argument("--stage", required=True)
        sub.add_argument("--inventory", required=True)
        if command == "stage-asset":
            sub.add_argument("asset_id")
            sub.add_argument("--source-root", required=True)
            sub.add_argument("--license-evidence", required=True)
        elif command == "stage-catalogue":
            sub.add_argument("--catalog", required=True)
            sub.add_argument("--release-index", required=True)
            sub.add_argument("--release-manifests", help="JSON mapping release IDs to explicit local manifest paths")
        else:
            sub.add_argument("--source", required=True)
            if command == "stage-cases":
                sub.add_argument("--local-unverified", action="store_true")
            else:
                sub.add_argument("--include", action="append", default=[])
    args = parser.parse_args(argv)
    if args.command == "contract":
        from .contracts import physical_contract
        result = physical_contract()
    elif args.command == "catalog":
        from .data import load_catalog
        result = load_catalog()
    elif args.command == "resolve-release":
        from .data import resolve_release
        result = resolve_release(args.release).to_dict()
    elif args.command == "assets":
        from .assets import load_registry
        result = load_registry()
    elif args.command == "resolve-asset":
        from .assets import resolve_asset
        result = {"path": str(resolve_asset(args.asset_id, args.resource_root))}
    elif args.command == "prepare-asset":
        from .assets import prepare_asset
        result = {"path": str(prepare_asset(args.asset_id, args.source_root, args.resource_root))}
    elif args.command == "check-inventory":
        from .publication import check_inventory
        result = check_inventory(args.stage, args.inventory)
    elif args.command == "hub-inspect":
        from .publication import read_hub_state
        result = read_hub_state(args.repo_id, revision=args.revision)
    elif args.command == "data":
        from pathlib import Path
        from .data.tools import validate_data, convert_raw, merge_episodes, build_replay
        if args.data_operation == "validate":
            result = validate_data(json.loads(Path(args.config).read_text()), raw=args.raw)
        elif args.data_operation == "convert":
            result = convert_raw(args.raw, args.canonical, ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
        elif args.data_operation == "merge":
            result = merge_episodes(json.loads(Path(args.entries).read_text()), args.output,
                                    ffmpeg=args.ffmpeg, ffprobe=args.ffprobe, work_id=args.work_id)
        else:
            result = build_replay(args.canonical, args.output)
    else:
        from pathlib import Path
        from .publication import stage_asset, stage_cases, stage_results, stage_catalogue
        if args.command == "stage-asset":
            result = stage_asset(args.asset_id, args.source_root, args.stage, license_evidence=args.license_evidence)
        elif args.command == "stage-cases":
            result = stage_cases(args.source, args.stage, require_verified=not args.local_unverified)
        elif args.command == "stage-results":
            result = stage_results(args.source, args.stage, include=args.include)
        else:
            manifests = json.loads(Path(args.release_manifests).read_text()) if args.release_manifests else None
            result = stage_catalogue(args.catalog, args.release_index, args.stage, release_manifests=manifests)
        inventory_path = Path(args.inventory)
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        if inventory_path.resolve().is_relative_to(Path(args.stage).resolve()):
            raise ValueError("Inventory must live outside the staged payload")
        inventory_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        result = {"kind": result["kind"], "files": len(result["files"]), "publication_status": result["publication_status"]}
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
