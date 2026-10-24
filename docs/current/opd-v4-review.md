---
id: OPD-V4-INDEPENDENT-REVIEW
type: current-design
status: accepted
source_map:
  - src/qlm_bench/backends/mujoco/training_pool.py
---

> OPD-004修订：本页保留2026-10-22对旧2/4、200-update实现的审核证据。
> 当前正式目标为1/2、400S，见[最新决定与代码差异](opd-v4-documentation-sync.md)。
> 本页历史结果不构成新目标的验证或训练准入。

# OPD-002 independent review

The method scheme and implementation plan were checked against both implementations.
Full native2/4 gradients, detached role-specific history/plan KV,5F→1S accumulation,
normal-round stream continuity and CPU-only worker boundaries were reviewed for that historical implementation.

Fixed receipt-level duplicate accounting,local distributed failure consensus,
authenticated train-only source/reset membership,launcher failure/deadline handling,
and missing per-context raw action/attempt diagnostics. Added focused regressions,
including multi-round checkpoint recomputation beyond eviction and actual tiny CPU
service resume into a new session. Original physics/controller/task criteria were not
modified. See [paired review work](../work/archive/OPD-002/plan.md).

Evidence is in workspace runs/audit/opd-v4-independent-review-20261022-v1/:
report.md,completion.json,pool-verification.json,gloo-failure.json and final regression logs.
The replacement pool SHA is dff729244322f6a1cb4aa7c2d9e73404fe002e0879474ba0190c022644f889a1.
It preserves all original800reset values and resources and carries10authenticated release
manifests plus800reset traces. Existing OPD-001 pools/configurations are historical;
rebuild pools and resolve new source bindings before a later authorized target run.

CPU/tiny evidence does not admit full5B,ROCm/RCCL,eight real streams or formal200updates.
Those checks remain not_run and require separate AMD authorization. This review did not
use GPU or run a new physical rollout,commit/push,or operate other evaluation/decoder jobs.
