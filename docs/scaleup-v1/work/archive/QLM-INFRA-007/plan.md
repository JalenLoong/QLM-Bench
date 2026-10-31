---
id: QLM-INFRA-007
type: exec-plan
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

- [x] Worker: `progress` (finite float `rt.outcome['progress']`) in the `restore` response and in every
      `execute` response (normal, terminal, `physics_instability`, `policy_command_rejected`); non-finite
      raises `FloatingPointError`. The terminal dict keeps `rt.outcome`'s fields.
- [x] `read_cases`: v1 (`policy_seed` 42) and v2 (`policy_seeds`, distinct non-negative ints, first 42)
      records, normalised `policy_seeds` on return; every other v1 check unchanged.
- [x] `run_case(record,case,controller,port,seed,…)`: seed -> `driver.reset_episode(policy_seed=seed)`,
      session id `rl-validation-<demo_uid>-s<seed>`, row key `policy_seed`.
- [x] `run(cases,controller,port,output,rollouts=None,*,case_indices=None)`: (case index, seed) rollouts,
      seed-major default, validation before output, `<demo_uid>-seed<seed>.json` rows,
      `result.json` (`…-result-v2`, `policy_seeds`, `success_rate`, `per_seed_success_rate`) for the complete
      set, otherwise `subset.json` (`…-subset-v2`, `rollouts`).
- [x] CLI `--rollouts i:seed,…` (strict, fails closed), `--case-indices` alias, `--visualize-case` first seed.
- [x] Tests extended; README runbook, handoff and registry updated.

Local tests only: no commit, AMD, Slurm, training, 5B model or upload.

Verification: `tests/qlm/test_rl_v2.py` (progress responses, pinned identity `6f7c0621…` unchanged because no
hashed folder was edited) and `tests/test_rl_v2_validation.py` (record parsing, rollout bookkeeping, CLI). Full
py3.12 suite and `scripts/check_governance.py`: see the handoff page (QLM-INFRA-007 section). Remaining: a real
MuJoCo multi-seed validation run and the WAM ALG-006 consumer are not exercised here; nothing was run on AMD.
