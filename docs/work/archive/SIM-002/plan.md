---
id: SIM-002
type: exec-plan
status: completed
namespace: adaptation-v2
source_map: []
---
# Restore actual scene RGB before learned-policy evaluation

## Problem and evidence

EVAL-002 first v2 trial executed1200commands and timed out at24s, but visual
inspection found uniform grey ego/task/observer RGB. Policy media is invalid.
The prior INFER-001 task-centric terminal SHA matches uniform238 RGB exactly;
its clock/command/cache/reset evidence remains valid, while the effective visual
closed-loop claim is withdrawn pending repair. All attempts remain immutable.

## Authorized scope

Repair camera/render runtime needed for the user-requested Push Box evaluation.
Keep Go2/controller/action/task predicates/physics cadence, mounted camera pose,
calibration and original model/data identities. Diagnose actual renderer flags,
USD/fabric camera transforms and scene visibility. No simulator upgrade, training,
normalizer fit, remote publication or fabricated replacement footage.

## Progress and evidence gates

- [x] Stop invalid v2 evaluation and queued v3; preserve failure/media and open preview.
- [x] Identify the actual blank-image cause using rendered-scene diagnostics.
- [x] Repair and verify nonempty scene content in all three views.
- [x] Confirm moving-camera extrinsics/frame cadence and physics freeze unchanged.
- [x] New actual first-SFT visual closed-loop proof, then valid10+10evaluation.

## Recovery and decisions

Use separate versioned render-probe attempts; do not edit original SDK/workspace
layers or persisted user settings. Rendering-only diagnostics do not become trials.
The failed first evaluation is excluded as an infrastructure-invalid batch, without
selecting on policy success. All seeds and metric denominators stay declared.

## Controlled cause and repair update

Static three-view probes show normal images without external CUDA allocation.
An independent10.2005GB allocation, without WAM or physics commands, turns all
three views uniformly238; releasing it plus a reset restores scene images. Stage
identities match, color rendering is enabled, and geometry-streaming disable
alone did not fix it. Root trigger is GPU memory pressure; exact internal RTX
fallback is not claimed.

Whole-model phase offload encountered OOM when reloading while actual RTX
resources were live. The adopted deployment CPU-offloads8original BF16 blocks
with CUDA forward via the already installed Accelerate hooks. No quantization
or sampling/model/task changes. Tiny fixed-seed output parity passed. The first
valid full-SFT v2 trial now has three real views and task success at9.14s/457commands.
Full10+10batch gates remain pending. Evidence: render-memory-cause.json and
v2/eval-10-block-offload-r3 under the current workspace audit directory.

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
