"""`qlm` command line: a thin dispatcher over the package entry points.

    qlm benchmark {fetch,verify,run,prepare} ...   == python -m qlm_bench.benchmark ...
    qlm training-env <sub-command> ...            == python -m qlm_bench.training_env ...
    qlm data {download,validate,convert,merge,replay} ...
    qlm catalog | qlm resolve-release <release>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def main(argv=None):
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw and raw[0] == 'benchmark':
        from qlm_bench.benchmark.__main__ import main as entry
        return entry(raw[1:])
    if raw and raw[0] == 'training-env':
        from qlm_bench.training_env.worker import main as entry
        return entry(raw[1:])
    parser = argparse.ArgumentParser(prog='qlm', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('benchmark', help='Standard100 (python -m qlm_bench.benchmark)')
    commands.add_parser('training-env', help='Streaming training environment (python -m qlm_bench.training_env)')
    commands.add_parser('catalog', help='Print the demonstration catalogue')
    resolve = commands.add_parser('resolve-release')
    resolve.add_argument('release')
    data = commands.add_parser('data', help='Demonstrations: download, validate, convert, merge, review')
    ops = data.add_subparsers(dest='data_operation', required=True)
    download = ops.add_parser('download')
    download.add_argument('--output', required=True)
    download.add_argument('--release', action='append', help='Release name (repeatable); default: all ten')
    download.add_argument('--physical', action='store_true', help='Also download physical/v1 initial-state bundles')
    download.add_argument('--repo-id')
    download.add_argument('--revision')
    validate = ops.add_parser('validate')
    validate.add_argument('--config', required=True)
    validate.add_argument('--raw', action='store_true')
    convert = ops.add_parser('convert')
    for name in ('--raw', '--canonical', '--ffmpeg', '--ffprobe'):
        convert.add_argument(name, required=True)
    merge = ops.add_parser('merge')
    for name in ('--entries', '--output', '--ffmpeg', '--ffprobe', '--release-name'):
        merge.add_argument(name, required=True)
    replay = ops.add_parser('replay')
    replay.add_argument('--canonical', required=True)
    replay.add_argument('--output', required=True)
    args = parser.parse_args(raw)
    if args.command == 'catalog':
        from qlm_bench.data import load_catalog
        result = load_catalog()
    elif args.command == 'resolve-release':
        from qlm_bench.data import resolve_release
        result = resolve_release(args.release).to_dict()
    else:
        from qlm_bench.data import download_demonstrations
        from qlm_bench.data.tools import validate_data, convert_raw, merge_episodes, build_replay
        op = args.data_operation
        if op == 'download':
            result = {'path': download_demonstrations(args.output, releases=args.release, repo_id=args.repo_id,
                                                      revision=args.revision, include_physical=args.physical)}
        elif op == 'validate':
            result = validate_data(args.config, raw=args.raw)
        elif op == 'convert':
            result = convert_raw(args.raw, args.canonical, ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
        elif op == 'merge':
            result = merge_episodes(json.loads(Path(args.entries).read_text()), args.output,
                                    ffmpeg=args.ffmpeg, ffprobe=args.ffprobe, work_id=args.release_name)
        else:
            result = build_replay(args.canonical, args.output)
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
