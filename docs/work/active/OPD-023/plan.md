---
id: OPD-023
type: exec-plan
status: active
source_map:
  - docs/governance/opd-v4-work-registry.json
---
# ExecPlan: OPD-023 offline target cache 变成 Slurm stage，`submit-matrix` 一次提交四个实验（QLM 侧镜像）

实施、验证与决策记录以 [WAM ExecPlan](../../../../../WAM-Policy-opd-v4/docs/work/active/OPD-023/plan.md) 为准。

- [x] registry、本 ChangeSpec/ExecPlan、INDEX 与 handoff 镜像（QLM 源码不变）。
- [ ] AMD 上首次 `submit-matrix` 验证 cache stage 与四条链（未执行；由 WAM handoff 描述）。
