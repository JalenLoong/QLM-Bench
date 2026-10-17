---
id: QLM-SIM-022
type: exec-plan
status: active
related_work: [QLM-SIM-021, QLM-SIM-020, QLM-DATA-028]
source_map: []
---

## Door目标更新：真实20mm退栓后推开15deg — 2026-10-16

用户明确允许把开门角成功门槛适当减小；实施采用15deg合理默认（用户未指定数字，已在会话说明）。严格bolt>=20mm且lever<=-20deg历史event、notfallen/三50Hz tick、原RAMBO/IK/PD/QP/history/native9/forcezero/500-100-50Hz/camera和资产物理保持。QLM-DATA-029承接新success profile/reference/完整原16scope，parentDATA028保留整批审核，SIM022物理证据继续复用。新成功定义为door-physical-unlock20mm-open15deg-v2，不把旧60deg失败追认为成功。

新runtime在workspace assets/mujoco/door-small-opening-approved-20261016-v1/A|B|C，仍同一A primary/B-C backups三个资产身份；仅task success metadata/closure改变，XML/mesh和完整compiled物理/相机fingerprint三资产逐一exact。证据workspace runs/audit/door-lowered-reference-20261016-v1/user-small-opening-decision.json、approved-profiles-small-v2.json、small-opening-profile-equivalence.json与reference-admission-small-v2.json。原28cm/60deg profiles、14条旧attempt/source/outcome完整保留，当前旧轮均已排空，不重跑成功资产qualification。

当前还未有合格新15deg nominal或16scope；降低角度不解决尚待验证的strict20mm退栓。既有四项完整reference和Oven范围失败/停止保持，原400保持。继续最多3physics+3render及原1GiB/7.6GiB/0.5GiB/4GiB保护；scope须先实际nominal独立验收并修复身份/exit/异常排空/source库存问题，完成集中交审，无10pilot人工gate、不100/WAM/cache/训练/AMD/commit/push/发布。最终随机十条延后至全部task完成。下方60deg与asset pending叙述只保留历史版本。

# Approved28cm Room Door: real physics and retained-RAMBO reference admission

用户已批准28cm A primary/B-C backups。仅新runtime approval metadata与closure派生，XML/mesh/物理参数逐字节保留；proposal和旧35cm资源/旧成功失败trace均不可改写。此Work负责独立Native/CUDA真实物理资格，QLM-DATA-028负责新版本原RAMBO reference/完整16范围和集中审核。WAM v2DOC025/v3DOC024只治理。

原RAMBO source/checkpoint/IK/PD/QP/history/native9/force-zero/500-100-50Hz/正式camera及任务成功条件保持。只允许高层Base/FL站位、连续路径与真实接触阶段门控迭代，不改资产物理参数、teleport、weld、辅助力、虚拟unlock或按结果缩scope。被动初动量/独立probe诊断须明确不是demonstration；不能把规定joint姿态当动态验收。

新高度三资产先做真实rest/latched阻挡、lever-cam-follower-bolt/socket接触、joint/finite/reset/mirror核对；Native及CUDA证据能力分开。独立fixture的删除robot/独立球质量/初动量均完整记录；未覆盖真实FL操作不得声称已证明。Backup不制造使用配额，不用A专属路径对B的风险阻断A，但实际资产缺陷须如实保留。

reference先在seed42同nominal下有界开发，每次失败保留轻量日志/实际身份/停止原因，成功完整PhysicalTrace保存。每次试跑依据上次真实误差作高层修复，若发现需要改冻结controller/asset/physics/任务语义则fail-closed集中汇报。成功后冻结recipe，按原dx/dy/yaw与两背景完整16边界真实验证，不重跑成功physics、不收缩范围、不搜索seed。原完整范围如未通过则明确失败，不能宣称高质量可扩量。

普通并发不超过3physics+3render，1GiB MemAvailable/7.6GiB launch-relative swap/0.5GiB紧急render-only回收/4GiB新render门槛保持；当前单Door开发先1physics，scope可2physics，所有launch实际记录。NativeCPU/RAMBOCPU与EGL离线同timestamp render，render不推进physics。W&B not_run/local-only；不WAM/cache/训练/AMD/100/source commit/push或发布。Oven已失败停止，不重启；四项就绪reference保持。

## Progress

- [x] 用户具体资产approval/Work ID登记及proposal/旧source基线。
- [x] 新approved runtime closure与XML/mesh/参数身份保持。
- [x] A/B/C真实Native/CUDA物理资格，真实接触与reset/mirror证据分列。
- [ ] A高质量原RAMBO reference与完整16范围，独立动作质量审计。
- [ ] 完整双RGB/Observer/terminal及集中审核包与治理检查，reference用户批准仍pending。

## 实际物理资格交付 — 2026-10-16

Native12/12、9000个2ms integration steps；CUDA3/3完整scene双world/rest/momentum/reset/同timestamp NativeEGL mirror，1200 world-steps。独立回读summary在workspace runs/audit/door-lowered-reference-20261016-v1/qualification/verified-qualification-summary.json。三asset均在lever nominal范围内真实20mm退栓且socket净空，先于高冲击probe后续overshoot；独立1kg/22mm probe不是Go2或慢压reference，handle峰59–61N/软穿透10.5–11.3mm/后续越限6.29–6.57deg完整披露。CUDA不冒充详细unlock或AMD资格。原asset/source保持，最小available21.716GiB、swap增长0。下一步DATA028原RAMBO nominal/完整16范围，仍未通过reference质量或用户审批。
