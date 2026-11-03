---
id: OPD-021
type: change
status: active
source_map:
  - src/qlm_bench/backends/mujoco/training_control.py
  - src/qlm_bench/backends/mujoco/training_compatibility.json
---
# ChangeSpec: OPD-021 OPD-v5.0 Regression-anchored Streaming-OPD（QLM 侧镜像）

完整意图与验收以 [WAM ChangeSpec](../../../../../WAM-Policy-opd-v4/docs/changes/active/OPD-021/change-spec.md) 与
[ADR-0008](../../../../../WAM-Policy-opd-v4/docs/decisions/opd-v4/ADR-0008.md) 为准。

## Intent and observable behavior

- `training_control.DESIGN` 改为 `opd-v5-regression1-2-900s-v1`；training profile schema 仍为 `qlm-opd-v4-training-profile-v2`，9 个训练任务、horizons、
  round-robin 调度、`max_active_per_task` 与 CPU runtime 字段不变。
- `training_compatibility.json` 的 `version` 改为 `regression1-2-900s-v1`，files 清单不变；运行时指纹随 `training_control.py` 改变，WAM `compatibility.json`
  的 `qlm.runtime_sha256` 同步。
- RPC release 响应的 `training` 字段不再含 `fake_updates_successful`；QLM 本来不读该字段，worker 无需改动。teacher 作 actor 的 cache 采集复用同一 worker 与 schedule。

## Compatibility and non-goals

v2 profile（design `opd-v4-native1-2-5f-900s-v2`）被 `read_profile` 拒绝；需由 WAM `configure` 重新生成 profile。physics、RAMBO、reset deck、pool、
visualization case 不变。

## Evidence threshold and acceptance scenarios

QLM `pytest -q` 通过（profile 测试改为新 design 字符串）；`scripts/check_governance.py --peer-root ../WAM-Policy-opd-v4` 通过；WAM 的 qlm 指纹与
`runtime_contract()` 一致。

## Migration and rollback

与 WAM 同步升级；回滚 = revert 本 `[OPD-021]` commit。
