---
id: QLM-DATA-016
type: change
status: completed
source_map: []
---

# Push Box 100条与task级consumer验证

用户批准既有十条pilot；保留其物理、录制和train身份，补90条。最终train80(16Clean64Randomized)、validation10(2+8)、test10(2+8)。新增train70(14+56)、validation10、test10。

批准的primaryBox05、smooth-v3、box±4cm/±3.5cm/±0.06rad、goal±3cm/±2cm、两套背景、Clean ap_00、无clutter、native9/RAMBO、500/100/50Hz、360p50FPS、OSMesa均保持。候选按同一ID分布预声明split/config/seed，跨split近重复去重，失败不缩小覆盖。

WAM v2/v3兼容性每task一次；Push Box现有验收有效，扩量不再运行Reader/VAE/cache/SFT-input/online验证。QLM逐条physics/quality/Raw/Canonical/terminal/media验证仍必须执行。批准删除仅与本轮十条pilot有关的验证缓存，保留manifest/result/hash、PhysicalTrace、Raw/Canonical、视频、原模型和normalizer。

QLM-DATA-016负责扩量；v2 DOC-012/v3 DOC-011仅治理规则与缓存记录。无训练、AMD、其他任务、commit/push或发布。

## Progress

- [x] 核对当前状态、记录最终pilot批准、归档上一组work。
- [ ] 精确盘点/删除授权验证缓存并验证保护项。
- [ ] 冻结100条配额、90条候选、split去重与source。
- [x] 自动生产90条；沿用成功trace/独立render恢复，不调用WAM。
- [x] 100条最终配额、唯一性、覆盖与QLM数据验收/报告。

## Validation / recovery

审计根workspace runs/audit/push-scale100-20261014-v1/。每槽最多5个candidate，全批最多270次新尝试，连续10次失败即停。单physics worker、最多2个独立OSMesa worker，最多3条待渲染trace形成背压；队列单写者。异常source/资源、重复物理身份、系统错误fail-closed。普通失败按预声明候选继续，不无限换seed。所有worker固定simulation clock；不并发推进同一world。

结束时以实际输出确认，不以队列计数代替文件验收。历史失败/身份不改写，缓存删除使用独立receipt。

## 实际交付完成

100条验收通过：保留已批准10条＋新增90条，train80/validation10/test10，分别16/64、2/8、2/8 Clean/Randomized。100物理身份唯一，跨split无近重复；Raw100视图与源字节一致、Canonical100已合并验证。WAM适配验证按task一次，本次不重复；34项pilot验证缓存已按授权清理。并发试跑与实际launch-policy源码快照、失败candidate、资源保护记录均保留。来源与交付详情见审计根completion.json、delivery-receipt.json、coverage.json、throughput.json、report.md。未训练/AMD/其他任务/commit/push/发布。
