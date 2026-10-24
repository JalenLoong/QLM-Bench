---
id: OPD-001
type: exec-plan
status: completed
source_map: []
---
# OPD-v4 implementation

## Purpose and boundaries
User authorized implementation on 2026-10-22. Independent WAM native-FM two-stage
OPD and QLM CPU-only persistent training interface. WAM parent e26d1ef0db9423af2e797abca8026af4bdec495e;
QLM parent 5954235ae75d787eef6af44d58594fd48bde51be. No old OPD imports, AMD access,
formal training, full-5B local load, publication, or resuming paused evaluations.

## Fixed decisions
SFT step5000/4af42de1ce-full at HF 6b8620888b119896866e22c27eff8b6f9f50a520;
manifest 84ddb4bc9332f78ceb3d20c17065cc5c8652f034541c2253e6d3e803df19e717.
Ten tasks; train800 reset pool only. Native9/state=video/360p contracts retained.
LoRA256; native full-denoise state2/action4; eight streams times three chunks;
5 fake updates then 1 student update, 200 successful student updates.
CPU-only Native physics/RAMBO/OSMesa; actual feedback after every chunk.
Round-boundary learner recovery opens a new segment with continuity_break.

## Milestones and progress
- [x] Isolated branches and baseline identity verified.
- [x] Roles, sampler, scoring, losses and immutable history.
- [x] QLM train-only pool, CPU worker, feedback stop hook and WAM coordinator.
- [x] Learner/DDP, recovery/export and administrator entrypoints.
- [x] CPU/tiny/real CPU-worker checks, docs/import regression and handoff.

## Validation
Analytic gradient and full-chain tests; cross-window replay; detach/ownership;
terminal/partial/retry/stop fixtures; CPU Gloo equivalence and recovery/export.
Bounded one-worker real QLM diagnostic, at most two rounds and 600 wall seconds.
Optional GPU module diagnostics: <=4GiB, <=120s each, <=600s total.
Full models, ROCm/RCCL and eight streams remain AMD-only future evidence.

## Recovery and evidence
Do not repeat physical effects or completed learner rounds on request retries.
Diagnostic outputs use a new workspace audit directory; original evidence is immutable.
No W&B upload from local diagnostics. This active plan is updated during implementation.

## Discoveries and current evidence — 2026-10-22
- Actual approved checkpoint headers:841 tensors,180 targets,456130560 LoRA parameters per role; no full model loaded.
- Frozen portable train pool:800 records,80/task,held-out excluded;1GiB new staging,original sources immutable.
- CPU core/stream/recovery/AC tests passed; two-rank Gloo versus explicit mean-gradient updates: max parameter error0.
- Host GPU tiny two rounds passed (reserved27262976bytes); one actual3072x3072 Q Linear+LoRA256 passed (reserved85983232bytes).
- Actual NativeCPU/RAMBOCPU/OSMesa mock-policy stream:6chunks,1reset,2mock updates,14frozenRPC waits,39.50s. No WAM inference or real optimizer in this physics diagnostic.
- Sandbox forbids sockets; CPU RPC/Gloo and real worker were run on host with GPUs hidden. No dependency installation.
- QLM worktree post-checkout LFS hook reported missing git-lfs on PATH; checkout/branch were verified complete; hook unchanged.
- Next: finalize config/admin/current docs, run complete affected CPU/docs/import checks, inspect final diffs and archive paired local-implementation records. AMD/full-model/200-update/evaluation remain not_run.

## Local implementation delivery —2026-10-22
All planned code/config/admin entries and local checks completed. Final WAM runtime
source f048b5b16819f38dda469c2a1b6119e524431474ed7336bc71bd45b2bf031e4b;
QLM source b2355f72f15d52dbd7beb6d869b6f6b8109540ed6b90c41afd97b8a0758158ff.
WAM188 CPU passed/20legacy fixture skipped;QLM260passed/13optional skipped.
Two-rank Gloo mean-gradient equivalence error0;bounded GPU and actual CPU mock stream
passed. AMD/full5B/eight-stream/200-update/evaluation remain not_run and independently
gated. No publication or source commit. This completion covers the authorized local
implementation scope,not target-hardware acceptance or policy performance.
