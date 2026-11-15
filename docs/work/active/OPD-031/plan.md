---
id: OPD-031
type: exec-plan
status: active
source_map:
  - src/qlm_bench/backends/mujoco/training_control.py
---
# ExecPlan: OPD-031 M-OPD v1 的 AMD 正式链路（QLM 侧）

实施与验证以 [WAM ExecPlan](../../../../../WAM-Policy-mopd/docs/work/active/OPD-031/plan.md) 为准。

- [x] 任务子集 profile，并发上限从 profile 读；`make-profile --tasks/--max-active-per-task`。
- [x] `tests/qlm/test_opd_episode_schedule.py`：8 进程在两任务 profile（上限 4）上并发 `reserve` 全部成功、第 9 个流没有槽位；默认 profile 的原有测试不变。
- [x] registry、本记录、handoff 镜像。
