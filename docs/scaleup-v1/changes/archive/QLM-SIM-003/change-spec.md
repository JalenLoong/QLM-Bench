---
id: QLM-SIM-003
type: change
status: completed
source_map:
  - scripts/mujoco/probe_checkpoint_rgb.py
---

# Original RAMBO checkpoint verification with actual RGB

## Authority and problem
The user stops asset migration and requests evidence that the original Isaac-trained
RAMBO checkpoint actually runs in MuJoCo before migration proceeds. Existing six-second
two-world Native/CUDA probes have state/contact/reset evidence, but no saved RGB videos.
The previous three-task procedural assets do not establish original-asset migration or
preserved task difficulty; the aggregate P2 acceptance is consequently incomplete.

## Scope and invariants
Use the unchanged Go2 reference model and fixed model_2000 checkpoint, original
405D observation/18D residual, IK/QP/motor chain, force-zero and500/100/50Hz scheduling.
Run bounded18-second single-world Native and CUDA-MJWarp tests with the same preregistered
command schedule. Persist actual dual720p50Hz RGB, diagnostic observer25Hz, authoritative
snapshots, checkpoint/source identities and motor/actor telemetry. Rendering does not
step physics. Capture terminal before explicit reset; retain every failed attempt.
No source controller modification, asset conversion, WAM inference/training, new accepted
demonstrations, AMD, environment installation or external publication is in scope.

## Required evidence and interpretation
- Verify the retained checkpoint hash and strict original actor/normalizer restoration.
- Execute settle/stand/forward/lateral/yaw/FL-extension/return phases with measured state,
  finite outputs, active actor inference and original fall criteria.
- Report measured velocity/EEF tracking per phase, not merely a process exit code.
- Validate video frame count/time/resolution, actual raw RGB hashes, visible observer
  images and no-render-physics-advancement assertions.
- Verify explicit reset clears nonzero state/history/delay without physics advancement.
- Distinguish bounded run-through, numerical regression, tracking, and unverified
  long-horizon/task/AMD compatibility. Neither a short rollout nor asset test scenes
  establish a complete research benchmark or simulator equivalence.

## Recovery
Failures stop the affected attempt and persist partial media/telemetry. Do not change
controller weights/semantics or physics to obtain a pass. Asset migration remains paused
after this verification; any controller issue needing a major change is reported.
