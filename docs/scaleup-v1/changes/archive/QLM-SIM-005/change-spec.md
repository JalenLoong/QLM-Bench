---
id: QLM-SIM-005
type: change
status: completed
source_map: []
---

# Repair all MuJoCo alignment review findings

## Authority and full scope
The user's active goal is to fix every finding in workspace
`runs/audit/mujoco-alignment-review-r1/report.json` (R01–R10). This explicitly
resumes the asset/camera/physics work previously paused for independent review.
All ten findings remain required; completion is not defined by the first fixes.
Cross-repository consumer work is v3/INFER-004. Use the existing independent
MuJoCo worktrees and preserve all historical source, data, locks and attempts.

## Observable requirements
- R01: derive a versioned robot/physics reference from actual original Isaac
  geometry and runtime mass/inertia/COM/joint/actuator/contact properties. Document
  backend mappings, validate kinematics/actuation/contact and tracking on Native/CUDA;
  do not promote the condim3 diagnostic by target-fitting alone.
- R02: migrate original Box05, industrial button and OASIS basket visual assets,
  materials/UVs, collision and articulation. Preserve task semantics and difficulty,
  with real-contact expert evidence. No primitive substitute counts as completion.
- R03: restore full policy cameras, clipping, original per-task observer25Hz and
  visual rig. Validate actual cross-engine projection fixtures and EGL/OSMesa outputs.
- R04: restore shared original task-state semantics, including reset/progress values.
- R05: publish actual backend/asset/controller/source identities into each local
  Raw/Canonical bundle; no inherited old asset ID for a different resource.
- R06: persist complete/partial/failure/abort evidence independently of whether an
  episode is usable Canonical. Retain actual executed prefixes and terminal snapshots.
- R07: rerun actual WAM v3 with original weights and persistent actual RGB/state,
  feedback/KV/reset/terminal/clock evidence on all three repaired tasks.
- R08: connect backend-neutral task, collection, recorder/converter and evaluation
  contracts to public QLM entries, retaining explicit optional simulator loading.
- R09: provide portable dependency closure and full profile identity; enforce
  model-parameter freezing or synchronization; record actual GL renderer identities.
- R10: provide isolated lane/case RNG and lifecycle, verify contact measurement
  cadence, real-asset single/batch correctness and representative throughput.
  Complete the local dependency/feature matrix; AMD execution remains not_run under
  the existing administrator-only boundary, not an assumed pass.

## Invariants and exclusions
Keep original RAMBO checkpoint/405D/18D semantics, Go2/FL/native9 force-zero,
500/100/50Hz, dual720p RGB, model12.5Hz, root-link/body10D and terminal-before-reset.
No full-model/RAMBO training, ten-task expansion,1000-demo synthesis, AMD access,
source commit/push or external publication is implied. New engineering artifacts
are not formal demonstrations. Escalate only an irreducible high-impact change to
these frozen requirements, as already requested by the user.

## Completion evidence
The paired plan and per-finding ledger must link actual source, CPU tests, artifact
readback and necessary Native/CUDA/Isaac/WAM runs. Numerical, protocol, physical,
visual, dataset and platform gates are distinct. A broad completed claim requires
all applicable R01–R10 gates, not just no-fall rollouts or schema validation.

## Local completion — 2026-10-13
All applicable local requirements are verified in the paired archived plan and
workspace runs/audit/mujoco-alignment-repair-v1/completion-audit-a02/audit.json.
Read the current guide for explicit backend differences, EGL admission failures,
production-cost caveats and AMD not_run. No blanket physical/visual equivalence or
formal data/model evaluation claim is made.
