---
id: QLM-SIM-017
type: change
status: completed
source_map: []
---

# Approved Lift Basket assets targeted Native/CUDA physics, reset and mirror qualification

## Scope / contracts

用户批准Lift资产并指定A为primary，B/C为backup；原review/原models保持。SIM以新版本diagnostic fixture执行无controller的Native/CUDA静止/自由落体/真实sphere接触与提手可穿入性，不把passive测试当RAMBO任务完成；镜像必须完整qpos/qvel/time，不能独立推进physics。A实际RAMBO reference为QLM-DATA-020，backups不要求reference quota或阻塞已资格primary。没有正式pilot/100、WAM/训练/AMD/发布/commit/push。

WAM DOC只同步consumer治理，原Push/Press资格复用不重新cache；Lift新task一次正式检查留pilot阶段，不能以P2历史工程证据替代。固定native9/force-zero/原controller/history、500/100/50Hz、task success/Canonical/camera/OSMesa/LOD保持。源resource/历史attempt/失败都保留。

## Progress

- [x] 2026-10-15 核对用户资产批准并记录独立receipt。
- [x] 2026-10-15 三资产Native/CUDA targeted qualification通过，user/reference/scope边界同步。
- [x] 2026-10-15 docs/import/shared治理、11pass/1skip作用范围CPU、原623文件/三个HEAD保护通过，归档；DATA020 reference用户gate保持。

## Decision log / discoveries

原OASIS A已获主资产选择；unknown license不因审批改写，当前仅本地验证。B/C为原审阅的自建geometry，物理资格需要真实证据。成功定义仍为整个basket最低点离地2cm/notfallen/三tick；passive fixture不执行task成功判据。只允许预先声明初态与自由probe速度，无执行中的对象teleport/隐形constraint/辅助托举力。

## Validation / recovery / outcomes

workspace runs/audit/lift-reference-20261015-v1/。数据/模型/HEAD及原A资源hash保护。完整正式Native与CUDA精确轨迹一致不作为要求，只验收物理语义与合理数值行为；Native按CUDA snapshot重建contact的范围与真实CUDA force测量严格分开。失败保留并报告，不修改solver绕验收。当前实际物理结果not_run。

## 实际交付

## Lift Basket A reference交付；等待动作质量与范围审核 — 2026-10-15

A原OASIS编织篮为用户指定primary、B/C为backups。QLM-SIM-017的Native/CUDA被动物理资格三资产均通过；A原RAMBO实际高层recipe lift-body-lane-geometry-v2完成770actions/771boundaries、15.40s success/not-fallen，整篮最低点30.848mm，原20mm/三50Hz ticks判据未改。完整足端先穿孔后托举；实际snapshot几何为FL腿部接触38boundaries、base/其他腿0，sphere-only FL接触为0不直接拒绝。

原expert抬腿/伸腿hip最大10ms约5.3deg，推荐v2相应1.0–1.2deg、托举1.99deg；保留原gait及三成功开发trace，不宣称所有波动消失。仅高层Base/FL站位/轨迹连续性改变，原controller/IK算法/PD/QP/history/physics/camera/asset/default保持。预声明dx/dy±3cm、yaw±5deg八个product角点8/8实际成功，无重试/收缩，完整穿孔后托举/base-contact0；范围是proposal仍待用户批准，不是policy SR或全部seed验收。

完整NativeOSMesa双640×36050FPS/Observer1280×72025FPS及terminal验证通过，完整同timestamp snapshot镜像未推进physics；两个Background只换floor外观，非visual/camera/solver完全相同。主render507.4s/15.4s simulation（非稳态生产吞吐保证），scope2physics实际并发总820.1s，无guard，最低available6.97GiB/maxswap增长212.32MiB。范围trace是非formal geometry诊断，早期nominal task.goal.XY配置偏移元数据不提升为正式data；未来入口已用既有episode-goal overlay对齐初态XY，实际Native零步检查仅goal字段变、物理和其他state不变，旧trace不改写。

审核workspace runs/audit/lift-reference-20261015-v1/review.html与report.md。QLM-DATA-020保持active等待reference动作质量和范围审批，未批准前不10pilot/100。Lift正式0、Push100+Press100累计200/1000。WAM兼容性每task一次留pilot，本轮未加载WAM/checkcache/fit/训练/AMD/commit/push/发布；A asset包license unknown待资源交付前核实，未因视觉审批改写。


被动fixture引入的自由sphere仅作资产物理测试，不用于task成功。MuJoCoPhysics会import RAMBO joint/body mapping constants，但没有实例化controller或加载checkpoint；旧passive result的RAMBO_loaded=false指后者，不作为“没有import任何相关module”的证明。实际RAMBO task为独立DATA020。原代码/weights/scene/profile/default/历史数据/静态review及三HEAD未改，geometry/goal metadata修正不变原contract含义。检查通过后归档本SIM/DOC；DATA020保持active。
