---
id: QLM-DOOR-SMALL-OPENING-SUCCESS
type: decision
status: accepted
related_work: [QLM-DATA-029, QLM-DATA-028, QLM-SIM-022]
source_map: []
---

# Room Door：真实退栓后推开较小角度

2026-10-16用户明确允许降低成功门槛的开门角，只要真实退栓成功并把门推开较小角度。采用15deg作为合理默认值；用户原话没有指定数字，实施值已在会话说明。原60deg只保留历史版本，不对旧失败追认成功。

新reference success profile为`door-physical-unlock20mm-open15deg-v2`：实际bolt>=20mm且lever<=-20deg的历史事件成立后，door>=15deg、notfallen，保持三个50Hz tick。严格退栓、原RAMBO/IK/PD/QP/history/native9/forcezero/500-100-50Hz、camera与资产物理保持。只有开门角60→15，不能由门角猜测unlock或降低20mm门槛。

QLM-DATA-029承接新success profile、原controller reference与完整fixture XY±2cm/yaw±5deg×两背景16项；QLM-DATA-028保留其他task与整批审核路由。三个新runtime profile与此前28cm pack的XML/mesh和完整compiled物理/相机fingerprint相同，SIM022的实际Native/CUDA资格沿用；新metadata/closure独立，不重跑资产物理资格，也不混用旧60deg实验结果。

用户授权receipt与等价性证据在workspace runs/audit/door-lowered-reference-20261016-v1/user-small-opening-decision.json、small-opening-profile-equivalence.json；新profiles在workspace assets/mujoco/door-small-opening-approved-20261016-v1/。实际高质量nominal、scope与用户审批仍未完成；降角不等于已完成真实20mm退栓。正式任务注册/数据/evaluation在后续准入统一使用该版本，不能把新15deg结果与旧60deg结果混作同一指标。

原四项就绪reference、Oven范围失败/已停止及已验收400保持。本轮不100/WAM/cache/训练/AMD/commit/push/发布；reference/范围完成后集中交用户审核。
