---
id: QLM-DATA-030
type: change-spec
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
- [ ] 用户动作质量与下一步决定；不自动扩完整scope或继续试跑。
