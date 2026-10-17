---
id: QLM-DATA-037
type: change-spec
status: active
related_work: [QLM-DATA-034, QLM-DATA-036]
source_map: []
---

# Fridge一次机身前进推门reference

用户确认Sweep审核通过，A09为reference；原32范围31通过/032真实超时保留，不推断为历史全32成功或生产授权。

Fridge不再用足端大幅世界坐标轨迹加速门并依靠惯性。2s开始抬高并前伸，足端碰门后保持固定机身坐标前伸姿态，机身缓慢前进维持真实接触，直到原3deg/notfallen/三50Hz tick成功或原40s/跌倒结束。仅调整高层native9 recipe；原controller/IK/PD/QP/history/checkpoint、资产物理、相机与时序不变。seed42、原初态与40s保持。

本次只一条真实physics，原runtime/review50和同timestamp离线三视角renderer复用。前置静态IK/几何检查0physics，不等于动态成功。一次budget/独占lock/独立attempt目录防止意外重复；启动时记录原资源保护，低内存不启动，已运行不强杀。视频仅诊断用25FPS展示完整实际50Hz snapshot，包括本次失败；不扩张普通失败的长期高频telemetry要求。

交付须核对完整command/terminal、forcezero、实际门角与原predicate及时停止、接触事件、固定body目标与机身前进证据。task success与动作质量分开；即使成功也待用户审视频，不能用少量接触计数证明全程连续接触。本次不scope/100/WAM/cache/训练/AMD/发布或额外试跑。

## Progress

- [x] 用户决定与Work-ID登记。
- [x] 原IK姿态静态检查及6项零步几何检查通过；一次recipe/source冻结。
- [x] 补充前A02和补充后唯一A03实际结果已保留；A03完整三视角交付。
- [x] 实际行为/保护/治理记录完成；停止等视频审核，动态可见性未达标。

## 用户运行中补充：更远停稳、主抬升前伸及ego可见性

原A02已在补充前启动，实际40s timeout、未跌倒，结果/完整review50保留；不把它写成按新要求执行。用户新要求作为同一任务的修订，far-stop-v2单独最多一条A03，新增receipt独立记录。先用原RAMBO零步IK及原ego相机projection/静态图检查前伸目标，再实际远处停稳→主抬高前伸→真实接触抵门→固定body目标并机身前进。固定相机不裁切/不改安装位；静态图不冒充真实trajectory。

采用5.4e-1m body前伸/0.15m侧向/-0.08m高度目标，关节缓冲限位内；远停点由原实际门面和前伸几何确定，约比A02抵门位置靠后。原早抬意图由远停稳后的主抬升/前伸体现，不把2s定时硬套为已到操作位置。此前3mm接近误差带导致接触门控过晚的事实保留；新版本只以真实接触对几何确认抵门，不因50Hz瞬时正常力未知/低值强制拒绝接触。原task success/controller/资产/时序不变。补充后只此一次，结果无论成败交视频后停止。

## Fridge A03视频交付；物理成功但ego/头部接触仍需修订 — 2026-10-16

Sweep A09已按用户确认登记合格reference，原31/32范围和032失败保留，不再运行Sweep。本轮QLM-DATA-037有补充前A02一次（40s timeout）及补充后far-stop-v2/A03唯一一次；两份真实source/结果保持，不隐藏或回写。

A03在38.14s达到原3deg/三tick/notfallen。5.38s远停稳后主抬升前伸，10.70s真实抵门；之后body足端目标固定[.4526,.15,-.08]，机身前进39.42cm。54cm仅目标上限，实际接触即冻结45.26cm，不能宣称达到54cm。最后FL正受力接触37.74s/门角−4.86deg，终止38.14s。ego足端中心仅约10.6%边界在画内、整球0%；11个50Hz边界存在Head_upper/lower接触（最大47.87N），不计合格reference/不准入SFT，task success保持真实。

完整1907commands/1908boundaries/原predicate及时终止/source及同timestamp三视角通过。审计workspace runs/audit/fridge-body-advance-reference-20261016-v1/review.html、report.md；原RAMBO/资产/相机/时序和400保持。全部physics/render结束，等待用户审视频，不追加尝试/scope/100/WAM/cache/训练/AMD/commit/push/发布。DATA037保持active等待质量审核，静态预览通过不代表动态可见性通过。

