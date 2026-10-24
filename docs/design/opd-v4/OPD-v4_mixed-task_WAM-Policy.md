# OPD-v4_mixed-task_WAM-Policy

当前修订：2026-10-24，OPD-005。原用户稿已通读，保留context-equal与episode-level fairness的目标；
按最新NFE决定将正式student改为1/2。旧2/4仅作历史参考。
[Method](OPD-v4_Streaming-OPD_method_scheme.md)、
[implementation状态](OPD-v4_Streaming-OPD_implementation_plan.md)、
[只读差异报告](../../current/opd-v4-documentation-sync.md)共同区分设计与已实现行为。

用户报告：25/50→旧2/4时，任务成功率和未来video prediction质量没有明显下降；
25/50→1/2时两者明显下降。这是选择更有挑战的正式student预算的定性动机，
不新增具体成功率差值或video metric。1/2不是待选ablation，也不改变FM/Euler参数化。

**文档类型：** Existing Implementation — Training Configuration & Objective Alignment

**目标分支：** `opd/v4_Streaming-OPD_on_WAM-Policy`

**实施状态：** OPD-005已落实1/2 NFE、400S/1200F、training profile与global episode scheduler；本地验收和AMD/正式训练证据分别报告。

**适用对象：** Adaptation v2 Quadrupedal WAM-Policy，十任务 Streaming OPD-v4

---

## 1. 本次调整的范围

目前，WAM-Policy 上的 OPD-v4 已经完成主体实现。本文件不是重新实现 OPD-v4 的计划，也不要求重新设计其训练架构。

本次需要对齐以下三个决策：

1. **Training Budget：** 将 Stage 2 正式训练预算确定为 400 次 student optimizer updates。
2. **Per-Task Training Horizon：** 采用已经根据 demonstrations 和 high-NFE teacher 闭环评测确定的十任务 rollout 时间上限。
3. **Mixed-Task Sampling & Loss Reduction：** 采用 episode-level fair task sampling，但不强制不同 task 的 context 数量或累计 loss 系数相等；每个有效 context 的 DMD loss 等权。

本次不改变 OPD-v4 的基础算法：

- Frozen teacher / trainable student / trainable fake-score 三模型；
- Student State 1 NFE / Action 2 NFE；
- Native FM velocity parameterization 与 Euler sampling；
- Conditional DMD 和 fake-score FM loss；
- 完整当前 chunk 内的 1/2-step sampling-chain gradient；
- State→Action conditioning 和既定 detach 边界；
- 8 条 environment streams；
- 每条 stream 每轮 3 个真实 contexts；
- 每轮 3 次 fake-score updates → 1 次 student update；
- 真实 feedback、episode history 和 KV cache 的原有合同。

已经实现且符合上述要求的模块无需重新开发。

---

## 2. Training Budget：400 Student Updates

### 2.1 正式训练预算

本次 All-Task Streaming OPD-v4 使用以下配置：

| 参数 | 数值 |
|---|---:|
| AMD GPU | 8 × MI355X |
| Environment streams | 8 |
| Contexts / stream / round | 3 |
| Global contexts / round | 24 |
| **Student optimizer updates** | **400** |
| Fake-score updates / student update | 3 |
| **Total fake-score updates** | **1,200** |
| **Total environment contexts** | **9,600** |
| Three-chunk clip instances | 3,200 |
| Student sampling | State 1 / Action 2 NFE |

每个训练 round 继续执行：

\[
\boxed{
24\text{ real contexts}
\rightarrow
3\text{ fake-score updates}
\rightarrow
1\text{ student update}
}
\]

总训练预算：

\[
\boxed{
400S+1200F+9600\text{ environment contexts}
}
\]

其中，9,600 contexts 是成功提交的训练 rounds 对应的真实 decision-context 实例数，不是完整 episodes 数量，也不包括 fake-score/student learner 在保存的 contexts 上重新采样产生的模型 samples。

### 2.2 预算约束

400 次 student updates 是本次实验暂定的正式预算。

不因为 task context share 不均衡而自动：

- 延长 student update 次数；
- 额外采集某个 task；
- 重新执行已完成的 episodes；
- 重复利用旧 contexts 补足任务配额。

训练到第 400 次成功 student update 后停止新 rollout，不要求所有正在运行的 episodes 都达到自然 terminal。

建议保留第 200 和 400 次 student update 的 checkpoint，最终使用冻结 checkpoint 进行标准闭环评测。

如果现有实现仍固定为 200 次更新，需要调整相应的训练预算、停止条件和 checkpoint 配置，而不是重写 learner。

---

## 3. Per-Task Training Horizon

### 3.1 确定的时间上限

根据已发布的 1,000 条 QLM-Bench demonstrations（每任务 100 条），以及 25/50-NFE Adaptation v2 teacher 在 300 次闭环 evaluation 中的成功轨迹时长，采用以下训练上限：

| Task | Demonstration 平均时长 | Teacher 最长成功时长 | **Training Horizon** | Max Joint Chunks |
|---|---:|---:|---:|---:|
| Push Box | 8.91 s | 9.22 s | **19.2 s** | 60 |
| Press Button | 13.38 s | 16.78 s | **24 s** | 75 |
| Lift Basket | 15.04 s | 17.76 s | **24 s** | 75 |
| Kick Ball to Goal | 15.39 s | 22.78 s | **24 s** | 75 |
| Sweep Block to Zone | 35.93 s | 无成功 | **40 s** | 125 |
| Close Fridge Door | 26.98 s | 30.90 s | **40 s** | 125 |
| Close Oven Door | 15.71 s | 17.96 s | **32 s** | 100 |
| Turn Valve | 12.77 s | 31.12 s | **32 s** | 100 |
| Pull Open Drawer | 25.97 s | 39.38 s | **40 s** | 125 |
| Open Room Door | 22.75 s | 19.36 s | **40 s** | 125 |

每个 joint chunk 对应名义上 0.32 秒 simulation time。

相对于 QLM-Bench 标准评测 horizon，本次只缩短三个任务：

- Push Box：24 → 19.2 秒；
- Close Oven Door：60 → 32 秒；
- Open Room Door：60 → 40 秒。

其他任务保留原有上限。

### 3.2 Training Horizon 的意义

这里设置 rollout 上限，是为了避免低 NFE student 在长时间无法完成任务时持续占用过多训练 contexts。

它不是一个 success predictor，也不代表超过该时长的所有 contexts 都没有监督价值。

特别是 Sweep Block to Zone：

- Demonstration 平均时长为 35.93 秒；
- High-NFE teacher 在 30 次评测中未能成功；
- 原训练时间上限为 40 秒。

因此本次仍然保留 40 秒，不因为 teacher 的低成功率而额外缩短。

### 3.3 Train/Eval 分离

Training Horizon 只作用于 Streaming OPD 的环境数据采集。

正式 evaluation 继续使用原始 QLM-Bench standard horizon。

需要区分：

- `task_success`；
- `robot_fall`；
- `training_timeout`；
- 训练预算结束造成的未完成 episode。

不得把 training timeout 计作 task success，也不得把预算停止伪装成自然 timeout。

即使 training horizon 对齐整数个 joint chunks，success/fall 仍可能在 chunk 内部发生。此时应沿用既有 partial execution 与有效 context 处理规则，不补造未来 observations。

本次不新增基于 progress、success rate 或动作重复程度的动态 Stall Detection。

---

## 4. Mixed-Task OPD 为什么不需要强制 Task-Equal Context Weighting

### 4.1 首先明确 OPD 的真实目标

本次 OPD-v4 的目的不是通过 RL reward 提升总体 success rate，也不是专门改善某个弱势任务。

我们的目标是：

**让使用 State 1 NFE / Action 2 NFE 的 student，尽可能保留使用 State 25 NFE / Action 50 NFE 的原始 teacher 的能力。**

两者来自相同的 Adaptation v2 SFT checkpoint。

OPD 主要希望修正：

- Low-NFE sampling 造成的生成分布偏移；
- Student 自身闭环交互引起的 environment-history distribution shift；
- Student-generated state plan 对 action generation 造成的 conditioning mismatch。

在这个目标下，训练样本的自然单位是：

**Student 实际访问的一个 decision context，以及该 context 下的 state/action DMD supervision。**

不是完整 episode 的单个监督结果。

### 4.2 Episode 长度不同，意味着监督机会自然不同

设 task \(t\) 的 episode 长度为 \(L_{t,i}\)，其中 \(i\) 表示该 task 的第 \(i\) 条 episode。

该 episode 会产生 \(L_{t,i}\) 个 decision contexts。

如果所有 contexts 等权，那么：

\[
\mathcal L_{\mathrm{OPD}}
=
\frac{1}{N}
\sum_t\sum_i\sum_{k=1}^{L_{t,i}}
\ell_{t,i,k},
\]

其中：

\[
N=\sum_t\sum_i L_{t,i}.
\]

将其按 task 分组：

\[
\boxed{
\mathcal L_{\mathrm{OPD}}
=
\sum_t
\underbrace{\frac{N_t}{N}}_{p_t}
\bar{\ell}_t
}
\]

其中：

- \(N_t\)：task \(t\) 实际贡献的 contexts；
- \(p_t=N_t/N\)：该 task 的 context 份额；
- \(\bar{\ell}_t\)：该 task 的平均 context-level loss。

因此，不同 task 的累计训练系数自然由实际 context 数量决定。

**这不是无意引入的 task loss imbalance，而是 context-equal training objective 的直接结果。**

### 4.3 为什么可以接受长任务获得更多累计监督

长任务通常需要经历更多连续决策，才能完成从初始状态到目标状态的交互。

在 WAM 中，每个 chunk 都包含：

1. 基于当前真实 history 生成未来 state plan；
2. 基于该 plan 生成 action；
3. 执行动作；
4. 获取真实环境 feedback；
5. 将实测结果纳入下一次决策历史。

因此，长 episode 天然包含更多需要进行条件生成和决策的 contexts。

此外，随着交互推进，student 早期生成的 action 可能使环境进入 demonstrations 中较少出现的状态，后续 student 就需要在这些真实 histories 上继续生成 state/action。

这正是 Streaming OPD 希望覆盖的分布偏移。

对于一个 20-chunk episode 和一个 100-chunk episode，如果我们认为每个真实 decision context 都值得接受同等的局部蒸馏监督，那么后者自然贡献约五倍的监督项。

**我们不需要额外通过 task reweighting，把这种长度带来的监督数量差异人为消除。**

但这并不意味着：

- 长任务一定比短任务困难；
- Exposure bias 一定随 episode 长度单调增长；
- 长 episode 的后期 contexts 一定更有价值；
- 更多 contexts 一定带来更高的 task success rate。

它仅说明：在本次 OPD 目标下，**允许真实访问到的每个 context 等权，是合理且更直接的训练定义。**

### 4.4 为什么不选择 Task-Equal Loss

之前的 `task_balance_v1` 希望每个 task 长期获得约 10% 的 context/loss 系数份额。

这实际上对应另一个目标：

\[
\mathcal L_{\mathrm{task\text{-}equal}}
=
\frac{1}{10}
\sum_{t=1}^{10}\bar{\ell}_t.
\]

它与 context-equal objective 不同。

Task-equal loss 会降低自然产生较多 contexts 的长任务的单个 context 系数，提高短任务的单个 context 系数。

这种设计可以用于明确追求 task-macro optimization 的实验，但不是我们当前 low-NFE teacher-ability retention 实验的必要条件。

因此，本次决定：

**不引入 task-frequency-dependent loss weighting，也不要求每个 task 最终恰好贡献 10% contexts。**

---

## 5. Task Sampling：Episode-Level Fairness

虽然不强制 context 数相同，我们仍希望所有 tasks 获得合理的环境启动机会。

因此采用此前确认的：

**Global Episode-Level Round-Robin**

其核心规则是：

- 任务选择发生在真实 episode reset 边界；
- 优先选择累计 confirmed episode starts 较少的 task；
- 相同计数时使用确定性、可恢复的 round-robin 顺序；
- 同 task 内使用原有 train reset shuffle deck；
- 同一 task 同时运行或预留的 episodes 默认不超过 2；
- 不为了 task balance 截断正在正常推进的 episode。

Episode-level fairness 不意味着 context-level fairness。

在足够长的统计窗口下，如果各任务的 episode 启动次数接近，并且长度分布相对稳定：

\[
p_t
\approx
\frac{\mathbb E[L_t]}{\sum_u\mathbb E[L_u]}.
\]

因此，长任务可以获得更大的 context share。这是预期行为，不是错误。

本次不再使用：

- Context-deficit balancing；
- Predicted remaining context quota；
- Per-task 10% context quota；
- Inverse-frequency task weighting；
- `[0.5,2.0]` task loss multiplier；
- Frequency-based loss normalization。

如果这些机制已经存在于当前实现中，应核对它们是否仍然生效，并明确关闭与当前设计冲突的部分；不必为了删除旧功能而重构整个训练系统。

---

## 6. Context-Equal Student / Fake Loss

不再使用额外的 task-dependent 权重 \(w_t\)。

### Student DMD

每轮：

\[
\boxed{
\mathcal L_S^r
=
\frac{1}{24}
\sum_{e=1}^{8}
\sum_{j=1}^{3}
\left(
\mathcal L_{\mathrm{DMD}}^{Z,e,j}
+
\mathcal L_{\mathrm{DMD}}^{A,e,j}
\right)
}
\]

### Fake-Score FM

每次 fake-score update：

\[
\boxed{
\mathcal L_F^{r,q}
=
\frac{1}{24}
\sum_{e=1}^{8}
\sum_{j=1}^{3}
\left(
\mathcal L_{\mathrm{FM}}^{Z,e,j,q}
+
\mathcal L_{\mathrm{FM}}^{A,e,j,q}
\right)
}
\]

其中 \(q=1,\ldots,3\)。

继续保持：

- 每 rank 三个 contexts 进行梯度累积；
- 本地 loss 除以 3；
- DDP 对八个 ranks 的梯度进行平均；
- 不再额外按 task 求平均；
- 不根据 episode 长度除以 \(L_{t,i}\)；
- DMD 内部 normalization、state/action loss scaling 以及梯度边界不变。

需要注意，这种 context equality 指的是每个有效 context 的**外层 loss 系数相同**，不意味着每个 context 对最终参数更新产生完全相同的梯度幅度。

---

## 7. 400-Update Mixed-Task Training 的统计与评估

本次不再以 task context share 是否接近 10% 作为训练验收条件。

只需记录：

| Metric | 用途 |
|---|---|
| Per-task episode starts | 验证 episode-level task sampling |
| Per-task completed episodes | 记录实际完成的环境轨迹 |
| Per-task raw contexts | 确认自然训练份额 |
| Per-task context share | 分析 episode 长度造成的训练数据分布 |
| Per-task episode length | 观察 rollout 时长分布 |
| Per-task training timeout | 验证训练 horizon |
| Per-task DMD / fake FM loss | 诊断蒸馏过程 |
| Student / fake update counts | 验证训练预算 |

上述统计只用于透明报告实际训练过程，不自动驱动新的 task weighting、训练预算延长或 horizon 改动。

### 最终评估

对比：

1. High-NFE teacher：State 25 / Action 50；
2. Initialized low-NFE student：State 1 / Action 2；
3. OPD-v4 distilled student：State 1 / Action 2。

使用相同的 held-out evaluation cases、原始 benchmark horizon 和成功判据。

本次重点关注：

**Streaming OPD 是否缩小 low-NFE student 与 high-NFE teacher 在闭环任务能力上的差距，同时尽量避免已经具备的能力退化。**

不要求 OPD student 超越 teacher，也不把某个 task 的成功率提升当作本次训练算法的必达目标。

---

## 8. 当前实现与恢复

新配置使用State1/Action2、400S/1200F、24contexts/round、3F→1S；actor、learner和export
共用由原scheduler生成的manifest。Student/fake外层context系数仍为本地1/3与DDP mean8。

每100次成功student update及安全/最终边界保存完整恢复checkpoint，保护S200/S400并保留latest2。
QLM独立training profile绑定原train800 pool hash及本表horizons，不回写旧pool。
Global confirmed-start round-robin由同机SQLite事务维护；task内原shuffle deck、确认/预留幂等，
同task运行＋预留最多2。逻辑snapshot与learner同round保存；恢复到新segment，取消旧active/pending，
保留确认计数和deck进度，明确continuity_break。不恢复物理轨迹。

[OPD-005本地实施报告](../../current/opd-v4-implementation-005.md)记录实际结果；
[OPD-004历史审查](../../current/opd-v4-documentation-sync.md)保留当时未实现状态，不作为当前状态。

---

## 9. 最终决策摘要

本次 mixed-task Streaming OPD-v4 采用：

**400 Student Updates + Fixed Per-Task Training Horizon + Episode-Level Fair Sampling + Context-Equal DMD Supervision。**

核心理由：

> Streaming OPD 的训练目标是让 low-NFE student 尽可能保留 high-NFE teacher 在实际闭环决策中的能力。因此，我们选择真实 decision context 作为等权监督单位，而不人为要求不同 task 的累计 context 数量相等。不同 episode 长度造成的累计训练系数差异是这一目标的自然结果。

本文只调整正式训练预算、rollout horizon 和 mixed-task 的采样与 loss reduction 原则，不改变已经实现的 OPD-v4 核心算法。

**当前状态：OPD-005代码已适配；AMD真实三角色/八流/400S正式训练未运行。**
