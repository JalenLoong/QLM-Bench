---
id: OPD-020
type: change
status: completed
source_map: []
---
# ChangeSpec: OPD-020 审查后的 v2 调整（QLM 侧镜像）

完整意图与验收以 [WAM ChangeSpec](../../../../../WAM-Policy-opd-v4/docs/changes/archive/OPD-020/change-spec.md) 为准。

## Intent and observable behavior

本工作只改 WAM：action DMD 权重 0.2、训练视频改到第 0/400/800 步、取消 go/no-go 门槛、新增两路梯度分量指标。
QLM 的 training profile、调度、物理、渲染、视频 case 与 `training_compatibility.json`（`native1-2-5f900s-v2`，指纹 `8b5724f8…`）均不变；
本仓库只镜像 registry 与本页。

## Compatibility and non-goals

QLM 运行时指纹不变，v2 profile 不变；WAM 侧 algorithm digest 改变仍要求新 run ID 与完整链。

## Evidence threshold and acceptance scenarios

`scripts/check_governance.py --peer-root ../WAM-Policy-opd-v4` 通过（registry 逐字节一致）；QLM 代码未改，无需重跑 pytest。

## Migration and rollback

无 QLM 迁移；回滚 = revert 该 commit。
