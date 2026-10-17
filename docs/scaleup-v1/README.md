<!-- QLM-DATA-041 verified HF1000 release -->
## 十task精确prompt与private HF1000已验证发布 — QLM-DATA-041 / 2026-10-17

用户指定十句prompt已作为user-prompts-20261017-v1发布；既有400仅文本与必要hash/索引依赖更新，视频/数值/snapshot/command/terminal不变；新增600采用最终已验收版本，四项Observer为左后侧。main实际revision=470e0a1f290ef65a25ca1933a91a51ccd6427fcf，payload=b84488eca8a723767cef27fa455ec2ea8169f81c；private=True，Isaac-based=519725c8bc77b35fd5d3b4ac8555a3e96a8876a7保持。1000条=10task各100，800/100/100 split和200Clean/800Randomized，964151actions/965151boundaries。全远端LFS/Gitblob、20条Clean/Randomized独立data-only回读、精确prompt/索引/原400非文本保护均通过。

原始采集source/frozen-source/历史prompt及receipt不回写，新正式发布语言版本单独lineage。原冻结text encoder无梯度生成十项embedding，无训练/optimizer/WAM策略重复验证/physics/render/AMD。HF数据发布不自动切换历史TRAIN/EVAL输入；源repo所有此前未提交tracked/untracked源码/文档由用户明确授权统一commit/push。当前GitHub提交状态见workspace runs/audit/mujoco1000-prompt-publication-20261017-v1/github-commits.json；物理执行不冒称运行于后续新commit。
<!-- /QLM-DATA-041 verified HF1000 release -->

## 六task600条正式验收完成 — QLM-DATA-040 / 2026-10-17

用户已明确批准六项随机审核并要求正式验收登记与配对归档。Sweep/Fridge/Oven/Valve/Drawer/Room Door各100，共600条正式user_accepted；每task全100均匀无放回随机10，共60条审核通过。加上原Push/Press/Lift/Kick400条，累计10task、1000条正式验收完成。

独立验收receipt及逐条600登记在workspace runs/audit/remaining-six-acceptance-20261017-v1/：user-acceptance.json、formal-accepted600.json、protected-evidence.json。工程证据、原Raw/Canonical/PhysicalTrace/source/媒体和历史失败不改写；原400验收保持。累计610physics含Drawer原10失败，另Door2bootstrap为0physics；验收登记未执行新physics/render/WAM验证。

QLM-DATA-040已completed，ChangeSpec/ExecPlan配对移至QLM MuJoCo repo的docs/scaleup-v1/{changes,work}/archive/QLM-DATA-040/，active副本移除；权威登记为该repo docs/scaleup-v1/work-registry.json及remaining-six-formal-acceptance-20261017.md。监看保持停用，无训练/AMD/commit/push/HF发布授权；新增600尚未发布HF，原private HF400保持。以下pending/运行中只保留原历史时点。

## 六task各100工程完成；随机十条集中待审核 — QLM-DATA-040 / 2026-10-17

Sweep/Fridge/Oven/Valve/Drawer/Room Door各100，共600全新demonstrations已完成全量Raw/Canonical/实际snapshot/必需telemetry/command/terminal/媒体/source/去重检查和各task合并；700553actions/701153boundaries、600唯一实际trajectory。20Clean80Randomized和80/10/10 split逐项准确。六task一次双WAM共24项通过，扩量不重复模型验证。

累计610次physics=600成功+Drawer原10超时，历史失败保持。Drawer31旧source成功保留+69原scope-v5新成功；Door2次初始import失败为0physics/0commands，成功判据始终几何v3。成功physics未重跑，原reference/范围/RAMBO/reset/camera/native9和NativeCPU/EGL路线保持。最终241primary文件、6reference、原checkpoint、三repo HEAD和60审核视频/链接核对通过。

审核入口workspace runs/audit/remaining-six-production-20261016-v1/review.html：六项各从全100均匀无放回随机10，共60条，原400已人工验收与本次600最终人工审核pending分开。无训练/AMD/commit/push/新HF发布。当前physics/render/pipeline均结束；监看已停用，QLM-DATA-040配对active等待用户最终审核。完整报告docs/scaleup-v1/remaining-six-engineering-delivery-20261017.md；当前入口active-task-roots.json、completion.json、final-source-and-delivery-audit.json和progress.json。以下运行中/旧0/600/旧gate段落只保留历史时点。



## Reference中间产物已清理；当前获批证据保留 — 2026-10-16

按用户要求，QLM-DOC-009清理9870个reference迭代中间文件，逻辑37.66GiB；因硬链接实际可用空间观测增量约2.50GiB。原attempt/result/source/参数/文字记录保留，旧manifest不再保证历史payload可加载，不回写原成功/失败。

当前六reference及有效scope保留，10788个保护文件hash通过；6个reference资源/源码import和112个当前scope模型manifest、实际frozen source依赖核对通过。正式400、全局assets/模型/env未列为删除目标，未启动新合成。Sweep复用旧成功、Door A19原动作状态与v3范围等依赖仍保留。新会话继续使用当前绑定与交接文档，不能从已清理的旧试跑取数据，也无需重做已批准reference。

审计workspace runs/audit/reference-intermediate-cleanup-20261016-v1/：report.md、cleanup-receipt.json、historical-attempt-text-archive.json及完整清单。旧页面缺失媒体已标记；当前正式/获批文件不变。

## 当前交接：三项范围已批准，正式400/1000，剩余600待生产 — 2026-10-16

用户明确批准DATA039 Fridge/Oven/Valve三项修订范围，实际48/48工程通过；独立receipt为workspace runs/audit/revised-three-scope-20261016-v1/user-scope-approval.json，DATA039配对归档。六task当前资产/reference人工审核均已完成，Drawer/Door既有批准、Sweep A09批准保持；Sweep历史31/32及032失败不回写。

当前Push/Press/Lift/Kick各100，共400正式已验收并完成private HF400发布；剩余六task正式0/600，scope/reference不自动计入100。生产公共接入尚未完成：六registration仍planned、公共rendition仍限制旧四task、Door须用几何退栓v3适配，不能直接复用含旧20mm逻辑的generic helper。新会话需阅读交接后先与用户对齐，等下一条开工指令；本轮不生产。

当前权威交接：docs/scaleup-v1/handoffs/remaining-six-production-20261016.md（QLM MuJoCo repo）；完整绑定和可复制prompt在workspace runs/audit/remaining-six-handoff-20261016-v1/。未来沿用直接每task100，无10pilot人工gate；每task一次WAM兼容与全量工程检查，最终每task随机十条人工验收延后到六task全部完成。3+3/1GiB/7.6GiB/0.5GiB/4GiB政策保持。旧pending/旧角度/旧20mm/旧10pilot段落均是历史，不恢复已完成审批。

## 剩余六task候选资产静态包已生成；等待资产审核 — 2026-10-15

HF400最新实际状态：旧main已保留为Isaac-based，原SHA为519725c8bc77b35fd5d3b4ac8555a3e96a8876a7；private400正在临时分支上传，现有登录具write权限，无需新token。main尚未切换。mujoco400-hf监看已ACTIVE，首轮计划悉尼2026-10-16约01:13，上传回读验证后再收尾/切换；下方历史“尚未上传或改branch”仅描述原时点，不能作为最新状态。本资产Work不启动第二上传写者。

QLM-DATA-027已生成Sweep/Fridge/Oven/Valve/Drawer/Room Door各A/B/C共18候选（每task建议A primary＋B/C backups，无使用配额），Native compile＋mj_forward与72张NativeEGL静态图已生成；全部六task overview与Room Door背面cam/bolt近景已实际检查；18模型resource identity、72图hash/尺寸及页面相对链接QA通过（workspace runs/audit/remaining-six-assets-20261015-v1/visual-qa.json），用户资产批准仍pending。审核workspace runs/audit/remaining-six-assets-20261015-v1/review.html；verification.json记录physics steps=0/controller commands=0/reference=0/formal=0，原Go2 camera/inertia、资产独立inertia及parent resource identity保持。零step检查不证明动态机构、任务难度或RAMBO资格。

资产包含真实slide/U形hook、竖直/水平铰链、单bar valve及Room Door的lever→eccentric cam→bolt→空心strike socket。全部为本项目参数化几何，source/版本/hash/许可状态如实记录，公开再分发许可尚未断言。Room Door的cam行程、spring/friction与同步按压推门，Drawer的真实穿hook等仍待资产批准后物理验收；不得以预设关节姿态或无初始穿透冒充真实解锁/操作成功。

流程具有两个整批人工gate：先审核剩余六task的全部候选资产；这批资产获批后，完成各task物理资格并各生成一条高质量reference及适用范围，六条集中交审。只有用户批准这整批六条reference/范围后，才按task顺序直接合成各100条；仅完成或批准其中一条reference不能先启动该task的100生产。 不设10pilot人工审核。每task一次WAM v2/v3资格放在最初合格Clean＋Randomized production工程准入并计入100，100全量检查和随机十条最终验收保持。DATA027保持active等待资产批准；本轮v2DOC-024/v3DOC-023仅治理，完成后配对归档；无WAM/cache/训练/AMD/source commit/push或新资产发布。已验收四task400和全部旧receipt保持；HF400由独立DATA026及原monitor收尾，不启动第二上传写者。以下旧pending/10pilot规则保留历史，对剩余六task以新决定为准。

## Lift100已获用户最终验收；下一task Kick先审资产 — 2026-10-15

用户明确批准本次手机静态审核并要求进入下一task。独立receipt在workspace runs/audit/lift100-acceptance-20261015-v1/user-acceptance.json，明确实际审阅为原随机十条中的067/099各三个真实时点，并非手机已观看十条动态视频。Push100＋Press100＋Lift100累计300/1000，三份原数据/technical/attempt/selection记录保持。手机派生GIF/JPEG/展示metadata共8文件16202281bytes已按批准清理；正式Raw/Canonical、PhysicalTrace、原随机十条MP4/review及用户上传截图保留。

下一task为Kick Ball to Goal，QLM-DATA-023仅交付候选资产静态审核：A黑白拼片球（建议primary）、B橙色训练球/C蓝白拼片球（建议backups），共用真实门柱/横梁/后侧球网的实体训练球门。全部项目自建参数化几何；球直径20cm/0.40kg、球门净宽80cm/净高45cm/深40cm均为待批准候选参数，不是冻结pool或难度已验收。三模型compile和15路NativeEGL静态views通过，physics/controller/reference/formal均0；task注册仍planned。审核包workspace runs/audit/kick-asset-review-20261015-v1/review.html。

继续资产审核→物理资格及高质量reference/retarget范围审核→10pilot审核→100及最终验收；本轮停在候选资产审核，不跨gate。保持1primary+最多2backup、两背景/无clutter/无强制Recovery、原RAMBO/native9/时序/camera，未来本地普通3+3和swap launch增量7.6GiB/其余资源保护不变。QLM-DOC-007/v2DOC-020/v3DOC-019只做本轮验收清理及consumer治理；Push/Press/Lift task一次WAM资格复用，Kick的新资格留formal pilot。无WAM执行/cache/训练/AMD/commit/push或发布；原篮A asset包license unknown不改写。以下pending/旧并发仅为历史时点。

> 2026-10-15用户最新采用配置（QLM-DOC-006）：后续本地目标为[Native CPU physics／原RAMBO CPU＋EGL GPU rendering，4physics＋4render](decisions/local-synthesis-concurrency.md)，维持重叠流水线和原资源保护，替代旧本地3+3建议。以下CUDA/OSMesa baseline及旧launch叙述保留其实际历史身份；本次仅治理，不代表producer已完成切换或端到端准入。OSMesa跨平台reference与AMD路线保持，当前任务审核状态以task-synthesis-progress.md为准。

> 2026-10-15当前：Lift A的v2高层reference与八角点适用性工程交付完成，review在workspace runs/audit/lift-reference-20261015-v1/review.html；DATA020等待用户动作质量和范围审核，未开始10pilot/100，正式计数仍200/1000。前文资产pending/reference执行中保留各自历史时点。

> 2026-10-15最新：Lift资产已获批，用户指定A OASIS编织篮primary、B/C backups；SIM017被动Native/CUDA资格通过，DATA020原RAMBO reference/范围准备中，下一gate是reference审核，正式Lift仍0。旧asset-pending描述保留原时点。

> 2026-10-15最新：Push100与Press100均已获用户最终验收，累计200/1000；Press独立批准receipt在workspace runs/audit/press100-acceptance-20261015-v1/user-acceptance.json。下一task Lift Basket由QLM-DATA-020先交候选资产审核；本轮不执行reference/pilot。按资产→reference→10pilot→100及最终验收推进，双WAM每task一次。此前pending/0条/生产中段落保留原历史时点。

> 2026-10-15当前：Press100工程交付完成，随机十条review已交付；Push100已用户验收。早期pilot pending/生产运行中段落保持历史范围。

> 2026-10-15当前：用户已批准Press十条，QLM-DATA-019正以4physics+4render扩100，不重复WAM验证；完成后均匀随机10展示。下面待pilot审核状态保留历史时点。

> 2026-10-15当前：Press十条formal pilots工程交付完成，等待用户动作质量/覆盖/吞吐审核；Push100已验收。以task-synthesis-progress.md及QLM-DATA-018 active plan为当前事实，早期段落保留历史时点。

> 2026-10-15最新任务状态：Push100已验收；Press三资产、墙面Y/Z范围和press-body-carry-v2新reference均获用户批准。新recipe四角重验全部通过；QLM-DATA-018执行十条2Clean/8Randomized alltrain formal pilots，等待最终pilot审核后才100。双WAM仅本Press task一次兼容性。下面早期计划保持其历史范围。


> 2026-10-14最新任务状态：Push Box100已获用户验收；下一task为Press Button资产/reference准备，QLM-DATA-017。每task reference审核→10pilot审核→补100保持，当前Press formal=0。下面早期P2/10pilot状态保留其原历史时点；不得覆盖最新任务进度。

# QLM Scale-up v1 public foundation

当前 MuJoCo 生产规则见 [自动合成决定](decisions/automated-synthesis.md)。M0–M6只生成
Push Box10条pilot，2Clean/8Randomized全部train，无强制Recovery配额；新失败仅轻量日志。
以下80/20Normal/Recovery、失败全归档和旧slot工具描述保留原Isaac foundation范围，
不作为新 `synthesize-pilot` admission。旧P3资产已撤销，不恢复或计入本轮资源。

This QLM-only work does not change WAM branches or the historical shared-v2 registry. Work allocation is in `docs/scaleup-v1/work-registry.json`. Ten per-task plug-ins live in `src/qlm_bench/tasks/registrations/`; only existing Push/Lift/Press are ready. The seven new tasks remain planned and fail closed on collection. Each task owns its registration, spec, asset overlay registry and task/expert modules. Central recorder/profile/dispatcher changes are integrated by the parent task.

Use2..3 asset families per task, preserving original Push/Lift/Press assets and variants. Each task has100 accepted episodes,80/20 normal/recovery,20/80 clean/randomized and80/10/10 whole-episode splits. Ten formal pilot slots cover all assets with8 normal/2 recovery and2 clean/8 randomized. `qlm scaleup plan-slots` emits a reproducible draft; condition/preset IDs must be backed by frozen task manifests before collection. Existing demonstration references may fill matching slots; never duplicate source hashes or rewrite old releases.

Initial object visibility in either policy camera is sufficient. Partial FOV and nonzero historical initial velocity are accepted and are not rejection gates. Recovery requires real progress, meaningful deviation, actual correction and eventual success. Keep original controller/native9/force-zero and physical/camera/timestamp/terminal contracts. Fit no model normalizers or caches here.

Initial attempt plus3 retries means a01..a04 at one immutable slot. `SlotAttempts` logs every result; runtime/interruption errors get lightweight logs, task failure/timeout/fall gets local failure archives excluded from demonstrations. Exhaustion preserves available failure video and requests user attention. Retry must preserve slot quota/asset identity and frozen randomization bounds. Only success plus complete validation can be admitted.

The opt-in batch interface uses one Isaac process and a same-task scene batch, independent lane clocks/commands/expert state/terminal snapshots and original mounted RGB calibration. Current vector implementation is Press Button; other tasks implement `batch_environment`, `batch_expert` and the `BatchNative9Mixin` lane callbacks. `qlm collect-batch --probe-only` is an intentionally bounded capacity probe and produces no Raw/Canonical demonstration. Indexed `Recorder(env_index=...)`, `BatchRecorderMux` and pure `collect_wave` hooks are provided. Full accepted-slot Raw/Canonical production validation remains each task pilot gate; do not promote capacity probes as demonstrations.

Task-specific resource overlays live under `src/qlm_bench/assets/manifests/tasks/<task_id>/registry.json`. Entries use package-relative manifest paths and SHA256, and may not override historical asset IDs. Task converters are explicit plug-ins; the common conversion preserves the frozen columns and accepts an explicit `canonical_goal_position` for new tasks. Existing three converters/spec hashes are retained.

Runtime source selection uses the existing worktree-local `scripts/rambo/run60.sh`; do not rebind shared editable environments. `qlm scaleup bindings --source-root` verifies all three QLM/RAMBO/CRL2 import paths. `freeze-source` writes base commit, binary tracked patch, new-file archive and file hashes outside the checkout. `apply-source` only accepts a clean checkout at the exact base and verifies all hashes. This supports independent task branches without committing the foundation prematurely.

For task sessions: create a QLM-only worktree from the snapshot base, apply the foundation snapshot, use that worktree's run60.sh, and modify only task-owned files. Every run records the actual selected source. Keep outputs under the task's own versioned data directory; local failures belong outside the formal dataset. Existing workspace.env/venvs/controller/assets/WAM roots remain unchanged. No commit/push/HF publication is performed automatically.

## Task handoff ownership

`task-index.json` reserves QLM-DATA-001..010 in this QLM-only namespace and declares task branches/worktree directories/owned paths. Do not amend the historical shared-v2 registry. New ready task plug-ins provide their own task spec/hash, environment/config/expert/converter bindings and `configure_profile(cfg, profile, asset)` callback. Batch tasks additionally provide `batch_environment`, `batch_expert(env,index,time)`, task-state/review callbacks and per-lane success/reset handling. Existing spec-registry hashes are fallback historical identities; a task's new explicit spec/hash may be declared in its owned registration file.

For recording, construct one Recorder with its own lane index/output/observer, attach BatchRecorderMux at the environment-ready callback, then run collect_wave with explicit prepare_command and budget. Close/package each lane independently through its registered converter and validate before acceptance. Per-lane capture profiles must carry the actual `canonical_goal_position` and environment-origin provenance; never substitute env_0 state/goal/RGB for another lane. A same-process wave shares asset/appearance scene configuration; task-specific initial conditions/expert state must be assigned per lane before begin. Asset/preset groups can use separate queued waves/processes.

Use `scripts/rambo/run_scaleup.sh` to lease the GPU across task worktrees. The lease controls Isaac jobs, not lane count inside a job. It avoids concurrent full-memory jobs interfering; CPU development/validation continues independently. No safe cross-process concurrency was established by this same-process probe.

Call `runtime.prime_render()` after attaching render products and before beginning any recorder. It refreshes actual sensor buffers without physics advancement. Initial visibility is still task-specific; the priming heuristic is not an object-visibility certificate. `profile_for_lane` supplies the actual recorded canonical goal/origin for packaging.

Formal evaluation keeps the existing EvalCase structure. Each task defines a machine-checkable success condition before formal synthesis; numerical horizon/thresholds and environment/policy seeds freeze before formal evaluation. All policies/checkpoints for a task share frozen criteria. Timeout/fall/not-completed are policy failures in SR; explicit runtime/infrastructure errors are excluded, separately reported and rerun at the same slot/case/seed. Ten valid trials/task are required for a complete Standard evaluation. No formal evaluation runs or case-seed lists are created by this foundation.

## Capacity finding on2026-10-07

Press Button same-process probes use1280x720 dual RGB at50Hz, one1280x720 observer/lane sampled at25Hz, original controller and4 simulation seconds/200 commands per lane.2,3,4,5,6,8 and12 lanes run with actual final RGB.12 had two startup warmup frames before valid scene feedback; final-code probing adds explicit no-physics render priming.13/14 execute commands but produce sustained invalid near-uniform RGB;16 additionally reports RTX ERROR_OUT_OF_DEVICE_MEMORY. This establishes12 as the highest tested usable count for this short configuration, not a formal production acceptance or global theoretical limit. Use12 for the current Press configuration after task pilot checks; new heavier assets may need a smaller wave. Long episodes, live FFmpeg throughput and new task scenes remain task-level validation gates. Probe logs/images/data artifacts are intentionally removed by user instruction; only this compact finding remains.

Final-code12-lane recheck passed:200 commands/lane,24 policy cameras plus12 observers, sampled board peak13379MiB on a16303MiB device.13/14 retained near-uniform RGB throughout the short run;16 emitted explicit RTX device-memory allocation errors. Recommendation:12 for this Press configuration, with10/8 fallback if full recording or heavier assets require it. CPU checks:83 passed/1 dependency skip on public/data paths and22 passed on affected runtime/recorder/camera/ledger paths; docs/import/shared-governance checks pass. WAM v2/v3 refs and tracked source remain unchanged.
