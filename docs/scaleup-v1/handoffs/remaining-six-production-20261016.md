---
id: QLM-REMAINING-SIX-PRODUCTION-HANDOFF
type: current
status: accepted
related_work: [QLM-DOC-008, QLM-DATA-039, QLM-DATA-038]
source_map: []
---

# MuJoCo QLM-Bench：剩余六任务数据合成交接

日期：2026-10-16（Australia/Sydney）。本页是当前状态和执行入口索引，不把旧目标计划、审计候选或 scope trace 当成已完成的正式生产。

## 当前任务与本次停止点

目标是以原 Go2/FL/RAMBO 生成完整 10-task、每 task 100 条的全新 MuJoCo demonstrations，共1,000条；同一份 Raw/Canonical 服务 WAM v2/v3。当前处于 P3 数据合成；P0–P2 本地基础工程已收尾，SFT/AMD/OPD/RL不在本交接执行范围。

用户已批准 Fridge/Oven/Valve 修订后的全部范围。本轮只登记批准、更新治理和准备交接，**未启动剩余六项的100条生产**。新会话第一轮先只读理解并与用户对齐，等待下一条开工指令后实施。既有“不100”的历史段落不能被误读为这些已完成审核还要重新审批；本次尚不生产是交接/首轮对齐的明确边界。

批准 receipt：[DATA039 用户范围批准](/home/jalen/workspace/WAM-Policy/runs/audit/revised-three-scope-20261016-v1/user-scope-approval.json)。DATA039 配对 ChangeSpec/ExecPlan 已归档；QLM-DOC-008负责本交接。旧 `scope-result`、`delivery-check` 等签名工程记录不回写，旧 `pending` 用新批准 receipt 解释。

## 已完成与尚未完成

- Push Box、Press Button、Lift Basket、Kick Ball to Goal 各100条，合计 **400/1,000**，均已用户最终验收。
- 这400条已发布到 private HF dataset `dontKnow23456/QLM-Bench` 的 `main`。本地发布回读证据：`/home/jalen/workspace/WAM-Policy/runs/audit/mujoco400-hf-publication-20261015-v1/publication-receipt.json`。main=`a8eafc5b1e6019e4431d0417d9064f9fd658cc03`，不可变payload=`fde0f80eeec7ae36b7848a2bc6147d3c063d9f9b`；旧main完整保留在`Isaac-based`，原SHA=`519725c8bc77b35fd5d3b4ac8555a3e96a8876a7`。这是已有receipt状态，本轮没有再次联网发布。
- 剩余六项各100、合计600条正式数据 **尚未生产**。reference/scope里的成功轨迹是开发/验收证据，不能自动凑进正式100条或冒充已建立新pilot。
- 六task的资产角色、当前reference与相应人工审核已完成；当前必须补齐的是生产接入、生产准入、一次task级WAM兼容与规模化采集，不是重新搜资产/重新调reference。
- reference原型和scope代码大量保存在`runs/audit`，不是公共production/runtime已接入的证明。源码和已发布HEAD之间存在本地差异，必须看真实工作区；不要reset或覆盖它们。

## 六任务当前权威绑定

**先读结构化完整入口，避免从旧同名`a04`中选错：**

`/home/jalen/workspace/WAM-Policy/runs/audit/remaining-six-handoff-20261016-v1/approved-six-task-bindings.json`

它为每项列出当前 reference、真实executor/recipe/初态入口、primary model、视频hash、批准receipt、scope证据及特殊注意点。

| task_id | 当前获批reference | 最新scope工程事实 | 当前范围/关键语义 |
|---|---|---|---|
| `sweep_block_to_zone` | Sweep A09 | 31/32；032原40s timeout保留；用户随后明确批准Sweep/A09 | 正前方地面、outline-only goal；nominal距离22.5cm、20.5–24.5cm；block XY±2cm/yaw±5°、goal方向±4°。小拨/侧移顺序不再硬门控，以原full-footprint/notfallen/三tick为task success。 |
| `close_fridge_door` | **DATA038 A04**，27.96s | DATA039 16/16，已获用户批准 | XY±2cm/yaw±5°、初角45–55°；nominal50°。远停稳后伸腿，抵门后随实际门面继续前伸、机身配合；不能恢复抵门后固定短前伸或旧冲击关门。 |
| `close_oven_door` | DATA034 oven-a01，1kg/35°/4s | DATA039 16/16，已获用户批准 | XY±2cm/yaw±5°、初角25–35°；门体1kg含handle、35°限位、中央操作、约4s停进场并前伸。不要复用旧1.8kg、50°或落到90°的方案。 |
| `turn_valve` | DATA034 valve-a01，约6s开始操作 | DATA039 16/16，已获用户批准 | XY±2cm/yaw±5°、lever初态0–5°，真实接触转至≥85°，沿用实际mount方向适配。 |
| `pull_open_drawer` | `reference-drawer-a07`，scope qualification-v5 | 16/16，reference/范围此前已获批准 | XY±2cm/yaw±5°、初始伸出0–2cm；真实完整穿过U-hook再拉出≥24cm。注意executor内部recipe id与scope验收版本不是同一编号。 |
| `open_room_door` | A19历史动作来源+获批v3策略 | DATA033 Door 16/16，reference/范围此前已获批准 | 28cm handle/联动锁机构；XY±2cm/yaw±5°、8角点×两背景。先抬足高于handle，再前伸搭顶、下压真实解锁后推开≥15°。 |

共同notfallen和连续三个实际50Hz边界保持。Fridge/Oven/Valve数据见：

- `/home/jalen/workspace/WAM-Policy/runs/audit/revised-three-scope-20261016-v1/reference-scope-catalog.json`
- `/home/jalen/workspace/WAM-Policy/runs/audit/revised-three-scope-20261016-v1/campaign.json`
- `/home/jalen/workspace/WAM-Policy/runs/audit/revised-three-scope-20261016-v1/user-scope-approval.json`

这些范围是primary A的证据，不自动把A的资格推到B/C。每task A primary+B/C backups，无使用配额；缺少某backup的新资格不应阻塞已合格primary生产。

### 必须保留的事实

1. **Sweep用户批准不等于把历史31/32改成32/32。** 保留032及其他失败；不默认重试reference、缩范围或要求32/32作为新增人工gate。批量候选仍按批准分布和有界失败处理。A09是人工动作reference；DATA036的optional/geometry executor是不同实际source，生产迁移必须显式绑定真实版本，不能冒充旧录像由新executor产生。不要原样复制旧A09的顺序硬门控后又恢复已取消要求。
2. **Room Door成功判据必须特别接入。** 权威是`/home/jalen/workspace/WAM-Policy/runs/audit/door-lowered-reference-20261016-v1/reference/door_socket_predicate_v3.py`内`DoorSocketExit`/`task_state_class()`：实际bolt实体退出socket的历史event +开门≥15°；开门后bolt回弹不撤销解锁。不得恢复固定20mm退栓门槛。通用`shared_runtime.ReferenceTaskState`仍含旧Door逻辑，不能直接拿来生产Door。
   A19是获批的历史动作来源：原attempt仍是旧20mm判据下的失败，当前展示视频只是截到离线新判据24.4s位置的媒体前缀，没有改写原terminal，也不是重新按v3实时执行的nominal成功。v3实时及时终止的通过证据来自DATA033的16/16范围。A19原执行使用small-opening profile，当前生产primary是geometric-opening profile；resource ID不同，compiled物理参数已独立核对完全相同。绑定JSON分别记录两个身份，禁止把A19失败trace直接当v3正式成功数据。
3. **保留完整原robot reset状态。** 从批准reference snapshots/manifest或对应campaign取值，再只施加批准的场景参数；不能只复制hinge角、改用通用spawn站姿。Fridge nominal50°是runtime初态override，原on-disk model默认仍55°；生产应冻结清晰的新初态profile/metadata。
4. Drawer的reference manifest里`recipe_config={}`不是“无recipe”：真实`DrawerLaneHeadingExecutor`有继承默认和lane/heading修订。必须连同继承链冻结，不可退回泛用base expert。
5. DATA039的Fridge10/16有1–7次FL calf正受力观测，最大5.19N；全部48个case无非FL正受力观测（50Hz层面），这些观察随范围已获用户批准。Oven首次接触均约35°，Valve首次接触接近0°，不是操作阶段仍覆盖reset全部初角。Drawer旧scope的短暂head擦碰及独立方向分析也要保留。
6. 当前scope验证采用NativeCPU/原RAMBOCPU；不声称新profile已在CUDA/ROCm实测。保留原backend/source身份，不给旧CUDA/OSMesa轨迹改名为Native/EGL。

## 工程接入差距与可复用基础

已具备：P0–P2解耦基础、原RAMBO、真实PhysicalTrace、Native state replay/EGL renderer、Raw/Canonical converter/validator、队列/背压/资源保护、成功trace复用和四task100条交付流程。

当前只读代码审计确认的限制：

- 六项`src/qlm_bench/tasks/registrations/*.json`仍为`planned`。
- `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco/src/qlm_bench/backends/mujoco/rendition.py`的`audit_trace`等路径明确限于旧四task；不能把scope成功当作已经能生产六task Raw/Canonical/RGB。
- `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco/src/qlm_bench/backends/mujoco/tasks.py`仍主要是P2三task通用实现；后来的task-specific paths及audit helpers要按实际调用核查。
- `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco/scripts/mujoco/synthesis/kick100.py`是“旧10pilot+新90”专用流程；剩余六项是全新100，不能照抄其pilot/consumer-already-validated断言。
- 冻结的reference/success adapter需要通过公共task/data接口接入，包含articulation progress、完整snapshot、初态/goal metadata、独立predicate、Raw/Canonical回读与实际prompt。通过可逆的工程接入完成；不篡改旧lock或Frozen v2.1 schema来绕过validator。

可复用的生产入口：

- `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco/src/qlm_bench/backends/mujoco/native_production.py`
- `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco/src/qlm_bench/backends/mujoco/production.py`
- `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco/src/qlm_bench/backends/mujoco/kick_production.py`
- `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco/src/qlm_bench/backends/mujoco/trace.py`
- `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco/src/qlm_bench/backends/mujoco/rendition.py`
- `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco/scripts/mujoco/synthesis/render_trace.py`
- `/home/jalen/workspace/WAM-Policy/runs/audit/kick-scale100-20261015-v1/pipeline.py`及同目录`finalize.py`、`deliver_review.py`、`full-artifact-checks.json`。

旧生产campaign/source是不可变历史。新生产建立独立Work-ID、source/campaign/队列，复用模块和有效证据，不能向旧队列加写或覆盖其成功trace。

## 已冻结的生产规则

- 六task各100：每task20 Clean+80 Randomized；train80/validation10/test10，各split为16/64、2/8、2/8。三split共享批准的ID支持域，具体配置与physical trajectory不跨split重复/近重复；不把几何区间切成互斥段，不另建OOD track。
- Clean是nominal附近小幅真实几何变化，非同初态复制；Clean使用ap_00。Randomized覆盖ap_00/ap_01；不自造asset×background交叉配额。无clutter、无强制Recovery。
- 保持goal observability gate：变化的goal必须可由policy RGB或原有明确任务条件辨识，不能生成只有privileged expert知道的目标，也不通过改相机/裁切来绕过问题。
- 原native9/forcezero、500Hz physics/100Hz controller/50Hz action-state和原RAMBO内部history保持。model/checkpoint不重训、不改核心控制器。
- 双路原始RGB640×360@50FPS、原FoV/extrinsics/intrinsics/full view；Observer1280×720@25FPS只作独立诊断。WAM stride4→12.5Hz，320×180再pad320×192；v2/v3使用同一Canonical，保留各自适配。
- 执行频率不等于额外diagnostic长期保存要求。必需Raw/Canonical字段、N actions/N RGB、N+1 state boundaries、实际snapshot、完整command confirmation、pre-reset terminal保持；不造dummy action。当前Raw validator要求的既有高频stream不能丢/伪造/绕过；不额外无条件扩张高频diagnostic存储。
- task success和demonstration quality分开。未知/缺失FL telemetry不直接失败；拒绝入SFT须可靠实际行为证据，不放宽task predicate。
- 真实contact完成任务，无teleport、虚拟解锁、FL焊接或辅助外力。成功physics不因media失败/资源恢复重跑；只重试同一trace的媒体。失败候选默认轻量日志，有界尝试，不通过持续改seed/收缩范围制造表面成功。
- 后续普通本地Native MuJoCo CPU/原RAMBO CPU + Native EGL RTX5070Ti，**3 physics+3 render重叠流水线**。MemAvailable<1GiB停新physics；swap相对launch增长>7.6GiB排空；<0.5GiB仅回收render；新render需≥4GiB；pressure后render≤2。并发是全局上限目标，不对每个task各开3+3。
- OSMesa仍为跨平台reference，CUDA-MJWarp保留，AMD优先ROCm-MJWarp主线保持；当前不连接AMD/训练或扩大技术路线。

## 批量流程与下一工作包

人工资产/reference阶段已通过；**不再设每task十条pilot人工审核**。建议按现有目录顺序Sweep→Fridge→Oven→Valve→Drawer→Room Door逐task100；若工程依赖更适合调整顺序，先说明依据，无须重开已冻结研究决策。

用户对齐并批准新会话开工后：

1. 检查当前Work-ID/ExecPlan及真实source，建立新生产工作包。核对这份绑定manifest，不重新搜资产或调nominal。
2. 先补齐六task共用的生产准入桥/renderer+Raw+Canonical audit及当前success adapter；保持QLM与WAM环境/公共协议边界，不重写已有PhysicalTrace和offline rendering架构。
3. 用最早合格的Clean+Randomized实际production样本完成端到端准入，计入100。每task WAM v2/v3兼容仅一次：先查已有真实receipt，确实没有才做Reader/原VAE/cache/SFT-input/online路径检查，保留证据，不fit/训练，也不对100条逐条反复生成模型验证cache。这是工程准入，不新增人工pilot gate。
4. 冻结candidate配置、source、recipe、asset、split与资源政策后逐task到100。每task结束立即全量物理身份/Raw/Canonical/媒体/时钟/command/terminal/既有telemetry/跨split去重检查与合并，失败fail-closed并保留source。
5. 六task全部完成后统一进行每task全100均匀无放回随机10的人工最终验收；不把逐task随机十条人工确认作为进入下一task的门槛。此时累计应为1,000条，但600条的新HF发布需另有用户授权。

本轮不做SFT、AMD、OPD/RL、Git commit/push、HF新发布或历史失败二进制清理。用户要求重新设计冻结action/observation/data contract、主要physics/rendering路线、重训/大改RAMBO、改变任务物理语义/success或需大规模返工的风险时才集中确认；普通工程细节自主推进并留记录。

## 最小必读清单与读取顺序

1. 本文件和 `/home/jalen/workspace/WAM-Policy/runs/audit/remaining-six-handoff-20261016-v1/approved-six-task-bindings.json`。
2. workspace `/home/jalen/workspace/WAM-Policy/AGENTS.md`及三个当前repo的AGENTS；按各repo的`.agent/PLANS.md`、Work registry和当前文档协议执行。优先最新置顶状态，旧历史段落不能覆盖新批准。
3. `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco/docs/scaleup-v1/decisions/remaining-six-batch-approval.md`、`automated-synthesis-v2.md`、`local-synthesis-concurrency.md`、`task-level-consumer-validation.md`。
4. `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco/docs/current/contracts-v2.md`与上述生产源码入口；必要时读取`compatibility/dataset_v2`具体Raw/Canonical、rendition及media validator。
5. 原完整背景材料 `/home/jalen/Downloads/QLM-Bench_randomization_and_automated_synthesis_handoff.md`。它的旧Push-only/10pilot/旧backend阶段受后续用户决定覆盖；整体execution plan v3也只是目标路线，不是工程完成事实。
6. 按绑定manifest读取六项当前reference manifest/recipe/executor、scope结果和approval；不必把所有500Hz telemetry/旧失败日志一次塞入上下文。Room Door必须另读`door_socket_predicate_v3.py`和`docs/scaleup-v1/decisions/door-geometric-unlock.md`；Sweep另读`sweep-task-success-only.md`。
7. 进入一次WAM兼容接入前，读WAM v2 `docs/current/contracts-v2.md`及v3 `docs/v3/current/`、各自AGENTS/registry与已有task级consumer receipts。此交接未要求重做四task已有资格。

实际工作区：

| 角色 | 路径 | 当前分支 | HEAD（不能替代dirty source库存） |
|---|---|---|---|
| QLM | `/home/jalen/workspace/WAM-Policy/repos/QLM-Bench-mujoco` | `migration/mujoco-foundation` | `7e7665b99bb3e753072cf9331377370eae1c385f` |
| WAM v2 | `/home/jalen/workspace/WAM-Policy/repos/WAM-Policy-v2-mujoco` | `adaptation/v2-mujoco-sft` | `f36dcea78580cffa4a6c1e5150d476dc845285f4` |
| WAM v3 | `/home/jalen/workspace/WAM-Policy/repos/WAM-Policy-mujoco` | `adaptation/v3-mujoco-sft` | `c8cf19dffbfe36a3fd3e3b35c2d1da3bcd4d3fd3` |

Simulator Python：`/home/jalen/workspace/WAM-Policy/envs/qlm-mujoco-py312-v1/bin/python`，源码通常以显式`PYTHONPATH`绑定当前QLM `src`；不要重装共享editable binding。原RAMBO checkpoint为`/home/jalen/workspace/WAM-Policy/assets/qlm/resources/20261003-refactor-v1/rambo-go2-controller/iteration-2000/runtime/model_2000.pt`，SHA256=`1cc5f68fe15e37ccabae26060d79a26a8c078ed465a81f6f729c2009b67ca706`。

**新会话首轮输出：** 用自己的话重述目标、400/600状态、已批准六reference和真实scope限制；指出实际生产接入缺口，提出第一个具体工作包与推进顺序，只提真正高影响的未决问题。首轮仅只读审查并对齐理解，等待用户下一步指令，不开始实现或合成。


## Reference中间产物已清理 — QLM-DOC-009

用户于本交接后明确要求清理reference反复调整中间产物。失败、被拒和已替换版本的媒体/数组/压缩telemetry/原始command与terminal payload/可重建cache已依清单移除，仅保留原参数、attempt/result/manifest/source及文字记录；历史manifest不再代表payload可回读。旧结果不回写。

当前六个获批reference、有效scope、原400正式数据、asset/model/environment和后续执行所依赖源码保持。尤其Sweep三条复用旧成功及32模型、Drawer16scope、Door A19原始动作状态/当前16scope、Fridge A04/当前三项48scope仍在。不要从已清理的旧版本读取数据，不因历史payload被删而重跑成功physics。

总清理汇总：workspace runs/audit/reference-intermediate-cleanup-20261016-v1/cleanup-completion.json；主批次/补充receipt及逐文件hash分别见cleanup-receipt.json、supplement-cleanup-receipt.json、cleanup-plan.json；文字归档为historical-attempt-text-archive.json。旧hand-off文档的授权前字节保存在同目录handoff-before-reference-cleanup.md，便于解释DOC008历史checksum；当前绑定清单与prompt本身未改写。

## 生产接入补注 / 2026-10-17 / QLM-DATA-040

原structured bindings与所有已冻结source保持不变。Drawer的nominal类为DrawerLaneHeadingExecutor，但实际已批准scope qualification-v5明确使用drawer_fixture_heading_executor.py的DrawerFixtureHeadingExecutor，hash9ecea6fc8a4add97bbb9076cf0b05819bd1165cfe974cbd5b770addc7141d27a；在nominal yaw0数值等价，randomized yaw主动将heading朝向fixture。公共binding从qualification的proposal及其hash解析该adapter，不再漏接。原生产31成功保留真实source，10次失败保持；独立版本root及累计预算见workspace runs/audit/remaining-six-production-20261016-v1/drawer-scope-binding-recovery.json。四项各100工程完成，最终用户审核仍pending。
