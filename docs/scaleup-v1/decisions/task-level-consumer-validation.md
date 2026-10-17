---
id: QLM-DATA-016-TASK-CONSUMER-RULE
type: decision
status: accepted
source_map: []
---


## 2026-10-15：剩余六task审核流程覆盖

[最新用户决定](remaining-six-batch-approval.md)对剩余六task取代旧10pilot人工gate：全部资产→各task reference/范围→逐task直接100。每task一次consumer检查仍在最早Clean+Randomized实际production准入执行且计入100；不增加模型验证频率、人工pilot审核或新的固定10条配额。四个已验收task及历史receipts不回写。

## 已批准Push100；WAM兼容性每task一次 — 2026-10-14

用户已批准push-formal-pilots-20261014-v3的十条，计入Push Box100条；新QLM-DATA-016补90条，最终80train/10validation/10test，各split Clean/Randomized=20%/80%。旧十条pilot审核停止要求至此已满足。
WAM adaptation v2/v3兼容性检查按task执行一次。Push Box已有通过记录，扩量及同task后续批次不再重复Reader/VAE/cache/SFT-input/online验证，不生成这些缓存。逐条QLM物理结果、独立动作质量、Raw/Canonical、媒体、timestamp/terminal和split去重仍保留。未来若冻结contract确实改变，以独立变更评审处理，不能把普通批次重复验证设为默认流程。
用户明确授权删除本轮pilot验证派生缓存，保留验证result/manifest/hash和原始数据/模型。当前source与100条审计根为runs/audit/push-scale100-20261014-v1/；v2 DOC-012/v3 DOC-011记录规则与清理。无训练/AMD/其他任务/commit/push/发布。

## Push Box100本地数据交付完成 — 2026-10-14

QLM-DATA-016完成原批准10条＋新90条，共100条；train80(16Clean/64Randomized)、validation10(2/8)、test10(2/8)。100条真实物理身份唯一，跨split配置无近重复，原native9/RAMBO/physics/camera/success predicate/primaryBox05及批准范围保持。最终44563actions/44663boundaries。完整Raw视图与Canonical在data/qlm_bench/push100-20261014-v1/。
用户授权后实际试跑2＋2、3＋2和4physics＋3render；4＋3持续运行触发swap保护后，剩余13条降到3＋2完成。独立进程controller history/RNG/world，实际launch-policy和resource guard全记录；没有修改冻结physics源代码。WAM v2/v3验证每task一次，Push Box已有证据可复用，本次90条不重复验证、不产生模型验证缓存；34项旧pilot验证缓存payload约12.3MiB已删除，结果/manifest/来源metadata保留。
QLM-DATA-016及v2 DOC-012/v3 DOC-011均归档。审计与完整交付报告：runs/audit/push-scale100-20261014-v1/。其他9task、训练、AMD、发布及commit/push未执行。
