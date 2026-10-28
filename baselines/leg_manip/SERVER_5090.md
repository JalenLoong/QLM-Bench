# 5090 部署与验收记录

日期：2026-10-26（Australia/Sydney）。当前状态：上传、代码审查修复与工程运行验收已完成；本页为工程验收历史；当前正式训练状态见 `TRAINING_RUN.md`。

## 连接与环境

- SSH：`ssh ubuntu@<5090服务器IP>`
- 项目：`/home/ubuntu/mycode/Leg-Manip`，不是根目录 `/mycode`。
- 环境：复用项目 `.venv`，没有重装 Python 依赖或修改 `uv.lock`。
- GPU：RTX 5090，32607 MiB；16 vCPU，94 GiB RAM；Ubuntu 24.04。
- 驱动：580.178.04 Open Kernel Module。原闭源580模块在5090上报
  `requires use of the NVIDIA open kernel modules`，已由Ubuntu包切换到同版本
  `nvidia-driver-580-open`；重新加载模块后识别GPU，无需重启。
- torch 2.9.0+cu128、mjlab 1.6.0、mujoco/mujoco-warp 3.11.0、warp-lang 1.18.0；
  CUDA矩阵运算、Warp初始化和161个包的兼容性检查通过。

操作入口：

```bash
export PATH="$HOME/.local/bin:$PATH"
cd /home/ubuntu/mycode/Leg-Manip
tmux attach -t legmanip-verify
```

已有环境的验证用 `uv run --no-sync ...`，避免无意重解析环境。初次创建新NVIDIA
环境才使用 `uv sync --frozen --extra sim`。

## 自动关机

已按用户要求注释 `/home/check_resolv.sh` 内唯一的 `sudo shutdown -h now`。
备份：`/home/check_resolv.sh.bak.20261026T042636Z`。`bash -n`通过；用户crontab
仍每分钟执行原脚本的其余检查。此修改只禁用该脚本触发的关机，不涉及云平台策略。

## 审查前的运行证据

远端日志在 `/home/ubuntu/mycode/deploy-5090/`；本地留存
`outputs/deploy-5090/baseline-evidence.tar.gz`。

| 项目 | 结果 |
|---|---|
| 源码与运行Go2模型 | 87文件逐项SHA-256匹配 |
| 单元测试 | 15 passed |
| 两个任务的相机/点云 | 均PASS；每任务16/16环境可见物体 |
| PPO短训练 | 4096环境 × 100轮，退出0 |
| 默认DP3模型 | 约255M参数，4轮训练、EMA保存和加载通过 |
| 点云采集/闭环 | debug数据采集和4回合闭环可运行；成功0/4、跌倒0/4 |

以上使用未收敛控制器与显式 `--keep-failed` 调试数据，只证明管线可运行。
不能用来证明专家成功率或论文效果。审查后的控制器高度语义会更新，旧权重须重训。

## 审查后的最终验收

| 项目 | 实测结果 |
|---|---|
| 代码与模型上传 | 原始108MB包SHA-256一致；运行模型、16个网格、CAD和论文均到位 |
| 单元测试 | 本地94 passed；服务器94 passed（9.59秒） |
| 风格检查 | lint、format检查通过 |
| 相机/点云 | 按按钮、关洗碗机均PASS，每任务16/16可见 |
| 修正版控制器 | 4096环境 × 300轮从头训练通过；观测version 2；非收敛权重 |
| 默认255M DP3 | 两任务各4轮训练、EMA保存加载通过 |
| GPU续训 | 按按钮从epoch 2恢复至epoch 4通过；CPU测试另验证逐项精确一致 |
| 多回合评估 | 每任务、每checkpoint 8回合，seed 1000/1004；均成功0、跌倒0 |
| 按钮内部碰撞 | 原生物理的5N按压及弹簧回位回归通过；机器人接触保持启用 |
| 终端状态记录 | GPU上重置前采样与禁用auto-reset的物理参考逐项一致 |
| 最终场景管线 | 修正按钮后重新采数据、轻量DP3训练与8回合评估通过（成功仍0） |
| wheel打包 | 成功；含Go2 XML、16个网格、Go2/DP3许可证；CAD按约定排除 |

审查修复记录见 `CODE_REVIEW.md`。运行日志在远端
`/home/ubuntu/mycode/deploy-5090/reviewed/`、`final/`，本地保留验收证据包。
`legmanip-verify` tmux会话保留，验收进程已结束；新的正式训练使用独立tmux，见 `TRAINING_RUN.md`。

## 低层训练用时

修正版5090短跑300轮，去掉前10轮后平均0.49803秒/轮；4096环境 × 24步/轮，约19.7万步/秒。
30亿步折算4.22小时/次，不含首次编译、评估和调参，也不保证在该时间内收敛。

## 硬件分工

| 算法部分 | 运行位置 | 输出 |
|---|---|---|
| ① 轨迹参数化 | 纯torch，两边可用，无单独训练 | 31维参数与目标轨迹 |
| ② PPO + 并发估计器 | 5090 | 通用控制器checkpoint |
| ③ 专家示范采集 | 5090 | 每任务100条成功示范、200帧/条的zarr |
| ④ DP3离线训练 | AMD MI355X | 每任务/seed的EMA权重和续训状态 |
| ④ 闭环评估 | 5090 | 固定场景种子下的成功率、摔倒率 |

AMD端使用ROCm版torch，不安装 `sim` extra，不导入仿真模块；当前按单卡单作业
提交任务/seed，未实现DDP。数据经HF私有数据集仓库传到AMD，EMA权重经HF模型
仓库回到5090，W&B记录实验。当前两个任务对应3个seed时共6个训练作业。

## 尚未完成的验收

- 控制器收敛、厘米级跟踪误差、专家成功率和正式成功示范数据。
- AMD/ROCm实机训练与NVIDIA回载测试，由用户在集群上执行。
- HF实际上传/下载、W&B在线记录：本轮没有使用账号令牌。
- 其余7个任务场景仍属于后续扩展，当前实现按按钮与关洗碗机。

驱动维护参考：[Ubuntu官方说明](https://ubuntu.com/server/docs/how-to/graphics/install-nvidia-drivers/)。
