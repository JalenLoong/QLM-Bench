---
id: QLM-DATA-023
type: exec-plan
status: completed
source_map: []
---

# Kick Ball to Goal：已批准资产的高质量reference与retarget范围审核

当前工程交付完成，等待用户审核v3 reference与ball dx/dy±3cm、goal dx±8cm/dy±5cm范围。QLM-SIM-019与v2DOC-021/v3DOC-020已归档；本DATA023仍active，无formal pilot/100授权。

## 最初资产准备阶段（以下为历史）

仅准备至多三个候选：真实球体＋门柱/横梁/后侧球网组成的实体球门。现有kick_ball_to_goal注册为planned，不能冒充已有MuJoCo task。优先自建可复现参数化资产，无第三方下载，候选来源/几何/碰撞/质量/摩擦/惯性/version/hash与未执行项明确记录。用户确认资产之前只Native compile/mj_forward/static render，0physics steps/0controller/0reference/0demonstrations。角色与参数是提案，不是批准asset pool，不制造backup配额。

后续仍资产审核→实际物理资格及高质量reference/retarget范围审核→2Clean8Randomized十条pilot审核→补至100及最终验收。仅当前候选阶段获准，不跨gate。保留原RAMBO/native9/500-100-50Hz/640×36050FPS及原camera语义；正式task success保持真实入球要求，不能用平面zone替代实体球门。新task数值范围/正式predicate与pool将在对应阶段冻结，不在静态预览中虚称完成。任务只用FL真实接触，不使用teleport/辅助外力/隐形约束。

后续本地NativeCPU/RAMBOCPU＋EGL，普通3+3、swap增量7.6GiB及原资源保护；OSMesa reference与AMD优先ROCm保持。本轮不WAM验证/cache/训练/AMD/commit/push或发布。Kick的task一次WAM资格留正式pilot，不复验Push/Press/Lift。

## Progress

- [x] 核实Lift100用户批准、三repo真实状态和Kick planned注册。
- [x] 三候选profile/解析质量惯性/来源/hash、15路Native EGL静态预览与审核页交付。
- [x] 用户确认A primary、B/C backups及共同球门；asset gate解除。

## Evidence / recovery

workspace runs/audit/kick-asset-review-20261015-v1/；本work不改已验收数据、旧Isaac、原models/weights/env/default或已有task source，不创建分支。静态render不证明动力学、动作质量或任务难度通过。

## Actual static evidence

三个model compile/质量惯性检查、15张960×720 PNG和3张720×850 JPEG已生成，实际GL vendor=NVIDIA/RTX5070Ti；0physics/controller/reference。球门前口开放、实体post/crossbar/back-and-side net，所有角色/尺寸/范围资格仍pending。等待用户资产审核，不能因工程预览通过自动推进物理或reference。已有源码/模型/三task数据不变。

## 用户资产批准后的当前授权

A/B/C及共同球门已批准，独立receipt在workspace runs/audit/kick-reference-20261015-v1/asset-approval.json。QLM-SIM-019完成针对性物理与新task profile，DATA023继续原RAMBO high-level reference/retarget范围；保留前述计划中的所有接口与三次首轮开发预算。当前停点改为reference/范围用户审核，未授权formal pilot/100。WAM本阶段仍not_run。

## 工程交付完成，当前人工gate

## Kick reference与范围工程交付；等待用户审核 — 2026-10-15

已批准A primary/B-C backups及实体球门；QLM-SIM-019的Native/CUDA三资产各7项被动物理、真实接触/reset/mirror均通过。新Kick判据为正面整球入实体goal/notfallen/三50Hz ticks，旧三task判据和action/state/Raw/Canonical接口保持；public task注册仍planned，未冒充formal production ready。

QLM-DATA-023交付推荐kick-impulse-retract-v3-tucked-carry reference：原RAMBO NativeCPU真实16.22s、811actions/812boundaries，pre-strike球位移0，FL接触仅strike阶段3个50Hz boundary，之后自由滚动4.22s入门；原gait小幅波动保留。三个nominal开发成功trace全部保留，未训练或改controller/IK/PD/QP/history/asset mass-friction。

v2首轮范围11/16、5timeouts保留；只将高层carried FL目标X .23→.16后，对相同seed42、相同完整16角点和两背景重新真实执行，v3为16/16，全部pre-strike位移0，50Hz snapshot未发现其他robot部位碰球。范围提案ball X/Y±3cm、goal X±8cm/Y±5cm，仍待用户批准；未按结果收缩或搜索seed，不宣称全连续状态或policySR。两轮对应model resource identity逐点相同，16点球/goal都可由原policy相机观察。

审核workspace runs/audit/kick-reference-20261015-v1/review.html与report.md，宽视角画面只用于人工诊断，原Ego/Task/Observer、dual360p50FPS和Observer720p25FPS保持；所有图像导入真实同timestamp snapshot，不独立推进physics。DATA023保持active，等待reference动作质量与范围审核；未批准前不10pilot/100，formal Kick0，原Push/Press/Lift300/1000已验收保持。Kick task一次WAM资格留pilot，v2DOC-021/v3DOC-020仅治理，无WAM执行/cache/训练/AMD/commit/push/发布。后续本地普通3+3/swap增量7.6GiB及原保护保持。以下旧pending只保留历史时点。

- [x] A/B/C实际Native/CUDA资产资格、新task判据与原task回归。
- [x] 三个真实nominal开发attempt；推荐v3与完整media/状态/质量/原相机可见性证据。
- [x] 原16点11成功5timeouts保留；同范围v3重验16/16，两个Background和目标可见性通过。
- [ ] 用户审核推荐reference动作质量及上述retarget范围。审核前不得formal pilot/100。

## 用户后续批准（2026-10-15）

推荐v3 reference及完整ball XY±3cm/goal X±8cm Y±5cm范围已获批准。原pending记录保留历史，新独立receipt：workspace runs/audit/kick-formal-pilots-20261015-v1/user-approval.json。资产/reference/范围工作完成；后续十条pilot归QLM-DATA-024，未授权100。
