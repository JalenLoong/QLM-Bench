---
id: SIM-002
type: change
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
- [ ] Identify the actual blank-image cause using rendered-scene diagnostics.
- [ ] Repair and verify nonempty scene content in all three views.
- [ ] Confirm moving-camera extrinsics/frame cadence and physics freeze unchanged.
- [ ] New actual first-SFT visual closed-loop proof, then valid10+10evaluation.

## Recovery and decisions

Use separate versioned render-probe attempts; do not edit original SDK/workspace
layers or persisted user settings. Rendering-only diagnostics do not become trials.
The failed first evaluation is excluded as an infrastructure-invalid batch, without
selecting on policy success. All seeds and metric denominators stay declared.

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

The implemented deployment replaces the initial full-model phase-offload proposal; its failed attempt remains evidence, while the accepted16-block option satisfies actual RGB/memory gates.
