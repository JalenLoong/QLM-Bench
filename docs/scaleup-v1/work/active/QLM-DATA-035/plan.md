---
id: QLM-DATA-035
type: exec-plan
status: active
related_work: [QLM-DATA-034, QLM-DATA-028]
source_map: []
---

# Sweep A09范围验证与三reference集中审核

用户明确批准A09为Sweep reference，保留22.5cm和稳定侧触→小拨→必要时右侧移→再拨动。原动作/成功判据/RAMBO/physics/camera/seed42/40s冻结，不回写A09原结果。旧30cm范围不代表本版本。

原5维完整32角点与两背景各16保持；blockXY±2cm、yaw±5°、goal方向±4°。距离以22.5cm为中心沿用原±2cm宽度，即20.5–24.5cm，不缩宽度、不搜索seed，robot reset完整初态固定为A09。exact approved executor/recipe，只有predeclared模型布局/视觉背景改变；失败停止新派发并排空，不隐藏失败或未执行角点。普通最多3physics，1GiB available/7.6GiB launch-relative swap保护保持；无成功physics重跑。

A09批准独立receipt在workspace runs/audit/four-reference-refinement-20261016-v1/a09-user-reference-approval.json；新scope审计workspace runs/audit/sweep-a09-scope-20261016-v1/。所有model/source/recipe/初态及命令/terminal/原predicate应独立复核，task success与quality分开；未知contact不硬判失败，不新增常规成功数据500/100Hz永久存储规范。失败仅轻量日志/结果，不扩张完整失败capture。

并行复用Fridge16.76s/Oven15.62s/Valve12.72s现有三视角，集中页workspace runs/audit/four-reference-refinement-20261016-v1/fridge-oven-valve-revised-review.html；三项动作仍待用户审核，不重跑physics/WAM/cache。Oven1kg/35deg及4s时序、Fridge2s、Valve6s保持；不能借旧scope证明新版本。

Drawer/Room Door批准及原400保持。当前不开始100、新formal数据、WAM/cache/训练/AMD/commit/push/发布。完成scope结果报告及三条集中视频后等待用户审核；重大方案变化按既定规则另行确认。

## Progress

- [x] A09用户批准receipt与冻结方案，三reference既有媒体集成交审。
- [ ] 完整32角点模型及实际执行/独立验收（失败/未执行区分）。
- [x] 本轮结果与未执行点如实记录、source保护和配对治理更新；完整32点通过仍未完成。

## 几何retarget补齐与严格序列复核（不改nominal）

首轮exact-world-anchor版本按fail-closed结束：执行4/32，物理成功1条但该条停在acquire阶段，未执行批准的小拨/侧移序列，因此独立序列资格0；其余3条超时，28未执行。scope-independent-sequence-review.json纠正旧验收器只检查“已出现阶段”的不足，原task结果/source/trace均保留，不把物理成功当作reference序列通过。

发现具体适配缺口为世界坐标body anchors不随case block XY平移，且body侧移终点未适配goal距离/方向。仅补geometry-retarget-v1：body anchors按实际dx/dy平移，侧移距离按目标距离delta平移，侧移方向投影到实际goal方向。名义dx/dy/距离/方向零扰动时，与批准A09的全部合并参数、entry锚点/几何和初始native9逐项一致，reset幂等，0physics；原接触门控/小拨/判据/RAMBO保持。

新版本审计workspace runs/audit/sweep-a09-scope-20261016-v1/retarget-v1/，复用相同32模型字节/seed42/40s/两背景及范围，不缩域、不重跑nominal。此前成功但序列不合格的scope trace保留；因新retarget executor不同，必须重新做该版本实际验证，非媒体重跑。若还需改变已批准nominal动作本身，则停止并汇报；本轮只补一版必要几何适配，不继续无界调参。新验收要求实际稳定接触及first stroke，侧移后必须实际recontact/final stroke，质量仍与task success分离。

## Scope035未通过并已排空；A09 nominal批准保持，三reference待审 — 2026-10-16

QLM-DATA-035保留原5D32角点（blockXY±2cm/yaw±5°/goal方向±4°、22.5cm中心距离±2cm，两背景各16）不缩域。首轮4/32仅1 task success但无获批序列资格，28未执行；补geometry-retarget-v1后3/32虽3 task success，均未执行first stroke/侧移，序列合格0、29未执行。共7次两个版本的scope物理运行，不合并冒充32点通过；首失败停止新派发并排空，当前0physics。

已量化共同原因：操作段机身Y误差最高8.6–10.6cm，稳定足端侧触与机身停稳从未同时成立；准备阶段却追随block继续推进，导致任务成功但批准动作顺序未执行。需要加强操作期机身保持并使接触准备有界，可能影响nominal实际动作，因此本轮不继续修改获批A09，不放宽门控/成功条件或缩范围。几何retarget在零扰动下保持A09且0physics，旧task结果/trace不回写；旧“可选阶段出现才校验”不足已由独立序列复核明确纠正。

当前报告workspace runs/audit/sweep-a09-scope-20261016-v1/review.html及final-report.json。A09 nominal reference用户批准保持，完整范围验收未完成，DATA035保持active；DATA034保留其余三项动作审核。Fridge/Oven/Valve修订三视角集中页workspace runs/audit/four-reference-refinement-20261016-v1/fridge-oven-valve-revised-review.html，均复用原媒体、hash和链接通过，用户动作批准仍pending。原400/Drawer/Door/原RAMBO及source保持。暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布。


## Oven/Valve reference已批准；Sweep取消顺序门槛，DATA036续验 — 2026-10-16

用户明确批准Close Oven Door与Turn Valve修订reference，独立receipt见workspace runs/audit/four-reference-refinement-20261016-v1/{oven,valve}-user-reference-approval.json。Fridge仍待审核。Sweep参考A09，取消小拨/侧移必须按序完成的门槛，达到原task success即可；原footprint/notfallen/三tick、RAMBO、camera、22.5cm及原32范围保持。阶段/姿态诊断不独立拒收task成功，工程完整性仍须验证。

QLM-DATA-036负责新口径复核旧3成功（保留实际source、原outcome不回写且不重跑成功physics）及其余范围续跑；小拨未达量/侧移未停稳/再次接触硬等待改为可选继续分支。DATA035原“顺序不合格”是旧口径历史，不再作为当前阻塞。审计workspace runs/audit/sweep-task-success-scope-20261016-v1/。暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布；原400/Drawer/Door批准保持。


## DATA036结果：Sweep 31/32；Oven/Valve reference批准 — 2026-10-16

完整原范围验收 31/32；尚未通过，停止原因 physical_failure，未执行0个。 用户取消小拨/侧移顺序门槛，原task success和完整工程证据为准，动作/接触诊断不独立拒收。22.5cm及原32范围/两背景/seed42/40s/原RAMBO与camera不变，无缩域或seed选择。

旧Work035成功3条保留实际身份复用；Work036实际新physics30次，成功28、失败2，007原超时不回写。十条成功前缀证明不受新增6s实际几何出口影响，不重跑成功physics。最终逐条source见workspace runs/audit/sweep-task-success-scope-20261016-v1/final-report.json，审核入口同目录review.html。旧035顺序拒收只是历史。

Close Oven Door与Turn Valve合格nominal reference用户批准已登记，Fridge仍待审核；Oven/Valve修订后完整scope未在036执行。原400、Drawer/Door与108原source/三repo HEAD保持。全部在途排空，暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布。

