---
id: QLM-DATA-015
type: change
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
- [ ] Phase0 contract/storage/source/assets/quality audit and candidate definitions.
- [x] Phase3 reference analysis and high-quality actual reference; user accepted reference quality.
- [ ] Phase4 bounded retarget evidence and user reference/scope review.
- [ ] Phase1/2 targeted trace/render reuse and actual dual-WAM verification.
- [ ] Phase5 coverage-aware candidate/recording queue.
- [ ] Phase6 ten formal pilots,review report and user quality gate.

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

## 用户最终批准

用户已审核通过全部十条pilot，批准计入Push Box100条并继续扩量。Phase0–6关闭；新执行按QLM-DATA-016，task级WAM验证规则按v2 DOC-012/v3 DOC-011。旧记录保持原阶段语境。
