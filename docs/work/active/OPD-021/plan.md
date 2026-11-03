---
id: OPD-021
type: exec-plan
status: active
source_map:
  - src/qlm_bench/backends/mujoco/training_control.py
---
# ExecPlan: OPD-021 OPD-v5.0 Regression-anchored Streaming-OPD（QLM 侧镜像）

实施、验证与决策记录以 [WAM ExecPlan](../../../../../WAM-Policy-opd-v4/docs/work/active/OPD-021/plan.md) 与
[ADR-0008](../../../../../WAM-Policy-opd-v4/docs/decisions/opd-v4/ADR-0008.md) 为准。

- [x] `training_control.DESIGN` → `opd-v5-regression1-2-900s-v1`；`training_compatibility.json` version → `regression1-2-900s-v1`。
- [x] `tests/qlm/test_opd_episode_schedule.py` 的 design 断言同步。
- [x] registry、本 ChangeSpec/ExecPlan、INDEX 与 handoff 镜像。
- [ ] AMD 上以新 profile 跑 cache 采集与 formal（未执行；由 WAM handoff 的命令框架描述）。
