---
id: QLM-INFRA-005
type: change
status: completed
source_map: []
---
# RL-v2 QLM pre-commit AMD review fixes

Paired with mujoco-v2/INFRA-007, the pre-commit AMD review of RL-v2.

- [x] Withdraw the QLM-INFRA-004 replay PNG-subset change. `execution_source_identity()` hashes
      `backends/mujoco`, and every anchor prepared on AMD with 42cda63 stores 95feae2a…;
      restore requires an exact match. `backends/` is byte-identical to 42cda63 again, and a test
      pins the identity.
- [x] `rl_v2.worker`: frames go to a private copy of the stdout pipe and fd 1 points at stderr
      before MuJoCo/OSMesa load. libmujoco 'WARNING:' prints, which become immediate under
      PYTHONUNBUFFERED=1, can no longer corrupt the length-prefixed stream.
- [x] AGENTS.md routes DATA-002 again, which the dataset-context test requires.
- [x] User decision: delete the Isaac-era tests that need the removed Isaac Lab / rambo-isaac60
      environment (registry environment-override test, worktree runtime-wrapper test file).
- [x] User decision: a FloatingPointError from physics during `execute` ends the chunk with a
      `physics_instability` policy-failure terminal, carrying the last observed frame. The
      diverged state is never rendered, and the next candidate restores a fresh anchor.

Physics, RAMBO, rendering, task success and the IPC schema are unchanged. Local tests only.
