---
id: QLM-LOCAL-SYNTHESIS-CONCURRENCY
type: decision
status: accepted
related_work: [QLM-SIM-018, QLM-DOC-006, QLM-DATA-022]
source_map: []
---

# 本地合成采用配置

2026-10-15，用户最新要求“后续保持3+3的并发，把swap增量保护上限提高至7.6GiB”。后续本地普通新launch采用 **Native CPU＋EGL、3 physics＋3 render**，替代同日此前选定的4+4；physics与原RAMBO仍在CPU执行，不是CUDA-MJWarp＋EGL。

| 配置项 | 用户采用值 |
|---|---|
| Physics | Native MuJoCo，CPU |
| RAMBO | 原controller／checkpoint／history语义，CPU执行 |
| Rendering | Native MuJoCo＋EGL，RTX 5070 Ti硬件渲染 |
| Physics workers | 3 |
| Render workers | 3 |
| 调度方式 | physics/render同时推进的流水线 |
| 跨平台rendering reference | OSMesa，继续保留 |

适用主机为RTX 5070 Ti 16GB、32GB RAM；已测试场景为Lift Basket A、LOD a02、dual RGB 640×360@50FPS及Observer 1280×720@25FPS。3+3是调度目标，实际派发仍受backpressure与下列资源保护约束，不强行维持数量，不采用先全physics再全render的阶段模式。

此选择只确定本地路线与并发。OSMesa继续作为跨平台reference/fallback；CUDA-MJWarp保留，AMD优先ROCm-MJWarp的方案不变。不能将本地Native CPU＋EGL的3+3自动套用到CUDA＋EGL、OSMesa或AMD服务器。

## 保持已批准的资源保护

| 条件 | 调度行为 |
|---|---|
| MemAvailable < 1 GiB（1073741824 bytes） | 暂停新physics派发，进入排空 |
| host swap相对本launch基准增长 > 7.6 GiB（8160437862 bytes） | 进入排空 |
| MemAvailable < 0.5 GiB（536870912 bytes） | 回收最新render-only worker |
| 启动新render | MemAvailable必须至少4 GiB（4294967296 bytes） |
| pressure后排空 | render上限2；按实际资源记录降档 |

成功physics不因媒体或资源重跑；需要恢复媒体时使用同一真实trace。保留原native9/force-zero、controller history与500/100/50Hz执行、camera/preprocessing、Raw/Canonical字段和task success predicate。

## 配置采用与工程状态

该组合通过的是单轮阶段压力测试：新physics与已有同配置真实trace的EGL rendering同时执行。它不等同于新轨迹全流程持续生产验收、EGL/OSMesa视觉等价证明或所有任务长期稳定性保证。用户采用配置不应被补写为这些验收已经完成。

历史QLM-DOC-006只更新治理；没有修改producer/runtime/validator，也没有启动新合成。后续正式执行前，应把这一已选定配置接入实际producer并完成既有数据准入和端到端检查；本次记录不能当作Native正式trace接入已完成。已完成的CUDA/OSMesa数据及原launch/source身份保持，不重标为Native/EGL。Lift十条pilot的用户审核仍独立。

QLM-SIM-018的全部benchmark目录、trace/RGB/视频、审核页、日志、诊断源码和派生缓存已按用户要求删除。本文件只保留采用配置、适用条件和必要决策记录；旧3+3建议及旧本地CUDA/OSMesa配置描述属于各自历史阶段。4+4与6GiB只是此前采用值；5+5没有获准用于正式生产。

## QLM-DATA-022实际接入与生产恢复

本轮用户批准原十条并要求按本配置扩100，producer已接入显式Native CPU/RAMBO CPU trace与实际NVIDIA EGL来源。新增90中的Clean031/ap00、Randomized046/ap01已完成真实physics、完整RGB/Raw/Canonical/terminal准入，见workspace runs/audit/lift-scale100-20261015-v1/production-admission.json。没有WAM重复执行，也不宣称OSMesa像素等价；旧10条CUDA/OSMesa原始身份保留。

完整生产曾实际达到4+4，发生available约110MiB/swap约8GiB的资源事件并回收一个render-only worker。随后会话中断，主调度退出，在途renderer已排空；已生成成功trace按原hash接管，没有physics重跑。此后曾按保护策略以3+3、2+2恢复，均使用旧6GiB增量阈值；当前普通launch目标按用户最新决定固定为3+3、7.6GiB，不能把单轮benchmark通过视为本次全流程4+4稳定通过。实际政策/中断/恢复与资源记录同审计目录。

## QLM-DATA-022最新调度policy v3

此次变更使用workspace runs/audit/lift-scale100-20261015-v1/resource-policy-v3.json及runtime-policy-v3/lift_production.py，保留冻结producer/campaign/source和原所有launch-policy，先停止新增派发并排空在途worker，再启用新launch。7.6GiB是相对每次launch的host swap使用基准增量，非swap使用总量或额外预留容量；本机swap总量约8GiB，若基准已用>0.4GiB，增量线可能无法先于swap用尽触发，原两道RAM保护继续有效。pressure排空期间render最多2不代表普通目标改成3+2，不把配置写入当作稳定生产已通过。
