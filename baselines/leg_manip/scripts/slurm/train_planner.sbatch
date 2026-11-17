#!/usr/bin/env bash
# Generic Slurm example: train the DP3 planner of one task with three seeds, one GPU per seed.
# Adjust the partition/resources for your cluster; the planner needs no simulator (CUDA or ROCm PyTorch).
#   sbatch --partition=<partition> scripts/slurm/train_planner.sbatch <demos.zarr> [epochs]
#SBATCH --job-name=legmanip-dp3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:3
#SBATCH --cpus-per-task=24
#SBATCH --time=08:00:00
#SBATCH --output=legmanip-dp3-%j.out
set -euo pipefail
DATA="${1:?demonstration zarr}"; EPOCHS="${2:-500}"
cd "${SLURM_SUBMIT_DIR:-$PWD}"
for SEED in 0 1 2; do
  CUDA_VISIBLE_DEVICES=$SEED HIP_VISIBLE_DEVICES=$SEED lm-train-planner --data "$DATA" --seed "$SEED" \
      --num-epochs "$EPOCHS" --wandb-mode "${WANDB_MODE:-offline}" &
done
wait
