---
id: QLM-RL-V2-CONTEXT-ROUTING
type: governance
status: accepted
related_work: [workspace/WS-DOC-001]
source_map: []
---

# Agent context 路由

本次统一 Work ID：`workspace/WS-DOC-001`。权威登记是
[workspace registry](../../../../docs/governance/work-registry.json)；当前状态是
[handoff-20261029](../current/handoff-20261029.md)，管理文档只报告已核对事实与明确缺口。
[管理员反馈](../../../../docs/evidence/amd-feedback-20261028.md)是外部原始记录，
[会话摘录](../../../../runs/audit/workspace-context-reorganization-20261029-v1/thread-evidence.json)保留后续 W&B 读取结论与来源。
外部记录须标明截至时点，不能当作本轮实时集群核验。

## Registry 与 Work ID 的消歧

历史 registry 在本次整理中保持不变：
- [QLM scale-up registry](../scaleup-v1/work-registry.json)记录 `QLM-SIM-023` 至 `QLM-SIM-026`、`QLM-DOC-011/012` 等 RL 配对工作。
- [历史共享 registry](work-registry.json)与 [scale-up work index](../scaleup-v1/work/INDEX.md)用于检索旧记录。

WAM 原 MuJoCo SFT checkout 与 RL checkout 中，历史 `mujoco-v2/DOC-007` / `DOC-008` 指向不同工作。
因此完整定位键是 **repository + 实际 Git branch + registry namespace + Work ID**；引用时同时给出文件路径。
不要合并这些历史记录或把另一 branch 的同号任务当作本任务。
新跨 workspace 工作使用 `workspace/WS-DOC-001`，由 workspace registry 登记参与仓库，不复用旧同号条目。
未来 RL 实现须先确认明确的 RL 工作范围及新登记位置，沿用既有单调编号时仍携带 branch 定位；不能修改历史身份来规避冲突。

## 历史入口的处理

`docs/history/context-before-20261029/` 是被替换入口的逐字节快照，不作为当前规则。
原 source-publication、review、run manifest、registry 与历史 active/archive 记录保持原字节。
旧 active 状态代表该 branch 分叉时保存的工作快照，不意味着当前有正在运行的服务，也不授权恢复。
查运行状态必须核对对应 branch 的当前交接页、run manifest/执行状态和有时间戳的外部证据。

本次文档整理不改变通用治理协议，不重命名既有 Work ID，不自动升级算法/实验 claim。
纯文档验证不触发训练或 simulator rollout；后续实现只按实际影响选择必要检查。
