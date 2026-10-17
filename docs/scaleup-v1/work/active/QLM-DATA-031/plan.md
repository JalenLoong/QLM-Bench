---
id: QLM-DATA-031
type: exec-plan
status: active
related_work: [QLM-DATA-028, QLM-DATA-030]
source_map: []
---

# Oven最大开度50deg及两次reference重试

用户明确批准把相对于oven本体垂直面的最大打开角限制为50deg，执行两次真实reference重试。关门为0deg、打开为负q，因此新joint range=[-50deg,0]；保持此前45deg初始开度、原关门3deg/notfallen/三个50Hz tick，原RAMBO/core/IK/PD/QP/history/native9/500-100-50Hz/camera保持。新版A/B/C独立资源，仍A primary/B-C backup，旧资源/attempt/source不回写。真实MuJoCo joint limit提供约束，不逐步clamp qpos、不teleport或辅助力。记录软约束实际overshoot，不冒充数学硬截断。

第一轮复用原final-bounded高层recipe；第二轮依据第一轮证据做必要高层修正或有限验证，不超过两次。两条均保存完整50Hz诊断snapshot/commands/terminal与三视角视频；这不扩大正式失败candidate常规存储范围。独立single-writer预算/既有1GiBavailable与7.6GiBswap保护，最多原3physics+3render，本轮通常1+1。全部结果完成后交用户审核，不自动scope/100/WAM/AMD/发布。

Door A19本轮已获动作质量批准，由QLM-DATA-030负责新几何退出判据与及时terminal接入；原A19完整结果不回写，范围尚未完成。本Work只处理Oven两次。

## Progress

- [ ] 新版三资产joint limit和metadata/hash/compiled差异核对。
- [ ] 两次实际原RAMBO尝试，逐条保留真实成功/失败。
- [ ] 限位实际行为、媒体、状态与source核对及交审。

## Oven50deg两次已完成；第二次关门成功待动作审核 — 2026-10-16

QLM-DATA-031按用户要求完成两次，无追加第三次/无scope。第一次60s超时，第二次40.48s满足原3deg/三50Hz tick/notfallen；最大实际开度由50.679deg减至50.073deg，有限soft-limit超调据实保留。第二次有40个50Hz边界的Head接触记录，尚未量化关闭力矩，任务成功与动作质量分开，等待人工审核。审核workspace runs/audit/oven-limit50-reference-20261016-v1/review.html。

Door A19已获用户动作批准并选作reference；QLM-DATA-030显式runtime/新几何判据已接入，实际A19状态feed在24.40s触发成功，terminal后命令拒绝；未重跑Door physics，原A19结果和完整范围pending保持。原RAMBO/source/已验收400保持，无WAM/cache/训练/AMD/commit/push/发布。下方运行中记录仅为历史。


## Oven旧两条动作均被拒绝；35deg中央前推单次重试 — 2026-10-16

用户明确拒绝QLM-DATA-031两条动作质量，旧第二条task success保留但不作合格reference。新QLM-DATA-032授权最大开度35deg、中央前推，仅一次实际重试并给视频；初态35deg以遵守新限位。足端门局部Y0，机身Y-.18以FL对准中央；质量/原RAMBO/相机/原成功判据不改。旧资产/source/结果保持，无第二次、scope/100/WAM/AMD/发布授权。审计workspace runs/audit/oven-limit35-center-reference-20261016-v1/。

