# 复现分析：Learning Visual Quadrupedal Loco-Manipulation from Demonstrations

- arXiv: [2403.20328](https://arxiv.org/abs/2403.20328)（He, Lei, Ze, Sreenath, Li, Xu；2024-03 首发，源码为 2024-08 版本）
- 项目主页: https://zhengmaohe.github.io/leg-manip
- 本地文件：
  - `paper/2403.20328.pdf`：论文 PDF
  - `paper/src/`：arXiv LaTeX 源码（`sections/*.tex`），**注释里有正文没写的超参**，下文已摘出

---

## 1. 一句话概括

四足机器人（Unitree **Aliengo**）只用一条前腿当"机械臂"做操作（按按钮、压门把手、推门、抬篮子、关洗碗机、拧阀门、射门……），同时用另外三条腿走路。
做法是**两层分层**：

| 层 | 方法 | 输入 | 输出 | 频率 |
|---|---|---|---|---|
| 高层 Planner π_p | **DP3**（3D Diffusion Policy）行为克隆 | 世界系点云（768 点）+ 本体状态 | 末端轨迹参数 ʷp（世界系） | 10 Hz |
| 低层 Controller π_c | **PPO** 强化学习 | 15 步本体历史 + 由轨迹参数算出的当前/未来目标点、目标朝向、操作腿 flag | 12 维期望关节角 → 低通 → PD | 50 Hz |

两层之间的"接口"是一组**轨迹参数 p**：

- 操作腿 flag `f`（0 = 左前 FL，1 = 右前 FR）
- 有理 Bézier 曲线的控制点 `p_i ∈ R³` 与权重 `w_i`（正文写 n=6 即 7 个点；LaTeX 注释里的配置是 start / ctrl_1..4 / end 共 6 个点、6 个权重，见 §6）
- 起点 / 终点目标朝向 `q0, q1`，中间用 SLERP 插值

关键 trick：**专家数据不用遥操作**。给每个任务在**物体坐标系**里手工设计一条轨迹参数，随机化物体位姿后转到世界系，让训好的低层控制器在 IsaacGym 里并行执行，同时录点云 + 状态 + 参数。100 条 × 200 步（= 20k 帧视觉数据）约 3 分钟就能采完。DP3 再从点云回归这组参数。

框架图见 `paper/src/figures/framework.pdf`，四个阶段：① RL 训控制器 → ② 冻结控制器采专家数据 → ③ DP3 行为克隆 → ④ 部署（D435 点云 + 外部相机 AprilTag 定位机器人位姿）。

---

## 2. 复现可行性结论

**官方代码没有开源。** 项目主页上的 Code 按钮在 HTML 里被注释掉了，作者 GitHub（`ZhengmaoHe`）下只有主页仓库。所以复现是"拿开源积木自己搭"。

能直接复用的积木：

| 积木 | 仓库 | 用途 |
|---|---|---|
| Isaac Gym Preview 4 | https://developer.nvidia.com/isaac-gym （需 NVIDIA 开发者账号手动下载） | 仿真 + 并行训练 + 采集 |
| walk-these-ways (go1_gym) | https://github.com/Improbable-AI/walk-these-ways | **低层 RL 的底座**。论文 LaTeX 注释里的 `Cfg.domain_rand.*` / `Cfg.commands.*` 写法和这个仓库的配置格式完全一致，作者大概率基于它改的 |
| legged_gym + rsl_rl | https://github.com/leggedrobotics/legged_gym | 备选底座 / PPO 实现 |
| Aliengo URDF | https://github.com/unitreerobotics/unitree_ros （`robots/aliengo_description`） | 机器人模型 |
| DP3 | https://github.com/YanjieZe/3D-Diffusion-Policy | **高层 Planner**（作者之一 Yanjie Ze 就是 DP3 作者） |
| DrQ-v2 | https://github.com/facebookresearch/drqv2 | 仅基线 HRL / VRL 需要 |
| 并发状态估计器 | Ji et al., RA-L 2022（无官方代码，结构简单可自写） | 估计机身速度、末端位置 |

需要**自己写**的部分：

1. 有理 Bézier + SLERP 的命令生成器与随机采样器（低层训练用）
2. "三条腿走 + 一条腿跟踪轨迹"的奖励、观测、终止条件
3. 9 个任务的仿真场景和物体资产（按钮、门把手、门、篮子、洗碗机、阀门、球门等），以及成功判据
4. 每个任务的专家轨迹参数（物体坐标系）
5. IsaacGym 深度相机 → 世界系点云 → 裁剪 / 采样 768 点 → 存成 DP3 的 zarr 格式
6. DP3 闭环评估：Planner 10 Hz 与 Controller 50 Hz 的调度、世界系↔机体系变换

---

## 3. 需要训练什么

| # | 模型 | 算法 | 数据 | 数量 | 是否必须 |
|---|---|---|---|---|---|
| 1 | **低层控制器 π_c**（含并发估计器） | PPO + 估计器监督回归（MSE） | 仿真交互，论文用 **30 亿步**（3B timesteps） | **1 个**，任务无关，左右前腿共用（靠 flag 区分） | ✅ 核心 |
| 2 | **高层 Planner π_p** | DP3（扩散策略） | 每任务 100 条 × 200 步 = 20k 帧（点云 + 状态 + 参数） | 每任务 1 个；论文 9 个任务 × 3 个 seed | ✅ 核心 |
| 3 | 基线 BC（端到端） | DP3 直接输出关节角 | 采集时顺便记录控制器动作；20k / 500k 帧 | 2 个任务 | 可选 |
| 4 | 基线 HRL | DrQ-v2 当 Planner，低层沿用 π_c | 1M 视觉帧，需逐任务设计奖励 | 9 个任务 | 可选 |
| 5 | 基线 VRL | DrQ-v2 端到端 | 5M 视觉帧 | 2 个任务 | 可选 |

**建议的最小复现**：只做 #1 + #2，任务先挑论文重点分析的 **Press Button**（论文 92.3%）和 **Close Dishwasher**（50.3%），再扩展到其余任务。

论文 Table I 的目标数（Ours，3 seed 均值）：

| 任务 | 成功率 | 任务 | 成功率 |
|---|---|---|---|
| Press Button | 92.3 ± 9.0 | Close Dishwasher | 50.3 ± 8.1 |
| Pull Handle | 82.3 ± 3.2 | Pull Objects | 12.7 ± 10.8 |
| Push Door | 85.3 ± 5.0 | Twist Valve | 52.3 ± 10.2 |
| Lift Basket | 59.3 ± 12.0 | Shoot Football | 26.0 ± 2.0 |
| Open Dishwasher | 5.7 ± 5.5 | | |

---

## 4. 环境与依赖

### 4.1 本机现状（已检查）

| 项 | 值 | 评价 |
|---|---|---|
| GPU | RTX 4060 Laptop，**8 GB** 显存，驱动 595 | 能跑，但低于 walk-these-ways 推荐的 10–12 GB，需减少并行环境数 |
| CPU / 内存 | 32 核 / 62 GB | 充足 |
| 磁盘 | 剩余 695 GB | 充足 |
| 系统 | Ubuntu 22.04 | Isaac Gym 官方支持 18.04/20.04，22.04 实测社区普遍可用 |
| Python | 系统 3.10 + `/opt/miniconda3` | Isaac Gym 只支持 Python 3.6–3.8 → **用 conda 建 3.8 环境** |
| CUDA toolkit | 未装 nvcc | 不需要单独装，PyTorch wheel 自带 CUDA runtime |
| ROS | Humble | 仿真阶段用不到；若真机是 Go2 可用于部署 |

### 4.2 推荐软件栈（一个 conda 环境装全部）

```text
conda env: legmanip, python=3.8
├── torch 2.0.1 + cu118（或 2.1 + cu121）  # 4060 是 sm_89，别用 walk-these-ways 写的 1.10+cu113
├── isaacgym (Preview 4, pip install -e isaacgym/python)
├── walk-these-ways (pip install -e .)  —— 改造为 Aliengo + 腿操作任务
├── 3D-Diffusion-Policy/3D-Diffusion-Policy (pip install -e .)
│     只需核心包 diffusion_policy_3d；它 INSTALL.md 里的 mujoco / MetaWorld / Adroit / DexArt 都是它自己的 benchmark，不需要装
├── zarr, hydra-core, einops, diffusers, numba, wandb  # DP3 依赖
├── pytorch3d（可选，最远点采样 FPS；也可以自己写 FPS）
└── drqv2 依赖（仅做基线时）
```

Isaac Gym 必须你自己登录 NVIDIA 开发者账号下载 `IsaacGym_Preview_4_Package.tar.gz`。装完后常见坑：`libpython3.8.so` 找不到 → `export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH`。

**为什么不用 Isaac Lab**：更现代，但 Isaac Sim 推荐 16 GB 以上显存，8 GB 笔记本显卡很吃力；论文用的也是 Isaac Gym，复现时对齐更方便。

### 4.3 算力与时间（粗估，未实测）

| 阶段 | 显存 | 时间 |
|---|---|---|
| 低层 PPO，3B 步 | 2048 env 约 6–7 GB（默认 4000 env 需约 12 GB，要减半） | 按笔记本 4060 约 3–6 万步/秒估算 → **14–28 小时**；实际可能更早收敛 |
| 专家数据采集（带深度相机） | 相机传感器很吃显存，100 个 env 可能要分 2–4 批 | 每任务分钟级 |
| DP3 训练（每任务 20k 帧） | 默认 batch 在 8 GB 上可能放不下，需降 batch 或 `down_dims` | 每任务数小时 |
| DP3 推理 | — | DDIM 10 步，10 Hz 可达 |

---

## 5. 低层控制器细节（正文 + LaTeX 注释）

**训练环境**：轨迹控制点在机器人周围 4 m × 4 m 内随机生成，episode 20 s；控制点每步转到机体系再喂给策略，所以机器人能学会全向三腿行走。

**观测**（15 步历史）：

- 本体 s_t：重力投影 g (3)、关节角 q (12)、关节速度 q̇ (12)、上一步动作 a_{t-1} (12)
- 命令 c_t：flag f (1)、当前目标点 x_t^d (3)、未来 3 个目标点 x_{t+1,t+2,t+3}^d (9)、当前目标朝向 θ_t^d
  - LaTeX 注释提到未来目标点可能取 **0.3 s / 0.6 s / 0.9 s 之后**，而不是相邻控制步
- 估计器输出：机身速度、末端位置（Ji et al. 2022 并发估计器，同样吃 15 步历史；critic 直接拿真值）

**动作**：12 维期望关节角 → 低通滤波 → PD 控制器出力矩。

**奖励**（正文 Table）：

| 项 | 表达式 | 权重 |
|---|---|---|
| 位置跟踪 xy | exp(−‖x_xy − x^d_xy‖² / σ) | 0.8 |
| 位置跟踪 z | exp(−‖x_z − x^d_z‖² / σ)，z 方向尺度放大 5 倍以鼓励抬腿 | 0.8 |
| 朝向跟踪 | exp(−(1 − θ·θ^d) / σ) | 0.3 |
| 末端加速度 | ‖ẍ_ee‖² | −5 |
| 机身加速度 | ‖ẍ_base‖² | −5 |

LaTeX 中**被注释掉但很可能实际用了**的稳定 / 平滑项：base orientation ‖g_xy‖² (−5)、self-collision (−5)、joint pos limit (−10)、joint torque limit (−1)、"free gait" 1(0<触地脚数<3) (+2)、joint torques / angles / velocities (−1e-4)、joint acc (−2.5e-7)、一阶 / 二阶动作平滑 (−0.3 / −0.3)。σ 值正文没给，需要自己调。

**命令随机化**（正文 Table II）：控制点 x, y ∈ [−2, 2] m，z ∈ [0.01, 1.2] m（注释里写 1.4）；权重 w ∈ [1, 2000]；目标朝向 φ, ψ ∈ [0, 2π]，cos θ ∈ [0, 1]（相当于在上半球均匀采样一个方向向量）。

**动力学随机化**（全部来自 LaTeX 注释）：

```text
friction_range         = [0.5, 1.25]
ground_friction_range  = [0.7, 3.0]
restitution_range      = [0.0, 0.4]
added_mass_range       = [0.8, 1.2]   (×)
ran_inertia_range      = [0.5, 1.5]   (×)
com_displacement_range = [-0.08, 0.08] m
gravity_range          = [-1.0, 1.0]
motor_strength_range   = [0.8, 1.2]
motor_offset_range     = [-0.002, 0.002]
Kp / Kd                = [0.7, 1.3] × 默认值（被注释）
drag_range             = [-0.1, 0.8]
```

外加：正文说末端要能承受"未知外力"，应在末端施加随机外力（范围未给）。

**预期效果**（Fig. 控制器误差图）：位置误差约 3 s 收敛到最低，接触物体后略升；朝向误差最低约 0.4 rad（系统欠驱动，优先保证位置）。

---

## 6. 论文没写清楚、需要自己定的点

1. **Bézier 阶数**：正文说 n=6（7 个控制点），LaTeX 注释配置是 6 个点 + 6 个权重（相当于 n=5）。建议先用 6 个点。
2. **朝向的表示**：奖励用的是点积 `θ·θ^d`，采样用的是球面角，说明"朝向"很可能是**小腿 / 足端的方向单位向量**（3 维），而不是完整 SO(3)。注释里另有 start/end euler roll/pitch/yaw ∈ [0,1] 的写法，二者需要自己统一。
3. **相位 t 怎么推进**：t ∈ [0,1] "按轨迹时长缩放"，但时长是固定的、每任务一个值，还是参数的一部分，没说。Planner 每 0.1 s 重新预测参数时 t 是否重置也没说，推测**不重置**（全局 episode 时间）。
4. **PPO 超参 / 网络结构 / σ / PD 增益 / 低通截止频率**：全部未给。建议直接用 walk-these-ways 默认值，Aliengo 的 PD 增益参考 legged_gym 社区配置（Kp≈40–60，Kd≈1–2，需自己调）。
5. **任务资产与成功判据**：9 个任务的物体模型、尺寸（只给了按钮直径 10 cm、阀门直径约 40 cm 且轴高 60 cm）、成功阈值都要自己定义。洗碗机、门可以考虑用 PartNet-Mobility 的铰接模型。
6. **评估初始分布**（来自被注释的表注）：物体出现在机器人前方**半径 3 m、张角 40°** 的扇形内，阀门 yaw 随机 ±36°。
7. **相机位置与点云处理**：正文写"相机装在机器人身后以及头部"，有歧义。框架图里仿真点云只有物体（篮子），说明做了**物体分割 / 裁剪**。真机上要用后处理（裁剪工作空间、去地面、降采样）对齐到仿真分布。
8. **DP3 配置**：单任务还是多任务、horizon、n_obs_steps 都没给。由于专家参数在一个 episode 内基本恒定（物体系固定、只随物体位姿变），Planner 本质上是"从点云估计物体位姿并输出对应轨迹"，horizon 可以取短。
9. **"专家"上限**：用真值参数开环执行的成功率论文没报告，复现时应先测，用来区分"控制器不行"和"Planner 不行"。

---

## 7. 分阶段复现路线

| 阶段 | 内容 | 验收标准 |
|---|---|---|
| **P0 环境** | conda py3.8 + torch cu118 + Isaac Gym + walk-these-ways + DP3 核心包 | `1080_balls_of_solitude.py` 能跑；walk-these-ways 的 Go1 默认训练能启动 |
| **P1 换机器人** | 在 walk-these-ways 里接入 Aliengo URDF，先训普通速度跟踪行走 | Aliengo 能稳定四足行走（验证 URDF、PD、观测管线正确） |
| **P2 低层控制器** | 实现 Bézier + SLERP 命令生成、15 步历史、并发估计器、§5 的奖励与随机化，PPO 训练 | 随机曲线上末端位置误差约 3 s 内收敛到厘米级；三腿行走不摔；左右腿都能用 |
| **P3 任务场景** | 先搭 Press Button、Close Dishwasher；手工设计物体系专家参数 | 用**真值参数**开环执行，成功率显著高于论文 Ours 数字（作为上限） |
| **P4 采数据** | 随机物体位姿，深度相机 → 世界系点云 → 768 点；存 zarr | 每任务 100 条 × 200 步，可视化点云与参数正确对齐 |
| **P5 训 Planner** | DP3：点云 + 状态 → 世界系轨迹参数；闭环评估（10 Hz / 50 Hz） | 3 seed 成功率接近 Table I（Button 约 90%，Dishwasher 约 50%） |
| **P6 扩展** | 其余 7 个任务；可选基线 BC / HRL / VRL | 对照 Table I / III |
| **P7 真机**（可选） | 见 §8 | 零微调部署能完成按按钮 / 推门 |

---

## 8. 真机部署需要的东西（如果要做 sim2real）

- **机器人**：Unitree Aliengo（论文原型）。如果手上是 Go1 / Go2，需要换 URDF、重训低层；Go2 腿更短、机身更矮，门把手、阀门（轴高 60 cm）这类任务的高度可能够不到，需要缩放任务。
- **深度相机**：Intel RealSense D435（装在机器人头部）。
- **全局定位**：外部相机 + 机器人身上贴 AprilTag，用来求机器人在世界系的位姿，做点云和轨迹参数的坐标变换。也可以用动捕替代。
- **计算**：带 GPU 的主机跑 DP3（扩散推理是论文自认的瓶颈）+ 50 Hz 控制器。
- **SDK**：Aliengo 用旧版 `unitree_legged_sdk`（3.x）；Go2 用 `unitree_sdk2` 或 ROS 2（本机已装 Humble）。
- **点云后处理**：工作空间裁剪、去地面、离群点滤波、FPS 降到 768 点，目标是对齐仿真里"只有物体"的干净点云。
