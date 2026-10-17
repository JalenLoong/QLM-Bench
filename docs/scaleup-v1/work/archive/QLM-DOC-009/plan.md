---
id: QLM-DOC-009
type: exec-plan
status: completed
related_work: [QLM-DOC-008]
source_map: []
---

# Reference调试中间产物清理

用户明确要求清理本会话各task reference反复调整产生的中间产物，只保留文档文字记录。删除前建立逐文件清单、hash/大小、原attempt/result/source文字汇总，标记历史manifest不再代表payload可回读。保护当前获批六reference、最新有效scope、原400正式数据/pilots/模型资产/环境与任何后续生产实际依赖；保留依赖的代码/recipe/元数据。旧版成功但已被替换的reference也属中间产物，不把清理写成原任务失败。

只在明确审计目录处理废弃媒体、trace数组/telemetry payload、重复制品与可重建cache；不删除全局assets/data/模型/env。检查活跃进程/治理状态，若仍被生产使用则排除。按精确冻结清单删除，不用宽泛rm-rf。删除前后核对保护文件身份，保留完整文字审计、hardlink实际空间限制及交接更新。

- [x] 用户授权与Work-ID建立。
- [x] 候选/保护依赖清单及文字归档。
- [x] 精确清理并验证当前reference/范围与source不变。
- [x] 治理/交接/链接状态更新及归档。

## Reference中间产物已清理；当前获批证据保留 — 2026-10-16

按用户要求，QLM-DOC-009清理9870个reference迭代中间文件，逻辑37.66GiB；因硬链接实际可用空间观测增量约2.50GiB。原attempt/result/source/参数/文字记录保留，旧manifest不再保证历史payload可加载，不回写原成功/失败。

当前六reference及有效scope保留，10788个保护文件hash通过；6个reference资源/源码import和112个当前scope模型manifest、实际frozen source依赖核对通过。正式400、全局assets/模型/env未列为删除目标，未启动新合成。Sweep复用旧成功、Door A19原动作状态与v3范围等依赖仍保留。新会话继续使用当前绑定与交接文档，不能从已清理的旧试跑取数据，也无需重做已批准reference。

审计workspace runs/audit/reference-intermediate-cleanup-20261016-v1/：report.md、cleanup-receipt.json、historical-attempt-text-archive.json及完整清单。旧页面缺失媒体已标记；当前正式/获批文件不变。

