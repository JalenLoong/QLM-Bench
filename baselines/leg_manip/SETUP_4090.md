# RTX 4090 机器环境配置需求（Leg-Manip）

这台机器负责：写代码调试、② 低层控制器 PPO 训练、③ 专家数据采集、④ DP3 闭环评估。DP3 训练放 MI355X（见 ENV_SETUP.md §3）。

**你只需要配好第 1–4 节（系统层）**，Python 环境由项目里的 `uv.lock` 一条命令装出来（第 5 节）。

> 版本号来自我在本地笔记本（RTX 4060 8G，驱动 595.99）上实际装通、跑通的环境（2026-10-26）。4090 上还没跑过。

---

## 1. 硬件

| 项 | 要求 |
|---|---|
| GPU | RTX 4090 48G（首选）。如果是 RTX 4080 16G 也能用，见第 8 节要调小的地方 |
| CPU | ≥ 16 核（GPU 物理不怎么吃 CPU） |
| 内存 | ≥ 64 GB |
| 磁盘 | **200 GB**（最少 120 GB），放在关机不丢的数据盘上 |

## 2. 系统和驱动（需要 root）

| 项 | 要求 | 检查 |
|---|---|---|
| 系统 | Ubuntu 22.04 或 24.04，x86_64。云平台镜像选干净的 **ubuntu24.04** | `lsb_release -a` |
| NVIDIA 驱动 | **≥ 580**。原因：warp-lang 1.18 的 wheel 用 CUDA 13.4 编译，官方要求 R580 及以上；torch 2.9.0 本身要 ≥ 570 | `nvidia-smi` |
| CUDA toolkit | **不需要装**。torch 和 warp 的 wheel 都自带运行时 | — |

```bash
sudo apt update
sudo apt install -y git curl tmux ffmpeg libegl1 libgl1 libglib2.0-0
```

`libegl1` / `libgl1` 只用于无显示器时录视频。点云采集用的是 MuJoCo Warp 的 CUDA 光线追踪相机，不依赖 EGL。

## 3. uv（不需要 root）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

uv 会自动下载 Python 3.12，不需要另装 Python 或 conda。

## 4. 网络和账号

需要能访问：

| 地址 | 用途 |
|---|---|
| `pypi.org`、`files.pythonhosted.org` | 所有 Python 包，包括 torch（PyPI 上的 torch 2.9.0 就是 CUDA 12.8 版） |
| `github.com` | 拉代码；uv 下载 Python 解释器 |
| `huggingface.co` | 上传专家数据、下载 DP3 权重（国内注意：镜像站 `hf-mirror.com` 只能下载、不能上传） |
| `api.forge.coreweave.com` | W&B。新版 wandb（0.31）默认登录这个地址，不是 wandb.ai |

**不需要** `download.pytorch.org`（本机测过这个源只有约 2 KB/s，所以项目改成从 PyPI 装 torch）。

账号由你自己登录，token 不经过我：

```bash
cd ~/legmanip_ws/Leg-Manip
uv run wandb login     # 在 https://forge.coreweave.com/wandb/authorize 拿 key
uv run hf auth login   # Hugging Face，要有写权限的 token
```

## 5. 项目环境

代码我会推到你给的私有 Git 仓库，之后：

```bash
mkdir -p ~/legmanip_ws && cd ~/legmanip_ws
git clone <私有仓库地址> Leg-Manip
cd Leg-Manip
uv sync --frozen --extra sim
```

`--extra sim` 会装上仿真相关的包；`--frozen` 表示严格按 `uv.lock` 安装。锁定的关键版本：

| 包 | 版本 |
|---|---|
| Python | 3.12 |
| torch | 2.9.0（CUDA 12.8） |
| mjlab | 1.6.0 |
| mujoco / mujoco-warp | 3.11.0 / 3.11.0 |
| warp-lang | 1.18.0 |
| rsl-rl-lib | 5.4.2 |
| diffusers | 0.42.0 |
| zarr | 2.18.7（必须 2.x） |
| huggingface_hub | 2.3.0 |
| wandb | 0.31.0 |

DP3 的核心代码已经内置在项目里（`src/leg_manip/planner/dp3/`），不需要另外装 DP3 仓库，也不需要 pytorch3d。

## 6. 验收（配好后把输出发我）

都在 `~/legmanip_ws/Leg-Manip` 下执行：

```bash
# 1) 驱动和 GPU
nvidia-smi
uv run python -c "import torch, warp as wp; wp.init(); print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

```bash
# 2) 单元测试（轨迹库等）
uv run pytest -q
```

```bash
# 3) 低层控制器训练冒烟：4096 个并行环境跑 20 轮，记下终端里的 "Iteration time"
uv run train LegManip-Track-Go2 --env.scene.num-envs 4096 --agent.max-iterations 20 --agent.logger tensorboard --log-root logs/smoke
```

```bash
# 4) 任务场景 + 深度相机 + 点云（按按钮、关洗碗机）
uv run python scripts/check_manip_env.py
```

```bash
# 5) W&B 和 HF 能写
uv run python -c "import wandb; print(wandb.Api().viewer.username)"
uv run hf auth whoami
```

第 3 步的参考：本地 4060 笔记本上，1024 个环境每轮约 0.67 秒（每轮 24 步）。4090 跑 4096 个环境每轮的耗时，乘以约 3 万轮，就是论文规模（30 亿步）的训练时长。

## 7. 跑长任务

训练和采数据都用 `tmux` 开会话再跑，断开 SSH 不会中断。日志写到项目的 `logs/`（已在 `.gitignore` 里）。

## 8. 如果是 RTX 4080（16 GB）

- 低层训练：4096 个环境大概率放得下（本地 8 GB 的 4060 跑 1024 个环境没有问题），放不下就用 `--env.scene.num-envs 2048`。
- 采数据和评估：每批并行环境数从 100 降到 50。
- 其余要求不变。
