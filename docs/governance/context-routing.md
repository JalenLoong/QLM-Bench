---
id: OPD-V4-CONTEXT-ROUTING
type: governance
status: accepted
related_work: [workspace/WS-DOC-001]
source_map: []
---
# Quadrupedal OPD context 路由

本页落实现有文档治理协议，限定本 worktree 的上下文边界，不改变算法、runtime、registry 历史或发布状态。

| 问题 | 当前入口 |
|---|---|
| 这条路线目前做到哪、缺什么 | [交接状态](../current/opd-v4-handoff-20261029.md) |
| 当前算法与训练合同 | [OPD design](../design/opd-v4/OPD-v4_Streaming-OPD_method_scheme.md)、[OPD-005](../current/opd-v4-implementation-005.md)、[OPD-014](../current/opd-v4-compatibility-014.md) |
| OPD Work ID、配对计划和完成范围 | [OPD registry](opd-v4-work-registry.json) |
| 当次真实执行 | run manifest / W&B / workspace audit；将管理员记录与本机复现分开 |
| 早期 Isaac/MuJoCo 数据、SFT 和旧评估 | 原 registry/archived plan；仅作为继承历史按需检索 |

共享适配、MuJoCo 和 QLM scaleup 的 registry、work index、active plan 在 branch 创建时被继承。保留原文件有助于追溯，不能把它们当作当前 OPD 的运行队列，也不能因此恢复旧任务。需要跨路线核对时回到 workspace 的目录与状态索引。

历史 Work ID 必须连同 repository、branch、namespace 引用；单独的 DOC-008 或 ALG-001 不保证全 workspace 唯一。本次整理使用 workspace/WS-DOC-001，统一登记在 workspace docs/governance/work-registry.json。OPD 后续实现继续使用两仓库配对的 OPD registry，不复用旧编号。

旧入口全文保存在 [context-before-20261029](../history/context-before-20261029/README.md)。旧文档中的未提交、not_run、暂停与当时授权是原时点事实；最新交接页追加后来状态，不改写原 completion、manifest、ADR 和 registry。
