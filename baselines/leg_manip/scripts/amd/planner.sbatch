#!/usr/bin/env bash
#SBATCH --job-name=legmanip-dp3
#SBATCH --partition=mi355x
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:6
#SBATCH --cpus-per-task=48
#SBATCH --mem=384G
#SBATCH --time=08:00:00
#SBATCH --output=legmanip-dp3-%j.out
#
# Leg-Manip DP3 planner training on MI355X: 2 tasks x 3 seeds spread over the
# allocated GPUs (one run per GPU by default), then upload of the EMA exports to
# Hugging Face. Submit from baselines/leg_manip; settings and steps in AMD_RUN.md.
# Two GPUs (three runs each) instead:
#   sbatch --gres=gpu:2 --cpus-per-task=16 --mem=128G --time=12:00:00 \
#     scripts/amd/planner.sbatch
dir=${LEGMANIP_PROJECT_DIR:-${SLURM_SUBMIT_DIR:-$PWD}}
export LEGMANIP_SLURM_LOG=$dir/legmanip-dp3-${SLURM_JOB_ID:-local}.out
exec bash "$dir/scripts/amd/job.sh" run
