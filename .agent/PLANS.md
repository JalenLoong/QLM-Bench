# Work-plan protocol

遵循原项目文档与 Agent context 治理原则：稳定规则留在 AGENTS；当前语义/状态在 current；
ChangeSpec 记录预期行为，ExecPlan 记录执行与下一步，ADR 记录重要语义决策，实际运行使用真实 attempt manifest。
按变更风险选择文档重量，不为每个小修复机械新增多套文档。

先读 docs/INDEX.md 与 docs/governance/context-routing.md，确认实际 branch、dirty 状态和用户范围。
当前跨 workspace 文档整理统一使用 workspace/WS-DOC-001，登记于 workspace docs/governance/work-registry.json；
本仓库不复制另一个独立登记，不占用历史算法 Work ID。
后续多文件实现应建立可恢复的 ChangeSpec/ExecPlan 并关联工作身份；完成后配对归档。

历史 registry、旧 run/manifest、原 source/checkpoint 身份不回写。需要纠正当前解释时写 current 页并链接旧证据。
继承的 active 文档不是运行中任务列表。先查 context routing，Work ID 必须带 branch/namespace 和仓库定位。
算法、动作/相机/时间、数据/恢复/评估语义改变才需要相应 ADR/current 更新；实现通过不等于科研收益被证明。

纯文档工作只做文档/链接/范围检查。代码更改验证受影响行为；CPU physics 证据和 GPU/RCCL/Slurm 证据分别记录。
不将来源 hash、人工确认或可选科研实验自动变为训练准入，不因文档整理重跑历史任务。
