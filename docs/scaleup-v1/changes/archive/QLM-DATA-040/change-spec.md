---
id: QLM-DATA-040
type: change
status: completed
related_work: [QLM-DOC-008, QLM-DOC-009]
source_map: []
---

## 用户最终审核与正式验收完成 / 2026-10-17

用户原文：“六项随机审核通过，完成600条正式验收登记和配对文档归档。保持不训练、不连接AMD、不commit/push、不发布HF。”六task每项100均正式验收；此前400保持，累计1000条。独立receipt在workspace runs/audit/remaining-six-acceptance-20261017-v1/user-acceptance.json，逐条正式登记formal-accepted600.json绑定600实际唯一trace及各10条原随机审核清单。700553actions/701153boundaries、610累计physics的工程事实不变；原失败/source/attempt/工程receipt与数据payload均保持，不追加physics/render/模型验证。监看已停用，无训练/AMD/commit/push/HF。

QLM-DATA-040已完成并配对归档。前文pending/active描述保留其工程交付时点；本节及completed frontmatter为最终状态。


# 六task公共生产接入与600条生产

用户于2026-10-16明确开工：先补齐六task公共生产接入与端到端准入，再Sweep→Fridge→Oven→Valve→Drawer→Room Door逐项全新100。沿用 approved-six-task-bindings.json及全部批准，不重新调reference、不设10pilot人工gate。六项全部完成后每task全100均匀无放回抽10集中人工验收。禁止训练、AMD、commit/push、HF发布。

冻结原RAMBO/native9/forcezero、500/100/50Hz、dual640×36050FPS、原相机及成功条件。NativeCPU/EGL全局3+3、RAM1GiB停派/0.5GiB仅回收render、swap launch增长7.6GiB排空、新render4GiB、pressure后render≤2。成功physics不重跑。每task20Clean80Randomized及split80/10/10，Clean ap00且有真实几何变化，所有split共享批准支持域并去重。

## Progress
- [x] 只读交接与明确开工授权。
- [x] 公共task/runtime、完整reset/recipe、独立predicate审计和rendition接通。
- [x] 全新100队列与逐task源冻结、候选预算、异常排空。
- [x] 最早Clean+Randomized端到端准入；每task查真实consumer receipt，缺少才各一次双WAM验证。
- [x] Sweep100；Fridge100；Oven100；Valve100；Drawer100；RoomDoor100。
- [x] 每task完整Raw/Canonical/media/clock/source/dedup检查和合并。
- [x] 六task随机十条集中审核交付；工程完成与用户最终验收分开。

## Discoveries / Decision Log
公共NativeProductionQueue继承十条pilot/准入12假设，必须显式参数化为零旧数据/目标100。registration的旧ready语义绑定Isaac，不伪造Isaac实现；新增显式Native后端接入。Door几何v3与A19历史身份分离。Sweep31/32保持，不收缩批准分布。

## Validation / Recovery
新版本证据根runs/audit/remaining-six-production-20261016-v1/。先独立静态/CPU契约检查，再真实Clean+Randomized与双WAM准入；不fit。实际attempt才写attempt记录，失败轻量日志且有界，source变化停止新派发。每个成功trace不可变、media只从同snapshot恢复；保留真实backend/source及完整初态。原400及已清理历史不改写。

## 2026-10-17接入修复
Sweep/Fridge/Oven/Valve各100全量工程完成。Drawer qualification-v5已批准的fixture-heading adapter必须用于随机化生产；旧binding仅nominal类导致两个+4deg slot无法穿hook，各5超时后正常停止。独立版本保留31成功及原source；修复后失败slot各一次原c01复核，累计预算包含旧失败。跨版本逐条保持rendition/source身份，成功physics不重跑。详见配对plan及workspace drawer恢复receipt。

## 工程交付与剩余人工门槛 / 2026-10-17
六task公共NativeCPU/EGL生产接入、各一次双WAM共24项准入及600全新demonstrations、逐task全量工程检查/合并和每task全100均匀随机10集中审核包均完成。700553actions/701153boundaries、600唯一轨迹、610累计physics含Drawer10原失败；实际source版本/历史负结果保留。最终source/原checkpoint/241primary/6reference/三repo HEAD及60视频/链接核对通过，详见remaining-six-engineering-delivery-20261017.md。工程checkbox以配对plan为准；本配对保持active等待用户最终动作审核，未冒充已通过人工审核。禁止自动新生产、重复WAM、训练/AMD/commit/push/HF发布。
