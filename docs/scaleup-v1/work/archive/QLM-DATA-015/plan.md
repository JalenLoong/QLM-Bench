---
id: QLM-DATA-015
type: exec-plan
status: completed
source_map: []
---

# Push Box automated synthesis Phase 0–6

## Authority / scope

User authorizes the complete Phase0–6 delivery, not merely planning:10 qualified
Push formal pilots,2Clean/8Randomized alltrain,primaryBox05,OSMesa,360p50FPS and
bothWAM routes. Paired QLM-DATA-015 / shared-v2 DATA-016 / v3 DATA-006.
Only two review gates: high-quality reference plus retarget scope, then ten-pilot
quality/coverage/throughput before100. Stop before dependent production at gate1.
No100/other tasks,AMD,training,publication or commit/push. Do not restore discarded
P3 assets or the retired QLM-SIM-015 experiment.

## Accepted corrections

Execution500/100Hz does not mandate retaining every high-frequency diagnostic.
Audit actual Raw requirements; preserve required fields,50Hz actual boundaries,
render snapshots,complete confirmations and terminal. Diagnostic retention is
explicit and purpose-scoped; never change controller history/physics stepping.
Task success is unchanged. Behavior eligibility is separate;unknown FL contact
is unknown,not automatic rejection. Reject only on reliable actual evidence.
Clean allows small real geometry changes near nominal. Splits sample distinct
configurations from the same approved ID distribution;no disjoint range/OOD rule.
Deduplicate physical trajectories and near-duplicate configs across splits.
Keep primary+2backup maximum;pending backups do not block approved primary.
Review old ten traces individually without relabeling,counting or deleting them.
Pure rendering changes permit rendition;changed executor/reference physics needs
new actual execution. Two backgrounds,no clutter,no forcedRecovery.

## Progress

- [x] Actual three clean worktrees/source baseline inspected and Work IDs reserved.
- [x] Phase0 contract/storage/source/assets/quality audit and candidate definitions.
- [x] Phase3 reference analysis and high-quality actual reference; user accepted reference quality.
- [x] Phase4 bounded retarget evidence and user reference/scope review.
- [x] Phase1/2 targeted trace/render reuse and actual dual-WAM verification.
- [x] Phase5 coverage-aware candidate/recording queue.
- [x] Phase6 ten formal pilots and engineering review package delivered.
- [ ] User final ten-pilot quality/coverage/throughput review before100.

## Validation and recovery

Use existing simulator environment and immutable original resources. Evidence:
workspace runs/audit/automated-push-quality-20261014-v1/.
Record actual attempts only; preserve oldsource/traces/models/pilots and failures.
New candidate failures retain lightweight summaries. Missing/uncertain contact
requires review,not fabricated confirmation. No trace/rendition can count twice.
Record per-task progress,discoveries,decisions,checks and not_run below. Archive
only after required delivery gates; pending human reviews remain explicit.

## Actual first review checkpoint — 2026-10-14

Phase0 actual source/Raw field/asset/quality/split audit is recorded. Current
Raw validator explicitly requires2N controller/10N+1physics rows;retain required
fields for this reference/Raw compatibility check,not a blanket diagnostic rule.
Offline review of original reference and each oldpilot preserves all identities:
8/10 show measuredbody-midline crossing duringpush; botholdClean initial physical
configs are identical despite differentseeds. Allten remain individually review
pending,not invalidated or automatically admitted.

New bounded high-level reference candidate changes only basevy duringstraightpush
with a smoothstateless working-lane correction;retainedFLworldpath,basevx/yaw,
RAMBO/IK/physics/camera/taskpredicate unchanged. Nominal42 attempts succeed at8.90s
and9.22s. LateFLhip minima are-27.58/-27.47degrees versusoldreference-55.02degrees;
bodyy minima0.0592/0.0597m andzeropushmidlinecrossing. Results arenotbitwiseequal;
no universal posturethreshold or resolveddeterminism claim. Quality needs userreview.

Declaredretarget(+.04,+.035,+.06rad,seed104) and(-.04,-.035,-.06rad,seed105) both
timeout24s,withoutfall. Onlylightweightfailurelogs/config/results are retained.
Retargetscope is NOTadmitted;no range was silentlyreduced andnoformalpilot started.
Current candidate isnot a frozenproductionrecipe. Phase3/4 userreview and technical
scope closure remain gates beforePhase5/6;the fullten-pilotobjective remains active.

Firstnominalmedia was rendered butCanonical rejectedmissing source_commit in the
newrunner;originaltrace/failureoutput retained. Runnerlineage was corrected before
the planned nominalrepeat. RepeatRaw/Canonical/threeoriginalvideos pass,461actions/
462boundaries,360p50FPS andObserver720p25FPS;previewfullydecoded. Renderingnever
executesphysics/controller. Capturedsourcehashes are backed by exactsource snapshots.

New separatequalityreport treatsunknowncontact asunknown,not failure,and incidental
bodycontact asreviewevidence ratherthan a rejectionpredicate. Explicitreview-mode
traces donotapplylegacyFL-counteligibility;formalexport rejectsreview-pendingtraces.
Legacyprofilebehavior is retained. Sourcewithnewworkidentity isrecorded byrecorder.

AffectedCPU tests20pass;finaldocs/governance/boundary/diff checks and protected
source/inputverification are stored in theauditroot. NewWAMmodel/readback/normalizer/
SFT/AMD/publication are not_run. Existing360p dualconsumeracceptance remains.
Threepairedplans remain active;this isnotPhase0–6completion orpilotapproval.

## User reference quality approval and continuation

User explicitly approved the displayed reference-repeat-a01 quality and requested
continuation. Exacttrace/video identities are in workspace
runs/audit/push-retarget-scope-20261014-v1/reference-approval.json.
Referencequality is accepted;retargetscope isnot yet accepted. Keep the accepted
reference unchanged and diagnose the declaredoffset failures. Newretarget changes
need boundedactualvalidation;do not silentlyshrinkranges orstart formalpilots.
Two-background/coverage work maycontinue independently. Otherconstraints remain.

## Retarget 后续实际进度

用户已接受 reference 动作质量，原 reference 保持。轻量1Hz诊断确认原失败点存在
Y方向 footprint 越界。新有界 cross-track 反馈在两个原失败点成功，再加入每command
8mm世界目标步长上限，改善阶段衔接。六个预声明开发配置全部成功，模拟时长8.82–9.06s；
无falls、无按结果替换seed，推动阶段未测到足端越过body中线。不是统计SR或全域保证。

两套背景资源、相同state实际OSMesa比较及非视觉参数校验已通过。Goal平移同时更新
原绿色边框与数值区域，大小和task predicate不变。开发runner继承旧ap00标签的缺陷
已记录并修正；原trace不改写，新ap01来源回归成功并正确记录preset/resource/recipe。

代表性ap00/ap01已通过Raw/Canonical及双WAM的原冻结VAE、原normalizer、cache、
SFT-input和online初始/feedback诊断，不进行训练或改变正式训练准入。新的metadata
修复回归独立记录。完整材料位于 workspace runs/audit/push-retarget-scope-20261014-v1/。

当前等待用户审核retarget候选范围：Box dx±4cm、dy±3.5cm、yaw±0.06rad；goal
平移dx±3cm、dy±2cm。没有缩小原偏移范围。Phase5/6的新正式pilot尚未启动，
完整十条目标保持active。Primary仍为Box05，两个backup只登记；原十条逐条待审。

## Retarget 范围获批，启动十条正式 pilot — 2026-10-14

用户明确回复“审核通过，继续推进”，通过已展示的 reference/retarget 第一审核点。
继续既有 QLM-DATA-015 / v2 DATA-016 / v3 DATA-006，冻结 smooth-v3 与两套背景。
正式采样仍为 Box dx±4cm、dy±3.5cm、yaw±0.06rad，goal dx±3cm、dy±2cm；
2 Clean 有小幅真实几何差异，8 Randomized 覆盖正负和组合偏移，全部 train。
每槽预声明5个候选，最多30次实际尝试，连续10次失败即停；不按结果收缩范围。
复用 PhysicalTrace 与 RenditionQueue。先保留最多十条成功 trace，再冻结独立
recording profile；这是本轮有界缓冲，不是100/1000条积压策略。
保留独立行为证据与完整 task success 判据；contact unknown 不自动拒绝。
旧十条不计入新批次：新 executor 要求新的实际执行，旧身份和逐条审核记录保留。
审计根为 workspace runs/audit/push-formal-pilots-20261014-v2/。
十条最终动作质量/覆盖/吞吐仍须用户审核；无100、其他任务、训练、AMD、发布或commit/push。

## Phase5 实际冻结与 Phase6 physics 完成

已冻结10槽/50个预声明candidate，实际使用11个candidate得到10条成功trace，
共4463 actions / 4473 boundaries；其中一条负向偏移candidate在24s timeout，
未倒地，按既有预声明同区间候选重试后成功。所有失败保留轻量记录。
Phase5单写者/断点恢复/跨重启预算检查通过；十条trace目前进入独立render-only队列。
独立质量证据和用户reference/scope批准绑定到recording profile，原task predicate不变。
formal pilot最终动作质量、覆盖及吞吐仍未获用户批准，不扩量100。

## Phase1/2 复用的本批实际验证

新批次代表性Clean01和Randomized08正式Raw/Canonical与渲染队列验收通过。
v2/v3各自实际Reader、原冻结VAE、原normalizer、cache回读、SFT-input及online
initial/feedback与offline对应关系全部通过，共4个实际readback；v3保留原10D。
没有optimizer更新、模型修改、normalizer fitting或policy-performance声明。
其余8条媒体继续生成，未绕过最终十条用户审核。证据为本审计根readbacks/。

## Clean 背景配置修正与当前审计根 — 2026-10-14

后续逐项核对handoff发现初批第二条Clean错误分配ap_01；Clean必须ap_00。
这是实现配置遗漏，不是用户批准的范围变化。旧批次暂停，全部trace/媒体/日志保留于
runs/audit/push-formal-pilots-20261014-v2/，configuration-correction.json记录纠正。
当前执行根为runs/audit/push-formal-pilots-20261014-v3/，正式数据根为
data/qlm_bench/push-approved-pilot-20261014-v3/。第二条Clean已用ap_00重新执行成功，
其余九条trace原路径/原hash/原物理身份保留；五条合规旧媒体可经精确hash校验重新封装，
记录原render lineage，不冒充新物理或新渲染。新profile强制Clean ap_00并有回归测试。
共实际12个candidate：10条本包合规成功、1次timeout、1条成功但背景配置不合规的历史样本。
当前十条共4464 actions / 4474 boundaries；最终用户审核仍pending，无100/训练/AMD/发布。

## 十条新正式 pilot 技术交付；等待最终用户审核 — 2026-10-14

QLM-DATA-015 / v2 DATA-016 / v3 DATA-006 的 Phase0–6 工程交付完成，保留 active
等待既定的十条pilot动作质量/覆盖/吞吐审核。当前审计根为
runs/audit/push-formal-pilots-20261014-v3/，review.html/report.md为最终审核入口；
数据为data/qlm_bench/push-approved-pilot-20261014-v3/。2Clean均ap_00；
8Randomized覆盖ap_00/ap_01及批准的box/goal范围，全部train、仅primaryBox05。
最终4464 actions / 4474 boundaries；原判据、native9/RAMBO、physics/camera保持。
实际共12个candidate：10条合规交付、1次timeout、1条成功但Clean背景配置错误的
历史样本。修正只新执行一条Clean，保留九条合规trace；五条已完成媒体逐字节复用，
原render lineage显式保留。错误批次和全部历史证据保留，不隐去配置纠正成本。
全部Raw/Canonical/terminal/媒体/原telemetry验证通过；双WAM各自Clean/Randomized
实际原VAE、SFT-input、online反馈与cache检查通过，另有十条完整采样RGB与action/
timestamp/tail读取，两路线逐字节一致。无normalizer fitting、训练或policy性能声明。
QLM当前回归140pass/13skip；WAM v2/v3基础回归131/59pass，socket沙箱失败及
复核记录保留。本批未知contact不自动拒绝，task success和demonstration quality分离。
保持最终用户审核gate；没有100、其他任务、AMD、训练、commit/push或远端发布。

## 用户最终批准

用户已审核通过全部十条pilot，批准计入Push Box100条并继续扩量。Phase0–6关闭；新执行按QLM-DATA-016，task级WAM验证规则按v2 DOC-012/v3 DOC-011。旧记录保持原阶段语境。
