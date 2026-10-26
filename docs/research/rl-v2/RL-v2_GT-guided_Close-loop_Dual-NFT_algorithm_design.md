---
id: RL-V2-ALGORITHM
type: research
status: proposed
source_map: []
---
# WAM-Policy RL-v2：GT-Guided Closed-Loop Dual DiffusionNFT

**完整算法设计（Revised Method v2.0）**  
**日期：** 2026-10-25  
**对象：** Quadrupedal LingBot-VA（基于四足机器人数据 SFT 后的模型）+ RAMBO 9D high-level commands  
**算法简称：** GT-Guided Closed-Loop Dual-NFT  
**定位：** 本方案命名为 **RL-v2**。先前从任务初始状态执行**完整 environment trajectory**、主要依据最终 **0/1 terminal task-success reward** 进行 DiffusionNFT 更新的方案，命名为 **RL-v1**。RL-v2 不再以完整任务成功作为唯一学习信号，而是使用 demonstration anchors、可配置短时程闭环执行和 dense reward。

> **版本修订范围：** 在此前确认的 Quadrupedal LingBot-VA、9D RAMBO action、EMA old policy、三类 reward、首个 joint chunk 的双条件 DiffusionNFT 更新设计基础上，新增并统一 **每条 demonstration 默认 8 个 temporal strata（相应动态 anchor 起点）** 的抽样设置。单条 demonstration 的首轮验证配置为每个 outer iteration 使用 **2 个 anchors**，每个 anchor 采样 **4 个 candidate clips**；评分 clip 长度统一记为可配置的 **\(H\)**，不固定为 3。其余算法约定保持不变。

---

## 1. 方法概述

### 1.1 研究目标

本方法面向经过四足机器人 demonstration 数据 SFT 的 **Quadrupedal LingBot-VA**，通过真实 simulation environment feedback 和 DiffusionNFT，对模型的 video prediction 与 inverse dynamics 两个生成阶段进行联合 RL fine-tuning。

希望解决两个核心问题：

1. **完整任务 rollout 成本高。** RL-v1 每次都从任务初态执行完整 trajectory，才能获得最终 task reward。
2. **低成功率导致 reward 稀疏。** 当 SFT 基础模型尚不能可靠完成任务时，terminal binary success reward 很难区分不同失败轨迹的质量。

为此，RL-v2 引入 **demonstration-guided rollout**：从成功 demonstration 的中间状态恢复环境，使模型从有意义的任务状态出发进行短时程探索，再根据实际执行结果与 GT trajectory 的接近程度计算 dense reward。

### 1.2 核心设计

采用 PersistWorld-style 的 **multi-chunk scoring, first-chunk update**：

```text
Quadrupedal SFT demonstration
    │
    ▼
默认 8 个 temporal strata；每轮采样 B 个 GT simulator anchors
    │
    ▼
EMA old policy 从每个 anchor 采样 G 个 joint candidates
    │  对每条 candidate：Video flow → Action flow → RAMBO execution
    ▼
每条 candidate 执行 H-chunk 真实 closed-loop rollout
    │  每个 chunk 后读取实际 observation，重建下一 chunk history
    ▼
计算三类 rewards
    ├─ Joint-execution：主要信号，评价整个 H-chunk clip（默认 70%）
    ├─ Video：较强辅助，仅评价首个 chunk（默认 25%）
    └─ Action：较弱辅助，仅评价首个 9D action chunk（默认 5%）
    │
    ▼
同一 anchor 内形成 reward-relative NFT weights
    │
    ▼
仅以第一个 joint chunk 的 video/action clean endpoints 计算双条件 NFT loss
    │
    ▼
更新 trainable policy；外层迭代结束后 EMA soft update
```

必须区分如下范围：

| 概念 | 含义 | RL-v2 设定 |
|---|---|---|
| Joint chunk | 一次 video/action 生成及相应环境执行 | 基本更新单元 |
| Clip size \(H\) | 从一个 demonstration anchor 连续执行的 joint chunk 数量 | 可配置，\(H\geq1\) |
| Reward horizon | 使用多少个 chunks 的后果评价首段候选 | \(H\) |
| Update window | 哪些生成结果参与 DiffusionNFT loss | **仅首个 joint chunk** |
| Anchor strata | 每条 demonstration 沿时间轴划分的起点区间 | **默认 8 个** |

参考 [PersistWorld](https://arxiv.org/abs/2603.25685) 的多段评价、首段更新思路，但我们的后续 rollout 是真实环境闭环，并且同时训练 video/action 两个条件分布，并非直接复用其 action-conditioned video world model。

---

## 2. 模型与系统定义

### 2.1 RL 的初始化模型

RL 从已完成四足适配 SFT 的 checkpoint 开始：

\[
\boxed{\theta_{\mathrm{init}}=\theta_{\mathrm{Quadrupedal\ SFT}}}
\]

**不是** native LingBot-VA 的原始 30D action checkpoint。

当前项目的相关版本：

- **Adaptation v2：** 9D RAMBO action，双视角 RGB。
- **Adaptation v3：** 在 v2 基础上增加 proprioception/state 建模，但输出的 high-level action 仍然是 9D。
- **RL-v2：** 不重新定义 action space，不重新训练 RAMBO 底层控制器。

两种 SFT 模型均可以使用这套 RL 算法，但 observation/history 的构造必须遵循相应 checkpoint 的输入约定。

### 2.2 9D RAMBO high-level action

动作顺序固定为：

\[
\boxed{
 a_t=[v_x,v_y,\omega_z,p_x^{FL},p_y^{FL},p_z^{FL},f_x^{FL},f_y^{FL},f_z^{FL}]\in\mathbb R^9
}
\]

其中 \(FL\) 为前左操作腿。

| Action group | Dimensions | 物理含义 |
|---|---|---|
| Desired base velocity | 0–2 | Base \(v_x,v_y\) 和 yaw rate \(\omega_z\) |
| Desired FL EEF position | 3–5 | 操作腿足端目标位置 |
| Desired FL EEF force | 6–8 | 操作腿足端期望作用力 |

这一顺序与项目中的 [WAM-Policy native9 model interface](https://github.com/JalenLoong/WAM-Policy/blob/adaptation/v2-mujoco-sft/docs/current/model/adaptation-v2.md) 一致。

必须注意：

- **9D 为 high-level command，而非机器人真实状态。** Desired EEF position 与 actual EEF position、desired force 与 actual contact force 不可混用。
- 当前部分 quadrupedal 数据与运行配置会把 desired EEF force 固定为零。算法保持 9D 接口，但 Action reward 要区分可变控制量与固定控制量，避免无效 force 输出干扰 RL。

### 2.3 环境执行接口

\[
\boxed{
\text{WAM-Policy}\xrightarrow{\text{9D command}}
\text{RAMBO}\xrightarrow{\text{low-level control}}
\text{Quadrupedal simulator}
}
\]

- WAM-Policy：生成 future video 和 9D high-level action。
- RAMBO：将 high-level command 转换成底层控制。
- Simulator：执行控制并返回真实 observations 与 task status。
- DiffusionNFT：**只更新上层 WAM-Policy**，不更新 RAMBO。

环境必须与选定 quadrupedal SFT checkpoint 的任务及数据契约对应。MuJoCo SFT 路线使用 quadrupedal MuJoCo/QLM-Bench 环境；Isaac 路线则使用对应 Isaac 任务。**本轮 RL 不是 native LingBot-VA 的 LIBERO-Long / Panda action setup。**

### 2.4 Observation 与 multi-rate 约定

以项目 v2 的接口为例：

- Policy RGB：Go2 ego-view + D435i task-centric 双视角。
- 原始 RGB 与 high-level command：50 Hz。
- 模型侧 RGB：12.5 Hz，遵循既定采样相位和预处理。
- Action：保持 50 Hz，不因视频降采样而丢弃中间指令。
- 模型输入遵循 action validity mask、causal VAE temporal packing 及其原有 history 约定。

一个 joint chunk 不等同于“一个视频帧 + 一个 9D action”。设该 chunk 有 \(K_a\) 个有效控制指令、\(K_v\) 个模型视频采样时刻，两者由 SFT 模型 chunk 配置、validity mask、实际 timestamps 决定，不默认 \(K_a=K_v\)。所有 reward 的对齐都使用真实环境时间，而不是仅凭数组索引。

---

## 3. Demonstration Anchors 与训练数据

### 3.1 Demonstration trajectory

先针对一个 task，选择 training split 中的一条成功 demonstration：

\[
\mathcal D=\{(s_n^D,h_n^D,V_n^D,A_n^D)\}_{n=0}^{N-1}.
\]

| 符号 | 含义 |
|---|---|
| \(N\) | Demonstration 中的 joint chunk 数量 |
| \(n\) | Demonstration 的 joint chunk index |
| \(s_n^D\) | 第 \(n\) 个 chunk 执行前的完整 simulator/controller state |
| \(h_n^D\) | 截止该 chunk 起点，模型可以合法观察到的历史 |
| \(V_n^D\) | 该 chunk 后续时间区间内的 GT video |
| \(A_n^D\) | 该 chunk 对应的 GT 9D RAMBO command sequence |

历史可以写成：

\[
h_n^D=(c, O_{\le n}^D,A_{<n}^D,\text{其他已启用的历史条件}).
\]

其中 \(c\) 为任务指令。对于 Adaptation v3，加入已经观测到的 proprioception/state history；对于 v2，不凭空加入新的状态输入。**GT future video/action 不属于 \(h_n^D\)。**

### 3.2 默认 8 个 Anchor 起点：Temporal Stratified Sampling（RL-v2 新增明确设定）

对于每条 demonstration，默认将其合法的 joint chunk 起点划为 **8 个沿时间分布的区间（temporal strata）**，再从每个区间动态采样 anchor。这个选择参考 [DemoStart](https://arxiv.org/abs/2409.06613) 对 demonstration 时间区间分层取样的思路，而不是说“8”对所有四足任务有理论最优性。

设合法且可恢复的起点集合为：

\[
\mathcal I_D=\{n:\text{anchor }n\text{ 可恢复且至少有 1 个有效后续 joint chunk}\},
\]

\[
N_{\mathrm{valid}}=|\mathcal I_D|,
\qquad M_D=\min(8,N_{\mathrm{valid}}).
\]

按照时间顺序，把 \(\mathcal I_D\) 划为 \(M_D\) 个互不重叠、尽量等数量的区间：

\[
\mathcal I_D=\bigcup_{q=1}^{M_D}\mathcal I_q,
\qquad
\mathcal I_q\cap\mathcal I_{q'}=\varnothing\;(q\ne q').
\]

每次选中第 \(q\) 个区间时，从中均匀采一个具体 chunk index：

\[
\boxed{n_q\sim\operatorname{Uniform}(\mathcal I_q),
\qquad b_{n_q}=(s_{n_q}^D,h_{n_q}^D,n_q).}
\]

**这表示默认在一条 demonstration 上维护 8 个时间区域的 anchor 机会，而不是永久固定 8 个不变的 simulator states。** 具体起点在区间内随训练重新采样。

**单条 demonstration 的第一阶段训练配置**：

\[
\boxed{M_D=8,\quad B=2,\quad G=4}
\]

其中：

- \(M_D=8\)：每条 demonstration 默认 8 个 temporal strata（若合法起点不足 8 个则取 \(N_{\mathrm{valid}}\)）。
- \(B=2\)：每个 outer iteration 从该 demonstration 的两个不同 strata 各采一个 anchor，总计 2 个 anchors。
- \(G=4\)：每个 anchor 使用同一 EMA old policy、独立生成噪声采 4 条 candidate clips。
- **无重复循环：** 先随机打乱 8 个 strata 的顺序，每轮用其中两个；4 个 outer iterations 覆盖 8 个 strata，再重新打乱并在各区间内重新选取实际 chunk。不会反复只训练同一段。
- 后续引入多条 demonstrations 时，先确定本轮的 demonstration/stratum，再采样 anchors；\(B\) 表示 **本轮全局 anchor 数量**，不应误解为每条 demonstration 强制额外各取 \(B\) 个。

对某个 anchor \(n\)，接下来可用于评分的有效长度：

\[
\boxed{H_n=\min(H,N-n)}
\]

如果尾部有效 chunks 不足，\(H_n\) 自动缩短；**同一 anchor 的全部 \(G\) 个 candidates 使用相同的 \(H_n\)**，保证组内比较公平。

初始 worst-case environment execution budget（不含 reset/replay 开销）约为：

\[
\boxed{C_{\mathrm{env}}\lesssim BGH=8H\quad\text{joint chunks / outer iteration}.}
\]

如果提前成功/失败，或 anchor 靠近尾部，实际执行可能更短。

> **与 RL-v1 的差别：** RL-v1 从正常任务初态做完整 trajectory rollout；RL-v2 在训练期间通过 demonstration-derived anchors 扩大可学习状态覆盖。正式 evaluation 仍必须从正常任务初态开始。

### 3.3 Simulator state restoration

仅保存视频、9D command 和部分机器人状态，并不意味着可以精确恢复整个 simulator。合法 anchor 的 snapshot 必须足以恢复：

- 机器人及环境物体的物理状态；
- 当前 task 状态；
- RAMBO controller 内部状态；
- action filter、reference 和必要的时间/控制上下文；
- WAM 可见 history，以及对应模型版本的 KV cache 或可重建 prefix。

同一个 anchor 的所有 candidates，恢复相同物理状态与历史；仅生成随机噪声独立。

在 RL 前先完成 GT replay reproducibility test：

\[
\operatorname{EnvRollout}
(s_n^D,A_{n:n+H_n-1}^D)
\approx s_{n+H_n}^D.
\]

同时检查中间 observations 和 timestamps。

如果现有 quadrupedal SFT demonstration 没有完整 snapshot，则需要补采 snapshot，或从 episode 初态重放 GT commands 到 anchor。后者具有额外前缀执行成本，不能默认为 reset 免费。本算法要求可恢复性，但**不预设现有数据已具备该能力**。

---

## 4. Trainable、EMA Old 与 Frozen Reference Policy

### 4.1 三个模型版本

| Policy | 参数 | 职责 | 梯度 |
|---|---|---|---|
| Trainable policy | \(\theta\) | 计算 NFT loss，接收 optimizer 更新 | 是 |
| EMA old policy | \(\bar\theta\) | 生成 candidates 和 continuation；提供 old velocity | 否 |
| Frozen reference | \(\theta_{\mathrm{ref}}\) | 提供四足 SFT 初始模型的稳定正则约束 | 否 |

\[
\boxed{
\theta_0=\bar\theta_0=\theta_{\mathrm{ref}}=\theta_{\mathrm{Quadrupedal\ SFT}}
}
\]

### 4.2 EMA 更新机制

第 \(r\) 个 outer iteration 内固定 \(\bar\theta_r\) 采样全部 candidates，并使用同版本计算 NFT old velocity。优化结束获得 \(\theta_{r+1}\) 后：

\[
\boxed{
\bar\theta_{r+1}
=\mu_r\bar\theta_r+(1-\mu_r)\theta_{r+1}
}
\]

其中 \(\mu_r\in[0,1)\) 是 EMA decay。\(\mu=0.9\) **每个 outer iteration 更新一次**可作为试跑值，但必须结合一个 outer iteration 内的 optimizer steps 校准，不能与 per-step EMA 0.9 视为等价。

同一批 rollout 的采样 policy version 必须一致；reference 始终冻结。EMA 用于平滑 rapidly changing video/action policy 的采样分布，并不保证单调 improvement。

### 4.3 冻结与训练范围

| Component | RL-v2 设定 |
|---|---|
| Video flow / Transformer 相关参数 | Trainable |
| Action flow / Transformer 相关参数 | Trainable |
| 可训练共享 attention / projection | Trainable |
| Frozen causal VAE | Frozen |
| Text encoder | Frozen |
| Reward LPIPS encoder | Frozen |
| RAMBO low-level controller | Frozen |
| SFT action normalizer | Frozen |
| Frozen reference | Frozen |
| EMA old policy | 无梯度，仅 soft update |

可通过 LoRA 降低显存，但必须覆盖 video/action 的必要训练路径，不能仅更新 video branch 却声称完成双阶段 RL。是否全参数训练属于实现配置。

### 4.4 Joint policy factorization

令 \(Z\) 为 future video clean latent endpoint，\(U\) 为 SFT normalized action space 的 9D action endpoint：

\[
\boxed{
\pi_\theta(Z,U\mid h)
=p_\theta(Z\mid h)q_\theta(U\mid h,Z)
}
\]

保留 LingBot-VA 原生 video prediction → inverse dynamics 的 causal factorization。两个条件分布可共享参数，并非必须是两套完全独立模型。

---

## 5. \(H\)-Chunk Closed-Loop Candidate Sampling

### 5.1 从共同 anchor 采样多个 candidates

针对 anchor \(b_n\)，对所有 \(i=1,\dots,G\) 恢复：

\[
s_{i,0}=s_n^D,
\qquad h_{i,0}=h_n^D.
\]

同一个 \(\bar\theta_r\) 配合各自独立的随机噪声生成：

\[
\mathcal C_n=\{\tau_n^{(1)},\ldots,\tau_n^{(G)}\}.
\]

### 5.2 Clip 内每个 joint chunk 的生成与执行

对候选 \(i\)，\(j=0,\ldots,H_n-1\)：

**Stage 1 — Video prediction**

\[
Z_{i,j}\sim p_{\bar\theta_r}(Z\mid h_{i,j}),
\qquad
\widehat V_{i,j}=\operatorname{Decode}(Z_{i,j}).
\]

**Stage 2 — Inverse dynamics**

\[
U_{i,j}\sim q_{\bar\theta_r}(U\mid h_{i,j},Z_{i,j}),
\qquad
A_{i,j}^{\mathrm{req}}=\mathcal T_{\mathrm{9D}}(U_{i,j}).
\]

**Stage 3 — Environment execution**

\[
\left(O^{\mathrm{exec}}_{i,j},A^{\mathrm{exec}}_{i,j},s_{i,j+1}\right)
=\operatorname{EnvExecute}(s_{i,j},A^{\mathrm{req}}_{i,j}).
\]

**Stage 4 — Closed-loop history update**

\[
\boxed{
h_{i,j+1}
=\operatorname{UpdateHistory}
(h_{i,j},O^{\mathrm{exec}}_{i,j},A^{\mathrm{exec}}_{i,j})
}
\]

区分：

- \(A^{\mathrm{req}}\)：WAM 提交给 RAMBO 的 requested 9D command。
- \(A^{\mathrm{exec}}\)：经实际控制接口限制/处理后确认执行的 command。

**从第二个 joint chunk 起，模型必须依赖真实执行反馈更新 history，不得重新注入后续 GT observation 或 GT action 作为闭环条件。**

### 5.3 仅保存首段 NFT 样本

当 \(j=0\)，额外保存：

\[
\boxed{
\mathcal X_{i,n}=(h_n^D,Z_{i,0},U_{i,0})
}
\]

及采样 action 时实际使用的 video-conditioning representation。后续 \(j\ge1\) 的 video/action 只用于评价首段的后果，不直接进入当前 NFT loss；无需保存其完整 denoising 计算图，但应保留 reward 和必要 execution diagnostics。

### 5.4 Partial-video-denoising 约束

基本算法以完整 clean video endpoint \(Z\) 为 NFT 样本，并假设 action decoder 以这个 endpoint 为条件。这是清晰的首版数学设定，**不能未经验证就认为等价于使用 partial denoising 的部署 sampler**。

若 action decoder 实际使用 \(s_p<1\) 的中间视频表示，应区分：

\[
Z^{\mathrm{cond}}=Z(s_p),
\qquad Z^{\mathrm{clean}}=Z(1).
\]

Action NFT 保留采样时真正使用的 \(Z^{\mathrm{cond}}\)；Video NFT 不将 noisy intermediate 冒充 clean endpoint。可沿同一视频采样轨迹继续积分至数据端获得 clean endpoint，但这是进一步适配，须验证与 partial-denoise policy 的一致性。采样及正式评估必须记录 video/action NFE、video flow endpoint 和 action-conditioning 类型。

---

## 6. Reward Design

\[
\boxed{R=w_JR_J+w_VR_V+w_AR_A},
\qquad
w_J>w_V>w_A\ge0,
\quad w_J+w_V+w_A=1.
\]

默认：

\[
\boxed{(w_J,w_V,w_A)=(0.70,0.25,0.05)}.
\]

| Reward | 评价对象 | 时间范围 | 目的 |
|---|---|---|---|
| Joint-execution \(R_J\) | 实际 environment observation vs GT observation | 整个 \(H\)-chunk clip | 评价真实执行结果 |
| Video \(R_V\) | 首段 predicted video vs GT video | 仅首个 chunk | 引导未来视觉计划 |
| Action \(R_A\) | 首段 generated 9D RAMBO command vs GT command | 仅首个 chunk | 保留较弱的示范动作先验 |

### 6.1 统一视觉相似度：MAE + LPIPS

第一版采用冻结的 MAE + LPIPS 组合。相关工作如 [RLVR-World](https://arxiv.org/abs/2505.13934) 和 [VLA-RFT](https://arxiv.org/abs/2510.00406) 使用参考视频相似度构造密集引导；[WAM-RL](https://arxiv.org/abs/2606.17906) 的部分任务消融也说明简单 pixel metric 不一定劣于复杂 learned features。这些工作支持 metric 的选择，但不能证明同一 reward 对 quadrupedal RAMBO task 最优。

设 \(X,Y\) 是具有 \(C\) 个 camera views、每个 view 含 \(F\) 个对齐有效帧的视频：

\[
\begin{aligned}
d_{\mathrm{vis}}(X,Y)
=&\sum_{c=1}^{C}\omega_c\frac1F\sum_{f=1}^{F}
\Bigg[
\alpha\frac{\operatorname{MAE}(X_{c,f},Y_{c,f})}{s_M}\\
&+(1-\alpha)\frac{\operatorname{LPIPS}(X_{c,f},Y_{c,f})}{s_L}
\Bigg],
\end{aligned}
\]

\[
\sum_{c=1}^{C}\omega_c=1,
\quad \alpha\in[0,1],
\qquad
\boxed{S_{\mathrm{vis}}(X,Y)=\exp[-d_{\mathrm{vis}}(X,Y)]}.
\]

初始设置：

- \(\alpha=0.5\)；两个 policy views 等权 \(\omega_1=\omega_2=0.5\)。
- \(s_M,s_L>0\) 由初始训练 rollout 误差统计一次性标定并固定。
- 对 padding/black-border 区域遮罩，避免其主导 reward。
- MAE 与 LPIPS 分别遵守自身的输入归一化要求。
- Video reward 的 GT video 可先经同一冻结 VAE reconstruction 再比较，以降低生成与重建域差异；Joint reward 的真实 observation 和 GT observation 均来自 simulator，可用一致 RGB preprocessing 后直接比较。
- 两类视觉 reward 的输入方式不同，对其误差尺度可分别标定。
- 可使用可靠的固定 task ROI mask；第一版不强制增加 segmentation model。

### 6.2 Joint-execution reward（主要信号）

对 candidate \(i\) 的 chunk \(j\)：

\[
\boxed{
r^J_{i,j}
=S_{\mathrm{vis}}(O^{\mathrm{exec}}_{i,j},V^D_{n+j})
}
\]

它衡量“模型发出的 video-action 决策导致的**真实环境观测**是否接近 demonstration”，而不是 predicted video 对实际 observation 的直接一致性。整个 chunk 使用对齐的观测序列，不只取最后一帧。

将 \(H_n\) 个 chunk 的执行分数聚合：

\[
\boxed{
R_i^J
=\frac{\sum_{j=0}^{H_n-1}\gamma^j r^J_{i,j}}
{\sum_{j=0}^{H_n-1}\gamma^j}
}
\]

\(\gamma\in(0,1]\)，第一版 \(\gamma=1\)，即平均各 chunk 的执行效果，避免 \(H\) 增大时仅靠多项求和改变 reward 尺度。

**提前终止规则：**

| 事件 | 处理 |
|---|---|
| 正常执行完 \(H_n\) | 正常聚合 |
| 环境明确确认成功 | 结束 rollout，剩余 nominal chunks 的 execution reward 记 1 |
| 跌倒或不可恢复失败 | 结束 rollout，剩余 nominal chunks 的 execution reward 记 0 |
| 普通时间截断但未确认成功/失败 | 不自动判断为不可恢复失败，按预定义的有效区间规则处理 |

这是 terminal handling，不是新加第四类 reward。

**边界：** 强时间对齐的 reference reward 仍具有示范轨迹和执行节奏偏好；当 learner 纠偏或采用其他有效轨迹时，可能暂时得到较低分。增大 \(H\) 本身不会自动消除这个问题。

### 6.3 Video reward（较强辅助引导）

只对首个 joint chunk 计算：

\[
\boxed{
R_i^V=S_{\mathrm{vis}}(\widehat V_{i,0},V_n^D)
}
\]

\(\widehat V_{i,0}\) 来自 EMA old policy 生成的 clean video 经冻结 VAE decoder 得到的 RGB。它引导未来视觉计划接近 demonstration；该计划能否真正由 action decoder 实现，由 Joint-execution reward 间接反馈。

不对 \(j\ge1\) 的 continuation video 再额外使用同时间 GT video 施加强辅助约束，避免离轨后进一步强化不适用的目标。

### 6.4 Action reward（较弱辅助引导；9D RAMBO）

首个 chunk 的第 \(k\) 个有效 command：

\[
\widehat a^{\mathrm{req}}_{i,k}=[\widehat{\mathbf v}_{i,k},\widehat{\mathbf p}_{i,k},\widehat{\mathbf f}_{i,k}],
\quad
a^D_{n,k}=[\mathbf v^D_{n,k},\mathbf p^D_{n,k},\mathbf f^D_{n,k}].
\]

按 \(g\in\{v,p,f\}\) 划分三个 3D group。在每组有效维度上按固定物理尺度求归一化 L1 误差：

\[
d^g_{i,k}
=\frac{1}{|\mathcal A_g|}
\sum_{\ell\in\mathcal A_g}
\frac{|\widehat a^{g,\mathrm{req}}_{i,k,\ell}-a^{g,D}_{n,k,\ell}|}{b_{g,\ell}},
\]

其中 \(\mathcal A_g\) 是该组**实际有效且可执行**的维度集合，\(b_{g,\ell}>0\) 为固定尺度。没有有效维度的组不参与总距离。

\[
d^A_{i,k}
=\omega_vd^v_{i,k}+\omega_pd^p_{i,k}+\omega_fd^f_{i,k},
\quad
\sum_{g\in\mathcal G_{\mathrm{active}}}\omega_g=1.
\]

\[
\boxed{
R^A_i=\frac1{K_a}\sum_{k=1}^{K_a}\exp(-d^A_{i,k})
}
\]

这里 \(K_a\) 是有效的 50 Hz high-level commands 数量，包含有效 action mask 的处理；无 gripper matching，**不使用 native 30D action 逻辑**。

**Zero desired EEF force 情况：** 如果 force 三维在运行时被强制置零，且不能实际改变 RAMBO 控制，则把该组视为 inactive：

\[
\boxed{\omega_f=0,\qquad\omega_v=\omega_p=0.5.}
\]

9D 接口保留不变；此时 force 维不用于 Action reward 排序，也不能把 NFT 对这三维的变化误认为获得了可用 contact-force control。需要让 reward-driven action update 与运行时有效控制维度保持一致。若后续允许非零 desired force 且它确实影响环境，再启用该组。Desired force 不等于真实测量的接触力。

### 6.5 Total reward

\[
\boxed{
R_i=w_JR_i^J+w_VR_i^V+w_AR_i^A
}
\]

默认：

\[
\boxed{
R_i=0.70R_i^J+0.25R_i^V+0.05R_i^A
}
\]

各项 reward 在合适标定下都处于 \([0,1]\)，故 \(R_i\in[0,1]\)。这些比例控制的是 reward 组成，并不等同于 Video NFT / Action NFT 的梯度权重。

---

## 7. Reward Normalization 与 Candidate Ranking

同一 anchor 的 \(G\) 条 candidate clip 给出：

\[
\{R_1,\ldots,R_G\},
\qquad
\overline R_n=\frac1G\sum_{i=1}^{G}R_i.
\]

定义相对优势和 DiffusionNFT 正负分支权重：

\[
A_i=\frac{R_i-\overline R_n}{Z_R},
\]

\[
\boxed{
\rho_i=\frac12+\frac12\operatorname{clip}(A_i,-1,1)
}
\quad\Longrightarrow\quad\rho_i\in[0,1].
\]

- \(\rho_i>0.5\)：比本组平均更好。
- \(\rho_i<0.5\)：比本组平均更差。
- \(\rho_i=0.5\)：没有相对优势。

建议：

- \(Z_R=\max(\sigma_{\mathrm{running}},\epsilon_R)\)，使用跨组维护且有下限的尺度，避免微小组内差异被放大。
- **先合并三项 reward 再归一化 total reward**，不将 \(R_J,R_V,R_A\) 分别做每组 z-score。
- 若 \(\max_iR_i-\min_iR_i<\epsilon_{\mathrm{gap}}\)，跳过该组 reward-driven NFT 更新，记录 reward collapse、candidate diversity 等日志；不人为制造 positive labels。

上述组内中心化与正负映射参考 [DiffusionNFT](https://arxiv.org/abs/2509.16117)，不要求强行把每个小组的标准差归一化为 1。

---

## 8. Dual-Conditional DiffusionNFT Update

只对每条候选的**首个 joint chunk**计算 NFT loss。联合分布为：

\[
\pi_\theta(Z,U\mid h)=p_\theta(Z\mid h)q_\theta(U\mid h,Z).
\]

### 8.1 两种条件样本

| NFT 分支 | Clean endpoint | Conditioning |
|---|---|---|
| Video | \(X_i^V=\operatorname{sg}(Z_{i,0})\) | \(c_i^V=h_n^D\) |
| Action | \(X_i^A=\operatorname{sg}(U_{i,0})\) | \(c_i^A=(h_n^D,\operatorname{sg}(Z_{i,0}))\) |

\(\operatorname{sg}\) 表示 stop-gradient。表中是 full-clean-video 基本模式；若实际 action sampling 依赖 partial video，则 action 条件必须替换为**采样时真正使用的** intermediate representation，不得换成 GT video 或另一个 clean estimate。

两种 NFT 的 clean samples 都来自该轮 EMA old policy 的自主采样，未来 GT 仅用于 reward，而不作为当前 candidate 的生成条件。

### 8.2 对两个 endpoint 分别重新加噪

采用 LingBot-VA 的约定：\(s=0\) 为 noise，\(s=1\) 为 data。对 \(m\in\{V,A\}\)：

\[
s_m\sim\mathcal U(0,1),
\quad\epsilon_m\sim\mathcal N(0,I),
\]

\[
\boxed{x_{i,s}^m=(1-s_m)\epsilon_m+s_mX_i^m},
\qquad
\boxed{u_i^m=X_i^m-\epsilon_m}.
\]

这一步是 NFT 的 forward noising / flow regression，不是环境 rollout；video/action 可以分别采样自己的噪声及 flow time。

### 8.3 Old velocity 与 trainable velocity

\[
v_{i,\mathrm{old}}^m
=\operatorname{sg}\left[v_{\bar\theta_r}^m(x_{i,s}^m,s_m,c_i^m)\right],
\]

\[
v_{i,\mathrm{train}}^m=v_\theta^m(x_{i,s}^m,s_m,c_i^m).
\]

两者使用相同 noisy endpoint、相同条件；\(\bar\theta_r\) 是本轮冻结的 EMA old snapshot。共享 Transformer 的 forward 必须遵循正确的模态布局、causal mask 和时间输入。

### 8.4 Implicit positive/negative branches

\[
\boxed{
v_{i,+}^m=(1-\beta)v_{i,\mathrm{old}}^m+\beta v_{i,\mathrm{train}}^m
}
\]

\[
\boxed{
v_{i,-}^m=(1+\beta)v_{i,\mathrm{old}}^m-\beta v_{i,\mathrm{train}}^m
}
\]

\(\beta>0\) 是 NFT mixing coefficient，与 clip discount \(\gamma\) 不同。隐式 clean endpoint estimates 为：

\[
\widehat X_{i,\pm}^m=x_{i,s}^m+(1-s_m)v_{i,\pm}^m.
\]

### 8.5 Adaptive NFT loss

\[
\ell(\widehat X,X)
=\frac{\operatorname{MSE}_{\mathrm{valid}}(\widehat X,X)}
{\max\left[\operatorname{sg}\big(\operatorname{MAE}_{\mathrm{valid}}(\widehat X,X)\big),\epsilon_{\mathrm{NFT}}\right]}.
\]

正负分支分别计算停止梯度的归一化分母。模态 \(m\) 的 NFT loss：

\[
\boxed{
\mathcal L_m^{\mathrm{NFT}}
=\frac1\beta\mathbb E_i\left[
\rho_i\ell(\widehat X_{i,+}^m,X_i^m)
+(1-\rho_i)\ell(\widehat X_{i,-}^m,X_i^m)
\right]
}
\]

得到 \(\mathcal L_V^{\mathrm{NFT}}\) 和 \(\mathcal L_A^{\mathrm{NFT}}\)。

有效位置约束：

- Video：只计算有效新生成 latent tokens，排除 conditioning/padding/重复 overlap。
- Action：只计算 SFT validity mask 标记的有效 9D action tokens；若某个 command group 在实际运行时固定不可控，reward-driven update 也必须按对应有效控制 mask 处理。

正负分支与 adaptive endpoint loss 依据 [DiffusionNFT 官方实现](https://github.com/NVlabs/DiffusionNFT/blob/main/scripts/train_nft_sd3.py)。用于 WAM 双条件模型是我们的扩展，不是原始图像 NFT 已验证的完全相同设置。

### 8.6 Frozen-reference regularization

\[
\mathcal L_{\mathrm{ref}}^m
=\mathbb E\operatorname{MSE}_{\mathrm{valid}}\left(
v_\theta^m(x_s^m,s_m,c_i^m),
\operatorname{sg}[v_{\theta_{\mathrm{ref}}}^m(x_s^m,s_m,c_i^m)]
\right).
\]

\[
\boxed{\mathcal L_{\mathrm{ref}}=\mathcal L_{\mathrm{ref}}^V+\mathcal L_{\mathrm{ref}}^A}.
\]

它是 velocity-prediction regularizer，不是显式精确计算的 policy KL。reference 在相同 noisy input 和正确条件下输出 velocity，参数始终冻结为初始 quadrupedal SFT。

### 8.7 Joint training objective

\[
\boxed{
\mathcal L_{\mathrm{total}}
=\lambda_V\mathcal L_V^{\mathrm{NFT}}
+\lambda_A\mathcal L_A^{\mathrm{NFT}}
+\lambda_{\mathrm{ref}}\mathcal L_{\mathrm{ref}}
}
\]

起始可设 \(\lambda_V=\lambda_A=1\)，并采用较小的 \(\lambda_{\mathrm{ref}}\)；具体需结合规范化后的 loss 和 gradient norms。\(\lambda_A\) 不应因为 GT Action reward 的系数 \(w_A\) 很小就自动减小：Action policy 仍主要从 Joint-execution reward 学习。

本版以 frozen reference 为默认稳定机制，不额外强制引入 GT SFT rehearsal。如果以后添加 SFT anchor，则必须使用**与 demonstration history 匹配**的监督数据，而不是将离轨 history 与原本 GT future 硬配。

### 8.8 梯度边界

不需要通过以下链条反向传播：

```text
Video sampling → Action sampling → RAMBO → Simulator → Reward
```

环境只负责评分，score 转为 \(\rho_i\) 后用于两个 conditional NFT forward-process losses；不要求 simulator 可微，不要求保存跨 chunk denoising 计算图，也不要求 action loss 穿过先前的 video sampler。

同一 \(\rho_i\) 为 video/action 同时提供反馈是合理的联合 reward guidance，但**不能把单一 generator NFT 的理论保证直接解释为完整 WAM policy 的任务成功率单调提升保证**。

---

## 9. 完整训练算法

### Algorithm 1：RL-v2 — GT-Guided Closed-Loop Dual-NFT

```text
Inputs:
    D                 Successful quadrupedal SFT demonstration(s)
    theta_init        Quadrupedal LingBot-VA SFT checkpoint
    Env               Corresponding quadrupedal simulator
    RAMBO             Frozen low-level controller
    M_D               Temporal strata per demonstration (default 8)
    B                 Anchors per outer iteration (default 2 in single-demo trial)
    G                 Candidates per anchor (default 4)
    H                 Configurable clip size, measured in joint chunks
    wJ, wV, wA        Reward weights (default 0.70, 0.25, 0.05)
    gamma             Clip return discount
    beta              DiffusionNFT mixing coefficient
    mu                EMA decay per outer iteration

Initialize:
    theta       <- theta_init
    theta_old   <- theta_init
    theta_ref   <- theta_init

    Freeze theta_ref, VAE, text encoder, reward encoder, RAMBO
    Construct verified demonstration anchors and temporal strata
    For each demonstration:
        M_D <- min(8, number_of_valid_anchor_chunks)
        partition valid chunk indices into M_D contiguous temporal strata
        create a shuffled no-replacement cycle over stratum IDs
    Calibrate and freeze reward metric scales

For each outer iteration r:

    Freeze theta_old for the entire iteration
    Select B distinct strata/anchors from the current sampling cycle
        - In the single-demo trial: 2 different strata per iteration
        - Sample one valid chunk uniformly within each selected stratum
        - After all 8 strata have been visited (normally 4 iterations),
          reshuffle strata and resample chunk positions in future visits
    NFT_buffer <- []

    For each sampled anchor n:

        H_n <- min(H, remaining_valid_reference_chunks(n))
        CandidateGroup <- []

        For candidate i = 1 ... G:

            Restore identical simulator + RAMBO/controller snapshot
            Restore corresponding model-visible history h_demo[n]
            Initialize independent generation noise
            JointRewards <- []

            For chunk j = 0 ... H_n - 1:

                Z <- VideoFlow.sample(theta_old, history)
                actual_Z_condition <- ExtractActualActionVideoCondition(
                    Z, video_sampler_state
                )  # Clean Z in the full-endpoint mode
                U <- ActionFlow.sample(theta_old, history, actual_Z_condition)

                V <- DecodeVideo(Z)
                A_req <- InverseNormalizeAndMap9D(U)
                A_exec, Obs, status <- Env.execute_via_RAMBO(A_req)

                If j == 0:
                    Save detached first_video_endpoint (clean Z)
                    Save detached first_action_endpoint (normalized U)
                    Save actual action-conditioning video representation
                    RV <- VideoReward(V, GT_video[n])
                    RA <- ActionReward(A_req, GT_action_9D[n])

                RJ_j <- ExecutionReward(Obs, GT_video[n+j])
                Append RJ_j to JointRewards

                Update history from real Obs and actually executed actions

                If environment terminates:
                    Apply fixed terminal handling for remaining nominal chunks
                    Break

            RJ <- NormalizedDiscountedReturn(JointRewards, gamma, H_n)
            R_i <- wJ * RJ + wV * RV + wA * RA

            CandidateGroup.append(
                anchor_id, old_policy_version, original_history,
                first_video_endpoint, first_action_endpoint,
                actual_video_condition, R_i
            )

        Compute group-relative NFT weights rho_i from total rewards

        If candidate reward differences are meaningful:
            NFT_buffer.extend(CandidateGroup with rho_i)
        Else:
            Log no-preference group; skip reward-driven NFT update

    For each minibatch in NFT_buffer:

        Re-noise stored video clean endpoints
        Compute Video NFT with original-history condition

        Re-noise stored normalized 9D action clean endpoints
        Compute Action NFT with saved predicted-video condition

        Compute frozen-reference velocity regularization

        L_total <- lambdaV * L_video_NFT
                 + lambdaA * L_action_NFT
                 + lambdaRef * L_reference

        Backward L_total; optimizer step on theta

    theta_old <- mu * theta_old + (1 - mu) * theta

    Log reward statistics, gradient norms, policy drift and costs
    Save complete trainable / EMA / optimizer / RNG checkpoint

Output:
    Reward-fine-tuned Quadrupedal LingBot-VA policy theta
```

训练后 evaluation 只部署选定 inference policy，不读取 GT future、reward evaluator 或 demonstration reset。可以单独评估 EMA policy，但不能把 current/EMA 两套不同参数的 KV cache 或权重随意混用。

---

## 10. 训练配置与工程约束

### 10.1 初始超参数

以下为第一轮可执行配置，不代表最优实验参数：

| Hyperparameter | 符号 | 初始选择 |
|---|---|---|
| **Temporal strata per demonstration** | \(M_D\) | **默认 8；不足 8 个合法起点时取 \(N_{\mathrm{valid}}\)** |
| **Anchors per outer iteration** | \(B\) | **2（单条 demonstration 验证阶段）** |
| **Candidates per anchor** | \(G\) | **4** |
| **Strata selection** | — | **No-repeat cycle；每 4 轮覆盖 8 个 strata，随后重新打乱** |
| **Within-stratum anchor** | — | **均匀动态采样 1 个有效 chunk** |
| Clip size | \(H\) | 可配置整数；先用 \(H=1\) 验证，再扩展 |
| Joint reward weight | \(w_J\) | 0.70 |
| Video reward weight | \(w_V\) | 0.25 |
| Action reward weight | \(w_A\) | 0.05 |
| Visual MAE mixing | \(\alpha\) | 0.5 |
| Clip discount | \(\gamma\) | 1.0 |
| Video NFT loss weight | \(\lambda_V\) | 1.0 |
| Action NFT loss weight | \(\lambda_A\) | 1.0 |
| EMA decay | \(\mu\) | 0.9 / outer iteration，按更新频率校准 |
| NFT mixing coefficient | \(\beta\) | 0.1，作为实现起点 |
| Reference regularization | \(\lambda_{\mathrm{ref}}\) | 小的正值，按 loss 尺度设置 |
| Video/Action NFE | \(N_V,N_A\) | 与所选 SFT inference 模式一致，显式记录 |
| Action dimension | \(d_A\) | 9 |
| Low-level controller | — | RAMBO，冻结 |

Clip size 可以设：

\[
H\in\{1,\ldots,H_{\max}\},
\]

但同一个 anchor 的 candidate group 需要相同的有效 \(H_n\)。第一阶段 \(H=1\) 先验证双 NFT loss，之后作为独立配置扩展至 multi-chunk lookahead；不预先强制引入 \(H\) curriculum。

### 10.2 Actor、Environment、Learner 分工

| 模块 | 职责 | 主要资源 |
|---|---|---|
| Sampling actor | EMA old policy 的 video/action sampling | GPU |
| Environment worker | RAMBO、物理执行、observations、task status | 与仿真环境适配的 CPU/GPU |
| NFT learner | Re-noising、双 NFT loss、backward、EMA update | 训练 GPU |

AMD MI355X 上的 MuJoCo 路线可以把 physics/rendering 放在 CPU，避免引入 CUDA rendering 依赖；Isaac 路线需要单独满足其仿真资源约束。两者可共享算法接口，但 snapshot/渲染/低层控制的实现不能假定完全一致。

### 10.3 Rollout buffer 最小数据合同

| Field | 含义 |
|---|---|
| `task_id`, `demo_id`, `anchor_id`, `stratum_id` | 训练起点与所在时间区间 |
| `old_policy_version` | 采样与 old velocity 的准确参数版本 |
| `clip_size`, `effective_horizon` | \(H\)、\(H_n\) |
| `history_context` | 首个 joint chunk 的合法模型条件 |
| `video_clean_endpoint` | Video NFT clean sample |
| `action_clean_endpoint_9d` | Action NFT 在 normalized space 的 clean sample |
| `video_condition_used_by_action` | Action NFT 必须复用的实际 predicted-video condition |
| `requested_action_9d` | Action reward 和控制诊断 |
| `executed_action_9d` | 实际执行、history 更新 |
| `reward_joint`, `reward_video`, `reward_action` | 三项 reward |
| `reward_total`, `nft_weight` | NFT scalar feedback |
| `termination_status` | Success/failure/early termination |
| `validity_masks` | action / video / command-group validity |

不要求永久保存全部 denoising chains。按审计需要另外保存 observations、执行轨迹和可视化媒体。

### 10.4 History、Causality 与 KV cache

GT future 仅用于 reward evaluator 或将来独立声明的 GT SFT branch，不参与当前 candidate 的视频/动作生成条件。

\[
h_{j+1}=f(h_j,O_j^{\mathrm{exec}},A_j^{\mathrm{exec}}).
\]

KV cache 依赖生成它的模型参数；同一 old policy version 的起点 prefix 可以共享，但 current / old / reference 需要与自己的参数保持条件特征一致。不能在更新后把旧版本 KV 直接当作 current policy 的精确缓存。

### 10.5 环境成本

一个 outer iteration 的基础环境执行预算约为：

\[
C_{\mathrm{env}}\approx BGH.
\]

默认 \(B=2,G=4\) 时，最大 nominal 执行量约 \(8H\) 个 joint chunks，此外还包含恢复 snapshots、历史重建、视频生成、action 生成和媒体处理等开销。

**这种设计减少了参与 NFT gradient 的更新范围，不保证环境总步数一定低于 RL-v1。** 采样范围、起点数和候选数应分别记录。

---

## 11. 验证与评估

### 11.1 局部 RL 能力

训练日志至少记录：

- 每个 anchor、stratum 的 reward mean/std、validity 和训练次数；
- \(R_J,R_V,R_A\) 单独变化及 total reward gap；
- high-reward 与 low-reward candidates 的实际执行差异；
- Video NFT 与 Action NFT losses、gradient norms；
- Trainable 与 EMA old policy 的偏移；
- success、failure、termination 的比例；
- 每组有效 reward 的采样与仿真成本；
- 8 个 temporal strata 的周期性覆盖情况。

Reward group 的**可区分性**是核心观测量。如果所有 candidates 的 \(R_i\) 几乎一样，NFT backward 即使成功也未必获得有意义的策略改善方向。

### 11.2 完整闭环任务能力

正式 evaluation 从正常任务初态开始：

\[
s_0\sim p_{\mathrm{eval}}(s_0).
\]

在整个任务中不允许插入 demonstration anchor reset。优先比较：

- Quadrupedal SFT baseline；
- RL-v2 trainable checkpoint；
- RL-v2 EMA checkpoint（作为单独模型）；
- Task success rate、task progress；
- Robot fall、invalid action、unsafe command；
- 完整 episode 的实际交互与推理成本。

Training anchors 只来自 train split；validation/test GT futures 不能参与 RL reward、归一化统计的训练标定。固定一条成功 demonstration 可以验证局部可行性，但不能直接证明整个任务的跨初始状态泛化。

---

## 12. 方法优势、边界与研究定位

### 12.1 对比 RL-v1：Full-Trajectory Binary-Reward RL

| 维度 | RL-v1：Full-Trajectory Binary-Reward RL | RL-v2：GT-Guided Closed-Loop Dual-NFT |
|---|---|---|
| 训练起点 | 通常为任务初态 | Demonstration 中间的可恢复 anchor |
| Anchor 设置 | 无 | 默认每条 demonstration 8 个 temporal strata，动态 anchor 采样 |
| Reward | 完整轨迹最终 0/1 success | Joint-execution 主导的 dense reward + 首段 Video/Action 辅助 reward |
| 低初始成功率 | 多数候选同为失败，反馈稀疏 | 可比较局部轨迹的执行接近程度 |
| Rollout horizon | 完整任务 | 可配置 \(H\)-chunk |
| Credit assignment | 长时程粗粒度 | \(H\)-chunk lookahead 主要用于评价首段 |
| NFT 更新范围 | 可以覆盖完整 trajectory 的多个 chunks | 只更新首个 joint chunk 的 video/action 两个条件分布 |
| 成本 | 受完整任务时长制约 | 受 \(BGH\) 影响，不保证总成本一定降低 |

### 12.2 方法局限

1. **Reference tracking ≠ task-optimal reward。** 有效但不同于 demonstration 的轨迹，可能因不同步而被扣分。
2. **Lookahead credit 存在噪声。** 后续 continuation 本身包含 action sampling 和环境随机性，同一首段可能对应不同的后续结果。
3. **双条件 NFT 是方法扩展。** 原始单 generator DiffusionNFT 不能直接保证 joint WAM 的任务成功率单调改善。
4. **Snapshot restoration 是硬前提。** RAMBO controller state、simulator state、timestamps 不齐全会使奖励错误。
5. **Desired EEF force 是否实际可控影响学习对象。** 对零力固定接口，不得把 force 输出变化误认为实际接触控制能力。
6. **默认 8 个 strata 是采样设计而非定理。** 它借鉴 demonstration 分层 reset 的经验，不保证足以覆盖所有短暂关键接触事件。动态区间内抽样避免把起点永久固定为 8 个状态。

### 12.3 与相关工作的关系

- **DiffusionNFT：** Reward-weighted forward-process positive/negative policy optimization。
- **PersistWorld：** Multi-chunk continuation scoring 与局部 endpoint 更新。
- **DemoStart：** Demonstration 时间区间分层与 simulator reset 的 anchor 选择思路；RL-v2 默认 8 个 strata 的最直接数量参考。
- **RLVR-World / VLA-RFT：** Reference-aligned visual similarity 作为 dense reward 的相关依据。
- **Quadrupedal LingBot-VA + RAMBO：** 我们实际优化的 video-action 条件生成机制、9D high-level command 和真实控制反馈。

需要在本项目实验中验证的新组合是：

\[
\boxed{
\begin{gathered}
\text{Demonstration-Anchored Quadrupedal}\\
\text{Closed-Loop Rollout}
\\+
\text{Execution-Dominant Dense Reward}
\\+
\text{First-Joint-Chunk Dual DiffusionNFT}
\end{gathered}
}
\]

其可行性与有效性须通过状态重放、正确条件的双 NFT loss、局部 reward 区分度和正常任务初态下的完整闭环评估逐一证实。

---

## 13. 最终算法定义

RL-v2 可以由以下核心公式概括。

**1. Quadrupedal EMA old policy 的联合采样**

\[
\boxed{
\pi_{\bar\theta}(Z,U\mid h)
=p_{\bar\theta}(Z\mid h)q_{\bar\theta}(U\mid h,Z)
}
\]

**2. 默认 8 个 strata 的动态 demonstration anchor 抽样**

\[
\boxed{
M_D=\min(8,N_{\mathrm{valid}}),\qquad
n_q\sim\operatorname{Uniform}(\mathcal I_q)
}
\]

单条 demonstration 的第一阶段训练默认：

\[
\boxed{B=2,\qquad G=4},
\]

区间按不重复循环选取，\(H\) 保持可配置。

**3. \(H\)-chunk reward 评价首段后果**

\[
\boxed{
R_i=w_J
\frac{\sum_{j=0}^{H_n-1}\gamma^j r_{i,j}^J}
{\sum_{j=0}^{H_n-1}\gamma^j}
+w_VR_{i,0}^V+w_AR_{i,0}^A
}
\]

**4. 仅首段 video/action 的双条件 NFT 目标**

\[
\boxed{
\mathcal L_{\mathrm{RL}}
=\lambda_V\mathcal L_V^{\mathrm{NFT}}
+\lambda_A\mathcal L_A^{\mathrm{NFT}}
+\lambda_{\mathrm{ref}}\mathcal L_{\mathrm{ref}}
}
\]

**5. 每轮优化后的 EMA old soft update**

\[
\boxed{
\bar\theta_{r+1}
=\mu_r\bar\theta_r+(1-\mu_r)\theta_{r+1}
}
\]

**最终定义：** WAM-Policy **RL-v2** 保留四足 SFT 模型已有的 video/action 架构与 RAMBO 9D command contract；对成功 demonstration 默认建立 8 个时间区间的动态 anchor 采样机制，通过短时程真实闭环得到以 execution 为主的 dense reward，用 reward 评价首个 joint chunk 的后续表现，再使用两个条件 DiffusionNFT loss 对上层 WAM policy 做 RL fine-tuning。与之相对，**RL-v1** 专指之前的完整任务 rollout + 最终稀疏 0/1 reward 方案。

---

## 参考资料

1. **DiffusionNFT — Online Diffusion Reinforcement with Forward Process**：<https://arxiv.org/abs/2509.16117>；[官方训练代码](https://github.com/NVlabs/DiffusionNFT/blob/main/scripts/train_nft_sd3.py)。
2. **PersistWorld**：<https://arxiv.org/abs/2603.25685>；[官方训练代码](https://github.com/Jai2500/PersistWorld/blob/main/scripts/train_nft_wm.py)。
3. **DemoStart**：<https://arxiv.org/abs/2409.06613>。
4. **Overcoming Exploration in Reinforcement Learning with Demonstrations**：<https://arxiv.org/abs/1709.10089>。
5. **WorldCompass**：<https://arxiv.org/abs/2602.09022>。
6. **Causal World Modeling for Robot Control / LingBot-VA**：<https://arxiv.org/abs/2601.21998>；[代码仓库](https://github.com/Robbyant/lingbot-va)。
7. **RLVR-World**：<https://arxiv.org/abs/2505.13934>。
8. **VLA-RFT**：<https://arxiv.org/abs/2510.00406>。
9. **WAM-RL**：<https://arxiv.org/abs/2606.17906>。
10. **RAMBO**：<https://arxiv.org/abs/2504.06662>；[代码仓库](https://github.com/catachiii/rambo)。
11. **WAM-Policy quadrupedal model/data contracts**：[9D model contract](https://github.com/JalenLoong/WAM-Policy/blob/adaptation/v2-mujoco-sft/docs/current/model/adaptation-v2.md)、[数据接口](https://github.com/JalenLoong/WAM-Policy/blob/adaptation/v2-mujoco-sft/docs/current/contracts-v2.md)。

**状态说明：** 本文件是算法设计，包含来自文献的构造、当前项目的已有接口约定以及本次提出但尚需实验验证的双条件 NFT / reward / anchor 组合；不声称已完成对应 RL 训练或闭环实验。
