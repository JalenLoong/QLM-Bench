---
id: OPD-019
type: change
status: completed
source_map:
  - src/qlm_bench/backends/mujoco/training_control.py
  - src/qlm_bench/backends/mujoco/training_visualization_case.json
  - src/qlm_bench/backends/mujoco/training_compatibility.json
---
# ChangeSpec: OPD-019 四足 OPD-v4 v2 训练配置（QLM 侧镜像）

完整意图、决定表与验收标准以 [WAM ChangeSpec](../../../../../WAM-Policy-opd-v4/docs/changes/archive/OPD-019/change-spec.md)
为准；本页只记录 QLM 职责范围内的可观察行为。

## Intent and observable behavior

- training profile v2：`design` 为 `opd-v4-native1-2-5f-900s-v2`，schema `qlm-opd-v4-training-profile-v2`，
  新增 `training_tasks`（10 个任务去掉 `sweep_block_to_zone`）。`training_horizons_s` 与 train800 pool 不变。
- `EpisodeSchedule` 的 decks、计数、cursor 与 round-robin 只覆盖 `training_tasks` 的 9 个任务；sweep 永不被 reserve。
  pool 仍要求 10 任务 800 resets（`training_pool.validate` 不改）。
- 训练视频 case 换成 turn_valve 的 train reset `turn_valve-20261016-001`（场景已在 train pool，AMD 无需新增资源）。
  方案原写 validation reset，但 turn_valve 每个候选场景独立，validation 场景不在 pool；用户 2026-10-31 选定 train reset。
- `training_compatibility.json` 的 `version` 升为 `native1-2-5f900s-v2`；运行时指纹随 `training_control.py` 变化。

## Compatibility and non-goals

- 新 profile 与 v1 不兼容；v1 的 schedule 快照不能恢复到 v2 schedule（profile digest 不同）。
- 不改 physics、RAMBO、渲染、pool、评测 horizon 与成功判据。

## Evidence threshold and acceptance scenarios

QLM pytest 通过；新增测试覆盖 9 任务调度、sweep 永不被 reserve、pool 仍为 10 任务，以及视频 case 绑定 train pool 场景。

## Migration and rollback

管理员重新生成 training profile（WAM `configure`），重跑完整链。回滚 = 不 merge。
