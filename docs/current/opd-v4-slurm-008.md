---
id: OPD-V4-SLURM-008
type: current-design
status: accepted
related_work: [OPD-008]
source_map: []
---
# OPD-008：Stage2-only Slurm交付

当前链已由[OPD-012](opd-v4-hf-publication-012.md)增加末尾CPU publish；下文是OPD-008交付时的四阶段证据。

本次已将WAM README和管理员入口切换到独立OPD流程，原SFT指南迁至
WAM `docs/legacy/mujoco-sft-submission.md`。原SFT实现、配置和历史证据保持。

新CLI为 `wam_policy.opd_v4 submit` / `run-stage`，站点模板为
`configs/opd_v4/slurm-site.example.json`，batch入口为 `scripts/slurm/opd-v4-worker.sh`。
同机任务链：prepare(0GPU资源核验)→single-smoke(1GPU)→eight-smoke(8GPU)→formal(8GPU)。
Stage1固定0updates，复用共同SFT checkpoint、normalizer、frozen资源/缓存prompts和prepared reset pool；
不处理离线SFT demonstrations，不生成cache/teacher trajectories，不重拟合normalizer，不自动上传HF。

默认preview无Slurm调用/模型加载/run目录创建。实际submit先hold并afterok串联、逆序release；
失败撤销已知jobs，未知sbatch结果或撤销失败保留ledger并拒绝重复提交。
continue-chain核验同一site/config/source和完整成功前缀，再检查旧jobs已退出。
支持through停在prepare/单卡/八卡smoke；formal保留真实smoke和显式startup acceptance gate。
Smoke权重不复用，只有显式resume恢复完整OPD checkpoint；新attempt/segment记录continuity_break。

每阶段采用独立attempt、成功report及绑定payload hashes。Formal要求400S/1200F和完整student export。
安全停止不将部分阶段计为passed；Slurm预警经launcher通知实际learner PID，保持torchrun agent与
等待feedback的CPU workers，避免torchrun提前强制关闭进程。Signal余量、time/RAM/GRES均需目标实测。
不承诺节点故障、硬SIGKILL或不足时间余量下总能完成新的checkpoint。

## 实际验证

- WAM完整make check通过：225 passed、21 skipped（既有dataset/media fixtures），新增23个测试用例。
- 定向Slurm/launch/admission第一次24 passed；扩展第二次29 passed；最终新增launcher集成测试包含在完整225中。
- 覆盖纯preview与无torch CLI、0/1/8/8分配、Stage1/旧SFT字段拒绝、afterok/逆序release、失败撤销、
  未知提交对账、active job防重、通过报告前缀/防篡改、四阶段fake dispatch、formal失败gate、显式resume、
  路径含空格的batch wrapper、env setup hash、有限smoke数值及learner PID信号路由。
- 所有Slurm命令使用注入的fake runner；模型阶段用CPU fixtures/mock launcher，未调用真实sbatch/squeue/scancel。
- 实际既有资源绑定通过公共configure重新解析，并以公共CLI生成四阶段preview；无run目录、无Slurm调用。
  旧OPD-005 config因过期QLM source hash按预期被拒绝，旧文件保持，未放宽校验。
- 旧README中的SFT指南除迁移后的相对链接外完整保留；既有SFT runtime/config/worker文件hash保持。
- 两repo的docs/governance/import检查及Git whitespace检查见独立日志；QLM runtime未修改，无需重复其旧CPU suite。

首次sandbox外完整测试的自动权限审核超时，重试获准后完整测试通过；不是测试失败。
本轮没有GPU测试、真实physics/rollout、AMD连接、实际Slurm提交、正式训练或完整5B加载。
Fake报告不构成AMD证据。真实ROCm/三角色/八流、站点Slurm信号和资源/性能验收仍not_run。
源码未commit/push；OPD-007已发布的历史提交保持不动。运行时source身份变化，旧smoke receipts不可复用。

证据：workspace runs/audit/opd-v4-slurm-chain-20261024-v1/。
