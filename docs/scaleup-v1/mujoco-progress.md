---
id: QLM-MUJOCO-PROGRESS
type: current
status: accepted
related_work: [QLM-DOC-001, QLM-SIM-013]
source_map: []
---

## P0–P2 source publication — QLM-DOC-002 / 2026-10-13

The user now authorizes this P0–P2 source batch on the independent MuJoCo branch.
The publication records supersede earlier local-uncommitted wording for this
batch only. Initial implementation and closing-documentation commits are verified
through exact remote readback in workspace
`runs/audit/mujoco-p0-p2-source-publication-20261013-v1/`.
Initial source publication passed exact remote readback. Read final closing-documentation
heads from that receipt. P6 still freezes the final
ten-task/source/resource/admin bundle; this batch is not that later release.

# MuJoCo 整体进度与阶段交接

核对日期：2026-10-13（Australia/Sydney）。P0–P2 **本地工程验收已完成**。
最新P3进度：[十任务候选资产已导入并提供实际MuJoCo画面](p3-asset-review.md)。
后续请求已为每个task追加两个，当前共30个A/B/C选择；以最新对比画册为准。
用户要求先审阅资产，expert/pilot暂不继续；踢球语义已纠正为足球/篮球进入实际足球门。
后续用户已明确要求“开始推进P3”。当前 [QLM-SIM-014](work/active/QLM-SIM-014/plan.md)
推进任务、资产池、expert、正式 pilot 资格与容量验证；未进入 P4 批量合成或训练。

来源会话：`01a12ecf-e271-7573-983c-917082cd1c19`，标题
“MuJoco (1): 冻结工程起点与实施协议、RAMBOCore解耦、3-task适配”。
该会话最后的 QLM-SIM-013 / v3/DATA-002 收尾结论优先于此前“核心完成、补证待关闭”
的中间判断。接受依据是本地实际 receipts，不是仅引用聊天结论。

## 当前执行基线

- QLM：独立 `migration/mujoco-foundation`，起点 `189545f`。
- WAM：独立 `adaptation/v3-mujoco-sft`，起点 `35d94a7`。
- 实现位于 workspace 的 `repos/QLM-Bench-mujoco` 与 `repos/WAM-Policy-mujoco`。
  上述 commit 只是起点；MuJoCo 实现仍包含本地未提交文件，不能把起点 SHA 当作最终源码身份。
- 正式后续路线保持 CUDA-MJWarp / ROCm-MJWarp physics + Native MuJoCo rendering。
  当前本地验收使用 CUDA-MJWarp + **OSMesa**，Native physics 提供对照。
- 默认 task-camera 支架为 **v1-step-rig-lod-a02**，使用共享 selector/resource pins。
  Camera/preprocessing、render quality、mass/collision 和模型参数保持已验收配置。
- Box/Basket 的 EGL 未通过既定视觉 gate；用户明确继续使用 OSMesa。
  不再将 EGL 优化列为 P0–P2 收尾阻塞，也不把它标记为已验收。
- 原 Isaac checkouts、历史数据/模型/normalizer/source identities 和环境 lock 保留。

运行说明见 [当前工程基线](mujoco-foundation.md)，资源选择见
[默认 LOD 与清理边界](decisions/mujoco-default-rig.md)。

## 阶段状态与证据边界

| 阶段 | 当前状态 | 已具备的证据或尚需交付 |
|---|---|---|
| P0 | 本地完成 | 源码与 Work-ID、接口、独立环境、版本/资源身份、CUDA/ROCm 候选矩阵；AMD 仍为 not_run |
| P1 | 本地完成 | RAMBOCore、原 controller checkpoint、Native/CUDA、Isaac 对照与 R01–R10 修复；控制、接触、reset/world 隔离的有界证据 |
| P2 | 本地完成 | 三任务 expert 与真实 WAM 闭环、render mirror、当前 LOD Raw/Canonical/VAE/10D；hinge、初态随机化、零步进 reconstruction/reset 与 RGB 同步 |
| P3 | 不属于本次发布；尚未验收 | 十任务正式 asset pool、合法范围、goal/horizon、Recovery、pilot 资格和生产容量仍为后续 gate；本地进行中的 P3 改动未包含在此 branch 发布批次 |
| P4 | 待推进 | 1000 条新 MuJoCo accepted demonstrations、800/100/100 split、双比例轴与100个固定 Standard EvalCases |
| P5 | 待推进 | 在既有模型代码和三任务工程 bridge 上实现十任务 reader/cache/prompt、task-balanced episode/window sampling、train-only normalizer 与 full-SFT 适配 |
| P6 | 待推进 | 固定双 repo commit、HF data/asset/case revisions、合法资源交付、完整管理员 bundle 和 pre-submit gate |
| S0–S5 | not_run | AMD 环境、ROCm/gfx950/OSMesa、全量数据、真实单/八卡 SFT 和短闭环 smoke，随后综合 SMOKE_GATE |
| F1–F4 | not_run | 新 MuJoCo 数据的正式 SFT、checkpoint publication/strict reload、100-trial evaluation 和归档 |

既有 Isaac 数据上的 AMD SFT 不构成本轮 F1 完成；P2 工程 bridge 不等于 P5 十任务训练适配完成。
本地 completion 不授予 AMD 执行通过状态，也不声明100个正式 EvalCases 已冻结。

## P2 收尾的具体事实

1. **当前 LOD 数据 readback：** Push/Press/Lift 各一条2.02s工程记录，每条101 actions、
   102 boundaries，共303/306。Raw/Canonical/media/provenance 验收和真实 frozen VAE、
   LeRobot、root-link/body-frame 10D readback 通过；latent 为 `[1,48,7,24,20]`，
   state 为 `[25,10]`，实际采样间隔80ms。未拟合 normalizer。
2. **物理与重建补证：** Native/CUDA 两个 world 的被动 object hinge 由真实碰撞驱动；
   序列化初始状态、seed、零步进 reset、其他 world 隔离、非法状态原子拒绝、完整 articulation
   mirror 和实际 RGB 同步通过。Hinge fixture 是非-task 诊断，不是第四项正式任务。
3. **真实 WAM 短闭环：** 原 step1000 checkpoint 在三任务各两次2.02s运行，
   606 commands、96次冻结 RPC、18路原始720p视频；feedback、KV eviction、reset、terminal通过。
4. **完整 horizon 的首轮观察：** Push timeout24s，Press 原判据 success5.76s，
   Lift timeout24s；无 falls、无 outcome-selected retries。共2688 commands、342次冻结 RPC、
   9路原始视频。Press 显示机头/前躯接触，不据此声称 FL 按压技能通过；用户确认当前模型
   仅在 Push Box 上训练，该现象不是 P2 阻塞，success predicate 不变。

这些记录均为工程诊断。正式 MuJoCo demonstrations 计数仍为 **0/1000**；
三次完整 horizon 的观察不构成正式 SR 或 Macro SR。

最终收尾： [QLM-SIM-013 决定与证据](decisions/mujoco-p0-p2-closeout.md)、
[归档 ExecPlan](work/archive/QLM-SIM-013/plan.md)，WAM 对应 v3/DATA-002。
实际 receipts 位于 workspace：

- `runs/audit/mujoco-p0-p2-closeout-20261013-v1/completion.json`
- `runs/audit/wam-v3-default-lod-rollout-20261013-v1/completion.json`
- `runs/audit/wam-v3-default-lod-full-rollout-20261013-v1/completion.json`

本次文档同步重新校验上述三份 receipt 引用的23个 evidence hashes，未重新运行 simulator、
模型或媒体完整解码；原16个受影响 tests通过和1个显式资源测试 skip 的验收范围保持原记录。

## 后续交接与防止范围混淆

- 下一阶段是 P3；先冻结各 task 的 asset pool、接触机制、predicate/horizon、随机化范围和
  Recovery，再做正式 pilot。新增七任务各10条合格 pilot 计入最终100条，旧三任务也须正式资格验收。
- OSMesa 成本已有测量，1000条生产容量仍需按最终 task/pilot 冻结。不能将旧短 clip 成本
  外推当作当前 LOD 或七个新任务的生产吞吐验收。
- P5 和 P6 的准备可按总体计划与任务工作并行，但不由本次进度同步自动启动。
- 原 Isaac scale-up 的 QLM-DATA-001 保留其独立历史状态，不计入 MuJoCo quota，
  也不从其 active 标记推断新 MuJoCo collection 已开始。
- 旧 payload 清理 receipt 保持不可变。历史路径/哈希描述原运行，不保证文件仍在；
  当前 LOD 新 evidence 和保留模型使用各自明确身份。
- AMD 只由管理员在 P6 完整交付后进行一次条件化提交；所有 required gates、profile/hash
  和联合执行验收通过才进入 F1。该阶段状态由 [平台矩阵](decisions/mujoco-platform-features.md)说明。

本次治理同步：[QLM-DOC-001 已归档](work/archive/QLM-DOC-001/plan.md)，对应 v3/DOC-007；证据位于 workspace
`runs/audit/mujoco-progress-sync-20261013-v1/`。不修改 implementation、既有归档或运行结果，
不进行新采集、训练、AMD 访问、commit/push 或发布。
