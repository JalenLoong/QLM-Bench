---
id: QLM-DATA-029
type: exec-plan
status: active
related_work: [QLM-SIM-022, QLM-DATA-028]
source_map: []
---

# Door真实退栓后推开小角度：独立15deg success profile

用户明确允许降低开门成功角。采用15deg合理默认值；用户原话没有指定数字，具体实施值已在会话说明。必须仍真实bolt>=20mm且lever<=-20deg历史事件、notfallen及三个50Hz tick；不从门角猜unlock，不修改原RAMBO/IK/PD/QP/history/native9/forcezero/500-100-50Hz/camera或资产物理。

新success profile独立派生，XML/mesh与28cm approved pack完全相同。model parameter identity相同证明既有SIM022 Native/CUDA机械资格适用，不重跑已成功的资产物理检查。新closure/target15与旧60deg明确分开；原14条旧attempt/source/outcomes不回写，不追认为成功。当前未有成功nominal或scope，不把减角当作已经完成20mm退栓。

参考继续实际高层轨迹/接触/站位的有据开发，统一seed42/原reset/h60；旧更大开门角的失败只作历史。得到合格新nominal后冻结expert/recipe及success-profile，经独立trace/quality验收，原完整XY±2cm/yaw±5deg×两背景16案例才派发，最多3physics，首失败/资源保护停新派发排空。成功physics不重跑，媒体用同timestamp完整snapshot镜像。Scope基础设施需完成独立提出的4项身份/exit/异常排空/source库存修复后才准入。

新reference/完整scope完成后与其余材料集中交用户审核；Oven已停止/范围失败保持，原四项就绪reference及已验收400不变，无10pilot人工gate，不100/WAM/cache/训练/AMD/commit/push/发布。最终随机十条仍延后至所有task合成结束。WAM v2DOC025/v3DOC024只治理，parentDATA028保留其余五task及整批审核路由。W&B not_run/local-only。

## Progress

- [x] 用户授权与15deg默认值/新Work ID/ADR。
- [x] 新15deg profile、resource closure与compiled物理/相机完全等价核对。
- [ ] 原RAMBO高质量nominal真实20mm退栓后15deg/三tick成功，task success与quality分开。
- [ ] 同一冻结recipe原完整16scope及独立验收，未执行不得宣称通过。
- [ ] 双正式RGB/Observer与集中审核、治理/source检查，用户reference/范围审核pending。

## 实际发现与下一步

SmallV15使用新15deg profile真实执行26.04s，因可靠足端侧触拒收；接触日志最大bolt18.972551mm，原strict unlock history始终false，未因门缝变大或门槛降低而追认成功。此次仅把高层pressure cap24改为28mm，不改变controller/资产物理；source与原始轻量失败记录保持在workspace runs/audit/door-lowered-reference-20261016-v1/reference/nominal-small-a15/及source-snapshots/。

独立零step几何与负载分析记录于同审计目录independent/bolt-clearance-small-v2.json/md：closed锁舌实际插入socket19mm，strict20mm包含1mm退出余量；转动/软接触可使门缝先出现，不能替代20mm历史判据。距lever转轴65/85/90mm接触处的20mm退栓准静态向下力估算分别18.31–19.71/14.00–15.07/13.23–14.23N，并非实际Go2力测量。下一高层候选优先检查85mm接触点与BaseY协调，先核对原IK/全腿及面板净空，再实际执行；不是新资产、范围收缩或已通过的动作。

Scope身份/exit/异常排空/source库存修复已迁移至small-v3并进行独立合成故障检查，尚待source冻结后的最终复核；实际scope仍0。未有独立合格nominal和显式工程准入前不派发。W&B not_run/local-only，formal0；原400与其他reference身份保持。

## Room Door已按用户要求暂停 — 2026-10-16

用户明确暂停Open Room Door后续尝试，只要求查看最近失败的三视角视频。当前Door physics/scope进程0，最后实际失败为QLM-DATA-029 SmallA16（22.74s侧触拒收/notfallen），没有A17，scope实际0。不得继续候选开发、physics或scope，等待用户下一步指令；其他reference/原400保持。receipt见workspace runs/audit/door-lowered-reference-20261016-v1/user-pause-decision.json。可仅用已保存127个真实qpos时点制作明确标注的5Hz为主稀疏诊断回放，不插值、不补跑physics，不冒充完整50Hz失败trace。下方“继续开发”只描述原历史状态。


## Room Door有界恢复：最多三次并保留视频 — 2026-10-16

用户纠正主要问题为实际前伸不足及下压/侧触门槛过严，授权高层路径和接触门控修复后至多三次真实尝试，所有尝试均交三视角视频。QLM-DATA-029沿用；只解除本有界轮的暂停，不授权完整scope或更多尝试。原20mm退栓/15deg/三tick/notfallen、RAMBO/资产/相机保持。失败仅此轮按用户要求保留完整50Hz诊断snapshot用于媒体，不改为正式demonstration或普遍高频存储要求。实际预算receipt为workspace runs/audit/door-lowered-reference-20261016-v1/user-three-attempt-decision.json，启动入口单写者强制最多3次。下方旧暂停保留历史。


## Door三次尝试完成；采用实际锁扣退出判据 — 2026-10-16

用户已取消固定20mm退栓门槛，采用实际锁舌实体退出锁扣口的历史event；开门后的回弹不撤销解锁，15deg/notfallen/三50Hz tick和原RAMBO/资产/physics/camera保持。QLM-DATA-030及decisions/door-geometric-unlock.md为新权威，旧20mm判据只保留历史。三次A17/A18/A19已全部结束并保留完整50Hz诊断状态、三视角视频。按新规则离线复核A18在24.86s、A19在24.40s通过，A17未达到15deg；原执行结果/terminal不回写，不冒充按新规则实时终止的正式数据。

前三次全部失败才追加第四次的条件不成立，因此无第四次、无scope/100扩量，当前0physics/scope，停止等待用户审核。审核workspace runs/audit/door-user-three-attempts-20261016-v1/review.html；动作质量及reference完整范围仍待审。原400/其他references/Oven停止保持，无WAM/cache/训练/AMD/commit/push/发布。下方旧暂停/20mm/进行中段落为历史。

