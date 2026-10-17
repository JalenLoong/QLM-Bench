---
id: QLM-DATA-031
type: change-spec
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
