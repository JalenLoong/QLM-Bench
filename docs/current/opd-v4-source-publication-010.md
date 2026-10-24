---
id: OPD-V4-SOURCE-PUBLICATION-010
type: current-design
status: accepted
related_work: [OPD-010]
source_map: []
---
# OPD-010：Slurm链与5S观测源码发布

2026-10-24，用户授权的OPD-008/009实现、测试与文档已统一提交并普通push到全部三个配置的GitHub目标。
没有force push，没有执行Slurm、AMD或训练。

- WAM-Policy-opd-v4：`opd/v4_Streaming-OPD_on_WAM-Policy`，source commit `230254bd550ebbe7851698289754c6393776840b`，28个变更文件。
  Target：`git@github.com:AIGeeksGroup/WAM-Policy.git`。
  Target：`git@github.com:JalenLoong/WAM-Policy.git`。
- QLM-Bench-opd-v4：`training/opd-v4-streaming-cpu`，source commit `2271f476d088839ef34d841c97a6322553863396`，15个变更文件。
  Target：`git@github.com:JalenLoong/QLM-Bench.git`。

每个目标均从GitHub fetch到全新、无alternates的独立bare Git库，核对完整commit对象、
root tree、全tree条目和所有变更文件的Git blob/SHA256；三目标均一致。
本文记录source commit；随后仅文档归档的closure提交及最终tip见workspace
runs/audit/opd-v4-slurm-ratio-publication-20261024-v1/completion.json与final-independent-readback.json。

发布内容包括独立prepare→single-smoke→eight-smoke→formal Slurm链、README/admin路由、
旧SFT独立指南，以及固定5S/15F的ratio_probe记录型观测。Stage1=0，复用既有checkpoint/reset pool，
不处理离线SFT数据。独立5S观测不加入Slurm依赖、不作为formal准入；原单/八卡工程smoke默认2rounds及gate保持。

提交前逐文件确认源码与OPD-009通过的版本相同，沿用实际WAM231pass/21skip（新增6例，定向31pass）证据，
没有重复模型或physics执行。此次docs、import boundaries、paired governance、Shell语法和whitespace检查通过。
历史OPD-008/009中未commit/push的表述保留原时点，不回写其执行source或测试receipt为新commit。

实际Slurm/ROCm/八流、5S观测及正式400S仍not_run；本轮没有连接AMD、启动训练、加载完整5B，
没有模型/数据发布、PR或其他评估、媒体、服务及automation操作。精确源码commit已包含本次全部实现；
权重、reset pool、环境和目标平台验收仍需独立准备。
