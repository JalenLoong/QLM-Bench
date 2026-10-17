---
id: QLM-DATA-024
type: change
status: completed
source_map: []
---

# Kick Ball to Goal十条formal pilots

## 授权与不变量
用户已批准kick-impulse-retract-v3-tucked-carry reference及完整范围：ball dx/dy±3cm、goal dx±8cm/dy±5cm。独立批准receipt在workspace runs/audit/kick-formal-pilots-20261015-v1/user-approval.json。A primary，B/C backups登记且无配额；两背景、无clutter、不强制Recovery。十条全新真实trajectory：2Clean小范围真实几何变化/ap00＋8Randomized/alltrain；开发reference/scope不计正式数据。

只新增Kick task-specific formal admission与producer，复用PhysicalTrace、Native RenderMirror、Raw/Canonical、render-only恢复与逐列验收；原task判据/接口/lock不改。Kick保持正面整球入实体goal、notfallen和连续三个50Hz ticks。task成功与动作质量分开：实际snapshot检查pre-strike球运动、FL/其他robot接触和phase/joint连续性，未知contact不硬失败。原RAMBO/native9/force-zero/IK/PD/QP/history/500-100-50Hz、双RGB640×36050FPS及Observer720p25FPS保持，不新增高频diagnostic永久保留要求。

## 执行与资源
NativeCPU physics/原RAMBOCPU＋NativeEGL硬件rendering重叠流水线，普通3physics＋3render；available<1GiB暂停新physics，swap相对每launch基准增长>8160437862bytes排空，available<0.5GiB仅回收最新render-only；新render≥4GiB，pressure后render≤2。成功trace保留且不重跑physics。50个预声明candidate/每slot5个、全局最多30次/连续失败10次，失败candidate只轻日志。任何完整性/contract异常fail-closed。

## 交付与验收
- [x] Kick正式数据入口、同timestamp实际球pose/goal/三tick审计与原三task回归检查。
- [x] 冻结recipe/source/50配置/资产pool/launch policy，3+3真实执行十条及media。
- [x] 全量Raw/Canonical/50Hz boundaries/commands/terminal/既有telemetry逐列、所有视频和物理身份去重、2/8覆盖验收；合并Canonical十条及清晰Raw视图。
- [x] Kick task一次WAM v2 DATA-019/v3 DATA-009：Clean+Randomized实际Reader/frozenVAE/SFT-input/online/cache回读及正确Kick prompt；原normalizers/模型不fit、不训练。
- [x] 审核页/动作质量证据/实际吞吐与resource历史，保护旧300及所有原模型/reference/资产/source heads；交用户pilot审核后停。

QLM-DATA-024保持active直至用户审核；v2/v3工程兼容work实际通过后归档。public task registration仍planned，不冒充完整public runtime绑定。无100、其他task、训练、AMD、install/upgrade、commit/push或发布。W&B not_run/local-only。

## 工程完成与当前人工gate

## Kick十条formal pilots工程交付；等待用户审核 — 2026-10-15

用户已批准v3 reference与完整ball XY±3cm/goal X±8cm Y±5cm范围。QLM-DATA-023归档，QLM-DATA-024完成全新2Clean8Randomized/alltrain十条，7832actions/7842boundaries、十个唯一物理身份；10次physics、0失败candidate。A primary、两背景、原recipe/controller/IK/PD/QP/history/physics/asset参数/native9/500-100-50Hz/camera保持，没有范围收缩、backup配额或成功physics重跑。formal新增十条仍待用户审核，最终已验收计数仍300/1000。

完整Raw/Canonical/媒体/50Hz action-state/完整command确认/terminal/原telemetry逐列、实际snapshot pose/速度/goal及独立正面整球入门/notfallen/三tick审计通过。准备阶段球最大位移0.0000mm；FL接触1–6个50Hz boundary，其他robot碰球0；最后FL接触后自由滚动2.42–4.44s。task success与quality分开，未知contact不硬失败，不新增高频diagnostic永久存储要求。

NativeCPU/RAMBOCPU＋NativeEGL真实同时3+3=True，1GiB暂停physics/7.6GiB launch-relative swap排空/0.5GiB仅render回收/新render至少4GiB及pressure排空保持。正式pipeline 215.2s≈167.29条/h（包含正式媒体验收，不含工程准备、WAM资格和附加审核出图），不作稳态保证。双RGB640×36050FPS/原Observer1280×72025FPS保持；同timestamp完整snapshot镜像不推进physics。宽视角仅人工看清球路/goal，不属于policy或formal Observer。

v2DATA-019/v3DATA-009各一次Kick Clean01＋Randomized04实际Reader/原VAE/SFT-input/online/cache回读、正确Kick prompt及v3实际10D通过并归档，原三task未复验、不fit/训练，同Kick扩100不再复验。public registration仍planned；当前仅显式MuJoCo profile正式数据链路通过，不声称public runtime全部ready。

审核workspace runs/audit/kick-formal-pilots-20261015-v1/review.html、report.md；合并Canonical及明确Raw相对symlink视图workspace data/qlm_bench/kick-approved-pilot-20261015-v1/（发布前需materialized staging）。QLM-DATA-024保持active等待十条动作质量/覆盖/吞吐审核，未授权100。原Push/Press/Lift300、source heads/资产/模型/环境锁保持。无其他task/AMD/commit/push/发布。以下pending只保留原历史时点。


- [ ] 用户十条pilot动作质量、覆盖与吞吐审核。未批准前不扩100。

## 用户pilot批准与100授权

用户明确“审核通过，推进至100条完成”。十条保留计入100，独立receipt在workspace runs/audit/kick-scale100-20261015-v1/user-approval.json；后续QLM-DATA-025补90及完整100工程交付/随机十条审核。原pending字段仅历史，不改原attempt/数据。
