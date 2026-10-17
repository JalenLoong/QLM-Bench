---
id: QLM-DATA-018
type: change
status: completed
source_map: []
---

# Press Button十条formal pilots

## Purpose / scope

用户明确批准新reference和此前资产/墙面范围。冻结press-body-carry-v2与recipe-config；先对四个已批准Y/Z角点/ap_00/ap_01重验，再自动合成10条formal Press pilots(2Clean/8Randomized、全部train)，primary A only，不为backup增加quota。reference/dev diagnostics不计quota，十条用户审核后才扩100。

## Contracts / implementation

保持native9/force-zero/原RAMBO/history、500/100/50Hz、真实12mm/三tick/not-fallen/24s、wall/collision/asset/camera/FoV/dual-rgb-360p-v1/50FPS及Observer720p25FPS。Clean有真实小Y/Z变化，ap_00；Randomized在同一批准ID范围，ap_00/ap_01，无clutter/Recovery要求。不同split仍来自同一ID分布且不近重复。

复用PhysicalTrace/RenditionQueue/offline Native mirror/VideoSink/Raw/Canonical转换。只去除目前render producer与admission的Push专用绑定，增加明确Press task/profile/predicate质量字段；旧Push schema/100数据/receipt不改写，不伪造full-footprint字段，不修改冻结storage列/hash。task success与behaviour quality分离，unknown contact不硬失败。完整command确认、50Hz实际snapshot/terminal及Raw已有必需streams保留，不额外强制所有diagnostic。

WAM v2/v3 compatibility每task一次：Press正式task尚not_run，本工作用各路线一条Clean与Randomized做一次Reader/VAE/SFT-input/online-input资格，不逐episode重复，不训练/fit normalizer。完成后记录task-once证据，后续100不用重做。同步shared-v2 DATA-017和v3 DATA-007，模型/环境/source namespaces分开。

## Milestones / Progress

- [x] 记录新reference批准，归档DATA017，注册新works和保护项。
- [ ] 新frozen recipe四角point retarget实际验证通过，原范围不缩小。
- [ ] Task-aware producer/admission source与CPU/artifact检查；冻结10槽/候选/scene/seed/recipe/source。
- [ ] 自动实际physics筛选，成功trace独立offline rendering与Raw/Canonical/terminal/full-media验收；失败轻量日志。
- [ ] WAM双路线各task一次actual admission，逐条QLM验证/动作/coverage/throughput报告。
- [ ] 10条审核页完整交付，保留active等待user pilot质量批准。

## Validation / recovery

审计根workspace runs/audit/press-formal-pilots-20261015-v1/；data根data/qlm_bench/press-approved-pilot-20261015-v1/。每slot最多5个预声明candidate、全批最多30physics attempts、连续10失败停止；不能无限换seed、移易目标或偷偷缩范围。先2个独立one-world physics进程，render最多2，成功trace backlog最多4；RAM低于2GiB或swap增长512MiB停止派发并排空。每world独立controller history/RNG，queue单写者。系统/源/resource/contract错误fail-closed；成功trace render初次+2 retries，媒体问题不重跑physics。

Quality依据已批准recipe与实际joint/足端/contact/terminal；不把任务成功当动作合格，不把unknown contact当失败。正式task input首先正确Press profile/goal/progress、物理/录制来源分离、独立predicate字段，真实原VAE与10D需要本task gate。全部source/attempts/artifacts版本化，不修改历史。

## Non-goals / outcomes

当前formal Press=0。无100/其他task/正式训练/AMD/commit/push/HF或模型发布。若frozen新recipe在范围重验失败，先分析适配实现，不改变已批准范围或controller；高影响recipe/contract修改才集中确认。

## 用户最终pilot质量审核通过 — 2026-10-15

用户明确批准全部十条并授权计入Press100，新QLM-DATA-019补90条、4physics+4render、双WAM不重复、交付后随机抽10。原pending-review receipts保留历史身份，新审批记录workspace runs/audit/press-scale100-20261015-v1/user-approval.json。
