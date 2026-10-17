---
id: QLM-SWEEP-TASK-SUCCESS-ONLY
type: decision
status: accepted
related_work: [QLM-DATA-036, QLM-DATA-035, QLM-DATA-034]
source_map: []
---

# Sweep：A09为策略参考，取消小拨/侧移顺序门槛

用户明确要求：小拨/侧移顺序门控去掉，模仿A09策略，最后达成task success即可。此决定取代DATA035中“first stroke、侧移和再接触必须出现”的附加验收要求；旧拒收结论保留历史，不回写原task result或terminal。

原task success不变：方块完整footprint进入原goal，notfallen，连续三个实际50Hz边界，40s上限。原RAMBO/checkpoint/IK/PD/QP/history/native9/forcezero/500-100-50Hz、Native真实接触和camera保持。22.5cm nominal、原32个五维角点与两背景保持，不缩范围、不搜索seed。动作顺序/阶段标签/姿态与接触指标记录为诊断，不独立否决task成功；完整trace/source/时钟/初态/terminal仍须通过。

执行器继续参考A09接触和拨动策略，但小拨未达到位移、侧移参考轨迹结束仍未满足停稳、再次接触等待，不再造成顺序硬等待，可继续朝task目标拨动。原几何进场和控制限幅保持，不伪造稳定接触/停稳事件。

复用旧retarget-v1的三个task成功：独立验证全量trace与新口径，且逐命令确认这些旧轨迹从未进入新增可选继续分支，因此新分支对其前缀无作用；保留实际执行Work-ID/source身份，不冒充新代码执行，也不重跑成功physics。其余29角点用新的optional-order版本执行，每条实际来源均进入验收目录。不能混入其他旧版本的同名case。

Close Oven Door及Turn Valve修订reference同次获用户明确批准；独立receipt在workspace runs/audit/four-reference-refinement-20261016-v1/{oven,valve}-user-reference-approval.json。Fridge仍待审核。当前不授权100合成、WAM/cache/训练/AMD或发布，原400保持。

当前实施与验收在workspace runs/audit/sweep-task-success-scope-20261016-v1/，权威user-decision.json及各acceptance记录保留新口径来源。

## 接触前等待修复记录 — DATA036

optional-order首批已排空，复用3条与新7条成功均通过，另007在40s前始终停留lower waypoint、没有碰块，余21未执行。保留其真实timeout与轻量日志。后继geometry-entry-v3仅为高层entry等待增加6s后的实际几何出口：足端高度≤9cm、X对齐≤2.5cm、在真实有向块侧外≥5mm才进入连续侧触引导；不写qpos、不伪造contact、不改task success或RAMBO。十条成功原lower时长均≤2s，因此新出口不触发，保留实际source并复用，不重跑成功physics。原32模型/范围/seed42/40s保持，007及余21继续真实验收；首真实失败仍停派排空。

## DATA036结果：Sweep 31/32；Oven/Valve reference批准 — 2026-10-16

完整原范围验收 31/32；尚未通过，停止原因 physical_failure，未执行0个。 用户取消小拨/侧移顺序门槛，原task success和完整工程证据为准，动作/接触诊断不独立拒收。22.5cm及原32范围/两背景/seed42/40s/原RAMBO与camera不变，无缩域或seed选择。

旧Work035成功3条保留实际身份复用；Work036实际新physics30次，成功28、失败2，007原超时不回写。十条成功前缀证明不受新增6s实际几何出口影响，不重跑成功physics。最终逐条source见workspace runs/audit/sweep-task-success-scope-20261016-v1/final-report.json，审核入口同目录review.html。旧035顺序拒收只是历史。

Close Oven Door与Turn Valve合格nominal reference用户批准已登记，Fridge仍待审核；Oven/Valve修订后完整scope未在036执行。原400、Drawer/Door与108原source/三repo HEAD保持。全部在途排空，暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布。

