---
id: QLM-DATA-032
type: change-spec
status: active
related_work: [QLM-DATA-031, QLM-DATA-028]
source_map: []
---

# Oven35deg限位与中央前推：单次尝试

用户明确拒绝此前两条Oven动作，授权最大开度35deg并从中间前推，只重试一条给视频。新A/B/C独立profile从50deg-v2派生，仅range改[-35deg,0]、初始开度35deg以处于新范围；质量1.8kg（A）、惯量、阻尼、摩擦、已调好局部limit solver、RAMBO/IK/PD/QP/history/native9/500-100-50Hz/camera保持。

中央指足端接触的门局部Y=0。FL操作需机身适度侧移，初始/工作bodyY=-.18m；接触点相对body前向.42m，较旧.26m增加头部净空；初始bodyX仍-.08m/default stance。接触初始半径.25m位于中央门板、低于handle半径.44m；高层世界高度目标.30m，沿真实门面法线向前推。第一段先到前侧预接触点，再依真实正关闭力矩接触进入关闭，原3deg/notfallen/三50Hz tick成功条件不变。

只一次真实原RAMBO试跑，成功或失败均保存完整50Hz诊断state/commands/terminal及三视角视频，不重跑成功physics、不补第二次、不scope/100/WAM/AMD/发布。新增50Hz非FL实际contact force/closing moment只作本次动作质量证据，不能用未知接触硬判失败。旧两条用户质量拒绝与原物理结果分开留存。

## Progress

- [ ] 新profile、中央站位和零step初态检查。
- [ ] 一次真实尝试和完整视频。
- [ ] 工程检查并停止交用户审核。
