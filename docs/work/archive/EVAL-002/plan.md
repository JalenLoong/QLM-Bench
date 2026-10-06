---
id: EVAL-002
type: exec-plan
status: completed
namespace: adaptation-v2
source_map: []
---
# First-SFT Push Box evaluation, ten trials per policy

## Purpose and authorization

The user explicitly requests actual Isaac closed-loop Push Box evaluation of the
first formal v2 and v3 SFT checkpoints,10rollouts each, plus QLM metrics and all
ego/task-centric/observer RGB videos. Use the existing independent inference
worktrees and original step1000 checkpoint identities at HF223634bc64bc225881de80c2ac6e38c1de713a93.
No new training, normalizer fitting, demonstrations or external publication.

## Protocol and compatibility

Local trial evaluation of the reviewed Box05 push-box-v2-2 scene and original
full-footprint/not-fallen/three-policy-tick success predicate.24s simulation horizon,
1200native9 commands maximum,75ordinary16-command groups; success/fall/timeout
stop immediately. Same environment and policy seeds42..51 across both models;
identical nominal geometry/goal/controller/cameras, with no hidden scenario changes.
Transformer GPU/BF16, original VAE CPU/BF16, verified cached prompt,CFG1,window8,
state/video5steps/action10steps; synchronous physics freeze while waiting.
Observer is diagnostic-only. Policy views recorded50Hz, observer25Hz, with actual
simulation timestamps and owned terminal-before-reset frames. Failed trials remain
in the10-trial denominator; no selective retries, padding or success-only filtering.

## Evidence thresholds

Declared protocol and exact expected trial membership before starting. Preserve
original source/checkpoint/normalizer identities and all actual attempts. Each
trial has outcome, actual terminal state/media, command counts and seed/reset
evidence. Video encoding/decoding/frame counts verified; frames consumed by the
model remain the original live RGB, independent of diagnostic MP4 compression.
Use existing QLM result validators; local empirical metrics are reported separately
from the unavailable accepted official benchmark aggregate. Do not weaken validators.

## Progress

- [x] User scope, current checkpoints and isolated worktrees inspected.
- [x] Work IDs reserved by the correct namespace authority.
- [x] Implement three-view video capture and declared trial evaluation binding.
- [x] Necessary CPU/encoding checks and first real recorded trial.
- [x]10actual v2 trials and10actual v3 trials.
- [x] Complete results/metrics/video gallery and contextual limitations.
- [x] Update current context and archive paired records after gates pass.

## Discoveries and decisions

The existing public live driver is reused; it already owns confirmed execution
and freezes physical/controller time around RPC. The environment owns terminal
state. New evaluation recording only consumes events through existing recorder
hooks and cannot drive reset,clock,hold or task decisions. Earlier1.5s engineering
trials are not part of this evaluation denominator.

## Visual acceptance failure

v2/eval-10-r1 camera arrays were essentially uniform grey. The first timeout
cannot be a valid policy evaluation; subsequent runtime was stopped. Repair is
shared-v2/SIM-002. The10+10trial set remains pending valid RGB.

## Deployment update — 2026-10-03

The eight-block CPU-master configuration passed one trial, then the fixed observer
turned uniform grey on the next trial. The complete r3 batch is infrastructure-invalid
and preserved in block8-invalidation.json; its outcomes are excluded without selecting
on policy success. Whole-model phase reload also failed with OOM. The adopted r4
configuration uses model_block_cpu_offload_count=16, physical_execution_offload=false:
16 original Transformer blocks retain CPU BF16 master parameters and execute their
forwards on CUDA through existing Accelerate hooks. The remaining parameters and K/V
are on CUDA; the original frozen VAE stays on CPU. No quantization, architecture,
sampling, task, camera, normalizer or checkpoint change is made.

Tiny CUDA fixed-seed parity passed for both original v2 and joint-state v3 paths
(atol 2e-5). Per-trial initial all-view content gates and per-frame fixed-observer
gates abort on infrastructure failure, preserving pending trials as not_run.
The first valid r4 v2 batch completed all ten seeds 42..51: six successes, four
timeouts, zero falls/errors. All 986 RPC waits froze physical time. v3 is executing
the same declared trial set; completion/media gates stay pending until all ten rows.
Actual attempt/config snapshots: runs/audit/push-box-first-sft-eval-20261003/
{v2,v3}/eval-10-block16-r4.

## Accepted local evaluation — 2026-10-03

Both original full first-SFT step1000 checkpoints completed ten actual nominal-Box05
Push Box trials each, seeds42..51, 24s simulation horizon. v2: 6success,
4timeout; v3: 5success,5timeout.
Both have zero falls/errors/not_run. Task success retains full projected footprint,
not-fallen and three50Hz ticks. Mean successful simulation time is
9.593s(v2) / 9.444s(v3).
All60 original RGB videos and20 three-view clips, terminal-before-reset frames,
trial tables and fixed seeds are preserved. All986
v2 / 1068v3 RPC waits preserved physics/controller/time.
Existing QLM result validation passed with complete ten-trial membership per policy.

Deployment is model_block_cpu_offload_count=16 and physical_execution_offload=false:
16 original BF16 Transformer blocks keep CPU master parameters and execute on CUDA
through existing Accelerate hooks. Remaining parameters/K/V stay on CUDA; the original
frozen VAE is CPU BF16. Full weights, architecture, prompt, normalizers, camera
calibration, physics, native9/force-zero, CFG1/window8 and5/10steps are unchanged.
This additional block offload is required by the tested16GB scene rendering setup;
the earlier Transformer-GPU/VAE-CPU visual acceptance remains withdrawn.

Controlled no-model10.2005GB GPU allocation reproduced uniform238 RGB; release/reset
restored the same scene. Exact internal RTX failure mechanism remains unestablished.
The original grey batch, whole-model phase-reload OOM and unstable eight-block batch
are preserved and excluded as complete infrastructure-invalid attempts. No task-failure
retry or success-based outcome selection was used in the accepted r4 batches.

Evidence: workspace runs/audit/push-box-first-sft-eval-20261003/report.json and report.md, with actual per-policy
r4 integration/results/media/config identities. Local empirical task metrics are
accepted for this declared nominal scene. Public EvalCase reconstruction, statistical
superiority/generalization, predicted-video quality and a formal benchmark aggregate
remain unverified/not_run; formal_score is null and result bundles are not publishable.
This synchronous simulation is not real-time. Source remains local/uncommitted;
no HF/W&B upload, normalizer fitting, new demonstrations, formal training or AMD access.
