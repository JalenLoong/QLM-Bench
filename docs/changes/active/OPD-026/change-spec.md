---
id: OPD-026
type: change
status: active
source_map:
  - docs/governance/opd-v4-work-registry.json
---
# ChangeSpec: OPD-026 cache 逐轮写盘、cache 进 W&B、分层 held-out、单卡八进程测试（QLM 侧镜像）

变更全部在 WAM（见 [WAM ChangeSpec](../../../../../WAM-Policy-opd-v4/docs/changes/active/OPD-026/change-spec.md)）。QLM 源码、`training_compatibility.json` 与 runtime 指纹 `0666c125…` 不变；WAM 的 8 进程测试使用本仓库真实的 `SynchronousDriver`。训练 horizon 与标准评测 horizon 的差异（push_box、close_oven_door、open_room_door）只记录在 WAM ExecPlan，待用户决定，本仓库未改。
