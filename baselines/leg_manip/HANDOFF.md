# Leg-Manip 项目交接

交接日期：2026-10-27，Australia/Sydney。23:20只读核查：两轮pipeline均completed/exit0，
GPU无计算进程，项目的两个结束监测均已删除。此次交接不启动训练，也不推送或合并GitHub。

## 1. 接手时先知道的结论

> **2026-10-28晚更新（以此为准）**：已有合格的正式控制器 `leg-manip-controller-go2-seed0-20261028-145340`
> （W&B dfa5vhi5，HF已核验；跟踪门槛全过，专家按钮100%、洗碗机91%，示范相机全程可见物体），
> 并用它在5090采好两任务各100条正式示范 `data/demos/legmanip-demo-20261028-152457/`。
> 已上传到公开数据集仓库 `Ethan-Xu-Deng/legmanip-demo`（commit `f096ba95…`，下载回来逐文件SHA核验一致）。
> 下一步是AMD上的DP3训练（`lm-train-planner --hf-repo Ethan-Xu-Deng/legmanip-demo --hf-file <task>.zarr.zip`），
> 须用户决定后再启动。
> 过程与证据见AGENTS.md与TRAINING_RUN.md顶部。
>
> **2026-10-28更新**：诊断出Lift失败根因（重心转移段奖励平坦）并加入操作脚载荷占比奖励、修正Lift起点；重训的 `leg-manip-controller-go2-seed0-20261028-012627`（W&B df5yqprr）三seed×双前腿全部通过Lift门槛。详见TRAINING_RUN.md顶部。以下为10-27交接时的原文。

四部分算法已有实现，但目前只有按按钮、关洗碗机两个任务。**尚无合格低层控制器，
没有正式成功示范数据，也没有正式DP3效果复现。**126项回归通过是工程证据。

第一次30000轮训练学成了前脚接地、抬起后腿的策略。修正奖励后，第二次2000轮近距离
抬腿短训仍失败。已证实一个奖励漏洞，但不能把它当成全部根因，也不能假定再跑久一点即可解决。
用户要求先分析汇报，再由用户决定是否开启下一次训练。不要自动续训或启动AMD作业。

## 2. 哪份代码才是当前版本

| 位置 | 内容与状态 |
|---|---|
| 本地 `/home/xu/workspace/Leg-Manip` | 当前维护源码及交接文档；独立Git目录尚无commit/remote |
| 5090 `/home/ubuntu/mycode/Leg-Manip` | 当前运行源码；交接前与2000轮冻结清单96文件逐项匹配 |
| 5090 `/home/ubuntu/mycode/QLM-Bench-LegManip` | 用户用于推送的团队仓库克隆；干净，HEAD为6885590 |
| GitHub `JalenLoong/QLM-Bench` / `Leg-Manip` | 当前仍为`6885590c872f2db483615dfdac969bdbe9cd038d`，不是最新修复版 |
| 团队仓库 `baselines/leg_manip/` | 独立baseline子项目；尚未完成QLM任务/数据/评估API适配 |

GitHub分支由 `migration/mujoco-foundation` 建立，6885590仅新增142文件，未修改团队原有1248文件。
当前工作区相对该分支的运行文件差异为：

- 修改：`src/leg_manip/tasks/track/mdp/rewards.py`、`tasks/track/env_cfg.py`、`tasks/__init__.py`（后两项同在src/leg_manip下）。
- 新增：`src/leg_manip/tasks/track/lift.py`、`src/leg_manip/eval/lift.py`。
- 新增测试：`tests/test_lift_rewards.py`、`tests/test_lift_profile.py`；README也更新。
- 本次AGENTS/HANDOFF和训练/部署/审查文档也需后续纳入交接；并未推送到GitHub。

**不要把独立项目根目录覆盖到QLM-Bench根目录。** 后续同步仅在 `baselines/leg_manip/` 内进行，
先检查diff，再普通commit/push；不使用force、不清理团队其他文件。PR/merge状态本轮未核验。

源码交接包：`outputs/handoff-20261027/Leg-Manip-handoff-20261027.tar.gz`。
服务器副本：`/home/ubuntu/mycode/deploy-5090/handoff-20261027/Leg-Manip-handoff-20261027.tar.gz`。
包内根目录为`Leg-Manip/`，附`HANDOFF_MANIFEST.json`逐文件SHA；包外有SHA256SUMS。
包内普通文件权限归一为0644，原可执行文件为0755；不修改原工作区文件权限。
不包含Git历史、虚拟环境、训练日志、数据集、权重、CAD及outputs。原始证据另按第5节取得。

## 3. 已有环境和运行边界

- SSH：`ubuntu@<5090服务器IP>`；16vCPU、约94GiB内存、RTX5090 32GiB。
- Python3.12；torch2.9.0、mjlab1.6.0、mujoco/mujoco-warp3.11.0、warp-lang1.18.0、
  rsl-rl-lib5.4.2、wandb0.31.0、huggingface-hub2.3.0；复用项目`.venv`。
- 驱动580.178.04-open。`/home/check_resolv.sh`中的shutdown已按用户要求注释，
  备份为`/home/check_resolv.sh.bak.20261026T042636Z`；不要执行该脚本进行验收。
- 现有环境使用 `uv run --no-sync`；依赖安装/升级先讲清方案并获得用户同意。
- SSH复用socket曾为`/tmp/legmanip-train-ssh.Xtu5SQ/control`，交接时已关闭旧连接。
  接手者使用正常SSH重新登录；密码和token不在交接材料中。不要复用历史PID发信号。
- NVIDIA负责所有本项目仿真、采集、PPO及闭环；AMD仅负责离线DP3。
  AMD尚未实测；保留既有ROCm torch，在激活环境中 `uv pip install -e .`，不装sim extra，
  运行用 `uv run --active --no-sync`。当前训练器单卡单作业，没有DDP入口。

## 4. 两轮真实训练结果

| 轮次 | 任务 | 步数 | 耗时 | 行为结果 |
|---|---|---:|---|---|
| 30000轮，seed0 | 全范围Track | 2,949,120,000 | 训练4h14m12s；全流程4h15m52s | 按钮1/100，洗碗机0/100；均无提前终止 |
| 2000轮，seed0 | 近距离Lift | 196,608,000 | 训练16m15s；全流程17m15s | 3个评估seed×2前腿全部0%合格 |

30000轮末轮训练日志：位置误差指标0.476606m、方向误差0.274279rad、回报51.3359、
回合长度988.23步。它们是训练日志统计，不是独立跟踪RMSE。

2000轮近距离验收结果（每组64环境；不是三次独立训练）：

| 评估seed | 前腿 | 合格率 | 位置误差cm | 高度误差cm | 操作脚接地 | 提前终止率 |
|---|---|---:|---:|---:|---:|---:|
| 1000 | FL | 0.00% | 13.20 | 12.58 | 100.0% | 0.00% |
| 1000 | FR | 0.00% | 13.80 | 12.71 | 100.0% | 0.00% |
| 1001 | FL | 0.00% | 13.13 | 12.46 | 100.0% | 0.00% |
| 1001 | FR | 0.00% | 13.72 | 12.63 | 100.0% | 1.56% |
| 1002 | FL | 0.00% | 12.90 | 12.21 | 100.0% | 0.00% |
| 1002 | FR | 0.00% | 13.33 | 12.33 | 100.0% | 0.00% |

验收门槛未改：每侧≥90%合格且≤5%提前终止；每个合格环境末2秒均值需3D误差≤5cm、
z误差≤3cm、操作脚接地≤10%。提前终止计为失败；误差和接地均值只统计存活原回合。
`pipeline.exit=0`表示执行/上传完整；`gate-summary.json.passed=false`表示技能不合格。

## 5. 权重、云端记录和证据

W&B账号`dengxu1207`，entity`junlinlong-the-university-of-sydney`，项目`WAM-Policy`。
HF账号`Ethan-Xu-Deng`，模型仓库`Ethan-Xu-Deng/legmanip-weights`，**用户明确选择公开，保持公开**。
数据集仓库另行配置；没有已合格的正式示范可供AMD训练。

| 记录 | 30000轮 | 2000轮 |
|---|---|---|
| run名 | `leg-manip-controller-go2-seed0-20261027-155013` | `leg-manip-controller-go2-seed0-20261027-225007` |
| W&B | [sdtnyowv](https://forge.coreweave.com/wandb/junlinlong-the-university-of-sydney/WAM-Policy/runs/sdtnyowv) | [kmey8ymz](https://forge.coreweave.com/wandb/junlinlong-the-university-of-sydney/WAM-Policy/runs/kmey8ymz) |
| 最终权重 | model_29999.pt | model_1999.pt |
| HF结果commit | `785df10affa6c23eabf109a0e559cefa6ada0002` | `47bfc5d5330b2a41ccaafc32ebaa642caee7b544` |

- [30000轮HF目录](https://huggingface.co/Ethan-Xu-Deng/legmanip-weights/tree/785df10affa6c23eabf109a0e559cefa6ada0002/controller/leg-manip-controller-go2-seed0-20261027-155013)
- [2000轮HF目录](https://huggingface.co/Ethan-Xu-Deng/legmanip-weights/tree/47bfc5d5330b2a41ccaafc32ebaa642caee7b544/controller/leg-manip-controller-go2-seed0-20261027-225007)
- 30000轮权重SHA：`391bb5e746dba1639b3d5bbc8235b3f4dd62f8c2b68c3f4074d2ef6dde21592e`。
- 2000轮权重SHA：`2d68d7df5f80937272294edcc3d3c6b925c0b57e2bc60f9e8d813d8712c883d7`。
- 两个checkpoint均101个张量有限、观测契约version2，服务器/HF SHA一致。

服务器每轮目录均为 `/home/ubuntu/mycode/Leg-Manip/logs/<run名>/`：
`source/`、`source-manifest.json`、`source.tar.gz`冻结代码；`run.sh`与`finalize.py`记录启动及上传；
`run.json`记录环境/参数；`ppo/`保存权重、配置和upload-status；`completion-verification.json`
保存最终校验；`expert_eval/`或`lift_eval/`保存行为结果。HF对应目录的`provenance/`与`results/`
也保存代码快照/结果。不要修改这些历史文件。

本地证据（源码交接包不含这些目录）：

- `outputs/leg-manip-controller-go2-seed0-20261027-155013/`、`outputs/leg-manip-controller-go2-seed0-20261027-225007/`：最终JSON、摘要、校验过的证据压缩包。
- `outputs/controller-diagnosis-20261027/`：旧权重9组只推理诊断、运动学可达性、奖励反例。
- `outputs/reward-fix-20261027/`：修复前3文件副本、7文件清单、短训方案、126项测试和GPU验收证据。
- `outputs/lift-launch/`：2000轮启动脚本/归档逻辑及启动证明。
- `outputs/deploy-5090/`：早期工程验收，不能当作收敛或真实成功证据。

服务器相应额外证据位于 `/home/ubuntu/mycode/deploy-5090/`。

## 6. 已查明什么，尚不能断言什么

旧版free_gait排除操作腿后只检查另外三脚有1或2脚接地，操作前脚仍着地、抬后腿也得满2分。
只推理诊断证实了这种策略；操作前脚约99.7%–99.9%时间接地。Oracle状态输入没有明显改善，
原生MuJoCo静态IK证明8cm位置抬升可达；后者不是动态平衡或完整姿态可达证明。

已实施修复：按目标高度门控支持奖励和接地代价，支持奖励2→0.3，接地代价-0.5，
保留Gaussian高度跟踪但std0.5→1.0，并新增Lift阶段。旧权重在新验收器FL/FR均0/64，
正确被拒绝。126项回归与独立审查通过；随后新短训仍0%合格。

因此，“奖励漏洞是唯一原因”“修完已学会”“仅需加轮数”都没有证据。
不要将实验适配参数冒充论文未公开的确切超参数。不要把新短训13cm与旧全范围47.7cm
直接比较为同分布改进。后续应进一步区分奖励/探索、观测与动作映射、接触几何、
姿态约束及优化问题；这些是待检验方向，不是已确认根因。

## 7. 接手后的安全起点

1. 读AGENTS/HANDOFF/TRAINING_RUN，确认用户本轮授权范围。当前是交接，不是新训练授权。
2. 用清单核对当前代码和冻结实验身份，检查GPU/进程，避免复用旧run或已过期SSH socket。
3. 必要时运行CPU回归或已有权重的短时评估；先记录假设和判据，不动历史权重。
4. 将下一步证据和方案汇报用户；新训练/续训、长期GPU作业、环境改动均先获得同意。
5. 合格控制器与成功示范出现前，不启动正式AMD DP3；模型需回5090做闭环评估。

常用检查（在项目目录，沿用现有环境）：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CUDA_VISIBLE_DEVICES='' uv run --no-sync pytest -q
uv run --no-sync ruff check src tests scripts
uv run --no-sync ruff format --check src tests scripts
uv run --no-sync python -m leg_manip.eval.lift --checkpoint <已有权重.pt> --seed 1000 --out <新结果.json>
```

Lift验收退出0为通过、2为行为未达标；其他错误需查看日志，不能改阈值使其通过。
`list-envs`会打印任务并以任务数作为退出码，非零本身不等于环境初始化失败。

本次只完成交接材料和源码打包；不再启动计算任务，不操作团队仓库的提交/PR/合并。
