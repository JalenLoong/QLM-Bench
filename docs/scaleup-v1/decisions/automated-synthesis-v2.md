---
id: QLM-AUTOMATED-SYNTHESIS-V2
type: decision
status: accepted
related_work: [QLM-DATA-015]
source_map: []
---


## 2026-10-15：剩余六task审核流程覆盖

[最新用户决定](remaining-six-batch-approval.md)对剩余六task取代旧10pilot人工gate：全部资产→各task reference/范围→逐task直接100。每task一次consumer检查仍在最早Clean+Randomized实际production准入执行且计入100；不增加模型验证频率、人工pilot审核或新的固定10条配额。四个已验收task及历史receipts不回写。

> 2026-10-15用户最新采用配置（QLM-DOC-006）：后续本地目标为[Native CPU physics／原RAMBO CPU＋EGL GPU rendering，4physics＋4render](local-synthesis-concurrency.md)，维持重叠流水线和原资源保护，替代旧本地3+3建议。以下CUDA/OSMesa baseline及旧launch叙述保留其实际历史身份；本次仅治理，不代表producer已完成切换或端到端准入。OSMesa跨平台reference与AMD路线保持，当前任务审核状态以task-synthesis-progress.md为准。



# Phase 0–6 新一轮 Push Box 合成授权

2026-10-14，用户确认完整 Phase0–6，不只停留在规格讨论。目标是10条合格
Push formal pilots，2Clean/8Randomized、全部train，同一 Canonical 由v2/v3消费。
配对工作 QLM-DATA-015 / shared-v2 DATA-016 / v3 DATA-006。
执行记录见 [active plan](../work/archive/QLM-DATA-015/plan.md)。

## 已确认的约束

- 两个审核点：高质量reference及retarget适用范围；十条pilot的动作质量/覆盖/吞吐。
  普通工程细节自主推进，gate1通过前不开始依赖其recipe的新正式pilot批次。
- 原 task success predicate 不变，demonstration eligibility 单独管理。缺失/不确定
  FL contact是unknown，不等于失败；body contact计数也不自动证明操作依赖机身。
  拒绝入SFT必须有可靠实际行为证据。保留task outcome和质量判断各自的来源。
- Clean允许nominal附近的小范围真实几何变化。各split从同一批准ID分布抽取不同
  配置；去除重复trajectory和跨split近重复config，不划互斥几何范围，不引入OOD榜。
- Box05优先；每task一个primary、最多两个backup。只登记现有backup的真实状态，
  未批准backup不阻塞primary，不新增配额、不恢复已撤回P3资产。
- 旧十条保持原身份；逐条审核复用资格，不自动纳入新pilot、不整体废弃。
  纯render变化可重录；reference/executor/物理操作变化必须重新执行相关轨迹。
- ap_00/ap_01两个背景、无clutter、无强制Recovery；CUDA-MJWarp、Native OSMesa、
  LOD a02、原RAMBO/native9/force-zero、policy640x360@50FPS和Observer720p@25FPS保持。
- 执行频率不等于存储频率。保留实际Raw/Canonical必需字段、50Hz boundaries、
  physical snapshots、完整command confirmation和terminal；其他高频诊断按需要显式保留。
  不改controller内部history/physics执行；不自动清理已有数据或证据。

## Phase0 已发现的存储依赖

当前冻结Raw validator在 `compatibility/dataset_v2/validation.py` 明确要求
controller stream有2N行、physics stream有10N+1行及各自字段。Canonical并不需要这些
高频streams。新PhysicalTrace不能仅因runtime执行500/100Hz就强制包含所有额外诊断；
但导出当前Raw仍需这些必需stream，不能丢弃、伪造或默默绕过validator。
本次reference诊断复用现有collector的required Raw-compatible telemetry，明确为
兼容性/姿态证据需要，不扩展成所有成功trajectory永远保存全部diagnostic的规定。
Phase1/2在正式采集前进一步区分唯一Raw记录与可选诊断/重复capture，记录实际字段依赖。

## 执行边界

优先完成旧reference/十条数值质量分析，再开发新版本高层reference/retarget并验证。
QLM-SIM-015已退役；不恢复其源码或声称复现差异已解决。所有新结果独立版本化。
证据：workspace `runs/audit/automated-push-quality-20261014-v1/`。
本授权不包括100条扩量、其他task采集、AMD、正式训练、commit/push或发布。

## Retarget 范围获批，启动十条正式 pilot — 2026-10-14

用户明确回复“审核通过，继续推进”，通过已展示的 reference/retarget 第一审核点。
继续既有 QLM-DATA-015 / v2 DATA-016 / v3 DATA-006，冻结 smooth-v3 与两套背景。
正式采样仍为 Box dx±4cm、dy±3.5cm、yaw±0.06rad，goal dx±3cm、dy±2cm；
2 Clean 有小幅真实几何差异，8 Randomized 覆盖正负和组合偏移，全部 train。
每槽预声明5个候选，最多30次实际尝试，连续10次失败即停；不按结果收缩范围。
复用 PhysicalTrace 与 RenditionQueue。先保留最多十条成功 trace，再冻结独立
recording profile；这是本轮有界缓冲，不是100/1000条积压策略。
保留独立行为证据与完整 task success 判据；contact unknown 不自动拒绝。
旧十条不计入新批次：新 executor 要求新的实际执行，旧身份和逐条审核记录保留。
审计根为 workspace runs/audit/push-formal-pilots-20261014-v2/。
十条最终动作质量/覆盖/吞吐仍须用户审核；无100、其他任务、训练、AMD、发布或commit/push。

## Clean 背景配置修正与当前审计根 — 2026-10-14

后续逐项核对handoff发现初批第二条Clean错误分配ap_01；Clean必须ap_00。
这是实现配置遗漏，不是用户批准的范围变化。旧批次暂停，全部trace/媒体/日志保留于
runs/audit/push-formal-pilots-20261014-v2/，configuration-correction.json记录纠正。
当前执行根为runs/audit/push-formal-pilots-20261014-v3/，正式数据根为
data/qlm_bench/push-approved-pilot-20261014-v3/。第二条Clean已用ap_00重新执行成功，
其余九条trace原路径/原hash/原物理身份保留；五条合规旧媒体可经精确hash校验重新封装，
记录原render lineage，不冒充新物理或新渲染。新profile强制Clean ap_00并有回归测试。
共实际12个candidate：10条本包合规成功、1次timeout、1条成功但背景配置不合规的历史样本。
当前十条共4464 actions / 4474 boundaries；最终用户审核仍pending，无100/训练/AMD/发布。

## 十条新正式 pilot 技术交付；等待最终用户审核 — 2026-10-14

QLM-DATA-015 / v2 DATA-016 / v3 DATA-006 的 Phase0–6 工程交付完成，保留 active
等待既定的十条pilot动作质量/覆盖/吞吐审核。当前审计根为
runs/audit/push-formal-pilots-20261014-v3/，review.html/report.md为最终审核入口；
数据为data/qlm_bench/push-approved-pilot-20261014-v3/。2Clean均ap_00；
8Randomized覆盖ap_00/ap_01及批准的box/goal范围，全部train、仅primaryBox05。
最终4464 actions / 4474 boundaries；原判据、native9/RAMBO、physics/camera保持。
实际共12个candidate：10条合规交付、1次timeout、1条成功但Clean背景配置错误的
历史样本。修正只新执行一条Clean，保留九条合规trace；五条已完成媒体逐字节复用，
原render lineage显式保留。错误批次和全部历史证据保留，不隐去配置纠正成本。
全部Raw/Canonical/terminal/媒体/原telemetry验证通过；双WAM各自Clean/Randomized
实际原VAE、SFT-input、online反馈与cache检查通过，另有十条完整采样RGB与action/
timestamp/tail读取，两路线逐字节一致。无normalizer fitting、训练或policy性能声明。
QLM当前回归140pass/13skip；WAM v2/v3基础回归131/59pass，socket沙箱失败及
复核记录保留。本批未知contact不自动拒绝，task success和demonstration quality分离。
保持最终用户审核gate；没有100、其他任务、AMD、训练、commit/push或远端发布。

## 已批准Push100；WAM兼容性每task一次 — 2026-10-14

用户已批准push-formal-pilots-20261014-v3的十条，计入Push Box100条；新QLM-DATA-016补90条，最终80train/10validation/10test，各split Clean/Randomized=20%/80%。旧十条pilot审核停止要求至此已满足。
WAM adaptation v2/v3兼容性检查按task执行一次。Push Box已有通过记录，扩量及同task后续批次不再重复Reader/VAE/cache/SFT-input/online验证，不生成这些缓存。逐条QLM物理结果、独立动作质量、Raw/Canonical、媒体、timestamp/terminal和split去重仍保留。未来若冻结contract确实改变，以独立变更评审处理，不能把普通批次重复验证设为默认流程。
用户明确授权删除本轮pilot验证派生缓存，保留验证result/manifest/hash和原始数据/模型。当前source与100条审计根为runs/audit/push-scale100-20261014-v1/；v2 DOC-012/v3 DOC-011记录规则与清理。无训练/AMD/其他任务/commit/push/发布。

## Push Box100本地数据交付完成 — 2026-10-14

QLM-DATA-016完成原批准10条＋新90条，共100条；train80(16Clean/64Randomized)、validation10(2/8)、test10(2/8)。100条真实物理身份唯一，跨split配置无近重复，原native9/RAMBO/physics/camera/success predicate/primaryBox05及批准范围保持。最终44563actions/44663boundaries。完整Raw视图与Canonical在data/qlm_bench/push100-20261014-v1/。
用户授权后实际试跑2＋2、3＋2和4physics＋3render；4＋3持续运行触发swap保护后，剩余13条降到3＋2完成。独立进程controller history/RNG/world，实际launch-policy和resource guard全记录；没有修改冻结physics源代码。WAM v2/v3验证每task一次，Push Box已有证据可复用，本次90条不重复验证、不产生模型验证缓存；34项旧pilot验证缓存payload约12.3MiB已删除，结果/manifest/来源metadata保留。
QLM-DATA-016及v2 DOC-012/v3 DOC-011均归档。审计与完整交付报告：runs/audit/push-scale100-20261014-v1/。其他9task、训练、AMD、发布及commit/push未执行。
