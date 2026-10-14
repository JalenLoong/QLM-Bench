---
id: QLM-AUTOMATED-SYNTHESIS
type: decision
status: accepted
related_work: [QLM-DATA-011]
source_map: []
---

# 自动数据合成 — 2026-10-13

用户明确授权 M0–M6，只贯通 Push Box 并交付10条正式 pilot，审核前不扩到100条或其他任务。
沿用 P0–P2 与默认 LOD a02 + CUDA-MJWarp / Native OSMesa，不恢复已撤销的 P3 资产。
来源计划及 SHA 位于 workspace `runs/audit/automated-push-synthesis-20261013-v1/`。

少量真实 reference → 阶段 TemplateBundle → 新场景 retarget/native9 → 原 RAMBO 实际执行
→ 成功 PhysicalTrace → 离线 state replay → Raw/Canonical/consumer validation → accepted slot。
无渲染执行不创建 GL/renderer/encoder；render worker 不加载 RAMBO/WAM，不推进 physics。
保留实际 commands/state/100Hz controller/500Hz physics telemetry、N/N+1 与 pre-reset terminal。
离线 RGB 明确记录 `recording_mode=offline_state_replay`，不改变模型 observation。

新数据每任务100条、20 Clean/80 Randomized、80/10/10 split；取消强制 Recovery 配额。
本轮10条为2 Clean/8 Randomized且全部 train；自然纠正可保留，禁止故意制造错误。
新物理失败只保留轻量日志，清理本次临时 payload；成功 trace 保留供录制恢复。
历史失败证据与所有旧产物不受此新规则影响。Reference/template/source identities 保留；
batch 不逐 candidate 调用 GPT，也不新增 GPT model/version/prompt provenance。

仍保留 full-footprint/not-fallen/three50Hz-tick success。正式 demonstration 还需检查合理
FL 操作、真实接触和数据质量。评测 cases 独立于训练成功筛选。

旧 Isaac scale-up 配额和发布后的 P3 路由段落只描述历史。P3 实现已撤销；
本轮接替数据生产路线，并非恢复旧 P3。P5/AMD/SFT/发布属于后续授权范围。
