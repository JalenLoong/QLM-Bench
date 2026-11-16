---
id: OPD-032
type: exec-plan
status: active
source_map:
  - src/qlm_bench/backends/mujoco/training_control.py
---
# ExecPlan: OPD-032 M-OPD v1.1（QLM 侧）

实施与验证以 [WAM ExecPlan](../../../../../WAM-Policy-mopd-v1.1/docs/work/active/OPD-032/plan.md) 为准。

- [x] profile 接受含 sweep 的子集；默认 9 任务不变。
- [x] `tests/qlm/test_opd_episode_schedule.py` 按新规则改两处断言（十任务上限 2 与只有 sweep 的子集现在被接受）。
- [x] registry 镜像。
