---
id: OPD-031
type: change
status: active
source_map:
  - src/qlm_bench/backends/mujoco/training_control.py
  - src/qlm_bench/backends/mujoco/training_live.py
  - tests/qlm/test_opd_episode_schedule.py
  - src/qlm_bench/backends/mujoco/runtime.py
  - tests/qlm/test_opd_training.py
  - docs/governance/opd-v4-work-registry.json
---
# ChangeSpec: OPD-031 M-OPD v1 的 AMD 正式链路（QLM 侧）

分支 `mopd/v1_M-OPD_on_RL-v4-experts`。主体在 WAM 同名分支（见 [WAM ChangeSpec](../../../../../WAM-Policy-mopd/docs/changes/active/OPD-031/change-spec.md)）。
QLM 一侧只为 M-OPD 的 cache 阶段加任务子集 profile：

- `training_control.profile(pool, tasks=None, max_active_per_task=2)`：默认仍是 9 个训练任务、每任务同时最多 2 个 episode。
  `tasks` 是按 `TRAINING_TASKS` 顺序的非空子集，配一个整数上限（≥ 2），例如 M-OPD 采集用 `[push_box, open_room_door]`、上限 8 / 2 = 4，
  8 个 worker 同时都能拿到 episode。`accepted`/`read_profile` 只接受这两种形状；9 任务 profile 的上限必须是 2。
- `EpisodeSchedule` 的并发上限从 profile 的 `max_active_per_task` 读（`reserve` 与 `validate`）；默认 profile 下取值仍为 2，行为不变。
- `training_live make-profile` 加 `--tasks`（逗号分隔）与 `--max-active-per-task`；`DESIGN`、horizons、`seed`、sampling 不变。

runtime 指纹 `0666c125…` → `e0493ea7…`（下文的渲染节奏改动后为 `df399db3…`）。WAM `compatibility.json` 的 `qlm` 块把旧值登记为等价（默认 profile 的值与调度不变）；`e0493ea7…` 后来也登记为等价。两项等价登记已获用户以 code owner 身份认可（2026-11-16，经主会话转达，用户原话“认可指纹等价登记”）。
`training_compatibility.json` 的文件清单不变。

## 训练 worker 的渲染节奏（2026-11-16 追加）

依据只读提速分析 `runs/audit/mopd-v1-speedup-analysis-20261116-v1/` 的方案 1：`runtime.py` 原样移植 RL-v4 分支已评审的
`MuJoCoRuntime.observation_ticks`（QLM-INFRA-006，默认 10，其他调用方不变），`training_live.run_worker` 在 `create_runtime` 之后关掉 observer
（`evaluation_observer=False`、`observer_clip=None`）并设 `observation_ticks=40`，与 RL-v4 scene worker 相同。闭环视频（`training_visualization.py`）
与评测路径不变。driver 仍在 tick%40 调 `state()`（惰性，未缓存时当场渲染），reset 与终止帧照旧；WAM `online.py` 只要求 40 tick 网格上的 4 帧，
`sensor_frame_ids` 只检查严格递增（QLM `live/protocol.py`、`live/history.py`），WAM 不读它。5090 CPU（LP=1）实测：push_box 每 chunk 7.5 → 1.75 s，
lift_basket 24.3 → 4.7 s，每 chunk 渲染 16 → 4 次，reset 帧与每个 40 tick 策略帧（各 13 帧）在改前改后逐位相同。
QLM 指纹 `e0493ea7…` → `df399db3…`，`e0493ea7…` 登记为等价（模型收到的帧、命令、时间戳不变，只有 frame id 的数值与 worker events 里的
observer 收据变）；WAM 指纹不变；`training_compatibility.json` 的文件清单不变。
