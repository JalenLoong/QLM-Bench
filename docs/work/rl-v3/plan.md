# RL-v3 阶段 0 工程准备 ExecPlan

- 分支：`rl/v3_frozen-student_external-head_privileged-reward`（WAM 从 a7a4e1c、QLM 从 6b7ce7c 分出）
- registry：`docs/governance/rl-v3-work-registry.json`（namespace `rl-v3`）
- 设计来源：workspace `docs/current/rl-v3-full-plan-20261108.md` 第 7 节、`rl-v3-plan-merged-20261108.md` 第 2 节
- 范围：只做工程与离线/单元检验。不训练、不跑整局 rollout、不连 AMD、不上传、不 push。

## 步骤

| Work ID | 内容 | 状态 |
|---|---|---|
| rl-v3/DOC-001, rl-v3/QLM-DOC-001 | worktree、registry、本计划 | 完成 |
| rl-v3/QLM-SIM-001 | worker execute/restore 返回逐 command 特权数组 | 进行中 |
| rl-v3/QLM-SIM-002 | 自身状态 capture_state/restore_state RPC 与 CPU 续跑一致性测试 | 进行中 |
| rl-v3/ALG-001 | 特权 reward 模块与离线检验 | 进行中 |
| rl-v3/INFER-001 | 采样器噪声偏移与有界残差钩子 | 进行中 |
| rl-v3/INFER-002 | GPU VAE 编码与 CPU 对账 | 进行中 |
| rl-v3/INFER-003 | 自身状态 history/KV 重建与对账 | 进行中 |

结果与数字记在 workspace `docs/current/rl-v3-infra-20261108.md`。
