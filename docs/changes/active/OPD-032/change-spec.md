---
id: OPD-032
type: change
status: active
source_map:
  - src/qlm_bench/backends/mujoco/training_control.py
  - tests/qlm/test_opd_episode_schedule.py
  - docs/governance/opd-v4-work-registry.json
---
# ChangeSpec: OPD-032 M-OPD v1.1（QLM 侧）

分支 `mopd/v1.1_M-OPD_sweep-via-door-expert`。主体在 WAM 同名分支（见 [WAM ChangeSpec](../../../../../WAM-Policy-mopd-v1.1/docs/changes/active/OPD-032/change-spec.md)）。
QLM 一侧只放开 profile 的任务集合：`training_control.accepted` 接受十个 pool 任务（含 `sweep_block_to_zone`）按 `TASKS` 顺序的非空子集，
上限 ≥ 2；默认 9 任务与十任务 profile 的上限都必须是 2。M-OPD v1.1 用十任务训练 profile（上限 2）和只有 sweep 的采集 profile（上限 8）。
默认 9 任务 profile、`DESIGN`、horizons、sampling 不变。runtime 指纹 `df399db3…` → `d11b395b…`，WAM `compatibility.json` 的 `qlm` 块把旧值登记为等价。
