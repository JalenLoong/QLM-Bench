---
id: QLM-SIM-003
type: exec-plan
status: completed
source_map:
  - scripts/mujoco/probe_checkpoint_rgb.py
---

# RAMBO checkpoint evidence before original-asset migration

## Context and scope
Worktree migration/mujoco-foundation at189545f plus retained local P0–P2 changes.
User explicitly pauses asset migration and prioritizes original RAMBO/MuJoCo verification.
The two existing six-second two-world probes pass but did not retain RGB video.
No asset source or runtime asset was changed by the interrupted migration audit.
The existing P2 procedural-asset runs remain engineering evidence, not migration acceptance.

## Milestones
1. Audit original checkpoint, existing acceptance and source binding.
2. Add a bounded evidence entry using the unchanged controller/Go2 model. Save actual
   RGB/snapshots/telemetry under a new workspace audit root.
3. Run Native then CUDA sequentially; preserve failures and quantify each motion phase.
4. Decode/inspect media, check reset/source identities and issue a narrowly scoped report.

## Progress
- [x]2026-10-12: Original checkpoint SHA256 and six-second Native/CUDA receipts audited.
- [x]2026-10-12: Migration stopped before asset/source changes; reserve QLM-SIM-003.
- [x] Implemented evidence entry; Native-a01 and CUDA-a02 completed18s actual recordings.
- [x] Decoded all videos; source/normalizer/tensor/snapshot/reset identities and actual RGB verified.

## Validation and stopping
Dual RGB50Hz and observer25Hz remain separate. The18-second preregistered schedule is
settle0–2, stand2–4, forward4–7, lateral7–10, yaw10–13, FL extension13–16 and return16–18.
Report transient-aware phase means, drift, orientation and EEF error without hiding
tracking failures behind a no-fall result. Failed physical/renderer attempts stay local
and are not retried with altered conditions to select success.

## Evidence and next action
Workspace runs/audit/rambo-mujoco-checkpoint-20261012/. W&B not_run; all evidence local.
After verification, stop and explain RAMBO readiness before resuming any asset migration.

## Actual results and interpretation

Both engines completed9000physics/1800controller/900commands, preserving original
405D inputs,18D actor residuals and9000×12motor efforts. Each retained900frames per
policy camera50Hz and450observer frames25Hz, plus independent terminal18s PNGs.
Checkpoint, actor parameters and original normalizers are byte-identified and unchanged.
Native forward/lateral mean velocities0.141/0.104m/s; CUDA0.142/0.103m/s for
0.15/0.10 commands. FL-extension mean position errors12.3/12.4mm. Original fall
criteria were not triggered; explicit zero-time reset checks passed.

Yaw mean rates0.073/0.076rad/s for0.15 requested are weak tracking, not an accepted
Isaac-equivalent tracking result. This diagnostic proves basic physical execution,
not complete portability/performance or long-horizon stability. Comparison to the
original Isaac response under this exact schedule remains a future investigation.

CUDA-a01 failed before any actions because the sandbox could not see CUDA; retained.
CUDA-a02 used the already-authorized host GPU path with the same commands/model/weights.
Native EGL used Mesa llvmpipe; CUDA EGL used NVIDIA. No throughput or pixel-equivalence
claim is made from this controller diagnostic.

Evidence: workspace runs/audit/rambo-mujoco-checkpoint-20261012/report.json,
review.html and per-attempt identity/result/media-validation-final.json. Source/docs
checks pass. No controller/asset/environment change, retraining, WAM run, accepted
demonstration, AMD, commit/push or external upload. Asset migration remains paused.
