# 环境配置清单（Leg-Manip 复现：Go2 + MuJoCo）

> 当前5090部署实况与命令见 [SERVER_5090.md](SERVER_5090.md)。[SETUP_4090.md](SETUP_4090.md) 保留为旧4090安装参考；本文件说明整体分工与AMD数据流。

## 硬件分工（2026-10-25 定）

| 机器 | 负责 |
|---|---|
| **RTX 5090 32G 单卡**（开发机） | 写代码、调试；② 低层控制器 PPO 训练；③ 专家数据采集；④ 闭环评估 |
| **8× AMD MI355X**（训练集群） | 只跑 ④ DP3 训练；当前2任务 × 3 seed = 6个run，扩展9任务后为27个 |
| **W&B + Hugging Face** | W&B 记录实验；HF 存放数据集和 checkpoint，两台机器之间靠它传数据 |

为什么这样分：MuJoCo Warp / Warp 只支持 NVIDIA CUDA，所以凡是跑物理仿真的作业都只能放在 5090 上。DP3 训练是纯 PyTorch，可以在 ROCm 上跑（详见 §3）。

**仿真栈：[mjlab](https://github.com/mujocolab/mjlab) v1.6.0**
- 底层是 MuJoCo Warp（GPU 并行的 MuJoCo），上层是 Isaac Lab 风格的 manager-based API
- 用 PyTorch + rsl_rl 训练
- 自带 GPU 批量 RGB-D 相机（`CameraSensor`，Warp 光线追踪）
- 机器人模型用 mujoco_menagerie 的 `unitree_go2`

> 版本号和命令已对照 mjlab v1.6.0、ROCm 兼容表、JAX / Warp 文档核实（2026-10-25），5090已完成基础运行和短训练验收；AMD/ROCm仍须在集群上实测。

---

## 1. 四个部分跑在哪

| 部分 | 要做的事 | 用到的组件 | 机器 |
|---|---|---|---|
| ① 轨迹参数 g(t) | 有理 Bézier、SLERP、坐标变换 | 纯 PyTorch | 5090（MI355X 上也能用） |
| ② 低层控制器 | PPO，4096 个并行环境，目标约 30 亿步 | mjlab（MuJoCo Warp）+ rsl_rl | **5090** |
| ③ 专家数据采集 | 并行环境里装深度相机 → 点云 → 降采样到 768 点 | mjlab `CameraSensor` | **5090** |
| ④ DP3 训练 | 点云 + 本体状态 → 轨迹参数 | PyTorch + DP3 核心包 | **MI355X** |
| ④ 闭环评估 | Planner + Controller 一起在仿真里跑 | PyTorch + mjlab | **5090** |

---

## 2. 5090 开发机

### 2.1 当前服务器（2026-10-26 实测）

- 地址：`ubuntu@<5090服务器IP>`，项目：`/home/ubuntu/mycode/Leg-Manip`。
- GPU：RTX 5090，32607 MiB；系统 Ubuntu 24.04。
- 驱动：580.178.04 **Open Kernel Module**。旧4090镜像的闭源模块无法初始化5090，现已切换。
- 复用项目现有 `.venv`，CUDA/Warp初始化和依赖一致性检查通过。
- 原始CAD与运行模型均放项目目录；相机位姿按项目CAD模型，不能回退到旧模型。

磁盘估算：

| 用途 | 大小 |
|---|---|
| 系统和基础包 | 约 10G |
| Python 环境：项目环境 + mjlab 验收环境 + uv 缓存 | 约 25G |
| 源码：mjlab、DP3、mujoco_menagerie | 约 2G |
| 专家数据：点云每任务约 0.2G；调试时如果存深度图，每任务约 6G | 1–15G |
| 从 HF 拉回来评估的 DP3 权重（只要 EMA，每个约 1G，27 个） | 约 30G |
| PPO checkpoint、日志、评估视频 | 约 10G |
| **合计** | **约 80–90G，加上余量取 200G** |

### 2.2 系统与驱动（需要 root 的部分）

| 项 | 要求 | 检查命令 |
|---|---|---|
| 系统 | Ubuntu 22.04 或 24.04，x86_64 | `lsb_release -a` |
| NVIDIA 驱动 | **580及以上的open内核模块**；本机已验证580.178.04-open | `nvidia-smi` |
| CUDA toolkit | **不需要**，torch 和 warp 的 wheel 都自带运行时 | — |
| 系统包 | `git tmux ffmpeg libegl1 libgl1 libglib2.0-0`（EGL 用于无显示器时录视频） | — |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh`（装在用户目录，不需要 root） | `uv --version` |
| 网络 | 能访问 `pypi.org`、`pypi.nvidia.com`（warp）、`download.pytorch.org`、`github.com`、**`wandb.ai`、`huggingface.co`** | — |

### 2.3 验收（配好后请把输出发我）

先用 mjlab 自己的仓库测试机器，正式工程由我来建：

```bash
mkdir -p ~/legmanip_ws && cd ~/legmanip_ws
git clone -b v1.6.0 --depth 1 https://github.com/mujocolab/mjlab.git
cd mjlab
uv sync --extra cu128
```

```bash
# 1) 基础信息
nvidia-smi && lsb_release -a && uv --version
uv run python -c "import torch, warp as wp, mujoco, mujoco_warp; wp.init(); print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0), mujoco.__version__)"
```

```bash
# 2) GPU 并行物理 + PPO（对应 ②），记下终端打印的每秒步数
uv run train Mjlab-Velocity-Flat-Unitree-Go1 \
    --env.scene.num-envs 4096 --agent.max-iterations 50 --agent.logger tensorboard
```

```bash
# 3) GPU 批量相机（对应 ③④）
uv run pytest tests/test_camera_sensor.py -q
```

```bash
# 4) 无显示器离屏渲染（只用于录视频；失败也不影响主流程，可以改用 CPU 软件渲染）
MUJOCO_GL=egl uv run python -c "import mujoco; m=mujoco.MjModel.from_xml_string('<mujoco><worldbody><geom size=\"1\"/></worldbody></mujoco>'); r=mujoco.Renderer(m); d=mujoco.MjData(m); mujoco.mj_forward(m,d); r.update_scene(d); print('egl ok', r.render().shape)"
```

第 2 步打印的每秒步数决定训练时间：30 亿步除以它，就是 ② 在这张卡上大约要跑多久。

### 2.4 正式工程（由我来建，你不用操作）

```text
~/legmanip_ws/
├── mjlab/                  # 上面的验收副本，也作为源码参考
├── Leg-Manip/              # 本项目，uv 管理，Python 3.12
│   ├── pyproject.toml      # extra "sim"：mjlab + torch（5090）；不带 extra：只有 DP3 训练所需（MI355X）
│   ├── uv.lock             # 锁死全部版本
│   └── source/leg_manip/
│       ├── sim/ ...        # 依赖 mjlab，只在 5090 上用
│       └── planner/ ...    # DP3 训练，纯 PyTorch，不 import 任何仿真代码，两边都能跑
├── 3D-Diffusion-Policy/    # DP3，只用核心包 diffusion_policy_3d
└── mujoco_menagerie/       # unitree_go2 模型
```

DP3 原来锁定的 `numba==0.56.4`、`diffusers==0.11.1`、`hydra-core==1.2.0` 等太老，和 Python 3.12、新版 numpy 不兼容。我会换成新版本，有接口不兼容的地方在代码里修。

---

## 3. MI355X 训练集群（只跑 DP3）

保留集群现有ROCm torch；用 `uv pip install -e .` 安装项目（不带extra），运行用 `uv run --active --no-sync`。不要在该环境执行会重建/清理依赖的 `uv sync`。

### 3.1 能跑什么、不能跑什么（2026-10 核实）

- **不能跑物理**：Warp 和 MuJoCo Warp 只支持 NVIDIA CUDA。MuJoCo Warp 的 README 写明是为 NVIDIA 硬件设计的；社区给 Warp 提过的 HIP/ROCm 移植 PR（#1770、#1932）都没有合并。
- **能跑 DP3**：ROCm 官方兼容表已验证 PyTorch 2.12–2.14 支持 MI355X（gfx950）。DP3 的模型都是标准算子（Conv1d、GroupNorm、MLP），diffusers 的调度器也是纯 PyTorch。
- **唯一要避开的**：DP3 可选的 pytorch3d 最远点采样是 CUDA 扩展。点云降采样在 5090 上采数据时就做完，MI355X 上只训练，不需要它。

### 3.1b 从 W&B 查到的集群实况（WAM-Policy 项目置顶的 4 个 run，2026-10-19/20）

| 项 | 值 | 来源 |
|---|---|---|
| 调度 | SLURM，分区 `mi355x`；作业从登录节点提交，共享盘挂在 `/shared/<用户>/` | v2/v3-TRAIN-001 的 run 元数据 |
| 节点 | 128 核，约 2.2 TB 内存，系统盘约 930 GB | 同上 |
| 系统 | Linux 6.8，glibc 2.39（Ubuntu 24.04） | 同上 |
| Python / torch | CPython 3.12.3；torch 2.9.1（ROCm 自编译版 `+git8907517`）、torchvision 0.24.1、triton 3.4.0、diffusers 0.36.0 | v3 run 的 requirements.txt |
| 外网 | HF 上传约 10 MB/s（40 GB 用了 50 分钟）；W&B 在线记录正常 | v3 run 的 output.log |
| MuJoCo CPU 闭环 | **通过**（Q2-CPU、Q3-CPU、L-CPU） | "AMD compatibility matrix" run |
| EGL 离屏渲染 | **失败**（`EGL_DEVICE_OR_CONTEXT`） | 同上 |
| GPU 物理 | **不支持**（SAPIEN/PhysX 找不到 `libcuda.so`） | R-GPU/T2 run |

这些和本方案的分工一致：MI355X 上只跑纯 PyTorch 的 DP3 训练，不跑任何物理和渲染。Python 3.12 和本项目相同；集群上的 torch 2.9.1 与 5090 上的 torch 2.9.0 存的 checkpoint 可以互相加载。W&B 元数据里没有记录 ROCm 版本和每节点卡数，要在集群上执行 §3.3 的命令确认。

### 3.1c 2026-10-28 补充核查（WAM-Policy 2026-10-19/20 的 67 个 run，含元数据、requirements、日志）

| 项 | 值 |
|---|---|
| ROCm/HIP | 7.0.51831；torch `2.9.1+git8907517`（AMD 镜像 `/app/pytorch` 源码编译），triton 3.4.0 |
| 基础环境 | `/shared/yue/wamx/env/v3m/bin/python`（Python 3.12.3）；有 numpy 2.2.6、diffusers 0.36.0、huggingface_hub 0.36.2、safetensors 0.8.0、wandb 0.29.0、einops 0.8.2、pytest 9.1.1；**没有 zarr、tyro** |
| SLURM | 用户 `yue`，从 `/home/yue` 提交；用 `afterok` 串联阶段；单卡作业 8 CPU/128 GB，整节点 8 卡 64 CPU/512 GB，CPU 发布作业 8 CPU/64 GB；时限见过 16 h 与 36 h |
| 节点 | 8 × MI355X（288 GB），128 核，约 2.4 TB 内存，系统盘 930 GB（Ubuntu 24.04，内核 6.8.0-106） |
| GPU 隔离 | 有一次单卡作业里 W&B 看到 7 张卡，隔离不一定生效；我们的作业在未导出可见列表时把 `ROCR_VISIBLE_DEVICES` 设为 `SLURM_JOB_GPUS`，并核对 torch 看到的卡数 |
| 失败记录 | prepare 阶段多次 `HfHubHTTPError`（一次拉 9080 个文件）；GPU 训练本身无失败 |
| 训练设置 | DataLoader `num_workers=0`，`device="cuda"`，W&B 在线正常 |

操作员 2026-10-28 的 WAM-Policy 进度文档补充了现行做法：部署根目录 `/shared/yue/opd4`，每个作业先
`source env/rocm.sh`；token 存在 `.secrets/`（600），提交前 `unset HF_TOKEN WANDB_API_KEY`，由作业自己读取；
`/shared` 是 Isilon NFS（硬链接上限 127）；CPU 密集的验证走 sbatch，不在登录节点跑；节点占用控制在
2 个以内；AMD 上没有 EGL GPU 渲染和 MJWarp，仿真闭环很慢。旧环境 `/shared/yue/wamx/env/v3m` 可能已被清理。

据此的作业设计见 [AMD_RUN.md](AMD_RUN.md)：独立 venv 借用基础环境的 torch，只补装缺包且版本与集群一致
（`scripts/amd/constraints.txt`）；HF 请求有限重试；数据、HF 缓存与 MIOpen 缓存放节点本地盘；
每个阶段的状态与失败原因写入 W&B。5090 上用相同包版本（torch 换成 2.9.1 CUDA 版）完整演练过该作业。

### 3.2 环境要求

| 项 | 要求 |
|---|---|
| ROCm | **≥ 7.0**（MI355X 从 ROCm 7 起支持） |
| 运行方式 | 用集群现有的 ROCm 版 torch（W&B 记录里是 2.9.1），在激活的虚拟环境中 `uv pip install -e .`（不带 extra，不会装 mjlab）；或用 AMD 官方 `rocm/pytorch` 镜像 |
| Python | 3.12 |
| 依赖 | DP3 核心包 + `zarr<3`、`numba`、`diffusers`、`einops`、`hydra-core`、`wandb`、`huggingface_hub`；**不装 mjlab / mujoco** |
| 网络 | 能访问 `wandb.ai`、`huggingface.co`、`github.com`、`pypi.org` |
| 调度 | SLURM 或其他均可；每个 DP3 run 单卡 |

### 3.3 验收命令

```bash
amd-smi list        # 或 rocm-smi
python -c "import torch; print(torch.__version__, torch.version.hip, torch.cuda.is_available(), torch.cuda.device_count(), torch.cuda.get_device_name(0))"
python -c "import diffusers, zarr, numba, einops, wandb, huggingface_hub; print('deps ok', zarr.__version__)"
```

PyTorch 在 ROCm 上沿用 `torch.cuda` 这套接口，所以 `torch.cuda.is_available()` 为 True 就说明 GPU 能用。

---

## 4. 数据与实验管理（W&B + Hugging Face）

```text
5090                                   Hugging Face（私有仓库）              MI355X ×8
③ 采数据 ── 上传 ──────────────────▶  legmanip-demos（数据集）  ── 下载 ──▶ ④ DP3 训练（27 个 run）
                                                                              │
④ 闭环评估 ◀── 下载 ───────────────  legmanip-dp3（模型权重）  ◀── 上传 ──────┘
   │
   └── 成功率 ─────────────────────▶  W&B  ◀──────────────────────────── 训练曲线
② PPO 训练曲线、控制器 checkpoint ─▶  W&B（mjlab 默认就用 W&B）
```

| 东西 | 放哪 | 说明 |
|---|---|---|
| ② PPO 训练曲线、控制器 checkpoint | W&B | mjlab 默认 logger 就是 W&B，`play` 可以直接按 run 路径拉 checkpoint |
| ③ 专家数据集（每任务一个 zarr） | HF 数据集仓库（私有） | zarr 是成千上万个小文件，**先打包成单个 `.zarr.zip` 再上传** |
| ④ DP3 训练曲线 | W&B | DP3 原生支持 W&B |
| ④ DP3 权重 | HF 模型仓库（私有） | 只传 EMA 权重（safetensors，每个约 1G）；带优化器状态的完整 checkpoint 留在集群本地 |
| ④ 闭环评估结果 | W&B | 成功率表、评估视频 |

**可复现性约定**：DP3 run 的 W&B 配置里记录所用数据集在 HF 上的 commit hash；评估 run 里记录所用 DP3 权重的 commit hash 和控制器 checkpoint 的 W&B 路径。

**checkpoint 怎么选**：DP3 默认在训练中跑仿真评估、挑成功率最高的 checkpoint，但 MI355X 上没有仿真。改成**按固定 epoch 保存几个 checkpoint**，全部拉回 5090 统一评估。具体选哪几个 epoch、怎么汇总成一个数，在开始训练前定死。

**账号和网络**：
- 两台机器都由你自己登录：`wandb login` 和 `hf auth login`（旧版命令是 `huggingface-cli login`）。token 不经过我。
- 如果机器在国内，先确认能直接访问 `huggingface.co`。镜像站 `hf-mirror.com` 只能下载，不能上传。

---

## 5. 训练时长（5090短跑测量与外推）

| 作业 | 机器 | 时长 |
|---|---|---|
| ② 低层控制器 PPO（30 亿步） | 5090 | 当前4096环境配置外推约4.2小时/30亿步；调参、评估另计 |
| ③ 专家数据采集 | 5090 | 9 个任务合计不到 1 小时 |
| ④ DP3 训练（27 个 run） | 8× MI355X | 每卡 288G 显存，当前采用每卡一个作业；8卡最多8个run并发，27个run分批提交；时长待AMD实测 |
| ④ 闭环评估（27 组 × 100 回合） | 5090 | 1–2 小时 |

PPO依据：本项目5090上审查后实跑4096环境 × 300轮，每轮24步。排除前10轮后平均0.49803秒/轮，约19.7万步/秒；30亿步外推4.22小时。这是当前配置的吞吐测量，不代表该时长内必然收敛。

AMD训练时长尚未实测。当前训练器为单进程单卡；8卡按任务和seed并行提交独立SLURM作业，不会自动组成DDP。正式数据集规模下的吞吐和显存需在集群验收。

---

## 6. 需要你提供的

- **5090**：§2.3 四条验收命令的输出；我怎么连上去（在 Claude 应用里加 SSH 连接，或者在机器上直接运行 Claude Code）
- **MI355X**：ROCm 版本；能不能用 `rocm/pytorch` 镜像；调度方式；§3.3 验收输出
- **W&B**：entity / 项目名（两台机器都已 `wandb login`）
- **HF**：用哪个账号或组织建私有仓库（两台机器都已 `hf auth login`）
- **Git**：一个私有仓库，用来同步代码

## 2026-10-27 当前权重仓库约定

用户明确选择公开模型仓库 `Ethan-Xu-Deng/legmanip-weights`，保持公开。
控制器权重位于 `controller/<run-name>/`，DP3 权重位于 `planner/`。
上文私有模型仓库的建议由此覆盖；数据集仓库另行配置。
当前 W&B 记录写入 `junlinlong-the-university-of-sydney/WAM-Policy`，
控制器 run 名为 `leg-manip-controller-go2-seed0-日期时间`。
