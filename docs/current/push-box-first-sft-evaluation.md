---
id: CURRENT-FIRST-SFT-EVALUATION
type: current
status: accepted
last_verified_at: 2026-10-03
related_work: [EVAL-002, SIM-002, INFER-002]
source_map: []
---

> **Later audit correction:** Clean reset-isolation acceptance is withdrawn.
> Root-link reset velocities carry over at9/9 episode boundaries per policy.
> Existing success counts are historical observations; read [the audit](inference-chain-audit.md) before reuse.

# First-SFT Push Box local evaluation

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
