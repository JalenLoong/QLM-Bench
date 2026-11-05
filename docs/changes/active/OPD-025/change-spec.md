---
id: OPD-025
type: change
status: active
source_map:
  - docs/governance/opd-v4-work-registry.json
  - tests/qlm/test_opd_training.py
---
# ChangeSpec: OPD-025 AMD 首次提交的两个 bug（QLM 侧镜像）

完整意图与验收以 [WAM ChangeSpec](../../../../../WAM-Policy-opd-v4/docs/changes/active/OPD-025/change-spec.md) 为准。

## Intent and observable behavior

QLM 代码不变：WAM 改为只发出 `live/runner.py` 白名单内的 stop reason。本仓库新增测试锁定这份白名单。

## Compatibility and non-goals

QLM 源码、profile、runtime 指纹 `0666c125…` 均不变。

## Evidence threshold and acceptance scenarios

`pytest -q`、`scripts/check_governance.py --peer-root ../WAM-Policy-opd-v4` 通过。

## Migration and rollback

与 WAM 同步；回滚 = revert 本 `[OPD-025]` commit。
