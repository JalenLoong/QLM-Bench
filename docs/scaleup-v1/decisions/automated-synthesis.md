---
id: QLM-AUTOMATED-SYNTHESIS
type: decision
status: accepted
related_work: [QLM-DATA-011]
source_map: []
---


## 最新本地合成配置：3physics＋3render，swap增量7.6GiB — 2026-10-15

用户明确要求“后续保持3+3的并发，把swap增量保护上限提高至7.6GiB”。本地路线仍为Native MuJoCo CPU／原RAMBO CPU＋Native EGL GPU rendering，保持重叠流水线。普通新launch目标改为3physics＋3render；host swap相对本launch基准增长>7.6GiB（8160437862 bytes）触发排空。MemAvailable<1GiB暂停新physics、<0.5GiB回收最新render-only、新render至少4GiB、pressure后render上限2保持。旧4+4/6GiB政策只代表原launch，不回写；成功trace不重跑。

QLM-DATA-022以独立runtime-policy-v3和resource-policy-v3.json落实本次调度变更，冻结producer/campaign/recipe/physics/controller/camera/Raw/Canonical/split不变。审计在workspace runs/audit/lift-scale100-20261015-v1/。Lift原十条已批准，100生产进行中，完整交付及最终整task用户审核尚未完成。WAM v2/v3每task一次资格继续复用，不运行WAM或新增验证cache。以下旧配置/pending叙述均保留原历史时点。

> 2026-10-15用户最新采用配置（QLM-DOC-006）：后续本地目标为[Native CPU physics／原RAMBO CPU＋EGL GPU rendering，4physics＋4render](local-synthesis-concurrency.md)，维持重叠流水线和原资源保护，替代旧本地3+3建议。以下CUDA/OSMesa baseline及旧launch叙述保留其实际历史身份；本次仅治理，不代表producer已完成切换或端到端准入。OSMesa跨平台reference与AMD路线保持，当前任务审核状态以task-synthesis-progress.md为准。



# 自动数据合成 — 2026-10-13

用户明确授权 M0–M6，只贯通 Push Box 并交付10条正式 pilot，审核前不扩到100条或其他任务。
沿用 P0–P2 与默认 LOD a02 + CUDA-MJWarp / Native OSMesa，不恢复已撤销的 P3 资产。
来源计划及 SHA 位于 workspace `runs/audit/automated-push-synthesis-20261013-v1/`。

少量真实 reference → 阶段 TemplateBundle → 新场景 retarget/native9 → 原 RAMBO 实际执行
→ 成功 PhysicalTrace → 离线 state replay → Raw/Canonical/consumer validation → accepted slot。
无渲染执行不创建 GL/renderer/encoder；render worker 不加载 RAMBO/WAM，不推进 physics。
保留实际 commands/state/100Hz controller/500Hz physics telemetry、N/N+1 与 pre-reset terminal。
离线 RGB 明确记录 `recording_mode=offline_state_replay`，不改变模型 observation。

新数据每任务100条、20 Clean/80 Randomized、80/10/10 split；取消强制 Recovery 配额。
本轮10条为2 Clean/8 Randomized且全部 train；自然纠正可保留，禁止故意制造错误。
新物理失败只保留轻量日志，清理本次临时 payload；成功 trace 保留供录制恢复。
历史失败证据与所有旧产物不受此新规则影响。Reference/template/source identities 保留；
batch 不逐 candidate 调用 GPT，也不新增 GPT model/version/prompt provenance。

仍保留 full-footprint/not-fallen/three50Hz-tick success。正式 demonstration 还需检查合理
FL 操作、真实接触和数据质量。评测 cases 独立于训练成功筛选。

旧 Isaac scale-up 配额和发布后的 P3 路由段落只描述历史。P3 实现已撤销；
本轮接替数据生产路线，并非恢复旧 P3。P5/AMD/SFT/发布属于后续授权范围。

## 用户更新资源保护阈值 — 2026-10-15

后续新launch采用MemAvailable<1GiB暂停新physics、host swap相对本launch基准增长>6GiB触发排空、MemAvailable<0.5GiB回收最新render-only worker。机制保留，render启动门槛4GiB及pressure后上限2不变。这是用户明确更新，替代早先2GiB/512MiB/1.5GiB默认；旧launch/事件/receipt保持原值，不能改写成新值。当前已latched的初始launch先排空成功trace，下一launch用版本化resource-policy-v2.json，以1physics+2render完成剩余三条；不自动重试4+4或扩100。

workspace runs/audit/lift-formal-pilots-20261015-v1/resource-policy-v2.json与runtime-policy-v2/source-provenance.json记录用户来源、执行层source和精确bytes。只替换等待中的续跑supervisor，当前renderer未中断。原frozen QLM producer/campaign/recipe/physics/controller/camera/数据分布逐字节保持；执行层policy单独版本化，后续治理与新campaign须沿用批准阈值。当前physics与RAMBO主要Torch计算在CUDA；NativeOSMesa render为CPU软件出图，不使用EGL/GPU batch renderer。


## 历史：维持流水线与当时3physics+3render默认 — 2026-10-15

用户当时明确维持physics与rendering同时推进，后续新launch默认3physics+3render；不采用先全physics再render的阶段模式。资源保护使用最新1GiB available/6GiB launch-relative swap growth/0.5GiB render-only eviction；既有4GiB新render启动门槛和pressure后的排空机制保持。3+3是配置目标，实际重叠与稳定性按launch/resource证据记录，不预先宣称通过。

当前Lift十条的第二launch已经以1+2运行，保留该实际配置完成，不中断worker、不重跑成功physics或旧媒体，也不改写旧launch。完成十条后交用户审核，未批准前不100。批准来源workspace runs/audit/lift-formal-pilots-20261015-v1/streaming-concurrency-decision.json；stage-scheduling-assessment.json只是先前讨论，未被采用为默认路线。

