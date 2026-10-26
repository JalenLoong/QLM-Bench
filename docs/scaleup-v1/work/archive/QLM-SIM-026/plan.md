---
id: QLM-SIM-026
type: exec-plan
status: completed
source_map: []
---
# Independent task-specific RL-v2

User requests an additional Sweep Block task on the existing RL branches, independent of Push Box. Keep numerical algorithm/training configuration and parent quadrupedal v2 SFT5000 identical. Separate task pools, prompts, calibration, optimizer/EMA, checkpoints, validation and HF namespaces. Preserve the fixed Push selection; Sweep uses matching 2 clean +8 randomized train-only stratified selection, seed42.

Latest user instruction: do not duplicate shared engineering smoke tests. One single/eight-GPU smoke pair provides source/parent/recipe/hardware evidence to both tasks; each task still prepares its own reference/calibration and preflight. A combined Slurm DAG has16 jobs, no cross-task train/export/publish dependency, and one common smoke pair. Bounded local tests only; no AMD/Slurm submission, formal RL or remote writes/commit/push.

## Completed — 2026-10-26

Implemented separate Push Box/Sweep Block task bindings and outputs from the identical quadrupedal SFT5000 parent, with the numerical RL core unchanged. Sixteen-job combined DAG runs only one shared single/eight-card smoke pair. Separate task calibration/preflight and independent train/export/publish/eval tails; task-specific HF namespace and cross-task checkpoint rejection. RL physical entries use QLM's accepted task factory, retaining original predicates.

Validation: WAM218 unique passes/21 optional skips; QLM core/validation271 passes/13 skips, socket restrictions covered on host. Real-resource dual/no-git configuration,40 scene packs,two validation memberships,16-job fake Slurm and separate fake HF publication pass. Real Push/Sweep16-command snapshot replay both have qpos/qvel/RGB error0. Core algorithm files byte-identical. Evidence: workspace runs/audit/rl-v2-dual-task-20261026-v1/completion.json.

Not run: AMD/real Slurm, full two-task GT references/calibration, full5B backward, formal RL/validation, remote writes, commit/push.
