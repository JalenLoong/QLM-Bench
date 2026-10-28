# AMD MI355X：DP3 Planner 训练操作说明

本文件给集群操作人员照做。一个 SLURM 作业完成全部流程：建环境 → 预检 → 2 个任务 × 3 个 seed
训练 → 上传 Hugging Face 并逐文件核验。作业内自带预检（真实数据上 2 轮训练、权重重载与推理），
不需要另提交冒烟作业。只用 PyTorch，不跑任何仿真（MuJoCo/mjlab），不需要 EGL 或 MJWarp。

## 1. 提交需要的信息

| 项 | 值 |
|---|---|
| 代码 | `https://github.com/JalenLoong/QLM-Bench`（公开），分支 `Leg-Manip`，目录 `baselines/leg_manip`，commit 由提交人给出 |
| 训练数据（只读） | HF 数据集 `Ethan-Xu-Deng/legmanip-demo`（公开），固定 revision `f096ba95637029f70b712abe7db5811081f5aaf7` |
| 权重上传 | HF 模型仓库 `Ethan-Xu-Deng/legmanip-weights`，路径 `planner/<tag>/` |
| W&B | entity `junlinlong-the-university-of-sydney`，project `WAM-Policy`，**以提交人账号 `dengxu1207` 记录** |
| 凭据 | 提交人提供的 `HF_TOKEN`（对 `Ethan-Xu-Deng/legmanip-weights` 有写权限）与 `WANDB_API_KEY`，存成凭据文件（见下） |
| 资源（默认） | 1 节点、6 × MI355X、48 CPU、384 GB、8 小时，分区 `mi355x`；卡数可调（见第 3 节） |

## 2. 操作步骤

```bash
# 凭据文件：只含提交人的两行，权限 600，不进 git、JSON 或命令行参数
#   HF_TOKEN=<提交人提供>
#   WANDB_API_KEY=<提交人提供>
chmod 600 /shared/yue/opd4/.secrets/legmanip.env

WORK=/shared/$USER/legmanip
mkdir -p "$WORK" && cd "$WORK"
git clone --branch Leg-Manip https://github.com/JalenLoong/QLM-Bench.git
cd QLM-Bench/baselines/leg_manip
git checkout <提交人给出的 commit>

unset HF_TOKEN WANDB_API_KEY                                   # 不让 token 随 --export=ALL 进作业
export LEGMANIP_ENV_SETUP=/shared/yue/opd4/env/rocm.sh         # 与 WAM 作业相同的 ROCm 环境
export LEGMANIP_BASE_PYTHON=<带 ROCm torch 的 python>          # 例如 WAM b1 的 $OPD_MODEL_PYTHON
export LEGMANIP_SECRETS=/shared/yue/opd4/.secrets/legmanip.env
sbatch scripts/amd/planner.sbatch
```

- `LEGMANIP_BASE_PYTHON` 须在加载 `LEGMANIP_ENV_SETUP` 后能 `import torch`，且 `torch.version.hip` 非空。
  作业只借用它的包（通过 `.pth`），不改动它。
- 作业先加载 `LEGMANIP_ENV_SETUP`，再读凭据文件，所以提交人的 token 会覆盖环境脚本里的团队 token；
  并清空 `PYTHONPATH`/`PYTHONHOME`，避免其他环境的包遮挡本作业的 venv。
- 若 W&B 登录的不是 `dengxu1207`，作业在训练前停止，不会在别人名下建 run。
- 若站点申请 GPU 不用 `--gres`，按站点写法在 sbatch 命令行指定（命令行参数覆盖脚本头）。

## 3. 卡数

驱动按作业实际分到的 GPU 数轮流分配 6 个 run，卡数只由 sbatch 参数决定，代码不用改：

| 申请 | 每卡 run 数 | 命令 |
|---|---|---|
| 6 卡（默认） | 1 | `sbatch scripts/amd/planner.sbatch` |
| 2 卡 | 3 | `sbatch --gres=gpu:2 --cpus-per-task=16 --mem=128G --time=12:00:00 scripts/amd/planner.sbatch` |
| 3 卡 / 1 卡 | 2 / 6 | 同上，改 `--gres` 与时限 |

作业运行中不能增减卡。需要换卡数时取消作业，用新的卡数、**同一个 tag** 重新提交：已完成的 run 跳过，
未完成的从最近一次保存（每 50 轮）续训。

## 4. 作业做什么

| 阶段 | 内容 | 失败时 |
|---|---|---|
| setup | 在 `$WORK/env/legmanip-amd` 建独立 venv：借用基础 python 的 torch 等包，只补装缺的包（`scripts/amd/constraints.txt`，版本与集群一致） | 作业退出，原因写入 W&B |
| environment | 记录 torch/HIP、包版本、GPU 可见性；核对 GPU 数与 SLURM 分配一致；每张卡做一次矩阵乘 | 作业退出 |
| credentials | 核对 W&B 账号为 `dengxu1207`、HF token 能写上传仓库 | W&B 账号不对：退出；HF 无写权限：继续训练，上传时再失败 |
| data | 下载固定 revision 的两个数据集，核对 zip SHA-256 与内容指纹 | 作业退出 |
| tests | 运行不依赖仿真的单元测试 | 作业退出 |
| preflight | 真实数据上训练 2 轮，重载 EMA 权重并推理，检查输出有限 | 作业退出 |
| train | 6 个 run 各 500 轮，每 50 轮存完整状态 | 其余 run 继续，完成的照常上传 |
| publish | 上传 EMA 权重（每 run 第 250/375/500 轮各一份）、日志、清单到 HF，逐文件核对 SHA-256 | 权重留在 `$WORK/runs/<tag>`，可单独补传 |

HF 缓存、解压后的数据、MIOpen 缓存和预检输出放节点本地 `/tmp`，作业结束删除；共享盘
（Isilon NFS）上只有 venv、训练输出和日志，不做硬链接和文件锁。

## 5. 看结果

- **W&B**（`WAM-Policy`）：分组 `planner-dp3-20261029`。`dp3-pipeline-dp3-20261029-run` 记录每个阶段的状态与
  失败原因；6 个训练 run 名为 `planner-<任务>-seed<k>-dp3-20261029`。
- **HF**：`Ethan-Xu-Deng/legmanip-weights` 的 `planner/dp3-20261029/`，含 `manifest.json`（每个文件的 SHA-256）
  与 `job_report.json`。
- **集群本地**：`$WORK/runs/dp3-20261029/job_report.json` 与 `logs/`；SLURM 输出在提交目录
  `legmanip-dp3-<作业号>.out`。

## 6. 出问题时

- **超时、被中断或部分 run 失败**：用同一命令重新提交，同一个 tag 自动续训。
- **只差上传**（例如 HF token 权限不对）：修正凭据文件后提交不占 GPU 的上传作业（与第 2 节同样的环境变量）：
  `sbatch scripts/amd/publish.sbatch`。不要在登录节点运行。
- **换一批新实验**：提交前 `export LEGMANIP_TAG=<新名称>`，输出与上传路径随之改变。

## 7. 预计用量

5090 上实测单 run 每轮约 6 秒（2.55 亿参数，显存约 8 GB），一张卡同时跑 3 个 run 时每个约 18 秒/轮。
6 卡默认配置每卡 1 个 run，按 1–2 小时估计；2 卡约 3–5 小时。上传约 18 GB（每份 EMA 权重约 1 GB），按集群实测约 10 MB/s 计约 30 分钟。
`$WORK/runs/<tag>` 约占 115 GB（每 run 含 4 GB 的 `latest.pt` 和三份 `training_epoch*.pt`）；
上传核验通过后，`*.pt` 只在需要续训时有用。
