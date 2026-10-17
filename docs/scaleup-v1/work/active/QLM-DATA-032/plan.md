---
id: QLM-DATA-032
type: exec-plan
status: active
related_work: [QLM-DATA-031, QLM-DATA-028]
source_map: []
---

# Oven35deg限位与中央前推：单次尝试

用户明确拒绝此前两条Oven动作，授权最大开度35deg并从中间前推，只重试一条给视频。新A/B/C独立profile从50deg-v2派生，仅range改[-35deg,0]、初始开度35deg以处于新范围；质量1.8kg（A）、惯量、阻尼、摩擦、已调好局部limit solver、RAMBO/IK/PD/QP/history/native9/500-100-50Hz/camera保持。

中央指足端接触的门局部Y=0。FL操作需机身适度侧移，初始/工作bodyY=-.18m；接触点相对body前向.42m，较旧.26m增加头部净空；初始bodyX仍-.08m/default stance。接触初始半径.25m位于中央门板、低于handle半径.44m；高层世界高度目标.30m，沿真实门面法线向前推。第一段先到前侧预接触点，再依真实正关闭力矩接触进入关闭，原3deg/notfallen/三50Hz tick成功条件不变。

只一次真实原RAMBO试跑，成功或失败均保存完整50Hz诊断state/commands/terminal及三视角视频，不重跑成功physics、不补第二次、不scope/100/WAM/AMD/发布。新增50Hz非FL实际contact force/closing moment只作本次动作质量证据，不能用未知接触硬判失败。旧两条用户质量拒绝与原物理结果分开留存。

## Progress

- [x] 新profile、中央站位和零step初态检查。
- [x] 一次真实尝试和完整视频。
- [x] 工程检查并停止交用户审核。

## Oven35deg中央前推单次成功；等待动作审核 — 2026-10-16

QLM-DATA-032仅一次真实尝试完成，19.42s满足原3deg/三50Hz tick/notfallen；971actions/972boundaries，完整trace通过。初态35deg，实际最大35.0158deg，未硬截断qpos。首次FL_foot触门板中央worldY=-6.52mm；50Hz实际接触记录仅FL_foot，非FL记录0，不夸大为全500Hz证明。用户动作质量待审，未追加第二次/scope/100。审核workspace runs/audit/oven-limit35-center-reference-20261016-v1/review.html。

原50deg两条已被用户拒绝动作质量，历史task结果保留。当前A质量仍1.8kg，原RAMBO/physics时序/camera不变；中央recipe与35deg新资源均独立版本。当前physics/render结束后停止等审核，无训练/AMD/commit/push/发布。


## Door/Oven reference已获批；开始冻结方案范围及六task集中确认 — 2026-10-16

用户批准Oven35deg中央前推，Door继续A19几何退栓/15deg。QLM-DATA-033执行Door16与Oven16范围；Oven初态提案25–35deg保留10deg宽度并遵守35deg限位，待集中确认。冻结动作/资产物理/成功条件，首失败停止该task新派发排空，最多3physics与原资源保护；无生产扩量。之后集中六task材料，按用户要求将历史失败/被拒Door/Oven二进制中间产物先文字归档后清理，保护合格reference、已批准资产及当前范围/依赖。审计workspace runs/audit/remaining-six-final-scope-20261016-v1/。


用户已明确批准本nominal动作及reference方案，范围由QLM-DATA-033承接；reference与范围的整批最终确认尚待完成。

## 六task reference与范围已集中交审；历史失败产物已清理 — 2026-10-16

QLM-DATA-033完成Door16/16与Oven16/16全部实际角点验收，原RAMBO/已批准动作/物理/成功判据保持；所有episode在首次满足条件的完整50Hz边界结束，50Hz实际记录无非FL正受力接触。Door18.56–23.46s，Oven17.38–19.64s。Oven初始开度25–35deg为待此次集中确认的新范围提案，保留原10deg宽度并符合35deg限位；XY±2cm/yaw±5deg保持。

原四项复用：Sweep32/32、Fridge16/16、Valve16/16、Drawer16/16；六项集中审核workspace runs/audit/remaining-six-final-scope-20261016-v1/review.html。范围均为primary A，B/C资格不从A结果自动推定。Door A19与Oven35deg中央nominal已获批准，本轮整批reference/范围最终确认pending，新增formal0/原400保持。

按用户明确要求，历史失败/被拒/未采纳Door/Oven中间产物先文字归档后清理809文件、约3.13GiB逻辑大小；硬链接原因不冒充实际回收空间。原文字记录/source hashes保持；1278个受保护二进制逐文件hash复核，合格reference、当前范围、已批准资产及其他任务完整。删除receipt和文字汇总同审计目录。无后续physics/scope/100/WAM/cache/训练/AMD/commit/push/发布；停止等待用户整批确认。以下历史pending/运行中仅保留原时点。

