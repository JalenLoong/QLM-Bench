---
id: QLM-DATA-039
type: change-spec
status: completed
related_work: [QLM-DATA-034, QLM-DATA-038]
source_map: []
---

# 三项修订reference完整范围验证

用户批准Fridge A04。采用Fridge DATA038 A04（50deg/实际门面随动）、Oven DATA034 a01（1kg/35deg/4s）、Valve DATA034 a01（6s）；原名义成功不重跑。每项XY±2cm/yaw±5deg，Fridge初角45–55（50±5，原宽度10deg平移）、Oven25–35、Valve0–5，各16全组合与两背景各8。Fridge范围平移依据用户初角55→50，最终范围仍交本轮集中确认，不按结果缩域。

复用已有scene factory、NativeCPU/原RAMBOCPU、PhysicalTrace验证和single-writer调度。模型仅显式刚体布局/初态/背景变换，核对原质量/惯量/摩擦/solver/controller/camera。每task source/recipe/seed42/horizon固定，Fridge40s/Oven60s/Valve32s。普通最多3physics、1GiB available与7.6GiB launch-relative swap保护；首真实失败停止该task新派发并排空，独立task可继续。实际成功不重跑，失败日志轻量；不可借旧版本scope冒充当前通过。

逐条独立核对初态/真实predicate/首次成功及时终止、50Hz command/state、既有500/100Hz时钟、source/模型/背景身份，真实机器人接触单列quality诊断，未知contact不硬失败。范围模型静态检查不是动态资格；本轮NativeCPU，不能宣称CUDA/AMD已实测。完成后集中三条获批reference视频+范围统计供用户确认，若失败则原失败/not_run如实列出。无100/WAM/cache/训练/AMD/发布或其他task重跑。

- [x] A04批准与DATA038配对归档、DATA039建立。
- [x] 48模型及source冻结；质量/惯量/solver/camera检查通过，48初态无robot-asset穿透，0physics。
- [x] 本轮真实范围结果已交付，实际通过/not_run见结构化记录。
- [x] 集中审核页与原source保护完成，等待用户确认。

## DATA039修订范围交付：Close Fridge Door 16/16；Close Oven Door 16/16；Turn Valve 16/16 — 2026-10-16

Fridge A04已获用户批准；Oven1kg/4s与Valve6s reference批准保持。本轮实际执行48项、工程验收48/48，逐项失败/not_run保留。范围共同XY±2cm/yaw±5deg；Fridge45–55（50±5，宽度不缩）、Oven25–35、Valve0–5，两背景各8；原recipe/RAMBO/成功条件/相机/seed42保持，nominal未重跑。

集中审核workspace runs/audit/revised-three-scope-20261016-v1/review.html，结构化reference-scope-catalog.json包含全部source、实际首次接触角及非FL/FL非足端接触观察。每task代表范围视频按最大非FL力、FL非足端力、成功时长依次选取，不是正式随机审核。初始范围与实际接触角分开，不冒充全过程同角度分布。NativeCPU范围证据，不宣称CUDA/ROCm已复测。

所有physics/render已结束；DATA039保持active等待用户集中确认，工程验收与动作质量批准分开。原400和其他批准保持，无新formal/100/WAM/cache/训练/AMD/commit/push/发布。108个原source及checkpoint/三repo HEAD保持。


用户已批准三项修订范围；独立receipt为workspace runs/audit/revised-three-scope-20261016-v1/user-scope-approval.json。原工程结果不回写。后继QLM-DOC-008只进行治理/交接，不启动100。
