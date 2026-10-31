# Quadrupedal OPD 文档索引

本 worktree 只路由 `opd/v4_Streaming-OPD_on_WAM-Policy` 与 `training/opd-v4-streaming-cpu` 的配对工作。当前事实按下面顺序读取；旧 SFT、数据采集和 evaluation 文档保留历史，不构成当前执行计划。

## 当前入口

- [2026-10-29 交接状态：源码、部署证据和待办](current/opd-v4-handoff-20261029.md)。
- [OPD-014 兼容性简化、旧 run 续接与 EMLINK](current/opd-v4-compatibility-014.md)；用户随后已 local commit，发布/AMD 验证状态见交接页。
- [配套 WAM 管理员 runbook](../../WAM-Policy-opd-v4/README.md)。
- [运行接口](current/opd-v4-training.md)，结合后续 OPD-005/014 修订；早期 2/4 NFE 等描述为历史。

## 当前算法与已有交付

- [算法 design](design/opd-v4/OPD-v4_Streaming-OPD_method_scheme.md)、[mixed-task 合同](design/opd-v4/OPD-v4_mixed-task_WAM-Policy.md)。
- [OPD-005 当前实现](current/opd-v4-implementation-005.md)：1/2 NFE、3F→1S、400S/1200F。
- [OPD-006 审核](current/opd-v4-independent-review-006.md)、[OPD-008 Stage2-only Slurm](current/opd-v4-slurm-008.md)。
- [HF dataset 获取地址](current/opd-v4-hf-dataset-011.md)、[checkpoint uploader](current/opd-v4-hf-publication-012.md)、[OPD-013 已发布源码记录](current/opd-v4-source-publication-013.md)。
- [兼容性决策 ADR-0005](decisions/opd-v4/ADR-0005.md)。其余 ADR 按对应日期与 superseding 关系阅读。

## 管理与证据

- [原文档治理协议](governance/documentation.md)、[本分支路由与继承历史边界](governance/context-routing.md)、[执行计划规则](../.agent/PLANS.md)。
- [OPD Work registry](governance/opd-v4-work-registry.json)，通过每条记录查找 paired ChangeSpec / ExecPlan。
- [OPD-014 原执行计划](work/archive/OPD-014/plan.md)、[OPD-014 原变更规格](changes/archive/OPD-014/change-spec.md)。
- [OPD-015 审查跟进与预测视频](work/archive/OPD-015/plan.md)、[变更规格](changes/archive/OPD-015/change-spec.md)。
- [OPD-016 放宽旧 run 的 WAM 全源码指纹](work/archive/OPD-016/plan.md)、[变更规格](changes/archive/OPD-016/change-spec.md)。
- [OPD-017 提交前 AMD 审查修复](work/archive/OPD-017/plan.md)、[变更规格](changes/archive/OPD-017/change-spec.md)。
- [OPD-019 第二次 formal 的 v2 训练配置（QLM 侧：profile v2、9 任务调度、turn_valve 视频 case）](work/archive/OPD-019/plan.md)、[变更规格](changes/archive/OPD-019/change-spec.md)。
- [整理前完整索引和 AGENTS 快照](history/context-before-20261029/README.md)：早期 Isaac、MuJoCo、SFT、数据与 evaluation 记录的检索入口；内部相对链接按原位置解析。

当前 workspace 文档工作为 workspace/WS-DOC-001。运行状态以实际 run/attempt 证据为准；“源码已交付”“local commit”“已发布”“AMD 通过”“算法有效”分别记录。
