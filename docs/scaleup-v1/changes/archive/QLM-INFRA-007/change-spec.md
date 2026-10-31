---
id: QLM-INFRA-007
type: change
status: completed
source_map:
  - src/qlm_bench/rl_v2/worker.py
  - src/qlm_bench/rl_v2/validation.py
  - tests/qlm/test_rl_v2.py
  - tests/test_rl_v2_validation.py
---
# RL-v2 worker task progress and multi-seed validation protocol v2

Paired with mujoco-v2/ALG-006 (the WAM consumer of both interfaces). Only `src/qlm_bench/rl_v2/` changes, which
is outside `execution_source_identity()`: physics, RAMBO, rendering, task outcome, anchors, the IPC envelope and
the hashed folders are untouched, so the pinned digest `6f7c0621…` and every AMD-prepared pool stay valid.

- [x] Worker (`rl_v2.worker.AnchorWorker`): the `restore` response carries `progress` (float
      `rt.outcome['progress']` of the restored anchor state); the `execute` response carries `progress`
      evaluated after the chunk's commands ran (after a task terminal too, where the terminal dict keeps
      `rt.outcome`'s fields; after `physics_instability` it is the last completed command's value; the
      `policy_command_rejected` early return carries the current value). A non-finite value raises
      `FloatingPointError` (`task_progress`), which poisons the session like any other worker error. For
      push_box, progress is the box's forward displacement in metres since reset
      (`backends/mujoco/tasks.py evaluate()`).
- [x] Validation record: `qlm-rl-v2-validation-v1` (`policy_seed` 42) and `qlm-rl-v2-validation-v2`
      (`policy_seeds`: non-empty list of distinct non-negative ints whose first element is 42) are both read;
      `read_cases` returns the record with a normalised `policy_seeds` list. `horizon_seconds` 60, the ten
      held-out episodes, lineage/prompt hashes, scene provenance and resource verification are unchanged.
- [x] `run_case(record,case,controller,port,seed,*,on_observation=None,observer=False)` passes the seed as
      `policy_seed` to `driver.reset_episode`, uses the session id `rl-validation-<demo_uid>-s<seed>` (two
      seeds of one case never share a session) and records `policy_seed` in the row
      (`demo_uid`, `policy_seed`, `outcome`, `simulation_time_ns`, `renderer`).
- [x] A rollout is a (case index, seed) pair. `run(cases,controller,port,output,rollouts=None,*,case_indices=None)`:
      None means every case under every seed, seed-major (for seed in seeds: for case in cases); explicit
      pairs are validated (index in 0..9, seed of the record, no duplicates, non-empty) before the output
      directory is created. Every rollout writes `<demo_uid>-seed<seed>.json` atomically; the v1
      `<demo_uid>.json` name is never written, even for a single seed. The complete set writes `result.json`
      (`qlm-rl-v2-validation-result-v2`: `passed`, `task_id`, `split`, `GT_actor_visible`, `cases_sha256`,
      `policy_seeds`, seed-major `outcomes`, `success_rate` = successes/len(outcomes),
      `per_seed_success_rate` {str(seed): rate}); any other set writes `subset.json`
      (`qlm-rl-v2-validation-subset-v2`: `task_id`, `rollouts` [[i, seed], …], `outcomes`, `cases_sha256`).
- [x] CLI: `--rollouts i:seed,i:seed,…` parsed strictly (decimal, no signs, spaces or leading zeros; a
      malformed item exits 2 with `Malformed rollout …`); `--case-indices` stays as the alias "listed cases
      under every seed of the record"; both are mutually exclusive and refused with `--visualize-case`, which
      runs the first seed (42). `visualize()` only passes that seed explicitly.
- [x] Tests: `tests/qlm/test_rl_v2.py` (restore/execute/rejected/instability responses carry a finite float
      `progress`, non-finite raises; identity pin unchanged) and `tests/test_rl_v2_validation.py` (v1/v2
      parsing, `run_case` session/seed binding through fakes, per-rollout files, result/subset selection and
      rates, the alias, invalid rollouts, strict CLI parsing).

Local tests only: no commit, AMD, Slurm, training, 5B model or upload.
