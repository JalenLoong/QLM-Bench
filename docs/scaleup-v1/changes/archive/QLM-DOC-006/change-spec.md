---
id: QLM-DOC-006
type: change
status: completed
source_map: []
---

# 用户采用本地 Native CPU＋EGL 4+4

用户在并发结果表中明确选中 Native CPU＋EGL 4+4，并要求写入治理文档。将其记录为后续本地采用的路线/并发目标，替代此前3+3建议；保留原资源保护、OSMesa跨平台reference、AMD路线与既有数据身份。只更新治理，不修改producer/runtime/validator，不开始合成或复测，不恢复已清理测试产物。

- [x] 核对用户选择与既有治理状态，独立登记Work ID。
- [x] 更新唯一配置来源、两个AGENTS、当前进度、合成决定及baseline/README路由。
- [x] 核对历史/当前范围与资源阈值，治理/文档检查通过，成对归档。

配置采用不等同于producer已接入、完整端到端生产验收、视觉等价或长时间稳定性证明。正式数据及Lift pilot人工审核保持各自身份和状态。

验收：用户采用配置与原资源阈值静态核对通过；治理及文档检查通过。未运行physics/render/WAM或生成任何新数据、cache；未修改producer/runtime/validator或发布。
