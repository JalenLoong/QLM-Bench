---
id: QLM-SIM-008
type: change
status: completed
source_map: []
---

# STEP support impact and bounded performance assessment

User asks whether replacing procedural support with supplied STEP geometry changes
camera/physics/visual semantics or slows rollout/data synthesis. Compare unchanged
old v1-ethan-rig-a01 and new v1-step-rig-a01 packs; do not modify either resources,
camera/data/controller/model interfaces or source STEP.

Read prior actual optical/physical/registration evidence. Measure model/triangle
size,initialization,RSS,isolated OSMesa dual/Observer rendering at the same state,
Native/CUDA stepping and short actual controller/Raw/Canonical capture. Serial GPU
runs,counterbalanced orders,warmup and stable timings separate startup from execution.
Three tasks for rendering;Push and heavy Basket for paired bounded capture.
All new data is engineering diagnostic,not demonstration/pilot/release/task SR.

Acceptance: identical inputs/resource identity and recorded dependencies/order;
render contains real RGB with original1280x720 cameras; cost breakdown avoids
double-counting observation/render; disclose short-run/noise/batch/AMD limitations.
Report negative effects and recommendations without automatically simplifying
meshes or changing calibration. No training,AMD,publication,commit/push.

Evidence: workspace runs/audit/step-camera-rig-impact-20261013-v1/.

## Actual completion
All12render/8physics units and4recovered completecapture units passed. The first
capture Path-serialization wrapper failure is preserved; valid microbenchmarks
were not rerun. Read decisions/step-rig-impact.md and the workspace report/
analysis/completion for timings,source identities,CPU RAM,shortCUDA statevariation
and limits. Camera/mesh/runtime/training inputs were not altered or optimized.
No production capacity,AMD,EGL,long-horizon SR orWAM latency claim.
