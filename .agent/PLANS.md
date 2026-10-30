# Work-plan protocol

根据风险使用原 [文档治理协议](../docs/governance/documentation.md)：R0 只读说明，R1 小改动使用 issue/验证记录，R2 多文件可恢复工作维护 ExecPlan，涉及算法/数据/checkpoint/评估语义的 R3 再配 ChangeSpec 和 ADR。不要把所有小改动都扩成新流程。

本分支 OPD 使用 `docs/governance/opd-v4-work-registry.json`；WAM 分配 OPD Work ID，QLM 镜像配对。实现前确定本次范围、相关合同、验证和未执行项；完成后将本次 ChangeSpec/ExecPlan 配对移入 archive。保留实际 attempts 的原始 manifest，不为未运行任务制造证据。

当前算法、最新源码/部署状态分别由 [文档索引](../docs/INDEX.md) 和 [交接状态](../docs/current/opd-v4-handoff-20261029.md) 路由。shared-v2 / MuJoCo / scaleup 的继承 active 条目不能作为 OPD 的执行授权；历史编号按 repository + branch + namespace + Work ID 定位。

当前跨 workspace 文档整理是 `workspace/WS-DOC-001`，由 workspace 的 docs/governance/work-registry.json 与 docs/work/INDEX.md 统一记录，不新增 OPD 算法工作或重写历史 registry。

每次交接更新当前 plan 的进度、证据、未决问题和下一步；清楚区分代码已实现、local committed、已发布、AMD 实际执行及算法效果。测试按变更风险选择；本地 native MuJoCo CPU 验证是服务器 CPU 路径的有用证据，不自动代表整条 ROCm/Slurm 训练链已通过。

整理前全文见 [历史 context 快照](../docs/history/context-before-20261029/README.md)。
