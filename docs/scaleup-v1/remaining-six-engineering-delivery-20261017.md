---
id: QLM-REMAINING-SIX-ENGINEERING-DELIVERY
type: report
status: accepted
related_work: [QLM-DATA-040]
source_map: []
---

# 六task600条工程交付；最终人工审核待定

2026-10-17。Sweep、Fridge、Oven、Valve、Drawer、Room Door各100，全新600条已完成生产、完整工程检查和各task Canonical合并。原Push/Press/Lift/Kick400条人工验收保持；总计1000条已生产，但本次600条动作质量的最终用户验收仍pending，尚无新增HF发布。

| Task | Episodes | Actions | Boundaries | 累计实际physics尝试 |
|---|---:|---:|---:|---:|
| sweep_block_to_zone | 100 | 179671 | 179771 | 100 |
| close_fridge_door | 100 | 134921 | 135021 | 100 |
| close_oven_door | 100 | 78557 | 78657 | 100 |
| turn_valve | 100 | 63836 | 63936 | 100 |
| pull_open_drawer | 100 | 129843 | 129943 | 110 |
| open_room_door | 100 | 113725 | 113825 | 100 |

合计700553 actions/701153 boundaries、600唯一实际trajectory；累计610次physics=600成功+Drawer10次原超时。Door另有2次初始化import失败，0physics/0commands，不计物理尝试。失败与各版本source保持，不将其回写成成功。

每task20Clean80Randomized；train80/validation10/test10，分别16/64、2/8、2/8。各split共享批准ID支持域，无跨split近重复，固定controller seed42及预声明有界candidate。六task均为NativeCPU physics/原RAMBO CPU与Native MuJoCo EGL；原完整reset、recipe、native9/forcezero、500/100/50Hz、双RGB640×36050FPS与原相机保持。未修改任务物理、成功条件、schema或批准分布。

每task全量Raw/Canonical/实际snapshot独立成功判据/必需telemetry逐列/command/terminal/timestamps/source/媒体/去重检查及合并通过。六task一次双WAM24项实际兼容性检查通过，未fit/训练；扩量未重复模型验证。最终轻量跨task核对600唯一trajectory、所有实际frozen source、241primary文件、6reference媒体/nominal executor、原checkpoint、三repo HEAD和原WAM源码snapshot/实际consumer receipts。60审核视频hash、H264/1920×360/25FPS探测及HTML相对链接全部通过；正式双RGB仍50FPS，审核拼接只用于展示。

## 两项接入恢复与真实source

Door初次缺door_geometry import路径，独立open_room_door-v2修复依赖后按同100候选/recipe/seed/资产生产；实际成功adapter为几何v3，目录v2不代表旧成功条件，A19历史旧判据结果保持。

Drawer原nominal-only绑定漏接已批准scope-v5 fixture-heading adapter，021/024各5超时后停止。独立pull_open_drawer-v2接回原DrawerFixtureHeadingExecutor；nominal零步数值等价、无reference调参。两个slot各一次原c01实际复核成功；31原nominal-source成功原样保留、69scope-v5新成功，全部source/profile逐条保留，成功physics未重跑。累计110次Drawer physics见cumulative-attempt-summary.json；原completion的队列member计数100未包含旧10失败，最终汇总显式补齐。

## 最终人工审核入口与证据

workspace审计根为runs/audit/remaining-six-production-20261016-v1。review.html集中60视频；active-task-roots.json指定各task实际root。每task从完整100均匀无放回抽10，无质量、split、backend筛选；random10-selection.json保存固定seed，random10-media.json保存实际媒体hash。

各task completion.json、full-artifact-checks.json、accepted100.json为全量证据；最终跨task/保护审计为final-source-and-delivery-audit.json，审核媒体为random60-media-validation.json。数据在workspace data/qlm_bench/remaining-six-20261016-v1，每task都有raw/、episodes/视图及canonical/合并结果。原400数据及其既有HF发布保持；本次不训练、不连接AMD、不commit/push、不发布HF。

QLM-DATA-040工程目标完成、配对记录保持active等待用户最终审核，当前无新physics/render；30分钟监看已停用。用户确认后再配对归档；不得把本报告当作用户动作质量批准receipt。
