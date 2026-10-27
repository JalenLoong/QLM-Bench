# 复现方案：在 Go2 + MuJoCo（mjlab）上复现 Leg-Manip 算法

> 论文分析见 [REPRODUCTION.md](REPRODUCTION.md)，服务器配置见 [ENV_SETUP.md](ENV_SETUP.md)。四部分已有实现；5090上的代码审查后工程运行验收已完成，见 `SERVER_5090.md`。训练收敛、专家成功率和正式多seed结果须单独验证。

## 0. 已确定的前提

| 项 | 决定 | 理由 |
|---|---|---|
| 目的 | 按论文把它的算法复现出来 | — |
| 范围 | 论文算法的四部分全部做：① 轨迹参数 g(t)、② 低层控制器、③ 专家数据采集、④ DP3 Planner | — |
| 机器人 | **Unitree Go2**（论文用的是 Aliengo） | 已确定 |
| 仿真 | **MuJoCo**：用 mjlab v1.6.0（MuJoCo Warp GPU 并行 + Isaac Lab 风格 API + PyTorch / rsl_rl） | 不依赖 Isaac Sim 和 RT Core；集群选卡不受限；Go2 模型用 mujoco_menagerie 的 `unitree_go2` |
| 算力 | **RTX 5090 32G 单卡**：开发、② PPO、③ 采数据、④ 闭环评估；**8× MI355X**：只跑 ④ DP3 训练 | MuJoCo Warp 只支持 NVIDIA，物理相关作业只能在 5090 上；DP3 是纯 PyTorch，可以在 ROCm 上跑 |
| 数据与实验管理 | **W&B** 记录所有训练和评估；**Hugging Face 私有仓库**存数据集和 DP3 权重，两台机器靠它交换 | 见 ENV_SETUP.md §4 |

沿用论文的两层结构、轨迹参数化（有理 Bézier + SLERP + flag）、观测 / 动作接口、DP3 Planner 和批量专家采集思路。Go2 + MuJoCo 属于方法级复现；奖励权重与缺失超参采用有记录的实现选择，不能声称逐项原样复刻。

因换机器人、换仿真器而必须改的部分：

1. **尺寸缩放**：Go2 腿长约 0.21 + 0.21 m，Aliengo 约 0.25 + 0.25 m；Go2 站高约 0.30 m，Aliengo 约 0.40 m。论文中的 z 采样范围、按钮 / 门把手 / 阀门高度要按 Go2 实测可达工作空间重新定（先粗按 0.75 倍，训完控制器后实测再校正）。
2. **框架移植**：论文基于 Isaac Gym 和 walk-these-ways，这里改写成 mjlab 的 manager-based 环境（命令项、观测项、奖励项、事件项）。
3. **接触模型**：MuJoCo 是软接触，和 PhysX 不同。脚推物体这类接触参数（solref / solimp、摩擦）要单独调，并在 S4 用真值参数开环执行来检验。

## 1. 环境

```text
uv 项目，Python 3.12，一个 uv.lock：
├── extra "sim"（5090）：mjlab==1.6.0（mujoco / mujoco-warp 3.11、warp-lang、rsl_rl）+ torch 2.9.0（PyPI 版即 CUDA 12.8）
├── 不带 extra（MI355X）：用集群自带的 ROCm 版 torch，不装 mjlab / mujoco
├── 共用：内置DP3核心代码 + diffusers、zarr<3、einops、wandb、huggingface_hub
└── leg_manip（本项目）
```

旧安装配置参考见 [SETUP_4090.md](SETUP_4090.md)；MI355X 见 [ENV_SETUP.md](ENV_SETUP.md) §3。

## 2. 工程结构

```text
Leg-Manip/
├── paper/  REPRODUCTION.md  PLAN.md  ENV_SETUP.md
├── pyproject.toml  uv.lock
├── src/leg_manip/
│   ├── assets/                # Go2 机器人配置（menagerie MJCF + 执行器 / PD），任务物体 MJCF
│   ├── traj/                  # ① 有理 Bézier、SLERP、轨迹参数 <-> 向量、坐标变换（纯 torch，带单元测试）
│   ├── tasks/track/           # ② 低层：LegManip-Track-Go2（三腿行走 + 一腿跟踪）
│   ├── tasks/manip/           # 当前2个任务场景、专家参数、成功判据；其余7个待扩展
│   ├── learning/              # ② PPO + 并发估计器（rsl_rl 子类，加辅助损失）
│   ├── planner/               # ④ DP3 训练与推理封装：纯 PyTorch，不 import 任何仿真代码，MI355X 上也能跑
│   ├── collect/               # ③ 相机 → 点云 → zarr，打包上传 HF（只在 5090 上跑）
│   └── eval/                  # ④ 闭环评估：从 HF 拉 DP3 权重，和控制器一起在仿真里跑（只在 5090 上跑）
├── scripts/                   # train_controller / play / collect_demos / train_planner / eval
└── tests/
```

## 3. 分阶段实施

| 阶段 | 内容 | 在哪跑 | 验收标准 |
|---|---|---|---|
| **S0 环境** | 按 ENV_SETUP.md 配两台机器；建 uv 工程，锁定依赖；打通 W&B 和 HF | 5090 + MI355X | ENV_SETUP.md §2.3、§3.3 验收通过；两边都能读写 W&B 和 HF 私有仓库 |
| **S1 Go2 接入** | 用 menagerie `unitree_go2` 写 mjlab 机器人配置（执行器、PD、碰撞体、足端 site），先跑普通速度跟踪 | 5090 | Go2 速度跟踪能训出稳定四足行走（验证模型、PD、观测管线） |
| **S2 轨迹库 ①** | 有理 Bézier、SLERP、参数打包、世界系 / 物体系 / 机体系变换 | 任意 | 单元测试通过（端点插值、权重全相等时退化为普通 Bézier、SLERP 结果保持单位长度等） |
| **S3 低层环境 ②** | 命令项：随机生成曲线、相位推进、未来 3 个目标点。观测：15 步历史。奖励：见 REPRODUCTION.md §5。事件：域随机化、末端随机外力。flag 选左腿或右腿 | 5090（256–1024 env） | 零动作 / 随机动作能跑通；奖励各项数值合理；能可视化目标曲线 |
| **S4 训练控制器 ②** | PPO + 并发估计器（输出机身速度、末端位置） | **5090**，4096 env，目标约 3B 步，收敛就停；曲线和 checkpoint 记到 W&B | 末端位置误差约 3 s 内收敛到厘米级；三腿行走不摔；左右腿都能用；测出 Go2 可达工作空间 |
| **S5 任务场景** | 先做 Press Button、Close Dishwasher：MJCF 铰接体（按钮用带弹簧的滑动关节，洗碗机门用带阻尼的铰链）；手工设计物体系专家参数；定义成功判据 | 5090 | 用**真值参数**开环执行，记录每任务专家成功率并能采足100条成功示范；不把更换机器人后的数字直接视为论文结果 |
| **S6 采数据 ③** | 深度相机按项目 CAD 装配的支架位姿（机身系 (0.323, 0, 0.328) m、下倾 30.5°，D435 深度视场，见 `assets/go2/CAMERA_MOUNT.md`）→ 反投影到世界系点云 → 只保留物体 → FPS 降到 768 点；每任务 100 条 × 200 步，存成 DP3 的 zarr 格式，打包上传 HF | 5090 | 点云和参数可视化对齐；每任务 20k 帧；HF 上有对应版本 |
| **S7 训 Planner ④** | DP3：点云 + 本体状态 → 世界系轨迹参数；每任务 1 个模型 × 3 seed；先在 5090 上跑通一个 run 并测时长 | **8× MI355X**，从 HF 拉数据；按固定 epoch 把 EMA 权重传回 HF | 训练损失收敛；W&B 里记录数据集的 HF commit |
| **S8 闭环评估** | Planner 10 Hz + Controller 50 Hz；物体随机放在机器人前方扇形区（论文为半径 3 m、40°，按 Go2 缩放）；每 seed 100 回合；固定 epoch 的几个 checkpoint 都评估，按事先定好的规则汇总 | 5090，从 HF 拉 DP3 权重 | 输出成功率表，格式同论文 Table I；结果记到 W&B |
| **S9 扩展** | 其余 7 个任务 | — | 同上 |

先用 Press Button、Close Dishwasher 两个任务打通 S0–S8，再做 S9。

## 4. 需要先定下来的实现选择（我的默认值，可改）

| 问题 | 默认做法 |
|---|---|
| Bézier 阶数 | 6 个控制点 + 6 个权重（和 LaTeX 注释里的配置一致） |
| 末端"朝向" | 小腿方向单位向量（膝 → 足），奖励用点积，和论文的奖励形式一致 |
| 相位 t | 每任务固定时长；Planner 重新预测时 t 不重置 |
| 未来目标点 | 取 0.3 / 0.6 / 0.9 s 之后（LaTeX 注释中的说法） |
| 轨迹参数向量 | flag(1) + 控制点(18) + 权重(6) + 起止朝向(6) = **31 维** |
| PPO 网络 | rsl_rl 默认（actor / critic 为 [512, 256, 128]，ELU） |
| 控制频率 | 物理 200 Hz，策略 50 Hz（decimation 4），Planner 10 Hz |
| DP3 | 单任务模型；n_obs_steps=2；action 就是 31 维参数（一个 episode 内基本恒定，horizon 取短） |
| DP3 checkpoint 选择 | MI355X 上没有仿真，不能边训边评估。按固定 epoch 保存（例如训练进度 50% / 75% / 100% 时），全部拉回 5090 评估；报告最后一个 checkpoint 的成功率，同时列出各 epoch 的结果 |
| 成功判据 | 按钮下压 > 5 mm；洗碗机门角度 < 5°；门开 > 30°；门把手转 > 30°；篮子离地 > 10 cm 并保持 2 s；阀门转 > 30°；球进门；物体掉下桌面 |

## 5. 不在本方案范围内

- 论文的对比基线（端到端 BC、DrQ-v2 HRL / VRL）
- 真机部署

## 6. 需要你提供的信息

- 5090：现有连接与项目环境已验收，具体见部署记录
- MI355X：ROCm 版本、能否用 `rocm/pytorch` 镜像、调度方式、§3.3 验收输出
- W&B 的 entity / 项目名；HF 用哪个账号或组织建私有仓库（两台机器都由你自己登录）
- 一个私有 Git 仓库
- 任务优先级：默认先做 Press Button、Close Dishwasher
