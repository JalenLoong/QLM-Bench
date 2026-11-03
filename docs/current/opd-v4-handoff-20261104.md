---
id: QLM-OPD-V4-HANDOFF-20261104
type: current-status
status: accepted
related_work: [OPD-021, OPD-022]
source_map:
  - src/qlm_bench/backends/mujoco/training_control.py
  - src/qlm_bench/backends/mujoco/training_compatibility.json
---
# QLM quadrupedal OPD 当前交接状态（2026-11-04）

本仓库 `training/opd-v4-streaming-cpu` 配套 WAM 的 `opd/v4_Streaming-OPD_on_WAM-Policy`。跨仓库状态、tiny smoke 报告、AMD 命令框架和待办统一维护在
[WAM 2026-11-04 交接页](../../../WAM-Policy-opd-v4/docs/current/opd-v4-handoff-20261104.md)；上一版见 [2026-10-29 交接页](opd-v4-handoff-20261029.md)。

OPD-021（本地 commit，未 push）：WAM 改为 OPD-v5.0 Regression-anchored Streaming-OPD（同噪声 teacher ODE 终点回归，删除 fake critic，
[ADR-0008](../../../WAM-Policy-opd-v4/docs/decisions/opd-v4/ADR-0008.md)）。QLM 只同步身份：`training_control.DESIGN` 改为
`opd-v5-regression1-2-900s-v1`，`training_compatibility.json` version 改为 `regression1-2-900s-v1`，运行时指纹随之改变（WAM `compatibility.json` 的
`qlm.runtime_sha256` 同步）。physics、RAMBO、reset deck、train800 pool、9 任务调度、视频 case、socket RPC 均不变；release 响应的 `training` 字段不再含
`fake_updates_successful`（QLM 从未读取）。

teacher 作 actor 的 offline target cache 采集（WAM `launch-cache`）复用同一 worker、schedule 与 profile；`offline_only` 的训练不启动 QLM worker。
本地验证：QLM `pytest -q` 571 passed / 15 skipped；`scripts/check_governance.py --peer-root ../WAM-Policy-opd-v4` 通过。AMD 未执行。

OPD-022（本地 commit，未 push）：WAM formal attempt 的 rank 0 在每个 checkpoint 点后台上传 `students/step_N/{raw,ema}` 到 HF（ledger
`publication/periodic.json`），publish 只上传最终 student 并引用周期导出；WAM `engine.py` 的挂钩为 logging-only，WAM runtime 指纹重算并把 OPD-021 指纹登记为等价。
QLM 代码、`training_compatibility.json` 与 `runtime_contract()` 不变，本仓库只镜像 registry 与 ChangeSpec/ExecPlan。管理员需让 formal 作业的 GPU 节点拿到写权限 `HF_TOKEN`。
