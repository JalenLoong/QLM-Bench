# WAM-Policy OPD-v4：两阶段 On-Policy Distillation 方案

当前设计与实现修订：2026-10-24，OPD-005。已实现 native1/2、400S/1200F、
独立training profile和全局episode调度；本地证据见OPD-005交付，目标AMD与正式训练未运行。
见 [implementation plan](OPD-v4_Streaming-OPD_implementation_plan.md) 和
[mixed-task 合同](OPD-v4_mixed-task_WAM-Policy.md)。旧 2/4、200-update 实现证据保留其历史范围。

OPD-v4 统一采用：

\[
\boxed{
\text{Stage 1: Off-Policy Student Initialization}
\;\longrightarrow\;
\text{Stage 2: On-Policy Streaming Distribution Matching Distillation}
}
\]

**本版保留 quadrupedal-adapted LingBot-VA 的 shared DiT、FM velocity parameterization 和原生 Euler-style sampler。** Student 正式使用 **State 1 NFE、Action 2 NFE**，不经过 ODE Endpoint Bootstrap、endpoint 参数化转换、denoise–re-noise student sampler 或独立 Input Calibration。

用户报告的闭环实验定性结论是：从 25/50 降至旧 2/4 时，任务成功率和未来 video prediction
质量没有明显下降；降至 1/2 时，两者均明显下降。因此选择 1/2 作为正式目标，检验 Streaming
OPD 能否恢复低采样预算损失的行为能力与 video prediction 质量。这里不添加未给出的成功率
差值或 video quality metric，也不把“恢复能力”写成已经验证的结论。

两阶段的职责是：

> **Stage 1 提供可用的初始行为，必要时通过 teacher-generated dataset 做初步能力迁移；Stage 2 在 student 自己访问的环境 histories、自己生成的 state plans 和真实使用的低 NFE 采样路径上进行分布匹配。**

以下以当前 **single-teacher OPD** 为主体。Teacher 记为 \(T\)，当前对应共同的 quadrupedal SFT base。将来使用 RL task experts 时，可以扩展 teacher 数据来源与监督选择，但不在本版加入 M-OPD、teacher router 或 RL 训练设计。

---

## 一、统一配置与模型角色

### 1.1 已确定的训练配置

| 项目 | OPD-v4 的定义 |
|---|---|
| Student backbone | Quadrupedal-adapted LingBot-VA shared DiT |
| Student 参数化 | 保留原生 FM velocity 输出形式 |
| Student sampler | 原生 Euler-style ODE sampler，完整去噪到 \(\sigma=0\) |
| Student State / Action NFE | **1 / 2** |
| High-NFE teacher 基线推理 | **25 / 50**；DMD score query 不运行这条完整轨迹 |
| Student 权重来源 | 共同的 quadrupedal SFT checkpoint |
| Teacher | 当前 single-teacher 使用冻结的共同 SFT base |
| Student 可训练部分 | Shared DiT 内的 **LoRA，rank 256** |
| Fake-score 可训练部分 | 独立的 shared-DiT LoRA，rank 256 |
| LoRA 设置 | \(\alpha=256\)、dropout \(=0\)、bias 不训练 |
| 模态 project-in/out | 冻结 |
| VAE、text encoder、normalizer、底层 controller | 冻结 |
| 每条 stream 的 rollout clip | **3 个 joint chunks** |
| Clip 内参数 | 固定同一个 student 版本 |
| 每个 chunk 的环境反馈 | 执行后立即接收并提交 |
| Per-GPU batch size | **1 个 clip** |
| GPU / Global batch size | **8 × MI355X / 8 个 clips** |
| 每轮 supervised contexts | 完整 round 下为 **24 个** |
| Fake-score / student 更新比 | **3:1** |
| Stage 2 训练预算 | **400 次成功 student optimizer updates，1,200 次 fake updates，9,600 contexts** |
| Task sampling / loss | Global episode-level round-robin / context-equal supervision |
| 梯度范围 | 不跨环境历史反传；保留当前 chunk 内完整的 1/2-step 生成链梯度 |

这里的 **projection 冻结**指 state、action，以及已有 proprioception 的模态输入输出 projection。DiT 内 Q/K/V/O 和 FFN 的原始权重同样冻结，但相应 LoRA 参数可以更新。

LoRA 覆盖范围沿用此前跑通的 self-attention Q/K/V/O 与 FFN 两个主要 Linear projections，不继承 OPD v3 的 dual-timestep 模块。此前配置中确实存在这套 rank-256 LoRA 范围；OPD-v4 复用的是参数适配方式，而不是旧 FFM 训练目标。[参考：native LingBot-VA joint-forward 实现](https://github.com/Robbyant/lingbot-va/blob/main/wan_va/modules/model.py#L701-L798)。

### 1.2 三种模型的职责

| 模型 | 职责 | 是否更新 |
|---|---|---|
| **Teacher \(T\)** | 提供目标行为的 denoising/score guidance；需要时生成初始化数据 | 冻结 |
| **Student \(S_\theta\)** | 使用固定 1/2 NFE 生成 state/action，最终用于部署 | 更新 LoRA |
| **Fake-score \(F_\phi\)** | 估计当前 student 输出的条件分布，构造 DMD correction | 更新独立 LoRA |

Fake-score 不是 reward model，也不是另一个 task expert。它只服务于训练，最终部署时不需要运行。

### 1.3 Mixed-task 采集与硬件边界

十任务都参与训练，沿用原 800 个 train reset candidates，每 task 80 个，保留原场景、
初始状态、seed 和难度分布。全局在真实 terminal/reset 边界优先选择 confirmed episode
starts 较少的 task；平局采用可恢复的 round-robin。同 task 使用原 shuffle deck，运行中与
预留 episodes 默认最多 2 个。不按 context 欠额调度、不提前 reset 健康 episode。

固定 training horizons 见 [十任务表](OPD-v4_mixed-task_WAM-Policy.md#3-per-task-training-horizon)。
训练采集上限与标准 evaluation horizon 分离；不启用 dynamic stall detection。Success、fall、
training timeout 和总预算停止分开记录，terminal partial execution 不补造未来 observations。

全部 8 条 streams 的 RAMBO controller、Native MuJoCo physics 与 OSMesa/llvmpipe rendering
均为 CPU only，包括 reset 和 observation collection。AMD GPU 负责模型、采样、score、loss
及优化；正常 CPU↔GPU 数据传输保留。不得启用 MJWarp、GPU EGL 或其他 GPU simulation/rendering。

---

## 二、保留原生 FM 模型与采样过程

### 2.1 统一符号

用 \(r\) 表示 student optimizer-update index，\(k\) 表示环境 decision/chunk index，\(\sigma\) 表示实际 noise level，避免将训练迭代、物理时间与 diffusion time 混在一起。

生成前 context 为：

\[
C_k=(H_k,c),
\]

其中 \(H_k\) 是当时可用的实测 observation、executed-action history，以及模型 contract 包含时的实测 proprioception；\(c\) 是 instruction。

对 adaptation v2：

\[
X=Z,
\]

即 state flow 预测 video latent。

对已经包含 proprioception prediction 的模型版本：

\[
X=(Z,P).
\]

**本方案不要求为了 OPD 再新增 proprioception 分支。** 使用哪个四足 checkpoint，就保留它已经定义的 state representation。

### 2.2 原生 FM 的监督语义

采用：

\[
Y_\sigma=(1-\sigma)Y_0+\sigma\epsilon,
\qquad
\epsilon\sim\mathcal N(0,I).
\]

FM 的训练 target 为：

\[
v^\star=\epsilon-Y_0.
\]

当前 adaptation 分支确实为 video/action 分别建立 1000 个训练 timesteps 的 schedulers，再从中抽取 noise levels、构造 noisy inputs 和 FM targets。**这 1000 个 timesteps 是监督网格，不是推理调用次数。** [参考：WAM-Policy adaptation/v2-mujoco-sft `flow.py`](https://github.com/JalenLoong/WAM-Policy/blob/adaptation/v2-mujoco-sft/src/wam_policy/training/flow.py)。

### 2.3 Student 的固定预算 sampler

对一个模态，固定：

\[
1=\sigma_0>\sigma_1>\cdots>\sigma_B=0.
\]

从：

\[
Y^{(0)}=\xi
\]

开始，执行：

\[
\boxed{
Y^{(b+1)}
=
Y^{(b)}
+
(\sigma_{b+1}-\sigma_b)
v_\theta\!\left(Y^{(b)},\sigma_b,C\right).
}
\]

这里的 \(v_\theta\) 表示已经按既定配置处理 timestep、模态条件和 CFG 的输出。实际 noise grid、shift 与 CFG 沿用原生接口，不重新设计另一套采样过程。

于是：

\[
X_k^S
=
G_\theta^{X,1}(\xi_X;H_k,c),
\]

\[
\boxed{
A_k^S
=
G_\theta^{A,2}
\left(
\xi_A;H_k,c,\operatorname{sg}(X_k^S)
\right).
}
\]

State 执行一次完整 Euler update，action 执行两次完整 Euler updates；action 的两次调用
读取同一份最终 detached state plan，不在中途重新预测 state。

实际网格由既定 scheduler 生成：state shift=5、action shift=1、sigma_min=0、
extra_one_step=True。当前源码推导的查询 sigmas 分别为 state `[1]`、action `[1,0.5]`，
均完整到零，model timesteps 分别为 `[1000]`、`[1000,500]`。不能从旧网格删步来替代 scheduler。
辅助 timestep=0 plan/history cache forwards 单独计数，不计入 1/2 denoising NFE。

当前 v2 inference 实现正是分别创建指定步数的 scheduler、执行迭代更新，先完成 video sampling，再完成 action sampling；执行反馈到达后，会清除临时预测缓存，提交实测状态与已执行动作。[参考：WAM-Policy `inference.py`](https://github.com/JalenLoong/WAM-Policy/blob/adaptation/v2-mujoco-sft/src/wam_policy/inference.py)。

**原生 sampler 输出最终去噪结果，不等于网络被改造成了直接 endpoint predictor。** OPD-v4 保留的是 velocity-form 网络与 Euler 采样链。

---

## 三、Stage 1：Off-Policy Student Initialization

### 3.1 阶段目标

Stage 1 的目标是：

> **得到来源明确、在原生 1/2-step sampler 下通过有界启动检查、可进入持续交互的 student。**

本阶段不要求学习 teacher 的完整 noise-to-endpoint transport，也不要求生成 teacher ODE 中间状态数据。

“Off-Policy”表示其能力基础来自已经存在的 SFT checkpoint，以及需要时使用的离线 demonstrations，而不是通过当前 student 的持续环境交互收集数据。

### 3.2 当前 single-teacher 设置：直接继承 SFT checkpoint

当前 teacher 就是共同的 quadrupedal SFT base，因此：

\[
\theta_{\mathrm{init}}
\leftarrow
\theta_{\mathrm{quad\text{-}SFT}}.
\]

在其 shared DiT 上添加初始有效增量为零的 rank-256 LoRA，保持原始行为不变。

**当前 single-teacher 主线仍采用权重继承，Stage 1 optimizer updates=0。** 新 1/2 基线已观察到
能力下降，这正是蒸馏的起点；不要求初始化已恢复 teacher 水平，也不据此自动开启额外 SFT。
实际启动仍需绑定该 checkpoint、1/2 sampler 与有界行为检查，不用旧 2/4 receipt 代替。

这样做时，Stage 1 没有新的 optimizer updates。它仍然明确规定了 student 的来源、模型接口和初始 sampler，避免后续混入 native 双臂 checkpoint、旧 Flow Map adapter 或其他初始化权重。

这里保留此前的证据边界：可用的低 NFE 行为是启动前提，不能仅由“在 1000 个噪声时间点上训练过”推导出来。

### 3.3 需要初步迁移新能力时：teacher-generated dataset 上的 joint SFT

当 teacher 相比共同 SFT base 已经获得额外能力时，可以在 Stage 1 中增加：

\[
T
\xrightarrow{\text{环境执行}}
\mathcal D_T
\xrightarrow{\text{joint FM SFT}}
S_{\mathrm{init}}.
\]

Dataset 的基本记录为：

\[
\mathcal D_T
=
\left\{
H_k^T,\ c,\ A_k^{T,\mathrm{exec}},\
X_{k+1}^{\mathrm{env}}
\right\}.
\]

这里：

**Action 来自 teacher 的实际执行；后续 RGB/proprioception 来自环境反馈。** Teacher 的 imagined state 可以作为诊断记录，但不能替代实际后果，冒充 ground truth。

数据的时间对齐、action normalization、坐标系、有效维度与 history contract 必须沿用四足 SFT 的定义。

这部分是 Stage 1 内可执行的监督微调，不是新增一个阶段；**当前 single-teacher 主线不强制执行它。**

### 3.4 Joint FM SFT 的训练目标

对离线数据中的某一模态 \(Y_0^T\)，构造：

\[
Y_\sigma=(1-\sigma)Y_0^T+\sigma\epsilon.
\]

使用原生 FM 目标：

\[
\mathcal L_{\mathrm{FM}}^Y
=
\mathbb E
\left[
w_Y(\sigma)
\left\|
v_\theta^Y(Y_\sigma,\sigma,C_Y^{\mathrm{data}})
-
(\epsilon-Y_0)
\right\|_{M_Y}^{2}
\right].
\]

其中 \(\|\cdot\|_{M_Y}^{2}\) 表示按原有有效元素与时间位置规则进行归一化的误差，\(w_Y\) 是既定 scheduler 的训练权重。

联合目标为：

\[
\boxed{
\mathcal L_{\mathrm{init}}
=
\mathcal L_{\mathrm{FM}}^Z
+
\lambda_P\mathcal L_{\mathrm{FM}}^P
+
\lambda_A\mathcal L_{\mathrm{FM}}^A.
}
\]

没有 proprioception prediction 时删除 \(P\) 项。

Video/state 与 action 可以采用原生 joint token packing，在同一次 shared-DiT forward 中计算各自预测，再由总 loss 更新同一套 LoRA。两个模态仍保留独立的 noisy inputs、timesteps 与 masks，不要求使用相同的 noise level。

**Stage 1 可选 SFT 继续使用原生训练 noise sampling。** 1/2 约束最终 sampler，不把普通 SFT
的训练网格缩成一个 state、两个 action inference query points，也不回归新的 endpoint 参数化。

### 3.5 Stage 1 不承担的职责

Native joint SFT 中，action conditioning 主要来自 dataset 的 future-state condition，可能包含既定的噪声增强；它不是由当前 student 完整运行 1-step state sampler 后得到的 plan。当前 adaptation 代码也保留了这一 dataset-conditioning 路径。[参考：WAM-Policy `flow.py`](https://github.com/JalenLoong/WAM-Policy/blob/adaptation/v2-mujoco-sft/src/wam_policy/training/flow.py)。

因此，Stage 1 不宣称已经消除了：

\[
H^{\mathrm{data}}\neq H^{S},
\]

\[
X^{\mathrm{data}}\neq X^{S},
\]

以及 dataset forward-noising inputs 与 student sampling inputs 之间的差异。

**这些差异继续存在，但不再为其单独设置 Input Calibration；其对齐职责交给 Stage 2。**

---

## 四、Stage 2：On-Policy Streaming Distribution Matching Distillation

### 4.1 阶段目标

Stage 2 在同一个固定预算 student 上同时处理：

| 层次 | 要改善的分布差异 |
|---|---|
| **Environment-level** | Dataset/teacher histories 与 student 实际执行后访问的 histories 不同 |
| **Denoising-level** | 普通 FM 加噪训练输入与 student 低 NFE 采样链中的实际 inputs 不同 |
| **State→Action conditioning** | Dataset state condition 与 student 自己生成的 state plan 不同 |

核心不是要求 teacher 重现 student 的完整轨迹，而是：

> **在 student 实际遇到的 context 下，使用 student 真正部署的 sampler 生成样本，再让 teacher 指导这些样本的条件分布。**

DMD 可以通过 generator 输出对参数的 Jacobian 传递分布校正梯度；因此这里将原生 Euler 采样链整体作为 generator，不要求先转换成 endpoint model。这是对 DMD 接口的适配，不是照搬 DMD2 的 consistency-style sampler。([DMD2 原文](https://arxiv.org/html/2405.14867v1))

### 4.2 每轮保持一个 student 参数版本

在第 \(r\) 轮开始时，所有 environment streams 使用：

\[
\theta_{\mathrm{actor}}=\theta_r.
\]

在本轮全部 clips 收集完成、全部 student 梯度累积结束之前，不更新 \(\theta_r\)。

每条 stream 保留环境状态、历史、instruction、episode ID 和 decision index。**一次 student update 不触发环境 reset。**

### 4.3 每条 stream 执行三个闭环 joint chunks

对 stream \(e\)，本轮按顺序执行：

\[
H_{e,r,1}
\rightarrow
\text{Chunk 1}
\rightarrow
H_{e,r,2}
\rightarrow
\text{Chunk 2}
\rightarrow
H_{e,r,3}
\rightarrow
\text{Chunk 3}.
\]

每个 joint chunk 都包含：

\[
\text{State prediction}
\rightarrow
\text{Action generation}
\rightarrow
\text{Action execution}
\rightarrow
\text{Real feedback}.
\]

**三个 chunks 内参数固定，但 observation 每个 chunk 都更新。** 这是 closed-loop short-clip collection，不是 open-loop 执行三个 chunks 后才观察一次。

按此前使用的 \(0.32\) 秒/joint chunk，完整 clip 约覆盖 \(0.96\) 秒模拟时间；这个时间只描述环境推进，不包含 learner 计算耗时。

### 4.4 保存生成前 context，提交真实反馈

每次生成前保存：

\[
C^-_{e,r,j}
=
\operatorname{Snapshot}(H_{e,r,j},c_e).
\]

区分模型请求与实际执行：

\[
A^{\mathrm{req}}_{e,r,j}
\quad\text{和}\quad
A^{\mathrm{exec}}_{e,r,j}.
\]

随后：

\[
\boxed{
H_{e,r,j+1}
=
\operatorname{Commit}
\left(
H_{e,r,j},
O_{e,r,j+1}^{\mathrm{obs}},
P_{e,r,j+1}^{\mathrm{obs}},
A_{e,r,j}^{\mathrm{exec}}
\right).
}
\]

未包含 proprioception 输入的模型不提交对应模态。

长期 history 只记录真实发生的 observations 与 executed actions。Teacher correction 不替 student 执行，student predicted state 也不冒充实测结果。

如果 episode 在三个 chunks 之前结束，按正常 terminal/reset 规则继续收集剩余 decision slots，并保留 episode 边界；不能拼接不同 episodes 的 causal history，也不能构造终止后的伪 observations。

---

## 五、Teacher 在 clip 内如何监督

### 5.1 每个 chunk 使用自己的生成前 history

对于第二、第三个 chunk，teacher 读取：

\[
H_{e,r,2},\qquad H_{e,r,3},
\]

也就是 **student 执行此前 chunks 后，真实环境反馈形成的 histories**。

不能让 teacher：

- 沿自己的 imagined trajectory 继续；
- 使用原 demonstrations 中相同时间索引的状态；
- 对三个 chunks 都读取 clip 结束时的最新 history。

前两种会失去 student-history alignment，后一种会泄漏未来信息。

### 5.2 训练时重新进行可微采样

环境采集不保留计算图。之后在保存的每个 \(C^-\) 下，重新执行：

\[
X^S
=
G_{\theta_r}^{X,1}(\xi_X;C^-),
\]

\[
A^S
=
G_{\theta_r}^{A,2}
\left(\xi_A;C^-,\operatorname{sg}(X^S)\right).
\]

这些训练 samples 可以使用新的 noise draws，但必须与 actor 使用相同的 sampler、schedule、CFG、history 和输出语义。

**重新采样的 action 没有在环境中执行，不能将原 rollout 的未来 observation 当作它的真实后果。** 原环境反馈用于构造历史分布，不与新 action 强行配对。

### 5.3 三个模型的 conditioning

State teacher 与 fake-score 使用：

\[
C^X=(H,c).
\]

Action student、teacher 与 fake-score 使用：

\[
\boxed{
C^A=(H,c,\operatorname{sg}(X^S)).
}
\]

Teacher 为 state loss 提供的 clean estimate，不替换 action condition 中的 student plan。

对于 \(X=(Z,P)\) 的模型，state scoring 联合读取该 state representation，再分别计算各模态的 loss reduction；不把 video 与 proprioception 当成完全无关的两个预测任务。

---

## 六、Stage 2 的 DMD loss

### 6.1 Teacher 与 fake-score 的分工

Teacher 估计目标分布，fake-score 估计当前 student 分布。

对 student 输出 \(Y^S\)，随机采样 score-query noise level \(\rho\)，重新加噪：

\[
\widetilde Y_\rho
=
(1-\rho)\operatorname{sg}(Y^S)
+
\rho\epsilon.
\]

在同一 noisy input、noise level 和 conditioning 下计算：

\[
\mu_T
=
D_T^Y(\widetilde Y_\rho,\rho,C),
\]

\[
\mu_F
=
D_\phi^Y(\widetilde Y_\rho,\rho,C).
\]

对采用 noise-minus-clean velocity 的 score model：

\[
\mu
=
\widetilde Y_\rho-\rho v(\widetilde Y_\rho,\rho,C).
\]

这里使用实际 noise coefficient，并通过各自 adapter 转换模型 timestep。Teacher/fake-score 的这种 clean-estimate 转换，**不等于 student 已经改用 endpoint sampler**。

### 6.2 DMD 的 re-noising 不进入部署 sampler

需要明确区分：

| 操作 | 发生在哪里 |
|---|---|
| Euler 多步更新 | Student 的实际 state/action generation |
| 对最终 \(Y^S\) 重新加噪 | DMD 与 fake-score 的训练监督路径 |

所以，OPD-v4 仍有 DMD re-noising，但**没有恢复此前被删除的 denoise–re-noise student sampler**。

随机 \(\rho\) 也不改变固定的 1/2 NFE。Teacher 的 25/50 是高质量基线推理预算；
这里每次 teacher/fake-score query 仍是在给定 noisy sample、rho 和 condition 上的一次 velocity 查询。

### 6.3 Normalized DMD correction

对单个样本、单个模态，设有效 mask 为 \(M\)，有效元素数：

\[
n_M=\sum_iM_i.
\]

定义：

\[
a_Y
=
\max\left(
\frac{\sum_iM_i|Y_i^S-\mu_{T,i}|}{n_M},
\varepsilon
\right),
\]

\[
\boxed{
g_Y
=
\operatorname{sg}
\left(
\frac{\mu_F-\mu_T}{a_Y}
\right).
}
\]

Student surrogate 为：

\[
\boxed{
\mathcal L_{\mathrm{DMD}}^Y
=
\frac{1}{2n_M}
\sum_iM_i
\left[
Y_i^S-\operatorname{sg}(Y_i^S-g_{Y,i})
\right]^2.
}
\]

它向 student 输出传递的梯度为：

\[
\frac{\partial\mathcal L_{\mathrm{DMD}}^Y}{\partial Y_i^S}
=
\frac{M_i}{n_M}g_{Y,i}.
\]

全无效项跳过。Normalization 按样本、按模态计算，不能让无效 action channels 或 video token 数量改变其他模态的尺度。

这沿用现有 OPD v3 中的 `fake_clean - real_clean`、per-sample normalization 与 detached-target 思路。这里明确采用 \(1/2\) 的 surrogate 系数；与已有 loss reduction 衔接时应保持统一尺度。[参考：WAM-Policy OPD v3 `dmd.py`](https://github.com/JalenLoong/WAM-Policy/blob/opd/v3_shared-backbone_AnyFlow/src/opd/dmd.py)。

**该 normalized surrogate 是本方案的实际更新规则，不宣称它等于某个未经重加权的精确 KL 梯度。**

### 6.4 每个 context 与全局 loss

对第 \(e\) 条 stream、第 \(j\) 个 context：

\[
\ell_{e,j}
=
\mathcal L_{\mathrm{DMD}}^{Z,e,j}
+
\lambda_P\mathcal L_{\mathrm{DMD}}^{P,e,j}
+
\lambda_A\mathcal L_{\mathrm{DMD}}^{A,e,j}.
\]

不存在 \(P\) 分支时删除对应项。

完整 global round：

\[
\boxed{
\mathcal L_{\mathrm{student}}
=
\frac18
\sum_{e=1}^{8}
\frac13
\sum_{j=1}^{3}\ell_{e,j}.
}
\]

这是 **8 个 clips、24 个 local contexts** 的平均，不是完整三段新生成视频的 holistic distribution loss。

### 6.5 Context 等权与 task 的累计训练系数

对 task \(t\) 的第 \(i\) 个 episode，令有效 context 数为 \(L_{t,i}\)，则：

\[
\mathcal L_{\mathrm{OPD}}
=\frac1N\sum_t\sum_i\sum_{k=1}^{L_{t,i}}\ell_{t,i,k}
=\sum_t\frac{N_t}{N}\bar\ell_t,
\qquad N=\sum_tN_t.
\]

这是主动选择的 context-equal objective。长 episode 包含更多真实决策与生成、可能更长的
student-induced history shift，因此可以贡献更多监督；不据此声称长任务一定更难或后期
contexts 一定更有价值。Episode 启动机会公平不等于 task loss 宏平均。

Student 和 fake 的每个有效 context 外层系数相同：不使用 task-frequency weighting、
context-deficit 调度、10% context 配额或 episode-length `1/L` normalization。
Context 等权不保证梯度幅度相同；任务统计用于透明诊断，不自动修改预算、权重或 horizon。
不存在的模态按既有零贡献和 DDP 同步规则处理。

---

## 七、Fake-score training 与参数更新顺序

### 7.1 Fake-score 的初始化

Fake-score 使用与四足模型兼容的 FM backbone，从共同 SFT base 初始化，建立独立 rank-256 LoRA。

即使 student 最初也来自同一 checkpoint，fake-score 仍需学习**有限 NFE sampler 的实际输出分布**，不能把“初始权重相同”当成已经精确跟踪。

正式默认不增加额外 fake warm-up；每轮仍先完成三次 fake updates。不另立第三阶段，
也不把旧预适配预算混入本次 400 次成功 student updates。

### 7.2 Fake-score 的监督目标

在当前 student 参数固定时，生成并 detach：

\[
X^S,\qquad A^S\mid H,c,X^S.
\]

对输出 \(Y^S\) 加噪后训练：

\[
\boxed{
\mathcal L_F^Y
=
\frac{1}{n_M}
\sum_iM_i
\left[
v_\phi^Y(\widetilde Y_\rho,\rho,C)
-
\left(\epsilon_i-\operatorname{sg}(Y_i^S)\right)
\right]^2.
}
\]

State/action 使用与 student 相应分支一致的条件。Action fake-score 始终使用与该 action sample 配对的 student plan。

它拟合的是生成器输出，不是 teacher outputs，也不是经过 controller 修改后的动作分布。

### 7.3 一轮训练分为三个连续部分

**A．Environment collection。** 固定 \(\theta_r\)，8 条 streams 各执行 3 个闭环 chunks，得到 24 个生成前 contexts。

**B．Fake-score fitting。** 继续固定 \(\theta_r\)，在本轮 contexts 上进行 3 次 fake-score updates。每次可使用当前 student 的新 noise draws；这些 samples 不需要执行环境。

**C．Student distillation。** 固定 teacher 与更新后的 fake-score \(\phi_r^+\)，在全部 contexts 上累积 student DMD 梯度，再统一更新一次：

\[
\theta_r\rightarrow\theta_{r+1}.
\]

3:1 是用户本轮确定的更新比；不声称较旧5:1更优或同等稳定。DMD2 用更高频率的 fake-score 更新缓解其对非平稳 generator 分布的跟踪误差；这里保留该思路，但不把论文中的稳定性结果直接当成 WAM-Policy 的保证。([DMD2 原文](https://arxiv.org/html/2405.14867v1))

独立的3:1稳定性短程观测固定为 **5次成功student updates / 15次fake updates**，仅记录loss、
独立fake probe、correction/gradient、task contexts、耗时与资源数据，不作为正式OPD准入条件。
该观测不加入Slurm正式链，其缺失、未完成或数值趋势不能阻断formal；单卡/八卡工程smoke及其原准入规则保持不变。

**这三次 fake-score updates 不对应三轮环境 rollout。** 一次 student update 的各个 contexts 也不能使用不断变化的 fake-score。

---

## 八、反向传播与 shared-DiT joint optimization

### 8.1 Stage 2 的梯度边界

| 路径 | 是否保留梯度 |
|---|---|
| Environment、RAMBO/执行接口、反馈 | 否 |
| 先前环境 chunks | 否 |
| 历史 KV 构建 | 否 |
| 当前 state 的一步 Euler 采样链 | **是** |
| 当前 action 的两步 Euler 采样链 | **是** |
| Action loss → student state plan | 否 |
| Action plan 的 conditioning cache | Detach |
| Teacher 参数 | 否 |
| Fake-score 参数 | 仅在 fake-score update 中更新 |
| Student LoRA | 全部 contexts 累积后更新一次 |

通过原生采样链：

\[
\nabla_\theta\mathcal L_{\mathrm{DMD}}^Y
=
J_{G_\theta}^{\mathsf T}
\frac{\partial\mathcal L_{\mathrm{DMD}}^Y}{\partial Y^S},
\]

DMD correction 能影响实际参与生成的各次 velocity predictions，而不需要 teacher 为每个中间 timestep 提供独立 MSE target。

### 8.2 逐 context backward，最后统一更新

每张 GPU 负责一个三-chunk clip，其本地目标是：

\[
\mathcal L_e
=
\frac13\sum_{j=1}^{3}\ell_{e,j}.
\]

可以先对某个 context 的 state loss 反传，保存 detached plan、释放 state graph，再计算 action loss并反传。处理完三个 contexts 后，完成全局梯度同步和一次 optimizer update。

**State 与 action 之间、不同 contexts 之间，都不提前更新 student。**

这样它们共同优化同一套 shared-DiT LoRA：

\[
\nabla_\theta\mathcal L
=
\nabla_\theta\mathcal L_Z
+
\lambda_P\nabla_\theta\mathcal L_P
+
\lambda_A\nabla_\theta\mathcal L_A.
\]

Stage 1 可以使用 native joint forward；Stage 2 为了执行真实的 state→action 生成依赖，采用顺序采样。**两者都属于共享参数的联合优化，但不要求前向计算组织完全相同。**

### 8.3 不对环境做 BPTT

第三个 chunk 的 history 由前两个 chunks 的实际动作造成，但在计算局部 loss 时，该 history 是固定输入。

因此，三个 local gradients 相加，不包含：

\[
\theta
\rightarrow
A_{\mathrm{past}}
\rightarrow
\mathrm{Environment}
\rightarrow
H
\]

这条梯度路径。

本方案是 **student-induced histories 上的 conditional semi-gradient distillation**，不是对整个物理 trajectory 的精确 joint-KL 优化。

---

## 九、History、KV 与持续环境状态

### 9.1 History 内容与内部 KV 分开管理

每条 stream 的事实记录至少包含实测 observations、executed actions、instruction、时间边界、episode ID、student version，以及适用时的 proprioception。

不同模型分别构建：

\[
K_S=\operatorname{KV}_{\theta_r}(H),
\]

\[
K_T=\operatorname{KV}_{T}(H),
\]

\[
K_F=\operatorname{KV}_{\phi}(H).
\]

**共享的是历史内容，不是 KV tensor。**

### 9.2 参数更新后的处理

Student 更新后保留当前环境物理状态和实测历史，但重建受参数变化影响的 student KV。Fake-score 更新后同样处理其 cache；冻结 teacher 的 cache 可以在历史与条件一致时继续维护。

LoRA 更新同样会改变 hidden representations，因此不能因为 base weights 冻结就继续无条件使用旧 KV。

重建还必须遵守已有 window、position、causal mask 与 eviction 规则；只重新编码最近几个原始 chunks，不保证与原在线 cache 等价。

### 9.3 Streaming 的 on-policy 含义

在第 \(r\) 次更新之后，当前环境状态保留了过去多个 policy 版本的影响：

\[
H_r\sim d^{\theta_0,\theta_1,\ldots,\theta_{r-1}},
\]

而当前生成来自：

\[
(X_r^S,A_r^S)\sim S_{\theta_r}(\cdot\mid H_r,c).
\]

因此，本方案强调的是：

> **当前 student 在持续交互产生的 histories 下，自行生成当轮训练样本。**

它不意味着整条 episode 都由同一个最新参数版本从头生成。重建 KV 修复的是内部表示与参数的一致性，不会改写已经发生的物理过程。

同步仿真训练中，fake-score fitting 和 student update 期间不推进相应环境时间，避免将 learner 的等待时间变成额外的物理动作持续时间。

---

## 十、优化配置与训练预算

### 10.1 保持原有参数量级

| 参数 | Stage 1：若执行离线 SFT | Stage 2：Streaming DMD |
|---|---:|---:|
| Student LoRA rank / alpha | 256 / 256 | 256 / 256 |
| Student learning rate | \(2\times10^{-5}\) | \(2\times10^{-6}\) |
| Fake-score learning rate | 不适用 | \(2\times10^{-6}\) |
| Optimizer | AdamW | AdamW |
| Weight decay | 0.01 | 0.01 |
| Global gradient clipping | 1.0 | Student/fake-score 分别为 1.0 |
| 模态 loss weights | 原有归一化后 \(\lambda_P=\lambda_A=1\) | 分模态归一化后取 1 |
| 精度 | 已验证 mixed precision | 网络 BF16 autocast；关键运算 FP32 |
| Student updates | 可选 SFT 显式指定；直接继承时为 0 | **400** |
| FFM / endpoint regression | 不使用 | 不使用 |
| 独立 Input Calibration | 不使用 | 不使用 |
| 常驻离线 anchor | 不额外添加 | 不额外添加 |
| 大型跨轮 replay pool | 不适用 | 首版不使用 |

Stage 1 的学习率只在确实进行额外 joint SFT 时生效；不能因为存在这个参数，就将本来可直接加载权重的 single-teacher initialization 强制变成一次训练。

Stage 1 可选 SFT 的数据量和训练步数仅在启用时显式填写。Stage 2 沿用已实现的 constant LR，
AdamW betas=(0.9,0.999)、eps=1e-8，无额外 warm-up。**不把旧三阶段 ODE Bootstrap 的预算
或旧 OPD v3 的长 warm-up 自动带入新方案。**

### 10.2 Stage 2 的预算

在所有 rounds 正常完成的情况下：

| 项目 | 总量 |
|---|---:|
| Student optimizer updates | **400** |
| Global clip batches | **400** |
| Clip 实例 | \(400\times8=\mathbf{3,200}\) |
| Environment joint chunks | \(400\times8\times3=\mathbf{9,600}\) |
| 主要 DMD history-context 实例 | **9,600** |
| Fake-score optimizer updates | \(400\times3=\mathbf{1,200}\) |

这里的 9,600 是成功提交 rounds 的 decision-context 实例，不是独立 episodes。Fake-score 和
student learner 的重新采样不额外推进环境。第 400 次成功 student update 后停止后续 predict，
不等待活跃 episodes 自然结束、不补任务配额。建议保留第 200 与 400 次 checkpoint，
每 100 次成功student update以及安全/最终边界保存；保护S200/S400完整恢复点，并保留最近两份。

无效采集、失败 attempt 开销、evaluation 和跳过的 optimizer updates 单独记录，
不能混入“400 次成功 student updates”；9,600 不伪装成包含失败开销的物理交互硬上限。

---

## 十一、验收与方法边界

### 11.1 启动前必须成立的条件

Student 在原生 1/2 sampler 下通过有界启动检查；teacher 与 fake-score 的 FM 时间和输出转换
正确；actor、learner 与部署 sampler 前向一致；action 三方使用同一个 detached student plan；
没有 future observation 泄漏。初始化能力可以低于 teacher，不能把蒸馏目标先写成启动已通过的事实。

这些是算法成立的前提，不是要求重新增加初始化训练阶段。

### 11.2 正式评估使用冻结 checkpoint

Streaming 训练中的一次成功可能由多个参数版本共同完成，不能直接归属于最终 student。

正式评估应当：

\[
\text{冻结 checkpoint}
\rightarrow
\text{标准 reset}
\rightarrow
\text{完整 episode}
\rightarrow
\text{期间不学习}.
\]

比较对象为 initialized student 1/2、最终 OPD student 1/2 和 high-NFE teacher 25/50。
使用同一 held-out cases、原 benchmark horizon 和成功判据，观察任务成功率、失败模式、
video prediction 质量、action 有效性与 latency。旧 2/4 只作历史参考，不混为当前 student。
不虚构 video metric 或未提供的数值差异，不把 student 超越 teacher 或弱 task 提升设为必达目标。

DMD surrogate 数值下降不能单独证明 policy 改善；还应记录 fake-score 的独立样本拟合情况、correction/gradient norms、KV 重建成本和实际监督预算。

### 11.3 本方案能够与不能声称的内容

OPD-v4 的目标是**在固定低预算下保留或改善 teacher 行为，并缓解 student 的环境访问与生成输入偏移**。它不自动提供长期 reward credit assignment，也不保证 teacher 在所有错误 histories 或不可达 state plans 上都可靠。

以后换成 RL teacher 时，还需要区分两项能力：它能够成功执行任务，足以支持 teacher-rollout SFT；它能否在重新加噪的 student samples 上提供可靠的 score guidance，则是 DMD 需要额外成立的条件。

同时，DMD 优化的是固定 sampler 的输出。即使保留 velocity-form 网络，也不应默认更新后的 student 在任意 NFE 下都维持原生 FM 的校准性质或单调提升质量。

---

## 十二、OPD-v4 的最终执行主线

\[
\boxed{
\begin{gathered}
\text{Quadrupedal LingBot-VA SFT Checkpoint}\\
\downarrow\\
\textbf{Stage 1: Off-Policy Student Initialization}\\
\text{直接继承权重；需要时追加 teacher-rollout joint FM SFT}\\
\downarrow\\
\text{保留原生 State 1 / Action 2 Euler sampler}\\
\downarrow\\
\textbf{Stage 2: On-Policy Streaming Distribution Matching Distillation}\\
\text{8 streams × 3 joint chunks，逐 chunk 获取真实反馈}\\
\downarrow\\
\text{3 次 conditional fake-score updates}\\
\downarrow\\
\text{24 contexts 的 state/action DMD 与梯度累积}\\
\downarrow\\
\text{1 次 student update，保留环境状态并更新 KV}\\
\downarrow\\
\text{重复至 400 次成功 student updates}\\
\downarrow\\
\text{冻结 Student，完整闭环评估}
\end{gathered}
}
\]

**这版 OPD-v4 沿用原生 FM student，让离线初始化提供来源明确的行为基础，
让 Streaming DMD 直接优化最终部署的 1/2-NFE 生成与交互过程。** 一步 video 仍是 velocity
网络的一次完整 Euler update，不转换为 endpoint/consistency model。

Stage 1 不宣称完成所有输入校准；Stage 2 也不依赖它提前完成。两阶段通过同一模型、同一 sampler 和明确的 conditioning contract 衔接，构成当前 WAM-Policy 的统一 OPD 路线。
