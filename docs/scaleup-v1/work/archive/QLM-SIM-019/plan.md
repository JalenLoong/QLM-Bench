---
id: QLM-SIM-019
type: exec-plan
status: completed
source_map: []
---

# Approved Kick three-asset portable Go2 packs, actual Native/CUDA physics/reset/mirror qualification and goal-mouth predicate adapter

用户批准三候选及共同实体球门，A primary/B-C backup。QLM-SIM-019建立独立portable Go2/原STEP LODa02资源pack，保留原robot/camera/solver/checkpoint/控制语义；QLM-DATA-023继续真实FL踢球reference与适用范围。新的Kick task profile实现球完整从正面穿过门口、处于实体goal内部、notfallen/三50Hz tick的机器检查，拒绝侧后入场/横梁上方/门柱外及初态已入球；不修改原三task predicate、Raw/Canonical/action/state schema。参数化球mass/friction/尺寸及goalgeometry按已批准值保持，不辅助加力/teleport。

先实际Native/CUDA被动物理资格（自由落体/滚动/真实足端半径probe碰撞/门柱横梁/后侧网/reset其他world不变/完整state mirror）；predeclared初速度仅诊断，明确非demonstration，不能冒充RAMBO task成功。reference使用原controller NativeCPU/RAMBOCPU＋EGL，500/100/50Hz、双640×36050FPS/Observer720p25FPS和原camera，physics与offline render不相互推进。

先最多3个明确24s-or-terminal high-level recipe开发attempt，相同seed42，成功trace保持，失败轻量日志；不按结果调小asset/predicate或偷偷筛seed。需要controller/contract/物理语义变化时报告。用户reference及范围审核前不pilot/100；成功与独立动作质量分开，unknown contact不硬失败。后续普通3+3、swap增量7.6GiB及原保护保持。

WAM本轮仅治理，不加载模型/验证/cache/fit/训练；Kick task一次兼容留pilot。Push/Press/Lift原300数据和资格保持，其他tasks/AMD/commit/push/发布不做。

## Progress

- [x] 用户批准receipt及实际source保护baseline。
- [x] portable三approved scenes与新Kick predicate；17项新/既有task语义及reset检查通过。
- [x] 实际Native/CUDA物理资格及reference工程交付；DATA023保留用户审核停点。

## Evidence

workspace runs/audit/kick-reference-20261015-v1/；当前static candidate历史pending receipt不改写。

## Actual passive evidence

qualification-native-a01/result.json与qualification-cuda-a01/result.json均通过，三个asset各7项、真实FL半径probe、门柱/横梁/网接触、roll-in、reset其他world保护和EGL完整mirror。无外加wrench、无RAMBO/task数据计数；CUDA effective solver/tolerance按实际metadata保留，不宣称AMD通过。

## 实际交付与边界

## Kick reference与范围工程交付；等待用户审核 — 2026-10-15

已批准A primary/B-C backups及实体球门；QLM-SIM-019的Native/CUDA三资产各7项被动物理、真实接触/reset/mirror均通过。新Kick判据为正面整球入实体goal/notfallen/三50Hz ticks，旧三task判据和action/state/Raw/Canonical接口保持；public task注册仍planned，未冒充formal production ready。

QLM-DATA-023交付推荐kick-impulse-retract-v3-tucked-carry reference：原RAMBO NativeCPU真实16.22s、811actions/812boundaries，pre-strike球位移0，FL接触仅strike阶段3个50Hz boundary，之后自由滚动4.22s入门；原gait小幅波动保留。三个nominal开发成功trace全部保留，未训练或改controller/IK/PD/QP/history/asset mass-friction。

v2首轮范围11/16、5timeouts保留；只将高层carried FL目标X .23→.16后，对相同seed42、相同完整16角点和两背景重新真实执行，v3为16/16，全部pre-strike位移0，50Hz snapshot未发现其他robot部位碰球。范围提案ball X/Y±3cm、goal X±8cm/Y±5cm，仍待用户批准；未按结果收缩或搜索seed，不宣称全连续状态或policySR。两轮对应model resource identity逐点相同，16点球/goal都可由原policy相机观察。

审核workspace runs/audit/kick-reference-20261015-v1/review.html与report.md，宽视角画面只用于人工诊断，原Ego/Task/Observer、dual360p50FPS和Observer720p25FPS保持；所有图像导入真实同timestamp snapshot，不独立推进physics。DATA023保持active，等待reference动作质量与范围审核；未批准前不10pilot/100，formal Kick0，原Push/Press/Lift300/1000已验收保持。Kick task一次WAM资格留pilot，v2DOC-021/v3DOC-020仅治理，无WAM执行/cache/训练/AMD/commit/push/发布。后续本地普通3+3/swap增量7.6GiB及原保护保持。以下旧pending只保留历史时点。


## 工程验收与归档

28项CPU回归通过/1项因未显式指定Go2 model/GL而skip，随后实际EGL单项补验通过，三资产Native/CUDA各7项实际物理及reset/mirror通过；新reference和同16角点v3全部真实成功，完整原相机媒体与额外诊断视角、目标可见性/两轮几何同identity、源版本及799个受保护文件/三HEAD检查通过。六项active治理/import检查通过。本SIM/consumer治理工程完成，用户reference/范围审批仍由QLM-DATA-023 active gate管理；不生成formal数据或WAM缓存，不训练/AMD/commit/push/发布。

实际EGL补验：使用已批准A pack，原render镜像不推进physics、拒绝非法model/camera/world/timestamp变更的独立检查1pass。日志workspace runs/audit/kick-reference-20261015-v1/actual-egl-regression.log。CPU28pass加该实际补验共29个不同检查通过，不重复WAM。
