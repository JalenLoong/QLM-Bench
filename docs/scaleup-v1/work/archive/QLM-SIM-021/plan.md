---
id: QLM-SIM-021
type: exec-plan
status: completed
related_work: [QLM-SIM-020, QLM-DATA-028]
source_map: []
---

# Room Door较低把手/完整锁机构候选资产

用户明确选择“允许提出较低把手/锁机构的新asset profile，审核后重新做物理与reference验收”。本Work只准备具体可审核资产，不把路线批准当作具体资产、动态物理或reference已获批。

保留原35cm A/B/C、旧失败/成功trace及原已验收400。使用独立proposal目录；仍A primary、B/C backups，总pool最多3。先比较29/30/31cm的原retained IK→FK、motor限位余量和既有实际body-envelope，再选择统一推荐高度；高度候选分析不构成多套正式pool。原controller/IK/PD/QP/history/checkpoint/native9/500-100-50Hz/camera/任务success条件保持。

整套lever、cam、bolt、strike/socket及配套面板的相对位置必须一致平移，保留机构形状、质量、摩擦、弹簧、铰链和真实锁舌关系。不能只降低可见handle。静态compile/mj_forward与几何测试允许，mj_step、actor inference、WAM、动态验收、reference/100、AMD/发布/commit/push均not_run；用户批准新资产后再进入后继动态验收。

验收证据：可复现generator及parent/new资源hash；原IK/FK误差与限位/净空并列报告；独立机制几何审计；A/B/C静态overview、front/side和锁机构近景；页面/图片链接与source保护检查。静态可达不宣称新gait或任务成功。原范围不按本次结果缩减。

## Progress

- [x] 用户路线选择与Work ID记录。
- [x] 原IK/FK及真实body-envelope只读高度/站位比较。
- [x] 选定一个统一推荐高度，生成独立A/B/C proposal。
- [x] 独立mechanism/robot/camera静态审计与NativeEGL预览。
- [x] 形成review与治理收尾，保持新资产用户审核pending。

## 实际交付与审核边界

推荐28cm完整机构独立profile，A primary/B-C backups；静态分析、120父文件保护/生成复现、独立192规定姿态机构及相机审计、6初态零步检查、NativeEGL36图与review已完成。主证据workspace runs/audit/door-lowered-asset-review-20261016-v1/proposal-report.md、independent-mechanism-audit.json、proposal-static-final-verification.json、static-render.json、source-preservation.json。

1mm是本次静态分析容差，不能写成原RAMBO gate。A220静态姿态/额外最小3.26°/误差最大.104mm/净空3.99mm/硬碰0；B在共用路径4calf擦碰，未取得操作资格。静态结果不证明未来actor、平衡、真实unlock/push或scope。

本Work工程材料交付但status仍active，等待用户对28cm具体A/B/C的asset approval；physics、controller inference、reference及formal均0。先前用户只批准提案路线。获批后再做实际物理与reference，不自动承接旧高度资格。文档与交付核对见同审计目录delivery-verification.json及governance-checks.json，不声明W&B/训练/发布结果。


## 2026-10-16具体资产获批

用户明确批准28cm A primary/B-C backups，独立receipt在workspace runs/audit/door-lowered-reference-20261016-v1/asset-approval.json。原proposal/pending记录保留历史；后继QLM-SIM-022进行真实物理资格，QLM-DATA-028继续高质量reference/完整范围并集中交审。资产批准不等于动态或reference批准，未授权formal100。
