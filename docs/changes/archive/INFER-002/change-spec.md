---
id: INFER-002
type: change
status: completed
namespace: adaptation-v2
source_map: []
---
# Coordinate synchronous model GPU residency with actual RTX rendering

## Problem and evidence

SIM-002 controlled GPU allocation10.2005GB reproduces uniform238 RGB without any
WAM model. The same scene renders normally without pressure, and releases restore
actual scene RGB. Turning off geometry streaming did not fix the pressure failure.
No exact internal RTX allocation/fallback mechanism is claimed. The previous
Transformer-GPU/VAE-CPU numerical acceptance does not prove valid scene feedback.

## Change and compatibility

Explicit opt-in physical_execution_offload moves full BF16 Transformer weights
to CPU while the single environment executes/renders. Reset/predict/feedback model
operations compute on the original CUDA device; weights are released after reset
and predict, retained only between feedback and the immediately following predict.
KV/history remains device-consistent and episode-local; no physics runs during RPC.
Original checkpoints, normalizers, cached prompt,5/10steps,CFG1/window8, calibrated
cameras, native9/force-zero and all task/control/timestamp semantics remain unchanged.
No quantization, architecture/pruning, training, new demos or external publication.

## Evidence gates and progress

- [x] User evaluation requires valid RGB; controlled cause/recovery inspected.
- [ ] Implement explicit residency lifecycle with truthful placement provenance.
- [ ] Fixed-seed output/cache/reset parity across residency transitions.
- [ ] Real original-scene RGB under full first-SFT inference, all three views.
- [ ] Actual valid10+10evaluation and complete media, then paired archive.

## Evidence location

Workspace runs/audit/push-box-first-sft-eval-20261003, including all invalid attempts
and no-model renderer probes. Earlier assertions of effective visual closed loop
remain withdrawn until these gates pass. New deployment is recorded separately.

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
