---
id: QLM-MUJOCO-PROGRESS
type: current
status: accepted
related_work: [QLM-DOC-001, QLM-SIM-013, QLM-DOC-006, QLM-DATA-026, QLM-DATA-027]
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

## DATA039修订范围交付：Close Fridge Door 16/16；Close Oven Door 16/16；Turn Valve 16/16 — 2026-10-16

Fridge A04已获用户批准；Oven1kg/4s与Valve6s reference批准保持。本轮实际执行48项、工程验收48/48，逐项失败/not_run保留。范围共同XY±2cm/yaw±5deg；Fridge45–55（50±5，宽度不缩）、Oven25–35、Valve0–5，两背景各8；原recipe/RAMBO/成功条件/相机/seed42保持，nominal未重跑。

集中审核workspace runs/audit/revised-three-scope-20261016-v1/review.html，结构化reference-scope-catalog.json包含全部source、实际首次接触角及非FL/FL非足端接触观察。每task代表范围视频按最大非FL力、FL非足端力、成功时长依次选取，不是正式随机审核。初始范围与实际接触角分开，不冒充全过程同角度分布。NativeCPU范围证据，不宣称CUDA/ROCm已复测。

所有physics/render已结束；DATA039保持active等待用户集中确认，工程验收与动作质量批准分开。原400和其他批准保持，无新formal/100/WAM/cache/训练/AMD/commit/push/发布。108个原source及checkpoint/三repo HEAD保持。

## DATA039进行中：Fridge A04批准，三项修订范围待集中确认

用户已明确批准Fridge A04合格reference，DATA038已归档。当前仅执行Fridge/Oven/Valve修订后各16个角点，Fridge45–55deg、Oven25–35deg、Valve0–5deg，共同XY±2cm/yaw±5deg和两背景各8；范围宽度不因结果缩小。实际进度以workspace runs/audit/revised-three-scope-20261016-v1/scope-result.json为准，当前不能宣称全48通过。完成后集中获批nominal视频、全部范围结果及按接触问题/时长选出的代表scope视频供审核，不重跑nominal、不100。

## Fridge A04交付：50deg与实际门面持续跟随 — 2026-10-16

QLM-DATA-038本轮仅一条A04，27.96s按原3deg/三tick/notfallen成功；55→50deg只在reset前改变hinge初态，原model/资产物理/camera/原RAMBO保持。6.04s主前伸，11.40s抵门，之后足端body参考从45.48持续延伸到54cm（+8.52cm），机身推进29.48cm，不再冻结首次接触长度。原伸展上限到达后由机身配合。

50Hz实际FL足端正受力31次、FLcalf3次、非FL0；最后FL接触27.94s距终止0.02s。ego足端中心入画约91.1%、整球73.8%，实际中段/末段图已看，不宣称全程无遮挡或500Hz连续接触。1398commands/1399boundaries/初态差异/及时终止/source和700帧三视角验证通过，任务成功不替代动作质量审核。

当前审核workspace runs/audit/fridge-door-follow-20261016-v1/review.html；DATA038 active等待用户视频审核，未标合格reference。所有physics/render结束，无额外尝试/scope/100/WAM/cache/训练/AMD/commit/push/发布。旧A02/A03失败或质量不足记录、原400/其他task批准保持。

## Fridge A03视频交付；物理成功但ego/头部接触仍需修订 — 2026-10-16

Sweep A09已按用户确认登记合格reference，原31/32范围和032失败保留，不再运行Sweep。本轮QLM-DATA-037有补充前A02一次（40s timeout）及补充后far-stop-v2/A03唯一一次；两份真实source/结果保持，不隐藏或回写。

A03在38.14s达到原3deg/三tick/notfallen。5.38s远停稳后主抬升前伸，10.70s真实抵门；之后body足端目标固定[.4526,.15,-.08]，机身前进39.42cm。54cm仅目标上限，实际接触即冻结45.26cm，不能宣称达到54cm。最后FL正受力接触37.74s/门角−4.86deg，终止38.14s。ego足端中心仅约10.6%边界在画内、整球0%；11个50Hz边界存在Head_upper/lower接触（最大47.87N），不计合格reference/不准入SFT，task success保持真实。

完整1907commands/1908boundaries/原predicate及时终止/source及同timestamp三视角通过。审计workspace runs/audit/fridge-body-advance-reference-20261016-v1/review.html、report.md；原RAMBO/资产/相机/时序和400保持。全部physics/render结束，等待用户审视频，不追加尝试/scope/100/WAM/cache/训练/AMD/commit/push/发布。DATA037保持active等待质量审核，静态预览通过不代表动态可见性通过。

## Sweep A09审核确认；Fridge仅一次机身推门修订 — 2026-10-16

用户已确认Sweep审核通过，A09为合格reference；原31/32范围结果及032超时保留，不回写成全32成功。Fridge原动作需改为早抬高前伸，实际足端接触门后保持前伸姿态，以机身前进推至关闭；“早停”不再作为该动作意图。QLM-DATA-037仅一次真实尝试及三视角视频，原RAMBO/physics/camera/native9/判据保持。审计workspace runs/audit/fridge-body-advance-reference-20261016-v1/。失败亦交视频后停止；不额外尝试/scope/100/WAM/cache/训练/AMD/commit/push/发布，原400/其他批准保持。

## DATA036结果：Sweep 31/32；Oven/Valve reference批准 — 2026-10-16

完整原范围验收 31/32；尚未通过，停止原因 physical_failure，未执行0个。 用户取消小拨/侧移顺序门槛，原task success和完整工程证据为准，动作/接触诊断不独立拒收。22.5cm及原32范围/两背景/seed42/40s/原RAMBO与camera不变，无缩域或seed选择。

旧Work035成功3条保留实际身份复用；Work036实际新physics30次，成功28、失败2，007原超时不回写。十条成功前缀证明不受新增6s实际几何出口影响，不重跑成功physics。最终逐条source见workspace runs/audit/sweep-task-success-scope-20261016-v1/final-report.json，审核入口同目录review.html。旧035顺序拒收只是历史。

Close Oven Door与Turn Valve合格nominal reference用户批准已登记，Fridge仍待审核；Oven/Valve修订后完整scope未在036执行。原400、Drawer/Door与108原source/三repo HEAD保持。全部在途排空，暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布。

## Scope035未通过并已排空；A09 nominal批准保持，三reference待审 — 2026-10-16

QLM-DATA-035保留原5D32角点（blockXY±2cm/yaw±5°/goal方向±4°、22.5cm中心距离±2cm，两背景各16）不缩域。首轮4/32仅1 task success但无获批序列资格，28未执行；补geometry-retarget-v1后3/32虽3 task success，均未执行first stroke/侧移，序列合格0、29未执行。共7次两个版本的scope物理运行，不合并冒充32点通过；首失败停止新派发并排空，当前0physics。

已量化共同原因：操作段机身Y误差最高8.6–10.6cm，稳定足端侧触与机身停稳从未同时成立；准备阶段却追随block继续推进，导致任务成功但批准动作顺序未执行。需要加强操作期机身保持并使接触准备有界，可能影响nominal实际动作，因此本轮不继续修改获批A09，不放宽门控/成功条件或缩范围。几何retarget在零扰动下保持A09且0physics，旧task结果/trace不回写；旧“可选阶段出现才校验”不足已由独立序列复核明确纠正。

当前报告workspace runs/audit/sweep-a09-scope-20261016-v1/review.html及final-report.json。A09 nominal reference用户批准保持，完整范围验收未完成，DATA035保持active；DATA034保留其余三项动作审核。Fridge/Oven/Valve修订三视角集中页workspace runs/audit/four-reference-refinement-20261016-v1/fridge-oven-valve-revised-review.html，均复用原媒体、hash和链接通过，用户动作批准仍pending。原400/Drawer/Door/原RAMBO及source保持。暂不100/新formal/WAM/cache/训练/AMD/commit/push/发布。

## Sweep A09单次成功，分阶段顺序通过；等待动作审核 — 2026-10-16

QLM-DATA-034仅实际一条A09，32.86s达到原完整footprint/notfallen/三tick，1643commands/1644boundaries并首次成功即终止。原进场/积分恢复，机身保持实际8.82s进入操作才启用；19.24s实际稳定足端侧触并小拨约6cm，21.74s确认原goal未满足后右侧移，25.10s再次稳定接触后最终拨动。接触及首次小拨前无计划goalward机身侧移。原RAMBO/成功判据/22.5cm资产布局与其余v8参数保持。

50Hz实际正受力接触仅FL_foot91次观测，FLcalf/机身0；足端横向顺序未反转，最小间隔+5.56cm，但肘部/支撑腿全程动作质量仍待用户视频审核，不替代该审核。workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a09-review.html；a09-completion.json、a09-sequence-audit.json及a09-report.md为当前证据。optional几何distance探测标记inconclusive，不用它作验收结论。

一次授权已用完，physics/render/监测结束，等待用户审核，无追加试跑/完整scope/100。旧30cm范围不证明22.5cm新reference范围通过；未自动计合格reference。旧A07/A08 payload/media与108源文件保持。Drawer/Door已批准、Fridge/Oven/Valve修订待审、原400保持；不WAM/cache/训练/AMD/commit/push/发布。下方A09启动及A08失败为历史。

## Sweep A08单次已结束：进场门控实现问题，未进入操作 — 2026-10-16

QLM-DATA-034按用户只一条要求执行A08，40s timeout/notfallen。实际仅settle/carry/approach_base，无FL/robot碰块、无稳定侧触/小拨动/右侧移，不能据此判断用户分阶段策略失败。本次expert把Y保持过早用于进场（cap2cm/s并清除recipe lateral integral），原1.5cm进场门控未收敛；终态Y误差约5.34cm。原RAMBO/内部history/physics/成功判据没有改动；不追加第二条，不计合格reference。

用户明确授权的距离30→22.5cm已通过独立profile实现：blockY.15→.075，goal位置/尺寸保持，A/B/C物理及camera参数不变。旧scope不能代表新布局。视频workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a08-review.html（完整40s/1001帧），a08-completion.json、a08-report.md和a08-actual-evidence.json为当前证据。4个零步mock阶段门控检查不等于真实流程验收。全部physics/render结束并停止等待用户反馈，无scope/100/WAM/cache/训练/AMD/发布；原400/其他reference保持。下方A08授权仅为启动前历史。

## Sweep A07一次重试完成，40s未成功；等待视频审核 — 2026-10-16

QLM-DATA-034按用户仅一次授权完成A07：40s timeout、未跌倒，未满足原完整footprint进区成功判据。身体终态goal方向移动32.6cm（A06为8.4cm）；全部50Hz采样足端横向顺序未反转，最小FL减FR bodyY间隔+12cm，但不能替代完整动作质量审核或task success。提前横移后lower阶段较久、后段足端抬高，方块未完整进区；不追加第二条，不计合格reference。

三视角workspace runs/audit/four-reference-refinement-20261016-v1/sweep-a07-review.html，原速40s/1001帧，同timestamp实际snapshot且无physics重跑；a07-completion.json、a07-comparison.json及a07-report.md为本次权威。原RAMBO/成功判据/接触路径/资产/camera/seed42/40s保持；只改高层身体跟随与其朝向参考点。完整2000commands/2001boundaries/source及独立原predicate检查通过。仅这一条，physics/render结束，等待用户视频反馈；未scope/100/WAM/cache/训练/AMD/发布。Fridge/Oven/Valve待审、Drawer/Door已批准、原400保持。下方A07授权/停止点为历史。

## Sweep失败视频已交付；四项修订停止新增尝试等反馈 — 2026-10-16

QLM-DATA-034已完成真实Fridge/Oven/Valve首轮，分别16.76/15.62/12.72s达到原task success，按2/4/6s提前操作；Oven新compiled门体1kg/35deg，Sweep新goal仅边框。Drawer与Room Door的reference/范围已获用户批准，原材料保持不复跑。原400保持，新增formal0。

Sweep五条失败（a01–a05，其中a03为heading实现缺陷）已完整生成三视角，workspace runs/audit/four-reference-refinement-20261016-v1/sweep-failure-review.html。用户要求先看失败视频后，原在途a06结束于33.52s task success，但实际FL/FR足端横向顺序曾反转约61mm且仍有FLcalf接触，末段交叉风险未排除，不计合格reference、不宣称动作已解决。全部physics/render现已结束，不再追加尝试，等用户视频反馈。

四项当前材料workspace runs/audit/four-reference-refinement-20261016-v1/review.html；三项动作质量仍待用户审核，Sweep仍需处理质量风险；四项新scope均未重验，旧范围只代表旧recipe/旧质量。Oven1kg新profile不借用旧1.8kg的CUDA资格。原RAMBO/IK/PD/QP/history/native9/500-100-50Hz/camera/成功判据及三repo HEAD保持。无100/WAM/cache/训练/AMD/commit/push/发布；普通3+3与原资源阈值保持。下方进行中/四项旧范围通过等仅为历史版本。

## 当前权威：四项reference用户修订（QLM-DATA-034）

用户已批准Drawer和Room Door的reference/范围；Sweep被拒绝，Fridge/Valve/Oven需修订。当前执行QLM-DATA-034的四条新nominal与视频审核，不自动扩100。Oven改1kg/4s，Fridge2s，Valve6s；Sweep远起点、身体/FL协同与边框goal。四项旧scope仅代表旧recipe/旧质量，新版本范围须重验；原RAMBO/成功判据/接口保持。最新证据workspace runs/audit/four-reference-refinement-20261016-v1/，本WAM配对仅治理，不执行WAM/cache/训练/AMD。下方进行中/整批待审等只描述各历史时点。

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

## Kick十条formal pilots工程交付；等待用户审核 — 2026-10-15

用户已批准v3 reference与完整ball XY±3cm/goal X±8cm Y±5cm范围。QLM-DATA-023归档，QLM-DATA-024完成全新2Clean8Randomized/alltrain十条，7832actions/7842boundaries、十个唯一物理身份；10次physics、0失败candidate。A primary、两背景、原recipe/controller/IK/PD/QP/history/physics/asset参数/native9/500-100-50Hz/camera保持，没有范围收缩、backup配额或成功physics重跑。formal新增十条仍待用户审核，最终已验收计数仍300/1000。

完整Raw/Canonical/媒体/50Hz action-state/完整command确认/terminal/原telemetry逐列、实际snapshot pose/速度/goal及独立正面整球入门/notfallen/三tick审计通过。准备阶段球最大位移0.0000mm；FL接触1–6个50Hz boundary，其他robot碰球0；最后FL接触后自由滚动2.42–4.44s。task success与quality分开，未知contact不硬失败，不新增高频diagnostic永久存储要求。

NativeCPU/RAMBOCPU＋NativeEGL真实同时3+3=True，1GiB暂停physics/7.6GiB launch-relative swap排空/0.5GiB仅render回收/新render至少4GiB及pressure排空保持。正式pipeline 215.2s≈167.29条/h（包含正式媒体验收，不含工程准备、WAM资格和附加审核出图），不作稳态保证。双RGB640×36050FPS/原Observer1280×72025FPS保持；同timestamp完整snapshot镜像不推进physics。宽视角仅人工看清球路/goal，不属于policy或formal Observer。

v2DATA-019/v3DATA-009各一次Kick Clean01＋Randomized04实际Reader/原VAE/SFT-input/online/cache回读、正确Kick prompt及v3实际10D通过并归档，原三task未复验、不fit/训练，同Kick扩100不再复验。public registration仍planned；当前仅显式MuJoCo profile正式数据链路通过，不声称public runtime全部ready。

审核workspace runs/audit/kick-formal-pilots-20261015-v1/review.html、report.md；合并Canonical及明确Raw相对symlink视图workspace data/qlm_bench/kick-approved-pilot-20261015-v1/（发布前需materialized staging）。QLM-DATA-024保持active等待十条动作质量/覆盖/吞吐审核，未授权100。原Push/Press/Lift300、source heads/资产/模型/环境锁保持。无其他task/AMD/commit/push/发布。以下pending只保留原历史时点。

## Kick reference与范围工程交付；等待用户审核 — 2026-10-15

已批准A primary/B-C backups及实体球门；QLM-SIM-019的Native/CUDA三资产各7项被动物理、真实接触/reset/mirror均通过。新Kick判据为正面整球入实体goal/notfallen/三50Hz ticks，旧三task判据和action/state/Raw/Canonical接口保持；public task注册仍planned，未冒充formal production ready。

QLM-DATA-023交付推荐kick-impulse-retract-v3-tucked-carry reference：原RAMBO NativeCPU真实16.22s、811actions/812boundaries，pre-strike球位移0，FL接触仅strike阶段3个50Hz boundary，之后自由滚动4.22s入门；原gait小幅波动保留。三个nominal开发成功trace全部保留，未训练或改controller/IK/PD/QP/history/asset mass-friction。

v2首轮范围11/16、5timeouts保留；只将高层carried FL目标X .23→.16后，对相同seed42、相同完整16角点和两背景重新真实执行，v3为16/16，全部pre-strike位移0，50Hz snapshot未发现其他robot部位碰球。范围提案ball X/Y±3cm、goal X±8cm/Y±5cm，仍待用户批准；未按结果收缩或搜索seed，不宣称全连续状态或policySR。两轮对应model resource identity逐点相同，16点球/goal都可由原policy相机观察。

审核workspace runs/audit/kick-reference-20261015-v1/review.html与report.md，宽视角画面只用于人工诊断，原Ego/Task/Observer、dual360p50FPS和Observer720p25FPS保持；所有图像导入真实同timestamp snapshot，不独立推进physics。DATA023保持active，等待reference动作质量与范围审核；未批准前不10pilot/100，formal Kick0，原Push/Press/Lift300/1000已验收保持。Kick task一次WAM资格留pilot，v2DOC-021/v3DOC-020仅治理，无WAM执行/cache/训练/AMD/commit/push/发布。后续本地普通3+3/swap增量7.6GiB及原保护保持。以下旧pending只保留历史时点。

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

## 用户已采用本地Native CPU＋EGL 4+4 — 2026-10-15

QLM-DOC-006记录用户明确选择：后续本地Native CPU physics／原RAMBO CPU＋EGL GPU rendering，4physics＋4render，替代先前3+3建议；继续重叠流水线与原资源保护。唯一来源为[本地合成配置](decisions/local-synthesis-concurrency.md)。OSMesa跨平台reference、AMD路线和既有数据身份保持。本轮仅治理，不表示producer接入、视觉等价或完整生产验收已完成，也不替代Lift十条用户审核；以下旧默认属于历史阶段。




## Lift Basket十条formal pilots交付；等待用户审核 — 2026-10-15

QLM-DATA-021完成全新10条2Clean/8Randomized、全部train，7506actions/7516boundaries，十个唯一物理身份；十次首次physics均成功，无范围收缩、backup配额或成功physics重跑。原A OASIS主资产、lift-body-lane-geometry-v2、dx/dy±3cm/yaw±5deg、两Background、原RAMBO/native9/force-zero、500/100/50Hz、整篮最低点20mm/notfallen/三tick保持。Clean为真实小幅几何变化，非同初态重复。

完整Raw/Canonical、50Hz boundaries/commands/terminal、原telemetry逐列与全部媒体检查通过，合并Canonical在workspace data/qlm_bench/lift-approved-pilot-20261015-v1/canonical。双RGB640×36050FPS/Observer1280×72025FPS，独立NativeOSMesa mirror不推进physics。十条完整穿孔后托举；实际CUDA50Hz snapshots在Native重建接触几何，FL腿部27–38个boundary、base合计0，不是独立CUDA force telemetry，sphere-only接触0不硬失败。task success与demonstration quality分开，不新增全体500/100Hz诊断永久保留要求。

v2 DATA-018/v3 DATA-008各一次实际Clean01+Randomized04 Reader/原VAE/SFT-input/online/cache及正确Lift prompt通过并归档，后续同task扩量不重复模型验证/cache，不fit或训练。QLM-DATA-021保持active，十条动作质量/覆盖/吞吐用户审核pending；工程交付不等于用户批准或policy success rate。

初始4+4尝试未同时达到，保留旧保护事件与一个render-only回收/同trace恢复。续跑实际1physics+2render，采用用户更新的1GiB available/6GiB launch-relative swap增长/0.5GiB render回收，未打断执行中的worker。用户当时确定后续新launch默认3+3并行流水线，不采用分阶段模式；3+3稳定性不因配置决定而被宣称通过。实际总pipeline 3895.2s≈9.24条/h，含保护排空与续跑，不是稳态保证。

审核workspace runs/audit/lift-formal-pilots-20261015-v1/review.html、report.md；完整receipt/资源policy/质量证据同目录。Push100+Press100仍为人工最终验收200/1000，Lift十条等待审核。A资产包license unknown保持，仅本地，无扩100、训练、AMD、commit/push或发布。下方pending/旧配置只描述各自原阶段。

> 2026-10-15当前：Lift A的v2高层reference与八角点适用性工程交付完成，review在workspace runs/audit/lift-reference-20261015-v1/review.html；DATA020等待用户动作质量和范围审核，未开始10pilot/100，正式计数仍200/1000。前文资产pending/reference执行中保留各自历史时点。

> 2026-10-15最新：Push100与Press100均已获用户最终验收，累计200/1000；Press独立批准receipt在workspace runs/audit/press100-acceptance-20261015-v1/user-acceptance.json。下一task Lift Basket由QLM-DATA-020先交候选资产审核；本轮不执行reference/pilot。按资产→reference→10pilot→100及最终验收推进，双WAM每task一次。此前pending/0条/生产中段落保留原历史时点。

> 2026-10-14最新任务状态：Push Box100已获用户验收；下一task为Press Button资产/reference准备，QLM-DATA-017。每task reference审核→10pilot审核→补100保持，当前Press formal=0。下面早期P2/10pilot状态保留其原历史时点；不得覆盖最新任务进度。


## P0–P2 source publication — QLM-DOC-002 / 2026-10-13

The user now authorizes this P0–P2 source batch on the independent MuJoCo branch.
The publication records supersede earlier local-uncommitted wording for this
batch only. Initial implementation and closing-documentation commits are verified
through exact remote readback in workspace
`runs/audit/mujoco-p0-p2-source-publication-20261013-v1/`.
Initial source publication passed exact remote readback. Read final closing-documentation
heads from that receipt. P6 still freezes the final
ten-task/source/resource/admin bundle; this batch is not that later release.

> 当前入口已于2026-10-14收束为360p/50FPS，见 `mujoco-workspace.md`（本目录或decisions/current）。下方720p产物、旧profile-v4和未发布状态均描述其原历史阶段；旧720p frozen profile不直接用于新版代码。清理receipt记录已evict诊断payload，旧10pilot/reference仍保留待审核。

# MuJoCo 整体进度与阶段交接

## 本轮reference收束：四项完整通过，Oven范围未通过，Door待决策 — 2026-10-16

QLM-DATA-028当前有5个nominal物理成功candidate，只有4个task完成原范围工程验收：Fridge a04 16/16、Drawer a07/v5 16/16、Valve a07/v7 16/16、正前方Sweep a15 32/32。Sweep独立2physics/single-writer实际31.35min，244 sources保持，无资源/物理/infra失败；不是正式生产吞吐或policy SR。五份三视角视频在workspace runs/audit/remaining-six-reference-20261016-v1/review.html，Oven明确单列为范围未过的诊断candidate，页面不是整批完成/用户批准。

按用户将Oven放最后且不无限重试的要求，最后仅修高层阶段门控的一条a04真实29.28s关门成功，原RAMBO/资产阻尼/3°三tick判据保持。45°初态仍自然落90°后接触；FLhip参与支撑及27.6s单次较快转姿显式待人工审视。原16角点首2项均60s timeout，余14未执行，首次失败后停止派发并排空；source不变、不缩范围、不再调参。Oven因此不计工程就绪。详见pairs/fridge-oven/oven-final-structured-summary.json。

Room Door仍无合格reference，原controller近限位/gait和一次实际快速接近失败证据已汇总。降低handle及联动lock的新profile、独立controller评估或暂缓Door三项已集中询问用户；答复前不改asset/controller或继续physics，推荐项不等于授权。决定待办为同审计目录pending-door-route-decision.json。

当前全部reference physics/writer已停止，QLM-SIM-020/DATA028、v2DOC025/v3DOC024保持active等待关键决定与整批审核。原已验收400、18原候选资源、原RAMBO source/checkpoint、相机/action/state契约保持；新formal0，不WAM模型/cache/训练/AMD/commit/push/发布。最终随机十条人工验收延后至所有task合成完成后统一，不恢复10pilot人工gate。以下进行中/待范围的叙述仅描述历史快照。

当前更新：旧 P3 实现及新增资产已按用户要求撤销。用户现在授权
[QLM-DATA-011 自动生产 M0–M6](decisions/automated-synthesis.md)，从保留的 Push Box
资源出发，交付2 Clean/8 Randomized共10条正式 pilot后审核。取消强制 Recovery 配额；
批量无逐条 GPT，成功 physics trace 再离线录制。后文旧 P3 候选/进行中描述保留发布时范围，
不作为当前资源或执行入口。P0–P2完成和独立源码发布保留。

核对日期：2026-10-13（Australia/Sydney）。P0–P2 **本地工程验收已完成**。
旧P3实现及其新增候选资产已按用户要求撤销。当前推进 QLM-DATA-011 M0–M6，
已交付 Push Box10条正式pilot（2Clean/8Randomized全部train）供审核；不恢复旧P3资产。

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
| P3 | 部分完成；300/1000用户验收 | Push/Press/Lift各100已验收；Kick候选资产静态审核pending，其他六task尚未实施；不恢复撤销资产 |
| P4 | 首批pilot交付，批量待审核 | 当前10条Push pilot（2Clean/8Randomized、全部train）；1000条20/80、800/100/100与100个Standard EvalCases仍为后续gate，不再强制Normal/Recovery比例 |
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
三次完整 horizon 的观察不构成正式 SR 或 Macro SR。此0/1000计数保留P2时点；
2026-10-14新自动路线已交付10条独立pilot，用户审核待完成，release未发布。

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
  reference/template，再做正式 pilot。新路线不要求Recovery配额。新增七任务各10条合格 pilot 计入最终100条，旧三任务也须正式资格验收。
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

## 2026-10-16 四项reference修订进行中

Drawer/Room Door已获reference与范围批准。QLM-DATA-034修订Sweep身体/FL协同、远站位和goal边框，Fridge2s、Valve6s、Oven1kg/4s更远前伸；先交新nominal视频，四项旧范围只保留旧版本证据，不冒充新版本通过。新增formal0；原400保持，不WAM/cache/训练/AMD/发布。证据workspace runs/audit/four-reference-refinement-20261016-v1/。
