---
id: QLM-OPD-V4-HANDOFF-20261104
type: current-status
status: accepted
related_work: [OPD-021, OPD-022, OPD-023, OPD-024, OPD-025, OPD-026, OPD-027, OPD-028, OPD-029]
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

OPD-023（本地 commit，未 push）：WAM 的 Slurm 链变为 prepare → single-smoke → eight-smoke → cache → formal → publish，cache 在 `site.cache_root/<cache key>/` 共享、
核验即复用；`submit-matrix` 一次提交四个 OPD-v5.0 实验（offline_only 2000 步、streaming、collect_once、streaming 且 `action_target_plan=student`），第一条链建 cache，
其余三条等它并复用。QLM worker 在 cache stage 中的调用与 `launch-cache` 相同；QLM 代码与 runtime 指纹不变，本仓库只镜像 registry 与 ChangeSpec/ExecPlan。

OPD-024（本地 commit，未 push）：`submit-matrix` 默认串行（后一条链等前一条的 publish job，一条路线一个八卡节点）；offline_only 的 run 改为 prepare → cache → single-smoke → eight-smoke → formal → publish，因为它没有 stream，smoke 要用 cache。QLM 代码与 runtime 指纹不变，本仓库只镜像 registry 与 ChangeSpec/ExecPlan。

OPD-025（本地 commit，未 push）：AMD 首次提交的 cache 在最后一次握手被 `live/runner.py` 的 stop-reason 白名单拒绝。修在 WAM 一侧：只发出白名单内的值，QLM 代码与 runtime 指纹 `0666c125…` 不变；本仓库加测试锁定白名单。

OPD-026（本地 commit，未 push）：变更全部在 WAM（cache 逐轮写盘、失败信息进 W&B、分层 held-out、八进程测试）。QLM 源码与 runtime 指纹 `0666c125…` 不变；WAM 的八进程测试用本仓库真实的 `SynchronousDriver`。训练 horizon 与评测 horizon 的差异待用户决定，本仓库未改。

OPD-027（本地 commit，未 push）：WAM launcher preflight 的 loopback 端口探测设 `SO_REUSEADDR`，与本仓库 `RPCServer.allow_reuse_address` 一致（第二次 AMD 提交的
第一次 single-smoke 在 cache 作业结束 37 s 后因 TIME_WAIT 被误判端口占用）。同一 run 的 formal 在第 3 次 update 后被外部 SIGTERM 终止，指标正常，根因待
`sacct`；细节见 WAM 2026-11-04 交接页的 OPD-027 段。QLM 源码与 runtime 指纹 `0666c125…` 不变，只镜像 registry 与记录。

OPD-028、OPD-029（本地 commit，未 push）：变更全部在 WAM（纯 streaming anchor 消融；追认登记 `8277c28`）。QLM 源码与 runtime 指纹 `0666c125…` 不变，只镜像 registry 与记录。

