---
id: QLM-DATA-028
type: exec-plan
status: active
source_map: []
---

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

# Remaining-six original-RAMBO high-quality references and retarget scopes; batch human review before any100

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

## 最新用户调整 — 2026-10-16

Oven以约45°初始开度重试（约−π/4），记录reset、准备、接触时的真实门角；
Room Door以更远本体站位执行先抬高、再前伸搭顶、下压真实把手后推门。
这是用户明确授权的initial-state/高层路线变更，不授权改物理参数、controller或成功条件。
旧失败、原成功reference与scope证据全部保留；新方案另存版本并完成真实reference及范围验证。
六条仍集中交用户审核，未批准前formal0。

后续最终随机十条人工验收延后至所有task合成完成后统一进行；每task全量工程检查和每task一次WAM准入仍保留，
不新增十条pilot人工gate。原四task400已获验收保持。决定receipt为本审计目录`user-reference-retry-decision.json`。
以下旧快照只描述各自历史时点。

## 最新执行证据：45°重试与Door顶接触路径 — 2026-10-16

Fridge a04、Drawer a07/v5、Valve a07/v7的nominal和完整16角点均已完成工程检查。
Drawer保留9个严格nonFL0与7个短暂Head brush的原始分类；独立实际500Hz姿态/摩擦几何界
证明后者不能直接提供正向开抽屉力，工程动作质量可交人工审核，不把strict flag回写为True。
Root已检查Fridge/Valve实际操作及terminal画面；三条集中审核视频复用现有同timestamp媒体合成，
不重跑physics，不新增模型验证。

Sweep a10 nominal18.76s真实成功，完整媒体已验收；v8完整32为30成功2timeout，
v10后续016/018仍timeout，另一个已进入派发的001成功排空后暂停，不能称范围通过。
下一高层tracking修复保留原完整范围/goal/predicate/controller，失败记录完整保留。

Oven用户45°profile只改变initial q与对应metadata，原物理/视觉model参数保持。
真实无接触启动0.28s已落至约88°；fixed-ready探针首次接触在0.18s约60°，
原RAMBO固有前1s FL stance将初始高FL姿态拉回地面，尚非合格reference。
不静默修改startup clock/history、增锁或辅助力；下一分支只尝试原自然startup后的真实托举。
Room Door更远站位的raw-world native9抬足探针A02实际整球净空≥3mm连续16ticks(320ms)，
比预声明10ticks门槛长；只是准备动作通过，前伸/顶部接触/真实lever-cam-bolt/push仍待验证。
raw-world命令保留原core内部IK/limits/history，去除的是先前reference额外的预投影，非修改原controller。

当前4个nominal candidates、3个完整范围通过，六条整批human批准pending，formal0。
当前机器可读快照为`reference-progress.json`；旧快照与所有原成功/失败证据不回写。

用户已批准六task A primary/B-C backups；保留approved18候选原geometry/mass/friction/articulation与全部旧400/旧source。先真实物理资格，再原RAMBO/native9 reference，六条及适用范围集中交审；未批准整批reference前不任何100，无10pilot人工gate。原500/100/50Hz、双640x36050FPS/Observer720p25FPS、force-zero、task success/quality分离、两背景/无clutter/无强制Recovery、NativeCPU/EGL3+3和1GiB/7.6GiB/0.5GiB/4GiB资源保护保持。新task数字目标在reference profile声明为待用户整批审核的新predicate，旧四task不修改；不能用teleport、weld、隐形锁/辅助力制造reference。被动初始速度诊断独立标记，不作demo。失败轻日志，成功trace保留；WAM task一次兼容留正式production，不运行WAM/cache/fit/训练/AMD。HF400由独立DATA026/monitor继续，禁止第二写者。W&B not_run/local-only。

- [x] 固定18 approved资源/原controller/old400/source身份及实际attempt记录。
- [x] 完成18资产Native机制检查及18/18 CUDA集成/reset/完整timestamp镜像；Oven C真实floor stop限制独立保留，不宣称全部hinge端点通过。
- [ ] 六task各一条实际原RAMBO高质量reference、任务专属成功证据与独立动作质量。
- [ ] 各task预声明retarget范围、两背景、完整边界真实复验，不按失败静默缩范围。
- [ ] 双正式RGB/Observer/terminal与集中审核页；数据/formal0，不跨用户gate。

## 实际阶段快照 — 2026-10-16

workspace `runs/audit/remaining-six-reference-20261016-v1/reference-progress.json`
记录当前四条真实成功candidate（Fridge a04、Drawer a05、Valve a06、正前方Sweep a05），
四份trace manifest身份及12段原双RGB/Observer媒体完整验收通过。
Fridge完整16角点16/16实际成功且非FL接触0；Sweep相对初态v2只执行7/32，
2成功5timeout后有据暂停，不能宣称范围通过。Drawer/Valve范围尚未执行。
Oven与Room Door仍处于高层站位/接触路径开发，无合格reference；
这些诊断不改变原controller/资产物理参数，也不计formal数据。
整个六task reference与范围仍须集中交用户审核，未跨生产gate。

物理资格的准确边界见同审计目录 `physical-qualification-summary.json`：
Native机制证据与CUDA两world集成证据分开；被动探针不是原RAMBO成功。
Oven C仅按实际floor stop限定的close操作记录，未到完整-90deg hinge端点，
backup无配额，不阻塞A primary的reference开发。HF400已在独立QLM-DATA-026完成，
monitor已暂停，不再处于上传中。


## Sweep工作区改为正前方 — 2026-10-16

用户指出旧Sweep reference处在侧前方，明确要求方块和goal在机器狗正前方地面。新versioned profile为workspace assets/mujoco/sweep-front-approved-20261016-v1/：block[.75,+.15]、goal[.75,-.15]，工作区中心[.75,0]在robot纵轴前方，base从后方站至[.30,0]附近，不随横拨沿Y走到目标侧面。原30cm横拨距离、方块/zone尺寸、geometry/mass/friction、full-footprint/notfallen/三tick、原controller/native9/时序/camera不变。用户纠正receipt见workspace runs/audit/remaining-six-reference-20261016-v1/sweep-front-layout-decision.json。

旧Sweep a01成功trace/媒体只保留历史，不作当前交审reference，旧5D scope未执行且已superseded；新front reference/适用范围必须真实重验，不复用旧成功冒充通过。其余五task继续。原资产几何批准保持，sidecar/布局新closure明确，不回写旧资源、scope或receipts。

## 后续实际进展：四candidate、两task完整范围 — 2026-10-16

`reference-progress.json`已更新为Fridge a04、Drawer a07、Valve a07、正前方Sweep a07，
四份trace身份及12段原camera完整媒体均核对通过，human动作质量整批批准仍pending。
Fridge16/16保持；Valve v7在相同完整16/seed/双背景上16/16真实成功且独立quality检查通过，
旧v6的10成功6失败不改写。Sweep新完整32、Drawer新完整16仍在执行，未提前计作通过；
Oven/Room Door无合格reference，formal0保持。

原reference专用runner硬编码ap00导致部分scope trace标签与实际ap01模型不符，
实际floor/物理/source身份不变，成功physics和原trace不重跑/回写；
各pair追加独立model/resource→真实appearance说明。另存metadata-only v2 runner及scope入口，
81个真实模型的正/负标签核对及显式metadata归一化后control/physics AST等价通过，
旧shared三文件SHA不变；证据`appearance-runner-v2-admission.json`。
后续新Sweep32使用新入口，已完成/活动旧scope不更换source。

正式producer的goal metadata、appearance字段、public task集成、每新task一次WAM兼容及后续AMD资格
见`formal-admission-open-items.json`，不能把reference工程证据冒充formal Raw/Canonical或AMD验收。

## 用户要求两条失败三视角视频 — 2026-10-16

用户明确要求查看Close Oven Door与Open Room Door失败demonstration三视角视频。
旧失败只有轻量日志，没有完整50Hz snapshots，不能插值或伪造成旧视频。
授权范围内对Oven A26-h60、Door A11各做一次原source/recipe/seed/model/初态/时长的真实复现，
独立诊断collector保存完整失败状态与真实False/timeout terminal，独立schema明确永不进入formal，
再同timestamp离线render，不改变success predicate或原collector/validator。
这是仅两次指定失败视频的留存例外，不升级其他失败或正式demo的高频存储要求。
成功physics不重跑，普通3physics/3render及内存保护保持；原失败与全部旧source不回写。

该子任务已完成：Oven A26复现3000actions/3001真实50Hz snapshots、Door A11复现
2400/2401；原诊断采样及真实timeout终态完全一致。独立失败schema保留False/非formal，
原成功trace准入明确拒收。原Observer/Ego/Task及额外前侧视角全部同timestamp镜像、零physics推进；
审核合成明确选偶数50Hz boundary形成同步25FPS，原双RGB50FPS未改。
两份三视角视频及原Observer版本在workspace
`runs/audit/remaining-six-failure-videos-20261016-v1/review.html`，
验收见`delivery.json`与`source-and-clock-closeout.json`；均已在会话提供，
app浏览器打开请求为queued，不冒充用户已观看/审核。
此交付不改变六reference/范围的pending状态，也不授权formal100。


## Room Door已按用户要求暂停 — 2026-10-16

用户明确暂停Open Room Door后续尝试，只要求查看最近失败的三视角视频。当前Door physics/scope进程0，最后实际失败为QLM-DATA-029 SmallA16（22.74s侧触拒收/notfallen），没有A17，scope实际0。不得继续候选开发、physics或scope，等待用户下一步指令；其他reference/原400保持。receipt见workspace runs/audit/door-lowered-reference-20261016-v1/user-pause-decision.json。可仅用已保存127个真实qpos时点制作明确标注的5Hz为主稀疏诊断回放，不插值、不补跑physics，不冒充完整50Hz失败trace。下方“继续开发”只描述原历史状态。


## Door三次尝试完成；采用实际锁扣退出判据 — 2026-10-16

用户已取消固定20mm退栓门槛，采用实际锁舌实体退出锁扣口的历史event；开门后的回弹不撤销解锁，15deg/notfallen/三50Hz tick和原RAMBO/资产/physics/camera保持。QLM-DATA-030及decisions/door-geometric-unlock.md为新权威，旧20mm判据只保留历史。三次A17/A18/A19已全部结束并保留完整50Hz诊断状态、三视角视频。按新规则离线复核A18在24.86s、A19在24.40s通过，A17未达到15deg；原执行结果/terminal不回写，不冒充按新规则实时终止的正式数据。

前三次全部失败才追加第四次的条件不成立，因此无第四次、无scope/100扩量，当前0physics/scope，停止等待用户审核。审核workspace runs/audit/door-user-three-attempts-20261016-v1/review.html；动作质量及reference完整范围仍待审。原400/其他references/Oven停止保持，无WAM/cache/训练/AMD/commit/push/发布。下方旧暂停/20mm/进行中段落为历史。


## 六task reference与范围已集中交审；历史失败产物已清理 — 2026-10-16

QLM-DATA-033完成Door16/16与Oven16/16全部实际角点验收，原RAMBO/已批准动作/物理/成功判据保持；所有episode在首次满足条件的完整50Hz边界结束，50Hz实际记录无非FL正受力接触。Door18.56–23.46s，Oven17.38–19.64s。Oven初始开度25–35deg为待此次集中确认的新范围提案，保留原10deg宽度并符合35deg限位；XY±2cm/yaw±5deg保持。

原四项复用：Sweep32/32、Fridge16/16、Valve16/16、Drawer16/16；六项集中审核workspace runs/audit/remaining-six-final-scope-20261016-v1/review.html。范围均为primary A，B/C资格不从A结果自动推定。Door A19与Oven35deg中央nominal已获批准，本轮整批reference/范围最终确认pending，新增formal0/原400保持。

按用户明确要求，历史失败/被拒/未采纳Door/Oven中间产物先文字归档后清理809文件、约3.13GiB逻辑大小；硬链接原因不冒充实际回收空间。原文字记录/source hashes保持；1278个受保护二进制逐文件hash复核，合格reference、当前范围、已批准资产及其他任务完整。删除receipt和文字汇总同审计目录。无后续physics/scope/100/WAM/cache/训练/AMD/commit/push/发布；停止等待用户整批确认。以下历史pending/运行中仅保留原时点。

