---
id: QLM-REMAINING-SIX-FORMAL-ACCEPTANCE
type: report
status: accepted
related_work: [QLM-DATA-040]
source_map: []
---

# 六task600条正式验收登记

2026-10-17（Australia/Sydney），用户明确确认：“六项随机审核通过，完成600条正式验收登记和配对文档归档。保持不训练、不连接AMD、不commit/push、不发布HF。”

Sweep、Fridge、Oven、Valve、Drawer、Room Door各100，600条全部登记user_accepted；审核依据是每task从完整100均匀无放回抽10，共60条原随机审核。原Push/Press/Lift/Kick各100验收保持，累计10task、1000条正式验收完成。这里记录用户明确批准，不推断或伪造播放器观看日志。

| Task | 正式验收 | Actions | Boundaries | 累计physics |
|---|---:|---:|---:|---:|
| sweep_block_to_zone | 100 | 179671 | 179771 | 100 |
| close_fridge_door | 100 | 134921 | 135021 | 100 |
| close_oven_door | 100 | 78557 | 78657 | 100 |
| turn_valve | 100 | 63836 | 63936 | 100 |
| pull_open_drawer | 100 | 129843 | 129943 | 110 |
| open_room_door | 100 | 113725 | 113825 | 100 |

每task20Clean80Randomized、train80/validation10/test10及各16/64、2/8、2/8保持。新增合计700553actions/701153boundaries、600唯一轨迹，累计610实际physics=600成功+Drawer10原超时；Door另2次bootstrap初始化失败是0physics/0commands。Drawer31原source成功+69原scope-v5成功的身份、全部历史负结果及原成功条件保持。

## 权威验收证据

workspace runs/audit/remaining-six-acceptance-20261017-v1/user-acceptance.json保存原用户批准文字、每task技术receipt、全部随机审核UID和原400验收receipt。formal-accepted600.json逐条登记600的Raw/Canonical/trace/profile路径、trajectory hash、split/difficulty及是否属于审核sample；profile及包含实际source的manifest hash由protected-evidence.json锁定，共2555个既有工程/trace manifest/profile/producer/result/审核媒体/24consumer/原400验收文件。登记不修改原数据payload，也不改写历史工程receipt中的pending时点。

工程及随机审核材料保持在workspace runs/audit/remaining-six-production-20261016-v1/。历史工程报告见[原工程交付记录](remaining-six-engineering-delivery-20261017.md)，其中pending仅描述用户批准前的时点；当前人工验收状态以本报告和独立user-acceptance receipt为准。

数据路径保持workspace data/qlm_bench/remaining-six-20261016-v1下各task的raw/、episodes/视图和canonical/合并结果。正式验收通过独立登记生效，不移动、重命名或修改冻结数据。原600全量工程检查和各task一次双WAM24项兼容证据保持，本次无新增physics/render/WAM/cache验证。

## 配对归档与边界

QLM-DATA-040已completed并配对归档：[ChangeSpec](changes/archive/QLM-DATA-040/change-spec.md)、[ExecPlan](work/archive/QLM-DATA-040/plan.md)；active副本已移除，独立work-registry和索引同步。既有WAM v2 DATA-020/v3 DATA-010此前已完成归档，本次不重开、不新增模型工作。监看保持停用。

本次用户只授权验收登记与归档；不训练、不连接AMD、不commit/push、不发布HF。新增600未发布；原private HF400不变。正式数据验收不自动改变原TRAIN/EVAL输入声明。
