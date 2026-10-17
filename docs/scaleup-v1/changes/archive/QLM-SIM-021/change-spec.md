---
id: QLM-SIM-021
type: change
status: completed
related_work: [QLM-SIM-020, QLM-DATA-028]
source_map: []
---

# Room Door较低把手/完整锁机构候选资产

用户明确选择“允许提出较低把手/锁机构的新asset profile，审核后重新做物理与reference验收”。本Work只准备具体可审核资产，不把路线批准当作具体资产、动态物理或reference已获批。

保留原35cm A/B/C、旧失败/成功trace及原已验收400。使用独立proposal目录；仍A primary、B/C backups，总pool最多3。先比较29/30/31cm的原retained IK→FK、motor限位余量和既有实际body-envelope，再选择统一推荐高度；高度候选分析不构成多套正式pool。原controller/IK/PD/QP/history/checkpoint/native9/500-100-50Hz/camera/任务success条件保持。

整套lever、cam、bolt、strike/socket及配套面板的相对位置必须一致平移，保留机构形状、质量、摩擦、弹簧、铰链和真实锁舌关系。不能只降低可见handle。静态compile/mj_forward与几何测试允许，mj_step、actor inference、WAM、动态验收、reference/100、AMD/发布/commit/push均not_run；用户批准新资产后再进入后继动态验收。

验收证据：可复现generator及parent/new资源hash；原IK/FK误差与限位/净空并列报告；独立机制几何审计；A/B/C静态overview、front/side和锁机构近景；页面/图片链接与source保护检查。静态可达不宣称新gait或任务成功。原范围不按本次结果缩减。

## 已形成的具体提案

推荐统一28cm（原35cm），完整机构下移7cm；独立A/B/C与review已形成，静态证据及限制见配对ExecPlan和workspace runs/audit/door-lowered-asset-review-20261016-v1/proposal-report.md。用户具体资产审批仍pending，本Work保持active，不进行动态物理/controller/reference。


## 2026-10-16具体资产获批

用户明确批准28cm A primary/B-C backups，独立receipt在workspace runs/audit/door-lowered-reference-20261016-v1/asset-approval.json。原proposal/pending记录保留历史；后继QLM-SIM-022进行真实物理资格，QLM-DATA-028继续高质量reference/完整范围并集中交审。资产批准不等于动态或reference批准，未授权formal100。
