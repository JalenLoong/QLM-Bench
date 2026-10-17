---
id: QLM-MUJOCO1000-PROMPT-PUBLICATION
type: report
status: accepted
related_work: [QLM-DATA-041]
source_map: []
---

# 十task精确prompt与MuJoCo1000私有发布

## 十task精确prompt与private HF1000已验证发布 — QLM-DATA-041 / 2026-10-17

用户指定十句prompt已作为user-prompts-20261017-v1发布；既有400仅文本与必要hash/索引依赖更新，视频/数值/snapshot/command/terminal不变；新增600采用最终已验收版本，四项Observer为左后侧。main实际revision=470e0a1f290ef65a25ca1933a91a51ccd6427fcf，payload=b84488eca8a723767cef27fa455ec2ea8169f81c；private=True，Isaac-based=519725c8bc77b35fd5d3b4ac8555a3e96a8876a7保持。1000条=10task各100，800/100/100 split和200Clean/800Randomized，964151actions/965151boundaries。全远端LFS/Gitblob、20条Clean/Randomized独立data-only回读、精确prompt/索引/原400非文本保护均通过。

原始采集source/frozen-source/历史prompt及receipt不回写，新正式发布语言版本单独lineage。原冻结text encoder无梯度生成十项embedding，无训练/optimizer/WAM策略重复验证/physics/render/AMD。HF数据发布不自动切换历史TRAIN/EVAL输入；源repo所有此前未提交tracked/untracked源码/文档由用户明确授权统一commit/push。当前GitHub提交状态见workspace runs/audit/mujoco1000-prompt-publication-20261017-v1/github-commits.json；物理执行不冒称运行于后续新commit。

| Task | Exact prompt |
|---|---|
| push_box | `Push the box inside the outlined area.` |
| press_button | `Press the button.` |
| lift_basket | `Lift the basket by its handle.` |
| kick_ball_to_goal | `Kick the ball through the goal.` |
| sweep_block_to_zone | `Sweep the block into the outlined area.` |
| close_fridge_door | `Push against the fridge door until the door closes.` |
| close_oven_door | `Push the oven door until the door closes.` |
| turn_valve | `Rotate the valve lever upward to the upright position.` |
| pull_open_drawer | `Slide your foot into the drawer handle opening and pull the drawer outward.` |
| open_room_door | `Press down the lever handle, then push the door open.` |

HF main：[完整1000数据集](https://huggingface.co/datasets/dontKnow23456/QLM-Bench/tree/main)。原始工程/人工验收、语言版本、Observer修订和源Git发布分别有receipt；本报告不替代历史物理source，不宣称新训练或learned-policy结果。
