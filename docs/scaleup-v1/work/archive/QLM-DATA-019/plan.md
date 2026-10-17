---
id: QLM-DATA-019
type: exec-plan
status: completed
source_map: []
---

# Press Button100条扩量

## Purpose / scope

保留已批准十条物理/录制/train身份，补90条，最终train80(16Clean64Randomized)、validation10(2+8)、test10(2+8)。各split从同一已批准ID分布抽取具体配置，去除跨split近重复，不按几何区间切分、不引入OOD。primary工业红按钮、两backup只登记，无额外quota。

## Frozen contracts

原press-body-carry-v2 recipe/template、原RAMBO/controller history/native9/force-zero、500/100/50Hz、真实12mm/3tick/not-fallen/24s、wall法向安装深度、Y0.10±0.03/Z0.30±0.02、ap_00/ap_01无clutter/Recovery、dualRGB640×36050FPS/Observer720p25FPS保持。Clean附近小范围真实Y/Z变化沿用pilot支持Y±3mm/Z±1mm。未知contact不硬失败，成功判据与行为质量分开；沿用已验收hip摆幅15deg/10ms2deg邻域review hold，body contact只暂停检查可靠证据。

## Implementation / validation

复用PhysicalTrace、SmoothPressExecutor、RenditionQueue、OSMesa完整snapshot mirror和Raw/Canonical。为Press新增明确production rendition schema允许正式split，保持旧Push/Press pilot schemas，旧pilot用其frozen-source验证不改来源。新资源仅在墙面平移既有被动cap/static housing，逐字段保护robot/collision/inertia/joints/camera/solver，原资源包不改写。每slot预声明5个candidate(小jitter+不同seed)、全批270次新physics/连续10失败停止；失败仅轻量日志、成功trace渲染可初次+2retry，source/contract错误fail-closed。

用户指定4physics+4render，独立one-world/history/RNG，单writer、backlog最多8。可用RAM2GiB/swap新增512MiB保护；先按4+4实际执行，资源压力停止新physics并排空；以实测记录resource-safe实际并发/launch epochs，普通资源保护允许有据降档/继续，不改冻结数据/recipe。不得以计数代替实际文件验收。

WAM task-once Press证据已通过，扩100不运行Reader/VAE/T5/SFT-input/online checks、不生成验证缓存、不fit normalizer/训练。旧once缓存/metadata不擅自删除。随机抽10由100最终membership均匀无放回固定seed，在结果全部完成后生成记录，不能按质量或split挑选。

## Progress

- [x] 记录pilot用户批准，归档D018，建立D019和consumer治理。
- [x] 生产schema、sampling/dedup、resource scheduler与保护检查通过。
- [x] 冻结100membership/90slots/source/asset configs，复用十条。
- [x] 实际补90条完整Raw/Canonical/media/quality/terminal。
- [x] 100最终quota/唯一性/跨split去重/原字段与合并验收。
- [x] 更新治理、随机十条审核页交付。

## Evidence / non-goals

workspace runs/audit/press-scale100-20261015-v1/、data/qlm_bench/press100-20261015-v1/。不启动其他task/训练/AMD/commit/push/HF或发布；保护已有Push100及Press references/pilots/source。

## Decision log / actual preflight

具体配置跨split近重复阈值Y1mm/Z0.5mm；同一ID支持、每split同四象限，held-out配置先预声明避免2D Clean小支持的顺序耗尽，无区间切分/OOD。两背景在每个象限均覆盖，避免颜色和位置符号关联；正式physics前已补检查，原准备版本保留，字节验证后复用一致资源。Massless task_static编译dummy inertial/frame缓存和unused fixed-camera COM cache随平移更新；实际fixed相机pose/动态惯性/全robot等逐字段一致，不改变物理语义。初次跨filesystem hardlink失败已加copy fallback；失败test/preparation日志均保留。

29项production/pilot/原Push检查通过；4physics+4render fake-process调度、bounded retry与内存保护检查通过(7个Press专用checks)。十条原pilot用原frozen source做QLM数据/来源验收通过，不触发WAM验证。

## Actual run start

90slots/450candidate资源与配置已冻结，campaign b1b3e16e48638719fee1ceb8da33c1f1366f197ee6e4696dfb60ff8c4dca08cc，双背景各墙面象限覆盖、100split quotas正确；十条原pilot不重跑。浮点边界0.3-0.02与0.28相差约5.6e-17m，guard以1e-12m tolerance处理，不改变支持，准备失败/partial资源保留，无formal physics。当前4physics+4render已开始，resource保护存在；结果未完成，不提前宣称100。

## Press100首次4+4触发resource保护 — 2026-10-15

4physics+4render已实际重叠执行。第一个8-candidate wave中，在4render启动/4physics在途期间swap新增超过512MiB，调度器自动停止新physics并排空；已完成数据和成功trace保留，无候选/recipe/物理/相机调整。当前等待最后媒体排空，随后按既有resource-safe分支3physics+2render续完100，必要时有据降低启动容量。实际政策/资源采样分别在execution-policies/和resources.jsonl；不把原冻结campaign目标4+4冒充持续实际设置。无WAM重复检查/模型cache/训练/AMD。

## Press Button100本地交付与随机十条review — 2026-10-15

QLM-DATA-019完成已批准十条＋新90条，共100，train80(16Clean64Randomized)/validation10(2+8)/test10(2+8)，66903actions/67003boundaries。100物理身份唯一，跨split无近重复；同一批准ID支持，没有变量区间分割/OOD。primary工业红/full wall/fixed X/YZ范围/两背景/press-body-carry-v2/原RAMBO/native9/500-100-50Hz/360p50FPS/predicate保持。成功Trace独立NativeOSMesa，不推进physics；全部Raw/Canonical/media/terminal/原telemetry逐列验收与Canonical100合并通过。Raw100 view显式相对symlink原不可变bytes，发布前需独立materialized staging。

用户指定4physics+4render已实际重叠；首8条触发swap新增512MiB保护后停止新派发并排空，保留全部成功trace/数据。后续resource-safe实际launch政策见execution-policies，源码/recipe/config保持冻结；不把初始4+4计划冒充全程实际设置。新增90条实际queue2.08h≈43.3条/h，含保护和续跑等待，非稳态保证。新physics尝试91、失败1；成功筛选数据收集不作为policy SR。

WAM v2/v3 Press once-per-task receipt复用，本批没有Reader/VAE/T5/SFT-input/online复验、模型验证cache、fit/训练或权重修改；v2 DOC-016/v3 DOC-015仅治理归档。QLM-DATA-019也归档，工程交付完成；用户对最终100整task验收等待随机十条review。审核：runs/audit/press100-random-review-20261015-v1/review.html(全100均匀无放回，seed202610151910，无quality/split筛选)。主报告runs/audit/press-scale100-20261015-v1/；data/qlm_bench/press100-20261015-v1/。Push100原验收、Press reference/pilot/source heads/原models保持。其他tasks、训练、AMD、commit/push/发布未执行。
