---
id: QLM-PRESS-WALL-ASSETS
type: decision
status: accepted
related_work: [QLM-SIM-016, QLM-DATA-017]
source_map: []
---

# Press Button三资产与完整墙面决定

2026-10-14用户批准已展示A/B/C：industrial-button(primary)、industrial-button-blue和emergency-button-red(backups)，并要求两个backup也通过MuJoCo物理验收。此批准是资产选择，不代表尚未执行的physics gate已通过。每task仍1primary+2backup，不新增quota。

用户明确要求整面墙壁，button安装在墙面上；按钮随机化指沿该墙面位置变化。本地采用法向X的固定实心墙(6m宽、2.4m高、0.12m厚)，移除旧小安装板，source外壳背面贴墙。cap沿+X真实滑动，随机化为平面Y/Z，具体ID/Clean数值范围在reference适用范围验收后、pilot前冻结。原cap几何/缩放和physics保持；C的新MuJoCo惯性/convexHull映射须实测验证并明确记录。

原12mm/三个50Hz ticks/not-fallen/24s、native9/force-zero/原RAMBO、physics时序、双RGB360p50FPS/Observer720p25FPS保持；无辅助操作力、无teleport/latch。wall作为真实collision geometry，无clutter。ap_00/ap_01仍是两套受控外观preset，物理墙不随preset变化。

继续[SIM016物理计划](../work/archive/QLM-SIM-016/plan.md)及[DATA017 reference计划](../work/archive/QLM-DATA-017/plan.md)。流程：资产审批(已通过)→物理验收/高质量reference与适用范围审核→10pilot审核→扩至100。WAM兼容性每task一次，当前stage not_run。旧reference/Push100/source/资源包不改写；新wall资产和证据独立版本化。无训练/AMD/commit/push/发布。

## 实际工程交付完成

A/B/C各自Native/CUDA静止、真实接触按压/回弹、正常/高速wall collision、有限行程、zero-step selected-lane reset、其他world不变与完整articulation镜像通过。三个原RAMBO/native9 nominal实际成功：A/B各501actions10.02s，C571actions11.42s；cap终态分别15.086/15.084/14.294mm，原predicate通过、无跌倒。旧Source pack/robotbody/joint/camera/solver逐字段保护检查通过，无额外equality constraints或辅助操作力。

主资产A墙面Y0.10±0.03/Z0.30±0.02m四个预声明角点全部成功，ap_00/ap_01非visual参数逐字节一致；range proposals仍等待用户审核。21路原始媒体/7个三视角preview/独立慢放及完整snapshot review交付，主资产/四角点other-geom-cap/wall/housing均0；C仅1个FL-housing边缘接触，非机身操作，不改task outcome。

QLM回归沙箱147pass/12skip、4socket权限失败；同四项host复核4pass，合计151pass/12skip。Docs/shared治理/import/compile/原资源保护通过。首轮wall stress guard失败及source-compliance分析保留；未改solver。七个真实task trace源码逐hash保存165个去重blob，原model_2000与旧Push100/receipt保持。

当前Press默认模型切换为新full-wall A resource pin，LOD a02保持；旧显式model/历史cases不改写或冒充新scene资格。无formal pilot/100、WAM模型验证、训练、AMD、commit/push或发布。本SIM技术资格完成并归档，QLM-DATA-017保持active等待reference动作质量与适用范围用户审核。证据与review见workspace runs/audit/press-wall-qualification-20261014-v1/。

## 用户批准范围，reference动作待修复 — 2026-10-15

资产与墙面随机化审批已通过：Y0.10±0.03/Z0.30±0.02m、fixed normal安装深度、ap_00/ap_01保持。旧reference推进肘部摆动未通过质量审核，QLM-DATA-017只调整高层reference再执行；不能把此审批解释为pilot开工。新recipe在pilot前重验既定范围，不改成功条件、原RAMBO或physics。

## 新reference获批并进入十条pilot — 2026-10-15

用户批准press-body-carry-v2新reference。DATA017归档，DATA018先在既定四角重验新recipe，再2Clean/8Randomized正式pilots。每成功slot冻结独立render-only profile，由同一不可变十槽campaign约束quota/候选/来源，以实现最多4条待渲染积压；这不改Raw/Canonical/action/camera/task contract。每task一次双WAM验证使用本Press一Clean和一Randomized，最后仍须用户审核十条后才能100。

## Press十条formal pilots技术交付，等待用户质量审核 — 2026-10-15

新reference及三资产/wallY/Z范围已获批准；新recipe四角重验4/4通过。QLM-DATA-018完成10条新真实primary A trajectories(2Clean/8Randomized alltrain)，6735actions/6745boundaries；10次首次物理执行均成功，零body-button contact，无范围收缩或backup配额。原RAMBO/native9/500-100-50Hz/真实12mm三tick/not-fallen/camera/360p50FPS保持，Native OSMesa mirror不推进physics。完整Raw/Canonical、实际articulation snapshot、terminal/原telemetry逐列、媒体与唯一身份检查通过。推进FL hip摆幅4.60–5.66deg，最大10ms1.127deg；保留原gait小波动，task success与动作质量分开。

v2 DATA-017/v3 DATA-007完成Press各一次实际Clean+Randomized Reader/原VAE/SFT-input/online/caches回读与v3实际10D，Press instruction embedding匹配；两模型works归档。今后同task扩100不重复WAM验证。2physics+2render/最多4积压，实际pipeline 1054.0s≈34.2条/h，RAM最低10.79GiB，无swap增长/资源guard；task一次WAM与最后渲染并行，此吞吐非稳定生产保证。

审核入口workspace runs/audit/press-formal-pilots-20261015-v1/review.html、report.md；data/qlm_bench/press-approved-pilot-20261015-v1/。QLM-DATA-018保持active等待指定十条动作质量/覆盖/吞吐用户审核，未批准前不100/其他task。Push100用户验收及原reference/asset qualification/receipts/source heads保持。无正式训练/AMD/commit/push/HF或发布。

## 用户批准Press100扩量 — 2026-10-15

Press十条pilot已全部获用户审核批准，QLM-DATA-018归档；QLM-DATA-019保留十条原身份并补90，最终80/10/10及20/80Clean/Randomized。primary A/full wall/fixed X/Y0.10±0.03/Z0.30±0.02/两背景/press-body-carry-v2/原RAMBO/360p50FPS均冻结。用户指定4physics+4render，独立process history/RNG与resource/backpressure保护，实际launch政策单独记录。

Press WAM v2 DATA-017/v3 DATA-007 once-per-task实际资格有效，扩100不再运行模型验证或生成验证缓存；当前v2 DOC-016/v3 DOC-015只有治理记录。训练first-input/原checkpoint/normalizers保持。新100完成后从全体均匀随机10展示；旧十条pending-review receipt保留历史时点，新批准见workspace runs/audit/press-scale100-20261015-v1/user-approval.json。当前生产运行中，不能提前宣称100完成。无训练/AMD/其他任务/commit/push/HF发布。

## Press Button100本地交付与随机十条review — 2026-10-15

QLM-DATA-019完成已批准十条＋新90条，共100，train80(16Clean64Randomized)/validation10(2+8)/test10(2+8)，66903actions/67003boundaries。100物理身份唯一，跨split无近重复；同一批准ID支持，没有变量区间分割/OOD。primary工业红/full wall/fixed X/YZ范围/两背景/press-body-carry-v2/原RAMBO/native9/500-100-50Hz/360p50FPS/predicate保持。成功Trace独立NativeOSMesa，不推进physics；全部Raw/Canonical/media/terminal/原telemetry逐列验收与Canonical100合并通过。Raw100 view显式相对symlink原不可变bytes，发布前需独立materialized staging。

用户指定4physics+4render已实际重叠；首8条触发swap新增512MiB保护后停止新派发并排空，保留全部成功trace/数据。后续resource-safe实际launch政策见execution-policies，源码/recipe/config保持冻结；不把初始4+4计划冒充全程实际设置。新增90条实际queue2.08h≈43.3条/h，含保护和续跑等待，非稳态保证。新physics尝试91、失败1；成功筛选数据收集不作为policy SR。

WAM v2/v3 Press once-per-task receipt复用，本批没有Reader/VAE/T5/SFT-input/online复验、模型验证cache、fit/训练或权重修改；v2 DOC-016/v3 DOC-015仅治理归档。QLM-DATA-019也归档，工程交付完成；用户对最终100整task验收等待随机十条review。审核：runs/audit/press100-random-review-20261015-v1/review.html(全100均匀无放回，seed202610151910，无quality/split筛选)。主报告runs/audit/press-scale100-20261015-v1/；data/qlm_bench/press100-20261015-v1/。Push100原验收、Press reference/pilot/source heads/原models保持。其他tasks、训练、AMD、commit/push/发布未执行。
