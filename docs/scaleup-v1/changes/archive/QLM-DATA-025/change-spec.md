---
id: QLM-DATA-025
type: change
status: completed
source_map: []
---

# Kick Ball to Goal100：原批准十条＋新90条

## 授权、接口与交付
用户批准全部十条pilot并授权100。独立receipt：workspace runs/audit/kick-scale100-20261015-v1/user-approval.json。保留原十条真实source/trace/Raw/Canonical/media，补90条；目标80train/10validation/10test，各split20%Clean/80%Randomized，合计20Clean80Randomized。各split均从相同批准ID支持抽具体配置，配置/物理身份唯一，跨split无近重复；不分割变量范围或引入OOD。A primary、B/C backups无配额；两背景、无clutter/强制Recovery。保持kick-impulse-retract-v3-tucked-carry与ball XY±3cm/goal X±8cmY±5cm、原参数/原RAMBO/native9/force-zero/500-100-50Hz/dual640×36050FPS/Observer720p25FPS、真实正面整球入门/notfallen/三tick。task success与quality分开，零/未知FLcontact不硬失败，可靠实际不合理行为保留trace待review，不自动缩范围或重训。

## 实施
复用既有ProductionQueue、PhysicalTrace、Native RenderMirror和render-only恢复；仅扩Kick production-rendition与task-specific几何配置/准入。保留旧三个task及新Kick pilot身份。新NativeCPU/原RAMBOCPU＋EGL普通3physics3render重叠流水线：available<1GiB暂停新physics，launch-relative swap增长>8160437862bytes排空，available<0.5GiB只回收最新render-only，新render≥4GiB/pressure后render≤2。成功physics不重跑，系统/完整性错误fail-closed。每slot最多5candidate/新90全局270attempts/连续失败10次；失败candidate只轻日志。配置、模型、recipe、source在执行前冻结；生产资源政策分launch据实保留。

## Progress / acceptance
- [x] 原十条批准、冻结来源隔离复核；新450candidate和完整quota/同ID去重，frozen producer/pool/recipe/resource policy。
- [x] Kick正式production admission与原task/pilot回归；原controller/physics/camera/interface保持。
- [x] 实际3+3补90；完整100Raw/Canonical/media/actions-state/command/terminal/既有telemetry逐列及snapshot/质量/唯一身份/跨split去重。
- [x] Canonical100合并、明确Raw相对symlink视图；全100均匀无放回固定seed202610152510随机十条，展示完整球路＋原三视角＋真实三时点截图。
- [x] 实际吞吐/resource/source保护、治理配对归档；交用户整task验收，未把工程完成当人工通过。

WAM v2 DATA-019/v3 DATA-009的Kick task一次资格复用，v2DOC-022/v3DOC-021仅治理，无WAM执行/新模型cache/fit/训练。public registration仍planned。旧Push/Press/Lift300保留，正式Kick100的最终用户验收pending。无其他task、AMD、install/upgrade、commit/push或发布；W&B not_run/local-only。

## 实际执行进度与普通实现决策

39项Kick/原task production与predicate回归通过；原十条用其实际frozen source隔离复核通过，未重绘或改标。新增90/450candidate已冻结；所有split均使用完整相同4D范围的Latin-hypercube抽样，retry只用预声明4%局部jitter，跨split near阈值为ball XY各0.5mm、goal XY各1mm，不改变支持范围、physics或成功标准。两条新增Clean/Randomized真实端到端production准入通过并计入90，剩余88正在3+3流水线执行；详见workspace runs/audit/kick-scale100-20261015-v1/pipeline.json、queue.json、execution-policies/和production-admission.json。

复用原ProductionQueue的单写者/成功trace恢复和已接受的Native worker策略，新task-neutral NativeProductionQueue显式注入task准入/freezer；原Lift/Press producer文件及历史run不修改。任何失败停在当前阶段，不启动后续合并/审核/治理。消费者本轮无WAM执行或cache。

## Kick100工程交付；随机十条等待最终验收 — 2026-10-15

QLM-DATA-025保留原已批准10条＋新90条，全100NativeCPU/原RAMBOCPU＋NativeEGL，80train/10validation/10test、各split20%Clean/80%Randomized，76950actions/77050boundaries。100物理身份唯一，跨split无近重复；相同批准4D ID支持，不分割变量范围/无OOD。原A primary、两背景、v3 recipe、ball XY±3cm/goal X±8cmY±5cm、原RAMBO/native9/500-100-50Hz/camera/实体goal正面整球入门/notfallen/三tick保持，无范围收缩、backup配额或成功physics重跑。

完整Raw/Canonical/媒体/50Hz boundaries/command/terminal/原telemetry逐列及完整snapshot球pose/速度/goal核对通过。task success与quality独立，准备球最大位移0.0000mm、其他robot碰球50Hz geometry合计0，零/未知FL contact不硬失败，不新增高频diagnostic永久存储要求。原十条完整payload/media/source字节身份保持；合并Canonical100与明确Raw/episode相对symlink视图在workspace data/qlm_bench/kick100-20261015-v1/，发布前需独立materialized staging。

普通3physics+3render已实际同时达到=True；available1GiB/launch-relative swap增长7.6GiB/紧急render-only回收0.5GiB/新render≥4GiB及pressure后render≤2保护保持，资源事件0。新增90pipeline 1712.9s≈189.15条/h（含准入/媒体验收/资源恢复，工程准备、最终合并和附加审核视角不含），不作稳态保证。实际政策/进程/失败与恢复见execution-policies和events。新physics尝试90、失败candidate0，不能用成功筛选收集作policy SR。

Kick task一次WAM v2DATA-019/v3DATA-009复用，未WAM执行/新模型cache/fit/训练；v2DOC-022/v3DOC-021仅治理。三Work工程交付后归档，用户对完整100最终验收仍pending。全100均匀无放回seed202610152510随机十条在workspace runs/audit/kick100-random-review-20261015-v1/review.html；不按quality/split/backend/原pilot筛选。宽视角仅人工诊断，不改变正式双640×36050FPS/Observer1280×72025FPS/模型输入语义。

原Push/Press/Lift300已获最终验收，Kick100现为工程交付，未提前计作用户最终验收400。public registration仍planned，不冒充public runtime全部ready。无其他task/AMD/commit/push/发布；OSMesa reference及AMD主线保持。以下pending/生产中仅描述原历史时点。

