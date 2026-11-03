---
id: OPD-022
type: change
status: active
source_map:
  - docs/governance/opd-v4-work-registry.json
---
# ChangeSpec: OPD-022 训练中自动上传 student 导出，publish 只传最终 student（QLM 侧镜像）

完整意图与验收以 [WAM ChangeSpec](../../../../../WAM-Policy-opd-v4/docs/changes/active/OPD-022/change-spec.md) 为准。

## Intent and observable behavior

- QLM 代码不变：WAM formal attempt 的 rank 0 训练中上传 `students/step_N/{raw,ema}`，publish 只传最终 student；都在 WAM 侧。
- WAM `compatibility.json` 的 WAM `runtime_sha256` 重算（engine.py 的 logging-only 挂钩），OPD-021 指纹登记为等价；QLM `training_compatibility.json` 与
  `runtime_contract()` 不变。

## Compatibility and non-goals

QLM worker、profile、schedule、physics、RAMBO、reset deck 均不变；本仓库只镜像 registry 与本页。

## Evidence threshold and acceptance scenarios

`scripts/check_governance.py --peer-root ../WAM-Policy-opd-v4` 通过。

## Migration and rollback

与 WAM 同步；回滚 = revert 本 `[OPD-022]` commit。
