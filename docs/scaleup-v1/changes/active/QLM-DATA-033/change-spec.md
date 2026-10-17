---
id: QLM-DATA-033
type: change-spec
status: active
related_work: [QLM-DATA-028, QLM-DATA-030, QLM-DATA-032]
source_map: []
---

# Door/Oven冻结方案范围与六task集中审核

用户批准Oven35deg中央前推nominal为reference，要求完成Door/Oven适用范围验证后集中交六task确认。Door使用已批准A19/28cm/实际锁舌退出历史event+15deg/notfallen/三tick；Oven使用已批准35deg中央方案/原3deg/notfallen/三tick。固定原RAMBO/checkpoint/native9/forcezero/500-100-50Hz、初始robot全状态、seed42、两背景，除预声明asset刚体pose及Oven初始门角外不改。

Door原XY±2cm/yaw±5deg×两背景，共16。Oven新35deg物理限位不允许旧40–50deg初态；本轮待最终确认提案为25–35deg，保持原10deg宽度，XY±2cm/yaw±5deg八角点×两初角共16、两背景各8。未缩变量宽度或引入OOD，非正式数据。单写者最多3physics，首个物理失败只停止该task新派发并排空，其余task独立继续；资源<1GiB或launch-relative swap增长>7.6GiB停止全部新派发并排空。成功physics不重跑，失败仅轻量记录，源/初态/模型/500-100-50Hz及terminal独立检查。

复用原四task范围与视频，完成后六task集中交审，不自动100/WAM/AMD/发布。用户另明确要求：合格reference整理后，历史Door/Oven失败/被拒尝试的中间二进制产物清理，只留文字记录。先汇总参数/source hashes/结果/原因/关键指标；保护合格reference、已批准资产、当前范围证据、运行依赖及其他task数据。以清单和实际依赖检查确认后执行，保留删除receipt。

## Progress

- [ ] Oven用户批准及新Work记录；冻结两个scope proposal/source。
- [ ] Door/Oven实际范围与独立验收，失败/未运行分开。
- [ ] 六task集中reference/范围审核包。
- [ ] 历史失败产物文字归档、限定清理和引用检查。
- [ ] 治理/源码/资产保护核对；等待整批用户确认。

## 2026-10-16 最新用户审核分流

Drawer与Room Door reference/范围已批准；Sweep旧动作被拒绝，Fridge/Valve/Oven需要按用户时序及Oven1kg要求修订。后继QLM-DATA-034先交四条nominal视频，不复跑已批准两task。四项旧scope不证明新recipe/新质量通过；新reference批准后再重验。当前无100/WAM/cache/训练/AMD/发布。原结果/历史清理receipt保持。
