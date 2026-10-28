#!/usr/bin/env bash
#SBATCH --job-name=legmanip-dp3-publish
#SBATCH --partition=mi355x
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=legmanip-dp3-publish-%j.out
#
# Upload-only job (no GPU): publishes and verifies the EMA exports of an existing
# tag, e.g. after fixing the HF token. Same settings as planner.sbatch.
dir=${LEGMANIP_PROJECT_DIR:-${SLURM_SUBMIT_DIR:-$PWD}}
export LEGMANIP_SLURM_LOG=$dir/legmanip-dp3-publish-${SLURM_JOB_ID:-local}.out
exec bash "$dir/scripts/amd/job.sh" publish
