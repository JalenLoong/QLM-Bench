---
id: QLM-RL-V2-INDEPENDENT-REVIEW
type: current-design
status: accepted
source_map:
  - src/qlm_bench/rl_v2/resources.py
  - src/qlm_bench/rl_v2/validation.py
  - src/qlm_bench/rl_v2/worker.py
  - src/qlm_bench/backends/mujoco/rl_v2/storage.py
---
# RL-v2 independent review — 2026-10-26

QLM-SIM-025 pairs with WAM mujoco-v2/ALG-003. Scene resources now use explicit server
locators verified against the historical resource closure. Validation has no fallback
to the collection machine's absolute scene path. A public resource-admission helper
keeps simulation out of WAM imports. Worker reference admission binds the actual
replay result and binding; source hashing is cached once per worker process.

Actual relocated NativeCPU/RAMBOCPU/OSMesa snapshot replay passed16 commands twice:
qpos/qvel/RGB exact,160 ticks each. This is an engineering regression, not a new demo,
full GT replay, task success claim or formal validation. Original resources and
historical evidence remain unchanged. Full ten-demo target preparation/calibration,
AMD/Slurm and formal training/validation are not_run.

See workspace runs/audit/rl-v2-independent-review-20261026-v1/report.md and completion.json,
and the WAM RL-v2 README for the executable administrator workflow.
