#!/usr/bin/env bash
# Low-level controller (PPO + estimator) as trained for the baseline: a warm-start chain, not a single run.
#   stage 1  Lift curriculum            LegManip-Lift-Go2   2000 iterations from scratch
#   stage 2  Track, all rewards except the heading terms, from stage 1, policy noise reset to 0.5, 6000 iterations
#   stage 3  + base_heading (weight 0.5), from stage 2, noise kept, 3000 iterations
#   stage 4  + base_heading_dir (weight 1.0, the repository default), from stage 3, noise kept, 3000 iterations
# Each stage is checked with the behaviour gates before the next one starts.
# Requires the `sim` extra (NVIDIA GPU, mjlab + MuJoCo Warp).  Usage: scripts/train_controller.sh <run prefix>
set -euo pipefail
P="${1:?run name prefix (must start with leg-manip-)}"; ENVS="${LEGMANIP_NUM_ENVS:-4096}"; SEED="${LEGMANIP_SEED:-0}"
LOGGER="${LEGMANIP_LOGGER:-tensorboard}"   # or wandb (set WANDB_ENTITY / --agent.wandb-project yourself)
last() { ls -1 "logs/rsl_rl/$1"/*"$2"*/model_*.pt | sort -V | tail -1; }
common=(--env.scene.num-envs "$ENVS" --agent.seed "$SEED" --agent.logger "$LOGGER")

uv run --no-sync train LegManip-Lift-Go2 "${common[@]}" --agent.max-iterations 2000 --agent.run-name "$P-lift"
L=$(last legmanip_lift_go2 "$P-lift")
uv run --no-sync python -m leg_manip.eval.lift --checkpoint "$L" --seed 1000 --out "logs/$P-lift-gate.json"

uv run --no-sync train LegManip-Track-Go2 "${common[@]}" --agent.max-iterations 6000 --agent.run-name "$P-track" \
    --agent.init-checkpoint "$L" --agent.init-noise-std 0.5 \
    --env.rewards.base-heading.weight 0.0 --env.rewards.base-heading-dir.weight 0.0
T=$(last legmanip_track_go2 "$P-track")
uv run --no-sync python -m leg_manip.eval.track --checkpoint "$T" --out "logs/$P-track-gate.json"

uv run --no-sync train LegManip-Track-Go2 "${common[@]}" --agent.max-iterations 3000 --agent.run-name "$P-heading" \
    --agent.init-checkpoint "$T" --env.rewards.base-heading-dir.weight 0.0
H=$(last legmanip_track_go2 "$P-heading")

uv run --no-sync train LegManip-Track-Go2 "${common[@]}" --agent.max-iterations 3000 --agent.run-name "$P-final" \
    --agent.init-checkpoint "$H"
F=$(last legmanip_track_go2 "$P-final")
uv run --no-sync python -m leg_manip.eval.track --checkpoint "$F" --out "logs/$P-final-gate.json"
echo "controller: $F"
