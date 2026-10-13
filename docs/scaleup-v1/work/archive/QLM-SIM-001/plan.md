---
id: QLM-SIM-001
type: exec-plan
status: completed
source_map: []
---

# P1 RAMBOCore and Native/CUDA physics

Authority: [accepted decisions](../../../decisions/mujoco-p0-p2.md).

## Progress
- [x] Reserved before implementation.
- [x] Implement and validate the stage-specific gates.
- [x] Record actual evidence and archive only after all required gates pass.

## Discoveries / Decision Log
QLM source189545f includes scale-up and continuous Push expert. Historical shared-v2
registry is not modified. WAM counterpart: v3/INFRA-002 and v3/INFER-003.

## Evidence and recovery
Workspace runs/audit/mujoco-p0-p2-20261012; preserve failed attempts.
Use independent worktree and explicit source binding; original checkouts stay unchanged.
Hardware acceptance: not_run at reservation.


## Actual progress — 2026-10-12

405D/18D actor and numerical core extracted; Isaac original/candidate QP comparison passed. Native/CUDA three-task experts passed with source-mass-preserving fixed foot frames. Integer controller clock and measured normal-force histories are covered by tests. Final two-world CUDA acceptance is running.

Evidence: workspace runs/audit/mujoco-p0-p2-20261012/report.json.
Not_run: AMD, formal pilot asset freeze,1000demonstrations, new SFT, benchmark, publication.

## Completion
All declared local P0–P2 gates pass; workspace completion.json/report.json bind the actual attempts.
GPU memory and single-world throughput are measured. AMD/formal pilots/SFT/benchmark/publication remain not_run.
