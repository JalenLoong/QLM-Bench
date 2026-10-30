---
id: QLM-OPD-V4-HANDOFF-20261029
type: current-status
status: accepted
related_work: [workspace/WS-DOC-001, OPD-014]
source_map:
  - src/qlm_bench/backends/mujoco/training_pool.py
  - src/qlm_bench/backends/mujoco/training_live.py
  - src/qlm_bench/backends/mujoco/training_compatibility.py
  - src/qlm_bench/live/transport.py
  - src/qlm_bench/backends/mujoco/training_visualization.py
---
# QLM quadrupedal OPD 当前交接状态

截至 2026-10-29（Australia/Sydney）。本仓库 `training/opd-v4-streaming-cpu` 配套 WAM 的 `opd/v4_Streaming-OPD_on_WAM-Policy`。跨仓库状态和待办统一维护在 [WAM 当前交接页](../../../WAM-Policy-opd-v4/docs/current/opd-v4-handoff-20261029.md)，本页只补充 QLM 职责。

用户已 commit OPD-014：QLM HEAD `b819b9544e7f241cc582b8b5811789d3b7b8bf78`，WAM HEAD `d4a961ee6ccb3240ace8e4b592b1059ff437d646`。本次文档整理前两 worktree clean，QLM 比本地 tracking ref `cffbd1d` 多 1 个 commit；本轮未 fetch，未断言远端实时状态。原 [OPD-014 说明](opd-v4-compatibility-014.md)内“未 commit”为历史时点，本页记录后续 local commit。

QLM 当前负责 Native MuJoCo CPU physics、RAMBO CPU、OSMesa/llvmpipe、train800 reset pool、global training profile 和 socket RPC；无需 WAM 内部 import。OPD-014 已实现 EMLINK → copy 回退、运行兼容性合同及部分重复检查简化；既有 pool 无需仅因存储方式变化重建。详细行为见 [OPD-014](opd-v4-compatibility-014.md)、[ADR-0005](../decisions/opd-v4/ADR-0005.md)和 [CPU runtime](opd-v4-training.md)。

已有本地验证：QLM 307 passed / 13 skipped，最后 10 个检查含新增 LINK_MAX 用例；配对 WAM 恢复/资源验证见其交接页。本轮没有重新运行仿真或测试，不把本地结果声称为新 AMD 执行。真实本地 native CPU 结果可佐证 AMD 服务器 CPU 路径；模型 ROCm/RCCL/Slurm 整链需要对应证据。

[管理员反馈](../../../../docs/evidence/amd-feedback-20261028.md)报告此路线 prepare/single-smoke 成功，eight-smoke 当时排队，formal 被旧 startup receipt 挡住；该记录是 2026-10-28 04:00 UTC 的快照。本轮更新的 W&B 读回显示 single/eight-smoke 都已有 student=2/fake=6 更新并标 finished；完整通过/恢复报告未读回，不能据此宣布所有 gate 已通过。具体 run 链接与查询范围见 WAM 当前交接页和 [W&B 摘要](../../../../docs/evidence/wandb-readback-20261029.md)。需要取得实际升级后的输出与续接结果。反馈中 native LIBERO 的 fd1 IPC 故障不适用于这里的 socket 通道；RL Push 的 MJWarp/native replay 不一致也不是本 OPD 的已知失败。

接手 QLM 工作重点：验证管理员原 pool 在真实部署中的来源和可用性、保留已有成功资源；结合日志核对 environment、reset、profile、RPC 和兼容性；支持模型侧训练 prediction 可视化所需的真实 RGB/step/task 对照，但不擅自改 physics 或添加新的失败准入。训练可视化、完整运行日志和实际集群续接仍属待办。

OPD-015（本地，未 commit）：新增 `backends/mujoco/training_visualization.py` 与 `training_visualization_case.json`，为 WAM 训练期预测视频跑一个固定 held-out lift_basket reset（场景与现有 train pool 共用），保存 evaluation observer 帧；两者不在 runtime 指纹文件清单内，QLM 运行时指纹不变。详见 [OPD-015](../work/archive/OPD-015/plan.md)。

OPD-016（本地，未 commit）：只放宽 WAM 侧旧 run 的全源码指纹；QLM 代码与运行时指纹不变，QLM 旧指纹仍须已登记才能续接。详见 [OPD-016](../work/archive/OPD-016/plan.md)。

OPD-017（本地，未 commit）：QLM 侧只在 AGENTS.md 补回 DATA-002 路由（数据上下文测试需要）。详见 [OPD-017](../work/archive/OPD-017/plan.md)。

当前文档整理为 workspace/WS-DOC-001，无代码/config/脚本变更。OPD 新工作继续经 WAM [OPD registry](../governance/opd-v4-work-registry.json)配对。继承 shared-v2/scaleup active 记录只供历史检索，详见 [context 路由](../governance/context-routing.md)。
