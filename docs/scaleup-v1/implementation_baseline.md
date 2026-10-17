---
id: QLM-AUTOMATED-PUSH-BASELINE
type: guide
status: accepted
related_work: [QLM-DATA-011, QLM-DATA-026, QLM-DATA-027]
source_map:
  - src/qlm_bench/backends/mujoco/trace.py
  - src/qlm_bench/backends/mujoco/replay_recording.py
  - src/qlm_bench/backends/mujoco/template.py
  - src/qlm_bench/backends/mujoco/synthesis_queue.py
---

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

## Kick100最终用户验收；累计400，先发布HF — 2026-10-15

用户明确批准Kick100整task，独立receipt在workspace runs/audit/kick100-acceptance-20261015-v1/user-acceptance.json；原technical/attempt/随机抽样记录不改。Push100＋Press100＋Lift100＋Kick100=400/1000，四task均20Clean/80Randomized、80train/10validation/10test。Kick收尾完成，下一工作仅QLM-DATA-026发布现有400至dontKnow23456/QLM-Bench main，将完整原main保留为Isaac-based，其他task暂不启动。

HF实际private保持，现有dontKnow23456登录已具write权限，未要求新token；如实际授权不足按用户要求暂停。先materialized staging/完整性验证，再保存旧main及临时分支上传回读，最后精确HEAD保护切换main。原数据/source/asset/controller/camera/consumer身份不变；WAM v2DOC-023/v3DOC-022只治理，不复验已有每task资格、不新cache/fit/训练。当前尚未上传或改branch；实际进度看workspace runs/audit/mujoco400-hf-publication-20261015-v1/。无source GitHub commit/push、AMD或新task合成。以下pending仅历史。

## Kick100工程交付；随机十条等待最终验收 — 2026-10-15

QLM-DATA-025保留原已批准10条＋新90条，全100NativeCPU/原RAMBOCPU＋NativeEGL，80train/10validation/10test、各split20%Clean/80%Randomized，76950actions/77050boundaries。100物理身份唯一，跨split无近重复；相同批准4D ID支持，不分割变量范围/无OOD。原A primary、两背景、v3 recipe、ball XY±3cm/goal X±8cmY±5cm、原RAMBO/native9/500-100-50Hz/camera/实体goal正面整球入门/notfallen/三tick保持，无范围收缩、backup配额或成功physics重跑。

完整Raw/Canonical/媒体/50Hz boundaries/command/terminal/原telemetry逐列及完整snapshot球pose/速度/goal核对通过。task success与quality独立，准备球最大位移0.0000mm、其他robot碰球50Hz geometry合计0，零/未知FL contact不硬失败，不新增高频diagnostic永久存储要求。原十条完整payload/media/source字节身份保持；合并Canonical100与明确Raw/episode相对symlink视图在workspace data/qlm_bench/kick100-20261015-v1/，发布前需独立materialized staging。

普通3physics+3render已实际同时达到=True；available1GiB/launch-relative swap增长7.6GiB/紧急render-only回收0.5GiB/新render≥4GiB及pressure后render≤2保护保持，资源事件0。新增90pipeline 1712.9s≈189.15条/h（含准入/媒体验收/资源恢复，工程准备、最终合并和附加审核视角不含），不作稳态保证。实际政策/进程/失败与恢复见execution-policies和events。新physics尝试90、失败candidate0，不能用成功筛选收集作policy SR。

Kick task一次WAM v2DATA-019/v3DATA-009复用，未WAM执行/新模型cache/fit/训练；v2DOC-022/v3DOC-021仅治理。三Work工程交付后归档，用户对完整100最终验收仍pending。全100均匀无放回seed202610152510随机十条在workspace runs/audit/kick100-random-review-20261015-v1/review.html；不按quality/split/backend/原pilot筛选。宽视角仅人工诊断，不改变正式双640×36050FPS/Observer1280×72025FPS/模型输入语义。

原Push/Press/Lift300已获最终验收，Kick100现为工程交付，未提前计作用户最终验收400。public registration仍planned，不冒充public runtime全部ready。无其他task/AMD/commit/push/发布；OSMesa reference及AMD主线保持。以下pending/生产中仅描述原历史时点。

## 当前执行入口：剩余六task集中资产审核（QLM-DATA-027）

Push/Press/Lift/Kick共400已获最终用户验收，HF400由独立QLM-DATA-026及原监看收尾。剩余六task A/B/C共18候选已完成Native compile/mj_forward及72张NativeEGL静态图，全部六task overview与Room Door背面cam/bolt近景已实际检查；18模型resource identity、72图hash/尺寸及页面相对链接QA通过（workspace runs/audit/remaining-six-assets-20261015-v1/visual-qa.json），用户资产批准仍pending；physics/controller/reference/formal均0。来源、尺寸、质量、关节、摩擦、handle间隙及动态未验风险在workspace runs/audit/remaining-six-assets-20261015-v1/中显式记录。

沿用[最新批量流程决定](decisions/remaining-six-batch-approval.md)：全部资产批准后准备各task各一条reference/适用范围集中交审；整批六条reference/范围获批后才逐task直接100，取消六task十条pilot人工gate，保留task一次WAM最初Clean/Randomized工程准入和100随机十条最终验收。当前权威为[task进度](task-synthesis-progress.md)及[QLM-DATA-027](work/archive/QLM-DATA-027/plan.md)。原controller/native9/500-100-50Hz/camera/Raw/Canonical、本地NativeCPU/EGL3+3及现有内存保护不变。

## Lift100已获用户最终验收；下一task Kick先审资产 — 2026-10-15

用户明确批准本次手机静态审核并要求进入下一task。独立receipt在workspace runs/audit/lift100-acceptance-20261015-v1/user-acceptance.json，明确实际审阅为原随机十条中的067/099各三个真实时点，并非手机已观看十条动态视频。Push100＋Press100＋Lift100累计300/1000，三份原数据/technical/attempt/selection记录保持。手机派生GIF/JPEG/展示metadata共8文件16202281bytes已按批准清理；正式Raw/Canonical、PhysicalTrace、原随机十条MP4/review及用户上传截图保留。

下一task为Kick Ball to Goal，QLM-DATA-023仅交付候选资产静态审核：A黑白拼片球（建议primary）、B橙色训练球/C蓝白拼片球（建议backups），共用真实门柱/横梁/后侧球网的实体训练球门。全部项目自建参数化几何；球直径20cm/0.40kg、球门净宽80cm/净高45cm/深40cm均为待批准候选参数，不是冻结pool或难度已验收。三模型compile和15路NativeEGL静态views通过，physics/controller/reference/formal均0；task注册仍planned。审核包workspace runs/audit/kick-asset-review-20261015-v1/review.html。

继续资产审核→物理资格及高质量reference/retarget范围审核→10pilot审核→100及最终验收；本轮停在候选资产审核，不跨gate。保持1primary+最多2backup、两背景/无clutter/无强制Recovery、原RAMBO/native9/时序/camera，未来本地普通3+3和swap launch增量7.6GiB/其余资源保护不变。QLM-DOC-007/v2DOC-020/v3DOC-019只做本轮验收清理及consumer治理；Push/Press/Lift task一次WAM资格复用，Kick的新资格留formal pilot。无WAM执行/cache/训练/AMD/commit/push或发布；原篮A asset包license unknown不改写。以下pending/旧并发仅为历史时点。

> 2026-10-15用户最新采用配置（QLM-DOC-006）：后续本地目标为[Native CPU physics／原RAMBO CPU＋EGL GPU rendering，4physics＋4render](decisions/local-synthesis-concurrency.md)，维持重叠流水线和原资源保护，替代旧本地3+3建议。以下CUDA/OSMesa baseline及旧launch叙述保留其实际历史身份；本次仅治理，不代表producer已完成切换或端到端准入。OSMesa跨平台reference与AMD路线保持，当前任务审核状态以task-synthesis-progress.md为准。



> 2026-10-15当前：Lift A的v2高层reference与八角点适用性工程交付完成，review在workspace runs/audit/lift-reference-20261015-v1/review.html；DATA020等待用户动作质量和范围审核，未开始10pilot/100，正式计数仍200/1000。前文资产pending/reference执行中保留各自历史时点。

> 2026-10-15最新：Lift资产已获批，用户指定A OASIS编织篮primary、B/C backups；SIM017被动Native/CUDA资格通过，DATA020原RAMBO reference/范围准备中，下一gate是reference审核，正式Lift仍0。旧asset-pending描述保留原时点。

> 2026-10-15最新：Push100与Press100均已获用户最终验收，累计200/1000；Press独立批准receipt在workspace runs/audit/press100-acceptance-20261015-v1/user-acceptance.json。下一task Lift Basket由QLM-DATA-020先交候选资产审核；本轮不执行reference/pilot。按资产→reference→10pilot→100及最终验收推进，双WAM每task一次。此前pending/0条/生产中段落保留原历史时点。

> 当前入口已于2026-10-14收束为360p/50FPS，见 `mujoco-workspace.md`（本目录或decisions/current）。下方720p产物、旧profile-v4和未发布状态均描述其原历史阶段；旧720p frozen profile不直接用于新版代码。清理receipt记录已evict诊断payload，旧10pilot/reference仍保留待审核。

# M0–M6 Push Box 实施基线

## 本轮reference收束：四项完整通过，Oven范围未通过，Door待决策 — 2026-10-16

QLM-DATA-028当前有5个nominal物理成功candidate，只有4个task完成原范围工程验收：Fridge a04 16/16、Drawer a07/v5 16/16、Valve a07/v7 16/16、正前方Sweep a15 32/32。Sweep独立2physics/single-writer实际31.35min，244 sources保持，无资源/物理/infra失败；不是正式生产吞吐或policy SR。五份三视角视频在workspace runs/audit/remaining-six-reference-20261016-v1/review.html，Oven明确单列为范围未过的诊断candidate，页面不是整批完成/用户批准。

按用户将Oven放最后且不无限重试的要求，最后仅修高层阶段门控的一条a04真实29.28s关门成功，原RAMBO/资产阻尼/3°三tick判据保持。45°初态仍自然落90°后接触；FLhip参与支撑及27.6s单次较快转姿显式待人工审视。原16角点首2项均60s timeout，余14未执行，首次失败后停止派发并排空；source不变、不缩范围、不再调参。Oven因此不计工程就绪。详见pairs/fridge-oven/oven-final-structured-summary.json。

Room Door仍无合格reference，原controller近限位/gait和一次实际快速接近失败证据已汇总。降低handle及联动lock的新profile、独立controller评估或暂缓Door三项已集中询问用户；答复前不改asset/controller或继续physics，推荐项不等于授权。决定待办为同审计目录pending-door-route-decision.json。

当前全部reference physics/writer已停止，QLM-SIM-020/DATA028、v2DOC025/v3DOC024保持active等待关键决定与整批审核。原已验收400、18原候选资源、原RAMBO source/checkpoint、相机/action/state契约保持；新formal0，不WAM模型/cache/训练/AMD/commit/push/发布。最终随机十条人工验收延后至所有task合成完成后统一，不恢复10pilot人工gate。以下进行中/待范围的叙述仅描述历史快照。

源分支 migration/mujoco-foundation 起点4cf1c643922ff1f479577f98d06c9e75518acc63；
WAM adaptation/v3-mujoco-sft 起点02939d121b127352a4a6178acb26e3ca30a5007d。
基于本地干净 worktrees 和已验收 Box05/default LOD a02，不恢复已撤销 P3 的资产或代码。
复用原 runtime/controller/physics/task predicate、Native mirror、VideoSink 与 Canonical exporter。

## 冻结范围

首轮同一 Box05、原 Go2/FL/native9/controller、force-zero、24s horizon；
goal 保持0.4m×0.5m矩形，full-footprint/not-fallen/three50Hz-tick判据不变。
随机化为物体X±4cm、Y±2cm、yaw±0.03rad、goal X±3cm/Y±2cm的小范围ID变化。
具体候选预先序列化完整初态、goal、seed与resource identity，不根据失败降为容易条件。
三套floor颜色preset为小幅外观变体，physics/camera/material摩擦均保持；源pack不可变。

工程reference由原nominal expert实际完成：444actions、8.88s，FL接触26个boundary且
无body-object接触。固定template提取commanded FL/world目标和measured base path；
阶段是settle/base approach/normal approach/straight push。执行时使用有界base/yaw反馈、
phase几何先决条件、固定操作progression与goal行程缩放，不逐candidate生成新脚本。
reference和调参开发数据不进入正式pilot quota。三项预定开发配置均实际成功。

## 生产入口与恢复

`qlm synthesize-pilot --profile FROZEN_JSON --output NEW_BATCH --checkpoint RAMBO`
使用显式资源/源码/template hash。首轮只允许10个Push slots，2Clean/8Randomized全部train。
最新profile在workspace `runs/audit/automated-push-synthesis-20261013-v1/pilot-profile-v4.json`。
Randomized目标边框四个contact-free geoms与数值goal共同冻结；仅修改视觉goal位置，
相机/机器人/物体collision和物理参数保持。两条nominal Clean保持原goal和原有效trace。
新versioned数据在workspace `data/qlm_bench/automated-push-pilot-20261013-v1/`。
一次冻结batch保存源码hash清单，不按episode复制source tree。

无渲染physics trace保留50Hz边界、100Hzcontroller和500Hzphysics/contact telemetry。
成功trace原子提交，失败只写轻量JSONL。Native OSMesa worker从完整snapshot离线出图，
不加载controller/WAM，不重新执行physics。源data与离线RGB的来源明确记录。
正式pilot必须task成功、complete interval、FL接触/无body操作、媒体/Raw/Canonical验证。

Queue单写入者使用文件lease；复用同model的已加载physics runtime；成功trace待录制时
阻止下一physics candidate，背压上限一条。每slot≤5候选、全pilot≤30、连续失败10条停止；
录制失败最多再试2次，复用同trace。restart验证trace及accepted inventory，幂等计数。
首轮采用单world和单render worker，容量优化不得先于per-world隔离验收。

## M6实际交付 — 2026-10-14

10条正式pilot（2Clean/8Randomized全部train）技术验收通过，用户审核待完成。
合计4540actions/4550boundaries，30路原始720p视频、10份三视角预览及完整串联均保留。
原资源/模型不变，Randomized goal视觉边框与数值区域一致；不恢复旧P3资产。
14physical attempts包括10成功、3timeout、1受控工程中断；11render attempts包括
10成功和一次受控中断恢复。成功trace未重跑physics，失败只轻量JSONL留档。

独立三tick footprint/not-fallen、去重hash、逐条/合并Raw/Canonical与实际LeRobot
逐episode首末RGB/native9读取通过。Clean01和Randomized03的原frozen VAE/10D
实际读取通过，latent1x48x28x24x20、state109x10；原weights/config hash匹配。
十条contact/terminal视图已检查，完整边界同姿态Native几何审计仅FL与箱子接触，
不代替CUDA实际力telemetry。未拟合normalizer或训练。

成功stage成本约35.05min、17.12accepted/hour；含失败/工程中断的实测batch约52.51min、
11.43accepted/hour。平均33.29MB/episode；组合worker RSS约8.08GB、GPU board峰值1417MiB。
不作为完整1000条生产容量或正式evaluation SR。已停在10条审核点。

## 验收与当前事实

参考离线Raw/Canonical和实际原frozen VAE/10D readback已通过。
固定模板开发配置443/462/457actions，三项成功。CPU回归14通过、5个显式runtime
fixture门槛skip；实际CUDA/OSMesa gates另记录。初次独立CUDA rollout逐bit比较出现
约4e-5速度差异，未放宽门槛；改在同一authoritative snapshot比较数值观测路径，并
核验physics/controller/RNG/clock零变化及双mirror图像逐byte一致，实际gate通过。

运行事实、failed轻量日志与milestone报告在对应audit层。M6完成后提交实际视频、
10条数据验收和吞吐/内存/磁盘成本，等待用户审核，不进入M7/其他任务/训练/发布。

最终诊断提取修正：settle段world目标从真实projected-COM转换推导，操作路径和fixed executor AST未改变。
实际pilot沿用template-development-v1身份，corrected display为template-display-v2，最终源码/profile可幂等恢复已accepted队列。
