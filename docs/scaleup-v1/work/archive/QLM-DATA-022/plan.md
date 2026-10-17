---
id: QLM-DATA-022
type: exec-plan
status: completed
source_map: []
---

# Lift100：批准十条＋新增90条

原10条CUDA/OSMesa保留，新增90采用用户在指定会话已选定且本轮要求正式使用的Native MuJoCo CPU／原RAMBO CPU＋Native EGL，当前3physics+3render重叠流水线（此前4+4为历史launch）。backend/controller device/renderer身份明确记录，不把新路线宣称为OSMesa像素等价；旧benchmark全部已清理，不恢复或计入正式数据。OSMesa reference及AMD优先ROCm保持。

保持A primary/B-C registered backups无配额、lift-body-lane-geometry-v2、几何±3cm/±5deg、Clean±3mm/±0.3deg、两Background、无clutter/Recovery配额、native9/force-zero和500/100/50Hz、dual RGB360p50FPS/Observer720p25FPS、原20mm whole-basket minimum clearance/notfallen/三tick。无controller重训或recipe修改。每split从同ID分布抽具体配置，跨split去重不分割变量区间。最终80/10/10与各split20%Clean/80%Randomized，pilot10全train计入；新90共18Clean72Randomized。

复用成功PhysicalTrace/RenderMirror/Raw/Canonical/renderer-only recovery；新增Native正式trace准入及真实EGL来源，所有原字段/commands/terminal保留。Native CPU正式接入需完成source/clock/predicate/完整端到端实际检查，再派发大批。失败轻量日志、成功trace媒体失败不重做physics，单episode五candidate、总270尝试、连续失败10、render最多3次，其他错误fail-closed。

RAM available1GiB暂停newphysics、swap launch增量7.6GiB排空、available0.5GiB回收render-only、新render至少4GiB、pressure后render最多2；记录实际launch及并发，资源不足允许保留成功数据后降档。WAM Lift task一次资格复用，不重复Reader/VAE/cache/SFT/online，不fit/训练。完成100后合并Raw/Canonical、全数据/媒体/唯一身份/跨split配置检查，均匀随机10条交用户整task验收。

## Progress

- [x] 读取指定会话，记录pilot批准，归档QLM-DATA-021，登记新Work。
- [x] Native明确profile/CPU controller/EGL真实来源接入，32项检查通过；两条实际完整端到端准入通过，不重复WAM。
- [x] 冻结90slot/450candidate/资产/recipe/source，按最新3+3/7.6GiB policy实际生产及逐条验收。
- [x] 最终100合并、随机十条review、治理/source保护。

## Evidence / boundaries

workspace runs/audit/lift-scale100-20261015-v1/，data/qlm_bench/lift100-20261015-v1/。原正式pilot/reference/Push100/Press100、assets/weights/env/lock与三HEAD保护。benchmark数据不恢复；不进行训练、AMD、commit/push或发布。A源license unknown不改写，当前仅本地数据。

## QLM-DATA-022实际接入与生产恢复

本轮用户批准原十条并要求按本配置扩100，producer已接入显式Native CPU/RAMBO CPU trace与实际NVIDIA EGL来源。新增90中的Clean031/ap00、Randomized046/ap01已完成真实physics、完整RGB/Raw/Canonical/terminal准入，见workspace runs/audit/lift-scale100-20261015-v1/production-admission.json。没有WAM重复执行，也不宣称OSMesa像素等价；旧10条CUDA/OSMesa原始身份保留。

完整生产曾实际达到4+4，发生available约110MiB/swap约8GiB的资源事件并回收一个render-only worker。随后会话中断，主调度退出，在途renderer已排空；已生成成功trace按原hash接管，没有physics重跑。当前按保护策略降3+3继续，原4+4仍是用户采用目标，不能把单轮benchmark通过视为本次全流程4+4稳定通过。实际政策/中断/恢复与资源记录同审计目录。

## 完整生产资源发现

4+4已实际重叠，available约110MiB时回收一个render-only worker；中断后成功trace不重跑，接管验收15条。3+3完整生产随后在available1.7666GiB、swap相对launch增长6.157GiB时触发swap保护；先排空已成功trace，再以2+2续跑。原1/6/0.5GiB和4GiB新render门槛均保持，不把benchmark波次当作完整生产稳定性。实际events/policies为准，未改变物理/动作/相机/split分布。

## 最新本地合成配置：3physics＋3render，swap增量7.6GiB — 2026-10-15

用户明确要求“后续保持3+3的并发，把swap增量保护上限提高至7.6GiB”。本地路线仍为Native MuJoCo CPU／原RAMBO CPU＋Native EGL GPU rendering，保持重叠流水线。普通新launch目标改为3physics＋3render；host swap相对本launch基准增长>7.6GiB（8160437862 bytes）触发排空。MemAvailable<1GiB暂停新physics、<0.5GiB回收最新render-only、新render至少4GiB、pressure后render上限2保持。旧4+4/6GiB政策只代表原launch，不回写；成功trace不重跑。

QLM-DATA-022以独立runtime-policy-v3和resource-policy-v3.json落实本次调度变更，冻结producer/campaign/recipe/physics/controller/camera/Raw/Canonical/split不变。审计在workspace runs/audit/lift-scale100-20261015-v1/。Lift原十条已批准，100生产进行中，完整交付及最终整task用户审核尚未完成。WAM v2/v3每task一次资格继续复用，不运行WAM或新增验证cache。以下旧配置/pending叙述均保留原历史时点。


## Lift100技术交付；随机十条等待整task审核 — 2026-10-15

QLM-DATA-022完成原批准10条CUDA/OSMesa＋新增90条NativeCPU/RAMBO CPU/EGL，80train/10validation/10test、各split20%Clean/80%Randomized；100物理身份唯一、跨split无近重复。旧benchmark未恢复或计入，原十条source与媒体保持原样。原recipe/asset pool/±3cm±5deg/two backgrounds/无clutter/native9/500-100-50Hz/camera/20mm三ticknotfallen保持，Native/EGL来源显式记录，不宣称OSMesa像素等价。OSMesa reference和AMD优先ROCm保持。

完整Raw/Canonical/媒体/commands/terminal与原telemetry逐列检查通过，data/qlm_bench/lift100-20261015-v1/；Raw视图为明确相对symlink，发布前需独立materialized staging。早期4+4已实际达到；之后用户最新采用3physics＋3render、swap相对launch基准增长7.6GiB。完整生产的资源保护、render-only回收、主调度中断后的在途排空与各次实际恢复均据实记录，不重跑成功physics。实际launch见workspace runs/audit/lift-scale100-20261015-v1/execution-policies/，不把单轮benchmark冒充持续生产吞吐。

Lift task一次WAM v2DATA-018/v3DATA-008资格复用，未执行WAM或生成模型验证cache，v2DOC-019/v3DOC-018仅治理。QLM-DATA-022工程交付后归档，最终整task人工验收仍pending。全100无放回随机十条seed202610152210在workspace runs/audit/lift100-random-review-20261015-v1/review.html，不按quality/split/backend筛选。Push100和Press100验收保持；其他tasks、训练、AMD、commit/push/发布未执行，A license unknown不改写。以下pending等只描述原阶段。

