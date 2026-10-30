---
id: OPD-017
type: exec-plan
status: completed
source_map: []
---
# Quadrupedal OPD pre-commit AMD review fixes

User-requested pre-commit review before pushing the branch to the AMD administrator: four review
lenses (recurrence of administrator-reported problems, AMD runtime) with adversarial verification.
Algorithm, recipe, data and success criteria are unchanged.

- [x] The closed-loop video rollout timeout defaults to, and is capped at, the collective/RPC
      timeouts minus 600 s (1200 s with the admin's 1800 s timeouts). An override above about
      1700 s would trip the RCCL/RPC timeouts and abort formal. At local speed, a failed 24 s
      episode still needs about 21-22 min of simulation, so it times out without a video; a
      shorter episode or a multi-threaded render for the runner is a pending user decision.
- [x] Video set-up is failure-tolerant and decided on rank 0, then broadcast, so ranks cannot
      issue mismatched collectives. A missing imageio-ffmpeg, an invalid
      OPDV4_VISUALIZATION_EVERY or no usable timeout disables the video instead of stopping formal.
      A round that received a safe-stop request skips its video.
- [x] A safe-stopped attempt finishes its W&B run with exit code 1, `passed=false` and
      `safe_stop=true`; formal runs record `passed`.
- [x] `submit` removes credential variables from the sbatch environment (`--export=ALL`).
- [x] The reviewed runtime fingerprint is updated for the engine change, and the OPD-014
      equivalence note covers it.
- [x] QLM AGENTS.md routes DATA-002 again; the test suite needs it.
- [x] User decision: delete the three QLM tests that need the removed Isaac environment
      (registry environment override, worktree runtime wrapper, Isaac qp_env observation layout).
- [x] README: imageio/imageio-ffmpeg, token handling, safe-stop status, and the video's
      blocking time and timeout.

Local CPU tests only; no commit/push, AMD, Slurm or training.

Verification:
- WAM `make check` passes.
- New tests cover the timeout cap, the encoder check, the safe-stop W&B outcome and a credential-free sbatch environment.
- QLM pytest on py3.12: 569 passed / 15 skipped after deleting the three Isaac-only tests.
- Not run on AMD.

