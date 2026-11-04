---
id: OPD-024
type: change
status: active
source_map:
  - docs/governance/opd-v4-work-registry.json
---
# ChangeSpec: OPD-024 矩阵默认串行、offline_only 的 cache 提前、管理员 README 走查（QLM 侧镜像）

完整意图与验收以 [WAM ChangeSpec](../../../../../WAM-Policy-opd-v4/docs/changes/active/OPD-024/change-spec.md) 为准。

## Intent and observable behavior

- QLM 代码不变：WAM 的 `submit-matrix` 默认让后一条链等前一条的 publish job；offline_only 的 run 把 cache stage 放到 smoke 之前。QLM worker 只在 cache stage 被调用，调用方式不变。

## Compatibility and non-goals

QLM worker、profile、schedule、physics、RAMBO、reset deck 均不变；本仓库只镜像 registry 与本页。

## Evidence threshold and acceptance scenarios

`scripts/check_governance.py --peer-root ../WAM-Policy-opd-v4` 通过。

## Migration and rollback

与 WAM 同步；回滚 = revert 本 `[OPD-024]` commit。
