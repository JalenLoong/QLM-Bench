---
id: QLM-PUSH-RETARGET-SCOPE-REVIEW
type: guide
status: active
related_work: [QLM-DATA-015]
source_map:
  - src/qlm_bench/backends/mujoco/reference_retarget.py
  - scripts/mujoco/synthesis/review_reference.py
  - scripts/mujoco/synthesis/prepare_backgrounds.py
  - scripts/mujoco/synthesis/compare_backgrounds.py
---

# Reference 已接受；retarget 范围审核材料

用户明确接受上一轮 reference-repeat-a01 的动作质量，并要求继续。原reference和trace
保持不变。接受记录位于 workspace `runs/audit/push-retarget-scope-20261014-v1/reference-approval.json`。
本页描述开发验收，不是正式pilot、统计成功率或连续配置空间的成功保证。

## 已定位的问题与修正

对原正向失败点做一次1Hz轻量几何诊断：12s时footprint的X已在goal内，Y上边界
却达到0.4404m，超过原goal上界0.4m；13s进一步达到0.4845m。原retarget继续沿
初始参考路径前推，没有跟踪实际box横向进度。task predicate没有修改。

新固定retarget基于初始box-center→goal-center路径计算实际cross-track误差，
使用有界、有速率限制的FL接触线修正，保留纵向参考推进与已接受的Base/FL工作侧协同。
修正先在两个原失败点实际成功，再加世界目标步长上限8mm/command以平滑阶段衔接。
同一个rule用于全部seed，不写逐case条件。RAMBO、IK、native9、physics、camera不变。

## 预声明的同一smooth-v3开发矩阵

| 配置 | Box dx/dy/yaw | Goal dx/dy | Background | 实际结果 |
|---|---|---|---|---|
| nominal | 0 / 0 / 0 | 0 / 0 | ap_00 | success 8.88s |
| 正偏移 | +4cm / +3.5cm / +0.06rad | 0 / 0 | ap_01 | success 8.88s |
| 负偏移 | -4cm / -3.5cm / -0.06rad | 0 / 0 | ap_01 | success 9.02s |
| 组合偏移 | +4cm / -3.5cm / +0.06rad | 0 / 0 | ap_00 | success 9.06s |
| goal正移 | -2cm / +2cm / +0.03rad | +3cm / -2cm | ap_00 | success 8.94s |
| goal负移 | +2cm / -2cm / -0.03rad | -3cm / +2cm | ap_01 | success 8.82s |

没有falls、没有按结果替换seed；全部push body-midline crossing为0，世界目标步长
不超过8mm（浮点容差）。原v1失败与中间v2实际成功均保留。这里不声称所有连续
组合都必然成功，也不将6/6作为benchmark SR。具体source/trace/scene/metrics在scope-matrix.json。

## 两套背景和goal一致性

ap_00保持原中性地面，ap_01为QLM自定义温和暖色checker地面。没有clutter、
没有新增碰撞物体或改变光照/渲染质量。完整可移植资源与非视觉model arrays比较
验证physics、camera、mass/inertia/collision与reset配置一致。相同state的三视角
实际OSMesa比较通过，rendering不step physics。正式候选必须在physics前选定preset，
后续recording使用相同资源身份，不绕过RenderMirror的identity检查。

Goal平移同步修改四个原contact-free绿色边框和数值goal；矩形大小/成功条件不变。
它是明确task configuration，不是未声明辅助碰撞。实际policy图像用于核对goal可观测性。

开发runner最初继承旧ap_00 scene标签，三个ap_01开发trace的实际resource/profile正确
但scene文字标签错误。原记录不改写；独立correction receipt说明范围。runner已修正，
新ap_01来源回归确认scene/profile/resource与显式executor variant一致；该回归也成功。
所有这些记录都不是正式数据，不得将有标签缺陷的旧开发trace自动纳入formal batch。

## 后续边界

待用户审核的候选范围：Box dx±4cm、dy±3.5cm、yaw±0.06rad；goal平移dx±3cm、dy±2cm。
这是有开发点证据的pilot候选分布，不是全域保证。Clean按用户决定使用nominal附近
不同的小幅真实配置；各split从同一批准ID分布取不同配置并去近重复，不做互斥范围或OOD。
Primary仍为Box05；两backup仅登记真实状态，不增加资产配额。

完成范围审核后才进入Phase5/6的新正式pilot。当前没有生成新formal pilots、没有
扩100、没有新SFT/AMD或publication。原十条仍逐条待审，原SIM-015/P3撤回内容不恢复。

## Retarget 范围获批，启动十条正式 pilot — 2026-10-14

用户明确回复“审核通过，继续推进”，通过已展示的 reference/retarget 第一审核点。
继续既有 QLM-DATA-015 / v2 DATA-016 / v3 DATA-006，冻结 smooth-v3 与两套背景。
正式采样仍为 Box dx±4cm、dy±3.5cm、yaw±0.06rad，goal dx±3cm、dy±2cm；
2 Clean 有小幅真实几何差异，8 Randomized 覆盖正负和组合偏移，全部 train。
每槽预声明5个候选，最多30次实际尝试，连续10次失败即停；不按结果收缩范围。
复用 PhysicalTrace 与 RenditionQueue。先保留最多十条成功 trace，再冻结独立
recording profile；这是本轮有界缓冲，不是100/1000条积压策略。
保留独立行为证据与完整 task success 判据；contact unknown 不自动拒绝。
旧十条不计入新批次：新 executor 要求新的实际执行，旧身份和逐条审核记录保留。
审计根为 workspace runs/audit/push-formal-pilots-20261014-v2/。
十条最终动作质量/覆盖/吞吐仍须用户审核；无100、其他任务、训练、AMD、发布或commit/push。

## 十条新正式 pilot 技术交付；等待最终用户审核 — 2026-10-14

QLM-DATA-015 / v2 DATA-016 / v3 DATA-006 的 Phase0–6 工程交付完成，保留 active
等待既定的十条pilot动作质量/覆盖/吞吐审核。当前审计根为
runs/audit/push-formal-pilots-20261014-v3/，review.html/report.md为最终审核入口；
数据为data/qlm_bench/push-approved-pilot-20261014-v3/。2Clean均ap_00；
8Randomized覆盖ap_00/ap_01及批准的box/goal范围，全部train、仅primaryBox05。
最终4464 actions / 4474 boundaries；原判据、native9/RAMBO、physics/camera保持。
实际共12个candidate：10条合规交付、1次timeout、1条成功但Clean背景配置错误的
历史样本。修正只新执行一条Clean，保留九条合规trace；五条已完成媒体逐字节复用，
原render lineage显式保留。错误批次和全部历史证据保留，不隐去配置纠正成本。
全部Raw/Canonical/terminal/媒体/原telemetry验证通过；双WAM各自Clean/Randomized
实际原VAE、SFT-input、online反馈与cache检查通过，另有十条完整采样RGB与action/
timestamp/tail读取，两路线逐字节一致。无normalizer fitting、训练或policy性能声明。
QLM当前回归140pass/13skip；WAM v2/v3基础回归131/59pass，socket沙箱失败及
复核记录保留。本批未知contact不自动拒绝，task success和demonstration quality分离。
保持最终用户审核gate；没有100、其他任务、AMD、训练、commit/push或远端发布。
