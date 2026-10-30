---
id: QLM-INFRA-004
type: exec-plan
status: completed
source_map: []
---
# RL-v2 AMD blockers: prepare cost, W&B/log fidelity, identity gates, prediction video

User-authorized engineering repair on `rl/v2_GT-guided_chunk-level_close-loop_NFT` (WAM + QLM).
The RL recipe, LoRA/120-round budget, data split, reward and success criteria are unchanged.

- [x] prepare: GT replays/verifications run in parallel single-threaded CPU processes; only the
      first demo is replayed twice as the task replay-determinism probe (native CPU replay is
      bitwise deterministic locally: repeat error 0); other demos reuse its tolerance; one VAE
      load builds all prefixes; prefix self-check re-encodes and write-then-reload removed;
      replay PNGs only at consumed 0.08 s/terminal ticks; failed outputs are kept aside and
      recomputed; per-job/phase timing in `preparation-timing.json`.
- [x] Verification keeps every anchor restore (8 commands, 2 RGB ticks) plus one long midpoint
      continuation that must retain success; duplicate 32-command continuations removed.
- [x] Calibration replay gap uses the available repeat probe(s); older pools with ten repeats are unchanged.
- [x] W&B: stage and model runs open when computation starts (real duration), finish with
      exit code 1 on failure, carry error/returncode/log tail, upload redacted `compute.log` and
      child logs; torchrun `@record`; rank-0 tracebacks printed before conversion to messages;
      SIGTERM/timeout recorded before Slurm kills the job; pending W&B sync no longer blocks the next stage.
- [x] Identity gates: WAM/QLM full-source fingerprints are provenance, not admission/resume/
      publication keys; operational site edits no longer invalidate completed stages; the
      renderer GL string is recorded instead of forcing a new prepare; train-time estimate is a warning.
- [x] Large-file content hashes reused while inode/size/mtime/ctime are unchanged.
- [x] Training: current policy rolls out one fixed held-out validation case at round 0 and every
      fifth of the run; composite MP4 (predicted ego/task from sampled latents, simulator ego/task,
      simulator observer) rendered by a background CPU process and logged to W&B.

Local tests only; no commit/push, AMD, Slurm, formal training or full 5B load.

Paired with mujoco-v2/INFRA-005. QLM parts: replay PNG subset, determinism probe and verification schedule, renderer-string warning, single-case visualization runner with evaluation observer.
