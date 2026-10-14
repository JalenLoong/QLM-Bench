---
id: CURRENT-PREDICTED-VIDEO
type: current
status: accepted
related_work: [EVAL-003]
source_map: []
---
# Single-trial predicted-video closed loop — 2026-10-08

The user requested one Push Box trial per original v2/v3 full first-SFT step1000
checkpoint, with every predicted video chunk retained for viewing. Same nominal
Box05 scene, seed42,24s horizon, original prompts/normalizers/native9/force-zero,
CFG1/window8/video-state5/action10 and16-block CPU-master/CUDA-forward placement.
Actual inference uses the published reset repair in clean QLM source
a11e5a77c09a5fcc0170463dcb59f428ac6a65a9; source scale-up edits are not part of the run.

- v2: timeout, 24.00s simulation, 75 predicted chunks/300 frames, 152 frozen RPC waits.
- v3: timeout, 24.00s simulation, 75 predicted chunks/300 frames, 152 frozen RPC waits.

Predicted targets are captured directly from v2 video-flow return values and v3
sample_chunk.predicted_video. Frozen VAE decoding branches from prior actual observed
context; every future chunk has4frames at12.5Hz,0.32s. Both views are available
individually and ego-above-task together. Raw BF16 latents, lossless review RGB NPZ,
all MP4 chunks, actual three-view videos and synchronized gallery remain preserved.
All available prediction tensors differ from subsequent actual observed latents and
were saved before them; every played MP4 frame is checked against predicted RGB
within encoding loss. This is successive short-horizon closed-loop prediction.

Evidence: workspace runs/audit/predicted-video-close-loop-20261008/completion.json,
prediction-provenance-final.json, review.html and per-policy trial directories.
Original historical20-trial outcomes remain unchanged. This single-trial request does
not establish a success-rate estimate, generalization or comparative benefit.
No model/data/normalizer/physics change, demonstrations, formal training, AMD access,
W&B/HF upload or source commit/push occurred. Runtime hooks and governance records
remain local; no historical receipt is overwritten.

Remote final readback verifies150 predicted_chunks table rows,2 trial rows and
all468 Artifact file digests. Run state: finished. Published run: https://wandb.ai/junlinlong-the-university-of-sydney/WAM-Policy/runs/d64992a6
Local final receipt: workspace runs/audit/predicted-video-close-loop-20261008/completion-final.json.
