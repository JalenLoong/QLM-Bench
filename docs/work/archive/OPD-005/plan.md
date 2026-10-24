---
id: OPD-005
type: exec-plan
status: completed
source_map: []
---
# Native1/2 mixed-task implementation

User authorized implementation of400S/1200F/9600contexts,3F→1S,checkpoint every100,
protected full S200/S400 plus latest2. Reuse existing OPD worktrees and source.
Global confirmed-start task scheduling,CPU-only QLM,independent training horizons,
sampler/restore/export identity and documentation are in scope.

- [x] Sampler/config/learner and artifact identity.
- [x] QLM training profile,transactional scheduler and streaming integration.
- [x] Checkpoint/control-state recovery and administrator entrypoints.
- [x] CPU/Gloo and bounded local smoke,governance/docs and delivery.

No AMD/full5B/formal training/commit/push/PR or evaluation restarts. Preserve old
archives,model/data/resource identities. Evidence: workspace
runs/audit/opd-v4-mixed-task-implementation-20261024-v1/.

## Outcomes and evidence

Completed local implementation and approved bounded validation. WAM make check201pass/21skip;
QLM suite282pass/13skip plus one8-process scheduler regression. Two-rank Gloo matches explicit
mean gradients exactly and common-abort cases pass. Tiny CUDA2rounds uses26MiB reserved in3.145s.
Real NativeCPU/RAMBOCPU/OSMesa mock policy6chunks/2mock updates/1reset/14frozen RPC passed;
zero WAM inference. First OSMesa-import failure retained; existing library path resolved it,
no dependencies installed. Actual SFT/resource/pool hashes and control CLI portability passed.
AMD/full5B/real8streams/formal400S/performance not_run; no commit/push/PR.
