---
id: OPD-027
type: change
status: active
source_map:
  - docs/governance/opd-v4-work-registry.json
---
# ChangeSpec: OPD-027 preflight 端口探测 SO_REUSEADDR（QLM 侧镜像）

变更全部在 WAM（见 [WAM ChangeSpec](../../../../../WAM-Policy-opd-v4/docs/changes/active/OPD-027/change-spec.md)）：launcher preflight 的
loopback 端口探测设 `SO_REUSEADDR`，与本仓库 `live/transport.py` `RPCServer.allow_reuse_address=True` 一致。QLM 源码、
`training_compatibility.json` 与 runtime 指纹 `0666c125…` 不变，仅镜像 registry 与本记录。
