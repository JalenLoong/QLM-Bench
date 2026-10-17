---
id: QLM-DATA-018
type: exec-plan
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
- [x] 新frozen recipe四角point retarget实际验证通过，原范围不缩小。
- [x] Task-aware producer/admission source与CPU/artifact检查；冻结10槽/候选/scene/seed/recipe/source。
- [x] 自动实际physics筛选，成功trace独立offline rendering与Raw/Canonical/terminal/full-media验收；失败轻量日志。
- [x] WAM双路线各task一次actual admission，逐条QLM验证/动作/coverage/throughput报告。
- [x] 10条审核页完整交付，保留active等待user pilot质量批准。

## Validation / recovery

审计根workspace runs/audit/press-formal-pilots-20261015-v1/；data根data/qlm_bench/press-approved-pilot-20261015-v1/。每slot最多5个预声明candidate、全批最多30physics attempts、连续10失败停止；不能无限换seed、移易目标或偷偷缩范围。先2个独立one-world physics进程，render最多2，成功trace backlog最多4；RAM低于2GiB或swap增长512MiB停止派发并排空。每world独立controller history/RNG，queue单写者。系统/源/resource/contract错误fail-closed；成功trace render初次+2 retries，媒体问题不重跑physics。

Quality依据已批准recipe与实际joint/足端/contact/terminal；不把任务成功当动作合格，不把unknown contact当失败。正式task input首先正确Press profile/goal/progress、物理/录制来源分离、独立predicate字段，真实原VAE与10D需要本task gate。全部source/attempts/artifacts版本化，不修改历史。

## Non-goals / outcomes

十条formal Press工程交付完成，用户动作质量批准尚pending；整体accepted仍为Push100。无100/其他task/正式训练/AMD/commit/push/HF或模型发布。若frozen新recipe在范围重验失败，先分析适配实现，不改变已批准范围或controller；高影响recipe/contract修改才集中确认。

## Decision log / 2026-10-15

Push旧录制profile要求一次绑定十条，不能在保持backlog4时直接复用。增加明确Press pilot-slot schema：每success绑定不可变十槽campaign hash、实际trace/quality/source/资源和单独录制身份；原十槽Push与100 schema保持。单writer campaign负责2/8/alltrain/上限，RenditionQueue负责每slot媒体重试。仍是一物理轨迹一demonstration，不把reference/retarget计入配额。行为抖动超过已审阅reference邻域(推进hip range15deg或10ms step2deg)仅暂停实际成功样本以人工检查，不改task success，unknown contact不拒绝；最终用户动作质量gate保持。

## Actual evidence / 2026-10-15

新recipe四角技术重验4/4 success，原范围不缩小、零body-object contact。50个candidate资源/geometry/preset/seed在campaign c10cdc2cc6e26a49339dd8516b7b37870436c815e349b961d4689372b5999fd8冻结；clipped retry候选可能重复的问题在物理开工前修正，首轮准备移至preparation-attempt-01，仅资源准备，无formal physical execution。首两条Clean实际通过，推进hip摆幅5.66/5.06deg、最大10ms0.926/0.981deg，两条Raw/Canonical完整media验证通过，后续Randomized运行中。

QLM159pass/13skip、4socket权限失败，host同模块11pass(含四项失败复核)。双WAM常规checks各出现本地socket权限失败；v3单项host通过，v2首host挂起保留/终止并进行CPU-only explicit-loopback120s有界复核；不改training源代码。当前尚不声明WAM task实际readback通过。

## Press十条formal pilots技术交付，等待用户质量审核 — 2026-10-15

新reference及三资产/wallY/Z范围已获批准；新recipe四角重验4/4通过。QLM-DATA-018完成10条新真实primary A trajectories(2Clean/8Randomized alltrain)，6735actions/6745boundaries；10次首次物理执行均成功，零body-button contact，无范围收缩或backup配额。原RAMBO/native9/500-100-50Hz/真实12mm三tick/not-fallen/camera/360p50FPS保持，Native OSMesa mirror不推进physics。完整Raw/Canonical、实际articulation snapshot、terminal/原telemetry逐列、媒体与唯一身份检查通过。推进FL hip摆幅4.60–5.66deg，最大10ms1.127deg；保留原gait小波动，task success与动作质量分开。

v2 DATA-017/v3 DATA-007完成Press各一次实际Clean+Randomized Reader/原VAE/SFT-input/online/caches回读与v3实际10D，Press instruction embedding匹配；两模型works归档。今后同task扩100不重复WAM验证。2physics+2render/最多4积压，实际pipeline 1054.0s≈34.2条/h，RAM最低10.79GiB，无swap增长/资源guard；task一次WAM与最后渲染并行，此吞吐非稳定生产保证。

审核入口workspace runs/audit/press-formal-pilots-20261015-v1/review.html、report.md；data/qlm_bench/press-approved-pilot-20261015-v1/。QLM-DATA-018保持active等待指定十条动作质量/覆盖/吞吐用户审核，未批准前不100/其他task。Push100用户验收及原reference/asset qualification/receipts/source heads保持。无正式训练/AMD/commit/push/HF或发布。

## Remaining gate

十条动作质量/覆盖/吞吐用户审核pending，review通过后才扩100。工程交付已完整；本QLM work在用户review前保持active，不把API compatibility当policy性能或用户质量批准。

## 用户最终pilot质量审核通过 — 2026-10-15

用户明确批准全部十条并授权计入Press100，新QLM-DATA-019补90条、4physics+4render、双WAM不重复、交付后随机抽10。原pending-review receipts保留历史身份，新审批记录workspace runs/audit/press-scale100-20261015-v1/user-approval.json。
