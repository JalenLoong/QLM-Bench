---
id: QLM-REMAINING-SIX-BATCH-APPROVAL
type: decision
status: accepted
related_work: [QLM-DATA-027, QLM-SIM-020, QLM-DATA-028]
source_map: []
---

## 当前交接：三项范围已批准，正式400/1000，剩余600待生产 — 2026-10-16

用户明确批准DATA039 Fridge/Oven/Valve三项修订范围，实际48/48工程通过；独立receipt为workspace runs/audit/revised-three-scope-20261016-v1/user-scope-approval.json，DATA039配对归档。六task当前资产/reference人工审核均已完成，Drawer/Door既有批准、Sweep A09批准保持；Sweep历史31/32及032失败不回写。

当前Push/Press/Lift/Kick各100，共400正式已验收并完成private HF400发布；剩余六task正式0/600，scope/reference不自动计入100。生产公共接入尚未完成：六registration仍planned、公共rendition仍限制旧四task、Door须用几何退栓v3适配，不能直接复用含旧20mm逻辑的generic helper。新会话需阅读交接后先与用户对齐，等下一条开工指令；本轮不生产。

当前权威交接：docs/scaleup-v1/handoffs/remaining-six-production-20261016.md（QLM MuJoCo repo）；完整绑定和可复制prompt在workspace runs/audit/remaining-six-handoff-20261016-v1/。未来沿用直接每task100，无10pilot人工gate；每task一次WAM兼容与全量工程检查，最终每task随机十条人工验收延后到六task全部完成。3+3/1GiB/7.6GiB/0.5GiB/4GiB政策保持。旧pending/旧角度/旧20mm/旧10pilot段落均是历史，不恢复已完成审批。

# 剩余六task：资产、reference与合成审核流程

## 用户调整：Oven最后处理，禁止无限重试 — 2026-10-16

优先完成Fridge/Drawer/Valve/Sweep/Room Door的reference与范围；Close Oven Door放最后。用户允许最终无法完成时直接报告失败，不以无限重复试跑追求表面完成。当前Oven a03已排空：60s timeout/notfallen、终态约−83.39°，无新physics派发。现有hinge damping=0.09、frictionloss=0.025、stiffness=0，实际45°初态仍快速自然落平；不能将用户推测写成“铰链完全无阻尼”，也不据此擅自修改物理参数/controller。原失败、成功source及trace保持。决定receipt为workspace runs/audit/remaining-six-reference-20261016-v1/user-oven-last-decision.json。六task集中review与formal0保持，最终随机十条人工审核仍延后至所有task合成结束。

## 当前有效决定 — 2026-10-16

全部18资产已获批准，各task A primary、B/C backups；当前QLM-DATA-028继续六条reference及其适用范围集中交审。
用户观看Oven/Door失败复现后明确更新：Oven初始开度改为约45°（门板与地面约45°，当前铰链约−π/4）；
Room Door采用更远本体站位、先抬足高于handle、再前伸搭在上方、下压真实lever/cam/bolt后前推开门。
仅初始状态和高层操作路线获得本轮变更授权；原controller/IK/PD/history、physics参数、camera和成功条件保持。
必须记录Oven从reset至接触的真实门角，不能用持续写qpos、虚拟锁、辅助力或未批准spring/friction维持初态。

六条reference/范围全部获得用户批准后，仍逐task直接合成100，不设十条pilot人工审核。
每task的100条全量工程检查仍在该task完成时进行；最终随机十条人工验收统一延后到所有task合成完成后。
抽样口径继续沿用原每task全100均匀无放回抽10，不把单task人工验收作为进入下一task的前置。
原已验收四task400保持，不重新制造已完成的审批；剩余六task在全部完成后集中交审。
新task一次WAM v2/v3兼容仍在最早合格Clean＋Randomized生产准入执行并计入100，同task后续不重复。
本轮尚未解除六reference整批审批gate，不启动100、训练、AMD或发布。

当前实际依据见workspace `runs/audit/remaining-six-reference-20261016-v1/user-reference-retry-decision.json`。
以下内容保留旧阶段记录；与本节冲突的旧审批时点以本节为准。

## 历史决定 — 2026-10-15
流程具有两个整批人工gate：先审核剩余六task的全部候选资产；这批资产获批后，完成各task物理资格并各生成一条高质量reference及适用范围，六条集中交审。只有用户批准这整批六条reference/范围后，才按task顺序直接合成各100条；仅完成或批准其中一条reference不能先启动该task的100生产。

用户将剩余六task改为：全部候选资产先交审→资产批准后物理资格及各task一条高质量reference/适用范围交审→reference批准后按task顺序直接合成100，不再设十条pilot人工审核。此前已验收四task400条与source/recipe/data保持；新决定不回写旧pilot历史。100条全量检查、随机十条最终整task验收及每task一次WAM v2/v3兼容资格保持，后者移到100生产最初合格Clean＋Randomized工程准入（计入100），不新增人工pilot节点。

## 当前范围
sweep_block_to_zone、close_fridge_door、close_oven_door、turn_valve、pull_open_drawer、open_room_door。每task最多A primary proposal＋B/C backups，无使用配额。优先本项目独立参数化几何，原Go2/STEP rig/solver/camera只作尺寸和静态视图参考；不修改任何已批准旧asset、source/模型/env。真实block/zone、竖直与水平铰链门、单bar quarter-turn lever、prismatic drawer及足端可进入U把手、room door的真实lever/bolt/cam/strike框架全部必须出现在模型中。不能用teleport、辅助外力、FL焊接或逻辑开门代替交互。静态候选的尺寸/质量/摩擦/关节/handle开口仍是proposal，待用户批准后物理验收，不冒充难度或controller成功。

只生成Native compile/mj_forward/静态EGL真实像素和review，0physics steps/0controller/0reference/0formal数据。相机原接口及dual640×36050FPS/Observer720p25FPS不改；额外自由视角和关节初始姿态仅人工资产诊断，非正式数据。当前18个候选不要求asset级与旧Isaac等价；source/hash/license/版本和真实状态记录齐全。两Background、无clutter/强制Recovery、原native9/force-zero/RAMBO/500-100-50Hz、task success与quality分开、普通NativeCPU/EGL3+3/1GiB/7.6GiB/0.5GiB/4GiB新render保护保持。

## Progress / acceptance
- [x] 18个候选的独立几何、关节/contact机构、mass/inertia/friction/handle开口、来源/license/版本/hash说明。
- [x] 实际Native compile和零step数据姿态/静态EGL各task完整外观、操作细节、Go2比例参照视图；所有真实状态与未执行项。
- [x] 六task集中资产审核页已生成、治理同步；最终图片QA另列，用户资产审核pending。
- [ ] 用户批准各task的primary/backups及资产方案；批准前不physics/reference/100。

HF400发布由独立QLM-DATA-026和mujoco400-hf heartbeat收尾，不占用新task批准，不启动第二个上传写者。v2DOC-024/v3DOC-023只治理，当前不WAM/checkcache/fit/训练/AMD/source commit/push或新资产发布。

## 2026-10-15实际工程进度

18候选（每task A/B/C）均已Native compile＋mj_forward；72张NativeEGL静态图已生成，真实NVIDIA RTX5070Ti GL来源见workspace runs/audit/remaining-six-assets-20261015-v1/verification.json。全部六task overview与Room Door背面cam/bolt近景已实际检查；18模型resource identity、72图hash/尺寸及页面相对链接QA通过（workspace runs/audit/remaining-six-assets-20261015-v1/visual-qa.json），用户资产批准仍pending。原Go2 camera/inertia、独立资产inertia及parent resource identity保护通过；零step并不证明动态物理或可操作难度。

完整候选metadata含source/version/hash/license状态、mass/friction/joints/初始姿态/handle间隙/真实未验风险，审核页为workspace runs/audit/remaining-six-assets-20261015-v1/review.html。原4task400保持。physics steps/controller/reference/formal/WAM/cache/训练/AMD/source commit/push/新资产发布均未执行。Room Door实际cam/bolt解锁、Drawer真实hook、各关节动态及FL操作需要资产批准后另做资格，不以静态几何探查代替。

- [x] 18个独立候选及元数据/来源/动态未验风险。
- [x] Native compile/零step以及72静态像素实际生成，原资源及相机/惯量保护。
- [x] 六task集中review文件生成，当前table/consumer规则同步。
- [x] 主会话实际检查六task overview与门锁背面近景；visual-qa.json核对18模型resource identity、72图hash/尺寸及review相对链接通过。
- [ ] 用户资产批准；未批准前不physics/reference/100，QLM-DATA-027保持active。

## 最新reference审核分流：QLM-DATA-034

2026-10-16用户批准Drawer与Room Door reference/范围；Sweep动作被拒绝，Fridge/Valve/Oven提出时序调整，Oven质量改1kg。四项独立版本先交新nominal审核，获批后重验原预声明范围；旧四项范围不能冒充新版本通过。详见[reference审核修订决定](reference-review-refinement.md)。不重跑已批准两项，不解除全批reference/范围gate或启动100。
