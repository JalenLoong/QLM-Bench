---
id: OPD-019
type: exec-plan
status: completed
source_map:
  - src/qlm_bench/backends/mujoco/training_control.py
  - src/qlm_bench/backends/mujoco/training_visualization_case.json
  - src/qlm_bench/backends/mujoco/training_compatibility.json
---
# ExecPlan: OPD-019 四足 OPD-v4 v2 训练配置（QLM 侧镜像）

实施方案、进度、验证与审查结论以 [WAM ExecPlan](../../../../../WAM-Policy-opd-v4/docs/work/archive/OPD-019/plan.md)
为准。本页列出 QLM 的改动项与本仓库验证。

- [x] training profile v2 与 `training_tasks`（Phase 5.1）：`DESIGN`/`PROFILE` 升版，`TRAINING_TASKS` 为去掉
      `sweep_block_to_zone` 的 9 个任务；`training_horizons_s` 与 pool 身份不变。
- [x] `EpisodeSchedule` 9 任务（Phase 5.2）：decks、计数、cursor、round-robin、`validate` 均基于 `profile['training_tasks']`；
      10 任务形状的快照不能通过 v2 校验。
- [x] 训练视频 case 换 turn_valve train reset `turn_valve-20261016-001`（Phase 5.3）。方案原写 validation
      `turn_valve-20261016-081`，但其场景 `4e76f964…` 不在 train pool（turn_valve 每个候选场景独立）；用户 2026-10-31
      选定 train reset，case 从本地 train pool 记录复制，provenance 记 release manifest `5e21b852…`。
- [x] `training_compatibility.json` version `native1-2-5f900s-v2`（Phase 5.4）；新运行时指纹 `8b5724f8…` 已登记到 WAM
      `compatibility.json`，`equivalent_runtime_sha256` 为空。
- [x] QLM pytest：571 passed / 15 skipped（基线 569 + 新增 2：9 任务调度/永不 reserve sweep/pool 仍 10 任务，视频 case）。
