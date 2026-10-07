---
id: CURRENT-OVERVIEW
type: current
status: accepted
source_map: []
---

> **Later audit correction:** Clean reset-isolation acceptance is withdrawn.
> Root-link reset velocities carry over at9/9 episode boundaries per policy.
> Existing success counts are historical observations; read [the audit](inference-chain-audit.md) before reuse.

# QLM-Bench current scope

QLM-Bench owns Isaac quadrupedal loco-manipulation tasks, fixed Go2/FL/native9/RAMBO
execution, dual RGB, scripted demonstrations, Raw/Canonical publication and evaluation
infrastructure. WAM is a separate model-side consumer. Current refactoring work is
tracked by [the generated work index](../work/INDEX.md); active plans distinguish
implemented, artifact-verified, runtime-verified and unpublished work.

## Accepted physical and data baseline

Keep original controller/checkpoint and task geometry/predicates. High-level commands
50Hz, controller100Hz, physics500Hz, Raw/Canonical RGB50Hz, diagnostic observer25Hz.
Native9 uses base vx/vy/yaw rate, absolute FL target xyz, and zero desired force xyz.
Simulation timestamps are authoritative. Raw has N+1 boundaries, Canonical has N
completed action rows, and pre-reset terminal state/RGB is separate; no dummy action.
WAM sampling/grouping is a consumer concern and remains covered by frozen compatibility
profiles. See [contracts](contracts-v2.md) and [dataset contract](adaptation_v2_dataset_contract.md).

Push Box success uses the whole pose-transformed box XY footprint inside the episode
goal, not fallen, held for three50Hz ticks. Lift retains2cm basket clearance/not-fallen/
three-tick semantics and diagnostic ego visibility. Press retains its accepted button
predicate. New conditions and unrelated behavior repairs require a separate Work ID.

## Published demonstrations and consumer admission

DATA-007 fixed revision4b5e0ed9aa04cbc1143774798f63171b27d838a7 contains Push Box
DATA-006-20260916T075451Z:50 episodes,24,335 actions,40/5/5. DATA-011 publication
receipt at05b09b89225759382e28bc3dc586f1cfb755a997 adds separate Lift10/7,042 actions
and Press10/5,194 actions, each8/1/1. These are historical fixed readback revisions;
actual Hub HEAD is checked anew during release staging. First WAM v2/v3 inputs remain
the original Push Box pin. [Publication rules](publication-v2.md) distinguish this
consumer admission from independently usable QLM releases.

## Evidence and current limits

Completed source/data milestones remain in paired archived work records and immutable
workspace receipts. Pilots, failures, interruption, quarantine, model caches/weights
and unapproved asset payloads remain excluded from demonstration publication.
Refactoring does not establish a formal evaluation suite, learned-policy success
or a benchmark score. INFER-001 adds the physical-only [live transport and driver](live-inference.md);
CPU and real model/runtime evidence remain separate. Case reconstruction, simulator regression
and external publication have separate gates; incomplete gates remain explicit.

WAM v2 training context belongs to its branch, and current v3 training status belongs
to WAM v3. QLM installation and normal use require neither WAM checkout nor its model
stack. Historical absolute paths and source hashes stay in original artifacts; new
public resource manifests use portable identities.

## Current visual deployment and evaluation

The accepted16GB deployment and complete local ten-trial results are in
[Push Box first-SFT evaluation](push-box-first-sft-evaluation.md). Use16 Transformer
blocks with CPU BF16 master parameters/CUDA forward plus the original VAE on CPU.
The earlier all-Transformer-GPU/VAE-CPU visual acceptance is withdrawn. Task metrics
apply to the declared nominal scene/seeds; formal benchmark/generalization claims
remain unavailable. Preserve invalid attempts and all first-attempt outcomes.

## Later local reset repair — SIM-003 / 2026-10-07

The user's latest repair request supersedes the earlier deferral for this task.
Current QLM shared reset freshness passed21/21 actual three-task checks, including
controller/public/recorded state and original v3 consumer readback; see
[the accepted reset repair](reset-state-freshness.md). The historical70 demonstrations/caches and
6/10 versus5/10 outcomes remain unchanged. No clean full-policy reevaluation or
new demonstration/training/publication is claimed. Use the repaired QLM source revision recorded by DOC-009; historical
serving pins do not include SIM-003.
