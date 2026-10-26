---
id: QLM-RL-V2-DUAL-TASK
type: current-design
status: accepted
source_map:
  - src/qlm_bench/backends/mujoco/rl_v2/replay.py
  - src/qlm_bench/rl_v2/worker.py
  - src/qlm_bench/rl_v2/verification.py
  - src/qlm_bench/rl_v2/validation.py
---

Current GitHub source delivery is recorded in [publication status](rl-v2-source-publication.md). Earlier local-only statements below retain their original execution scope.
# Push Box and Sweep Block RL environment routing

QLM-SIM-026 pairs with WAM mujoco-v2/ALG-005. Replay, verification, the anchor worker
and held-out validation explicitly create the selected task through the existing QLM
runtime factory, with NativeCPU/RAMBOCPU, trace_only=False and OSMesa. This selects
RemainingRuntime/RemainingTaskState for Sweep and preserves the existing Push runtime.
Sweep scene profiles own their goals; missing Push-specific goal overlays are not
invented. Existing task predicates, physics and force-zero contracts remain unchanged.

Validation records carry task_id; episode membership and prompt are checked against
that task's original release. Each task uses its own ten validation normal initial
states. Full reference/calibration preparation remains task-specific. WAM's shared
engineering smoke pair is not a shared trajectory or mixed-task training buffer.

A real Sweep16-command continuation repeated after serialized snapshot restoration
has qpos/qvel/RGB error0. The first diagnostic's wrong-runtime failure is retained.
This is bounded engineering evidence, not a formal GT reference or task success claim.
No AMD, formal RL/validation, remote publication or commit/push was executed. Evidence:
workspace runs/audit/rl-v2-dual-task-20261026-v1/completion.json.
