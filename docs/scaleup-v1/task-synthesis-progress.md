---
id: QLM-TASK-SYNTHESIS-PROGRESS
type: current
status: accepted
related_work: [QLM-DOC-005, QLM-DATA-020, QLM-DATA-021, QLM-SIM-018, QLM-DOC-006, QLM-DATA-026, QLM-DATA-027]
source_map: []
---

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

## 当前reference重试与最终审核安排 — 2026-10-16

用户已批准Oven改为约45°初始开度；Door改用更远本体站位，先抬足、再前伸搭顶、下压真实handle机构后推门。两者以新版本reference/范围验证，旧失败和成功证据不改。六条集中审核前不开始100。

最终随机十条人工验收延后到所有task合成完成后统一；每task100条全量工程验收、每task一次WAM兼容、原抽样口径仍保留，原四task400验收不重做。用户决定见workspace runs/audit/remaining-six-reference-20261016-v1/user-reference-retry-decision.json。该安排覆盖下方历史逐task人工终审时点。

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

## 用户已采用本地Native CPU＋EGL 4+4 — 2026-10-15

QLM-DOC-006记录用户明确选择：后续本地Native CPU physics／原RAMBO CPU＋EGL GPU rendering，4physics＋4render，替代先前3+3建议；继续重叠流水线与原资源保护。唯一来源为[本地合成配置](decisions/local-synthesis-concurrency.md)。OSMesa跨平台reference、AMD路线和既有数据身份保持。本轮仅治理，不表示producer接入、视觉等价或完整生产验收已完成，也不替代Lift十条用户审核；以下旧默认属于历史阶段。





独立QLM-SIM-018已完成各路线单轮3+3/4+4/条件5+5并清理本次全部测试产物；后续仅保留[本地并发建议](decisions/local-synthesis-concurrency.md)。此诊断不计正式数据，不改变以下Lift pilot待审核状态。

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


# MuJoCo任务数据合成当前状态

## 本轮reference收束：四项完整通过，Oven范围未通过，Door待决策 — 2026-10-16

QLM-DATA-028当前有5个nominal物理成功candidate，只有4个task完成原范围工程验收：Fridge a04 16/16、Drawer a07/v5 16/16、Valve a07/v7 16/16、正前方Sweep a15 32/32。Sweep独立2physics/single-writer实际31.35min，244 sources保持，无资源/物理/infra失败；不是正式生产吞吐或policy SR。五份三视角视频在workspace runs/audit/remaining-six-reference-20261016-v1/review.html，Oven明确单列为范围未过的诊断candidate，页面不是整批完成/用户批准。

按用户将Oven放最后且不无限重试的要求，最后仅修高层阶段门控的一条a04真实29.28s关门成功，原RAMBO/资产阻尼/3°三tick判据保持。45°初态仍自然落90°后接触；FLhip参与支撑及27.6s单次较快转姿显式待人工审视。原16角点首2项均60s timeout，余14未执行，首次失败后停止派发并排空；source不变、不缩范围、不再调参。Oven因此不计工程就绪。详见pairs/fridge-oven/oven-final-structured-summary.json。

Room Door仍无合格reference，原controller近限位/gait和一次实际快速接近失败证据已汇总。降低handle及联动lock的新profile、独立controller评估或暂缓Door三项已集中询问用户；答复前不改asset/controller或继续physics，推荐项不等于授权。决定待办为同审计目录pending-door-route-decision.json。

当前全部reference physics/writer已停止，QLM-SIM-020/DATA028、v2DOC025/v3DOC024保持active等待关键决定与整批审核。原已验收400、18原候选资源、原RAMBO source/checkpoint、相机/action/state契约保持；新formal0，不WAM模型/cache/训练/AMD/commit/push/发布。最终随机十条人工验收延后至所有task合成完成后统一，不恢复10pilot人工gate。以下进行中/待范围的叙述仅描述历史快照。

用户2026-10-15已批准Press随机10条并明确验收Press Button100；独立批准receipt在workspace `runs/audit/press100-acceptance-20261015-v1/user-acceptance.json`。Press原技术交付 `runs/audit/press-scale100-20261015-v1/completion.json`及随机样本seed202610151910保持。Push批准记录继续在 `runs/audit/push100-acceptance-20261014-v1/user-acceptance.json`。

| task | 当前资格 | formal accepted | 当前下一步 |
|---|---|---:|---|
| Push Box | 用户最终验收；本地Raw/Canonical/媒体交付完整 | 100 | 保留，等待完整十任务release |
| Press Button | 三资产/墙面范围/reference/10pilot及整task100均获用户批准；技术交付完整 | 100 | 保留，等待完整十任务release |
| Lift Basket | 资产/reference/范围/10pilot及完整100均获用户批准；技术交付完整 | 100 | 保留原数据与随机十条审核包，等待完整十任务release |
| Kick Ball to Goal | 完整100已获用户最终验收 | 100 | [QLM-DATA-026](work/archive/QLM-DATA-026/plan.md)；原10＋新90，当前先发布四task400至HF |
| Sweep Block to Zone | A/B/C候选已compile/零step静态出图；动态物理/reference未执行，用户资产批准pending | 0 | [QLM-DATA-027](work/archive/QLM-DATA-027/plan.md)；全部资产批准后集中交审六reference/范围；整批批准后才逐task100 |
| Close Fridge Door | A/B/C候选已compile/零step静态出图；动态物理/reference未执行，用户资产批准pending | 0 | [QLM-DATA-027](work/archive/QLM-DATA-027/plan.md)；全部资产批准后集中交审六reference/范围；整批批准后才逐task100 |
| Close Oven Door | A/B/C候选已compile/零step静态出图；动态物理/reference未执行，用户资产批准pending | 0 | [QLM-DATA-027](work/archive/QLM-DATA-027/plan.md)；全部资产批准后集中交审六reference/范围；整批批准后才逐task100 |
| Turn Valve | A/B/C候选已compile/零step静态出图；动态物理/reference未执行，用户资产批准pending | 0 | [QLM-DATA-027](work/archive/QLM-DATA-027/plan.md)；全部资产批准后集中交审六reference/范围；整批批准后才逐task100 |
| Pull Open Drawer | A/B/C候选已compile/零step静态出图；动态物理/reference未执行，用户资产批准pending | 0 | [QLM-DATA-027](work/archive/QLM-DATA-027/plan.md)；全部资产批准后集中交审六reference/范围；整批批准后才逐task100 |
| Open Room Door | A/B/C候选已compile/零step静态出图；动态物理/reference未执行，用户资产批准pending | 0 | [QLM-DATA-027](work/archive/QLM-DATA-027/plan.md)；全部资产批准后集中交审六reference/范围；整批批准后才逐task100 |

当前已获用户最终验收400/1000：合计80Clean/320Randomized、320train/40validation/40test；四task各100。保留原Push/Press/Lift/Kick数据、来源、technical/attempt及用户批准receipt。HF400发布由独立[QLM-DATA-026](work/archive/QLM-DATA-026/plan.md)收尾，本页不将上传状态提前表述为完成。六个新task正式数据均为0，18候选/72静态图不计demonstration quota。

## 审核顺序：剩余六task采用最新批量流程

1. 六task的全部A/B/C候选资产集中交用户审核，最多1primary＋2backup，展示来源/许可/尺寸/质量/关节/contact结构和实际未验证项；当前停在该gate。候选审批不能替代物理资格。
2. 六task整批资产批准后，进行各task真实Native/CUDA接触和机构验收；每task准备一条高质量真实reference及retarget适用范围，六条集中交用户审核。backup登记实际资格，不制造使用配额。
3. 这整批六条reference及范围获用户批准后，才按task顺序直接合成100条；单条reference获批不启动100。每task20Clean/80Randomized、80train/10validation/10test，各split20%/80%；取消这六task的10pilot人工审核。最初合格Clean＋Randomized作为每task一次WAM v2/v3实际工程准入并计入100，不能省略接口验证。
4. 每task100完成后进行全量Raw/Canonical、物理/独立quality/媒体/command/timestamp/terminal与split去重验收，全100均匀无放回随机十条交用户最终整task审核。不得按失败收缩已批准分布、强分几何变量区间或加入OOD。

新流程权威为[剩余六task批量审批决定](decisions/remaining-six-batch-approval.md)。原Push/Press/Lift/Kick曾完成的10pilot审核与全部历史receipt保持，不被新流程改写。

保留原native9/force-zero/RAMBO、500/100/50Hz、dualRGB640×36050FPS/Observer1280×72025FPS、LOD a02、两个Background/无clutter/无强制Recovery。本地NativeCPU/RAMBOCPU＋EGL普通3physics＋3render及1GiB/7.6GiB launch-relative swap/0.5GiB render-only回收/新render≥4GiB保护保持；OSMesa reference与AMD优先ROCm主线不变。PhysicalTrace必须保留原Raw/Canonical、50Hz boundaries、必要实际snapshot/完整command/terminal，不新增全体500/100Hz telemetry长期保存要求；task success与动作quality分开，零/未知FL contact不硬失败。

当前四task已有的WAM task一次资格复用，六新task尚未运行WAM资格、未生成模型cache；本资产包不训练/AMD/source commit/push或发布。最终图片QA已通过，用户资产批准仍pending。

## 历史阶段记录（以下pending/0条仅描述其原时点）

## 最新用户执行顺序修正

用户随后要求“先让我确认候选的虚拟资产”。当前先提交Press的A/B/C视觉/尺寸/来源/状态；primary和backup尚未由用户选择。资产审核前不继续reference执行/调试；此前完成的1条nominal实际CUDA诊断和离线capture不计formal、不构成用户批准。候选B/C只有真实源资源与静态MuJoCo外观预览，没有MuJoCo physics资格；B与A同几何仅cap颜色不同，不假称第三种机构。正式10条与100条均为0。

## 最新资产审批与环境决定

A/B/C均已获用户批准，A为primary、B/C为backups；MuJoCo physics资格仍须实测，不能把审批当通过。Press新增完整墙，位置随机化改为平面Y/Z、固定X安装深度。QLM-SIM-016负责三资产新profile和物理验收；QLM-DATA-017继续wall reference与适用范围。asset gate已解除，reference review仍pending，Press formal=0。

## 实际工程交付完成

A/B/C各自Native/CUDA静止、真实接触按压/回弹、正常/高速wall collision、有限行程、zero-step selected-lane reset、其他world不变与完整articulation镜像通过。三个原RAMBO/native9 nominal实际成功：A/B各501actions10.02s，C571actions11.42s；cap终态分别15.086/15.084/14.294mm，原predicate通过、无跌倒。旧Source pack/robotbody/joint/camera/solver逐字段保护检查通过，无额外equality constraints或辅助操作力。

主资产A墙面Y0.10±0.03/Z0.30±0.02m四个预声明角点全部成功，ap_00/ap_01非visual参数逐字节一致；range proposals仍等待用户审核。21路原始媒体/7个三视角preview/独立慢放及完整snapshot review交付，主资产/四角点other-geom-cap/wall/housing均0；C仅1个FL-housing边缘接触，非机身操作，不改task outcome。

QLM回归沙箱147pass/12skip、4socket权限失败；同四项host复核4pass，合计151pass/12skip。Docs/shared治理/import/compile/原资源保护通过。首轮wall stress guard失败及source-compliance分析保留；未改solver。七个真实task trace源码逐hash保存165个去重blob，原model_2000与旧Push100/receipt保持。

当前Press默认模型切换为新full-wall A resource pin，LOD a02保持；旧显式model/历史cases不改写或冒充新scene资格。无formal pilot/100、WAM模型验证、训练、AMD、commit/push或发布。本SIM技术资格完成并归档，QLM-DATA-017保持active等待reference动作质量与适用范围用户审核。证据与review见workspace runs/audit/press-wall-qualification-20261014-v1/。

## 2026-10-15：资产/墙面范围通过，旧reference动作质量未通过

用户明确批准墙面Y/Z随机化与三资产，冻结y0.10±0.03/z0.30±0.02m、固定normal深度与现有ap_00/ap_01；没有批准旧reference动作。用户指出推进中操作腿肘部大幅抖动，授权修复并重新实际生成一条reference。formal Press仍0，不进入10pilot/100。

旧trace离线分析：推进段FL hip roll实际范围约92.85deg，原IK reference最大10ms跳变13.65deg，实际最大10ms跳变8.59deg，底座vx近零切换31次。肘部横向摆动与此一致；需检查原IK workspace敏感性、world目标/body姿态及高层启停耦合，不能靠视频平滑掩盖真实执行。

当前工作在同一QLM-DATA-017中继续，审计根workspace runs/audit/press-reference-smoothing-20261015-v1/。新版本high-level executor采用低位body-relative收腿推进，先稳定底座，再缓慢伸向按钮；原native9接口保持，通过原IK/FK只读几何限制reference变化和可达空间，不改RAMBO内部history/checkpoint/PD/QP/IK算法、physics/camera/task predicate或已批准资产/范围。最多先3个明确recipe开发attempt，每次24s-or-terminal；失败轻量结果，成功trace可独立render retry。若必须改变原controller再集中报告，不以重新训练为默认。

验收：相同seed42/model/predicate下实际success/not-fallen、complete commands/terminal；对比推进段真实FL hip/thigh/calf与IK/desired角度波动、变化速度及末端轨迹，不用任务成功代替质量。完整OSMesa原始50FPS双RGB/Observer25FPS和原/新三视角对照交用户再次审阅。新recipe必须在正式pilot前针对已批准范围重新验证，批准范围不撤回、不偷偷缩小。WAM task-once检查仍not_run，不生成验证cache，不做训练/AMD/commit/push/发布。

## 2026-10-15实际reference修复交付

资产与墙面Y/Z范围已批准，旧reference动作质量未通过。成功的新reference-a02真实697actions/698boundaries、13.94s、终态cap18.572mm，原12mm/三个50Hz ticks/not-fallen判据通过，33个FL-cap boundary、其他geom-cap/wall/housing0。仅改high-level native9轨迹：低位body-relative收腿推进、平滑base速度、有界横向误差补偿、稳定后缓慢伸腿按压与几何reference slew；原RAMBO checkpoint、IK/PD/QP/history、physics/camera/资产/范围均未改。

推进段实际FL hip roll摆幅92.846→4.878deg(下降94.75%)，最大10ms跳变8.588→0.752deg(下降91.24%)；IK最大10ms跳变13.654→0.687deg。导致肘部横向大摆的主因改善，原gait的小幅thigh/calf波动仍在；完整三关节指标/曲线公开，不宣称所有关节振动消失。原/新推进video均1×实际速度，仅短段终帧padding；完整三视角preview未做动作动画平滑，原双RGB50FPS/Observer25FPS经过现有full media validator，Native mirror不推进physics。

第一次新recipe在base横向约2cm稳态误差下24s timeout/no fall，轻量日志/source保留，无失败完整trace/媒体；第二次加入高层Y积分和0.2s反馈平滑后成功。未换seed、移资产或缩范围。15项受影响CPU/geometry/quality checks通过，docs/import/shared治理及controller/旧evidence保护通过。

新审核包workspace runs/audit/press-reference-smoothing-20261015-v1/review.html。QLM-DATA-017保持active，只等待新reference动作质量审核；已批准的Y/Z范围不重问。new recipe在正式pilot前须重验该范围，然后进入10pilot审核；当前formal Press=0，未执行WAM/训练/AMD/commit/push/发布。

## 新reference已批准，formal pilot准备 — 2026-10-15

用户批准新reference；QLM-DATA-017归档，QLM-DATA-018重验新recipe的既定四角范围后交付10formal pilots。当前Press0，pilot审核后才扩100。v2 DATA-017/v3 DATA-007记录本task一次真实compatibility，原Push task证据不重做。

## Press十条formal pilots技术交付，等待用户质量审核 — 2026-10-15

新reference及三资产/wallY/Z范围已获批准；新recipe四角重验4/4通过。QLM-DATA-018完成10条新真实primary A trajectories(2Clean/8Randomized alltrain)，6735actions/6745boundaries；10次首次物理执行均成功，零body-button contact，无范围收缩或backup配额。原RAMBO/native9/500-100-50Hz/真实12mm三tick/not-fallen/camera/360p50FPS保持，Native OSMesa mirror不推进physics。完整Raw/Canonical、实际articulation snapshot、terminal/原telemetry逐列、媒体与唯一身份检查通过。推进FL hip摆幅4.60–5.66deg，最大10ms1.127deg；保留原gait小波动，task success与动作质量分开。

v2 DATA-017/v3 DATA-007完成Press各一次实际Clean+Randomized Reader/原VAE/SFT-input/online/caches回读与v3实际10D，Press instruction embedding匹配；两模型works归档。今后同task扩100不重复WAM验证。2physics+2render/最多4积压，实际pipeline 1054.0s≈34.2条/h，RAM最低10.79GiB，无swap增长/资源guard；task一次WAM与最后渲染并行，此吞吐非稳定生产保证。

审核入口workspace runs/audit/press-formal-pilots-20261015-v1/review.html、report.md；data/qlm_bench/press-approved-pilot-20261015-v1/。QLM-DATA-018保持active等待指定十条动作质量/覆盖/吞吐用户审核，未批准前不100/其他task。Push100用户验收及原reference/asset qualification/receipts/source heads保持。无正式训练/AMD/commit/push/HF或发布。

## Press十条获批，授权4physics+4render扩100 — 2026-10-15

用户明确批准Press全部十条，保留并计入100；QLM-DATA-018归档、新QLM-DATA-019补90条，最终80/10/10与20Clean/80Randomized。沿用冻结press-body-carry-v2/primary工业红/wallY/Z范围/两背景/原RAMBO/native9/500-100-50Hz/360p50FPS和真实predicate。独立4physics+4render，保留backpressure/RAM/swap保护与实际launch epoch记录；资源不足时排空并有据安全续跑，不改采样分布。WAM v2/v3 Press task已一次验收，不重复验证或新cache；v2 DOC-016/v3 DOC-015仅治理。完成100后固定seed均匀无放回随机10展示。当前生产尚未完成，不提前宣称100已交付；原pilot pending receipt保留历史，新批准receipt在runs/audit/press-scale100-20261015-v1/。无其他task/训练/AMD/commit/push/发布。

## Press100首次4+4触发resource保护 — 2026-10-15

4physics+4render已实际重叠执行。第一个8-candidate wave中，在4render启动/4physics在途期间swap新增超过512MiB，调度器自动停止新physics并排空；已完成数据和成功trace保留，无候选/recipe/物理/相机调整。当前等待最后媒体排空，随后按既有resource-safe分支3physics+2render续完100，必要时有据降低启动容量。实际政策/资源采样分别在execution-policies/和resources.jsonl；不把原冻结campaign目标4+4冒充持续实际设置。无WAM重复检查/模型cache/训练/AMD。

## Press Button100本地交付与随机十条review — 2026-10-15

QLM-DATA-019完成已批准十条＋新90条，共100，train80(16Clean64Randomized)/validation10(2+8)/test10(2+8)，66903actions/67003boundaries。100物理身份唯一，跨split无近重复；同一批准ID支持，没有变量区间分割/OOD。primary工业红/full wall/fixed X/YZ范围/两背景/press-body-carry-v2/原RAMBO/native9/500-100-50Hz/360p50FPS/predicate保持。成功Trace独立NativeOSMesa，不推进physics；全部Raw/Canonical/media/terminal/原telemetry逐列验收与Canonical100合并通过。Raw100 view显式相对symlink原不可变bytes，发布前需独立materialized staging。

用户指定4physics+4render已实际重叠；首8条触发swap新增512MiB保护后停止新派发并排空，保留全部成功trace/数据。后续resource-safe实际launch政策见execution-policies，源码/recipe/config保持冻结；不把初始4+4计划冒充全程实际设置。新增90条实际queue2.08h≈43.3条/h，含保护和续跑等待，非稳态保证。新physics尝试91、失败1；成功筛选数据收集不作为policy SR。

WAM v2/v3 Press once-per-task receipt复用，本批没有Reader/VAE/T5/SFT-input/online复验、模型验证cache、fit/训练或权重修改；v2 DOC-016/v3 DOC-015仅治理归档。QLM-DATA-019也归档，工程交付完成；用户对最终100整task验收等待随机十条review。审核：runs/audit/press100-random-review-20261015-v1/review.html(全100均匀无放回，seed202610151910，无quality/split筛选)。主报告runs/audit/press-scale100-20261015-v1/；data/qlm_bench/press100-20261015-v1/。Push100原验收、Press reference/pilot/source heads/原models保持。其他tasks、训练、AMD、commit/push/发布未执行。
