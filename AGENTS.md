## RL-v2 independent Push/Sweep tasks delivered — 2026-10-26

ALG-005/QLM-SIM-026 complete independent Push Box and Sweep Block bindings from the same SFT5000 with identical LoRA32/120-round numerical recipe. One shared single/eight-card smoke pair only (Sweep producer);16-job dual submission, separate calibration/preflight and independent train/export/publish/eval tails. Task-specific checkpoint/W&B/HF paths; cross-task resume rejected. RL simulator entries use existing task factory/accepted predicates. Read docs/current/rl-v2-dual-task.md and WAM README. Evidence: workspace runs/audit/rl-v2-dual-task-20261026-v1/completion.json. No formal references/calibration, AMD/Slurm/full5B/RL/validation or remote writes; source uncommitted/unpushed.

## RL-v2 independent review repaired — 2026-10-26

ALG-003/QLM-SIM-025 close the independent algorithm/AMD-portability/redundant-defense review. Final LoRA32/ten-demo/120-round profile unchanged. Target scene roots, configure+held Slurm chain, shared-rank attempts/timeouts/RNG, global logs and artifact admission repaired; repeated hashes and retired single-demo paths removed. Resume v3 requires rank-local RNG. Read docs/current/rl-v2-independent-review.md and WAM README. Evidence: workspace runs/audit/rl-v2-independent-review-20261026-v1/. No AMD/realSlurm/full5B/formalRL or remote writes; source uncommitted/unpushed.

## RL-v2 ten-demo LoRA configuration — 2026-10-26

User approved LoRA32/alpha32/dropout0 on30 blocks attn1/attn2/FFN; frozen original weights/projections/VAE/T5/RAMBO. Ten fixed Push train demos,8 strata each,B2 distinct demos/G4,H1,25/50NFE. LR3e-5/warmup10 actual updates/weight decay0/reference.05. EMA.9 only on optimizer updates (supersedes prior flat-round EMA).120 outer rounds/960 training candidates;validation40 current+EMA on10 held-out normal initial states;checkpoint20. Implementation task only; do not launch formal training/AMD/Slurm or remote writes. New CPU references/calibration not_run. See current RL page and WAM README.

## RL-v2 M1–M4 本地交付完成 —2026-10-26

隔离RL分支已完成mujoco-v2/ALG-001与QLM-SIM-023配对验收。两次CPU GT成功、27 anchors恢复、32H1+4H2真实SFT采样、8/8 preference groups、tiny CUDA精确恢复、2/8-rank Gloo及无.git部署检查通过。当前入口docs/research/rl-v2/；证据workspace runs/audit/rl-v2-local-m1-m4-20261025-v1/completion.json。真实5B backward、AMD/Slurm、正式RL/evaluation与远端发布均not_run；源码未commit/push。不得自动进入M5/M6或恢复旧评估。下方状态保留原日期/分支范围。

## Pending-source publication verified —2026-10-21

This branch source commit `cea9445300fac4d531699b7dd87690b0939691a0` has been pushed to every configured GitHub target and independently verified (commit/tree/changed blobs). See [publication status](docs/scaleup-v1/github-publication-20261021.md). Earlier execution/source identities stay unchanged. The separate v2 video2/action4 evaluation remains paused_before_launch with0trials; do not start/resume it without the user.

## v2 NFE2/4 evaluation 已按用户要求暂停 —2026-10-21

停在准备阶段，尚未启动controller/policy/client，0trial/0physics/0模型推理。新配置和QLM-EVAL-005、mujoco-v2/EVAL-003记录保留；不自动启动或恢复。实时状态：workspace runs/audit/mujoco-v2-sft5000-nfe2-4-evaluation-20261021-v1/workflow-state.json。原25/50评估结果与已删除监控保持原状。

## v2 step5000 NFE2/4 新评估已获授权 —2026-10-21

QLM-EVAL-005 active；同一v2 checkpoint和固定Standard100另跑100条，只改video/action NFEs为2/4。30blocksGPU/CPUVAE/BF16/window8保持。原25/50结果封存，不作为新结果复用；新run内部valid trial不重跑。实时入口workspace runs/audit/mujoco-v2-sft5000-nfe2-4-evaluation-20261021-v1/workflow-state.json；不要启动重复controller。原小时跟进保持已删除。

## MuJoCo SFT5000 闭环评估已全部完成并归档 —2026-10-21

QLM-EVAL-004及其两版/QLM配对工作已completed；v2=77success/23timeout，v3=67success/33timeout，各100valid、300实际+300预测视频。独立复核1200视频、原latent/CSV及CUDA events逐值一致通过。state/action稳态单步34.324/27.772ms。当前结果见docs/scaleup-v1/mujoco-sft5000-evaluation-20261021.md；权威交付workspace runs/audit/mujoco-sft5000-evaluation-20261020-v1/completion.json。原attempt/失败/执行source全部保留，无训练/AMD/远端发布。下方旧pending/旧placement叙述仅是历史，不恢复旧流程或自动重跑。

## Accepted evaluation observer source published —2026-10-18

QLM-EVAL-003 synchronizes accepted observer source8456b9ab352445028340315627ed0a40087cf421 to private HF main=575d4a3726896d498ed4fb76710948b2fbea7cdd. Archive/source/protocol/resource-snapshot hash bindings and downloaded-source admission passed;41026 existing objects, all100 cases, training and scene/RAMBO bytes unchanged. Old pins and historical execution sources remain. No new render/physics/inference/benchmark/training/AMD or GitHub push. Read docs/scaleup-v1/mujoco-standard-evaluation.md and docs/scaleup-v1/evidence/QLM-EVAL-003/.

## MuJoCo evaluation/resource delivery completed —2026-10-18

100 Standard cases and22 real old-Isaac policy engineering episodes verified; private HF training+evaluation main=254d4f0673e2698bcb74375f130aa88a344aa762; training bytes/DataRefs/splits/prompts preserved; local commits only. Formal benchmark/SR,training,AMD and GitHub push not run. Evidence:workspace runs/audit/mujoco-evaluation-20261018-v1/.
Read docs/scaleup-v1/mujoco-standard-evaluation.md and the archived paired EVAL records. Earlier pending statements retain their historical scope.

<!-- QLM-DATA-041 verified HF1000 release -->
## 十task精确prompt与private HF1000已验证发布 — QLM-DATA-041 / 2026-10-17

用户指定十句prompt已作为user-prompts-20261017-v1发布；既有400仅文本与必要hash/索引依赖更新，视频/数值/snapshot/command/terminal不变；新增600采用最终已验收版本，四项Observer为左后侧。main实际revision=470e0a1f290ef65a25ca1933a91a51ccd6427fcf，payload=b84488eca8a723767cef27fa455ec2ea8169f81c；private=True，Isaac-based=519725c8bc77b35fd5d3b4ac8555a3e96a8876a7保持。1000条=10task各100，800/100/100 split和200Clean/800Randomized，964151actions/965151boundaries。全远端LFS/Gitblob、20条Clean/Randomized独立data-only回读、精确prompt/索引/原400非文本保护均通过。

原始采集source/frozen-source/历史prompt及receipt不回写，新正式发布语言版本单独lineage。原冻结text encoder无梯度生成十项embedding，无训练/optimizer/WAM策略重复验证/physics/render/AMD。HF数据发布不自动切换历史TRAIN/EVAL输入；源repo所有此前未提交tracked/untracked源码/文档由用户明确授权统一commit/push。当前GitHub提交状态见workspace runs/audit/mujoco1000-prompt-publication-20261017-v1/github-commits.json；物理执行不冒称运行于后续新commit。
<!-- /QLM-DATA-041 verified HF1000 release -->

## 十task精确prompt修订与HF1000发布已获授权 — QLM-DATA-041 / 2026-10-17

用户明确指定十句新prompt，授权新增已验收600条发布到既有private dontKnow23456/QLM-Bench；既有400仅更新prompt及必要hash/索引引用。原400所有视频/数值/snapshot保持，Isaac-based旧SHA519725c8bc77b35fd5d3b4ac8555a3e96a8876a7保持；新增600采用最新左后Observer。当前本地语言版本与data-only验证/发布准备中，尚未宣称远端1000完成。

用户同时授权治理收尾后，将三个实际MuJoCo repo全部尚未提交的tracked/untracked源码/文档改动commit/push至各自配置的origin push targets；原dirty库存已固定，不回写历史执行source。QLM-DATA-041、v2 DOC-026、v3 DOC-025配对active；审计workspace runs/audit/mujoco1000-prompt-publication-20261017-v1。原冻结源/采集记录和旧prompt保留历史，新正式语言版本显式lineage；仅冻结text encoder无梯度生成匹配embedding，不训练、不重复WAM策略验证、不重跑physics/render、不连接AMD。以本条直接用户授权覆盖下方旧“不发布/不commit”时点，private可见性和历史TRAIN/EVAL输入声明保持。

## 六task600条正式验收完成 — QLM-DATA-040 / 2026-10-17

用户已明确批准六项随机审核并要求正式验收登记与配对归档。Sweep/Fridge/Oven/Valve/Drawer/Room Door各100，共600条正式user_accepted；每task全100均匀无放回随机10，共60条审核通过。加上原Push/Press/Lift/Kick400条，累计10task、1000条正式验收完成。

独立验收receipt及逐条600登记在workspace runs/audit/remaining-six-acceptance-20261017-v1/：user-acceptance.json、formal-accepted600.json、protected-evidence.json。工程证据、原Raw/Canonical/PhysicalTrace/source/媒体和历史失败不改写；原400验收保持。累计610physics含Drawer原10失败，另Door2bootstrap为0physics；验收登记未执行新physics/render/WAM验证。

QLM-DATA-040已completed，ChangeSpec/ExecPlan配对移至QLM MuJoCo repo的docs/scaleup-v1/{changes,work}/archive/QLM-DATA-040/，active副本移除；权威登记为该repo docs/scaleup-v1/work-registry.json及remaining-six-formal-acceptance-20261017.md。监看保持停用，无训练/AMD/commit/push/HF发布授权；新增600尚未发布HF，原private HF400保持。以下pending/运行中只保留原历史时点。

## 六task各100工程完成；随机十条集中待审核 — QLM-DATA-040 / 2026-10-17

Sweep/Fridge/Oven/Valve/Drawer/Room Door各100，共600全新demonstrations已完成全量Raw/Canonical/实际snapshot/必需telemetry/command/terminal/媒体/source/去重检查和各task合并；700553actions/701153boundaries、600唯一实际trajectory。20Clean80Randomized和80/10/10 split逐项准确。六task一次双WAM共24项通过，扩量不重复模型验证。

累计610次physics=600成功+Drawer原10超时，历史失败保持。Drawer31旧source成功保留+69原scope-v5新成功；Door2次初始import失败为0physics/0commands，成功判据始终几何v3。成功physics未重跑，原reference/范围/RAMBO/reset/camera/native9和NativeCPU/EGL路线保持。最终241primary文件、6reference、原checkpoint、三repo HEAD和60审核视频/链接核对通过。

审核入口workspace runs/audit/remaining-six-production-20261016-v1/review.html：六项各从全100均匀无放回随机10，共60条，原400已人工验收与本次600最终人工审核pending分开。无训练/AMD/commit/push/新HF发布。当前physics/render/pipeline均结束；监看已停用，QLM-DATA-040配对active等待用户最终审核。完整报告docs/scaleup-v1/remaining-six-engineering-delivery-20261017.md；当前入口active-task-roots.json、completion.json、final-source-and-delivery-audit.json和progress.json。以下运行中/旧0/600/旧gate段落只保留历史时点。

## 前五task各100工程完成；Room Door100进行中 — QLM-DATA-040 / 2026-10-17

Sweep/Fridge/Oven/Valve/Drawer各100全量工程检查与Canonical合并通过。Drawer129843actions/129943boundaries，31旧source成功原样保留+69已批准scope-v5成功；021/024接入修复后各一次原c01成功。累计110physics含原10失败，cumulative-attempt-summary.json补充真实次数，历史结果不改写。最后Room Door已按顺序进入100，实际几何v3及完整reset保持。原400人工验收、新600待六项全完成后随机10/task集中人工审核的区分保持。

当前单写者pipeline_v3、active-task-roots.json及progress.json为事实；每30分钟检查，正常不通知，实时3+3/resource/source保护继续。六task一次双WAM24项已通过，不重复模型验证。无训练/AMD/commit/push/HF发布。

## 前四task各100工程完成；Drawer接回原scope-v5 — QLM-DATA-040 / 2026-10-17

Sweep/Fridge/Oven/Valve各100全量Raw/Canonical/实际snapshot/必需telemetry/媒体/source/去重与合并通过。六task一次双WAM共24项已通过；原400人工验收保持，新增最终人工审核仍等六项全完成后各随机10，不能提前宣称600/1000最终通过。

Drawer原root 41次physics中31成功、10超时；021/024各5候选用尽后自动停止。定位交接仅nominal DrawerLaneHeadingExecutor，遗漏既已批准scope-v5 DrawerFixtureHeadingExecutor的fixture yaw heading。已按原scope proposal hash恢复该adapter，零步nominal数值等价及14相关tests通过；非重新调reference。033同trace媒体恢复后31成功全保留，各原source/profile不改写。当前独立pull_open_drawer-v2仅生产余69；两个旧失败slot修复后各一次原c01工程复核，失败即停，累计含旧失败上限300。其余候选/seed/范围/成功条件保持，历史失败不回写。active-task-roots.json、pipeline.json/progress.json和drawer-scope-binding-recovery.json为当前入口；pipeline_v3恢复中。Door仍open_room_door-v2/几何v3。

NativeCPU/EGL全局3+3和原资源保护保持，成功physics不重跑。无训练/AMD/commit/push/HF发布。

## Sweep100工程完成，Fridge100进行中 — QLM-DATA-040 / 2026-10-17

Sweep100全新唯一physical traces，100尝试首次全成功，179671actions/179771boundaries；20Clean80Randomized及80/10/10 split、全部Raw/Canonical/媒体/snapshot/必需telemetry/去重与Canonical100合并通过。原Sweep31/32及032失败不改写。Fridge扩量已启动，其余task按顺序继续；六项全部完成后才各全100均匀随机10集中人工验收。当前新增工程接受100+各task准入样本，以workspace runs/audit/remaining-six-production-20261016-v1/progress.json为准，不能提前宣称600/1000最终人工通过。

六task一次双WAM共24项已通过，后续扩量不重复。原RAMBO/完整reset/recipe、NativeCPU/EGL全局3+3及原资源保护保持；原400/资产/已批准reference不变。无训练/AMD/commit/push/HF发布。当前pipeline为run_pipeline_v2.py，active-task-roots.json对Door指定open_room_door-v2（实际成功判据仍为几何v3）；旧零步import失败记录完整保留。

## 六task生产准入全部完成；Sweep100进行中 — QLM-DATA-040 / 2026-10-16

六项首Clean+Randomized共12条真实样本通过NativeCPU/EGL/Raw/Canonical及必需telemetry逐列准入，计入各100；双WAM共24项实际兼容性通过，v2 DATA020/v3 DATA010已归档，后续同task不重复模型验证。当前按Sweep→Fridge→Oven→Valve→Drawer→Room Door生产；最终每task随机10在六项全完成后集中人工审核，当前不提前宣称600完成。原400及HF保持。

当前路由与状态：workspace runs/audit/remaining-six-production-20261016-v1/active-task-roots.json、pipeline.json、progress.json。Door旧root两次import初始化失败均0physics/0commands；独立open_room_door-v2修复依赖路径、同100候选/recipe/seed/范围，已通过实际v3准入，旧source/log不变。六primary241资源文件匹配开跑前身份并持续保护。已实测扩量3+3重叠，原资源阈值保持。无训练/AMD/commit/push/HF发布。

## 剩余六task生产已获开工授权 — 2026-10-16 / QLM-DATA-040

用户已明确要求先补齐六task公共生产接入和端到端准入，再Sweep→Fridge→Oven→Valve→Drawer→Room Door逐项全新100；reference/scope原批准保持，不再设10pilot人工gate。六项全完成后各全100均匀无放回随机10集中人工验收。当前已建立独立生产工作包及冻结source/candidates，端到端准入进行中，不能提前宣称600完成。状态入口workspace runs/audit/remaining-six-production-20261016-v1/，QLM active DATA040及WAM v2 DATA020/v3 DATA010。原400不变。

原RAMBO/完整reset/recipe继承/成功条件/640×36050FPS及全局NativeCPU/EGL3+3和原资源阈值保持；成功physics不重跑、媒体仅同trace恢复。Door必须几何v3；Sweep31/32历史保留且顺序门槛不恢复；Fridge50deg nominal显式冻结。不训练、不连接AMD、不commit/push或发布HF。后续首轮只读等待描述属于本次明确开工之前的交接时点。

## Reference中间产物已清理；当前获批证据保留 — 2026-10-16

按用户要求，QLM-DOC-009清理9870个reference迭代中间文件，逻辑37.66GiB；因硬链接实际可用空间观测增量约2.50GiB。原attempt/result/source/参数/文字记录保留，旧manifest不再保证历史payload可加载，不回写原成功/失败。

当前六reference及有效scope保留，10788个保护文件hash通过；6个reference资源/源码import和112个当前scope模型manifest、实际frozen source依赖核对通过。正式400、全局assets/模型/env未列为删除目标，未启动新合成。Sweep复用旧成功、Door A19原动作状态与v3范围等依赖仍保留。新会话继续使用当前绑定与交接文档，不能从已清理的旧试跑取数据，也无需重做已批准reference。

审计workspace runs/audit/reference-intermediate-cleanup-20261016-v1/：report.md、cleanup-receipt.json、historical-attempt-text-archive.json及完整清单。旧页面缺失媒体已标记；当前正式/获批文件不变。

## 当前交接：三项范围已批准，正式400/1000，剩余600待生产 — 2026-10-16

用户明确批准DATA039 Fridge/Oven/Valve三项修订范围，实际48/48工程通过；独立receipt为workspace runs/audit/revised-three-scope-20261016-v1/user-scope-approval.json，DATA039配对归档。六task当前资产/reference人工审核均已完成，Drawer/Door既有批准、Sweep A09批准保持；Sweep历史31/32及032失败不回写。

当前Push/Press/Lift/Kick各100，共400正式已验收并完成private HF400发布；剩余六task正式0/600，scope/reference不自动计入100。生产公共接入尚未完成：六registration仍planned、公共rendition仍限制旧四task、Door须用几何退栓v3适配，不能直接复用含旧20mm逻辑的generic helper。新会话需阅读交接后先与用户对齐，等下一条开工指令；本轮不生产。

当前权威交接：docs/scaleup-v1/handoffs/remaining-six-production-20261016.md（QLM MuJoCo repo）；完整绑定和可复制prompt在workspace runs/audit/remaining-six-handoff-20261016-v1/。未来沿用直接每task100，无10pilot人工gate；每task一次WAM兼容与全量工程检查，最终每task随机十条人工验收延后到六task全部完成。3+3/1GiB/7.6GiB/0.5GiB/4GiB政策保持。旧pending/旧角度/旧20mm/旧10pilot段落均是历史，不恢复已完成审批。

## DATA039修订范围交付：Close Fridge Door 16/16；Close Oven Door 16/16；Turn Valve 16/16 — 2026-10-16

Fridge A04已获用户批准；Oven1kg/4s与Valve6s reference批准保持。本轮实际执行48项、工程验收48/48，逐项失败/not_run保留。范围共同XY±2cm/yaw±5deg；Fridge45–55（50±5，宽度不缩）、Oven25–35、Valve0–5，两背景各8；原recipe/RAMBO/成功条件/相机/seed42保持，nominal未重跑。

集中审核workspace runs/audit/revised-three-scope-20261016-v1/review.html，结构化reference-scope-catalog.json包含全部source、实际首次接触角及非FL/FL非足端接触观察。每task代表范围视频按最大非FL力、FL非足端力、成功时长依次选取，不是正式随机审核。初始范围与实际接触角分开，不冒充全过程同角度分布。NativeCPU范围证据，不宣称CUDA/ROCm已复测。

所有physics/render已结束；DATA039保持active等待用户集中确认，工程验收与动作质量批准分开。原400和其他批准保持，无新formal/100/WAM/cache/训练/AMD/commit/push/发布。108个原source及checkpoint/三repo HEAD保持。

## Fridge A04已获批准；三项修订范围DATA039 — 2026-10-16

用户批准A04作为Close Fridge Door合格reference，DATA038配对归档，批准receipt在workspace runs/audit/fridge-door-follow-20261016-v1/user-reference-approval.json。DATA039继续Fridge/Oven/Valve修订后的各16角点：共同XY±2cm/yaw±5deg，Fridge45–55（新50±5，宽度不缩）、Oven25–35、Valve0–5，两背景各8。采用各获批recipe/资产，原RAMBO/成功条件/camera和seed保持。最多3physics与原内存保护，单task首失败停派，独立task继续。旧scope保留历史，原nominal不重跑。

审计workspace runs/audit/revised-three-scope-20261016-v1/，完成集中交用户确认；当前尚未通过，不提前宣称48成功。原400和其他reference批准保持，暂不100/WAM/cache/训练/AMD/commit/push/发布。

## Fridge A04交付：50deg与实际门面持续跟随 — 2026-10-16

QLM-DATA-038本轮仅一条A04，27.96s按原3deg/三tick/notfallen成功；55→50deg只在reset前改变hinge初态，原model/资产物理/camera/原RAMBO保持。6.04s主前伸，11.40s抵门，之后足端body参考从45.48持续延伸到54cm（+8.52cm），机身推进29.48cm，不再冻结首次接触长度。原伸展上限到达后由机身配合。

50Hz实际FL足端正受力31次、FLcalf3次、非FL0；最后FL接触27.94s距终止0.02s。ego足端中心入画约91.1%、整球73.8%，实际中段/末段图已看，不宣称全程无遮挡或500Hz连续接触。1398commands/1399boundaries/初态差异/及时终止/source和700帧三视角验证通过，任务成功不替代动作质量审核。

当前审核workspace runs/audit/fridge-door-follow-20261016-v1/review.html；DATA038 active等待用户视频审核，未标合格reference。所有physics/render结束，无额外尝试/scope/100/WAM/cache/训练/AMD/commit/push/发布。旧A02/A03失败或质量不足记录、原400/其他task批准保持。

## Fridge新请求：初角50deg，抵门后继续随门前伸 — 2026-10-16

QLM-DATA-038仅一条A04及三视角：初始开度55→50deg，抵门后按实际门面继续更新前伸目标，机身配合；取代037抵门后固定body目标。原RAMBO/physics参数/camera/3deg成功及seed42/40s保持，初角仅reset前显式override，不回写旧55deg模型或尝试。审计workspace runs/audit/fridge-door-follow-20261016-v1/。不scope/100/WAM/cache/训练/AMD/发布，完成视频后停止。

## Fridge A03视频交付；物理成功但ego/头部接触仍需修订 — 2026-10-16

Sweep A09已按用户确认登记合格reference，原31/32范围和032失败保留，不再运行Sweep。本轮QLM-DATA-037有补充前A02一次（40s timeout）及补充后far-stop-v2/A03唯一一次；两份真实source/结果保持，不隐藏或回写。

A03在38.14s达到原3deg/三tick/notfallen。5.38s远停稳后主抬升前伸，10.70s真实抵门；之后body足端目标固定[.4526,.15,-.08]，机身前进39.42cm。54cm仅目标上限，实际接触即冻结45.26cm，不能宣称达到54cm。最后FL正受力接触37.74s/门角−4.86deg，终止38.14s。ego足端中心仅约10.6%边界在画内、整球0%；11个50Hz边界存在Head_upper/lower接触（最大47.87N），不计合格reference/不准入SFT，task success保持真实。

完整1907commands/1908boundaries/原predicate及时终止/source及同timestamp三视角通过。审计workspace runs/audit/fridge-body-advance-reference-20261016-v1/review.html、report.md；原RAMBO/资产/相机/时序和400保持。全部physics/render结束，等待用户审视频，不追加尝试/scope/100/WAM/cache/训练/AMD/commit/push/发布。DATA037保持active等待质量审核，静态预览通过不代表动态可见性通过。

## Fridge最新补充：远停稳后大幅前伸，原ego可见 — 2026-10-16

用户在A02运行中补充先更远停稳再抬升前伸，使足端处于ego视野。A02（补充前已启动）40s timeout/notfallen保留；QLM-DATA-037以独立far-stop-v2仅追加这条新要求对应A03，不在旧attempt中改source。新远停点约[-.069,-.089]m，比A02抵门X约+.02后移9cm；主前伸目标body[.54,.15,-.08]，原IK缓冲限位内，原ego零步投影/静态图已检查，动态可见性仍须实际视频。实际抵门后冻结body前伸目标，机身缓慢推进；原RAMBO/相机/资产/40s/成功判据保持。完成A03三视角即停止，不额外试跑/scope/100。新审计runs/audit/fridge-body-advance-reference-20261016-v1/far-stop-v2/，下方A02单次预算保留补充前历史。

## Sweep A09审核确认；Fridge仅一次机身推门修订 — 2026-10-16

用户已确认Sweep审核通过，A09为合格reference；原31/32范围结果及032超时保留，不回写成全32成功。Fridge原动作需改为早抬高前伸，实际足端接触门后保持前伸姿态，以机身前进推至关闭；“早停”不再作为该动作意图。QLM-DATA-037仅一次真实尝试及三视角视频，原RAMBO/physics/camera/native9/判据保持。审计workspace runs/audit/fridge-body-advance-reference-20261016-v1/。失败亦交视频后停止；不额外尝试/scope/100/WAM/cache/训练/AMD/commit/push/发布，原400/其他批准保持。

## DATA036结果：Sweep 31/32；Oven/Valve reference批准 — 2026-10-16

完整原范围验收 31/32；尚未通过，停止原因 physical_failure，未执行0个。 用户取消小拨/侧移顺序门槛，原task success和完整工程证据为准，动作/接触诊断不独立拒收。22.5cm及原32范围/两背景/seed42/40s/原RAMBO与camera不变，无缩域或seed选择。

旧Work035成功3条保留实际身份复用；Work036实际新physics30次，成功28、失败2，007原超时不回写。十条成功前缀证明不受新增6s实际几何出口影响，不重跑成功physics。最终逐条source见workspace runs/audit/sweep-task-success-scope-20261016-v1/final-report.json，审核入口同目录review.html。旧035顺序拒收只是历史。

Close Oven Door与Turn Valve合格nominal reference用户批准已登记，Fridge仍待审核；Oven/Valve修订后完整scope未在036执行。原400、Drawer/Door与108原source/三repo HEAD保持。全部在途排空，暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布。

## Oven/Valve reference已批准；Sweep取消顺序门槛，DATA036续验 — 2026-10-16

用户明确批准Close Oven Door与Turn Valve修订reference，独立receipt见workspace runs/audit/four-reference-refinement-20261016-v1/{oven,valve}-user-reference-approval.json。Fridge仍待审核。Sweep参考A09，取消小拨/侧移必须按序完成的门槛，达到原task success即可；原footprint/notfallen/三tick、RAMBO、camera、22.5cm及原32范围保持。阶段/姿态诊断不独立拒收task成功，工程完整性仍须验证。

QLM-DATA-036负责新口径复核旧3成功（保留实际source、原outcome不回写且不重跑成功physics）及其余范围续跑；小拨未达量/侧移未停稳/再次接触硬等待改为可选继续分支。DATA035原“顺序不合格”是旧口径历史，不再作为当前阻塞。审计workspace runs/audit/sweep-task-success-scope-20261016-v1/。暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布；原400/Drawer/Door批准保持。

## Scope035未通过并已排空；A09 nominal批准保持，三reference待审 — 2026-10-16

QLM-DATA-035保留原5D32角点（blockXY±2cm/yaw±5°/goal方向±4°、22.5cm中心距离±2cm，两背景各16）不缩域。首轮4/32仅1 task success但无获批序列资格，28未执行；补geometry-retarget-v1后3/32虽3 task success，均未执行first stroke/侧移，序列合格0、29未执行。共7次两个版本的scope物理运行，不合并冒充32点通过；首失败停止新派发并排空，当前0physics。

已量化共同原因：操作段机身Y误差最高8.6–10.6cm，稳定足端侧触与机身停稳从未同时成立；准备阶段却追随block继续推进，导致任务成功但批准动作顺序未执行。需要加强操作期机身保持并使接触准备有界，可能影响nominal实际动作，因此本轮不继续修改获批A09，不放宽门控/成功条件或缩范围。几何retarget在零扰动下保持A09且0physics，旧task结果/trace不回写；旧“可选阶段出现才校验”不足已由独立序列复核明确纠正。

当前报告workspace runs/audit/sweep-a09-scope-20261016-v1/review.html及final-report.json。A09 nominal reference用户批准保持，完整范围验收未完成，DATA035保持active；DATA034保留其余三项动作审核。Fridge/Oven/Valve修订三视角集中页workspace runs/audit/four-reference-refinement-20261016-v1/fridge-oven-valve-revised-review.html，均复用原媒体、hash和链接通过，用户动作批准仍pending。原400/Drawer/Door/原RAMBO及source保持。暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布。

## Sweep scope035补齐几何retarget，保留A09 nominal — 2026-10-16

首轮执行4/32，只有1条task success但未执行批准序列，独立序列资格0；首失败后已停止并排空，28未执行，原证据不回写。当前仅补retarget-v1：case XY平移body锚点、goal距离delta平移侧移终点并按方向投影。零扰动与A09名义参数/锚点/初始native9一致，0physics；不改批准nominal动作/接触门控/判据/RAMBO。以同32模型、seed42、40s和原范围重新验证，不缩范围/搜索seed。再次需改nominal则停止汇报，不无界调参。三reference媒体集中审核保持pending，不100/WAM/cache/训练/AMD/发布。证据workspace runs/audit/sweep-a09-scope-20261016-v1/retarget-v1/。

## Sweep A09已获批准；QLM-DATA-035范围验证，三reference集中待审 — 2026-10-16

用户明确批准A09为Sweep reference，独立receipt在workspace runs/audit/four-reference-refinement-20261016-v1/a09-user-reference-approval.json。沿用22.5cm和当前分阶段动作，原RAMBO/成功判据/recipe/初态/seed42/40s冻结。后继QLM-DATA-035验证完整原5维32角点；距离中心从30平移至22.5cm并保持±2cm宽度（20.5–24.5cm），其余blockXY±2cm/yaw±5°/goal方向±4°与两背景各16保持。旧30cm scope不作新版本通过证据，首失败停派并排空，最多3physics和原资源保护。

Fridge/Oven/Valve修订视频已集中于workspace runs/audit/four-reference-refinement-20261016-v1/fridge-oven-valve-revised-review.html，动作质量仍待用户审核；直接复用媒体，不重跑physics/WAM/cache。原034保留其余三项审核，035只Sweep scope与集成交付。原Drawer/Door/400保持，暂不100/新formal/训练/AMD/commit/push/发布。下方A09动作待批准为历史。

## Sweep A09单次成功，分阶段顺序通过；等待动作审核 — 2026-10-16

QLM-DATA-034仅实际一条A09，32.86s达到原完整footprint/notfallen/三tick，1643commands/1644boundaries并首次成功即终止。原进场/积分恢复，机身保持实际8.82s进入操作才启用；19.24s实际稳定足端侧触并小拨约6cm，21.74s确认原goal未满足后右侧移，25.10s再次稳定接触后最终拨动。接触及首次小拨前无计划goalward机身侧移。原RAMBO/成功判据/22.5cm资产布局与其余v8参数保持。

50Hz实际正受力接触仅FL_foot91次观测，FLcalf/机身0；足端横向顺序未反转，最小间隔+5.56cm，但肘部/支撑腿全程动作质量仍待用户视频审核，不替代该审核。workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a09-review.html；a09-completion.json、a09-sequence-audit.json及a09-report.md为当前证据。optional几何distance探测标记inconclusive，不用它作验收结论。

一次授权已用完，physics/render/监测结束，等待用户审核，无追加试跑/完整scope/100。旧30cm范围不证明22.5cm新reference范围通过；未自动计合格reference。旧A07/A08 payload/media与108源文件保持。Drawer/Door已批准、Fridge/Oven/Valve修订待审、原400保持；不WAM/cache/训练/AMD/commit/push/发布。下方A09启动及A08失败为历史。

## Sweep A09单次授权：恢复进场，只在interaction后保持机身 — 2026-10-16

用户明确要求修复A08，恢复原approach/stabilize进场控制，只在进入操作阶段后启用机身保持；沿用22.5cm和稳定侧触→5cm小拨→必要时右侧移→再拨动，仅再一条并给三视角。QLM-DATA-034仅新增A09。v9只把机身保持override门控改为interaction_start非None，保留原进场速度/recipe lateral integral/1.5cm与停稳门控；原RAMBO及success、seed42/40s、资产/相机/时序和分阶段参数不变。

独立source/recipe/一次授权receipt在workspace runs/audit/four-reference-refinement-20261016-v1/。成功/失败均完整交视频后停止，不自动第二条/scope/100/WAM/cache/训练/AMD/发布；A08原timeout及全部历史/原400保持。下方A08停止为旧时点。

## Sweep A08单次已结束：进场门控实现问题，未进入操作 — 2026-10-16

QLM-DATA-034按用户只一条要求执行A08，40s timeout/notfallen。实际仅settle/carry/approach_base，无FL/robot碰块、无稳定侧触/小拨动/右侧移，不能据此判断用户分阶段策略失败。本次expert把Y保持过早用于进场（cap2cm/s并清除recipe lateral integral），原1.5cm进场门控未收敛；终态Y误差约5.34cm。原RAMBO/内部history/physics/成功判据没有改动；不追加第二条，不计合格reference。

用户明确授权的距离30→22.5cm已通过独立profile实现：blockY.15→.075，goal位置/尺寸保持，A/B/C物理及camera参数不变。旧scope不能代表新布局。视频workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a08-review.html（完整40s/1001帧），a08-completion.json、a08-report.md和a08-actual-evidence.json为当前证据。4个零步mock阶段门控检查不等于真实流程验收。全部physics/render结束并停止等待用户反馈，无scope/100/WAM/cache/训练/AMD/发布；原400/其他reference保持。下方A08授权仅为启动前历史。

## Sweep A08单次授权：22.5cm距离，先接触小拨再侧移 — 2026-10-16

用户确认A07身体停止位置，要求禁止足端稳定接触前侧移；仅再试一条A08并交三视角。保持goal原位，block-goal中心距30→22.5cm（blockY.15→.075），新独立profile sweep-short225-staged-approved-20261016-v1各A/B/C只改初始位置；原质量/碰撞/摩擦/camera/成功判据保持。此距离变化由用户明确授权，不沿用旧scope冒充新范围。

高层流程为原远初停点/伸腿→机身位置保持和真实FL_foot侧面稳定接触→5cm足端小拨动；若原goal未满足且block实际小移≥1cm，才允许身体向右（goalward世界-Y）侧移12cm，足端world目标保持；机身再停稳/重新实际侧触后完成拨动。原RAMBO/checkpoint/IK/PD/QP/history/native9/500-100-50Hz/forcezero/camera与原40s/footprint/notfallen/三tick保持。接触门控只是expert动作阶段，不替代task success；足端横向护栏只是质量保护，不自动判task失败。

QLM-DATA-034承接，独立v8/source/recipe/asset与一次授权receipt在workspace runs/audit/four-reference-refinement-20261016-v1/；仅A08，不自动第二条/scope/100/WAM/cache/训练/AMD/发布。原A07失败及其他reference/原400保持，完成视频后停止等审核。

## Sweep A07一次重试完成，40s未成功；等待视频审核 — 2026-10-16

QLM-DATA-034按用户仅一次授权完成A07：40s timeout、未跌倒，未满足原完整footprint进区成功判据。身体终态goal方向移动32.6cm（A06为8.4cm）；全部50Hz采样足端横向顺序未反转，最小FL减FR bodyY间隔+12cm，但不能替代完整动作质量审核或task success。提前横移后lower阶段较久、后段足端抬高，方块未完整进区；不追加第二条，不计合格reference。

三视角workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a07-review.html，原速40s/1001帧，同timestamp实际snapshot且无physics重跑；a07-completion.json、a07-comparison.json及a07-report.md为本次权威。原RAMBO/成功判据/接触路径/资产/camera/seed42/40s保持；只改高层身体跟随与其朝向参考点。完整2000commands/2001boundaries/source及独立原predicate检查通过。仅这一条，physics/render结束，等待用户视频反馈；未scope/100/WAM/cache/训练/AMD/发布。Fridge/Oven/Valve待审、Drawer/Door已批准、原400保持。下方A07授权/停止点为历史。

## Sweep A06交叉被拒；仅授权一次A07身体跟随修订 — 2026-10-16

用户要求身体在拨动中更早、更充分向goal移动，保持原RAMBO与success，只再试一条三视角。QLM-DATA-034仅新增sweep-a07：lower阶段提前1.5s渐建6cm身体目标领先、实际block进度1.2倍跟随、目标位移上限32cm；高层横移cap3.5→10cm/s，原加速度0.12m/s²保持，并平移身体朝向参考点，原heading反馈算法/角速度限制保持。原足端接触路径、远初停点、资产/physics/camera/seed42/40s成功判据及controller内部保持。

独立v7/source/recipe与一次预算receipt位于workspace runs/audit/four-reference-refinement-20261016-v1/。只此一条；成功/失败均交真实snapshot三视角并停止等审核，不自动追加、scope或100。A06仍被拒动作质量，不能覆盖旧结果。Fridge/Oven/Valve待动作审核，Drawer/Door批准/原400保持，无WAM/cache/训练/AMD/发布。下方停止等反馈是旧时点。

## Sweep失败视频已交付；四项修订停止新增尝试等反馈 — 2026-10-16

QLM-DATA-034已完成真实Fridge/Oven/Valve首轮，分别16.76/15.62/12.72s达到原task success，按2/4/6s提前操作；Oven新compiled门体1kg/35deg，Sweep新goal仅边框。Drawer与Room Door的reference/范围已获用户批准，原材料保持不复跑。原400保持，新增formal0。

Sweep五条失败（a01–a05，其中a03为heading实现缺陷）已完整生成三视角，workspace runs/audit/four-reference-refinement-20261016-v1/sweep-failure-review.html。用户要求先看失败视频后，原在途a06结束于33.52s task success，但实际FL/FR足端横向顺序曾反转约61mm且仍有FLcalf接触，末段交叉风险未排除，不计合格reference、不宣称动作已解决。全部physics/render现已结束，不再追加尝试，等用户视频反馈。

四项当前材料workspace runs/audit/four-reference-refinement-20261016-v1/review.html；三项动作质量仍待用户审核，Sweep仍需处理质量风险；四项新scope均未重验，旧范围只代表旧recipe/旧质量。Oven1kg新profile不借用旧1.8kg的CUDA资格。原RAMBO/IK/PD/QP/history/native9/500-100-50Hz/camera/成功判据及三repo HEAD保持。无100/WAM/cache/训练/AMD/commit/push/发布；普通3+3与原资源阈值保持。下方进行中/四项旧范围通过等仅为历史版本。

## 四项reference按最新审核修订；Drawer/Room Door已批准 — 2026-10-16

用户已批准Pull Open Drawer和Open Room Door的reference与范围，原资产/动作/证据保持，不复跑。Sweep旧动作被拒绝：从旧7s附近较远站位开始伸腿、身体随拨动方向协同，避免FL与右前腿FR交叉（用户原文RL指右前腿）；goal仅边框。Fridge约2s抬高前伸，Valve约6s停止接近并抬高前伸；Oven门体质量改1kg、约4s停止接近并抬高前伸且增加前伸。Oven35deg限位及各task success判据不变，原RAMBO/IK/PD/QP/history/native9/500-100-50Hz/camera保持。

QLM-DATA-034负责四项独立版本nominal与视频，审计workspace runs/audit/four-reference-refinement-20261016-v1/；Sweep仅透明中央填色的新profile、Oven1kg新profile均A primary/B-C backups，不回写旧资产。原四项scope针对旧recipe/旧质量，只作历史；新reference审核后再冻结并重验对应范围。当前不启动100/其他task/WAM/cache/训练/AMD/commit/push/发布。最多3physics+3render与1GiB/7.6GiB/0.5GiB/4GiB原保护保持。原400和Drawer/Door批准保持，以下六项全部待审或停止描述为旧时点。

## 六task reference与范围已集中交审；历史失败产物已清理 — 2026-10-16

QLM-DATA-033完成Door16/16与Oven16/16全部实际角点验收，原RAMBO/已批准动作/物理/成功判据保持；所有episode在首次满足条件的完整50Hz边界结束，50Hz实际记录无非FL正受力接触。Door18.56–23.46s，Oven17.38–19.64s。Oven初始开度25–35deg为待此次集中确认的新范围提案，保留原10deg宽度并符合35deg限位；XY±2cm/yaw±5deg保持。

原四项复用：Sweep32/32、Fridge16/16、Valve16/16、Drawer16/16；六项集中审核workspace runs/audit/remaining-six-final-scope-20261016-v1/review.html。范围均为primary A，B/C资格不从A结果自动推定。Door A19与Oven35deg中央nominal已获批准，本轮整批reference/范围最终确认pending，新增formal0/原400保持。

按用户明确要求，历史失败/被拒/未采纳Door/Oven中间产物先文字归档后清理809文件、约3.13GiB逻辑大小；硬链接原因不冒充实际回收空间。原文字记录/source hashes保持；1278个受保护二进制逐文件hash复核，合格reference、当前范围、已批准资产及其他任务完整。删除receipt和文字汇总同审计目录。无后续physics/scope/100/WAM/cache/训练/AMD/commit/push/发布；停止等待用户整批确认。以下历史pending/运行中仅保留原时点。

## Door/Oven reference已获批；开始冻结方案范围及六task集中确认 — 2026-10-16

用户批准Oven35deg中央前推，Door继续A19几何退栓/15deg。QLM-DATA-033执行Door16与Oven16范围；Oven初态提案25–35deg保留10deg宽度并遵守35deg限位，待集中确认。冻结动作/资产物理/成功条件，首失败停止该task新派发排空，最多3physics与原资源保护；无生产扩量。之后集中六task材料，按用户要求将历史失败/被拒Door/Oven二进制中间产物先文字归档后清理，保护合格reference、已批准资产及当前范围/依赖。审计workspace runs/audit/remaining-six-final-scope-20261016-v1/。

## Oven35deg中央前推单次成功；等待动作审核 — 2026-10-16

QLM-DATA-032仅一次真实尝试完成，19.42s满足原3deg/三50Hz tick/notfallen；971actions/972boundaries，完整trace通过。初态35deg，实际最大35.0158deg，未硬截断qpos。首次FL_foot触门板中央worldY=-6.52mm；50Hz实际接触记录仅FL_foot，非FL记录0，不夸大为全500Hz证明。用户动作质量待审，未追加第二次/scope/100。审核workspace runs/audit/oven-limit35-center-reference-20261016-v1/review.html。

原50deg两条已被用户拒绝动作质量，历史task结果保留。当前A质量仍1.8kg，原RAMBO/physics时序/camera不变；中央recipe与35deg新资源均独立版本。当前physics/render结束后停止等审核，无训练/AMD/commit/push/发布。

## Oven旧两条动作均被拒绝；35deg中央前推单次重试 — 2026-10-16

用户明确拒绝QLM-DATA-031两条动作质量，旧第二条task success保留但不作合格reference。新QLM-DATA-032授权最大开度35deg、中央前推，仅一次实际重试并给视频；初态35deg以遵守新限位。足端门局部Y0，机身Y-.18以FL对准中央；质量/原RAMBO/相机/原成功判据不改。旧资产/source/结果保持，无第二次、scope/100/WAM/AMD/发布授权。审计workspace runs/audit/oven-limit35-center-reference-20261016-v1/。

## Oven50deg两次已完成；第二次关门成功待动作审核 — 2026-10-16

QLM-DATA-031按用户要求完成两次，无追加第三次/无scope。第一次60s超时，第二次40.48s满足原3deg/三50Hz tick/notfallen；最大实际开度由50.679deg减至50.073deg，有限soft-limit超调据实保留。第二次有40个50Hz边界的Head接触记录，尚未量化关闭力矩，任务成功与动作质量分开，等待人工审核。审核workspace runs/audit/oven-limit50-reference-20261016-v1/review.html。

Door A19已获用户动作批准并选作reference；QLM-DATA-030显式runtime/新几何判据已接入，实际A19状态feed在24.40s触发成功，terminal后命令拒绝；未重跑Door physics，原A19结果和完整范围pending保持。原RAMBO/source/已验收400保持，无WAM/cache/训练/AMD/commit/push/发布。下方运行中记录仅为历史。

## Door A19获批；Oven50deg限位两次重试 — 2026-10-16

用户批准A19动作质量及reference方案；QLM-DATA-030接入几何退栓历史event和实时15deg/三tick/notfallen terminal，完整范围尚未验证。用户另授权Oven最大开度相对本体垂直面50deg及两次reference重试，由QLM-DATA-031执行；旧Oven停止要求仅对本有界两次解除，未授权额外scope/100。新版Oven保留45deg初态、原3deg关门判据与原RAMBO，使用真实joint限位，不clamp/teleport。审计workspace runs/audit/oven-limit50-reference-20261016-v1/；旧资产和失败结果不回写。

## Door三次尝试完成；采用实际锁扣退出判据 — 2026-10-16

用户已取消固定20mm退栓门槛，采用实际锁舌实体退出锁扣口的历史event；开门后的回弹不撤销解锁，15deg/notfallen/三50Hz tick和原RAMBO/资产/physics/camera保持。QLM-DATA-030及decisions/door-geometric-unlock.md为新权威，旧20mm判据只保留历史。三次A17/A18/A19已全部结束并保留完整50Hz诊断状态、三视角视频。按新规则离线复核A18在24.86s、A19在24.40s通过，A17未达到15deg；原执行结果/terminal不回写，不冒充按新规则实时终止的正式数据。

前三次全部失败才追加第四次的条件不成立，因此无第四次、无scope/100扩量，当前0physics/scope，停止等待用户审核。审核workspace runs/audit/door-user-three-attempts-20261016-v1/review.html；动作质量及reference完整范围仍待审。原400/其他references/Oven停止保持，无WAM/cache/训练/AMD/commit/push/发布。下方旧暂停/20mm/进行中段落为历史。

## Room Door有界恢复：最多三次并保留视频 — 2026-10-16

用户纠正主要问题为实际前伸不足及下压/侧触门槛过严，授权高层路径和接触门控修复后至多三次真实尝试，所有尝试均交三视角视频。QLM-DATA-029沿用；只解除本有界轮的暂停，不授权完整scope或更多尝试。原20mm退栓/15deg/三tick/notfallen、RAMBO/资产/相机保持。失败仅此轮按用户要求保留完整50Hz诊断snapshot用于媒体，不改为正式demonstration或普遍高频存储要求。实际预算receipt为workspace runs/audit/door-lowered-reference-20261016-v1/user-three-attempt-decision.json，启动入口单写者强制最多3次。下方旧暂停保留历史。

## Room Door已按用户要求暂停 — 2026-10-16

用户明确暂停Open Room Door后续尝试，只要求查看最近失败的三视角视频。当前Door physics/scope进程0，最后实际失败为QLM-DATA-029 SmallA16（22.74s侧触拒收/notfallen），没有A17，scope实际0。不得继续候选开发、physics或scope，等待用户下一步指令；其他reference/原400保持。receipt见workspace runs/audit/door-lowered-reference-20261016-v1/user-pause-decision.json。可仅用已保存127个真实qpos时点制作明确标注的5Hz为主稀疏诊断回放，不插值、不补跑physics，不冒充完整50Hz失败trace。下方“继续开发”只描述原历史状态。

## Door目标更新：真实20mm退栓后推开15deg — 2026-10-16

用户明确允许把开门角成功门槛适当减小；实施采用15deg合理默认（用户未指定数字，已在会话说明）。严格bolt>=20mm且lever<=-20deg历史event、notfallen/三50Hz tick、原RAMBO/IK/PD/QP/history/native9/forcezero/500-100-50Hz/camera和资产物理保持。QLM-DATA-029承接新success profile/reference/完整原16scope，parentDATA028保留整批审核，SIM022物理证据继续复用。新成功定义为door-physical-unlock20mm-open15deg-v2，不把旧60deg失败追认为成功。

新runtime在workspace assets/mujoco/door-small-opening-approved-20261016-v1/A|B|C，仍同一A primary/B-C backups三个资产身份；仅task success metadata/closure改变，XML/mesh和完整compiled物理/相机fingerprint三资产逐一exact。证据workspace runs/audit/door-lowered-reference-20261016-v1/user-small-opening-decision.json、approved-profiles-small-v2.json、small-opening-profile-equivalence.json与reference-admission-small-v2.json。原28cm/60deg profiles、14条旧attempt/source/outcome完整保留，当前旧轮均已排空，不重跑成功资产qualification。

当前还未有合格新15deg nominal或16scope；降低角度不解决尚待验证的strict20mm退栓。既有四项完整reference和Oven范围失败/停止保持，原400保持。继续最多3physics+3render及原1GiB/7.6GiB/0.5GiB/4GiB保护；scope须先实际nominal独立验收并修复身份/exit/异常排空/source库存问题，完成集中交审，无10pilot人工gate、不100/WAM/cache/训练/AMD/commit/push/发布。最终随机十条延后至全部task完成。下方60deg与asset pending叙述只保留历史版本。

## Door 28cm资产已获用户批准，真实物理与原RAMBO reference推进 — 2026-10-16

用户已明确批准28cm A primary/B-C backups，receipt在workspace runs/audit/door-lowered-reference-20261016-v1/asset-approval.json；QLM-SIM-021已配对归档，后继QLM-SIM-022负责新高度真实Native/CUDA资格，QLM-DATA-028继续高质量reference/完整适用范围与集中审核。独立approved runtime在workspace assets/mujoco/door-lowered-approved-20261016-v1/，XML/mesh与已审28cm proposal保持，仅approval metadata/closure派生；原proposal pending状态保留历史。

旧Door expert/scope工具有35cm局部Z/旧pack路径硬编码，新版本独立绑定实际28cm model机构坐标与closure。先真实rest/latched阻挡/lever-cam-follower-bolt/socket接触，再原RAMBO CPU慢速抬足→前伸搭顶→下压解锁→推门；保持原controller/IK/PD/QP/history/checkpoint/native9/force-zero/500-100-50Hz/camera/60deg三tick/notfallen。被动初动量或独立sphere诊断不是RAMBO demonstration，soft-limit overshoot不冒充慢压合格。

新reference先nominal有界开发，成功后冻结recipe并真实执行原XY±2cm/yaw±5deg八角点×两背景共16；固定seed/reset、不缩范围、不搜索seed、不改资产参数或辅助解锁。Native12/12被动机械检查（9000steps）及CUDA3/3双world/reset/mirror集成（1200world-steps）已通过，独立1kg/22mm接触probe有后续soft-limit overshoot，不能替代原RAMBO慢压/完整开门。实际证据以qualification/verified-qualification-summary.json为准，reference/完整范围尚未通过。原四项完整reference保持，Oven nominal成功但范围失败且停止，不重新试跑；formal0/原已验收400保持。

保持普通最多3physics+3render与1GiB available/7.6GiB launch-relative swap/0.5GiB紧急render回收/4GiB新render门槛；本次先独立1physics开发，scope可2physics，实际launch单列。完成后集中交用户reference/范围审核；无10pilot人工gate，最终随机十条仍延后至所有task合成结束。v2DOC025/v3DOC024只治理，不WAM/cache/训练/AMD/100/commit/push/发布。下方旧pending状态只保留历史。

## Door 28cm完整锁机构提案已交付，等待具体资产审核 — 2026-10-16

QLM-SIM-021已交付独立A/B/C新profile，把手轴35→28cm，lever/cam、bolt/follower、strike socket及配套面板整体下移7cm；仍A primary、B/C backups、无使用配额。29–31cm余量不足、28.5cm走廊窄的静态比较支持推荐28cm，但精确高度与新资产尚未获用户批准。审核workspace runs/audit/door-lowered-asset-review-20261016-v1/review.html。

A的55相关body姿态×4接近点共220静态姿态均在原保留joint限位内，最小额外余量3.26°、实际sphere回读误差最大0.104mm、整球净空至少3.99mm、robot–asset硬碰0。1mm是本次分析容差，不是原controller gate；10µm额外诊断212/220据实保留。B借用A接近姿态有4处calf擦碰，该路径未取得B操作资格，不阻塞A；C无硬碰但仍未动态验收。

三资产独立九节点/192规定joint配置静态机构审计通过，原可动质量惯量、joint/solver/lock常量、robot及实际camera矩阵保持；6初态零步无enabled穿透、120父资源hash保持。原RAMBO source/checkpoint与三repo HEAD保持。NativeEGL36张静态图与对照页只用于资产审核，不修改正式camera。physics/inference/reference/formal均0，不将静态可达或锁机构几何相同当作动态解锁/平衡/任务成功。

SIM021保持active等待用户批准具体profile，获批后才做新高度真实物理资格与reference/完整范围。原35cm资源/旧trace不改写，其他四项完整reference及Oven范围失败/停止状态保持。原400验收保持；不WAM/cache/训练/AMD/commit/push/发布，不恢复10pilot人工gate；最终随机十条仍延后至全部task合成结束。下方旧pending状态仅为历史时点。

## 本轮reference收束：四项完整通过，Oven范围未通过，Door待决策 — 2026-10-16

QLM-DATA-028当前有5个nominal物理成功candidate，只有4个task完成原范围工程验收：Fridge a04 16/16、Drawer a07/v5 16/16、Valve a07/v7 16/16、正前方Sweep a15 32/32。Sweep独立2physics/single-writer实际31.35min，244 sources保持，无资源/物理/infra失败；不是正式生产吞吐或policy SR。五份三视角视频在workspace runs/audit/remaining-six-reference-20261016-v1/review.html，Oven明确单列为范围未过的诊断candidate，页面不是整批完成/用户批准。

按用户将Oven放最后且不无限重试的要求，最后仅修高层阶段门控的一条a04真实29.28s关门成功，原RAMBO/资产阻尼/3°三tick判据保持。45°初态仍自然落90°后接触；FLhip参与支撑及27.6s单次较快转姿显式待人工审视。原16角点首2项均60s timeout，余14未执行，首次失败后停止派发并排空；source不变、不缩范围、不再调参。Oven因此不计工程就绪。详见pairs/fridge-oven/oven-final-structured-summary.json。

Room Door仍无合格reference，原controller近限位/gait和一次实际快速接近失败证据已汇总。降低handle及联动lock的新profile、独立controller评估或暂缓Door三项已集中询问用户；答复前不改asset/controller或继续physics，推荐项不等于授权。决定待办为同审计目录pending-door-route-decision.json。

当前全部reference physics/writer已停止，QLM-SIM-020/DATA028、v2DOC025/v3DOC024保持active等待关键决定与整批审核。原已验收400、18原候选资源、原RAMBO source/checkpoint、相机/action/state契约保持；新formal0，不WAM模型/cache/训练/AMD/commit/push/发布。最终随机十条人工验收延后至所有task合成完成后统一，不恢复10pilot人工gate。以下进行中/待范围的叙述仅描述历史快照。

## 当前阻塞与独立推进 — 2026-10-16

Room Door当前无合格reference：A16只真实前送80ms后退回，仍发生侧触/未解锁，不代表完整170ms路径或机器人绝对不可达。实际gait/body变化与原IK near-limit证据已汇总；降低handle及联动lock高度、独立controller扩展或暂缓Door三条路线已集中询问用户，答复前不改asset/controller，不继续无证据试跑。pending receipt在workspace runs/audit/remaining-six-reference-20261016-v1/pending-door-route-decision.json；其默认推荐不等于用户授权。

Fridge a04/Drawer a07/Valve a07及各完整16范围工程通过，整批用户审核仍pending。Sweep a15 nominal32.84s真实成功、完整媒体/状态检查通过，原32范围由独立single-writer/2physics政策执行，未完成前不宣称范围通过；Door保留最多1槽/Oven0，全局不超过3。原1GiB/7.6GiB资源排空保护保持，12项调度/身份针对性检查通过。Oven继续按用户要求最后处理，不新派发。formal0、无WAM/cache/训练/AMD/新发布，最终随机十条人工验收仍延后至所有task合成完成后。

## 用户调整：Oven最后处理，禁止无限重试 — 2026-10-16

优先完成Fridge/Drawer/Valve/Sweep/Room Door的reference与范围；Close Oven Door放最后。用户允许最终无法完成时直接报告失败，不以无限重复试跑追求表面完成。当前Oven a03已排空：60s timeout/notfallen、终态约−83.39°，无新physics派发。现有hinge damping=0.09、frictionloss=0.025、stiffness=0，实际45°初态仍快速自然落平；不能将用户推测写成“铰链完全无阻尼”，也不据此擅自修改物理参数/controller。原失败、成功source及trace保持。决定receipt为workspace runs/audit/remaining-six-reference-20261016-v1/user-oven-last-decision.json。六task集中review与formal0保持，最终随机十条人工审核仍延后至所有task合成结束。

## 最新reference调整与最终审核时点 — 2026-10-16

用户观看失败视频后指定：Oven初始开度改为约45°；Room Door本体停得更远，先抬足高于handle，再前伸搭上方、真实下压解锁后推门。QLM-DATA-028继续版本化reference及适用范围，六条集中交审。必须记录Oven准备期间的真实门角，不用锁门/teleport/未批准物理参数维持角度；原RAMBO/IK/PD/history/native9/时序/camera及success条件保持。

剩余六task的最终随机十条人工验收延后到全部task合成完成后统一；每task全量工程验收、原每task均匀无放回抽十口径和每task一次WAM兼容保持。原已验收400不重复审批。六reference整批获批前不100，无10pilot人工gate；普通3physics+3render与原1GiB/7.6GiB/0.5GiB/4GiB保护继续。v2DOC025/v3DOC024本轮只治理。

决定receipt：workspace runs/audit/remaining-six-reference-20261016-v1/user-reference-retry-decision.json。以下旧逐task随机十条审批时点仅保留历史，按本节执行。

<!-- QLM-DATA-026 verified-private-HF-publication -->
## MuJoCo400 HF私有发布已验证完成 — 2026-10-16

QLM-DATA-026已完成四task正式400条发布及独立远端回读；dataset保持private。
[MuJoCo main](https://huggingface.co/datasets/dontKnow23456/QLM-Bench/tree/main) revision为
`a8eafc5b1e6019e4431d0417d9064f9fd658cc03`，catalog内不可变payload revision为`fde0f80eeec7ae36b7848a2bc6147d3c063d9f9b`。
[Isaac-based](https://huggingface.co/datasets/dontKnow23456/QLM-Bench/tree/Isaac-based)完整保留原main SHA
`519725c8bc77b35fd5d3b4ac8555a3e96a8876a7`及全部2860个原文件身份。
Push/Press/Lift/Kick各100，总计320train/40validation/40test、80Clean/320Randomized；原40条已批准formal pilots和实际backend/renderer/source身份均保留，未混入旧Isaac数据。

逐文件LFS/Gitblob校验、四task各Clean＋Randomized实际Raw/Canonical/媒体/terminal/snapshot下载回读及400索引检查均通过。发布receipt在workspace `runs/audit/mujoco400-hf-publication-20261015-v1/publication-receipt.json`；治理检查以同目录`governance-completion.json`为准。原数据/source heads/资产/模型/env锁保持；asset许可unknown据实保留，asset source/模型/cache未上传。历史训练/evaluation的revision pins不随main切换，不执行WAM/cache/fit/训练或AMD，不作source GitHub commit/push。

本轮只归档QLM-DATA-026、v2DOC-023、v3DOC-022。独立的QLM-DATA-027/v2DOC-024/v3DOC-023及剩余六task“集中资产审核→reference/范围审核→逐task直接100→随机十条最终验收”流程保持，不因HF发布解除任何新task审核gate。下面“尚未上传/发布进行中”等段落仅描述其历史时点。

## Sweep工作区改为正前方 — 2026-10-16

用户指出旧Sweep reference处在侧前方，明确要求方块和goal在机器狗正前方地面。新versioned profile为workspace assets/mujoco/sweep-front-approved-20261016-v1/：block[.75,+.15]、goal[.75,-.15]，工作区中心[.75,0]在robot纵轴前方，base从后方站至[.30,0]附近，不随横拨沿Y走到目标侧面。原30cm横拨距离、方块/zone尺寸、geometry/mass/friction、full-footprint/notfallen/三tick、原controller/native9/时序/camera不变。用户纠正receipt见workspace runs/audit/remaining-six-reference-20261016-v1/sweep-front-layout-decision.json。

旧Sweep a01成功trace/媒体只保留历史，不作当前交审reference，旧5D scope未执行且已superseded；新front reference/适用范围必须真实重验，不复用旧成功冒充通过。其余五task继续。原资产几何批准保持，sidecar/布局新closure明确，不回写旧资源、scope或receipts。

## 剩余六task资产获批；物理资格与六reference集中交审 — 2026-10-16

用户明确批准全部18资产，各task A primary、B/C backups；独立receipt在workspace runs/audit/remaining-six-reference-20261016-v1/asset-approval.json。QLM-DATA-027已配对归档，后继QLM-SIM-020/DATA028 active。原静态review/metadata的pending保留其历史身份，不回写。原18候选XML/geometry/mass/friction/articulation不改；新approved runtime profiles显式新closure/provenance，旧四task/400/source/controller保持。

本轮先三资产各真实Native/CUDA物理资格，再A primary各一条原RAMBO CPU高质量reference与预声明适用范围，六task集中交审。新六task暂无accepted数字predicate/公共runtime实现，reference专属profile明确新的可检查目标并随此次reference/范围交用户批准；不能借用旧task谓词或修改旧四task成功条件。普通高层native9平滑/站位/接触路径可依据证据迭代，不改controller/IK/PD/QP/history/force-zero/500-100-50Hz/camera，不辅助力/teleport/虚拟解锁/FL焊接，不因未知FL contact硬失败。

资产通过不代表动态资格/reference通过；当前生产formal0。只有整批六reference/范围获用户批准后才逐task直接100，无10pilot人工审核；两背景/无clutter/无强制Recovery/既定split与比例及最终随机十条验收保持。WAM新task一次兼容留production，本轮v2DOC025/v3DOC024只治理，不WAM/cache/fit/训练/AMD/source Git commit/push。NativeCPU/EGL普通3+3及1GiB/7.6GiB/0.5GiB/4GiB保护保持。HF400仍由独立DATA026/mujoco400-hf处理，不第二上传写者。以下pending为历史时点。

## 剩余六task候选资产静态包已生成；等待资产审核 — 2026-10-15

HF400最新实际状态：旧main已保留为Isaac-based，原SHA为519725c8bc77b35fd5d3b4ac8555a3e96a8876a7；private400正在临时分支上传，现有登录具write权限，无需新token。main尚未切换。mujoco400-hf监看已ACTIVE，首轮计划悉尼2026-10-16约01:13，上传回读验证后再收尾/切换；下方历史“尚未上传或改branch”仅描述原时点，不能作为最新状态。本资产Work不启动第二上传写者。

QLM-DATA-027已生成Sweep/Fridge/Oven/Valve/Drawer/Room Door各A/B/C共18候选（每task建议A primary＋B/C backups，无使用配额），Native compile＋mj_forward与72张NativeEGL静态图已生成；全部六task overview与Room Door背面cam/bolt近景已实际检查；18模型resource identity、72图hash/尺寸及页面相对链接QA通过（workspace runs/audit/remaining-six-assets-20261015-v1/visual-qa.json），用户资产批准仍pending。审核workspace runs/audit/remaining-six-assets-20261015-v1/review.html；verification.json记录physics steps=0/controller commands=0/reference=0/formal=0，原Go2 camera/inertia、资产独立inertia及parent resource identity保持。零step检查不证明动态机构、任务难度或RAMBO资格。

资产包含真实slide/U形hook、竖直/水平铰链、单bar valve及Room Door的lever→eccentric cam→bolt→空心strike socket。全部为本项目参数化几何，source/版本/hash/许可状态如实记录，公开再分发许可尚未断言。Room Door的cam行程、spring/friction与同步按压推门，Drawer的真实穿hook等仍待资产批准后物理验收；不得以预设关节姿态或无初始穿透冒充真实解锁/操作成功。

流程具有两个整批人工gate：先审核剩余六task的全部候选资产；这批资产获批后，完成各task物理资格并各生成一条高质量reference及适用范围，六条集中交审。只有用户批准这整批六条reference/范围后，才按task顺序直接合成各100条；仅完成或批准其中一条reference不能先启动该task的100生产。 不设10pilot人工审核。每task一次WAM v2/v3资格放在最初合格Clean＋Randomized production工程准入并计入100，100全量检查和随机十条最终验收保持。DATA027保持active等待资产批准；本轮v2DOC-024/v3DOC-023仅治理，完成后配对归档；无WAM/cache/训练/AMD/source commit/push或新资产发布。已验收四task400和全部旧receipt保持；HF400由独立DATA026及原monitor收尾，不启动第二上传写者。以下旧pending/10pilot规则保留历史，对剩余六task以新决定为准。

## 剩余六task改为批量资产→reference→直接100 — 2026-10-15

用户明确取消剩余六task的10pilot人工审核：先集中交付Sweep/Fridge/Oven/Valve/Drawer/Room Door全部候选资产，批准后各task实际物理资格及高质量reference/适用范围交审，reference批准后按task顺序直接100。当前QLM-DATA-027仅候选资产/Native零step静态预览，未获批前不physics/reference/100。每task最多1primary+2backup，不制造backup配额；原数据/控制/physics/camera/成功判据与独立质量门槛保持。

每task一次WAM v2/v3兼容资格仍保留，移到最早合格Clean＋Randomized production工程准入并计入100，不新增人工pilot gate；100全量检查和随机10最终整task验收保持。原四task400已验收，不改旧pilot/receipt。HF上传由QLM-DATA-026及mujoco400-hf定时监看独立收尾，private保持、main验证后切换/Isaac-based保留原SHA；本阶段不第二上传写者、不WAM/cache/训练/AMD/source GitHub发布。v2DOC-024/v3DOC-023仅治理。新流程权威见QLM decisions/remaining-six-batch-approval.md；下面旧10pilot规则只保留历史，对这六task由新决定取代。

## Kick100最终用户验收；累计400，先发布HF — 2026-10-15

用户明确批准Kick100整task，独立receipt在workspace runs/audit/kick100-acceptance-20261015-v1/user-acceptance.json；原technical/attempt/随机抽样记录不改。Push100＋Press100＋Lift100＋Kick100=400/1000，四task均20Clean/80Randomized、80train/10validation/10test。Kick收尾完成，下一工作仅QLM-DATA-026发布现有400至dontKnow23456/QLM-Bench main，将完整原main保留为Isaac-based，其他task暂不启动。

HF实际private保持，现有dontKnow23456登录已具write权限，未要求新token；如实际授权不足按用户要求暂停。先materialized staging/完整性验证，再保存旧main及临时分支上传回读，最后精确HEAD保护切换main。原数据/source/asset/controller/camera/consumer身份不变；WAM v2DOC-023/v3DOC-022只治理，不复验已有每task资格、不新cache/fit/训练。当前尚未上传或改branch；实际进度看workspace runs/audit/mujoco400-hf-publication-20261015-v1/。无source GitHub commit/push、AMD或新task合成。以下pending仅历史。

## Kick100工程交付；随机十条等待最终验收 — 2026-10-15

QLM-DATA-025保留原已批准10条＋新90条，全100NativeCPU/原RAMBOCPU＋NativeEGL，80train/10validation/10test、各split20%Clean/80%Randomized，76950actions/77050boundaries。100物理身份唯一，跨split无近重复；相同批准4D ID支持，不分割变量范围/无OOD。原A primary、两背景、v3 recipe、ball XY±3cm/goal X±8cmY±5cm、原RAMBO/native9/500-100-50Hz/camera/实体goal正面整球入门/notfallen/三tick保持，无范围收缩、backup配额或成功physics重跑。

完整Raw/Canonical/媒体/50Hz boundaries/command/terminal/原telemetry逐列及完整snapshot球pose/速度/goal核对通过。task success与quality独立，准备球最大位移0.0000mm、其他robot碰球50Hz geometry合计0，零/未知FL contact不硬失败，不新增高频diagnostic永久存储要求。原十条完整payload/media/source字节身份保持；合并Canonical100与明确Raw/episode相对symlink视图在workspace data/qlm_bench/kick100-20261015-v1/，发布前需独立materialized staging。

普通3physics+3render已实际同时达到=True；available1GiB/launch-relative swap增长7.6GiB/紧急render-only回收0.5GiB/新render≥4GiB及pressure后render≤2保护保持，资源事件0。新增90pipeline 1712.9s≈189.15条/h（含准入/媒体验收/资源恢复，工程准备、最终合并和附加审核视角不含），不作稳态保证。实际政策/进程/失败与恢复见execution-policies和events。新physics尝试90、失败candidate0，不能用成功筛选收集作policy SR。

Kick task一次WAM v2DATA-019/v3DATA-009复用，未WAM执行/新模型cache/fit/训练；v2DOC-022/v3DOC-021仅治理。三Work工程交付后归档，用户对完整100最终验收仍pending。全100均匀无放回seed202610152510随机十条在workspace runs/audit/kick100-random-review-20261015-v1/review.html；不按quality/split/backend/原pilot筛选。宽视角仅人工诊断，不改变正式双640×36050FPS/Observer1280×72025FPS/模型输入语义。

原Push/Press/Lift300已获最终验收，Kick100现为工程交付，未提前计作用户最终验收400。public registration仍planned，不冒充public runtime全部ready。无其他task/AMD/commit/push/发布；OSMesa reference及AMD主线保持。以下pending/生产中仅描述原历史时点。

## Kick十条pilot获批；3+3补至100 — 2026-10-15

用户批准全部十条并授权100；QLM-DATA-024归档，QLM-DATA-025保留原10＋新90。目标80train/10validation/10test、各split20%Clean/80%Randomized，相同批准4D ID支持/跨split去重，A primary/两背景/原recipe/controller/physics/camera/task predicate保持。NativeCPU/RAMBOCPU＋EGL普通3physics+3render，原1GiB/7.6GiB launch-relative swap/0.5GiB render-only/4GiB新render保护保持。当前生产尚未完成，不提前宣称100交付。

审计workspace runs/audit/kick-scale100-20261015-v1/，data/qlm_bench/kick100-20261015-v1/；WAM task一次v2DATA-019/v3DATA-009复用，不重复验证/cache，v2DOC-022/v3DOC-021只治理。完成全量检查/合并及全100无放回随机十条后交用户整task验收。原300与pilot/source身份保持，无其他task/训练/AMD/commit/push/发布。以下pending等为历史时点。

## Kick十条formal pilots工程交付；等待用户审核 — 2026-10-15

用户已批准v3 reference与完整ball XY±3cm/goal X±8cm Y±5cm范围。QLM-DATA-023归档，QLM-DATA-024完成全新2Clean8Randomized/alltrain十条，7832actions/7842boundaries、十个唯一物理身份；10次physics、0失败candidate。A primary、两背景、原recipe/controller/IK/PD/QP/history/physics/asset参数/native9/500-100-50Hz/camera保持，没有范围收缩、backup配额或成功physics重跑。formal新增十条仍待用户审核，最终已验收计数仍300/1000。

完整Raw/Canonical/媒体/50Hz action-state/完整command确认/terminal/原telemetry逐列、实际snapshot pose/速度/goal及独立正面整球入门/notfallen/三tick审计通过。准备阶段球最大位移0.0000mm；FL接触1–6个50Hz boundary，其他robot碰球0；最后FL接触后自由滚动2.42–4.44s。task success与quality分开，未知contact不硬失败，不新增高频diagnostic永久存储要求。

NativeCPU/RAMBOCPU＋NativeEGL真实同时3+3=True，1GiB暂停physics/7.6GiB launch-relative swap排空/0.5GiB仅render回收/新render至少4GiB及pressure排空保持。正式pipeline 215.2s≈167.29条/h（包含正式媒体验收，不含工程准备、WAM资格和附加审核出图），不作稳态保证。双RGB640×36050FPS/原Observer1280×72025FPS保持；同timestamp完整snapshot镜像不推进physics。宽视角仅人工看清球路/goal，不属于policy或formal Observer。

v2DATA-019/v3DATA-009各一次Kick Clean01＋Randomized04实际Reader/原VAE/SFT-input/online/cache回读、正确Kick prompt及v3实际10D通过并归档，原三task未复验、不fit/训练，同Kick扩100不再复验。public registration仍planned；当前仅显式MuJoCo profile正式数据链路通过，不声称public runtime全部ready。

审核workspace runs/audit/kick-formal-pilots-20261015-v1/review.html、report.md；合并Canonical及明确Raw相对symlink视图workspace data/qlm_bench/kick-approved-pilot-20261015-v1/（发布前需materialized staging）。QLM-DATA-024保持active等待十条动作质量/覆盖/吞吐审核，未授权100。原Push/Press/Lift300、source heads/资产/模型/环境锁保持。无其他task/AMD/commit/push/发布。以下pending只保留原历史时点。

## Kick reference/完整范围获批；十条pilot开始 — 2026-10-15

用户批准v3 reference与ball XY±3cm/goal X±8cm Y±5cm，QLM-DATA-023归档，QLM-DATA-024执行全新2Clean8Randomized/alltrain十条。A primary/两背景/原recipe/controller/physics/camera/数据接口保持；NativeCPU/RAMBOCPU＋EGL普通3physics+3render，1GiB暂停physics/7.6GiB launch-relative swap排空/0.5GiB render-only回收及原4GiB新render门槛保持。新Kick正式准入尚待本轮验证，不提前宣称十条完成；public registration仍planned。

证据workspace runs/audit/kick-formal-pilots-20261015-v1/；v2DATA-019/v3DATA-009只做本Kick task一次Clean+Randomized实际兼容，原三task不复验、不训练。完成交用户十条pilot审核，未批准前不100；原Push/Press/Lift300/1000验收保持。无AMD/commit/push/发布。以下pending仅保留原历史时点。

## Kick reference与范围工程交付；等待用户审核 — 2026-10-15

已批准A primary/B-C backups及实体球门；QLM-SIM-019的Native/CUDA三资产各7项被动物理、真实接触/reset/mirror均通过。新Kick判据为正面整球入实体goal/notfallen/三50Hz ticks，旧三task判据和action/state/Raw/Canonical接口保持；public task注册仍planned，未冒充formal production ready。

QLM-DATA-023交付推荐kick-impulse-retract-v3-tucked-carry reference：原RAMBO NativeCPU真实16.22s、811actions/812boundaries，pre-strike球位移0，FL接触仅strike阶段3个50Hz boundary，之后自由滚动4.22s入门；原gait小幅波动保留。三个nominal开发成功trace全部保留，未训练或改controller/IK/PD/QP/history/asset mass-friction。

v2首轮范围11/16、5timeouts保留；只将高层carried FL目标X .23→.16后，对相同seed42、相同完整16角点和两背景重新真实执行，v3为16/16，全部pre-strike位移0，50Hz snapshot未发现其他robot部位碰球。范围提案ball X/Y±3cm、goal X±8cm/Y±5cm，仍待用户批准；未按结果收缩或搜索seed，不宣称全连续状态或policySR。两轮对应model resource identity逐点相同，16点球/goal都可由原policy相机观察。

审核workspace runs/audit/kick-reference-20261015-v1/review.html与report.md，宽视角画面只用于人工诊断，原Ego/Task/Observer、dual360p50FPS和Observer720p25FPS保持；所有图像导入真实同timestamp snapshot，不独立推进physics。DATA023保持active，等待reference动作质量与范围审核；未批准前不10pilot/100，formal Kick0，原Push/Press/Lift300/1000已验收保持。Kick task一次WAM资格留pilot，v2DOC-021/v3DOC-020仅治理，无WAM执行/cache/训练/AMD/commit/push/发布。后续本地普通3+3/swap增量7.6GiB及原保护保持。以下旧pending只保留历史时点。

## Kick三资产已获批准；物理资格通过，reference开发 — 2026-10-15

用户批准A黑白球primary、B橙色/C蓝白球backups与共同实体球门，asset gate解除。QLM-SIM-019已建立portable Go2/原STEP LODa02 pack，原robot/camera/solver不变；A/B/C各7项Native及CUDA-MJWarp被动物理/真实接触检查、双world reset隔离与完整timestamp镜像通过。这些初始动量诊断不是RAMBO demonstration，AMD尚未验证。

QLM-DATA-023继续真实FL踢球reference和retarget范围。a01原RAMBO/native9真实15.08s入球成功，准备阶段有提前轻碰；当前只调高层预接触间隙进行有界改进，任务成功不等于动作质量通过。原三task predicate/action-state/Raw/Canonical/500-100-50Hz/camera保持；Kick新增独立正面全球入门/三tick/notfallen predicate，拒绝初态门内和侧后入门。资产质量/摩擦/尺寸不修改，成功trace保留。reference/范围用户审核前不10pilot/100，正式计数仍Push100+Press100+Lift100=300/1000。

审计workspace runs/audit/kick-reference-20261015-v1/，批准receipt为asset-approval.json。WAM v2DOC-021/v3DOC-020本轮只治理；新task一次兼容性留pilot，不复验已有task、不生成cache或训练。后续本地NativeCPU/RAMBOCPU＋EGL、普通3+3与swap增量7.6GiB/原保护保持，无AMD/commit/push/发布。下面资产pending等均为历史时点。

## Lift100已获用户最终验收；下一task Kick先审资产 — 2026-10-15

用户明确批准本次手机静态审核并要求进入下一task。独立receipt在workspace runs/audit/lift100-acceptance-20261015-v1/user-acceptance.json，明确实际审阅为原随机十条中的067/099各三个真实时点，并非手机已观看十条动态视频。Push100＋Press100＋Lift100累计300/1000，三份原数据/technical/attempt/selection记录保持。手机派生GIF/JPEG/展示metadata共8文件16202281bytes已按批准清理；正式Raw/Canonical、PhysicalTrace、原随机十条MP4/review及用户上传截图保留。

下一task为Kick Ball to Goal，QLM-DATA-023仅交付候选资产静态审核：A黑白拼片球（建议primary）、B橙色训练球/C蓝白拼片球（建议backups），共用真实门柱/横梁/后侧球网的实体训练球门。全部项目自建参数化几何；球直径20cm/0.40kg、球门净宽80cm/净高45cm/深40cm均为待批准候选参数，不是冻结pool或难度已验收。三模型compile和15路NativeEGL静态views通过，physics/controller/reference/formal均0；task注册仍planned。审核包workspace runs/audit/kick-asset-review-20261015-v1/review.html。

继续资产审核→物理资格及高质量reference/retarget范围审核→10pilot审核→100及最终验收；本轮停在候选资产审核，不跨gate。保持1primary+最多2backup、两背景/无clutter/无强制Recovery、原RAMBO/native9/时序/camera，未来本地普通3+3和swap launch增量7.6GiB/其余资源保护不变。QLM-DOC-007/v2DOC-020/v3DOC-019只做本轮验收清理及consumer治理；Push/Press/Lift task一次WAM资格复用，Kick的新资格留formal pilot。无WAM执行/cache/训练/AMD/commit/push或发布；原篮A asset包license unknown不改写。以下pending/旧并发仅为历史时点。

## Lift100技术交付；随机十条等待整task审核 — 2026-10-15

QLM-DATA-022完成原批准10条CUDA/OSMesa＋新增90条NativeCPU/RAMBO CPU/EGL，80train/10validation/10test、各split20%Clean/80%Randomized；100物理身份唯一、跨split无近重复。旧benchmark未恢复或计入，原十条source与媒体保持原样。原recipe/asset pool/±3cm±5deg/two backgrounds/无clutter/native9/500-100-50Hz/camera/20mm三ticknotfallen保持，Native/EGL来源显式记录，不宣称OSMesa像素等价。OSMesa reference和AMD优先ROCm保持。

完整Raw/Canonical/媒体/commands/terminal与原telemetry逐列检查通过，data/qlm_bench/lift100-20261015-v1/；Raw视图为明确相对symlink，发布前需独立materialized staging。早期4+4已实际达到；之后用户最新采用3physics＋3render、swap相对launch基准增长7.6GiB。完整生产的资源保护、render-only回收、主调度中断后的在途排空与各次实际恢复均据实记录，不重跑成功physics。实际launch见workspace runs/audit/lift-scale100-20261015-v1/execution-policies/，不把单轮benchmark冒充持续生产吞吐。

Lift task一次WAM v2DATA-018/v3DATA-008资格复用，未执行WAM或生成模型验证cache，v2DOC-019/v3DOC-018仅治理。QLM-DATA-022工程交付后归档，最终整task人工验收仍pending。全100无放回随机十条seed202610152210在workspace runs/audit/lift100-random-review-20261015-v1/review.html，不按quality/split/backend筛选。Push100和Press100验收保持；其他tasks、训练、AMD、commit/push/发布未执行，A license unknown不改写。以下pending等只描述原阶段。

## 最新本地合成配置：3physics＋3render，swap增量7.6GiB — 2026-10-15

用户明确要求“后续保持3+3的并发，把swap增量保护上限提高至7.6GiB”。本地路线仍为Native MuJoCo CPU／原RAMBO CPU＋Native EGL GPU rendering，保持重叠流水线。普通新launch目标改为3physics＋3render；host swap相对本launch基准增长>7.6GiB（8160437862 bytes）触发排空。MemAvailable<1GiB暂停新physics、<0.5GiB回收最新render-only、新render至少4GiB、pressure后render上限2保持。旧4+4/6GiB政策只代表原launch，不回写；成功trace不重跑。

QLM-DATA-022以独立runtime-policy-v3和resource-policy-v3.json落实本次调度变更，冻结producer/campaign/recipe/physics/controller/camera/Raw/Canonical/split不变。审计在workspace runs/audit/lift-scale100-20261015-v1/。Lift原十条已批准，100生产进行中，完整交付及最终整task用户审核尚未完成。WAM v2/v3每task一次资格继续复用，不运行WAM或新增验证cache。以下旧配置/pending叙述均保留原历史时点。

## Lift十条pilot已获批准；NativeCPU/EGL4+4补90 — 2026-10-15

用户本轮批准全部十条Lift pilot，并指定采用会话01a13d38-5941-72d0-9a67-57f79b21478b更新配置扩100。QLM-DATA-021已归档，新QLM-DATA-022保留原十条CUDA/OSMesa数据及source身份，新增90采用Native MuJoCo CPU／原RAMBO CPU＋Native EGL，4physics+4render流水线，原1GiB/6GiB/0.5GiB与4GiB新render/pressure排空保护保持。目标80/10/10、20Clean/80Randomized，同ID配置分布/跨split去重；不制造backup配额或Recovery，不改recipe/任务物理谓词/native9/时序/camera。

已接入Native正式trace标记与EGL真实GL/provenance；旧benchmark未恢复或计入，原十条不重绘。32项相关检查通过，当前先实际Clean+Randomized各一条端到端准入，未将配置采用冒充生产完成或OSMesa像素等价。OSMesa reference与AMD优先ROCm保持。WAM task一次资格v2DATA-018/v3DATA-008复用，v2DOC-019/v3DOC-018只治理，不执行WAM验证或cache/fit/训练。

当前生产证据workspace runs/audit/lift-scale100-20261015-v1/；data/qlm_bench/lift100-20261015-v1/。结束后全100检查、合并并随机十条交用户整task验收。未启动其他task、训练、AMD、commit/push或发布，A asset license unknown不改写。以下pilot pending等均为原历史阶段。

## 用户采用本地Native CPU＋EGL 4+4 — 2026-10-15

用户明确选定后续本地配置：Native MuJoCo CPU physics／原RAMBO CPU＋Native EGL GPU rendering，4physics＋4render，维持重叠流水线；替代先前3+3建议。唯一来源为[本地合成配置](docs/scaleup-v1/decisions/local-synthesis-concurrency.md)，治理Work ID为QLM-DOC-006。原1GiB/6GiB/0.5GiB、4GiB新render及pressure后render上限2保持。OSMesa跨平台reference与AMD优先ROCm-MJWarp保持；4+4不自动套用其他backend。

本轮只更新治理，未修改producer/runtime/validator或启动新合成。单轮压力测试不等同于完整生产、视觉等价或长期稳定性验收；后续实际producer接入与既有端到端准入仍须落实，不能当作已实现。原数据/launch身份、原controller/native9/时序/camera/Raw/Canonical保持；Lift十条人工审核仍pending，正式验收仍Push100＋Press100。QLM-SIM-018测试产物已清理，不恢复或新增验证缓存。下面旧3+3/CUDA＋OSMesa叙述仅保留各自历史阶段。

## Lift Basket十条formal pilots交付；等待用户审核 — 2026-10-15

QLM-DATA-021完成全新10条2Clean/8Randomized、全部train，7506actions/7516boundaries，十个唯一物理身份；十次首次physics均成功，无范围收缩、backup配额或成功physics重跑。原A OASIS主资产、lift-body-lane-geometry-v2、dx/dy±3cm/yaw±5deg、两Background、原RAMBO/native9/force-zero、500/100/50Hz、整篮最低点20mm/notfallen/三tick保持。Clean为真实小幅几何变化，非同初态重复。

完整Raw/Canonical、50Hz boundaries/commands/terminal、原telemetry逐列与全部媒体检查通过，合并Canonical在workspace data/qlm_bench/lift-approved-pilot-20261015-v1/canonical。双RGB640×36050FPS/Observer1280×72025FPS，独立NativeOSMesa mirror不推进physics。十条完整穿孔后托举；实际CUDA50Hz snapshots在Native重建接触几何，FL腿部27–38个boundary、base合计0，不是独立CUDA force telemetry，sphere-only接触0不硬失败。task success与demonstration quality分开，不新增全体500/100Hz诊断永久保留要求。

v2 DATA-018/v3 DATA-008各一次实际Clean01+Randomized04 Reader/原VAE/SFT-input/online/cache及正确Lift prompt通过并归档，后续同task扩量不重复模型验证/cache，不fit或训练。QLM-DATA-021保持active，十条动作质量/覆盖/吞吐用户审核pending；工程交付不等于用户批准或policy success rate。

初始4+4尝试未同时达到，保留旧保护事件与一个render-only回收/同trace恢复。续跑实际1physics+2render，采用用户更新的1GiB available/6GiB launch-relative swap增长/0.5GiB render回收，未打断执行中的worker。用户当时确定后续新launch默认3+3并行流水线，不采用分阶段模式；3+3稳定性不因配置决定而被宣称通过。实际总pipeline 3895.2s≈9.24条/h，含保护排空与续跑，不是稳态保证。

审核workspace runs/audit/lift-formal-pilots-20261015-v1/review.html、report.md；完整receipt/资源policy/质量证据同目录。Push100+Press100仍为人工最终验收200/1000，Lift十条等待审核。A资产包license unknown保持，仅本地，无扩100、训练、AMD、commit/push或发布。下方pending/旧配置只描述各自原阶段。

## 历史：维持流水线与当时3physics+3render默认 — 2026-10-15

用户当时明确维持physics与rendering同时推进，后续新launch默认3physics+3render；不采用先全physics再render的阶段模式。资源保护使用最新1GiB available/6GiB launch-relative swap growth/0.5GiB render-only eviction；既有4GiB新render启动门槛和pressure后的排空机制保持。3+3是配置目标，实际重叠与稳定性按launch/resource证据记录，不预先宣称通过。

当前Lift十条的第二launch已经以1+2运行，保留该实际配置完成，不中断worker、不重跑成功physics或旧媒体，也不改写旧launch。完成十条后交用户审核，未批准前不100。批准来源workspace runs/audit/lift-formal-pilots-20261015-v1/streaming-concurrency-decision.json；stage-scheduling-assessment.json只是先前讨论，未被采用为默认路线。

## 用户更新资源保护阈值 — 2026-10-15

后续新launch采用MemAvailable<1GiB暂停新physics、host swap相对本launch基准增长>6GiB触发排空、MemAvailable<0.5GiB回收最新render-only worker。机制保留，render启动门槛4GiB及pressure后上限2不变。这是用户明确更新，替代早先2GiB/512MiB/1.5GiB默认；旧launch/事件/receipt保持原值，不能改写成新值。当前已latched的初始launch先排空成功trace，下一launch用版本化resource-policy-v2.json，以1physics+2render完成剩余三条；不自动重试4+4或扩100。

workspace runs/audit/lift-formal-pilots-20261015-v1/resource-policy-v2.json与runtime-policy-v2/source-provenance.json记录用户来源、执行层source和精确bytes。只替换等待中的续跑supervisor，当前renderer未中断。原frozen QLM producer/campaign/recipe/physics/controller/camera/数据分布逐字节保持；执行层policy单独版本化，后续治理与新campaign须沿用批准阈值。当前physics与RAMBO主要Torch计算在CUDA；NativeOSMesa render为CPU软件出图，不使用EGL/GPU batch renderer。

## Lift reference/范围已批准；十条pilot与4+4尝试 — 2026-10-15

用户批准lift-body-lane-geometry-v2 reference与dx/dy±3cm、yaw±5deg，授权十条formal pilots并尝试4physics+4render。DATA020归档，QLM-DATA-021执行2Clean(ap00小范围真实几何变化)+8Randomized(两背景)、全部train，仅primary A OASIS，backup无配额。asset pool/50candidate/source/recipe已冻结，实际campaign及记录workspace runs/audit/lift-formal-pilots-20261015-v1/；data/qlm_bench/lift-approved-pilot-20261015-v1/。RAM/swap保护后保留成功trace，有据排空/降档，不改变source/分布或重跑成功physics。

保留原whole-basket20mm/notfallen/三tick谓词及全部action/state/camera/native9/RAMBO时序，新增Lift录制准入独立核对完整几何与实际snapshot，不能借Push/Press predicate过关。Raw/Canonical接口不变。sphere-only contact0或unknown不硬失败，实际FL腿部/机身操作证据与task success分开。v2DATA-018/v3DATA-008只做本Lift task一次Clean+Randomized实际compatibility，原Push/Press不重复，不fit/训练。当前formal十条尚未交付，用户pilot审核pending，未授权扩100；无AMD/commit/push/发布，A asset包license待办不因审批改写。

## Lift Basket A reference交付；等待动作质量与范围审核 — 2026-10-15

A原OASIS编织篮为用户指定primary、B/C为backups。QLM-SIM-017的Native/CUDA被动物理资格三资产均通过；A原RAMBO实际高层recipe lift-body-lane-geometry-v2完成770actions/771boundaries、15.40s success/not-fallen，整篮最低点30.848mm，原20mm/三50Hz ticks判据未改。完整足端先穿孔后托举；实际snapshot几何为FL腿部接触38boundaries、base/其他腿0，sphere-only FL接触为0不直接拒绝。

原expert抬腿/伸腿hip最大10ms约5.3deg，推荐v2相应1.0–1.2deg、托举1.99deg；保留原gait及三成功开发trace，不宣称所有波动消失。仅高层Base/FL站位/轨迹连续性改变，原controller/IK算法/PD/QP/history/physics/camera/asset/default保持。预声明dx/dy±3cm、yaw±5deg八个product角点8/8实际成功，无重试/收缩，完整穿孔后托举/base-contact0；范围是proposal仍待用户批准，不是policy SR或全部seed验收。

完整NativeOSMesa双640×36050FPS/Observer1280×72025FPS及terminal验证通过，完整同timestamp snapshot镜像未推进physics；两个Background只换floor外观，非visual/camera/solver完全相同。主render507.4s/15.4s simulation（非稳态生产吞吐保证），scope2physics实际并发总820.1s，无guard，最低available6.97GiB/maxswap增长212.32MiB。范围trace是非formal geometry诊断，早期nominal task.goal.XY配置偏移元数据不提升为正式data；未来入口已用既有episode-goal overlay对齐初态XY，实际Native零步检查仅goal字段变、物理和其他state不变，旧trace不改写。

审核workspace runs/audit/lift-reference-20261015-v1/review.html与report.md。QLM-DATA-020保持active等待reference动作质量和范围审批，未批准前不10pilot/100。Lift正式0、Push100+Press100累计200/1000。WAM兼容性每task一次留pilot，本轮未加载WAM/checkcache/fit/训练/AMD/commit/push/发布；A asset包license unknown待资源交付前核实，未因视觉审批改写。

## Lift Basket资产已获批准；A主资产与reference阶段 — 2026-10-15

用户明确批准三候选并指定原OASIS编织篮A为primary，B/C自建方篮为backups。批准receipt：workspace runs/audit/lift-reference-20261015-v1/asset-approval.json；旧静态review/metadata保持其原pending时点。QLM-DATA-020当前允许原RAMBO真实reference及retarget范围准备，必须停在reference用户审核；无10pilot/100授权gate解除。

QLM-SIM-017对A/B/C分别完成Native/CUDA自由落体与落地、真实FL碰撞半径sphere穿孔、真实接触响应、zero-step selected-lane reset/other-lane保护及完整state mirror；physics-qualification.json记录实际结果。passive检查不证明RAMBO任务成功或backup的SFT资格；A实际reference正在执行，B/C无需使用配额。原A scene/profile/default、task success/controller/history/camera/physics保持。A asset包license unknown仍未自动变成MIT，仅本地工程执行，发布/AMD资源交付前须闭合。

WAM v2/v3本阶段只同步治理(v2DOC-018/v3DOC-017)，不运行模型或cache；Lift正式task一次兼容检查留pilot阶段，Push/Press已通过资格不重复。formal accepted仍Push100+Press100=200/1000，Lift0；无训练/AMD/commit/push/发布。

## Press100已获用户最终验收；下一task先审资产 — 2026-10-15

用户明确批准随机十条审核并验收Press Button100。Push Box100＋Press Button100累计200/1000，均为新的MuJoCo轨迹，各自20Clean/80Randomized及80train/10validation/10test。新批准receipt：workspace `runs/audit/press100-acceptance-20261015-v1/user-acceptance.json`；Press原technical/attempt/随机审核receipt和完整Raw/Canonical不改写。

下一task为Lift Basket，QLM-DATA-020仅准备候选资产及Native MuJoCo静态预览，等待用户批准。每task资产审核→实际物理资格/高质量reference与retarget范围审核→10formal pilot审核→补至100及最终验收；最多1primary＋2backup，backup不制造使用配额。原Lift工程pack只是历史基础，不能冒充新formal资格。当前Lift正式条数0，reference/physics资格本轮not_run。

WAM v2/v3每task一次：Push、Press通过证据复用，同task扩量不重复Reader/VAE/cache/SFT/online，不产生新模型验证cache；Lift新task检查留formal pilot阶段。原native9/RAMBO/500-100-50Hz、dual-rgb-360p-v1/OSMesa/LOD a02、task success与独立动作质量保持。本轮未进行reference/controller/physics运行、WAM执行、训练、AMD、commit/push或发布。治理工作QLM-DOC-005、v2/DOC-017、v3/DOC-016。


## Press Button100本地交付与随机十条review — 2026-10-15

QLM-DATA-019完成已批准十条＋新90条，共100，train80(16Clean64Randomized)/validation10(2+8)/test10(2+8)，66903actions/67003boundaries。100物理身份唯一，跨split无近重复；同一批准ID支持，没有变量区间分割/OOD。primary工业红/full wall/fixed X/YZ范围/两背景/press-body-carry-v2/原RAMBO/native9/500-100-50Hz/360p50FPS/predicate保持。成功Trace独立NativeOSMesa，不推进physics；全部Raw/Canonical/media/terminal/原telemetry逐列验收与Canonical100合并通过。Raw100 view显式相对symlink原不可变bytes，发布前需独立materialized staging。

用户指定4physics+4render已实际重叠；首8条触发swap新增512MiB保护后停止新派发并排空，保留全部成功trace/数据。后续resource-safe实际launch政策见execution-policies，源码/recipe/config保持冻结；不把初始4+4计划冒充全程实际设置。新增90条实际queue2.08h≈43.3条/h，含保护和续跑等待，非稳态保证。新physics尝试91、失败1；成功筛选数据收集不作为policy SR。

WAM v2/v3 Press once-per-task receipt复用，本批没有Reader/VAE/T5/SFT-input/online复验、模型验证cache、fit/训练或权重修改；v2 DOC-016/v3 DOC-015仅治理归档。QLM-DATA-019也归档，工程交付完成；用户对最终100整task验收等待随机十条review。审核：runs/audit/press100-random-review-20261015-v1/review.html(全100均匀无放回，seed202610151910，无quality/split筛选)。主报告runs/audit/press-scale100-20261015-v1/；data/qlm_bench/press100-20261015-v1/。Push100原验收、Press reference/pilot/source heads/原models保持。其他tasks、训练、AMD、commit/push/发布未执行。


## Press100当前真实运行策略 — 2026-10-15

用户指定4+4已实测，首8条全部成功但swap触发512MiB保护，已排空并保留数据。现在实际3physics+2render继续同一冻结campaign b1b3e16e48638719fee1ceb8da33c1f1366f197ee6e4696dfb60ff8c4dca08cc。不要按原4+4目标擅自再升档或原地改source/config；user批复10及100授权保持。资源压力才有据降档，其他异常fail-closed。自动末端仅在实际100完成后合并验收/随机10/治理归档；没有WAM重复验证/训练/AMD/发布。队列及真实状态在runs/audit/press-scale100-20261015-v1/queue.json、execution-policies/、events.jsonl。


## Press十条获批，授权4physics+4render扩100 — 2026-10-15

用户明确批准Press全部十条，保留并计入100；QLM-DATA-018归档、新QLM-DATA-019补90条，最终80/10/10与20Clean/80Randomized。沿用冻结press-body-carry-v2/primary工业红/wallY/Z范围/两背景/原RAMBO/native9/500-100-50Hz/360p50FPS和真实predicate。独立4physics+4render，保留backpressure/RAM/swap保护与实际launch epoch记录；资源不足时排空并有据安全续跑，不改采样分布。WAM v2/v3 Press task已一次验收，不重复验证或新cache；v2 DOC-016/v3 DOC-015仅治理。完成100后固定seed均匀无放回随机10展示。当前生产尚未完成，不提前宣称100已交付；原pilot pending receipt保留历史，新批准receipt在runs/audit/press-scale100-20261015-v1/。无其他task/训练/AMD/commit/push/发布。


## Press十条formal pilots技术交付，等待用户质量审核 — 2026-10-15

新reference及三资产/wallY/Z范围已获批准；新recipe四角重验4/4通过。QLM-DATA-018完成10条新真实primary A trajectories(2Clean/8Randomized alltrain)，6735actions/6745boundaries；10次首次物理执行均成功，零body-button contact，无范围收缩或backup配额。原RAMBO/native9/500-100-50Hz/真实12mm三tick/not-fallen/camera/360p50FPS保持，Native OSMesa mirror不推进physics。完整Raw/Canonical、实际articulation snapshot、terminal/原telemetry逐列、媒体与唯一身份检查通过。推进FL hip摆幅4.60–5.66deg，最大10ms1.127deg；保留原gait小波动，task success与动作质量分开。

v2 DATA-017/v3 DATA-007完成Press各一次实际Clean+Randomized Reader/原VAE/SFT-input/online/caches回读与v3实际10D，Press instruction embedding匹配；两模型works归档。今后同task扩100不重复WAM验证。2physics+2render/最多4积压，实际pipeline 1054.0s≈34.2条/h，RAM最低10.79GiB，无swap增长/资源guard；task一次WAM与最后渲染并行，此吞吐非稳定生产保证。

审核入口workspace runs/audit/press-formal-pilots-20261015-v1/review.html、report.md；data/qlm_bench/press-approved-pilot-20261015-v1/。QLM-DATA-018保持active等待指定十条动作质量/覆盖/吞吐用户审核，未批准前不100/其他task。Push100用户验收及原reference/asset qualification/receipts/source heads保持。无正式训练/AMD/commit/push/HF或发布。


## Press新reference获批，启动十条pilots — 2026-10-15

用户批准press-body-carry-v2新reference；三资产/wallY/Z范围此前已获批。QLM-DATA-017归档，QLM-DATA-018先重验新recipe四角，再自动完成2Clean/8Randomized alltrain十条primary A formal pilots；v2 DATA-017/v3 DATA-007只做Press task级一次实际兼容性。pilot审核前不100；原RAMBO/physics/camera/predicate/range/storage接口保持。审计runs/audit/press-formal-pilots-20261015-v1/，无训练/AMD/commit/push/发布。


## Press推进抖动修复，新reference待审核 — 2026-10-15

资产与墙面Y/Z范围已获用户批准，旧reference动作质量被指出抖动。QLM-DATA-017新high-level body-carry/native9 recipe在相同scene/seed42下真实success，推进FL hip roll摆幅92.85→4.88deg、实际10ms跳变8.59→0.75deg；原controller/IK/PD/QP/history/physics/camera/predicate不变，小幅gait波动仍保留。审核包runs/audit/press-reference-smoothing-20261015-v1/review.html。D017保持active等待新动作质量审核；v2 DOC-015/v3 DOC-014归档。范围不重问，recipe获批后先在既定范围重验，再10pilot审核/100；formal Press=0，无WAM验证/cache、训练/AMD/发布/commit/push。


## Press范围已批准，reference抖动修复 — 2026-10-15

用户批准三资产与墙面Y/Z范围，但指出旧reference推进中操作腿肘部大幅抖动，动作质量未通过。QLM-DATA-017继续，只调整high-level trajectory/速度/可达空间，保留原RAMBO/controller history/physics/camera/predicate及已批准范围；重新实际执行和渲染一条reference，再交用户审核。证据runs/audit/press-reference-smoothing-20261015-v1/。不得用视频平滑代替物理修复，formal Press=0，无10/100、WAM检查、训练/AMD/发布/commit/push。


## Press完整墙面物理资格完成，reference待审核 — 2026-10-14

A工业红primary、B工业蓝/C急停红backup已获用户批准，三项Native/CUDA接触/弹簧/限位/wall/reset/mirror验收及真实原RAMBO FL按压通过。QLM-SIM-016/v2 DOC-014/v3 DOC-013归档；QLM-DATA-017保留active，主资产reference及Y0.10±0.03/Z0.30±0.02m四角点与两背景技术交付，等待用户动作质量/范围审核，formal Press=0。审核包runs/audit/press-wall-qualification-20261014-v1/review.html。Press默认source模型为新full-wall A固定pin，原LODa02/controller/时序/camera/predicate保持；旧无墙reference/Push100/资源与receipt不改写。未启动10pilot/100、WAM检查、训练、AMD、commit/push或发布。


## Press三资产获批，完整墙面环境 — 2026-10-14

用户批准A工业红primary、B工业蓝/C急停红backup，要求两个backup也通过MuJoCo物理验收；Press按钮改为装在整面真实碰撞墙，位置随机化为墙面内Y/Z，固定X安装深度。QLM-SIM-016负责新portable wall profiles及Native/CUDA接触/弹簧/限位/reset验收；QLM-DATA-017继续高质量真实FL reference/适用范围，审核前formal=0。原controller/native9/时序/camera/task success保持。旧无墙reference仅历史诊断，不直接计入新wall数据。当前权威决定为QLM docs/scaleup-v1/decisions/press-wall-assets.md；上一asset-first停止已被本次批准解除。无训练/AMD/commit/push/发布。


## Press候选资产先审核 — 2026-10-14

用户最新要求先确认Press Button候选虚拟资产。QLM-DATA-017当前停在asset review，未批准primary/backup；不继续reference执行/调试或formal pilot/100。已有一条original industrial-button的实际CUDA诊断reference及OSMesa capture在要求到达前完成，仅历史开发证据，不计正式数据、不代表资产或reference审核通过。候选A工业红按钮、B同几何工业蓝按钮、C急停红按钮，最多1primary+2backup；只准备无physics stepping的Native OSMesa资产外观预览。证据在runs/audit/press-reference-20261014-v1/asset-review/。Push100用户验收保持。


## Push Box100用户验收；下一个task为Press reference — 2026-10-14

用户审核随机10条后明确验收全部Push Box100。技术receipt和100条数据保持；新批准receipt在runs/audit/push100-acceptance-20261014-v1/。当前100/1000，80/10/10及20Clean/80Randomized。QLM-DOC-004/v2 DOC-013/v3 DOC-012同步当前状态。
下一task为Press Button，QLM-DATA-017仅准备现有industrial-button资产和高质量真实FL reference及适用范围，复用原RAMBO/native9/CUDA physics/OSMesa/LOD/360p时序。各task仍须reference审核→10条pilot审核→批准后补100；Press formal=0。WAM兼容性每task一次，Push不重复，Press本阶段not_run。当前task权威状态见QLM docs/scaleup-v1/task-synthesis-progress.md和QLM-DATA-017 active plan；不恢复撤销资产/FL实验，不训练/AMD/commit/push/发布。


## Push Box100本地数据交付完成 — 2026-10-14

QLM-DATA-016完成原批准10条＋新90条，共100条；train80(16Clean/64Randomized)、validation10(2/8)、test10(2/8)。100条真实物理身份唯一，跨split配置无近重复，原native9/RAMBO/physics/camera/success predicate/primaryBox05及批准范围保持。最终44563actions/44663boundaries。完整Raw视图与Canonical在data/qlm_bench/push100-20261014-v1/。
用户授权后实际试跑2＋2、3＋2和4physics＋3render；4＋3持续运行触发swap保护后，剩余13条降到3＋2完成。独立进程controller history/RNG/world，实际launch-policy和resource guard全记录；没有修改冻结physics源代码。WAM v2/v3验证每task一次，Push Box已有证据可复用，本次90条不重复验证、不产生模型验证缓存；34项旧pilot验证缓存payload约12.3MiB已删除，结果/manifest/来源metadata保留。
QLM-DATA-016及v2 DOC-012/v3 DOC-011均归档。审计与完整交付报告：runs/audit/push-scale100-20261014-v1/。其他9task、训练、AMD、发布及commit/push未执行。


## 用户授权并发试跑 — 2026-10-14

用户根据GPU/CPU/内存余量授权后续尝试多条并发。原单physics调度器已停止派发并等待在途任务完成；原source、campaign、90个配置、controller/physics/camera均不修改。当前使用审计根parallel_dispatch.py的独立launch-policy override，先2个独立one-world physics进程＋2个render进程；每个进程独立controller history/RNG，队列单写者、trace背压。
每个execution-policy记录dispatcher源码hash、旧campaign hash、实际candidate和起止时间；不把原冻结campaign中的单worker计划冒充实际并发设置。小批量后排空，依据真实吞吐、系统内存与GPU占用再决定3/4并发，资源或正确性失败则停止新增工作。WAM验证仍不运行。


## 已批准Push100；WAM兼容性每task一次 — 2026-10-14

用户已批准push-formal-pilots-20261014-v3的十条，计入Push Box100条；新QLM-DATA-016补90条，最终80train/10validation/10test，各split Clean/Randomized=20%/80%。旧十条pilot审核停止要求至此已满足。
WAM adaptation v2/v3兼容性检查按task执行一次。Push Box已有通过记录，扩量及同task后续批次不再重复Reader/VAE/cache/SFT-input/online验证，不生成这些缓存。逐条QLM物理结果、独立动作质量、Raw/Canonical、媒体、timestamp/terminal和split去重仍保留。未来若冻结contract确实改变，以独立变更评审处理，不能把普通批次重复验证设为默认流程。
用户明确授权删除本轮pilot验证派生缓存，保留验证result/manifest/hash和原始数据/模型。当前source与100条审计根为runs/audit/push-scale100-20261014-v1/；v2 DOC-012/v3 DOC-011记录规则与清理。无训练/AMD/其他任务/commit/push/发布。


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

## Latest reference and retarget review state — 2026-10-14

The user accepted reference quality. Six predeclared smooth-v3 retarget development
points now pass on the unchanged task predicate, with two backgrounds and visible
numerical-goal alignment. Read QLM docs/scaleup-v1/decisions/push-retarget-scope-review.md
and the active paired plans. Retarget scope review is still pending; do not count
these diagnostics as formal pilots or start100/AMD/training/publication. Original
reference, prior failures and historical data remain. Evidence: workspace
runs/audit/push-retarget-scope-20261014-v1/.

## Current Phase0–6 synthesis authorization — 2026-10-14

QLM-DATA-015 / shared-v2 DATA-016 / v3 DATA-006 implement the user's new explicit
Phase0–6 authorization. Read docs/scaleup-v1/decisions/automated-synthesis-v2.md
and its active plan. Preserve original predicate; quality is independent and
unknown FL contact is not automatic failure. Execution rates do not mandate all
high-frequency diagnostic retention; keep actual required Raw fields. Clean has
small real geometry variation; splits use distinct configs from the same ID
distribution. PrimaryBox05 and two-background/no-clutter/360p/dual-WAM constraints
remain. Review old ten individually. Only reference/retarget and final ten-pilot
quality are mandatory user review gates. No100/AMD/training/commit/push/publication.
Do not restore retired QLM-SIM-015 or discarded P3 assets. Earlier stops below
retain historical scope; new reference work is now explicitly authorized.

## Accepted-source publication completed — 2026-10-14

QLM-DOC-003 records explicit source commit/push of accepted720p eviction governance and
360p pilot rendition/dual-WAM compatibility on the three existing MuJoCo branches.
Implementation heads were read back at all five configured GitHub targets. Read
docs/scaleup-v1/work/archive/QLM-DOC-003/plan.md and workspace
runs/audit/mujoco-accepted-source-publication-20261014-v1/. Selected tree checks pass:
QLM120/v2 131/v3 59. Pilot action-quality review remains pending; current batch is
singleBox05 with small pose/goal shifts and slight floor-color presets. This source
publication does not approve task/asset-pool completeness, further collection,
training/evaluation or AMD. Earlier local-only/source-pending statements describe
their original phases. Experimental implementation remains outside this publication.

## Ten360p pilot reconstruction delivered — 2026-10-14

QLM-DATA-014 is locally archived with paired QLM-DATA-014/v2-DATA-015/v3-DATA-005.
Ten unchanged retained trajectories have new360p formal renditions,2Clean/8Randomized
alltrain,4540actions/4550boundaries. Full Raw/Canonical/media/original telemetry and
bothWAM actual Clean+Randomized Reader/VAE/SFT-input/online-input checks pass.
Physical and recording identities remain separate; newphysics0. Read docs/scaleup-v1/decisions/push-pilot-360p-rendition.md
and workspace runs/audit/push-pilot-360p-reconstruction-20261014-v1/review.html/report.md.
Stop at user pilot-quality review before100/other tasks. No training/AMD/publication,
commit/push or policy-performance claim. Earlier planning-only and old720p retention
paragraphs retain their historical scope and do not override this delivery.

## Approved old720p pilot payload eviction — 2026-10-14

User explicitly confirmed deletion. Old10pilot Raw/Canonical payload/preview/cache
was evicted under QLM-DATA-013/v2-DOC-010/v3-DOC-009; source metadata/history remains.
Ten successful PhysicalTrace, independent reference demos, TemplateBundle,360p inputs
and weights/assets remain. Read latest subsection of current mujoco-workspace.md and
workspace runs/audit/obsolete-pilot-payload-eviction-20261014-v1/. Old720p queue is
historical/unavailable as dataset; do not resume it or count re-renders as new physics.
User requested replanning only; no new synthesis/implementation/commit/push authorized
by this turn beyond the explicit deletion and required governance updates.

## Current MuJoCo consolidation — 2026-10-14

Read docs/scaleup-v1/decisions/mujoco-workspace.md first. Current MuJoCo branches are QLM migration/mujoco-foundation, WAM adaptation/v2-mujoco-sft and adaptation/v3-mujoco-sft. v2/v3 have equal priority and share explicit360p/50FPS input, never merge their model implementations. This cleanup authorizes ordinary source commit/push on these three branches only; no Isaac/OPD refs, remote deletion, new collection/training/AMD/model/data publication. Shared-v2 future allocation is the MuJoCo v2 worktree, mirrored only in QLM MuJoCo; original Isaac registries stay unchanged.

## Accepted RGB spatial-only adaptation — 2026-10-14

Read docs/scaleup-v1/decisions/rgb-resolution-360p.md and docs/scaleup-v1/work/archive/QLM-DATA-012/plan.md. This user-authorized work covers QLM plus v2 and v3 equally:640×360 policy RGB,50FPS,Observer720p/25FPS unchanged; old720p artifacts and checkpoint training hashes remain immutable. No formal data/training/AMD/publication/commit/push.

# QLM-Bench agent guide

## Delivered automated Push Box M0–M6 — QLM-DATA-011

Read docs/scaleup-v1/decisions/automated-synthesis.md and the archived QLM-DATA-011 paired records.
User authorizes ten formal pilots only:2Clean/8Randomized,all train,trace-only actual
CUDA physics then Native OSMesa offline state replay. No forced Recovery quota;
new failures keep lightweight logs,successful traces allow independent render retry.
Preserve historical attempts/P0–P2;do not restore discarded P3 assets. Stop at the
ten-pilot review before100episodes/other tasks. No training/AMD/commit/push/publication.

## Authorized P0–P2 source publication — QLM-DOC-002 / 2026-10-13

P0–P2 implementation commit 5d3c3b7c5d92 is published on this
independent MuJoCo branch with exact remote readback. The user explicitly authorized
this source batch. Read docs/scaleup-v1/work/archive/QLM-DOC-002/plan.md. This supersedes dated local-only statements only for that
source batch. P3 work remains local; original Isaac/main branches and all external
resource/data/model/media publication are outside this authorization.

## Current MuJoCo progress routing — 2026-10-13

Read docs/scaleup-v1/mujoco-progress.md first for phase status. QLM-SIM-013 and
v3/DATA-002 close P0–P2 local engineering; QLM-DOC-001 / v3/DOC-007 reconcile that
completion from chat 01a12ecf-e271-7573-983c-917082cd1c19. Use default LOD a02 and
OSMesa. Diagnostic bundles are not formal demos; P3 pools/pilots/capacity, P4–P6,
AMD and new SFT remain later work. Earlier investigation pauses and incomplete
P2 claims below retain their dated scope. This reconciliation does not start P3
or authorize new execution/publication. Keep existing implementation and receipts.

Read docs/INDEX.md, docs/current/overview.md, docs/current/contracts-v2.md,
 docs/current/publication-v2.md and .agent/PLANS.md. Follow docs/governance/documentation.md
and docs/governance/v2.md. WAM v2 reserves shared adaptation-v2 Work IDs; this repo
mirrors the declaration. QLM-Bench is the current name; RAMBO_Data remains the stable
historical registry/schema identity. Do not rewrite original governance hashes or archives.

The local main checkout is now workspace repos/QLM-Bench under shared-v2/INFRA-004.
Use that path for current runtime/configuration and peer links. Old local paths in
historical manifests, receipts and archived documents remain evidence of their
original attempts, not current filesystem routing. No old-path symlink is retained.

Work on the explicitly selected branch/worktree, verify actual Python import sources,
and use one paired ChangeSpec/ExecPlan for each multi-file work. Commit/PR titles start
with [CATEGORY-NNN]. Keep active plans and evidence current; archive only after gates pass.

QLM owns tasks, Isaac runtime, Go2/RAMBO adaptation, assets, experts, recording,
Raw/Canonical data and model-independent evaluation. CPU qlm_bench core must not import
Isaac, RAMBO controller, WAM, VAE/T5 or model frameworks. Simulator loading is explicit.
WAM owns model processing, normalizers and checkpoints; exchange public contracts only.

Preserve Go2/FL/native9, absolute FL target, original controller, float32 execution,
force-zero, command50Hz/controller100Hz/physics500Hz, dualRGB50Hz and diagnostic observer25Hz.
Preserve authoritative timestamps, completed-interval history and terminal-before-reset.
Task predicates and physics remain unchanged. Recorder does not own episode lifecycle.

The approved refactor removes obsolete biped/15D and nonformal tasks after extracting
shared dependencies; no legacy entry is introduced. Current controller residual/observation
dimensions and checkpoint restoration are not obsolete high-level interfaces.

All published releases, source identities and failed/quarantined attempt evidence stay
immutable. First WAM v2/v3 input remains Push Box DATA-006-20260916T075451Z at
4b5e0ed9aa04cbc1143774798f63171b27d838a7, 50 episodes/40-5-5. Later Lift/Press releases
do not extend those inputs. No new demonstrations or training. Explicit online inference work uses the public
physical-only live protocol described in docs/current/live-inference.md.

Use explicit resource roots and pinned runtime; do not reinstall shared editable bindings.
Local bounded Isaac/GPU regression is authorized by the workspace; keep actual attempts
and not_run explicit. No AMD connection/submission. Remote commit/push/rename/HF publication
uses its own authorization and exact reviewed inventory; historical publication permission
is not reused. Asset redistribution requires confirmed licensing. Run governance, docs,
import boundaries, affected CPU/artifact tests and required simulator regression before handoff.

DATA-002 remains the frozen wam-quadruped-v2.1.0 storage/terminal contract; public
QLM compatibility packaging preserves its original identity and validator.

INFER-001 shared-v2 completion is archived in docs/work/archive/INFER-001/plan.md.
Both original formal SFT WAM consumers completed real synchronous Isaac engineering
numerical/controller trials; read workspace runs/audit/close-loop-20261003/completion.json.
The previous Transformer-GPU/VAE-CPU placement failed the subsequent scene RGB gate.
Effective visual acceptance is withdrawn; current repair/evaluation evidence takes
precedence. Formal benchmark scores remain unavailable.

## Historical visual gate correction — SIM-002 / 2026-10-03

Visual inspection of EVAL-002 found almost-uniform grey ego/task/observer camera
arrays. The earlier INFER-001 task-camera terminal SHA also matches uniform238
RGB. The numerical model/controller/clock/KV/reset evidence remains factual, but
valid scene visual feedback and effective visual closed-loop acceptance are
withdrawn for that original placement. The repair and ten-trial local evaluation
are now completed under shared-v2/SIM-002/EVAL-002 and v3/EVAL-001; see the accepted
local evaluation below. The invalid first batch is preserved and excluded as an infrastructure failure,
without selecting for policy success. Do not publish a success rate from grey-camera
trials. Diagnostic artifacts/preview are in runs/audit/push-box-first-sft-eval-20261003.

## Accepted rendering repair and local evaluation

Read docs/current/push-box-first-sft-evaluation.md and completed paired
INFER-002/EVAL-002/SIM-002 records. Valid actual scene feedback requires
16 original BF16 Transformer blocks using CPU master/CUDA forward and frozen VAE CPU
on the tested16GB host. The old GPU-Transformer/VAE-CPU visual acceptance is withdrawn.
The complete ten-trial nominal-scene metrics and all media are accepted local evidence;
formal benchmark/generalization remain unverified. No source publication is implied.

## Latest inference audit correction — shared-v2/DOC-007

Read docs/current/inference-chain-audit.md. Chunk feedback is implemented, but
clean reset isolation is NOT accepted:9/9 later resets per policy carry the prior
terminal root-link velocity. V3 initial10D and shared RAMBO initial observations
are affected. Preserve6/10 and5/10 only as historical outcomes until reset repair
and rerun. Do not reuse the preceding acceptance paragraph as clean-reset evidence.

## Inference source integration — 2026-10-07

The user authorizes source commit/merge/push under shared-v2/DOC-008. Read
docs/current/inference-source-publication.md for integrated branch routing,
QLM live dependencies and the preserved reset limitation. This publication scope
supersedes prior local-only/source-publication-pending wording for these changes.
The user defers reset repair; do not perform one as part of this batch.

## Local path migration source publication — INFRA-004 / 2026-10-07

After local acceptance, the user explicitly authorized commit/push of the
repo-internal path/tests/docs/governance changes to the existing QLM synthesis
and WAM v2 adaptation targets. This supersedes the earlier local-only publication
exclusion for these changes. Workspace/environment metadata and audit payloads
stay local; v3, feature/reset changes, training, HF and simulator runs remain out
of scope. Exact source/readback receipts: workspace
runs/audit/qlm-local-rename-publication-20261007/.

## Later local reset repair — SIM-003 / 2026-10-07

The user's latest repair request supersedes the earlier deferral for this task.
Current QLM shared reset freshness passed21/21 actual three-task checks, including
controller/public/recorded state and original v3 consumer readback; see
[the accepted reset repair](docs/current/reset-state-freshness.md). The historical70 demonstrations/caches and
6/10 versus5/10 outcomes remain unchanged. No clean full-policy reevaluation or
new demonstration/training/publication is claimed. Use the repaired QLM source revision recorded by DOC-009; historical
serving pins do not include SIM-003.

## Reset source publication — DOC-009 / 2026-10-07

The user explicitly authorized commit/push of reset-related source/docs and the
prerequisite cleanup governance/routing records. Initial exact readback passed for
all five existing targets. Use docs/current/reset-source-publication.md for the
new immutable QLM repair pin; old serving pins remain historical provenance.
No data/model/media/HF publication or new execution accompanies this source batch.

## QLM-only Scale-up v1 — QLM-INFRA-001

The user explicitly scopes current scale-up work to QLM source/data only. Read
[the scale-up foundation](docs/scaleup-v1/README.md) and its independent
[QLM-only registry](docs/scaleup-v1/work-registry.json). Do not allocate these
works in WAM or modify its branches/shared-v2 registry. Historical shared governance
remains unchanged. Ten task plug-ins distinguish planned from ready; new tasks
remain unimplemented until their branch-specific gates pass. Use independent
task worktrees and explicit run60 source binding, not global editable reinstall.
Batch probes are temporary capacity checks, not demonstrations or benchmark evidence.

## Authorized MuJoCo P0–P2 — 2026-10-12

Read docs/scaleup-v1/decisions/mujoco-p0-p2.md. User authorizes local implementation and bounded physical/model
engineering gates on this independent branch. This supersedes historical no-feature/
no-rollout restrictions only for P0–P2. No full data synthesis, training, AMD or
publication. Use new versioned evidence; preserve original resources and checkouts.

## RAMBO verification before asset migration

The latest user request pauses original-task asset migration and requires RAMBO
checkpoint evidence first. Read docs/scaleup-v1/mujoco-foundation.md and archived
QLM-SIM-003. Original P2 procedural assets do not establish faithful migration or
preserved task difficulty; aggregate original-asset acceptance is incomplete. Actual
checkpoint RGB verification has a limited no-fall18s scope and weak yaw tracking.
Do not silently resume asset migration or label prior reconstructed RGB as recordings.

The later independent original-source comparison under QLM-SIM-004 supersedes
the source-of-yaw-error uncertainty: Isaac tracks0.15 with about0.143rad/s;
contact-only MuJoCo diagnostics recover most of the gap. Read the foundation
guide before interpreting this as retraining need or complete adaptation. The
contact3 diagnostic has not replaced the formal profile; migration remains paused.

## Completed local alignment repair — 2026-10-13

The user's latest active goal explicitly authorizes fixing every finding R01–R10
in the comprehensive MuJoCo review. This resumes asset/camera/physics implementation
and supersedes the earlier pause for investigation. Read docs/scaleup-v1/work/archive/QLM-SIM-005/plan.md. Preserve the
frozen action/data/model contracts and all original resources. Earlier complete
claims are historical; require per-finding actual evidence. No training, AMD,
source publication or formal demonstration collection is implied.

Local R01–R10 repairs are now complete with per-finding actual evidence. Read docs/scaleup-v1/mujoco-foundation.md and the
current evidence and workspace runs/audit/mujoco-alignment-repair-v1/report.md.
Box/Basket EGL admission failed the unchanged ROI gates; accepted engineering data
and model sessions use OSMesa. AMD execution, production capacity and formal task
statistics remain unverified. Original assets/weights/records are preserved; no
training, external publication or formal dataset synthesis was performed.

## Current collaborator camera rig — QLM-SIM-006

User selected the procedural support identified in WAM-Policy_Ethan. Read
docs/scaleup-v1/decisions/ethan-camera-rig.md. Current independent packs are
assets/mujoco/original-{task}-v1-ethan-rig-a01 at workspace level; previous a03 packs
and all recorded rollouts remain immutable. Mount/FoV,robot inertia and collision
are unchanged; actual fixed-state comparison verifies camera/three-view RGB.
No new training,inference evaluation,AMD or publication is implied.

## Current supplied STEP support — QLM-SIM-007

The latest user request replaces procedural support with the supplied STEP geometry.
Read docs/scaleup-v1/decisions/step-camera-rig.md. Current three-task packs use
v1-step-rig-a01; historical v1-ethan-rig-a01/v1-a03 and all records remain unchanged.
Source mass/density is unspecified; imported geometry has no mass contribution or
collision. Optical calibration is retained separately from the mechanical shape.
Actual same-state RGB and Native/CUDA checks passed; no new WAM/SFT/AMD/publication.

## Available rendering LOD — QLM-SIM-009

User requested a protected lightweight STEP rendering mesh andObservercomparison.
Read docs/scaleup-v1/decisions/step-rig-rendering-lod.md. Accepted engineering
LOD is v1-step-rig-lod-a02,withfullSTEP/procedural/source preserved. Camera,quality,
mass andcollision settings stay unchanged. Explicit modelselection usesLOD;
current defaultfullSTEP routing is not altered by a compare/generate request.

## Accepted LOD default and local payload cleanup — QLM-SIM-010

The latest explicit user selection supersedes the preceding default-full-STEP
statement. Read docs/scaleup-v1/decisions/mujoco-default-rig.md. Current MuJoCo
runtime/rollout/collection/new-evaluation entries default to v1-step-rig-lod-a02
through a shared pinned model set. Camera/quality/mass/collision are unchanged.
Keep explicit historical overrides and case identities; no silent old-asset fallback.

User authorizes eviction of obsolete local MuJoCo episode/media/state and dependent
caches, a narrow exception to old retention statements. All STEP/old/full/LOD models,
source/CAD intermediates, receipts/scalars, compact comparisons, Isaac references
and original weights/encoders/prompts remain. Removed historical paths describe
original runs, not local presence. Exact receipt: workspace
runs/audit/mujoco-lod-default-cleanup-20261013-v1/.
No new WAM rollout, formal collection, training, AMD, commit/push or publication.

## Current actual default-LOD WAM validation — 2026-10-13

Latest user explicitly authorizes three-task real v3 checkpoint closed loop on
LOD a02 with persisted Ego/task/Observer RGB. Read paired QLM-SIM-011 and
v3/INFER-005 archived plans in the respective local registries. This supersedes
the preceding no-new-rollout wording only for this bounded engineering matrix.
Retain original settings/weights and all new actual attempts/media. No training,
formal demonstrations, AMD, source publication or external uploads. Evidence:
workspace runs/audit/wam-v3-default-lod-rollout-20261013-v1/.

The actual matrix and media readback now pass:6episodes,18original720p videos,
606commands and96frozenRPC waits. Reset/eviction/terminal/source-frame and full
decode gates pass. Allsix short episodes end at the planned horizon,not a task-SR
acceptance. Read current MuJoCo guide and the new evidence review.

## Current full-horizon user request — QLM-SIM-012 / v3-INFER-006

Latest request supersedes the short2.02s scope:one actual rollout per task until
success/fall/24s timeout. Archived paired plans own the runner24s/75group guard and
bounded-memory full event audit. Camera/controller/physics/model parameters remain.
Keep all first outcomes/media; no outcome-selected retries. Evidence:workspace
runs/audit/wam-v3-default-lod-full-rollout-20261013-v1/. No training,formal dataset,
AMD,commit/push or external publication.

Full-horizon actual results:Push timeout24s;Press original displacement-predicate
success5.76s via visually indicated head/front-body contact;Lift timeout24s. No
falls/retries. Press is not an accepted FL skill demonstration. Nine original
videos and all2688command/342RPC freeze/media/reset/terminal gates pass. Read the
current guide,full review and interaction audit before interpreting task success.

## Final local P0–P2 closeout — QLM-SIM-013 / v3-DATA-002

The user requested both tail items and they now pass:three currentLOD diagnostic
Raw/Canonical/frozen VAE/10D readbacks plus Native/CUDA real object-hinge contact,
seeded initial states,zero-step reconstruction/reset,world isolation and RGB sync.
Read current MuJoCo guide and QLM final closeout decision. OSMesa continues by
explicit user decision. User confirms the retained checkpoint is Push Box-only;
Press body/head contact is not a closeout blocker,and the predicate stays unchanged.
Default production params/packs remain;new random state reset is explicit/validated
and nominal reset unchanged. Diagnostic hinge fixture is not a fourth task. Local
P0–P2engineering is complete;P3pilots/pools/production capacity,AMD,SFT and external
publication remain later gates. Evidence:workspace
runs/audit/mujoco-p0-p2-closeout-20261013-v1/. No formal demos/training/commit/push.

M0–M6 completed2026-10-14:ten pilots/4540actions/30videos validated;user review pending.
Use current implementation baseline/report. Stop before100/other tasks.
