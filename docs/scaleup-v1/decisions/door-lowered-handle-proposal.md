---
id: QLM-DOOR-LOWERED-HANDLE-PROPOSAL
type: decision
status: accepted
related_work: [QLM-SIM-021, QLM-DATA-028]
source_map: []
---

# Room Door：允许提出较低把手及完整锁机构profile

用户批准的是新资产提案路线，尚未批准具体高度、新资产pool或动态reference。先在原RAMBO/原IK和相机契约下比较可达性，生成完整机构整体下移的新A/B/C，集中交用户审核；获批后再实际物理验收和reference。原35cm资产及历史证据保留，controller扩展/重训路线未被选中。

当前高度分析仅是假设下的限位改善，原IK→FK投影误差必须单独核对，不把“零越限”当作可达或成功。移动范围包括lever/cam、bolt、strike/socket及配套面板，不修改弹簧/摩擦/质量/解锁或开门判据。新几何会改变reach难度，这是用户明确允许提出的变化；精确高度与视觉profile等待下一次资产审核。

Work与实际证据：QLM-SIM-021；workspace runs/audit/door-lowered-asset-review-20261016-v1/。本阶段physics/inference/reference/formal均0。QLM-DATA-028的四项完整reference、Oven nominal成功/范围失败与其停止状态保持。最终随机十条人工审核仍延后至全部task合成完成。

## 具体提案交付

已形成28cm（下移7cm）统一A/B/C，仍1primary+2backups；29–31/28.5cm分析结果用于选择，不形成额外正式pool。120父文件与原controller保持，静态机构/相机/接近几何及NativeEGL图见SIM021审核包。此处accepted仅指用户允许提案路线；28cm资产仍待审核，动态物理及reference均not_run。

## 28cm具体profile用户批准 — 2026-10-16

用户已明确批准28cm A primary/B-C backups并授权真实物理和原RAMBO reference/完整范围，独立receipt在workspace runs/audit/door-lowered-reference-20261016-v1/asset-approval.json。SIM021已归档，SIM022承接物理资格、DATA028承接reference，原proposal/旧35cm证据不回写；此批准不等于动态/reference已通过，未授权100。
