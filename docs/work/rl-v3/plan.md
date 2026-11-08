# RL-v3 阶段 0 工程准备 ExecPlan

- 分支：`rl/v3_frozen-student_external-head_privileged-reward`（WAM 从 a7a4e1c、QLM 从 6b7ce7c 分出）
- registry：`docs/governance/rl-v3-work-registry.json`（namespace `rl-v3`）
- 设计来源：workspace `docs/current/rl-v3-full-plan-20261108.md` 第 7 节、`rl-v3-plan-merged-20261108.md` 第 2 节
- 范围：只做工程与离线/单元检验。不训练、不跑整局 rollout、不连 AMD、不上传、不 push。

## 步骤

| Work ID | 内容 | 状态 |
|---|---|---|
| rl-v3/DOC-001, rl-v3/QLM-DOC-001 | worktree、registry、本计划 | 完成 |
| rl-v3/QLM-SIM-001 | worker execute/restore 返回逐 command 特权数组 | 完成（QLM 07467a9），真实 CPU worker 测试通过 |
| rl-v3/QLM-SIM-002 | 自身状态 capture_state/restore_state RPC 与 CPU 续跑一致性测试 | 完成（QLM e35f638），恢复后 4 chunk 与连续执行逐值相同 |
| rl-v3/ALG-001 | 特权 reward 模块与离线检验 | 完成（WAM f76bab1），push 80 条示教 + 4 类 hack；press/sweep 未做示教检验 |
| rl-v3/INFER-001 | 采样器噪声偏移与有界残差钩子 | 完成（WAM e53de3c），关闭时逐值复现 |
| rl-v3/INFER-002 | GPU VAE 编码与 CPU 对账 | 代码完成（WAM 87ee01b）；GPU 实测见报告 3.4 |
| rl-v3/INFER-003 | 自身状态 history/KV 重建与对账 | 完成（WAM fb47f25、c1f4095），tiny 模型逐值一致；真实模型 GPU 对账未做 |

结果与数字记在 workspace `docs/current/rl-v3-infra-20261108.md`。

## 下一步（未授权执行，仅记录）

- WAM 侧 worker 客户端接 `capture_state/restore_state` 与 `privileged`；RL 循环（collection、buffer、SAC）。
- GPU 空闲时用真实 SFT5000 在 1/2 下做连续 vs 重建的 K/V 与预测对账。
- press/sweep 示教的 reward 离线检验与尺度校准；M1 判据放宽。
