---
id: EVAL-003
type: change
status: completed
source_map: []
---
# Single-trial closed-loop inference with predicted video

## Purpose and scope
User requests one v2 and one v3 Push Box trial, retaining every predicted video chunk.
Use original full-SFT step1000 checkpoints, seed42,24s horizon, CFG1,window8,
video/state5 and action10 steps,16 CPU-master/CUDA-forward blocks and frozen VAE CPU.
Run repaired QLM commit a11e5a77c09a5fcc0170463dcb59f428ac6a65a9 in an isolated source worktree.
Keep concurrent scale-up edits intact. No policy/model/normalizer or physics change.
No demonstrations, training, remote publication or new benchmark claim.

## Progress
- [x] Scope, source, checkpoint configuration and GPU reviewed.
- [x] Run-local read-only hooks persist observed and predicted latents with timestamps.
- [x] One actual trial per policy, all RPC waits frozen and valid scene RGB.
- [x] Frozen causal VAE decoding with observed-history cache branches, complete video gallery.
- [x] Verify chunk/frame membership, source identities, result validation and archive.

## Evidence and recovery
New evidence only: workspace runs/audit/predicted-video-close-loop-20261008.
Preserve all actual failed attempts. Never retry for task success.
Record W&B/HF upload not_run. Decode after physical execution to avoid altering runtime RNG,
VAE encoder caches, model caches or GPU residency. Raw BF16 latents remain retained.
One trial does not estimate success rate or establish comparative benefit.

## Later explicit authorization — 2026-10-08

The user requests publishing this inference batch as one independent W&B run in
the existing WAM-Policy project. This supersedes the prior W&B not_run restriction
only for these two trials and their evaluation videos/latents/evidence. No model
weights, frozen caches, datasets or assets are uploaded. No HF/Git publication or
new training/rollouts are implied. Exact inventory and readback live alongside
this batch as wandb-upload-manifest.json and wandb-publication.json.

## Outcomes and retrospective — 2026-10-08

- v2: timeout, 24.00s simulation, 75 predicted chunks/300 frames, 152 frozen RPC waits.
- v3: timeout, 24.00s simulation, 75 predicted chunks/300 frames, 152 frozen RPC waits.

All original actual ego/task/observer videos, terminal-before-reset frames, raw BF16
predicted/observed latent copies, individually decoded chunks and concatenated videos
are preserved in workspace runs/audit/predicted-video-close-loop-20261008.
Selected media/curated scalar and hash evidence published as independent W&B run https://wandb.ai/junlinlong-the-university-of-sydney/WAM-Policy/runs/d64992a6; 468 Artifact files readback-verified. Raw tensors/NPZ and all implementation/HTML/log files remain local.
The original QLM one-trial result validators pass; formal score remains unavailable.
All actual video frames pass the non-uniform scene gate.

## Discoveries and decision log

V2 recording r1 failed before loading model/starting physics due to output-directory
creation order. The corrected r2 is its only physical trial. Offline decode r1 failed
on a patch-size assertion; the original VAE has patch_size2 and official unpatchify
was retained. Neither failure selects for task success; both logs remain preserved.
First two prediction branches in both views match official full observed-prefix VAE
decode exactly (maximum absolute difference0). Every available complete predicted
latent differs from the subsequent physical-observation latent and was saved earlier.
Every played MP4 frame matches decoded predicted RGB ordering within H264 loss.
Observed latents provide prior causal context only; predicted future RGB comes from
the sampled prediction branch. No Isaac MP4 is read by the prediction decoder.

See completion.json, prediction-provenance-final.json and review.html in that evidence
directory. Independent source snapshot is clean at QLM a11e5a77c09a5fcc0170463dcb59f428ac6a65a9.
Concurrent scale-up source edits are preserved. No inference/model/normalizer/physics
implementation changes, new demonstrations, formal training, remote publication,
commit or push accompany this task. The two single outcomes do not revise the historical
6/10 versus5/10 batch or establish statistical comparative benefit.
