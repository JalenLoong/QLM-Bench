---
id: QLM-DATA-040
type: exec-plan
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
- [x] Sweep100全量工程检查与合并。
- [x] Fridge100。
- [x] Oven100。
- [x] Valve100。
- [x] Drawer100。
- [x] RoomDoor100。
- [x] 每task完整Raw/Canonical/media/clock/source/dedup检查和合并。
- [x] 六task随机十条集中审核交付；工程完成与用户最终验收分开。

## Discoveries / Decision Log
公共NativeProductionQueue继承十条pilot/准入12假设，必须显式参数化为零旧数据/目标100。registration的旧ready语义绑定Isaac，不伪造Isaac实现；新增显式Native后端接入。Door几何v3与A19历史身份分离。Sweep31/32保持，不收缩批准分布。

## Validation / Recovery
新版本证据根runs/audit/remaining-six-production-20261016-v1/。先独立静态/CPU契约检查，再真实Clean+Randomized与双WAM准入；不fit。实际attempt才写attempt记录，失败轻量日志且有界，source变化停止新派发。每个成功trace不可变、media只从同snapshot恢复；保留真实backend/source及完整初态。原400及已清理历史不改写。

## 2026-10-16 接入进度
六项显式Native后端绑定、approved state/predicate、完整snapshot审计、生产rendition metadata、全新100候选和零旧pilot queue计数已实现。六task零步nominal场景/完整reset及六项现存成功snapshot审计通过（Door使用v3实时scope）。QLM相关56 tests通过；v2 130/v3 58 tests通过，两个既有Gloo socket测试受沙箱PermissionError未通过，未将其冒称通过。v2/v3 docs/import检查通过。首Sweep Clean+Randomized实际physics已启动，尚未交付准入receipt。

## 六task生产准入完成；进入Sweep100
六项全部完成首Clean+Randomized的真实physics/NativeEGL/Raw/Canonical/全量必需telemetry对照与一次双WAM，共12条计入各100，24项consumer检查通过。WAM v2 DATA020/v3 DATA010已归档，此后不重复验证。QLM相关62 tests通过。Door首次两次初始化因缺door_geometry目录停止，0physics/0commands，旧root/frozen source与日志保持；独立open_room_door-v2使用同100候选、recipe、seed、范围，已实际通过。active-task-roots.json为当前路由；两条Door实际几何退栓事件/及时终止另有证据。六primary241资源文件匹配开跑前零步身份，asset_source_guard持续保护。当前Sweep完整100生产已启动，未提前宣称六项600完成。

## Sweep100工程完成 / 2026-10-17
100条全新唯一physical traces，100实际尝试均首次成功，179671 actions/179771 boundaries；20Clean80Randomized，80/10/10及16/64、2/8、2/8准确。全部Raw/Canonical/独立snapshot成功判据/必需telemetry逐列/command/terminal/媒体/跨split去重检查和Canonical100合并通过。工程receipt位于workspace runs/audit/remaining-six-production-20261016-v1/sweep_block_to_zone/completion.json。原31/32 scope与032失败保持历史，未改写。最终人工随机10仍等待六项全完成。Fridge现已进入100生产，既有一次双WAM不重复。

## Drawer scope-v5接入恢复 / 2026-10-17
前四项各100全量检查/合并通过。Drawer原生产41次physics中31成功、10超时；021与024分别耗尽5候选触发原有界停止。已定位交接绑定仅名义DrawerLaneHeadingExecutor，未指明已获批scope-v5的DrawerFixtureHeadingExecutor；实际旧heading固定0，而scope-v5按fixture yaw主动转向。接回原scope proposal hash锚定的adapter，不修改reference源码/recipe/范围/seed/成功条件。31成功不重跑，保持原profile和source，033仅补同trace媒体。独立新版本root保留31旧成员与旧准入，021/024在修复source后仅各一次原c01工程复核，失败即停止；其他原候选不变，累计physics含旧失败仍上限300。全100最终逐条审查真实source；dualWAM既有24项不重复。

## 监看频率 / 2026-10-17
用户要求进度监看降至30分钟一次；thread heartbeat qlm-task已ACTIVE，正常/无可行动变化保持安静，仅完成/失败/需决策通知。实时resource/source保护保持；单写者pipeline_v3和asset guard继续。精确恢复上下文在workspace审计根monitoring-handoff.md。

## Drawer100工程完成 / 2026-10-17
100唯一实际trace，129843 actions/129943 boundaries；全量Raw/Canonical/媒体/snapshot/predicate/必需telemetry/command/terminal/source/去重及合并通过。实际31原nominal-source成功保留、69 approved scope-v5 source新成功，021/024修复后各一次原c01成功。累计110次physics=100成功+10原失败，不冒充仅100次；补充receipt为pull_open_drawer-v2/cumulative-attempt-summary.json。Door按顺序已进入100生产，正常单写者与source/resource保护继续，最终随机审核仍等六项全完成。

## 600条工程收尾完成 / 2026-10-17
六项各100，700553actions/701153boundaries；600唯一实际physical trajectories，累计610实际physics含Drawer10原超时，另Door2初始化失败为0physics。六项全量工程检查/合并完成，60均匀随机审核视频与页面生成、hash/codec/尺寸/fps/链接核对通过。六task24原consumer checks和实际frozen source、241primary文件、6获批reference媒体/source、原checkpoint及三repo HEAD复核通过。final-source-and-delivery-audit.json及random60-media-validation.json为最终证据。原400验收与新增600工程完成/最终人工pending分开；当前无新physics/render，30分钟monitor交付后停用。

- [x] 用户最终随机审核确认；配对归档QLM-DATA-040完成。

工程接入/收尾已完成，active仅保留最终用户审核状态，不继续追加生产/模型验证/发布。无训练/AMD/commit/push/HF。
