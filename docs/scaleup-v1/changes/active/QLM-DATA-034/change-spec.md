---
id: QLM-DATA-034
type: change-spec
status: active
related_work: [QLM-DATA-028, QLM-DATA-033]
source_map: []
---

## Sweep A09单次成功，分阶段顺序通过；等待动作审核 — 2026-10-16

QLM-DATA-034仅实际一条A09，32.86s达到原完整footprint/notfallen/三tick，1643commands/1644boundaries并首次成功即终止。原进场/积分恢复，机身保持实际8.82s进入操作才启用；19.24s实际稳定足端侧触并小拨约6cm，21.74s确认原goal未满足后右侧移，25.10s再次稳定接触后最终拨动。接触及首次小拨前无计划goalward机身侧移。原RAMBO/成功判据/22.5cm资产布局与其余v8参数保持。

50Hz实际正受力接触仅FL_foot91次观测，FLcalf/机身0；足端横向顺序未反转，最小间隔+5.56cm，但肘部/支撑腿全程动作质量仍待用户视频审核，不替代该审核。workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a09-review.html；a09-completion.json、a09-sequence-audit.json及a09-report.md为当前证据。optional几何distance探测标记inconclusive，不用它作验收结论。

一次授权已用完，physics/render/监测结束，等待用户审核，无追加试跑/完整scope/100。旧30cm范围不证明22.5cm新reference范围通过；未自动计合格reference。旧A07/A08 payload/media与108源文件保持。Drawer/Door已批准、Fridge/Oven/Valve修订待审、原400保持；不WAM/cache/训练/AMD/commit/push/发布。下方A09启动及A08失败为历史。

## Sweep A08单次已结束：进场门控实现问题，未进入操作 — 2026-10-16

QLM-DATA-034按用户只一条要求执行A08，40s timeout/notfallen。实际仅settle/carry/approach_base，无FL/robot碰块、无稳定侧触/小拨动/右侧移，不能据此判断用户分阶段策略失败。本次expert把Y保持过早用于进场（cap2cm/s并清除recipe lateral integral），原1.5cm进场门控未收敛；终态Y误差约5.34cm。原RAMBO/内部history/physics/成功判据没有改动；不追加第二条，不计合格reference。

用户明确授权的距离30→22.5cm已通过独立profile实现：blockY.15→.075，goal位置/尺寸保持，A/B/C物理及camera参数不变。旧scope不能代表新布局。视频workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a08-review.html（完整40s/1001帧），a08-completion.json、a08-report.md和a08-actual-evidence.json为当前证据。4个零步mock阶段门控检查不等于真实流程验收。全部physics/render结束并停止等待用户反馈，无scope/100/WAM/cache/训练/AMD/发布；原400/其他reference保持。下方A08授权仅为启动前历史。

## Sweep A07一次重试完成，40s未成功；等待视频审核 — 2026-10-16

QLM-DATA-034按用户仅一次授权完成A07：40s timeout、未跌倒，未满足原完整footprint进区成功判据。身体终态goal方向移动32.6cm（A06为8.4cm）；全部50Hz采样足端横向顺序未反转，最小FL减FR bodyY间隔+12cm，但不能替代完整动作质量审核或task success。提前横移后lower阶段较久、后段足端抬高，方块未完整进区；不追加第二条，不计合格reference。

三视角workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a07-review.html，原速40s/1001帧，同timestamp实际snapshot且无physics重跑；a07-completion.json、a07-comparison.json及a07-report.md为本次权威。原RAMBO/成功判据/接触路径/资产/camera/seed42/40s保持；只改高层身体跟随与其朝向参考点。完整2000commands/2001boundaries/source及独立原predicate检查通过。仅这一条，physics/render结束，等待用户视频反馈；未scope/100/WAM/cache/训练/AMD/发布。Fridge/Oven/Valve待审、Drawer/Door已批准、原400保持。下方A07授权/停止点为历史。

# 四项reference按用户视觉审核修订

用户批准Pull Open Drawer与Open Room Door的reference/范围，原材料保持不复跑。Sweep旧reference动作不合格：需要从原7秒附近较远站位伸腿、身体随方块/goal方向协同移动避免FL与右前腿FR交叉；goal仅边框。用户原话RL指右前腿，工程按FR记录。Fridge约2秒开始抬高前伸；Valve约6秒停止接近并抬高前伸；Oven门质量改1kg、约4秒停止接近并抬高前伸、增加操作腿前伸。Oven35deg限位/原task predicates、RAMBO/IK/PD/QP/history/native9/500-100-50Hz/camera保持。

先交四条修订nominal动作视频，原四项scope属于旧recipe/旧质量，只作历史，不冒充新版本验证。新参考获批后再冻结并重验对应范围；当前不100/WAM/cache/AMD/发布。完整50Hz review capture用于本次视频（包括失败），无常规500/100Hz失败永久存储扩张。并发最多3physics+3render与原内存保护。

## Progress

- [x] 用户批准/拒绝及四项修订记录，两个新asset profile编译与差异核验通过。
- [ ] 四条真实修订reference及动作/时序/接触实际证据。
- [x] 集中视频材料及Sweep五条失败视频交付，明确新scope尚未重验。
- [x] 治理/保护与停止新增尝试等待用户视频反馈。

## 实际执行记录

Fridge a01、Oven a01、Valve a01分别16.76/15.62/12.72s达到原task success，完整50Hz/forcezero/同timestamp媒体/source检查通过，动作质量仍待用户审核。Sweep按实际几何证据进行有界高层调试；a01/a02/a04实际任务失败、a03为heading实现缺陷且原结果保留，不隐藏或放宽成功条件。具体当前结果以审计目录actual-evidence.json及最后交付catalog为准。新scope尚未重验。

## 当前交付与停止点

五条Sweep失败视频按用户要求完整交付；在途a06结束后无新派发。a06为33.52s task success但仍有足端横向顺序反转约61mm/末段交叉风险及FLcalf接触，未计合格reference。Fridge/Oven/Valve三项任务成功且完整视频已完成，质量待用户审核。actual-evidence.json/selected-reference-catalog.json/report.md为当前证据，sweep-failure-review.html为最新用户请求。全部physics/render0，等待用户反馈，未重验scope/未100。

## Sweep A06交叉被拒；仅授权一次A07身体跟随修订 — 2026-10-16

用户要求身体在拨动中更早、更充分向goal移动，保持原RAMBO与success，只再试一条三视角。QLM-DATA-034仅新增sweep-a07：lower阶段提前1.5s渐建6cm身体目标领先、实际block进度1.2倍跟随、目标位移上限32cm；高层横移cap3.5→10cm/s，原加速度0.12m/s²保持，并平移身体朝向参考点，原heading反馈算法/角速度限制保持。原足端接触路径、远初停点、资产/physics/camera/seed42/40s成功判据及controller内部保持。

独立v7/source/recipe与一次预算receipt位于workspace runs/audit/four-reference-refinement-20261016-v1/。只此一条；成功/失败均交真实snapshot三视角并停止等审核，不自动追加、scope或100。A06仍被拒动作质量，不能覆盖旧结果。Fridge/Oven/Valve待动作审核，Drawer/Door批准/原400保持，无WAM/cache/训练/AMD/发布。下方停止等反馈是旧时点。


## Sweep A08单次授权：22.5cm距离，先接触小拨再侧移 — 2026-10-16

用户确认A07身体停止位置，要求禁止足端稳定接触前侧移；仅再试一条A08并交三视角。保持goal原位，block-goal中心距30→22.5cm（blockY.15→.075），新独立profile sweep-short225-staged-approved-20261016-v1各A/B/C只改初始位置；原质量/碰撞/摩擦/camera/成功判据保持。此距离变化由用户明确授权，不沿用旧scope冒充新范围。

高层流程为原远初停点/伸腿→机身位置保持和真实FL_foot侧面稳定接触→5cm足端小拨动；若原goal未满足且block实际小移≥1cm，才允许身体向右（goalward世界-Y）侧移12cm，足端world目标保持；机身再停稳/重新实际侧触后完成拨动。原RAMBO/checkpoint/IK/PD/QP/history/native9/500-100-50Hz/forcezero/camera与原40s/footprint/notfallen/三tick保持。接触门控只是expert动作阶段，不替代task success；足端横向护栏只是质量保护，不自动判task失败。

QLM-DATA-034承接，独立v8/source/recipe/asset与一次授权receipt在workspace runs/audit/four-reference-refinement-20261016-v1/；仅A08，不自动第二条/scope/100/WAM/cache/训练/AMD/发布。原A07失败及其他reference/原400保持，完成视频后停止等审核。


## Sweep A09单次授权：恢复进场，只在interaction后保持机身 — 2026-10-16

用户明确要求修复A08，恢复原approach/stabilize进场控制，只在进入操作阶段后启用机身保持；沿用22.5cm和稳定侧触→5cm小拨→必要时右侧移→再拨动，仅再一条并给三视角。QLM-DATA-034仅新增A09。v9只把机身保持override门控改为interaction_start非None，保留原进场速度/recipe lateral integral/1.5cm与停稳门控；原RAMBO及success、seed42/40s、资产/相机/时序和分阶段参数不变。

独立source/recipe/一次授权receipt在workspace runs/audit/four-reference-refinement-20261016-v1/。成功/失败均完整交视频后停止，不自动第二条/scope/100/WAM/cache/训练/AMD/发布；A08原timeout及全部历史/原400保持。下方A08停止为旧时点。


## Sweep A09已获批准；QLM-DATA-035范围验证，三reference集中待审 — 2026-10-16

用户明确批准A09为Sweep reference，独立receipt在workspace runs/audit/four-reference-refinement-20261016-v1/a09-user-reference-approval.json。沿用22.5cm和当前分阶段动作，原RAMBO/成功判据/recipe/初态/seed42/40s冻结。后继QLM-DATA-035验证完整原5维32角点；距离中心从30平移至22.5cm并保持±2cm宽度（20.5–24.5cm），其余blockXY±2cm/yaw±5°/goal方向±4°与两背景各16保持。旧30cm scope不作新版本通过证据，首失败停派并排空，最多3physics和原资源保护。

Fridge/Oven/Valve修订视频已集中于workspace runs/audit/four-reference-refinement-20261016-v1/fridge-oven-valve-revised-review.html，动作质量仍待用户审核；直接复用媒体，不重跑physics/WAM/cache。原034保留其余三项审核，035只Sweep scope与集成交付。原Drawer/Door/400保持，暂不100/新formal/训练/AMD/commit/push/发布。下方A09动作待批准为历史。


## Scope035未通过并已排空；A09 nominal批准保持，三reference待审 — 2026-10-16

QLM-DATA-035保留原5D32角点（blockXY±2cm/yaw±5°/goal方向±4°、22.5cm中心距离±2cm，两背景各16）不缩域。首轮4/32仅1 task success但无获批序列资格，28未执行；补geometry-retarget-v1后3/32虽3 task success，均未执行first stroke/侧移，序列合格0、29未执行。共7次两个版本的scope物理运行，不合并冒充32点通过；首失败停止新派发并排空，当前0physics。

已量化共同原因：操作段机身Y误差最高8.6–10.6cm，稳定足端侧触与机身停稳从未同时成立；准备阶段却追随block继续推进，导致任务成功但批准动作顺序未执行。需要加强操作期机身保持并使接触准备有界，可能影响nominal实际动作，因此本轮不继续修改获批A09，不放宽门控/成功条件或缩范围。几何retarget在零扰动下保持A09且0physics，旧task结果/trace不回写；旧“可选阶段出现才校验”不足已由独立序列复核明确纠正。

当前报告workspace runs/audit/sweep-a09-scope-20261016-v1/review.html及final-report.json。A09 nominal reference用户批准保持，完整范围验收未完成，DATA035保持active；DATA034保留其余三项动作审核。Fridge/Oven/Valve修订三视角集中页workspace runs/audit/four-reference-refinement-20261016-v1/fridge-oven-valve-revised-review.html，均复用原媒体、hash和链接通过，用户动作批准仍pending。原400/Drawer/Door/原RAMBO及source保持。暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布。


## Oven/Valve reference已批准；Sweep取消顺序门槛，DATA036续验 — 2026-10-16

用户明确批准Close Oven Door与Turn Valve修订reference，独立receipt见workspace runs/audit/four-reference-refinement-20261016-v1/{oven,valve}-user-reference-approval.json。Fridge仍待审核。Sweep参考A09，取消小拨/侧移必须按序完成的门槛，达到原task success即可；原footprint/notfallen/三tick、RAMBO、camera、22.5cm及原32范围保持。阶段/姿态诊断不独立拒收task成功，工程完整性仍须验证。

QLM-DATA-036负责新口径复核旧3成功（保留实际source、原outcome不回写且不重跑成功physics）及其余范围续跑；小拨未达量/侧移未停稳/再次接触硬等待改为可选继续分支。DATA035原“顺序不合格”是旧口径历史，不再作为当前阻塞。审计workspace runs/audit/sweep-task-success-scope-20261016-v1/。暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布；原400/Drawer/Door批准保持。

