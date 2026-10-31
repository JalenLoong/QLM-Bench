---
id: QLM-OPD-V4-HANDOFF-20261029
type: current-status
status: accepted
related_work: [workspace/WS-DOC-001, OPD-014, OPD-019, OPD-020]
source_map:
  - src/qlm_bench/backends/mujoco/training_pool.py
  - src/qlm_bench/backends/mujoco/training_live.py
  - src/qlm_bench/backends/mujoco/training_compatibility.py
  - src/qlm_bench/live/transport.py
  - src/qlm_bench/backends/mujoco/training_visualization.py
  - src/qlm_bench/backends/mujoco/training_control.py
---
# QLM quadrupedal OPD 当前交接状态

截至 2026-10-29（Australia/Sydney）。本仓库 `training/opd-v4-streaming-cpu` 配套 WAM 的 `opd/v4_Streaming-OPD_on_WAM-Policy`。跨仓库状态和待办统一维护在 [WAM 当前交接页](../../../WAM-Policy-opd-v4/docs/current/opd-v4-handoff-20261029.md)，本页只补充 QLM 职责。

2026-10-31 已发布：QLM 内容 HEAD `63afc96ff1f0bddf362344d32a15de922024fa05`，WAM `b5bf0217a48698a9ced1e93a093c9858e4b6ebf7`（含 OPD-019 与 OPD-020，从 e0e98b7 / 25e10f6 快进，`git ls-remote` 核对；发布记录 commit 随后推送）。2026-10-30 已发布：QLM HEAD `fc1542be88306924f17bacd5ba3c5a9f33d6e1ea`，WAM HEAD `a26018b2fb40cb7f2ef5f1d90fa90890a44ca1e8`（含 OPD-014 至 OPD-018，已 push 并经 `git ls-remote` 核对）。此前用户 commit 的 OPD-014 为 QLM `b819b9544e7f241cc582b8b5811789d3b7b8bf78`、WAM `d4a961ee6ccb3240ace8e4b592b1059ff437d646`。本次文档整理前两 worktree clean，QLM 比本地 tracking ref `cffbd1d` 多 1 个 commit；本轮未 fetch，未断言远端实时状态。原 [OPD-014 说明](opd-v4-compatibility-014.md)内“未 commit”为历史时点，本页记录后续 local commit。

QLM 当前负责 Native MuJoCo CPU physics、RAMBO CPU、OSMesa/llvmpipe、train800 reset pool、global training profile 和 socket RPC；无需 WAM 内部 import。OPD-014 已实现 EMLINK → copy 回退、运行兼容性合同及部分重复检查简化；既有 pool 无需仅因存储方式变化重建。详细行为见 [OPD-014](opd-v4-compatibility-014.md)、[ADR-0005](../decisions/opd-v4/ADR-0005.md)和 [CPU runtime](opd-v4-training.md)。

已有本地验证：QLM 307 passed / 13 skipped，最后 10 个检查含新增 LINK_MAX 用例；配对 WAM 恢复/资源验证见其交接页。本轮没有重新运行仿真或测试，不把本地结果声称为新 AMD 执行。真实本地 native CPU 结果可佐证 AMD 服务器 CPU 路径；模型 ROCm/RCCL/Slurm 整链需要对应证据。

[管理员反馈](../../../../docs/evidence/amd-feedback-20261028.md)报告此路线 prepare/single-smoke 成功，eight-smoke 当时排队，formal 被旧 startup receipt 挡住；该记录是 2026-10-28 04:00 UTC 的快照。本轮更新的 W&B 读回显示 single/eight-smoke 都已有 student=2/fake=6 更新并标 finished；完整通过/恢复报告未读回，不能据此宣布所有 gate 已通过。具体 run 链接与查询范围见 WAM 当前交接页和 [W&B 摘要](../../../../docs/evidence/wandb-readback-20261029.md)。需要取得实际升级后的输出与续接结果。反馈中 native LIBERO 的 fd1 IPC 故障不适用于这里的 socket 通道；RL Push 的 MJWarp/native replay 不一致也不是本 OPD 的已知失败。

接手 QLM 工作重点：验证管理员原 pool 在真实部署中的来源和可用性、保留已有成功资源；结合日志核对 environment、reset、profile、RPC 和兼容性；支持模型侧训练 prediction 可视化所需的真实 RGB/step/task 对照，但不擅自改 physics 或添加新的失败准入。训练可视化、完整运行日志和实际集群续接仍属待办。

OPD-015（已发布）：新增 `backends/mujoco/training_visualization.py` 与 `training_visualization_case.json`，为 WAM 训练期预测视频跑一个固定 held-out lift_basket reset（场景与现有 train pool 共用），保存 evaluation observer 帧；两者不在 runtime 指纹文件清单内，QLM 运行时指纹不变。详见 [OPD-015](../work/archive/OPD-015/plan.md)。

OPD-016（已发布）：只放宽 WAM 侧旧 run 的全源码指纹；QLM 代码与运行时指纹不变，QLM 旧指纹仍须已登记才能续接。详见 [OPD-016](../work/archive/OPD-016/plan.md)。

OPD-017（已发布）：QLM 侧只在 AGENTS.md 补回 DATA-002 路由（数据上下文测试需要），并按用户决定删除三项依赖已移除 Isaac 环境的测试。详见 [OPD-017](../work/archive/OPD-017/plan.md)。

OPD-018（已发布）：只改 WAM（history KV 复用与每轮 W&B 指标）；QLM 代码与运行时指纹不变，配对记录见 [OPD-018](../work/archive/OPD-018/plan.md)。

OPD-019（已发布）：第二次 formal 的 v2 训练配置。QLM 侧 training profile 升为
`qlm-opd-v4-training-profile-v2`（design `opd-v4-native1-2-5f-900s-v2`），新增 `training_tasks`（去掉
`sweep_block_to_zone` 的 9 个任务）；`EpisodeSchedule` 只在这 9 个任务上调度，train800 pool 与 horizons 不变。
训练视频 case 换成 turn_valve train reset `turn_valve-20261016-001`（validation 场景不在 pool，用户选定）。
`training_compatibility.json` version 为 `native1-2-5f900s-v2`，运行时指纹随之改变，不与 v1 等价。
详见 [OPD-019](../work/archive/OPD-019/plan.md) 与 WAM 交接页。

OPD-020（已发布）：审查后的 v2 调整，只改 WAM（action DMD 权重 0.2、视频第 0/400/800 步、取消 go/no-go、两路梯度分量指标）。QLM 代码、profile v2 与运行时指纹不变，本仓库只镜像 registry 与 [OPD-020](../work/archive/OPD-020/plan.md)。

当前文档整理为 workspace/WS-DOC-001，无代码/config/脚本变更。OPD 新工作继续经 WAM [OPD registry](../governance/opd-v4-work-registry.json)配对。继承 shared-v2/scaleup active 记录只供历史检索，详见 [context 路由](../governance/context-routing.md)。
