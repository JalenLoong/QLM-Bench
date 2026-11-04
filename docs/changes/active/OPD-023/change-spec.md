---
id: OPD-023
type: change
status: active
source_map:
  - docs/governance/opd-v4-work-registry.json
---
# ChangeSpec: OPD-023 offline target cache 变成 Slurm stage，`submit-matrix` 一次提交四个实验（QLM 侧镜像）

完整意图与验收以 [WAM ChangeSpec](../../../../../WAM-Policy-opd-v4/docs/changes/active/OPD-023/change-spec.md) 为准。

## Intent and observable behavior

- QLM 代码不变：WAM 的 Slurm 链多出 `cache` stage（frozen teacher 以高去噪步数作 actor，经同一套 QLM worker、schedule 与 profile 采集），
  四个 OPD-v5.0 实验由 WAM `submit-matrix` 一次提交并共用一份 cache。
- QLM worker 在 cache stage 中的调用方式与 `launch-cache` 相同（`training_live worker --max-episodes` 按 cache 轮数）；`training_compatibility.json` 与 `runtime_contract()` 不变。

## Compatibility and non-goals

QLM worker、profile、schedule、physics、RAMBO、reset deck 均不变；本仓库只镜像 registry 与本页。

## Evidence threshold and acceptance scenarios

`scripts/check_governance.py --peer-root ../WAM-Policy-opd-v4` 通过。

## Migration and rollback

与 WAM 同步；回滚 = revert 本 `[OPD-023]` commit。
