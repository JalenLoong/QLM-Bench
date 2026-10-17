---
id: QLM-DATA-016
type: exec-plan
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
- [x] 精确盘点/删除授权验证缓存并验证保护项。
- [x] 冻结100条配额、90条候选、split去重与source。
- [x] 自动生产90条；沿用成功trace/独立render恢复，不调用WAM。
- [x] 100条最终配额、唯一性、覆盖与QLM数据验收/报告。

## Validation / recovery

审计根workspace runs/audit/push-scale100-20261014-v1/。每槽最多5个candidate，全批最多270次新尝试，连续10次失败即停。单physics worker、最多2个独立OSMesa worker，最多3条待渲染trace形成背压；队列单写者。异常source/资源、重复物理身份、系统错误fail-closed。普通失败按预声明候选继续，不无限换seed。所有worker固定simulation clock；不并发推进同一world。

结束时以实际输出确认，不以队列计数代替文件验收。历史失败/身份不改写，缓存删除使用独立receipt。

WAM规则与缓存清理已由v2 DOC-012/v3 DOC-011独立完成并归档；当前仅QLM数据生产active。25项受影响CPU检查通过，90条资源/候选正在冻结。

正式attempt001已启动，单physics和双独立render进程，最长队列背压3条；不调用WAM。独立背景抽样后的冻结campaign与源快照为当前有效版本；首份未执行physics的preflight配置保留。

## 用户授权并发试跑 — 2026-10-14

用户根据GPU/CPU/内存余量授权后续尝试多条并发。原单physics调度器已停止派发并等待在途任务完成；原source、campaign、90个配置、controller/physics/camera均不修改。当前使用审计根parallel_dispatch.py的独立launch-policy override，先2个独立one-world physics进程＋2个render进程；每个进程独立controller history/RNG，队列单写者、trace背压。
每个execution-policy记录dispatcher源码hash、旧campaign hash、实际candidate和起止时间；不把原冻结campaign中的单worker计划冒充实际并发设置。小批量后排空，依据真实吞吐、系统内存与GPU占用再决定3/4并发，资源或正确性失败则停止新增工作。WAM验证仍不运行。

## 并发实际验收与持续生产

2-worker实际8/8、3-worker实际12/12physics成功，独立初态/seed/command/clock及原source hash检查通过。三并发RAM峰值22.15GiB，CPU63.5%，显存1789MiB。选3physics＋2render完成44之后的56条；physics估算容量72.7/h、render68.1/h。未测试4worker，当前renderer为主要限制，避免增加无收益的physics积压。数据/物理/camera/controller及已声明configs保持；实际launch override见execution-policies/和concurrency-selection.json。

## 用户指定4＋3试跑

用户明确要求4physics＋3render worker。3＋2调度器已停止派发并排空在途任务，已完成数据及成功trace保留。新的dispatcher源码版本仅调整launch容量和资源保护：可用RAM低于2GiB或swap增长超过128MiB时排空并停止新增，配置/physics/controller/camera/recording source保持冻结。旧dispatcher源码按SHA保存在dispatcher-source/，每个新execution-policy绑定实际源码快照。先小批量实际验收，实测适合再继续100条。

## 4＋3实测试跑通过，持续生产

完整4physics＋3render的12个actual candidate全部成功，独立初态/seed/command/clock检查通过。RAM峰值27.32GiB、CPU79.5%、GPU2249MiB；12条小批wall798.4s，对照3＋2小批860.8s，非同seed受控比较。首次128MiB swap阈值过敏已记录，改512MiB并保留2GiB可用RAM下限后未触发。按用户明确请求和实测选择4＋3完成63之后37条。新执行策略不修改原冻结physics/controller/camera/configs；旧3＋2选择与源码快照保留。

## 持续4＋3资源保护与最终降档

4＋3持续到87条时swap增长551059456bytes(约526MiB)，超过512MiB阈值；可用RAM仍约3–4GiB，RAM峰值27.34GiB，未OOM。调度器停止新增并排空，所有成功trace/媒体保留。剩余13条回到已验收3physics＋2render，作为资源保护正常分支，不调整采样范围或task predicate。源代码/完整数据配置继续保持冻结。

## 实际交付完成

100条验收通过：保留已批准10条＋新增90条，train80/validation10/test10，分别16/64、2/8、2/8 Clean/Randomized。100物理身份唯一，跨split无近重复；Raw100视图与源字节一致、Canonical100已合并验证。WAM适配验证按task一次，本次不重复；34项pilot验证缓存已按授权清理。并发试跑与实际launch-policy源码快照、失败candidate、资源保护记录均保留。来源与交付详情见审计根completion.json、delivery-receipt.json、coverage.json、throughput.json、report.md。未训练/AMD/其他任务/commit/push/发布。
