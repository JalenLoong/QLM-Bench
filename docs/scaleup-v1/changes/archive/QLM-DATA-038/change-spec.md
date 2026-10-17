---
id: QLM-DATA-038
type: change-spec
status: completed
related_work: [QLM-DATA-037]
source_map: []
---

# Fridge50deg与实际门面跟随

用户将初始开度55→50deg，并要求抵门后持续随门位置前伸。仅初始化hinge q改为−50deg，原model XML/物理参数/相机/成功条件保持；原55deg模型profile保留，实际runtime reset override与attempt明确记录，不在运行中改变qpos。先远停稳并抬高前伸；首次真实接触后按实际门面更新足端目标，限制前伸速度，机身以更长的工作前伸距离配合推进，避免再次固定在首次接触长度。原RAMBO/IK/PD/QP/history/native9/forcezero与500/100/50Hz保持。

本轮沿用单条视频审核，仅A04一次真实physics；seed42、40s及原3deg/notfallen/三tick保持。前置几何检查0physics；成功失败均保存本次实际review50并交三视角。核对真实初角、抵门后目标实际变化、接触/头部接触、ego可见性、timely terminal/source，task success不替代动作质量。原其他references/400保持，不scope/100/WAM/cache/训练/AMD/commit/push/发布。

- [x] 决定、Work-ID及独立版本建立。
- [x] 一次执行、实际证据与视频交付。
- [x] 治理保护完成，停止等审核。

## Fridge A04交付：50deg与实际门面持续跟随 — 2026-10-16

QLM-DATA-038本轮仅一条A04，27.96s按原3deg/三tick/notfallen成功；55→50deg只在reset前改变hinge初态，原model/资产物理/camera/原RAMBO保持。6.04s主前伸，11.40s抵门，之后足端body参考从45.48持续延伸到54cm（+8.52cm），机身推进29.48cm，不再冻结首次接触长度。原伸展上限到达后由机身配合。

50Hz实际FL足端正受力31次、FLcalf3次、非FL0；最后FL接触27.94s距终止0.02s。ego足端中心入画约91.1%、整球73.8%，实际中段/末段图已看，不宣称全程无遮挡或500Hz连续接触。1398commands/1399boundaries/初态差异/及时终止/source和700帧三视角验证通过，任务成功不替代动作质量审核。

当前审核workspace runs/audit/fridge-door-follow-20261016-v1/review.html；DATA038 active等待用户视频审核，未标合格reference。所有physics/render结束，无额外尝试/scope/100/WAM/cache/训练/AMD/commit/push/发布。旧A02/A03失败或质量不足记录、原400/其他task批准保持。


用户已批准A04为合格reference。范围验证由后继QLM-DATA-039承接，未授权100。
