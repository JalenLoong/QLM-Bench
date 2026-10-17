---
id: MUJOCO-WORKSPACE-20261014
type: guide
status: accepted
source_map: []
---

> 2026-10-15当前：Lift A的v2高层reference与八角点适用性工程交付完成，review在workspace runs/audit/lift-reference-20261015-v1/review.html；DATA020等待用户动作质量和范围审核，未开始10pilot/100，正式计数仍200/1000。前文资产pending/reference执行中保留各自历史时点。

> 2026-10-15最新：Lift资产已获批，用户指定A OASIS编织篮primary、B/C backups；SIM017被动Native/CUDA资格通过，DATA020原RAMBO reference/范围准备中，下一gate是reference审核，正式Lift仍0。旧asset-pending描述保留原时点。

> 2026-10-15最新：Push100与Press100均已获用户最终验收，累计200/1000；Press独立批准receipt在workspace runs/audit/press100-acceptance-20261015-v1/user-acceptance.json。下一task Lift Basket由QLM-DATA-020先交候选资产审核；本轮不执行reference/pilot。按资产→reference→10pilot→100及最终验收推进，双WAM每task一次。此前pending/0条/生产中段落保留原历史时点。

# 当前 MuJoCo workspace

用户授权本次仅作source/branch/workspace收束与旧720p诊断payload清理。QLM使用唯一`migration/mujoco-foundation`（repos/QLM-Bench-mujoco）；WAM v2使用独立`adaptation/v2-mujoco-sft`（repos/WAM-Policy-v2-mujoco）；v3沿用`adaptation/v3-mujoco-sft`（repos/WAM-Policy-mujoco）。三者统一使用新版360p/50FPS接口。原Isaac/OPD分支与其他研究工作不改ref、不合并、不删除；旧工作副本的任务前未提交状态保留。

## 默认接口与执行绑定

policy RGB640×360/50FPS，Observer1280×720/25FPS；action50/controller100/physics500Hz，FoV/mount/physics/OSMesa/assets不变。WAM保持原resize/padding/frozenVAE；v2video/action与v3video+10D/action独立。Explicit rgb_profile=`dual-rgb-360p-v1`；v2位于online resources，v3位于online config根。API的legacy720p默认只服务历史兼容，不作为新的MuJoCo运行配置。

workspace.env中QLM_MUJOCO_SOURCE、WAM_V2_MUJOCO_SOURCE、WAM_V3_MUJOCO_SOURCE提供明确source绑定；原Isaac env/editable安装/lock保持。运行时分别以对应WAM source和同一个QLM MuJoCo source作为PYTHONPATH，不混用两条WAM实现。旧发布wheel不覆盖。

## 数据与当前自动合成

保留全部360p诊断Raw/Canonical/cache、reference demonstrations、成功PhysicalTrace、固定template、asset packs、原VAE/T5/RAMBO/正式checkpoint和normalizers。新自动入口仍是`qlm synthesize-pilot`；按新source哈希准备独立360p profile，不能用新代码原地resume旧720p frozen队列。现有实现是reference PhysicalTrace、固定模板retarget、真实physics screening、offlineNativeOSMesa和受限自动队列。实际批次GPT调用0；不宣称未实现的GPT在线服务或十任务已全部落地。三任务工程和十任务scale-up代码/计划均保留。

旧十条720p pilot仍待用户审核并被queue/acceptance引用，暂不删除，等待明确确认；不因cleanup合成新pilot或扩100/其他任务。旧MuJoCo诊断视频/帧/latent按精确清单evict，数值事件JSONL无损gzip后保留。旧manifest/checksum/provenance不修改，路径/哈希描述历史事实；新receipt记录本地缺失/压缩和恢复方式。

当前证据/准备配置：workspace runs/audit/mujoco-workspace-consolidation-20261014-v1/。前置RGB验收保持在rgb-resolution-360p-20261014-v1/。后续训练数据release准入和AMD仍需各自明确阶段，不由source发布自动完成。

实现源码已普通commit/push并在五个目标精确回读。当前branch/worktree各一套QLM/v2/v3；无可删除的冗余MuJoCo分支/工作树。最终source heads和具体保留项见本次workspace receipt；旧原Isaac未提交工作及OPD保持。

## Latest local pilot eviction — 2026-10-14

用户随后明确回复“删除”。旧10条720p pilot的Raw/Canonical媒体/行数据、fullcapture、预览及两份latent/state缓存已按原待确认清单evict。原manifest/checksum/provenance/report和历史queue不改；新LOCAL_PAYLOAD_EVICTED marker/receipt说明原payload本地已不可用，旧accepted计数不代表现有可读数据。10份成功PhysicalTrace、独立reference demonstrations、模板、资源与全部360p数据/cache保留。下一轮先审视物理质量，再以独立360p rendition/output identity重录合格trace，不增加物理demonstration计数、不伪改旧physical source身份。若recipe/physics/资产语义变化，则对应轨迹不能冒称新配置执行数据。

此轮仅已授权eviction和重新规划，未启动新的360p formal pilot/扩100/其他任务。治理记录QLM-DATA-013、v2/DOC-010、v3/DOC-009已本地归档，未commit/push。证据：workspace runs/audit/obsolete-pilot-payload-eviction-20261014-v1/。

## Latest360p pilot reconstruction — 2026-10-14

用户后续明确授权本阶段推进。QLM-DATA-014完成原十条trace的独立360p录制、整批验收和双WAM实际readback；本地交付完成但用户质量审核待定，停止于十条，不扩100/其他任务。当前状态详见`docs/scaleup-v1/decisions/push-pilot-360p-rendition.md`与workspace `runs/audit/push-pilot-360p-reconstruction-20261014-v1/`。本段只更新本阶段状态，前述cleanup/重新规划段落保留其历史授权范围。

## Accepted-source publication — 2026-10-14

用户明确授权此次已验收源码commit/push。720p清理治理和360p pilot重录/v2-v3兼容性分别提交；实现HEAD已在五个既有GitHub目标回读。完整源码发布记录见本次publication paired records与workspace runs/audit/mujoco-accepted-source-publication-20261014-v1/。过去local-only段落保持其历史范围；源代码发布不批准pilot动作质量、不扩asset pool或正式训练/评测。
