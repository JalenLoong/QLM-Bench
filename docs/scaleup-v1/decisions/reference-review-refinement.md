---
id: QLM-REFERENCE-REVIEW-REFINEMENT
type: decision
status: accepted
related_work: [QLM-DATA-034, QLM-DATA-033, QLM-DATA-028]
source_map: []
---

## 当前交接：三项范围已批准，正式400/1000，剩余600待生产 — 2026-10-16

用户明确批准DATA039 Fridge/Oven/Valve三项修订范围，实际48/48工程通过；独立receipt为workspace runs/audit/revised-three-scope-20261016-v1/user-scope-approval.json，DATA039配对归档。六task当前资产/reference人工审核均已完成，Drawer/Door既有批准、Sweep A09批准保持；Sweep历史31/32及032失败不回写。

当前Push/Press/Lift/Kick各100，共400正式已验收并完成private HF400发布；剩余六task正式0/600，scope/reference不自动计入100。生产公共接入尚未完成：六registration仍planned、公共rendition仍限制旧四task、Door须用几何退栓v3适配，不能直接复用含旧20mm逻辑的generic helper。新会话需阅读交接后先与用户对齐，等下一条开工指令；本轮不生产。

当前权威交接：docs/scaleup-v1/handoffs/remaining-six-production-20261016.md（QLM MuJoCo repo）；完整绑定和可复制prompt在workspace runs/audit/remaining-six-handoff-20261016-v1/。未来沿用直接每task100，无10pilot人工gate；每task一次WAM兼容与全量工程检查，最终每task随机十条人工验收延后到六task全部完成。3+3/1GiB/7.6GiB/0.5GiB/4GiB政策保持。旧pending/旧角度/旧20mm/旧10pilot段落均是历史，不恢复已完成审批。

# 六项reference审核后的四项修订

用户已批准Pull Open Drawer和Open Room Door的reference与完整范围；不重跑、不改变资产/成功判据或批准证据。Sweep旧动作被拒绝，Fridge/Valve/Oven按用户要求修订。历史工程成功不等于最新动作质量获批。

- Sweep从旧reference约7s的较远站位（实际base X约0.224m）停止后开始伸腿。新目标初始X0.23m，抬腿后身体随前伸及方块实际位移协同，横向跟随goal方向以避免FL与右前腿FR交叉；用户原文RL在本次指右前腿。goal只保留边框，不改变goal范围/full-footprint成功条件。新asset只改填充alpha，其他物理保持。
- Fridge约2s开始抬高前伸FL；原门体物理和3deg/三tick/notfallen保持。
- Oven门体总质量改1kg，惯性按相同几何和质量比例重算；35deg物理限位、原damping/friction/geometry和3deg/三tick/notfallen保持。约4s停止接近并抬腿前伸，减小预接触standoff使前伸增加。
- Valve约6s停止接近并开始抬腿前伸；原接触与角度成功条件保持，速度按原限加速度平滑停止。

原RAMBO/checkpoint/IK/PD/QP/history/native9/forcezero/500-100-50Hz和camera contract保持。新asset profile独立版本化：workspace assets/mujoco/sweep-outline-approved-20261016-v1/与oven-1kg35-center-approved-20261016-v1/，各A primary/B-C backups，无backup配额。source_asset/front_layout中的旧描述是parent历史；本Work recipe及用户决定覆盖旧的fixed-body行为，不回写历史资源。

QLM-DATA-034先完成四条新nominal及三视角视频交审；四项旧scope仅适用于旧recipe/旧质量，不证明新版本完整范围。新reference获批后才冻结对应recipe再重验范围。本轮不自动生产100，不执行WAM/cache/训练/AMD/发布。Drawer/Door批准与原400保持；最终每task随机十条人工验收仍延后至所有task合成完成后统一。

证据workspace runs/audit/four-reference-refinement-20261016-v1/：user-review-decision.json、asset-profiles.json、每次独立source inventory/result/review50、actual-evidence.json及媒体receipt。完整50Hz diagnostic capture用于本次reference质量审核，不增加普遍成功trajectory的500/100Hz永久存储要求。失败、实现缺陷和任务成功分开记录，不从结果选seed或缩范围。

## Sweep A06交叉被拒；仅授权一次A07身体跟随修订 — 2026-10-16

用户要求身体在拨动中更早、更充分向goal移动，保持原RAMBO与success，只再试一条三视角。QLM-DATA-034仅新增sweep-a07：lower阶段提前1.5s渐建6cm身体目标领先、实际block进度1.2倍跟随、目标位移上限32cm；高层横移cap3.5→10cm/s，原加速度0.12m/s²保持，并平移身体朝向参考点，原heading反馈算法/角速度限制保持。原足端接触路径、远初停点、资产/physics/camera/seed42/40s成功判据及controller内部保持。

独立v7/source/recipe与一次预算receipt位于workspace runs/audit/four-reference-refinement-20261016-v1/。只此一条；成功/失败均交真实snapshot三视角并停止等审核，不自动追加、scope或100。A06仍被拒动作质量，不能覆盖旧结果。Fridge/Oven/Valve待动作审核，Drawer/Door批准/原400保持，无WAM/cache/训练/AMD/发布。下方停止等反馈是旧时点。


## A07一次重试结果

本次仅Sweep A07，40s timeout/notfallen，原成功判据未满足；身体跟随显著增加，50Hz足端横向顺序未反转，但不作质量通过或合格reference。完整三视角见workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a07-review.html；a07-completion.json为当前结果，physics/render均已结束，停止等待用户视频审核，无第二条/scope/100/WAM/cache/训练/AMD。

## Sweep A08单次授权：22.5cm距离，先接触小拨再侧移 — 2026-10-16

用户确认A07身体停止位置，要求禁止足端稳定接触前侧移；仅再试一条A08并交三视角。保持goal原位，block-goal中心距30→22.5cm（blockY.15→.075），新独立profile sweep-short225-staged-approved-20261016-v1各A/B/C只改初始位置；原质量/碰撞/摩擦/camera/成功判据保持。此距离变化由用户明确授权，不沿用旧scope冒充新范围。

高层流程为原远初停点/伸腿→机身位置保持和真实FL_foot侧面稳定接触→5cm足端小拨动；若原goal未满足且block实际小移≥1cm，才允许身体向右（goalward世界-Y）侧移12cm，足端world目标保持；机身再停稳/重新实际侧触后完成拨动。原RAMBO/checkpoint/IK/PD/QP/history/native9/500-100-50Hz/forcezero/camera与原40s/footprint/notfallen/三tick保持。接触门控只是expert动作阶段，不替代task success；足端横向护栏只是质量保护，不自动判task失败。

QLM-DATA-034承接，独立v8/source/recipe/asset与一次授权receipt在workspace runs/audit/four-reference-refinement-20261016-v1/；仅A08，不自动第二条/scope/100/WAM/cache/训练/AMD/发布。原A07失败及其他reference/原400保持，完成视频后停止等审核。


## Sweep A08单次已结束：进场门控实现问题，未进入操作 — 2026-10-16

QLM-DATA-034按用户只一条要求执行A08，40s timeout/notfallen。实际仅settle/carry/approach_base，无FL/robot碰块、无稳定侧触/小拨动/右侧移，不能据此判断用户分阶段策略失败。本次expert把Y保持过早用于进场（cap2cm/s并清除recipe lateral integral），原1.5cm进场门控未收敛；终态Y误差约5.34cm。原RAMBO/内部history/physics/成功判据没有改动；不追加第二条，不计合格reference。

用户明确授权的距离30→22.5cm已通过独立profile实现：blockY.15→.075，goal位置/尺寸保持，A/B/C物理及camera参数不变。旧scope不能代表新布局。视频workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a08-review.html（完整40s/1001帧），a08-completion.json、a08-report.md和a08-actual-evidence.json为当前证据。4个零步mock阶段门控检查不等于真实流程验收。全部physics/render结束并停止等待用户反馈，无scope/100/WAM/cache/训练/AMD/发布；原400/其他reference保持。下方A08授权仅为启动前历史。


## Sweep A09单次授权：恢复进场，只在interaction后保持机身 — 2026-10-16

用户明确要求修复A08，恢复原approach/stabilize进场控制，只在进入操作阶段后启用机身保持；沿用22.5cm和稳定侧触→5cm小拨→必要时右侧移→再拨动，仅再一条并给三视角。QLM-DATA-034仅新增A09。v9只把机身保持override门控改为interaction_start非None，保留原进场速度/recipe lateral integral/1.5cm与停稳门控；原RAMBO及success、seed42/40s、资产/相机/时序和分阶段参数不变。

独立source/recipe/一次授权receipt在workspace runs/audit/four-reference-refinement-20261016-v1/。成功/失败均完整交视频后停止，不自动第二条/scope/100/WAM/cache/训练/AMD/发布；A08原timeout及全部历史/原400保持。下方A08停止为旧时点。


## Sweep A09单次成功，分阶段顺序通过；等待动作审核 — 2026-10-16

QLM-DATA-034仅实际一条A09，32.86s达到原完整footprint/notfallen/三tick，1643commands/1644boundaries并首次成功即终止。原进场/积分恢复，机身保持实际8.82s进入操作才启用；19.24s实际稳定足端侧触并小拨约6cm，21.74s确认原goal未满足后右侧移，25.10s再次稳定接触后最终拨动。接触及首次小拨前无计划goalward机身侧移。原RAMBO/成功判据/22.5cm资产布局与其余v8参数保持。

50Hz实际正受力接触仅FL_foot91次观测，FLcalf/机身0；足端横向顺序未反转，最小间隔+5.56cm，但肘部/支撑腿全程动作质量仍待用户视频审核，不替代该审核。workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a09-review.html；a09-completion.json、a09-sequence-audit.json及a09-report.md为当前证据。optional几何distance探测标记inconclusive，不用它作验收结论。

一次授权已用完，physics/render/监测结束，等待用户审核，无追加试跑/完整scope/100。旧30cm范围不证明22.5cm新reference范围通过；未自动计合格reference。旧A07/A08 payload/media与108源文件保持。Drawer/Door已批准、Fridge/Oven/Valve修订待审、原400保持；不WAM/cache/训练/AMD/commit/push/发布。下方A09启动及A08失败为历史。


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

