---
id: QLM-SIM-004
type: exec-plan
status: completed
source_map:
  - scripts/rambo/compare_controller_isaac.py
  - scripts/mujoco/probe_checkpoint_rgb.py
---

# Isaac reference for the original RAMBO checkpoint

## Context
Original controller source remains at workspace repos/QLM-Bench-scaleup-push_box,
HEAD189545f. Relevant original RAMBO/CRL2 files are unchanged from that commit.
New MuJoCo source is migration/mujoco-foundation, using the same checkpoint. QLM-SIM-003
measured yaw0.073/0.076rad/s versus0.15, forward0.141/0.142m/s versus0.15 and
lateral0.104/0.103m/s versus0.10 on Native/CUDA. Task asset migration is paused.

## Milestones and progress
- [x]2026-10-12: Verify independent reference source and original checkpoint routing.
- [x] Reserve and implement the independent original-source Isaac probe.
- [x] Isaac-a05 completed18s original controller execution and actual RGB; four0-action diagnostic failures retained.
- [x] Compared raw phase means, time series and quaternion yaw; tested contact-only interventions on Native/CUDA.
- [x] Decoded actual videos, verified original source/weights/actor equivalence and archived the comparison.

## Runtime/recovery
Use original worktree run60 launcher with explicit new script/output, unchanged
shared venv and user-authorized host GPU. EULA acceptance is process-scoped under
the user's prior all-task authorization. Source, module imports, resolved cfg and
weights are verified in the attempt; no original source/checkpoint is modified.
Runtime/renderer failures remain evidence and cannot be silently treated as policy
failures. Local W&B not_run and no external operations.

## Next action / evidence
New audit root runs/audit/rambo-isaac-mujoco-comparison-20261012/. Full recordings
and telemetry remain separate from QLM-SIM-003, whose original bytes are retained.
Do not resume migration or launch retraining after the analysis without user steering.

## Independent reference discovery

Isaac-a05 completed18s original source/CRL2 and actual Camera/RTX observer capture.
Yaw mean0.142906rad/s versus0.15; forward0.148858m/s versus0.15 and lateral
0.099587m/s versus0.10. Thus the MuJoCo approximately-half yaw response is a
migration regression, not the same nominal original-policy tracking deficit.
Four diagnostic startup attempts executed0actions and are retained separately.

Reference robot mass15.019kg differs from Menagerie15.206408kg, and sampled motor
delays differ; neither identifies pure solver causality. A specific contact-model
difference is visible in the actual MuJoCo data: foot priority1 overrides the
floor's condim3 with condim6 and friction[0.8,0.8,0.02,0.01,0.01]. This introduces
explicit torsional/rolling constraints. A versioned diagnostic XML changes ONLY
foot condim6→3, preserving sliding/geometry/weights/commands/cameras. Its current
Native18s attempt is not a production-profile change or task asset migration.
Evaluate the contact-only effect before drawing a retraining recommendation.

## Completed causal diagnostic and decision assessment

Isaac original yaw0.142906rad/s; existing Native/CUDA foot-condim6 yaw
0.073300/0.075730. Contact-only condim3 diagnostics restore0.133064/0.136295.
The intervention recovers85.9%/90.2% of the measured gap to Isaac. Quaternion-derived
yaw rates corroborate the body-velocity measurements, excluding a simple reported
angular-velocity factor error. Body/geometry/inertia/motor/camera model arrays are
identical between the MuJoCo profiles except four foot geom_condim entries.

Original Isaac1800×405 inputs replayed through the ported FrozenActor agree with
actual original CRL2 outputs to maximum1.67e-6, with no weight/normalizer update.
Actual18s videos decode450observer/preview frames per run and900dual-policy frames
for MuJoCo runs. Independent Isaac records9000physics rows and1800control/QP rows.
The Native contact diagnostic intentionally reuses the original QLM-SIM-003 entry;
its parent diagnostic profile and this QLM-SIM-004 receipt own the new intervention.

Recommendation: do not start RAMBO retraining now. The nominal yaw regression is
primarily a migration contact-profile effect, not an original checkpoint limitation
or proof of unavoidable MuJoCo solver degradation. Contact3 is NOT production-ready:
Native/CUDA lateral means0.115771/0.117064m/s exceed0.10. Robot mass, armature,
contact compliance/geometry and sampled delay differences remain; align and validate
physical profiles and task/longer/bidirectional behavior before deciding on training.
This is a single-seed bounded engineering comparison, not a formal benchmark.

Evidence: workspace runs/audit/rambo-isaac-mujoco-comparison-20261012/report.json,
review.html, tracking_comparison.png, actor-same-input.json, contact-only-invariants.json
and all actual attempt media/telemetry. Source/docs/import checks pass. The diagnostic
models were not promoted into assets/mujoco/p0-v1. No original source or controller
weights were modified, and no training, accepted demonstration, AMD, commit/push or
external upload occurred. Task asset migration and camera repair remain paused.
