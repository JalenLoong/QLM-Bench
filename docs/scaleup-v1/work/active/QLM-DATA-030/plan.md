---
id: QLM-DATA-030
type: exec-plan
status: active
related_work: [QLM-DATA-029, QLM-DATA-028, QLM-SIM-022]
source_map: []
---

# Room Door：实际锁舌退出锁扣，而非固定20mm

用户明确批准：锁舌只需退出到门能被真实推开的程度；门打开后锁舌回弹不撤销成功。新success profile为`door-socket-clear-open15deg-v3`。按完整实际qpos计算bolt shaft八顶点在固定strike frame中的位置，全部越过socket mouth平面、实际退栓为正且保留原lever≤−20deg操作条件时，记录历史unlock event；随后door≥15deg/notfallen/三个50Hz tick。没有固定20mm行程要求，也不把初态socket内无碰撞当作解锁。

新三资产metadata独立版本化于workspace assets/mujoco/door-geometric-opening-approved-20261016-v1/，同A primary/B-C backups，XML/mesh与全部compiled physics/camera参数相同，物理资格复用SIM022。旧20mm profile、实际trial source/result/terminal不回写。新纯几何criterion及显式task-state adapter在workspace runs/audit/door-lowered-reference-20261016-v1/reference/door_socket_predicate_v3.py；未来入口须显式采用该adapter和新profile，公共task注册/生产尚未宣称接通。

本轮至多三次原RAMBO尝试A17/A18/A19均已实际结束，分别24.36/60/60秒；完整50Hz review snapshots与commands/terminal保留，视频25FPS真实同timestamp三视角。不把失败诊断包改成正式数据，也不增加常规500/100Hz存储要求。原执行冻结旧20mm判据，A18/A19的原timeout保留；新规则对真实完整状态独立离线复核：A17只开到5.25deg未通过，A18在24.86s通过，A19在24.40s通过。开门后bolt回退不撤销历史event。验证只是新条件评估通过，动作质量/正式reference/完整范围/用户审核仍待完成。

用户仅在前三次全部未过新条件时授权第四次；此条件不成立，未启动第四次。当前physics/scope0，后续尝试停止等待用户审核；未运行16scope、100合成、WAM/cache/训练/AMD/commit/push/发布。其他四reference、Oven停止及已验收400保持。

证据：workspace runs/audit/door-user-three-attempts-20261016-v1/new-criterion-assessment.json（实际完整状态复核、5项零step检查）；同目录a17/a18/a19/receipt.json（媒体）；workspace runs/audit/door-lowered-reference-20261016-v1/user-geometric-unlock-decision.json、approved-profiles-geometric-v3.json。全部旧source身份保持。

## Progress

- [x] 用户新判据与条件化第四次授权记录。
- [x] 纯几何历史event实现、初始锁住/部分退回/完全退出/回弹保持/reset清除等零step验证。
- [x] 三次实际轨迹离线复核与三资产编译参数完全等价。
- [x] 三条完整三视角视频与真实source/时钟验证。
- [x] 用户已批准A19动作质量与reference，并授权由QLM-DATA-033继续范围。

## Door A19获批；Oven50deg限位两次重试 — 2026-10-16

用户批准A19动作质量及reference方案；QLM-DATA-030接入几何退栓历史event和实时15deg/三tick/notfallen terminal，完整范围尚未验证。用户另授权Oven最大开度相对本体垂直面50deg及两次reference重试，由QLM-DATA-031执行；旧Oven停止要求仅对本有界两次解除，未授权额外scope/100。新版Oven保留45deg初态、原3deg关门判据与原RAMBO，使用真实joint限位，不clamp/teleport。审计workspace runs/audit/oven-limit50-reference-20261016-v1/；旧资产和失败结果不回写。


## Oven50deg两次已完成；第二次关门成功待动作审核 — 2026-10-16

QLM-DATA-031按用户要求完成两次，无追加第三次/无scope。第一次60s超时，第二次40.48s满足原3deg/三50Hz tick/notfallen；最大实际开度由50.679deg减至50.073deg，有限soft-limit超调据实保留。第二次有40个50Hz边界的Head接触记录，尚未量化关闭力矩，任务成功与动作质量分开，等待人工审核。审核workspace runs/audit/oven-limit50-reference-20261016-v1/review.html。

Door A19已获用户动作批准并选作reference；QLM-DATA-030显式runtime/新几何判据已接入，实际A19状态feed在24.40s触发成功，terminal后命令拒绝；未重跑Door physics，原A19结果和完整范围pending保持。原RAMBO/source/已验收400保持，无WAM/cache/训练/AMD/commit/push/发布。下方运行中记录仅为历史。


## Door/Oven reference已获批；开始冻结方案范围及六task集中确认 — 2026-10-16

用户批准Oven35deg中央前推，Door继续A19几何退栓/15deg。QLM-DATA-033执行Door16与Oven16范围；Oven初态提案25–35deg保留10deg宽度并遵守35deg限位，待集中确认。冻结动作/资产物理/成功条件，首失败停止该task新派发排空，最多3physics与原资源保护；无生产扩量。之后集中六task材料，按用户要求将历史失败/被拒Door/Oven二进制中间产物先文字归档后清理，保护合格reference、已批准资产及当前范围/依赖。审计workspace runs/audit/remaining-six-final-scope-20261016-v1/。


## 六task reference与范围已集中交审；历史失败产物已清理 — 2026-10-16

QLM-DATA-033完成Door16/16与Oven16/16全部实际角点验收，原RAMBO/已批准动作/物理/成功判据保持；所有episode在首次满足条件的完整50Hz边界结束，50Hz实际记录无非FL正受力接触。Door18.56–23.46s，Oven17.38–19.64s。Oven初始开度25–35deg为待此次集中确认的新范围提案，保留原10deg宽度并符合35deg限位；XY±2cm/yaw±5deg保持。

原四项复用：Sweep32/32、Fridge16/16、Valve16/16、Drawer16/16；六项集中审核workspace runs/audit/remaining-six-final-scope-20261016-v1/review.html。范围均为primary A，B/C资格不从A结果自动推定。Door A19与Oven35deg中央nominal已获批准，本轮整批reference/范围最终确认pending，新增formal0/原400保持。

按用户明确要求，历史失败/被拒/未采纳Door/Oven中间产物先文字归档后清理809文件、约3.13GiB逻辑大小；硬链接原因不冒充实际回收空间。原文字记录/source hashes保持；1278个受保护二进制逐文件hash复核，合格reference、当前范围、已批准资产及其他任务完整。删除receipt和文字汇总同审计目录。无后续physics/scope/100/WAM/cache/训练/AMD/commit/push/发布；停止等待用户整批确认。以下历史pending/运行中仅保留原时点。

