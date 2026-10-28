# AGENTS.md — Leg-Manip

## 交接结论（2026-10-27，Australia/Sydney）

**工程代码可运行，但控制器技能未复现成功。两轮训练均已结束，GPU空闲；
没有正在等待自动续训的作业。新训练、续训、扩大任务或启动AMD作业，必须先由用户决定。**

- 30000轮全范围跟踪：按钮专家1/100成功、洗碗机0/100；没有合格的正式示范数据。
- 修复奖励后2000轮近距离抬腿：3个评估seed × 左右前腿，六组均0%合格、操作脚100%接地。
- **2026-10-28诊断（未训练）**：该策略的各奖励项与零动作站立几乎相同，即什么都没学会。
  抬脚前必须先把重心移出操作脚（站立时约承担15%体重），而旧奖励在这段几乎平坦，
  只在离地瞬间跳升；物理上可行（脚本恒定姿态抬10cm、256环境0摔倒）。另查出Lift起点
  取自重置时悬空的足端，目标平均偏高2.9cm。已加连续“操作脚载荷占比”惩罚并修正起点，
  证据见 `outputs/diagnosis-20261028/`。用户确认后启动新短训（W&B k2w4yngg），第169轮按用户要求终止；终止前操作脚接地项由-0.45降到≈0，但只存了model_0.pt；随后按用户要求从零重跑为 `...-20261028-012627`（W&B df5yqprr）。
- **2026-10-28 Lift验收首次通过**：三seed×FL/FR均64/64合格，位置误差1.6–2.4cm、高度误差0.6–1.4cm、操作脚接地0%、提前终止0%；权重SHA `7fcf28de…16a6`，HF/W&B已核验。只代表近距离抬脚阶段，全范围跟踪与专家任务仍未验证。
- **全范围跟踪试训（本地，3000轮）失败**：不摔、操作脚抬对高度，但完全不走（20s机身位移约7.5cm），
  位置误差约87cm、三seed双腿0/64、专家0/100。缺朝目标移动的连续奖励。
- **试训由Claude自行迭代（用户授权，仅本地）**：试训2加 `base_approach` 后会走，验收每侧59–75%合格（需80%），
  专家按钮3%、洗碗机57%；试训3加精确定位项 `ee_pos_fine` 后验收通过（1.9–2.7cm），专家按钮94%、洗碗机95%，
  对照组纯加训仅2%/5%。试训4（正式抬腿权重→最终奖励，6000轮）通过，专家86%/90%。
  正式训练 `logs/leg-manip-controller-go2-seed0-20261028-052422/`（W&B k1pyz71z）已结束：跟踪门槛三seed双腿通过
  （62–64/64，1.9–2.5cm），HF/W&B已核验（model_5999 SHA `d76565bf…927e`）；但专家按钮64%、洗碗机75%
  （300回合），提前终止18–22%，几乎全是机身/大腿碰地；试训4同评估85%/88%、终止≤1.3%。未续训，下一步待用户决定。
- **用户选定试训4控制器（2026-10-28）**：只读包 `data/controller/leg-manip-controller-go2-seed0-20261028-042919-pilot4single/`
  （SHA `ab79fd00…ab29`，服务器与本地各一份，未上传）。**但示范采集被阻塞**：机器人起步即转身、侧对物体，
  头部相机（水平±43.5°）在<1s后看不到物体，示范帧可见率仅约3%。
  目录 `logs/leg-manip-controller-go2-seed0-20261028-022813-pilot/`，验收用 `python -m leg_manip.eval.track`。
- **朝向修复后的正式控制器（2026-10-28，当前选用）**：用户同意后加 `base_heading`（接近时朝向目标）与
  `base_heading_dir`（脚在目标0.25m内时机身对齐命令小腿方向），试训6通过事先固定的验收后正式训练
  `logs/leg-manip-controller-go2-seed0-20261028-145340/`（W&B `dfa5vhi5`，HF `controller/<run>/`，model_2999 SHA `212945db…fa71`，云端已核验）：
  跟踪门槛全过（2.3–3.5cm），专家按钮100%、洗碗机91%、终止0%、物体可见100%。
- **正式示范已采集并上传**：`data/demos/legmanip-demo-20261028-152457/`（5090），两任务各100条×200帧，
  全部帧有物体点云。已传到用户建的公开数据集仓库 `Ethan-Xu-Deng/legmanip-demo`（commit `f096ba95…`，
  `press_button.zarr.zip`、`close_dishwasher.zarr.zip`、数据集说明、`collections/<名称>/` 采集证据）；
  下载回来zip与zarr逐文件SHA一致，匿名下载后DemoDataset指纹与上传前相同。
  （同名的空**模型**仓库是建错类型留下的，未动。）下一步是AMD上的DP3训练与5090闭环评估
  （`lm-eval --planner`），须用户决定后再启动。
- **试训一律不上传W&B和HF**（用户2026-10-28规定）：用 `--agent.logger tensorboard`、`WANDB_MODE=disabled`，
  不设 `LEG_MANIP_HF_REPO`；只有用户指定的正式训练才上传。
- 最新本地/5090回归均151项通过；这仅证明实现和验收工具的测试通过，不代表策略学会。
- 首先阅读 [HANDOFF.md](HANDOFF.md)，再读 [TRAINING_RUN.md](TRAINING_RUN.md)。
- **GitHub比当前工作区旧**：`JalenLoong/QLM-Bench` 的 `Leg-Manip` 分支停在
  `6885590c872f2db483615dfdac969bdbe9cd038d`，尚无后来的奖励修复、Lift任务和验收器。
  最新代码位于本工作区和5090的 `/home/ubuntu/mycode/Leg-Manip`，不能仅从GitHub恢复最新状态。
- 本独立工作区尚无Git提交和remote。不要将它直接覆盖或强推为QLM-Bench仓库；
  同步团队分支时只更新 `baselines/leg_manip/`，保留其他代码和历史。

在 Unitree Go2 + MuJoCo（mjlab）上复现论文 *Learning Visual Quadrupedal Loco-Manipulation from Demonstrations*（arXiv 2403.20328）的算法四部分。

- **①** 轨迹参数化：有理 Bézier + SLERP + 操作腿 flag。
- **②** 低层控制器：PPO + 并发状态估计器。三腿行走，同时一条前腿跟踪轨迹。
- **③** 专家数据：用物体系专家轨迹 + 训好的控制器在仿真里采集点云示范。
- **④** 高层 Planner：DP3，由点云 + 本体状态预测世界系轨迹参数，再做闭环评估。

## 先读这些

| 文件 | 内容 |
|---|---|
| `HANDOFF.md` | 当前交接状态、源码版本差异、产物索引、接手顺序与未解问题；优先阅读 |
| `TRAINING_RUN.md` | 两轮真实训练、诊断、奖励修复、双侧验收及云端校验证据 |
| `REPRODUCTION.md` | 论文分析，包括 LaTeX 注释里挖出的超参 |
| `PLAN.md` | 复现方案、分阶段验收标准、默认的实现选择 |
| `SERVER_5090.md` | 当前5090部署、实测吞吐与验收状态 |
| `CODE_REVIEW.md` | 本次实现审查、修复和验证边界 |
| `SETUP_4090.md` | 旧4090安装参考 |
| `ENV_SETUP.md` | 整体硬件分工；MI355X 集群实况（来自 W&B）；HF / W&B 数据流 |
| `paper/` | 论文 PDF 与 LaTeX 源码 |

旧文档中的94项测试、等待启动、私有模型仓库及旧环境建议属于历史快照。
当前状态以本文件、HANDOFF、运行JSON与checkpoint校验值为准；progress按时间追加，不能只取较早记录。

## 硬件分工（重要）

- **NVIDIA（5090 32G）**：所有物理仿真和渲染，即 ② 训练、③ 采数据、④ 闭环评估。MuJoCo Warp / Warp 只支持 CUDA。
- **AMD MI355X（SLURM，分区 `mi355x`）**：只跑 ④ 的 DP3 训练，纯 PyTorch。集群上没有 libcuda、EGL 失败，**不能 import mjlab / mujoco_warp**。
- 两边通过 **Hugging Face**（数据集、权重）和 **W&B**（实验记录）交换数据，不直连。
  用户在2026-10-27明确指定 `Ethan-Xu-Deng/legmanip-weights` 为公开模型仓库；
  保持用户选择的可见性，不强制改为私有。数据集仓库单独配置。

因此 `leg_manip.planner` 里的代码**不能 import 任何仿真相关模块**（mjlab、mujoco、warp、`leg_manip.tasks`、`leg_manip.collect`、`leg_manip.controller`）。

## 环境与常用命令

总是用 `uv run`，不要直接调 `python`。现有5090使用 `uv run --no-sync` 复用环境；
不要为检查项目重新安装依赖。以下命令是检查/评估入口，不构成启动训练的授权。

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CUDA_VISIBLE_DEVICES='' uv run --no-sync pytest -q
uv run --no-sync ruff check src tests scripts
uv run --no-sync ruff format --check src tests scripts
uv run --no-sync list-envs
uv run --no-sync python -m leg_manip.eval.lift --checkpoint <controller.pt> --out <result.json>
uv run --no-sync lm-eval --task press_button --controller <controller.pt> --expert
uv run --no-sync python scripts/check_manip_env.py
```

`list-envs` 在当前版本返回任务数量作为退出码；已打印任务列表时不要直接据非零码判故障。
仅新建NVIDIA环境且获得同意后用 `uv sync --frozen --extra sim`。
AMD激活既有Python3.12/ROCm环境后用 `uv pip install -e .`（不带sim extra），
运行用 `uv run --active --no-sync`；不能把全量仿真pytest当作AMD验收。

`train` / `play` / `list-envs` 是 mjlab 的入口。本项目通过 `pyproject.toml` 里的 entry point `mjlab.tasks` 注册任务（见 `src/leg_manip/tasks/__init__.py`）。

## 目录

```text
src/leg_manip/
  traj/            ① 有理 Bézier、SLERP、TrajParams（31 维向量）、yaw 坐标变换；纯 torch
  assets/go2/      Go2 MJCF（由 menagerie 派生，见文件头注释）+ mjlab EntityCfg / 执行器；
                   含按 CAD 建模的深度相机支架和相机 head_depth（见 CAMERA_MOUNT.md）
  assets/objects.py  按钮面板、洗碗机（程序化 MjSpec）
  tasks/track/     ② 低层环境：命令项 FootTrajectoryCommand、观测、奖励、滤波动作、PPO 配置
    lift.py       独立近足端抬腿阶段 LegManip-Lift-Go2；默认上限2000轮，不是完整轨迹任务
  learning/        ② EstimatorActorModel、PPOWithEstimator（rsl_rl 子类）
    cloud_logging.py / runner.py  项目内W&B兼容适配、checkpoint同步HF、上传回执
  tasks/manip/     ③④ 任务：ManipTaskSpec（specs.py，含专家轨迹和成功判据）、专家命令、
                   机器人/物体重置、相机点云（perception.py）
  collect/         ③ 同步 rollout 循环（rollout.py，采数据与评估共用）、lm-collect
  eval/            ④ 闭环评估 lm-eval
    lift.py       低层左右前腿行为验收，只推理；退出0=通过，2=未达标
  controller.py    加载控制器 checkpoint 用于推理
  demo_io.py       示范数据的 zarr 格式（不依赖仿真）
  hub.py           HF 上传 / 下载 lm-hub（zarr 目录自动打包成 .zarr.zip）
  planner/         ④ 数据集、DP3 构建与 checkpoint、训练 lm-train-planner、推理封装；
                   不依赖仿真（有测试保证）
  planner/dp3/     DP3 核心代码（vendored，MIT，见目录内 LICENSE 与 __init__ 说明）
scripts/           独立脚本（冒烟检查；cad/ 下是从 STEP 装配提取相机位姿的脚本）
tests/             pytest
third_party/       mjlab、DP3、menagerie 的参考 checkout，只读，已 gitignore
```

## 约定

- **代码风格**：行宽 88；注释和 docstring 用英文；尽量不用局部 import；测试写成函数，不用类。
- **坐标系**：
  - 物体系：原点在物体前表面中心的地面上，+x 指向物体内部，机器人从 -x 方向接近。
  - 世界系：sim world。给 Planner 的数据一律减去 `env.scene.env_origins`，即 env 系。
  - 控制器命令：机器人 heading 系（机身位置 + yaw），高度保持绝对。
- **轨迹参数向量（31 维）**：`[flag | 6 个控制点 ×3 | 6 个 log 权重 | 起始方向 3 | 终止方向 3]`。flag 0 = FL，1 = FR；"朝向"指小腿方向单位向量（膝 → 足）。
- **mjlab 重置时序的坑**：重置流程里命令项先于 `mj_forward` 执行，这时读到的机身 / 足端 / 物体位姿还是上一回合的。采样参数要放到 `_sample_params`（会被推迟到前向运动学之后执行），不要在 `_resample_command` 里直接读位姿。
- **程序化 MjSpec**：MuJoCo 默认角度单位是度，必须设 `spec.compiler.degree = False`。
- **geom margin**：Go2 MJCF 不能有非零 geom margin（和 MuJoCo Warp 的 multi-CCD 冲突）。
- **相机与支架以 CAD 为准**：用户确认之后所有仿真都用 `go2.xml` 里按 STEP 装配建的支架和 `head_depth` 相机（机身系 (0.323, 0, 0.328) m，下倾 30.5°）。改动前先看 `src/leg_manip/assets/go2/CAMERA_MOUNT.md`，改完同步更新它。
- **奖励**：mjlab 的奖励会乘以 dt。改权重前先看 `src/leg_manip/tasks/track/env_cfg.py` 里的注释（为什么偏离论文值）。
- **当前奖励修复**：目标高度高于env原点5cm时，操作脚着地不能拿支持奖励，并有-0.5代价；
  free_gait权重2→0.3，正确静态三腿支撑允许得分；高度Gaussian std0.5→1.0。
  这是本项目的显式适配，不是已知的原论文超参数。修复后短训仍失败，不能把漏洞视作全部根因。
  2026-10-28再加 `manip_foot_load`（权重-2）：目标>5cm时惩罚操作脚占四脚竖直反力的比例，
  给“先转移重心再离地”这段提供连续信号；Lift起点改为悬空足端正下方的地面
  （env原点+0.022m）。是否有效须以新短训的行为验收为准。
- **足端接触偏软**：Go2足端沿用menagerie的solimp(0.015,1,0.022)但已去掉margin，
  站立时陷地10–12mm、机身降到约0.23m（重置生成高度0.30–0.33m）。暂未改动，改前先讲方案。
- **Lift验收**：seed1000/1001/1002，各FL/FR64环境；每侧合格率≥90%、提前终止率≤5%。
  单环境末2秒均值：3D误差≤5cm、高度误差≤3cm、操作脚接地≤10%。不得为了过关改门槛。
- **评估重置**：mjlab关闭auto_reset后不能继续step已终止的环境。Lift评估保留auto_reset，
  永久累计首次提前终止标记；替代回合不能算成功，终点重置后的数据不能污染末段统计。
  `fall_rate`统计所有提前终止（含身体触地），不只姿态摔倒；误差均值只含存活原回合。

## 不要做的事

- 不要修改 `third_party/`（只读参考）；需要改 DP3 就改 `src/leg_manip/planner/dp3/` 并在其 `__init__` 里记录改动。
- 不要提交 `logs/`、`data/`、`outputs/`、`wandb/` 和 CAD 文件（已在 `.gitignore` 里）。
- 不要把 W&B / HF 的 token 写进代码或日志；两台机器都由用户自己 `wandb login`、`hf auth login`。
- 改动环境配置前，先跟用户讲清方案、得到同意再动手（用户的工作习惯）。
- 不要覆盖 `logs/<run>/source/`、已发布checkpoint或历史验收JSON。新实验使用新名称与目录。
- 不要因pipeline.exit=0、测试通过或权重有限就报告技能合格；必须检查对应行为验收结果。
- 不要自动重启已删除的监测或依据历史启动命令续训。训练启动必须有新的用户指令。
- 不要改动团队仓库里 `baselines/leg_manip/` 之外的代码；本次交接未授权GitHub推送或合并。

## 当前环境、产物与未完成事项

- 当前服务器：`ubuntu@<5090服务器IP>`，项目 `/home/ubuntu/mycode/Leg-Manip`，RTX 5090 32G。
- Python环境复用；驱动已修复为580.178.04-open。用户指定脚本的自动关机命令已注释。
- 四部分已有实现，当前两个任务为按按钮与关洗碗机。审查修复详见 `CODE_REVIEW.md`。
- Python3.12；torch2.9.0、mjlab1.6.0、MuJoCo/mujoco-warp3.11.0、Warp1.18.0、
  rsl-rl5.4.2、wandb0.31.0。现有环境和驱动已验收，不重建。
- 本地与5090均131项回归通过，lint/format通过；历史300轮PPO、DP3、闭环、续训冒烟
  只作工程证据，不能取代两轮真实训练已失败的行为结论。
- 控制器观测契约为version 2（绝对高度）；旧无版本checkpoint被拒绝，须重训。
- DP3已支持训练集专用归一化、数据校验、原子完整checkpoint和显式 `--resume`；
  AMD仍采用单GPU单作业，按任务/seed并行。HF只传 `epoch*/` 下的EMA推理文件。
- W&B账号 `dengxu1207`，entity `junlinlong-the-university-of-sydney`，项目 `WAM-Policy`。
  已结束run：`sdtnyowv`（30000轮）、`kmey8ymz`（2000轮Lift，失败）、`k2w4yngg`（用户第169轮终止）、
  `df5yqprr`（2000轮Lift，载荷奖励，门槛通过）。
- HF公开模型仓库 `Ethan-Xu-Deng/legmanip-weights`，控制器放 `controller/<run-name>/`；
  云端权重和最终验收结果已在线核验。正式数据集尚未形成，不把调试数据用于效果结论。
- 两个完成监测 `leg-manip-5090`、`leg-manip` 已删除。SSH复用socket仅临时有效，
  不把它当永久凭据，不在交接文档里写密码/token。
- 未完成：用新奖励训练全范围跟踪控制器、专家成功率与正式示范、AMD实机验证、
  正式DP3训练与完整闭环、其余7个任务。新短训在
  `logs/leg-manip-controller-go2-seed0-20261028-011755/`于第169轮被用户终止；重跑 `logs/leg-manip-controller-go2-seed0-20261028-012627/` 已通过Lift门槛。
- 服务器SSH只用密钥；公钥失效时请用户自己运行ssh-copy-id，不使用聊天中的密码。
  非交互SSH里uv在 `~/.local/bin`。GitHub推送一律由用户亲自操作。
- 完整流程命令见 `README.md`。
