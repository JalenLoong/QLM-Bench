---
id: QLM-DATA-029
type: change-spec
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
- [ ] 新15deg profile、resource closure与compiled物理/相机完全等价核对。
- [ ] 原RAMBO高质量nominal真实20mm退栓后15deg/三tick成功，task success与quality分开。
- [ ] 同一冻结recipe原完整16scope及独立验收，未执行不得宣称通过。
- [ ] 双正式RGB/Observer与集中审核、治理/source检查，用户reference/范围审核pending。
