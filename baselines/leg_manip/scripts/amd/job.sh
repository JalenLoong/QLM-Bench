#!/usr/bin/env bash
# Body of planner.sbatch (mode run) and publish.sbatch (mode publish). See AMD_RUN.md.
#
#   bash scripts/amd/job.sh run|publish
#
# Settings (environment variables of the submitting shell):
#   LEGMANIP_BASE_PYTHON  python with ROCm torch (required)
#   LEGMANIP_SECRETS      chmod-600 file with HF_TOKEN= and WANDB_API_KEY= (required;
#                         "none" uses the ambient login)
#   LEGMANIP_ENV_SETUP    script sourced first, e.g. the cluster's env/rocm.sh
#   LEGMANIP_TAG          run name; resubmitting the same tag resumes it [dp3-20261029]
#   LEGMANIP_WORK         shared work dir (venv, runs)          [/shared/$USER/legmanip]
#   LEGMANIP_ARGS         extra driver flags, e.g. "--upload dryrun"
set -uo pipefail

mode=${1:?usage: job.sh run|publish}
project=${LEGMANIP_PROJECT_DIR:-${SLURM_SUBMIT_DIR:-$PWD}}
tag=${LEGMANIP_TAG:-dp3-20261029}
work=${LEGMANIP_WORK:-/shared/$USER/legmanip}
venv=${LEGMANIP_VENV:-$work/env/legmanip-amd}
scratch=${LEGMANIP_SCRATCH:-${TMPDIR:-/tmp}/legmanip-${SLURM_JOB_ID:-local}}
slurm_log=${LEGMANIP_SLURM_LOG:-}
base=${LEGMANIP_BASE_PYTHON:-}
read -r -a extra <<<"${LEGMANIP_ARGS:-}"

fail() {
  echo "[job] FAILED at $1: $2"
  if [[ -n $base && -x $base ]]; then
    "$base" "$project/scripts/amd/report_failure.py" \
      --tag "$tag" --stage "$1" --log "$slurm_log" || true
  fi
  exit 1
}

echo "[job] $(date -Is) host $(hostname) job ${SLURM_JOB_ID:-none} tag $tag mode $mode"
[[ $mode == run || $mode == publish ]] || fail checkout "mode must be run or publish"
grep -q '^name = "leg-manip"' "$project/pyproject.toml" 2>/dev/null ||
  fail checkout "submit from baselines/leg_manip (no leg-manip pyproject in $project)"
commit=$(git -C "$project" rev-parse HEAD 2>/dev/null || echo unknown)
export LEGMANIP_SOURCE_COMMIT=$commit
echo "[job] source $commit project $project"

# 1. Cluster environment (ROCm libraries etc.), as the cluster's own jobs do.
if [[ -n ${LEGMANIP_ENV_SETUP:-} ]]; then
  [[ -r $LEGMANIP_ENV_SETUP ]] || fail env-setup "cannot read $LEGMANIP_ENV_SETUP"
  set +u
  # shellcheck source=/dev/null
  . "$LEGMANIP_ENV_SETUP" || fail env-setup "$LEGMANIP_ENV_SETUP returned an error"
  set -u
  echo "[job] sourced $LEGMANIP_ENV_SETUP"
fi
# Our venv must not be shadowed by another environment's packages.
cleared=()
for var in PYTHONPATH PYTHONHOME; do
  if [[ -n ${!var:-} ]]; then
    cleared+=("$var")
    unset "$var"
  fi
done
export LEGMANIP_CLEARED_VARS="${cleared[*]}"
[[ ${#cleared[@]} -eq 0 ]] || echo "[job] cleared ${cleared[*]} for the job venv"

# 2. The submitter's credentials, loaded after the environment so they win.
. "$project/scripts/amd/load_secrets.sh"
secrets=${LEGMANIP_SECRETS:-}
if [[ $secrets == none ]]; then
  echo "[job] LEGMANIP_SECRETS=none: using the ambient HF / W&B login"
  export LEGMANIP_SECRET_KEYS=""
elif [[ -n $secrets ]]; then
  legmanip_load_secrets "$secrets" || fail secrets "could not load $secrets"
else
  fail secrets "set LEGMANIP_SECRETS to the submitter's credential file (see AMD_RUN.md)"
fi
unset HUGGING_FACE_HUB_TOKEN

[[ -n $base ]] || fail base-python "set LEGMANIP_BASE_PYTHON to a python with ROCm torch"
[[ -x $base ]] || fail base-python "LEGMANIP_BASE_PYTHON not executable: $base"

# 3. Restrict ROCm to this job's GPUs if SLURM did not export a visibility list.
if [[ $mode == run && -z ${ROCR_VISIBLE_DEVICES:-}${HIP_VISIBLE_DEVICES:-}${CUDA_VISIBLE_DEVICES:-} &&
  -n ${SLURM_JOB_GPUS:-} ]]; then
  export ROCR_VISIBLE_DEVICES=$SLURM_JOB_GPUS
fi
echo "[job] GPUs: SLURM_JOB_GPUS=${SLURM_JOB_GPUS:-} ROCR=${ROCR_VISIBLE_DEVICES:-}" \
  "HIP=${HIP_VISIBLE_DEVICES:-} CUDA=${CUDA_VISIBLE_DEVICES:-}"

mkdir -p "$work" "$scratch" || fail setup "cannot create $work or $scratch"
# Node-local caches: HF downloads, extracted data, MIOpen kernels and databases.
export HF_HUB_CACHE=$scratch/hf-cache
export HF_HUB_DISABLE_PROGRESS_BARS=1
export MIOPEN_USER_DB_PATH=$scratch/miopen
export MIOPEN_CUSTOM_CACHE_DIR=$scratch/miopen
export PYTHONUNBUFFERED=1

LEGMANIP_BASE_PYTHON=$base LEGMANIP_VENV=$venv \
  bash "$project/scripts/amd/setup_env.sh" "$project" || fail setup "venv setup failed"

"$venv/bin/python" -m leg_manip.planner.cluster "$mode" \
  --tag "$tag" --work "$work" --scratch "$scratch" "${extra[@]}"
status=$?
report=$work/runs/$tag/job_report.json
if [[ $status -ne 0 && ! -f $report ]]; then
  fail driver "driver exited $status before writing $report"
fi
rm -rf "$scratch"
echo "[job] $(date -Is) exit $status; report $report"
exit $status
