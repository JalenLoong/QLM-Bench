"""Record a job failure in W&B before the planner venv exists.

Used by planner.sbatch when the venv setup or the driver fails before it wrote
its own report. Needs only the standard library and wandb, so it runs on the
cluster's base python.

    python report_failure.py --tag dp3-20261029 --stage setup --log job.out
"""

import argparse
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--log", default="")
    parser.add_argument("--entity", default="junlinlong-the-university-of-sydney")
    parser.add_argument("--project", default="WAM-Policy")
    args = parser.parse_args()
    log = Path(args.log) if args.log else None
    tail = ""
    if log is not None and log.is_file():
        tail = "\n".join(log.read_text(errors="replace").splitlines()[-60:])
    print(f"[report] {args.tag} failed at {args.stage}")
    try:
        import wandb

        run = wandb.init(
            project=args.project,
            entity=args.entity,
            group=f"planner-{args.tag}",
            job_type="amd-pipeline-failure",
            name=f"dp3-pipeline-{args.tag}-failed-{args.stage}",
            tags=["dp3", "amd", args.tag],
            config={"slurm_job_id": os.environ.get("SLURM_JOB_ID")},
        )
        run.summary.update(
            {
                "pipeline/status": "failed",
                "failure/stage": args.stage,
                "failure/log_tail": tail[-8000:],
            }
        )
        run.finish(exit_code=1)
    except Exception as exc:
        print(f"[report] W&B unavailable: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
