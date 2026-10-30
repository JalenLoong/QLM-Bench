# RL-v2 agent guide

本 checkout 的 branch 为 `rl/v2_GT-guided_chunk-level_close-loop_NFT`。
本仓库负责任务、MuJoCo/RAMBO、场景、GT replay、snapshot 恢复、环境通信与评估；配套 checkout 是 `../WAM-Policy-rl-v2`，必须显式选择这套 RL source。
不要改用 workspace 的旧 Isaac/SFT checkout，也不要从旧 active 文档推断需要恢复任务。

启动顺序：[docs/INDEX.md](docs/INDEX.md) → [当前交接状态](docs/current/handoff-20261029.md)
→ [context routing](docs/governance/context-routing.md) → 相关设计/源码/证据。
先核对 branch、HEAD 和已有 dirty diff，再开始工作。管理员提交入口由 WAM RL README 负责。

遵循 [原治理协议](docs/governance/documentation.md) 和 [.agent/PLANS.md](.agent/PLANS.md)。
Work ID 必须连同 repository、branch 和 namespace 定位；历史 registry 保留原身份，不能据裸 ID
或旧 `active` 路径判断现状。本次文档整理统一登记为 `workspace/WS-DOC-001`。

保留 Go2/FL/native9、原 RAMBO controller、force-zero、既定 RGB/action/timestamp 与 terminal-before-reset
契约。WAM 不直接导入 simulator；QLM core 不导入模型/VAE/T5，使用公开接口通信。
Push Box 与 Sweep Block 各自训练/验证/checkpoint/W&B；一套共享 single/eight smoke 的设计不变。
当前 LoRA/十 demo/120-round 数值方案见 current 页；不要用历史单 demo 或 full-parameter 方案覆盖。

本地 native MuJoCo CPU 通过可佐证 AMD 服务器 CPU 路径；Push 的原问题是 MJWarp 采集的 demonstrations
被固定用 native CPU replay 后有部分未成功，不能误写成 MuJoCo CPU 不可用或固定调用 MJWarp。
ROCm learner、多卡和 Slurm 的问题必须按实际日志定位。不要因外层 CalledProcessError 猜测根因。

保留原始数据、模型、成功/失败记录、历史 manifest 和其他分支修改；清理须按用户审查的名单执行。
执行训练/集群提交/发布须符合当前授权，不自动恢复历史 run。
代码变更做有意义的受影响验证；纯文档工作只检查文档和范围。来源记录不能默认升级为运行准入。
数据存储与终止语义以 DATA-002 冻结的 `wam-quadruped-v2.1.0` 为准，见 [当前数据合同](docs/current/adaptation_v2_dataset_contract.md)；DATA-001 旧验收只作历史。
旧历史入口保存在 [逐字节快照](docs/history/context-before-20261029/README.md)，不作为当前操作指令。
