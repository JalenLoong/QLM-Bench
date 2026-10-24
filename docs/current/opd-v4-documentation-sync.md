---
id: OPD-V4-DOCUMENTATION-SYNC
type: current-design
status: accepted
related_work: [OPD-004]
source_map: []
---
# Documentation Synchronization Report — OPD-004

日期：2026-10-24。范围：双仓库当前设计文档修订与代码只读审计。
**设计已同步；代码仍是旧2/4/200 profile，新目标不能直接执行。**
本轮没有修改source/config/test，没有模型加载、GPU/closed-loop验证或AMD访问。

## 1. 决策对照

| 项目 | 原实现/历史提案 | 当前接受的目标 |
|---|---|---|
| Student sampler | 旧native2/4 | **native1/2**，正式目标 |
| Teacher基线 | SFT25/50推理 | 保持25/50；不是DMD query内的采样次数 |
| 正式预算 | 200S/1000F/4800 contexts | **400S/2000F/9600 contexts**，3200 clips |
| 每轮 | 8streams×3slots、5F→1S | 保持 |
| Task reset | rank+episode_index×world_size | Global confirmed episode starts公平，平局round-robin |
| Task loss | 现有context mean；另有未实施的balance提案 | 保持context mean，无频率权重/1/L/10% quota |
| Push/Oven/RoomDoor训练上限 | 24/60/60秒 | **19.2/32/40秒**；其余七task不变 |
| Eval horizon | 标准benchmark时限 | 保持原值，与training分离 |
| 模型/梯度/KV | 三角色LoRA256、完整当前链、既定detach与replay | 保持，只将实际生成链改为1/2 |
| 环境硬件 | NativeCPU、RAMBOCPU、OSMesa/llvmpipe | 全八流保持CPU only；模型8×MI355X |

变更动机仅采用用户的定性实验结论：旧2/4基本保留teacher能力，新1/2有明显退化。
没有新增success-rate差值或video metric；OPD恢复能力是待验证目标。
Context份额随实际episode长度变化是选定objective的结果，不以task-macro loss equality验收。

## 2. 阅读与静态审查范围

完整阅读本轮pasted指令、479行最新版mixed-task稿，以及仓库方法/implementation plan。
核对两repo的AGENTS、docs/INDEX、documentation/v2治理、.agent/PLANS、
OPD registry、ADR-0001、OPD-003 paired records、OPD current/admin/review/portability。
按索引读取Adaptation v2 model/contracts/training、MuJoCo SFT5000与INFER-001 serving合同。
这些早期SFT/Isaac记录仅约束继承合同，不作为本轮OPD执行结果。

逐项静态阅读WAM config/sampling/models/runtime/engine/learner/cache/streaming/
checkpoint/export/binding/configure/initialization；定点检查inference/inference_loader、
FlowMatchScheduler、preflight、diagnostics、CLI及所有OPD examples/tests中的NFE引用。
读取QLM training_pool/training_live、SynchronousDriver stop入口和CPU admission。
检索task_balance、频率权重、horizons、budget、sampler与checkpoint相关引用。
没有导入模型、MuJoCo或Torch执行训练验证。

## 3. 实际修订文件

两repo同步相同的设计副本；WAM为算法与OPD registry的维护authority，QLM为边界镜像。

| 文件/类别 | 主要变化 |
|---|---|
| `docs/design/opd-v4/OPD-v4_Streaming-OPD_method_scheme.md` | 更新1/2方程与完整链、400预算、context objective、CPU边界与实验动机；保留DMD内部公式 |
| `docs/design/opd-v4/OPD-v4_Streaming-OPD_implementation_plan.md` | 在原位置改为主体完成度/现有模块映射/待实施delta，保留目标硬件与正式运行not_run |
| `docs/design/opd-v4/OPD-v4_mixed-task_WAM-Policy.md` | 仓库原无该文件；以用户稿建立索引入口，保留horizons/episode fairness，按最新指令更新1/2与审核状态 |
| `docs/decisions/opd-v4/ADR-0002.md` | 追加当前设计决定，部分supersede旧ADR，不回写ADR-0001 |
| `docs/current/opd-v4.md`（WAM） | 分开当前接受的目标与现有旧profile，保留资源及实现完成证据 |
| `docs/opd-v4-admin.md`（WAM） | 新正式目标与旧命令/配置的边界、准入/恢复/部署待改清单 |
| `docs/current/opd-v4-training.md`（QLM） | CPU-only实现事实、新调度与horizon差异、train/eval分离 |
| `docs/current/opd-v4-review.md` | 标明旧2/4 review证据范围，路由新决定，不复用为新验收 |
| `docs/current/opd-v4-documentation-sync.md` | 本报告：源码位置、验证清单、授权边界 |
| `AGENTS.md`、`docs/INDEX.md`、`.agent/PLANS.md` | 最小当前目标和治理路由；旧带日期记录保留历史 |
| `README.md` | 增加OPD当前目标与code pending入口，保持原SFT/QLM内容 |
| `docs/governance/opd-v4-work-registry.json`及OPD-004 pair | 文档同步独立Work ID，按既有检查通过后配对归档 |
| Workspace `AGENTS.md` | 仅追加OPD-004路由，不操作其他评估与服务 |

用户Downloads原稿和pasted附件未改。没有创建平行的第二套method/plan；新增mixed-task文件
是该此前只在Downloads中的稿件的仓库入口。完整逐文件hash清单在本轮审计目录。

## 4. 代码与配置影响清单（只读；后续待授权）

| 位置 | 当前事实 | 后续变更与验证 |
|---|---|---|
| WAM `config.py:45-47,78-85` | 默认200/2/4，validate固定2/4与formal(8,200) | 对齐1/2/400；旧值拒绝/显式历史身份测试，不能仅改JSON |
| WAM `sampling.py:8-17,29-48` | scheduler直接set_timesteps(4 if action else2)，不读Config.steps | 一套resolved sampler来源贯通generate/manifest；用原scheduler重建新网格 |
| WAM `streaming.py:59-76` | Actor调用共用generate；predict另写2次预测cache | 1/2 endpoint/parity与3 denoise+2 cache计数；无history或plan梯度 |
| WAM `learner.py:42-90,128-169` | Fake/student生成均走同一generate；DMD score单velocity query | 新1/2完整链反传，5F→1S不变；teacher/fake scoring不加25/50循环 |
| WAM `cache.py:34-119` | 角色/版本独立prefix replay，condition no_grad，current query保留图 | 复用；1/2跨eviction、stale拒绝、action→plan/KV detach及AC一致性回归 |
| WAM `inference.py:20-34,118-130` | SamplingConfig接受正整数、原_sample用指定steps生成网格 | 可作为1/2 parity参考；原inference_only对象不能用于learner backward |
| WAM `inference_loader.py:146-197`, `online_service.py:21-26`, `training/mujoco_profile.py:120-126` | 通用bundle loader不锁NFE；原SFT service factory仍强制25/50 | OPD用独立runtime/serve；保留teacher/SFT旧guard，不通过改原SFT身份放行1/2 |
| WAM `runtime.py:72-100` | Formal startup receipt写死sampling[2,4]；smoke绑定algorithm/source/pool | 更新[1,2]及新identity；拒绝旧receipt；真实startup另行授权 |
| WAM `configure.py:21-38` | non-diagnostic写200，logical_run名称继承OPD-001 | 新配置与运行身份；timeouts继续由实际AMD smoke测量，不能伪造准入 |
| WAM `engine.py:31-34,71,120-125` | formal stop参数、limit、final export/completion固定200 | 全部对齐400；第400成功update后feedback stop且无第401 predict |
| WAM `configs/opd_v4/*.json` | formal/deployment/AMD examples写200，NFE隐式继承旧Config | 后续更新示例并显式核对1/2/400；diagnostic/smoke仍用有界执行次数 |
| WAM `binding.py:70-90`, `Config.algorithm_digest` | Config semantics含steps/budget，source/pool严格绑定 | 新NFE/budget/horizons/schedule产生新identity；旧OPD resume不能静默复用 |
| WAM `checkpoint.py:56-123,126-133` | 原子round恢复；retain仅最近2份，无保护点 | 建议保护S200/S400；验证持续保存到400后200仍存在；双optimizer/RNG恢复 |
| WAM `export.py:12-28`, `engine.py:145-160` | export记录固定sampler_manifest；load验证artifact身份但未显式与active config sampler比对 | 绑定新manifest并显式校验runtime与export预算/网格；加载错误sampler拒绝；同noise导出parity |
| WAM `initialization.py:74-96` | 默认继承0updates，low_nfe_behavior仍pending | 保持0updates，初始化export和新startup明确1/2，不自动SFT/Bootstrap |
| WAM `tests/opd_v4/test_math_sampling.py:51-78,93-121` | trace与native parity fixture沿旧2/4；部分trace断言隐含2、4长度 | 更新为1/2全链；保留必要旧native对照但明确历史；不能只改test名称 |
| WAM `tests/opd_v4/test_service_and_admission.py:82-113` | startup fixture为[2,4] | 新profile准入正例及旧NFE/旧algorithm拒绝；无真实GPU调用 |
| QLM `training_pool.py:16,103,153` | HORIZONS旧24/60/60写入并严格校验pool records | 新train-only profile/manifest与身份，保护旧pool；标准suite时限不改 |
| QLM `training_pool.py:ResetSchedule.next` | global_index=rank+local_index×world_size；异步终止不按全局starts | 改为全局confirmed starts优先与可恢复tie/deck/预留；失败reset与并发测试 |
| QLM `training_live.py:67-70,84-103` | 每worker本地ResetSchedule，按record.horizon_s创建runtime/max_groups | 接入全局调度/确认与新训练profile，保持terminal和CPU freeze协议 |
| QLM `training_live.py:53,57,84,120` | max_episodes=1000是每worker安全上限，不是student updates | 400轮对应每rank1200slots；极短episodes可能先触及该上限，后续配置与测试需覆盖，不能机械替换所有1000 |
| WAM/QLM checkpoint/control state | 目前无全局confirmed-start/deck/tie/reservation恢复状态 | 最小持久化逻辑状态；resume仍新segment、continuity_break，旧active预留不复活 |
| Evaluation interfaces | WAM有student serve；QLM标准suite和source/EGL guard独立，未建立新OPD1/2冻结评测binding | 后续显式冻结teacher25/50与两种student1/2绑定，保持cases/horizon/判据、来源与比较口径 |

表内WAM相对路径均在 `src/wam_policy/opd_v4/`（特别注明inference/tests/configs除外）；
QLM位于 `src/qlm_bench/backends/mujoco/`。准确行号对应本轮未改动的源码。
静态网格推导：State query `[1]`、Action query `[1,.5]`，endpoint均0；model timestep乘1000。
State1只是单次Euler update，仍以velocity为网络输出，没有新增endpoint/consistency模型。

## 5. 已符合新方案、无需重写的部分

`Learner.train_round`各模态backward的scale是1/len(records)，每rank3contexts；
DDP mean8形成全局1/24。State/action按各自有效元素归一化后相加，student/fake规则一致。
未发现task-dependent loss multiplier、inverse frequency、1/L、context-deficit或旧balance实现。
Task计数仅用于metrics，当前未作为loss或调度系数；无须先构建再禁用旧提案。

LoRA三角色、生成/真实action区分、FP32 DMD公式、history/plan detach、KV chronology、
三slot barrier、ACK幂等、共同step/abort、连续环境与新segment恢复保留既有组织。
QLM已在MuJoCo import前设置OSMesa/software GL与worker GPU visibility隔离，强制Native、
RAMBO device=cpu、trace_only=False，实际检查controller参数和llvmpipe GL identity。
这些是源码事实，不是本轮重新通过了真实CPU rendering或目标硬件验收。

## 6. 一致性检查与证据边界

检查范围：文档metadata/链接/source-map、双仓库governance、成对registry/design镜像、
新目标关键数值与十任务表、DMD内部公式不变、旧代码/config/test/历史archive保护hash。
具体命令、退出码与日志见 workspace `runs/audit/opd-v4-documentation-sync-20261024-v1/`。
已完成结果见本报告末尾；未进行的模型与目标硬件验证继续标not_run。

旧2/4与200只在“原实现/历史证据/待改位置”语境保留；ADR-0001与OPD-001/002/003
为不可回写的旧决定和工程记录。新ADR明确superseding范围，当前入口指向新目标。
通用governance protocol与旧Isaac/MuJoCo registry保持不变。

## 7. 后续授权与未决事项

需要用户确认后才能修改本报告第4节所列source/config/tests，执行顺序见implementation plan。
算法目标已经明确，无需重新讨论1/2还是2/4、400预算、十任务horizons或loss重加权。
S200/S400保留为完整resume还是额外student export是一个可独立处理的artifact选择；
目标AMD环境、实测timeouts/HBM、startup与八流验收仍需真实证据和另行执行授权。
本轮不将这些待办描述为当前文档无法同步的阻断，也不据此重设计主体。

扩展索引检查发现一条原有非OPD失效链接：QLM `docs/INDEX.md` 指向
`scaleup-v1/work/active/QLM-DATA-027/plan.md`，目标已不存在。已用该分支HEAD核对，
此链接在本轮前就已存在，原行未改。本轮不扩展到其他任务的治理修复；它不阻断OPD
新文档的链接与成对检查，但作为尚存的索引问题明确记录。

新代码适配、1/2 tiny tests、GPU/closed-loop、AMD、正式400S与OPD性能：**not_run**。
源码commit/push/PR、依赖安装/升级、权重下载：**not_run**。

## 8. 本轮检查结果与关闭状态

- WAM docs-check：passed，224份governed documents。
- QLM docs-check：passed，118份governed documents。
- 双向peer governance与OPD成对registry：passed。
- 两repo AST import boundaries：passed；未运行模型或simulator。
- 本轮OPD链接检查通过；原有非OPD的QLM-DATA-027失效索引单列于第7节，未隐藏。
- 方法、plan、mixed-task、ADR-0002、差异报告与registry共6组镜像一致。
- 十任务training horizon与预算算术一致；DMD内部、fake FM与FM符号公式保持原文。
- 292份WAM、465份QLM受保护源码/config/test/script/历史治理文件hash保持，共757份。
- OPD-004 ChangeSpec/ExecPlan已成对归档，registry标记仅文档范围完成；后续代码待授权。

本轮未执行make check完整测试、tiny forward/backward、GPU、GL/physics rollout或AMD验收；
没有把这些项目标记为通过。全部更改仅为Markdown与OPD文档registry，既有未提交源码保持。
当前有效设计文档已对齐，当前代码与目标之间的差异已显式列出。
