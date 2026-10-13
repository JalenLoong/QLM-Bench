---
id: QLM-MUJOCO-DECISION
type: decision
status: accepted
source_map: []
---

# MuJoCo P0–P2 implementation — accepted 2026-10-12

## Authority and scope
User-approved P0–P2 only: dependency audit, simulator-independent RAMBOCore,
Native/CUDA-MJWarp foundations, Native rendering and three-task physical/data/live
engineering validation. No seven-task expansion, formal demonstrations, SFT, AMD
access, remote submission, commit/push or publication in this work package.
Original execution-plan SHA256: `1464e0365afa53d7ba74bb7fa0d1095debe71e08e99d498650e6606ce4d1d719`. A byte-preserved copy and source baseline
are in workspace `runs/audit/mujoco-p0-p2-20261012/`.

## Accepted decisions
- Native MuJoCo rendering is the common production route. OSMesa is the reference;
  local EGL is admitted only after same-state visual equivalence. AMD prepares
  OSMesa without assuming GPU OpenGL. MJWarp batch rendering is deferred.
- MJWarp alone advances physics. A separate render mirror synchronizes the entire
  robot/object articulation and camera/scene state at one completed timestamp.
  Rendering/derived refresh cannot step physics. Reject stale world/reset/model identities.
- Preserve dual1280x720 RGB50Hz, model12.5Hz, physics/controller/command500/100/50Hz,
  Go2/FL/native9 absolute target, requested versus executed force-zero, original
  controller semantics, terminal-before-reset and completed command history.
- Preserve Isaac reference assets/results. New independently versioned MuJoCo assets
  are allowed when migration/license/physics requires; retain interaction, success
  predicates and task difficulty. Real contact only; no teleport, hidden attachment
  or assistance forces. Freeze asset pools before formal pilots and revalidate
  affected pilots after semantic changes.
- Benchmark OSMesa/EGL correctness, state transfer, rendering, encoding, disk,
  CPU/GPU memory and projected1000-episode cost before large-scale collection.
  50Hz is simulation cadence, not a real-time claim. Report unacceptable differences
  or throughput instead of weakening camera/preprocessing contracts.
- Later SFT: fresh fixed LingBot native→native9+10D, v3 first; v2 optional. Preserve
  Canonical v2.1-style layout, versioned provenance, task/episode/window sampling,
  train-only normalizers and independent simulator/model environments.
- P0–P2 diagnostic clips never automatically become accepted demonstrations.
  Original normalizers/checkpoints and historical locks/receipts remain immutable.

## Stage gates
P0: actual source/Work IDs/interfaces/candidate locks/resource gaps documented.
P1: same-input obs/actor/IK/QP/motor regression; Native and CUDA standing/walking/
turning/FL actions, real contact, exact tick scheduling, reset and two-world isolation.
P2: timestamp-correct render mirror; OSMesa/EGL images and throughput; Push/Press/Lift
expert success and terminal/error paths; actual Raw/Canonical readback; real v3
multi-chunk feedback, eviction, reset and physics freeze. Task SR of the old WAM
checkpoint is not an acceptance criterion.
Later P3–P6 and S0–S5/F1–F4 remain planned, not executed by this package.

## Stop conditions
Stop the affected path and report if changing action/observation/data contracts,
main physics/render route, RAMBO training, task semantics/difficulty, or if rendering,
resource or reproducibility defects imply major rework. Routine implementation is
owned by the implementer. AMD compatibility remains not_run until administrator smoke.
