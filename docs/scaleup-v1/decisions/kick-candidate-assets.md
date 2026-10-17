---
id: QLM-KICK-CANDIDATE-ASSETS
type: decision
status: accepted
related_work: [QLM-DATA-023, QLM-DOC-007]
source_map: []
---


## 当前批准与pilot范围（QLM-DATA-024）

用户已批准A primary/B-C backups、实体goal、v3 reference及ball XY±3cm/goal X±8cm Y±5cm完整范围。原static pending与reference pending均为历史。新receipt及冻结50个candidate/pool在workspace runs/audit/kick-formal-pilots-20261015-v1/。Native/CUDA三资产各7项物理及reset/mirror已通过；仅A进行本次2Clean8Randomized正式pilot，backup无使用配额。十条完成后交用户审核，未授权100。public registration仍planned，不能将本地显式profile数据链路冒充public全部ready。

# Kick Ball to Goal候选资产：等待用户确认

[QLM-DATA-023](../work/archive/QLM-DATA-023/plan.md)仅准备静态候选，不把计划中的task注册改成ready。现有MuJoCo可执行实现不存在；本轮compile/render成功不证明动态物理、真实FL踢球、入球predicate、reference或任务难度通过。当前审计workspace runs/audit/kick-asset-review-20261015-v1/，candidates.json/verification.json/prepare_candidates.py记录来源、参数、hash与15张实际静态views。

| 候选 | 外观/来源 | 建议角色 | 实际资格 |
|---|---|---|---|
| A | 自建黑白12五边形/20六边形拼片球 | primary | Native compile/静态EGL通过；用户与动态物理pending |
| B | 自建橙色训练球/黑色缝线 | backup | Native compile/静态EGL通过；用户与动态物理pending |
| C | 自建蓝白拼片球 | backup | Native compile/静态EGL通过；用户与动态物理pending |

三者使用相同候选解析球碰撞/质量参数：直径0.20m、质量0.40kg、主惯性0.0016kg·m²、friction[0.6,0.005,0.0001]、condim6；只外观profile不同，不声称三种不同动力学或制造backup使用配额。visual panel与analytic collision独立；球与地面/球门必须通过真实碰撞作用，不能额外teleport、隐形约束或辅助外力。

共用自建小型实体训练球门：内宽0.80m/净高0.45m/深0.40m，门柱半径0.02m，门柱/横梁/后侧网均具有实际capsule碰撞；正面开放。后续任务语义仍是踢进真实球门，不以平面zone替代。static world固定球门框架；preview球至球门1m仅为展示摆放，不是正式randomization range。没有equality constraint或controller。全部项目自建几何与生成器可重建，无第三方mesh/texture依赖，最终公共license grant在发布阶段固定；本轮不发布。

这些尺寸、参数与角色均为候选，等待用户资产审批。Native EGL静态自由取景只供资产审核，正式双RGB640×36050FPS及Go2/STEP rig camera不改。0physics steps、0controller commands、0reference、0formal demos。普通后续本地3+3/swap增量7.6GiB及原RAM保护保持，OSMesa reference、AMD优先ROCm保持。原RAMBO/native9/500-100-50Hz与独立task success/quality规范保持，正式范围与pool在pilot前冻结。

用户确认后才进入针对性真实物理资格及高质量reference/retarget范围审核；再10pilot审核、补100/最终验收。Push/Press/Lift已通过的WAM task一次资格不重复；Kick新task资格留formal pilot。当前WAM/cache/训练/AMD/commit/push/发布均not_run。

## 用户批准及实际物理资格

用户“审核通过，继续推进”已确认A primary/B/C backups与全部候选参数。独立审批及Native/CUDA各21项被动物理、实际球门接触/reset/mirror证据在workspace runs/audit/kick-reference-20261015-v1/，QLM-SIM-019拥有新pack与predicate。当前DATA023进入原RAMBO reference开发，下一人工gate为reference动作质量/范围；不得根据被动物理通过声称backup已完成完整踢球/SFT资格。旧static-pending表只记录其原时点。

## Reference工程交付，范围仍待用户批准

原RAMBO v3真实16.22s成功及相同完整16角点重验全部成功；详见workspace runs/audit/kick-reference-20261015-v1/review.html。高层carry收腿修正取代早期会提前碰球的v2，原negative scope5timeouts保留。范围ball dx/dy±3cm、goal dx±8cm/dy±5cm只是待审批提案；本asset批准不自动等于reference/pilot审批。formal仍0，public registration仍planned，完整Raw/Canonical新task入库与task一次WAM资格留下一pilot阶段。
