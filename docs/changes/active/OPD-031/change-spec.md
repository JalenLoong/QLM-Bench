---
id: OPD-031
type: change
status: active
source_map:
  - src/qlm_bench/backends/mujoco/training_control.py
  - src/qlm_bench/backends/mujoco/training_live.py
  - tests/qlm/test_opd_episode_schedule.py
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

runtime 指纹 `0666c125…` → `e0493ea7…`。WAM `compatibility.json` 的 `qlm` 块把旧值登记为等价（默认 profile 的值与调度不变），需用户以 code owner 身份认可。
`training_compatibility.json` 的文件清单不变。
