# WAM-Policy OPD-v4 implementation plan and delivered interfaces

OPD-005，2026-10-24。当前代码已在既有独立worktree实现native1/2、400S/1200F、3F→1S、
每100次保存、global episode fairness与context-equal loss。主体与本轮适配完成状态以
[本地交付](../../current/opd-v4-implementation-005.md)为准；AMD/full5B/八流/正式400S未运行。

## 1. 来源与固定合同

WAM分支opd/v4_Streaming-OPD_on_WAM-Policy的parent为e26d1ef0db9423af2e797abca8026af4bdec495e；
QLM training/opd-v4-streaming-cpu的parent为5954235ae75d787eef6af44d58594fd48bde51be。
共同SFT为MuJoCo1000 v2 formal step5000、attempt4af42de1ce-full、HF revision
6b8620888b119896866e22c27eff8b6f9f50a520；normalizer/VAE/text/prompt/native9/RGB合同保持。

Stage1默认继承权重、零增量LoRA、0updates；显式teacher-data joint FM SFT仍是关闭的可选入口。
独立teacher/student/fake，actor复用student；student/fake各自LoRA256/alpha256/dropout0，
只训练self-attention Q/K/V/O和两个FFN Linear，其他参数冻结。

State1/action2完整Euler生成，原shift5/1、CFG1/window8；state query[1]、action[1,.5]，到0。
Teacher25/50是基线闭环推理，DMD单次score query仍为给定rho的velocity。
三次fake updates后一次student update；400S/1200F/9600contexts、3200clips，额外失败开销另计。
各模态归一化后相加，本地mean3/DDP mean8，无task频率权重、1/L或10%context quota。
AdamW2e-6、betas(.9,.999)、eps1e-8、WD.01、分别clip1、constant LR保持。

## 2. 实现映射与接口

| 子系统 | 当前实现 |
|---|---|
| 配置与sampler | Config的design为opd-v4-native1-2-3f-400s-v1；scheduler读取同一Config，manifest含实际grid/steps/shift/CFG/window/solver/parameterization |
| 生成与loss | sampling.generate用于actor、fake-fitting、student；learner保持逐模态完整链与FP32 DMD，三个fake substeps独立重采样 |
| 梯度/缓存 | State backward后释放graph；action使用detached plan与角色自己的conditioning KV；episode-prefix replay、版本、eviction与非重入AC保持 |
| Streaming | 三个真实slots；第三feedback提交后等3F→1S、checkpoint/KV/version就绪；重复ACK幂等，正常update不reset |
| DDP/metrics | 六个模态单元累积，最后同步；共同step/abort；task_contexts_global通过gather后SUM，task loss仅诊断 |
| 身份与部署 | identity-v2绑定sampler与training profile hash；student-v2导出和加载检查active设计及sampler，不静默接受旧2/4/5:1 |
| QLM控制 | training_control.EpisodeSchedule及training_live公共CLI；WAM control.TrainingControl用指定QLM解释器调用，无simulator实现import |
| 恢复 | resume-v2包含control_state，与同round双LoRA/optimizer/scheduler/RNG/counters原子保存 |

## 3. QLM training profile与全局调度

已认证train800资源池保持不变。新的qlm-opd-v4-training-profile-v1绑定pool SHA、十任务训练
horizons、seed42、global confirmed-start round-robin和CPU-only runtime。原pool内horizon是
历史元数据；worker显式使用training profile的时限，标准evaluation时限保持独立。
完整表见[mixed-task设计](OPD-v4_mixed-task_WAM-Policy.md#3-per-task-training-horizon)。

SQLite在node-local scratch独立attempt目录，默认系统临时目录下wam-opd-v4；control_root可配置。
DB地址不进入算法身份。BEGIN IMMEDIATE事务只处理计数、ticket与shuffle deck，锁等待5秒；
不在锁内做RPC/模型/collective。CLI操作有显式有限timeout，默认沿用rpc_timeout_s，管理员可设置
control_timeout_s；资源核验耗时与数据库锁等待分别处理。

真实reset时过滤同task运行＋预留达到2的任务，按confirmed starts最少、持久化round-robin平局选择。
Ticket由segment/stream/episode序号标识；预留不计start，reset RPC成功后confirm并消费UID；
失败cancel，正常terminal或budget-stop释放占用。task内保持原确定性shuffle顺序；完整cycle后再循环。
并发预留不重复UID；重试不重复计数；没有context-deficit、预测长度配额或动态stall规则。

WAM launcher为八worker传入同一segment/database/profile，每worker episode安全上限1201。
模型端点ready之前leader初始化或恢复调度；第三feedback全rank barrier内读取逻辑snapshot。
第400成功update先关闭新ticket领取，再保存/重建/释放停止反馈，QLM在下一predict前结束。

新增公共CLI：make-profile、inspect-profile、schedule-init、schedule-snapshot、schedule-restore、
schedule-stop。Worker新增必填training-profile/schedule-db/segment；policy RPC仍只有四种操作。

## 4. 保存、恢复与本地验证

保存S100/S200/S300/S400和安全停止完整round；retention=latest2 ∪ protected(S200,S400)。
S200/F600和S400/F1200为完整恢复点，最终另导出student。Fake计数恢复校验使用配置更新比。
Crash恢复到新segment，保留confirmed counts、round-robin/deck，取消旧reserved/active；
记录continuity_break，不恢复精确物理trajectory。旧schema/旧设计不提供隐式迁移。

本地测试包括1/2 full-chain与export parity、AC/KV跨eviction、3F→1S与独立optimizer、
CPU/Gloo平均与共同abort、并发/取消/恢复/八task初始覆盖、保护点与400控制流程。
400控制流程使用轻量fixture，没有执行400轮模型训练。实际CPU worker配mock policy最多6chunks，
tiny CUDA每项≤4GiB/120s、总≤600s。本地资源检查不加载完整5B。

## 5. 后续目标硬件准入

正式目标8×MI355X负责模型；全部8条QLM streams的Native physics、RAMBO和OSMesa/llvmpipe
都CPU only，先设置软件GL再import并核验device/GL identity，无GPU fallback。
经另行执行授权后，AMD单卡真实三角色/完整1/2 backward，再8卡8CPU streams至少两连续rounds，
核验HBM、RCCL、软件渲染、恢复与实测timeouts。完整400S和冻结teacher25/50、initialized1/2、
distilled1/2评估仍未执行。评测使用原held-out cases/horizons/判据与独立frozen source binding。

历史OPD-001至004、ADR-0001/0002、旧attempt与SFT身份不回写；OPD-005及ADR-0003记录当前实现。
