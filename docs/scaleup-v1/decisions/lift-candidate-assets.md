---
id: QLM-LIFT-CANDIDATE-ASSETS
type: decision
status: accepted
related_work: [QLM-DATA-020, QLM-DOC-005]
source_map: []
---

# Lift Basket获批资产：A primary，B/C backups

工作在[QLM-DATA-020](../work/archive/QLM-DATA-020/plan.md)。真实静态审核包workspace `runs/audit/lift-asset-review-20261015-v1/review.html`；模型/生成器/资源来源与hash在其candidate.json、verification.json和source-license-review.json。

| 候选 | 来源/提手 | 当前状态 | 建议角色 |
|---|---|---|---|
| A | 原OASIS编织篮、单中央刚性提手、原32cooked hulls | Native/CUDA被动物理资格passed；独立asset license仍unverified，RAMBO reference待审核 | 用户指定primary；许可待办保留 |
| B | 独立生成浅色方篮、单中央直边提手、Native primitives | 静态compile/render passed；0.53kg/几何派生惯性；被动Native/CUDA资格passed；实际RAMBO操作not_run | 用户批准backup |
| C | 独立生成绿色方篮、单中央圆角提手、Native primitives | 静态compile/render passed；0.53kg/几何派生惯性；被动Native/CUDA资格passed；实际RAMBO操作not_run | 用户批准backup |

A原source unknown不改写；repo MIT不是对独立外部asset archive的覆盖证明。B/C不复制第三方mesh/texture，可在本项目完整重建；最终release license在发布阶段固定，本轮不进行新公共license grant。来源/许可核对是资产准备的一部分，用户视觉批准不能代替其资格。

A外轮廓约27.46×24.55×29.15cm；B/C约27.6×24.7×28.2cm，均0.53kg。B提手内净宽16.8cm/篮沿以上净高10.8cm；C轮廓不同，不预先承诺难度相同。仅静态取景，正式camera/default/profile/controller未变，不引入额外constraint/操作力。自建primitive的compound惯性由MuJoCo按uniform density计算并缩放质量，重叠solid计入双方体积；实际稳定性/friction/穿孔/托举contact必须在批准后验收。

每task最多1primary+2backup，不制造backup quota。资产审批→真实物理资格及高质量reference/retarget范围审核→10pilot审核→扩100/最终验收。pilot前冻结asset pool，物理语义修改重新验收相关pilot。原FL接触/整个basket最低点离地2cm/not-fallen/三个50Hz ticks保持，unknown contact不直接失败；独立demonstration质量检查不能改task predicate。

2026-10-15资产gate已通过，QLM-SIM-017完成针对性被动物理资格，QLM-DATA-020正在准备A真实reference与retarget范围供下一用户审核。旧静态阶段0physics/待审批陈述只保留原时点；未执行formal pilots/100、WAM验证、训练、AMD、commit/push或发布。

独立人类审批证据及物理资格在workspace runs/audit/lift-reference-20261015-v1/。用户primary选择覆盖此前B推荐；原静态review建议和当时的hash不改写。新范围提案dx/dy±3cm、yaw±5deg提前声明在retarget-proposal.json，尚未经用户批准，失败不得偷偷缩小；正式pool在reference/范围获批后pilot前冻结。

## 实际工程资格与reference交付

三资产针对性Native/CUDA资格通过，A实际v2高层recipe成功及八角点physical通过，完整media和state-sync通过；详见workspace runs/audit/lift-reference-20261015-v1/report.md。正式pool尚未冻结，DATA020用户reference/范围审核pending，Lift正式0。B/C只有被动资产资格，不冒充完整RAMBO/SFT qualification。source asset许可待办保持。

## Reference与范围已批准，pool冻结用于十条pilot

2026-10-15用户批准reference与dx/dy±3cm、yaw±5deg，两Background保持；DATA020归档，新[DATA021](../work/archive/QLM-DATA-021/plan.md)负责十条2Clean8Randomized alltrain及4physics+4render测试。新批准receipt/campaign/asset-pool在workspace runs/audit/lift-formal-pilots-20261015-v1/，不改原reference receipt。用户pilot质量审核仍pending，不能自动100。
