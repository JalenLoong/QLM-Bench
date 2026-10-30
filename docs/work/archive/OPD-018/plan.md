---
id: OPD-018
type: exec-plan
status: completed
source_map: []
---
# Quadrupedal OPD: exact history KV reuse and round metrics in W&B (WAM-only; QLM unchanged)

User decision (2026-10-30): implement the reviewed, numerically exact learner speed-ups
and upload the existing per-round diagnostics to W&B. Algorithm, recipe, data, sampler,
losses, RNG keys, update order and success criteria are unchanged.

Admin formal OPD-008-formal-ac470b… (W&B 88f2d243…) shows learner time growing about
12.5 s per round, to 257–560 s after step 41. Each round builds 48 QueryContexts (student 16,
fake 26, teacher 6), and each one replays the episode from group 0.

- [x] Per-role history store: detached clones of a pure-history KV state keyed by
      (role version, verified prefix digest). A prepare restores the longest stored prefix
      of the same journal content and commits only the remaining groups. Store entries are
      not cache leases. A version advance or checkpoint restore clears them.
- [x] A. Frozen teacher: entries survive rounds (version never advances).
- [x] B. Student/fake: repeated prepares of one record within one version use one replay;
      record j+1 extends record j.
- [x] C. The training actor shares its pure-history state at predict entry (same student
      version); learner student prepares hit it.
- [x] Kill switch `OPDV4_HISTORY_REUSE=0` restores full prefix replay (no identity change).
- [x] Round metrics gathered once on all ranks and uploaded by rank 0: fake/student/probe
      losses and DMD diagnostics, gradient norms, phase and collection times, release
      barrier/actor rebuild, learner-phase model calls and history-reuse counters, HBM and host
      RSS, per-task contexts and terminal outcomes, state-plan vs real-latent error. student DMD
      loss is added to the unit metrics. No Config field is added. No skipped-round counter:
      any failed round aborts the attempt, so attempted_rounds - student_updates is always 0.
- [x] Equivalence tests: reuse on/off gives bitwise-identical student/fake adapters, Adam
      state and round metrics on tiny CPU models across window eviction, terminal resets
      and checkpoint restore.
- [x] compatibility.json: new runtime_sha256; 13b51f… and 00c06b… registered as equivalent.

Verification (local CPU only): WAM `make check` 297 passed / 21 skipped (baseline before OPD-018:
286 passed). New `tests/opd_v4/test_history_reuse.py` and `test_round_metrics.py`; the engine
lifecycle test now checks the uploaded keys. Reuse on/off gives bitwise-identical adapters, Adam
state and unit metrics; learner student contexts replay no group (actor hit). Injected faults
(restore one group short, actor sharing after the plan write, actor state never hit) all fail
the tests. Tiny-model round at prefix ~120: history forwards 11802 -> 1004, learner 14.2 s -> 1.8 s.

Independent adversarial review (4 lenses, 2 verifiers per finding): no exactness finding;
reviewers also ran 2-rank Gloo DDP, activation checkpointing, store capacity 1/2/8, mid-episode
resets and an interleaved video actor bitwise equal. A continuation of records produced by the
real e7ccf34 (OPD-013) code passes submit preview, run_stage, formal admission and checkpoint
restore with the current code. Fixed from the review: learner-phase call/reuse counts (actor,
release refresh and video excluded), exclusive terminal outcomes with tick-based length, float64
finite plan error, tighter tests, README safe-stop lead time including the video, per-key metric
semantics and the running-formal upgrade recipe.

Not run on AMD; AMD speed, HBM and determinism of ROCm kernels are not measured. No commit/push,
Slurm or training.
