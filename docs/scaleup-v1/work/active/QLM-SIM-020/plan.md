---
id: QLM-SIM-020
type: exec-plan
status: active
source_map: []
---

# Approved remaining-six18 assets Native/CUDA physical contact/articulation/reset/mirror qualification; no RAMBO parameter change

## 本轮reference收束：四项完整通过，Oven范围未通过，Door待决策 — 2026-10-16

QLM-DATA-028当前有5个nominal物理成功candidate，只有4个task完成原范围工程验收：Fridge a04 16/16、Drawer a07/v5 16/16、Valve a07/v7 16/16、正前方Sweep a15 32/32。Sweep独立2physics/single-writer实际31.35min，244 sources保持，无资源/物理/infra失败；不是正式生产吞吐或policy SR。五份三视角视频在workspace runs/audit/remaining-six-reference-20261016-v1/review.html，Oven明确单列为范围未过的诊断candidate，页面不是整批完成/用户批准。

按用户将Oven放最后且不无限重试的要求，最后仅修高层阶段门控的一条a04真实29.28s关门成功，原RAMBO/资产阻尼/3°三tick判据保持。45°初态仍自然落90°后接触；FLhip参与支撑及27.6s单次较快转姿显式待人工审视。原16角点首2项均60s timeout，余14未执行，首次失败后停止派发并排空；source不变、不缩范围、不再调参。Oven因此不计工程就绪。详见pairs/fridge-oven/oven-final-structured-summary.json。

Room Door仍无合格reference，原controller近限位/gait和一次实际快速接近失败证据已汇总。降低handle及联动lock的新profile、独立controller评估或暂缓Door三项已集中询问用户；答复前不改asset/controller或继续physics，推荐项不等于授权。决定待办为同审计目录pending-door-route-decision.json。

当前全部reference physics/writer已停止，QLM-SIM-020/DATA028、v2DOC025/v3DOC024保持active等待关键决定与整批审核。原已验收400、18原候选资源、原RAMBO source/checkpoint、相机/action/state契约保持；新formal0，不WAM模型/cache/训练/AMD/commit/push/发布。最终随机十条人工验收延后至所有task合成完成后统一，不恢复10pilot人工gate。以下进行中/待范围的叙述仅描述历史快照。

用户已批准六task A primary/B-C backups；保留approved18候选原geometry/mass/friction/articulation与全部旧400/旧source。先真实物理资格，再原RAMBO/native9 reference，六条及适用范围集中交审；未批准整批reference前不任何100，无10pilot人工gate。原500/100/50Hz、双640x36050FPS/Observer720p25FPS、force-zero、task success/quality分离、两背景/无clutter/无强制Recovery、NativeCPU/EGL3+3和1GiB/7.6GiB/0.5GiB/4GiB资源保护保持。新task数字目标在reference profile声明为待用户整批审核的新predicate，旧四task不修改；不能用teleport、weld、隐形锁/辅助力制造reference。被动初始速度诊断独立标记，不作demo。失败轻日志，成功trace保留；WAM task一次兼容留正式production，不运行WAM/cache/fit/训练/AMD。HF400由独立DATA026/monitor继续，禁止第二写者。W&B not_run/local-only。

- [x] 固定18 approved资源/原controller/old400/source身份及实际attempt记录。
- [x] 完成18资产Native机制检查及18/18 CUDA集成/reset/完整timestamp镜像；Oven C真实floor stop限制独立保留，不宣称全部hinge端点通过。
- [ ] 六task各一条实际原RAMBO高质量reference、任务专属成功证据与独立动作质量。
- [ ] 各task预声明retarget范围、两背景、完整边界真实复验，不按失败静默缩范围。
- [ ] 双正式RGB/Observer/terminal与集中审核页；数据/formal0，不跨用户gate。

## 物理证据已汇总，整批reference仍在开发 — 2026-10-16

workspace `runs/audit/remaining-six-reference-20261016-v1/physical-qualification-summary.json`
固定Native三组原始报告与CUDA18/18结果的路径/SHA。Native详细机制检查和CUDA集成、
双world隔离reset、完整同timestamp NativeEGL镜像为不同验收范围，不能互相替代，
也不证明AMD或原RAMBO完整任务成功。Oven C受原真实floor挡止，未到-90deg hinge端点，
仅记录带限制的close操作资格；Door初始动量探针的真实cam/bolt响应不冒充RAMBO解锁。
未修改任何批准资产的mass/friction/spring/solver，原失败探针保留。

四个nominal reference和Fridge16角点当前已具真实成功证据；Sweep范围存在失败，
Oven/Door仍开发。准确快照与后续推进归QLM-DATA-028，六task集中用户审核前formal0。
本Work继续active等待配对reference交付，不提前归档整批验收。
