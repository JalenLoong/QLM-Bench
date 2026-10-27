# Leg-Manip

在 Unitree Go2 + MuJoCo（mjlab）上复现 *Learning Visual Quadrupedal Loco-Manipulation from Demonstrations*（arXiv 2403.20328）。

- 方案：[PLAN.md](PLAN.md)
- 论文分析：[REPRODUCTION.md](REPRODUCTION.md)
- 5090 部署与验收：[SERVER_5090.md](SERVER_5090.md)
- 旧4090安装参考：[SETUP_4090.md](SETUP_4090.md)
- 整体分工与 MI355X：[ENV_SETUP.md](ENV_SETUP.md)
- 给 agent 的说明：[AGENTS.md](AGENTS.md)

## 完整流程

`<ctrl.pt>` 是第 1 步训出的控制器 checkpoint，`<user>` 是你的 Hugging Face 账号或组织。

### 1. 训练低层控制器 ②（5090）

```bash
uv run train LegManip-Track-Go2 --env.scene.num-envs 4096
# 日志与 checkpoint：logs/rsl_rl/legmanip_track_go2/<时间>/model_*.pt，W&B 项目 leg-manip
# 尚未登录W&B时，加 --agent.logger tensorboard；不要将token写进命令或代码。
```

### 2. 检查专家轨迹 ③（5090）

用真值参数开环执行，记录专家成功率，确认可以采足成功示范。不行就先检查控制器跟踪误差，再检查 `src/leg_manip/tasks/manip/specs.py` 的控制点。更换机器人后的结果不能直接等同于论文数字。

```bash
uv run lm-collect --task press_button --controller <ctrl.pt> --check-expert --num-envs 100 --max-rounds 1
uv run play LegManip-PressButton-Go2 --checkpoint-file <ctrl.pt>    # 可视化
```

### 3. 采集示范并上传 HF ③（5090）

每个任务 100 条成功示范，每条 200 帧。

```bash
uv run lm-collect --task press_button --controller <ctrl.pt> --num-demos 100
uv run lm-hub upload data/demos/press_button.zarr --repo <user>/legmanip-demos
```

### 4. 训练 DP3 Planner ④（MI355X，每个任务 × 3 个 seed）

在 50% / 75% / 100% 训练进度时各存一份 EMA 权重，然后上传 HF。

先激活集群现有的ROCm虚拟环境，在仓库目录执行 `uv pip install -e .`（不带extra）。
不要在这个环境执行项目的 `uv sync`，以免改动预装的ROCm torch。以下检查在申请到GPU
的计算节点运行，不能用登录节点的GPU可见性代替：

```bash
uv run --active --no-sync python -c "import torch; assert torch.version.hip and torch.cuda.is_available(); print(torch.__version__, torch.version.hip, torch.cuda.get_device_name(0))"
uv run --active --no-sync pytest -q tests/test_traj.py tests/test_planner_dataset.py tests/test_planner_training.py tests/test_planner_is_sim_free.py tests/test_hub.py
```

AMD只跑以上纯算法测试；全量pytest还包含依赖MuJoCo的仿真测试，应在5090运行。

```bash
# 在已经安装本项目的ROCm虚拟环境中运行；不要安装sim extra。
uv run --active --no-sync lm-train-planner --hf-repo <user>/legmanip-demos --hf-file press_button.zarr.zip --seed 0
# 只上传EMA推理目录；latest.pt和training_epoch*.pt是完整续训状态，留在集群。
for ckpt in outputs/planner/press_button/seed0/epoch*/; do
  uv run --active --no-sync lm-hub upload "$ckpt" --repo <user>/legmanip-dp3 --repo-type model --path-in-repo "press_button/seed0/$(basename "$ckpt")"
done
```

续训时重复原数据、模型、seed和训练参数，追加
`--resume outputs/planner/press_button/seed0/latest.pt`。`--num-epochs`是原计划的总轮数，
不是再训练多少轮。已有run目录不能无意覆盖；需要新实验时使用新seed或 `--out-root`。
训练集归一化只使用训练episode；验证episode不参与拟合。

当前按单卡单任务运行。两个任务 × 三个seed是6个独立作业，可分配到AMD集群的不同GPU；
当前没有DDP入口。集群实际ROCm/SLURM运行仍需单独验收，5090通过不能替代AMD验证。

### 5. 闭环评估 ④（5090）

```bash
uv run lm-hub download-dir --repo <user>/legmanip-dp3 --pattern "press_button/*"
uv run lm-eval --task press_button --controller <ctrl.pt> --planner <下载目录>/press_button/seed0/epoch0250 <下载目录>/press_button/seed0/epoch0500 --wandb-project leg-manip
uv run lm-eval --task press_button --controller <ctrl.pt> --expert   # 专家上限
```

任务名：`press_button`、`close_dishwasher`。

相机/支架采用项目CAD派生的Go2模型。代码审查修正了控制器绝对高度约定，旧的无版本
checkpoint不能用于当前控制器；需要重新训练。旧 `logs/local/`、`logs/server-smoke/`
里的短训权重和 `--keep-failed` 数据只用于历史冒烟，不是正式复现产物。

## 测试

```bash
uv run pytest -q
uv run python scripts/check_manip_env.py
```
