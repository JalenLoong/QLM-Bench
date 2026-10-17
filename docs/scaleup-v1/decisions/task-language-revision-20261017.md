---
id: QLM-TASK-LANGUAGE-REVISION-20261017
type: decision
status: accepted
related_work: [QLM-DATA-041]
source_map: [src/qlm_bench/tasks/prompts.py, src/qlm_bench/tasks/registration.py]
---

# 用户指定的十task instruction修订

用户2026-10-17明确给出以下精确文本，并授权新增600发布到既有private HF dataset、原400仅prompt及必要校验依赖更新，以及治理后commit/push三个实际MuJoCo repo的全部未提交源码/文档改动。此授权覆盖旧时点“不HF/不commit”限制；不包括训练/AMD/physics/render重跑，不自动切换历史TRAIN/EVAL数据输入。

| Task | Exact instruction |
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

当前registration以user-prompts-20261017-v1为明确语言版本；Press文本原样不变，其余九项保留previous_instructions用于识别历史scene profile。current_instruction_profile仅在副本中替换已声明历史instruction及source_profile的task_text/instruction，保留source_instruction，拒绝未知语言；on-disk模型、物理参数、源manifest和frozen-source不改。测试检查纯JSON入口的语言更新和原文件不变，不运行physics。

新的发布副本Raw task_text/profile和Canonical task/action-segment文字一致，物理源manifest保留采集当时instruction；原始工作区采集数据和工程/人工receipt不回写。旧400的policy/Observer视频、Parquet数值、snapshot/command/terminal保持字节一致，Press100整个原payload不变；现有metadata仅修改语言及capture/provenance/manifest/contract/checksum/release的必要hash依赖。新增600采用用户已批准动作和最新左后Observer，不把旧失败变成新成功。

各task文本embedding以原冻结tokenizer/text encoder在无梯度模式生成一次，与精确instruction和encoder版本hash绑定。没有训练、optimizer、VAE或WAM策略再次验证；原embedding/cache保留为历史，模型cache不上传到dataset或GitHub。

HF先在基于精确原main的临时branch上传已验收差分，验证全文件LFS/Gitblob身份、代表性Raw/Canonical/snapshot回读、精确文字及1000/800-100-100/200-800，再保护旧HEAD更新main。Isaac-based完整旧SHA和private保持。原始source/provenance的历史commit身份不因后续commit而改写。

当前执行和实际远端revision以[QLM-DATA-041计划](../work/active/QLM-DATA-041/plan.md)和workspace审计mujoco1000-prompt-publication-20261017-v1为准；尚未生成成功receipt时不得宣称已发布1000。
