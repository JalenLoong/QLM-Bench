---
id: QLM-SIM-011
type: exec-plan
status: completed
source_map: []
---

# Real WAM v3 closed loop on the accepted default STEP rendering LOD

User explicitly requests new Push Box, Press Button and Lift Basket real-checkpoint
closed-loop rollouts with persisted Ego, task-centric and Observer RGB. Partner
works are QLM-SIM-011 and v3/INFER-005. Use the current pinned LOD a02 model set,
CUDA-MJWarp physics, Native OSMesa, retained real full-SFT step1000 checkpoint,
original normalizers/frozen VAE, task-correct verified T5 prompts and accepted
16-block CPU-master/CUDA-forward deployment. Keep camera/quality/mass/collision,
controller/native9/force-zero and all model/sampling settings unchanged.

Repeat the accepted engineering matrix: each task has two 2.02s episodes,101
executed commands/episode and multichunk feedback, eviction/reset/terminal coverage.
This is a bounded pipeline verification, not a task-success-rate benchmark or new
formal demonstrations. Every first attempt and all failure attempts remain local.

Acceptance: actual strict model/load/resource identities, task-specific prompts,
all RPC waits freeze simulation/controller/time; complete 3x2 episodes, actual
three-view720p videos (policy50Hz/Observer25Hz), timestamps/frame membership,
terminal-before-reset and reset isolation. Validate actual decoded media, inspect
frames and deliver a playable review page. Generated images must come from the
live capture, not predictions or post-run simulator reconstruction.

No training, AMD, external publication, source commit/push or model refit. Evidence:
workspace runs/audit/wam-v3-default-lod-rollout-20261013-v1/.

## Progress
- [x] Validate inputs and default model set.
- [x] Serial actual GPU matrix.
- [x] Media/closed-loop readback and playable review.
- [x] Update current evidence, run checks and archive.

## Actual progress
Push Box completed both actual episodes with32frozenRPC waits,171.5s runtime
wall time and sealed three-viewRGB. Measured initial root velocities are zero
in both reset epochs. Press Button is currently running; Lift Basket remains
pending. Aggregate/media readback is not accepted before the entire matrix ends.

## Actual final completion

Three-task/two-episode matrix-a01 passes on the default pinned LOD with original
real v3 step1000 checkpoint and task-correct prompts. 606commands/96frozenRPC waits,
18original three-view720p videos,42predictions/36feedback commits/18KV evictions,
6resets/6planned horizon timeouts. All actual reset velocities,terminal prefixes,
source PNG/terminal/video hashes,full decode and frame timestamps pass. No grey
frames or selected-out attempts. Six display previews use actual recorded MP4s.

Runtime wall time:Push171.51s,Press167.92s,Lift272.03s for each task two episodes;
startup is separate and these are not throughput benchmark results. Playable
review.html and all original MP4s remain local. Browser automation refuses file://
protocol; deliver videos directly in the conversation and the local page file.
No settings/model/training/AMD/publication/commit/push change.
