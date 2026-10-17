---
id: QLM-DATA-036
type: exec-plan
status: active
related_work: [QLM-DATA-034, QLM-DATA-035]
source_map: []
---

# 新批准reference与Sweep仅task-success口径

用户明确批准Close Oven Door和Turn Valve修订reference，独立receipt在workspace runs/audit/four-reference-refinement-20261016-v1/{oven,valve}-user-reference-approval.json；Fridge仍待审核，不推断为拒绝。Sweep继续参考获批A09，但取消小拨/侧移顺序硬门槛，最后达到原task success即可。

原完整footprint/goal/notfallen/三50Hz tick、原RAMBO/IK/PD/QP/history/native9/forcezero/500-100-50Hz/camera、22.5cm nominal及原32模型/范围/两背景/seed42/40s保持。动作顺序、阶段标签、机身漂移和接触指标作为诊断，不再独立否决task成功；工程完整性/source/时钟/terminal仍必须通过。小拨未达量、侧移尚未停稳、再次接触等待改为可选继续拨动，保持原安全几何进场。

旧retarget-v1三条物理成功先独立复核：完整trace/原predicate通过，且从未进入新改动的等待分支时，可证明新分支对其执行前缀无作用，保留实际旧执行source身份复用，不重跑成功physics、不改原result/terminal。其余29点按新版本继续，不能混入旧exact-world-anchor不同执行的结果。所有复用及新跑来源显式列出，source不同不冒充全同一个历史版本。

审计workspace runs/audit/sweep-task-success-scope-20261016-v1/。普通最多3physics/3render和原1GiB/7.6GiB保护；首实际物理或工程完整性失败停派排空，不再因顺序缺失停止。失败仅轻量日志，未知contact不硬失败；诊断不偷改task success。当前不100/新formal/WAM/cache/训练/AMD/commit/push/发布；原400及其他批准保持。

## Progress

- [x] 两项用户批准与Sweep新口径receipt、当前index/WorkID建立。
- [x] 可选继续分支与4项零步检查通过；旧3成功全量复核复用，剩余29已开始（完整范围完成另行记录）。
- [x] 本轮32项实际结果/source/保护/治理已交付（31通过、032超时）。
- [ ] 完整范围32/32通过；未缩域或追加试跑，Work保持active。

## 接触前等待修复记录 — DATA036

optional-order首批已排空，复用3条与新7条成功均通过，另007在40s前始终停留lower waypoint、没有碰块，余21未执行。保留其真实timeout与轻量日志。后继geometry-entry-v3仅为高层entry等待增加6s后的实际几何出口：足端高度≤9cm、X对齐≤2.5cm、在真实有向块侧外≥5mm才进入连续侧触引导；不写qpos、不伪造contact、不改task success或RAMBO。十条成功原lower时长均≤2s，因此新出口不触发，保留实际source并复用，不重跑成功physics。原32模型/范围/seed42/40s保持，007及余21继续真实验收；首真实失败仍停派排空。

## DATA036结果：Sweep 31/32；Oven/Valve reference批准 — 2026-10-16

完整原范围验收 31/32；尚未通过，停止原因 physical_failure，未执行0个。 用户取消小拨/侧移顺序门槛，原task success和完整工程证据为准，动作/接触诊断不独立拒收。22.5cm及原32范围/两背景/seed42/40s/原RAMBO与camera不变，无缩域或seed选择。

旧Work035成功3条保留实际身份复用；Work036实际新physics30次，成功28、失败2，007原超时不回写。十条成功前缀证明不受新增6s实际几何出口影响，不重跑成功physics。最终逐条source见workspace runs/audit/sweep-task-success-scope-20261016-v1/final-report.json，审核入口同目录review.html。旧035顺序拒收只是历史。

Close Oven Door与Turn Valve合格nominal reference用户批准已登记，Fridge仍待审核；Oven/Valve修订后完整scope未在036执行。原400、Drawer/Door与108原source/三repo HEAD保持。全部在途排空，暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布。


用户在后继DATA037明确批准Sweep，指定A09为本task reference；批准receipt为workspace runs/audit/fridge-body-advance-reference-20261016-v1/sweep-user-approval.json。原范围31/32结果与032失败保持，不再追加Sweep尝试；此用户审批不回写原工程结果。
