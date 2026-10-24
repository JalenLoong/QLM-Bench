---
id: OPD-V4-SOURCE-PUBLICATION-007
type: current-design
status: accepted
related_work: [OPD-007]
source_map: []
---
# OPD-007 reviewed source publication

2026-10-24，用户授权的两个OPD worktree全部待提交实现、审核修复、测试与文档已统一提交，
普通push到全部三个配置的GitHub push targets；没有force push。

- WAM-Policy-opd-v4：`opd/v4_Streaming-OPD_on_WAM-Policy`，source commit `6b5b4debdeaa802b0704f1bab9c55b097f4ba3b0`，75个变更文件。
  Target：`git@github.com:AIGeeksGroup/WAM-Policy.git`。
  Target：`git@github.com:JalenLoong/WAM-Policy.git`。
- QLM-Bench-opd-v4：`training/opd-v4-streaming-cpu`，source commit `58fd720347d3ccb0f9ac2b442c13db114bf2be15`，41个变更文件。
  Target：`git@github.com:JalenLoong/QLM-Bench.git`。

每个target均从GitHub fetch到全新、无alternates的独立bare Git数据库，核对完整commit对象、
root tree与全tree条目，并逐一回读本次变更文件的Git blob和SHA256；三目标均一致。
本页记录source提交；后续仅文档归档的closure提交与最终远端tip由workspace
runs/audit/opd-v4-source-publication-20261024-v1/completion.json及final-independent-readback.json记录。

Runtime源码hash与OPD-006通过的版本相同，沿用WAM202pass/21skip、QLM283pass/13skip和
双rankGloo参数差0的既有证据；本轮没有重跑模型或physics。当前文档、import boundaries、
配对governance与Git whitespace检查通过。历史执行source/receipt不改写为新commit。

原OPD-001至006的“未commit/push”只描述当时状态，本次明确授权和实际发布取代其当前发布限制。
新克隆可以使用本页精确source commit或其后续closure commit；不能只使用原父commit。
源码Git归档不包含工作区权重、train800 pool、冻结资源、virtualenv或目标主机依赖。
管理员仍需按目标地址configure/relocate并完成ROCm/OSMesa和真实三角色/八流准入。

本轮不连接AMD、不训练、不加载完整5B、不发布模型/数据、不创建PR，也不操作原评估、媒体、
服务和automation。正式400S及目标硬件验收仍未执行。
