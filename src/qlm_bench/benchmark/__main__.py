"""Standard100 command line: fetch / verify / run / prepare (see qlm_bench.benchmark.evaluate for `run`)."""
import argparse
import json
import os
import sys


def main(argv=None):
    p = argparse.ArgumentParser(prog='python -m qlm_bench.benchmark', description=__doc__)
    sub = p.add_subparsers(dest='mode', required=True)
    fetch = sub.add_parser('fetch', help='Download the suite and scene/controller packs from Hugging Face')
    fetch.add_argument('--output', required=True, help='Resource root to create/fill')
    fetch.add_argument('--case-id', action='append', help='Only these cases (repeatable); default: all 100')
    fetch.add_argument('--repo-id')
    fetch.add_argument('--revision')
    verify = sub.add_parser('verify', help='Reset every case and check state/RGB reconstruction (no policy)')
    verify.add_argument('--resource-root', required=True)
    verify.add_argument('--suite')
    verify.add_argument('--output', required=True)
    verify.add_argument('--case-id', action='append')
    run = sub.add_parser('run', help='Evaluate a policy server over one policy seed of the protocol')
    run.add_argument('--resource-root', required=True)
    run.add_argument('--suite', help='Defaults to <resource-root>/benchmarks/mujoco-standard-test100-v1')
    run.add_argument('--policy-port', required=True, type=int)
    run.add_argument('--policy-seed', type=int, default=42, choices=(42, 43, 44),
                     help='42 = Standard100; 43/44 = repeats 2/3 of the 300-episode paper protocol')
    run.add_argument('--output', required=True)
    run.add_argument('--cases', help='Comma-separated case ids (selection aid, not a Standard100 score)')
    run.add_argument('--policy-name', default='policy')
    run.add_argument('--record-video', action='store_true')
    run.add_argument('--ffmpeg', default='ffmpeg')
    run.add_argument('--ffprobe', default='ffprobe')
    run.add_argument('--previous-result', help='result.json of an interrupted run: finished trials are kept')
    run.add_argument('--rpc-timeout-s', type=float, default=600.)
    prepare = sub.add_parser('prepare', help='Maintainers: freeze the test split of a dataset snapshot into a suite')
    prepare.add_argument('--snapshot', required=True)
    prepare.add_argument('--controller-root', required=True)
    prepare.add_argument('--output', required=True)
    prepare.add_argument('--resource-map', help='JSON {resource_identity: scene.xml} for scenes not at their recorded path')
    a = p.parse_args(argv)
    if a.mode == 'fetch':
        from qlm_bench.benchmark.download import fetch as run_fetch
        return print(json.dumps(run_fetch(a.output, case_ids=a.case_id, repo_id=a.repo_id, revision=a.revision), indent=2))
    if a.mode == 'prepare':
        from qlm_bench.benchmark.suite import prepare as run_prepare, read
        return print(run_prepare(a.snapshot, a.output, controller_root=a.controller_root,
                                 model_map=read(a.resource_map) if a.resource_map else None))
    os.environ['MUJOCO_GL'] = 'egl'
    import torch
    torch.set_num_threads(1)
    from qlm_bench.benchmark import suite
    from pathlib import Path
    bench = a.suite or str(Path(a.resource_root) / 'benchmarks' / suite.RELEASE)
    if a.mode == 'verify':
        return suite.write(a.output, suite.verify_cases(a.resource_root, bench, a.case_id))
    from qlm_bench.benchmark.evaluate import run as run_eval, complete
    previous = suite.read(a.previous_result)['outcomes'] if a.previous_result else ()
    result = run_eval(a.resource_root, a.output, policy_port=a.policy_port, policy_seed=a.policy_seed, suite_dir=bench,
                      cases=a.cases.split(',') if a.cases else None, policy_name=a.policy_name,
                      record_video=a.record_video, ffmpeg=a.ffmpeg, ffprobe=a.ffprobe,
                      previous_outcomes=previous, rpc_timeout_s=a.rpc_timeout_s)
    print(json.dumps(result['validation'], indent=2), flush=True)
    sys.exit(0 if complete(result) else 1)


if __name__ == '__main__':
    main()
