---
id: QLM-INFRA-006
type: change
status: completed
source_map:
  - src/qlm_bench/backends/mujoco/runtime.py
  - src/qlm_bench/backends/mujoco/rl_v2/storage.py
  - src/qlm_bench/backends/mujoco/rl_v2/snapshot.py
  - src/qlm_bench/rl_v2/worker.py
  - src/qlm_bench/rl_v2/validation.py
---
# RL-v2 opt-in 12.5 Hz observation capture, equivalent-identity restore and validation case subsets

Paired with mujoco-v2/INFRA-009 (per-rank validation). User-approved engineering speedup; physics, RAMBO,
rendering, task outcome, IPC schema, anchors and the 50 Hz behaviour of every other pipeline are unchanged.

- [x] `MuJoCoRuntime.observation_ticks` (default 10 = today's 50 Hz dualRGB). `step()` captures `state()`
      eagerly after a completed command only when the tick is a multiple of it; `state()` stays lazy and
      cached per (epoch, tick), the terminal capture is unchanged. Validated: positive multiple of 10
      dividing 40 (10/20/40). Recorders, trace, evaluation, suite media and `rl_v2/replay.py` keep 10.
- [x] Opt-in only for the RL-v2 CPU consumers that read RGB at the 80 ms grid: `rl_v2.worker.AnchorWorker`
      and `rl_v2.validation.run_case` (run and visualize; observer frames are still saved at tick % 40).
      Renders per 0.32 s group: 16 -> 4 of two 360p cameras.
- [x] Identity: `execution_source_identity()` hashes the edited folders, so the digest moves from
      `95feae2a…` (42cda63, every AMD-prepared pool) to `6f7c0621…` (`ef4f7da3…` was an uncommitted
      intermediate of this work, never deployed). `rl_v2/equivalence.EQUIVALENT_SOURCE_IDENTITIES` (excluded
      from the digest because it names it) maps the old digest to its registered successor set and the
      reason; `snapshot.check_identity`/`restore` accept a snapshot whose identity equals the live one
      except for a registered predecessor `source` whose successors contain the live source, printing one
      WARNING to stderr. Any other field, an unregistered stored source, a registered stored source on an
      unregistered live source, or another schema still raises. New captures record the live identity.
      The pin test asserts the live value and that it is the only registered successor of the old one.
- [x] `rl_v2.validation --case-indices a,b,…` (indices into the ten held-out episodes) runs only those
      cases, writes the per-case `<demo_uid>.json` rows as before, and writes `subset.json`
      (`indices`, `outcomes`, `cases_sha256`) instead of `result.json` unless all ten ran. WAM
      INFRA-009 launches one subprocess per rank with its own indices.
- [x] Evidence (local CPU, OSMesa llvmpipe): workspace
      `runs/audit/ws-fix-001-20261029-v1/rl-v2-speedup-research/render-cadence-20261030/`. The same 144 GT
      receipts of the Sweep demo at cadence 40 give 74/74 policy RGB frames bitwise equal to the
      old-cadence reference and 144/144 equal receipts; a cadence-10 anchor restores at cadence 40 with the
      exact and the legacy identity (WARNING) and identical frames at the next eight 40-tick boundaries.
      Wall 24.5 s (reference) / 22.4 s (same session) -> 7.6 s; render_readback 18.7 s -> 4.8 s. The
      real-runtime test (`test_observation_cadence_40_captures_a_quarter_with_identical_model_frames`, Sweep
      scene, OSMesa) was re-run on the final digest `6f7c0621…` after the successor-bound gate: 3 passed.

Local tests only: no commit, AMD, Slurm, training or upload.
