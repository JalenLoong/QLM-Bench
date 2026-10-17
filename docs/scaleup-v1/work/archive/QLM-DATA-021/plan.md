---
id: QLM-DATA-021
type: exec-plan
status: completed
source_map: []
---

# Approved Lift A reference/scope: ten2Clean8Randomized formal pilots; bounded4physics+4render trial, task-once dual-WAM

## Scope / contracts

用户批准Lift参考动作及dx/dy±3cm、yaw±5deg与两Background，指定A OASIS主资产。冻结lift-body-lane-geometry-v2和原模型/pose/solver/500-100-50Hz、native9/force-zero、dual-rgb-360p-v1/OSMesa、whole-geometry minimum clearance20mm/notfallen/三tick。两个Clean为真实小幅几何差异且ap00，八Randomized覆盖批准ID和两背景，全部train。A/B/C pool角色及真实资格固定，backup无配额且不阻塞primary。新十条不能用旧reference/旧scope诊断冒充；每slot预声明5candidate，最多30physics attempts/连续失败10即停，失败仅轻量日志；成功PhysicalTrace支持render-only retry3次。

复用现有PhysicalTrace/RenderMirror/Raw/Canonical/媒体校验/queue recovery。新增Lift rendition admission只实现原2cm三tick谓词，不修改task/schema。完整50Hz边界/必要实际snapshot/command confirmation/terminal保留，明确reference diagnostic高频不加到全项目新长期保留规则；原controller/history不变。sphere-only FL contact零/unknown不是硬拒绝，真实FL腿部穿孔/接触与base协同独立质量证据管理，task成功不代替质量。

尝试实际4physics+4render并发，记录launch epoch/max实际重叠、RAM/GPU/swap和吞吐。pressure停止派发并排空保留全部成功trace；若4+4不安全，可有据降档以完成十条，不改source/recipe/分布。严重低RAM时允许有记录终止render-only worker并用相同trace重试，不能误启动100或重做成功physics。正式首批所有判据通过仍需用户动作质量/覆盖/吞吐审批。

WAM v2/v3仅本Lift task一次实际Clean+Randomized Reader/原VAE/SFT-input/online/caches对照；用Lift正确prompt、保留原normalizers/weights，不fit/训练。Push/Press不重复，不全批逐条WAM encoding；QLM逐条physics/Raw/Canonical/media/terminal/去重校验保留。sim/model独立环境和public API，无source交叉import。资产包许可unknown记录不改写，不远端发布。

## Progress

- [x] 2026-10-15 记录用户reference/scope批准，归档DATA020。
- [x] 冻结asset pool、recipe/source、2Clean8Randomized与50个candidate/录制身份；campaign SHA61f2e8041b053304b6c7832b4ec9432337a722c3052a51548200d34bda3ac014。
- [x] 27项准入回归通过；完整十条Raw/Canonical/媒体/原telemetry/接触几何/唯一身份及review交付。4+4仅尝试，真实并发及资源恢复保留。
- [x] v2/v3各一次Clean/Randomized实际资格通过并归档；原602项资源与三HEAD保持，source/治理最终复核见completion。
- [x] 用户本轮明确批准全部十条，计入100；QLM-DATA-022负责新增90条。

## Validation / recovery

workspace runs/audit/lift-formal-pilots-20261015-v1/；data/qlm_bench/lift-approved-pilot-20261015-v1/。原reference/Push100/Press100/asset/weights/环境lock/三HEAD保护。变更前源文件hash固定，新增Lift测试覆盖whole geometry/三tick/错schema/错task/unknown contact/实际snapshot与目标字段。保持负结果和实际并发记录，无训练、AMD、commit/push/HF或正式发布。

## Decision log / discoveries

已批准范围不是需要重新讨论的选项；Clean默认dx/dy±3mm/yaw±0.3deg，Randomized覆盖±3cm/±5deg，不扩大范围。source frozen之前闭合goal XY元数据对齐与Lift原谓词来源；原diagnostic metadata不改写。正式执行已启动；首7条首次physics均成功，媒体正在独立排空。v2/v3各Randomized代表实际Reader/VAE/SFT-input/online通过，Clean等待对应正式媒体，不重复已有代表。详细状态以campaign-state和最终receipt为准。

## Outcomes

工程交付完成；QLM-DATA-021仅等待用户十条pilot动作质量/覆盖/吞吐审核，不自动100。

### 应用层资源保护澄清

2GiB MemAvailable或本launch swap增长512MiB为现有campaign继承的保守调度阈值，非Linux默认或硬件容量结论；1.5GiB紧急render-only回收为本次新增保护，新render还要求4GiB available。通常2s采样但不是硬上限；host全局swap基准1,919,107,072B。首触发available3.278GiB/swap5.695GiB，实际为swap增量；随后available226.66MiB/swap约8GiB时回收一个render，不重做成功physics。未改系统swappiness/swap/OOM，负结果及精确event保留于workspace audit/memory-guard-explanation.json。4+4是尝试目标，实际未同时达到；允许同冻结campaign降档完成十条。

## 本轮继续授权

用户明确“继续推进，保留内存保护，先完成Lift Basket的10条pilot，完成后给我审核”。现有4+4尝试的保护/负结果保留，不提高阈值。首7条成功trace先完成媒体；原campaign/source/recipe不改，随后1physics+2render完成剩余3条，若再次实际触发保护可降1+1；其他异常fail-closed。WAM两route Clean01/Randomized04四个实际检查均通过，不重复已通过代表。工作目标仍是完整十条review，不提前100。

## 用户更新资源保护阈值 — 2026-10-15

后续新launch采用MemAvailable<1GiB暂停新physics、host swap相对本launch基准增长>6GiB触发排空、MemAvailable<0.5GiB回收最新render-only worker。机制保留，render启动门槛4GiB及pressure后上限2不变。这是用户明确更新，替代早先2GiB/512MiB/1.5GiB默认；旧launch/事件/receipt保持原值，不能改写成新值。当前已latched的初始launch先排空成功trace，下一launch用版本化resource-policy-v2.json，以1physics+2render完成剩余三条；不自动重试4+4或扩100。

workspace runs/audit/lift-formal-pilots-20261015-v1/resource-policy-v2.json与runtime-policy-v2/source-provenance.json记录用户来源、执行层source和精确bytes。只替换等待中的续跑supervisor，当前renderer未中断。原frozen QLM producer/campaign/recipe/physics/controller/camera/数据分布逐字节保持；执行层policy单独版本化，后续治理与新campaign须沿用批准阈值。当前physics与RAMBO主要Torch计算在CUDA；NativeOSMesa render为CPU软件出图，不使用EGL/GPU batch renderer。


## 后续维持流水线，默认3physics+3render — 2026-10-15

用户最新明确维持physics与rendering同时推进，后续新launch默认3physics+3render；不采用先全physics再render的阶段模式。资源保护使用最新1GiB available/6GiB launch-relative swap growth/0.5GiB render-only eviction；既有4GiB新render启动门槛和pressure后的排空机制保持。3+3是配置目标，实际重叠与稳定性按launch/resource证据记录，不预先宣称通过。

当前Lift十条的第二launch已经以1+2运行，保留该实际配置完成，不中断worker、不重跑成功physics或旧媒体，也不改写旧launch。完成十条后交用户审核，未批准前不100。批准来源workspace runs/audit/lift-formal-pilots-20261015-v1/streaming-concurrency-decision.json；stage-scheduling-assessment.json只是先前讨论，未被采用为默认路线。


## Lift Basket十条formal pilots交付；等待用户审核 — 2026-10-15

QLM-DATA-021完成全新10条2Clean/8Randomized、全部train，7506actions/7516boundaries，十个唯一物理身份；十次首次physics均成功，无范围收缩、backup配额或成功physics重跑。原A OASIS主资产、lift-body-lane-geometry-v2、dx/dy±3cm/yaw±5deg、两Background、原RAMBO/native9/force-zero、500/100/50Hz、整篮最低点20mm/notfallen/三tick保持。Clean为真实小幅几何变化，非同初态重复。

完整Raw/Canonical、50Hz boundaries/commands/terminal、原telemetry逐列与全部媒体检查通过，合并Canonical在workspace data/qlm_bench/lift-approved-pilot-20261015-v1/canonical。双RGB640×36050FPS/Observer1280×72025FPS，独立NativeOSMesa mirror不推进physics。十条完整穿孔后托举；实际CUDA50Hz snapshots在Native重建接触几何，FL腿部27–38个boundary、base合计0，不是独立CUDA force telemetry，sphere-only接触0不硬失败。task success与demonstration quality分开，不新增全体500/100Hz诊断永久保留要求。

v2 DATA-018/v3 DATA-008各一次实际Clean01+Randomized04 Reader/原VAE/SFT-input/online/cache及正确Lift prompt通过并归档，后续同task扩量不重复模型验证/cache，不fit或训练。QLM-DATA-021保持active，十条动作质量/覆盖/吞吐用户审核pending；工程交付不等于用户批准或policy success rate。

初始4+4尝试未同时达到，保留旧保护事件与一个render-only回收/同trace恢复。续跑实际1physics+2render，采用用户更新的1GiB available/6GiB launch-relative swap增长/0.5GiB render回收，未打断执行中的worker。用户最新确定后续新launch默认3+3并行流水线，不采用分阶段模式；3+3稳定性不因配置决定而被宣称通过。实际总pipeline 3895.2s≈9.24条/h，含保护排空与续跑，不是稳态保证。

审核workspace runs/audit/lift-formal-pilots-20261015-v1/review.html、report.md；完整receipt/资源policy/质量证据同目录。Push100+Press100仍为人工最终验收200/1000，Lift十条等待审核。A资产包license unknown保持，仅本地，无扩100、训练、AMD、commit/push或发布。下方pending/旧配置只描述各自原阶段。


## 用户批准

用户已审核通过全部十条，并授权按QLM-DOC-006配置扩100。原pending receipts保持其历史身份，新批准在workspace runs/audit/lift-scale100-20261015-v1/user-approval.json。
