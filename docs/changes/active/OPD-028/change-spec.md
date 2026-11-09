---
id: OPD-028
type: change
status: active
source_map:
  - docs/governance/opd-v4-work-registry.json
---
# ChangeSpec: OPD-028 OPD-v5.0 纯 streaming anchor 消融（QLM 侧镜像）

变更全部在 WAM（见 [WAM ChangeSpec](../../../../../WAM-Policy-opd-v4/docs/changes/active/OPD-028/change-spec.md)）：`streaming` 允许 `offline_contexts_per_rank=0`，矩阵 schema `opd-v5-matrix-v2`，run `OPD-v5_pure-streaming_900s`。 QLM 源码、`training_compatibility.json` 与 runtime 指纹 `0666c125…` 不变，仅镜像 registry 与本记录。
