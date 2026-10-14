---
id: QLM-DOC-003
type: exec-plan
status: completed
source_map: []
---
# 已验收MuJoCo源码的选择性发布

用户于2026-10-14明确要求三条MuJoCo分支中的720p清理治理、360p pilot重录和v2/v3兼容性分别commit/push。只发布三条既有MuJoCo分支；原Isaac/OPD、未验收实验、data/media/cache/assets/weights和HF/W&B/AMD均不属于本次操作。保留全部既有未提交内容，普通push，不改写历史。

## Progress

已核对三条源码、目标remote及混合文件。计划将各分支清理治理与重录/consumer兼容性分开提交；发布记录在实现commit远端回读后归档。混合AGENTS/registry仅暂存已验收内容，工作区实验记录保留。检查必须覆盖准确的已选源码tree，而非包含排除实验的working tree。

## 验收

提交只包含声明的源码/tests/docs；不含未验收实验实现或登记。三条分支分别提交，WAM v2/v3既有双push目标与QLM单目标精确回读。excluded文件、registry实验条目和AGENTS实验段落原样保留；原checkouts的HEAD/status/内容hash保持。publication source不表示pilot动作质量已批准，也不表示新训练/evaluation或asset pool完成。

## Evidence

workspace runs/audit/mujoco-accepted-source-publication-20261014-v1/。保留prior eviction/rendition/completion manifests不改。

## 已执行的源码发布

清理治理与重录/consumer compatibility各自形成独立commit；准确提交tree的QLM120passed/13skipped、v2 131passed/20skipped、v3 59passed及docs/import/governance全部通过。三个implementation HEAD在五个既有目标精确回读：

- `QLM-Bench-mujoco`: `b67adbb20c65ecb17b08bd013295f9e1844cd61a`
- `WAM-Policy-v2-mujoco`: `9f2775995c119f18a2323420a4e9316c57421713`
- `WAM-Policy-mujoco`: `5656ef76bcd412e7c5d9109e2e7c5a399589bcbf`

excluded实现/条目/段落与五个原checkouts的HEAD/status/content hashes保持。发布仅源码，pilot动作质量审核、asset-pool覆盖、正式训练/evaluation仍为后续工作。closing documentation另作提交并再次普通push/readback；最终receipt在workspace runs/audit/mujoco-accepted-source-publication-20261014-v1/。
