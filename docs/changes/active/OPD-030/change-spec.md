---
id: OPD-030
type: change
status: active
source_map:
  - docs/governance/opd-v4-work-registry.json
---
# ChangeSpec: OPD-030 M-OPD v1 的 teacher 侧 task expert（QLM 侧镜像）

分支 `mopd/v1_M-OPD_on_RL-v4-experts`（自 `d235248` 切出）。变更全部在 WAM 同名分支（见 [WAM ChangeSpec](../../../../../WAM-Policy-mopd/docs/changes/active/OPD-030/change-spec.md)）：RL-v4 adapter 装在冻结 teacher 上，按 context 的任务切换。QLM 源码、`training_compatibility.json` 与 runtime 指纹 `0666c125…` 不变，仅镜像 registry 与本记录。
