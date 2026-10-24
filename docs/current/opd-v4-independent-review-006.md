---
id: OPD-V4-INDEPENDENT-REVIEW-006
type: current-design
status: accepted
related_work: [OPD-006]
source_map: []
---
# OPD-006：mixed-task OPD-v4 独立代码审核

2026-10-24，审核对象为现有 WAM-Policy-opd-v4 / QLM-Bench-opd-v4 的未提交 working-tree 实现，
对应会话 01a15ef6-edfd-7be1-b77e-1a24ab5d6636 的 OPD-005 交付；不是 native LingBot/LIBERO 路线。

发现并修复两项问题。在本轮检查的 Stage2 启动、资源加载、调度和恢复链路中，未发现必须保留调试机
原调试机的用户目录绝对地址 地址或 `.git` 的硬依赖。该结论有异路径 CPU 检查支持，但不等于 AMD 实测通过。

## 已修复问题

| ID | 级别 | 触发与影响 | 修复与证据 |
|---|---|---|---|
| R1 | P1 | 某 task 已消费79个 reset，最后一个 candidate 被另一条 stream 预留；它的 confirmed starts 仍最少、占用数仍低于2。原调度器再次选中该 task 后报 `Reset deck awaits outstanding reservations`，使正常并发训练退出。 | 在同一 SQLite 事务中按“并发数未满且有可用 candidate”筛选 task，再按原 confirmed-start/cursor 规则选择。只有选中已耗尽的 deck 才递增 cycle；不提前消费 pending、不重复 candidate。新增真实80-item deck 边界测试，覆盖失败 reset 取消后仍可领取原 candidate。修复前失败保存在 scheduler-before.log；修复后通过 QLM suite。 |
| R2 | P2 | `preflight` 的 `inspect-profile` 使用配置的 control timeout，但后续另一次完整 pool 扫描经 `probe` 仍固定120秒。迁移到较慢存储或失去 hardlink 去重的展开副本后，即使已调大配置，也可能在启动前被过早终止。 | 抽出同一 `control_timeout` 解析/校验函数，完整 pool 扫描与控制 CLI 均遵循 `control_timeout_s`，缺省回退 `rpc_timeout_s`。短环境 import probe 继续有独立120秒上限。回归测试复现配置777秒却实际传120秒，修复后传777秒；没有伪称实际测得 AMD 扫描超过120秒。 |

源码位置：QLM `src/qlm_bench/backends/mujoco/training_control.py` 的 `reserve`；
WAM `src/wam_policy/opd_v4/{control,preflight}.py`。
新增测试：QLM `test_pending_last_candidate_does_not_abort_other_stream`，
WAM `test_pool_preflight_honors_configured_resource_timeout`。

## 审核范围与路径验证

检查 configure/relocate/preflight、launcher 子进程环境、QLM profile/pool/worker/SQLite 调度、
WAM 模型加载/三角色/SDPA 与 LoRA、learner/DDP、checkpoint identity/restore/retention/export/serve。
追踪了 worker 实际调用的 factory、Native MuJoCo runtime、RAMBO checkpoint 和资源闭包读取。

- 路径与内容身份分离；config 相对路径以 config 所在目录解析，解释器 symlink 保留。
- 新 training profile 只绑定 pool 内容，不保存原 pool 的运行地址；SQLite 路径不进入算法身份，
  checkpoint 保存逻辑 control_state，新 segment 取消 pending、将旧 active 标记 interrupted。
- 原 trace 中的绝对 scene 路径属于历史 provenance；已准备的 pool 运行时从 pool 内部相对资源读取。
  若重新 prepare pool，则需要显式 resource-map；历史 expert/synthesis 路径不是本次 Stage2 worker 的依赖。
- 模型端使用 torch SDPA、常规 AdamW、PyTorch cuda 接口和 nccl backend；源码没有要求运行 NVIDIA 专属
  flash-attn 路径。QLM 子进程隐藏 GPU 并选择 OSMesa/llvmpipe。上述是源码检查，不能替代 ROCm/RCCL 实测。

实际异路径检查复制了两repo源码（无.git），为 checkpoint、pool、VAE/text config、十项 prompt、profile
建立新地址，以实际 `relocate`/`preflight` 和 QLM 公共 CLI 验证。CPython audit hook 拒绝读取原 repos、
models、runs、data、assets、checkpoints 目录；先做故意原路径读取确认 hook 生效。
800个 training resets、冻结资源与 prompts 通过验证；另对含1个 confirmed及1个 pending的非空调度快照，
经公共 CLI 恢复至新 segment，分别成为 interrupted/cancelled，confirmed保持1。

测试采用只读 hardlink 资源副本以避免重复大文件，不宣称独立磁盘拷贝；现有本地解释器继续显式使用，
并过滤本地 virtualenv 的旧 editable 安装搜索路径以模拟干净目标环境。没有复制 virtualenv 或验证目标OS ABI。
SFT仅读取 metadata/safetensors headers，未实例化模型；本轮没有重新哈希全部5B weight payload。
14项原始 manifest/profile/prompt hash 前后不变，实际消费的冻结资源和 pool 内容由 preflight 校验。
首次 /tmp hardlink 因 sandbox 跨挂载限制失败；改用同 workspace 下独立目录。另一次因本地 editable
搜索路径触发 audit hook 而失败，日志保留；它们是检查环境/脚本问题，不冒充产品代码发现。

## 验证结果

- WAM `make check`：compile/import/docs通过，sandbox中200 passed、21 skipped、2项 loopback权限失败。
  在宿主环境隐藏 GPU 后仅补跑这两项，2 passed；合计202 passed、21 skipped，无未解决测试失败。
- QLM `tests/qlm`：sandbox中265 passed、13 skipped、4项 loopback权限失败。
  宿主补跑完整 test_live_inference.py 与 tests/qlm_bench，39 passed（25个RPC/driver测试＋14个core测试）。
  去重后 tests/qlm + tests/qlm_bench 合计283 passed、13 skipped，含八进程SQLite调度与新增deck边界测试。
- 另跑实际 OPD 双rank CPU/Gloo：3F→1S，和显式平均梯度对照的最大参数差0，最终空模态 reducer 检查通过。
- 异路径 preflight、非空 control_state 公共CLI恢复、源码/输入身份与配对governance检查：见各独立JSON/日志。
- skips为已有 dataset/media 或可选 simulator fixtures；不计为通过。不重复真实 physics/rollout。

## AMD交接影响与剩余边界

本轮修改了两repo runtime source身份，OPD-005旧source bundle/config/receipt保持原历史内容。
使用本轮 `opd-v4-reviewed-runtime.tar.gz` 及 `runtime-bundle-manifest.json`，或当前实际 working tree；
不能用父commit的 git archive、远端旧源码或旧OPD-005 bundle 代替修复后的源码。
在目标主机按新source重新 configure/relocate并运行 preflight，不手改旧receipt以冒充通过。
旧checkpoint的runtime source绑定仍严格，本轮未提供跨代码版本的隐式迁移。

目标主机仍需原生ROCm PyTorch/RCCL及独立CPU MuJoCo/OSMesa环境、显式解释器与资源地址、同机local scratch、
可用loopback端口，以及按实际资源扫描/训练等待成本配置的有限timeout。八条CPU streams部署为同一主机；
本实现不是多节点launcher。W&B使用既有项目与目标主机凭据，仍需当地网络/账户权限。
真实三角色5B、ROCm kernel/backward、HBM峰值、八卡八流吞吐、恢复与正式400S均not_run。
1/2 NFE、3F→1S、400S/1200F、context等权、CPU-only和S200/S400保留策略未改。

未连接AMD、未加载完整5B、未执行正式训练、未commit/push/PR；其他评估、视频、服务和automation未操作。

Evidence: workspace runs/audit/opd-v4-independent-review-20261024-v1/.
