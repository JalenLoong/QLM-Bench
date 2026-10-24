---
id: OPD-V4-SOURCE-PUBLICATION-013
type: current-design
status: accepted
related_work: [OPD-013]
source_map: []
---
# OPD-013：HF dataset迁移与自动checkpoint上传源码发布

2026-10-25，用户授权的OPD-011/012全部实现、修复、测试及文档已commit并普通push到全部三个配置GitHub目标。
WAM以AIGeeksGroup主仓为管理员来源，JalenLoong/WAM-Policy仅为备份/同步目标。

- WAM-Policy-opd-v4：`opd/v4_Streaming-OPD_on_WAM-Policy`，source commit `bef9f6527a5169e76b51699e03e63b1f6627fbca`，26个变更文件。
  Target：`git@github.com:AIGeeksGroup/WAM-Policy.git`。
  Target：`git@github.com:JalenLoong/WAM-Policy.git`。
- QLM-Bench-opd-v4：`training/opd-v4-streaming-cpu`，source commit `621a8a79360b89bb1c7d4b01b58e11468138612d`，22个变更文件。
  Target：`git@github.com:JalenLoong/QLM-Bench.git`。

三个目标均fetch到新建无alternates的独立bare Git库，核验完整commit对象、root tree、全tree条目与每份变更blob的Git身份/SHA256，一致。
本文记录实现source commit；随后文档closure提交及最终tip的独立回读见workspace
runs/audit/opd-v4-hf-source-publication-20261025-v1/completion.json与final-independent-readback.json。

HF dataset网络入口改为AIGeeksGroup/QLM-Bench，固定revision及历史catalog/DataRef/checkpoint/reset pool字节不变。
Stage2-only Slurm链为prepare→single-smoke→eight-smoke→formal→publish，末尾publish仅CPU，
自动上传成功formal attempt保留的完整恢复点和final student到dontKnow23456/WAM-Policy的
checkpoints/opd-v4-quadrupedal/<run>/<formal-attempt>/，逐文件immutable-revision回读后才报告成功。
上传失败仅补publish、不重跑训练；仍需管理员实际提供具有model repo写权限的HF凭据。
Stage1=0、单/八卡工程smoke及独立5S/15F仅记录、不作为formal准入的规则保持。

发布前逐文件核对本次源码与已验证交付完全相同，沿用实际WAM255passed/21skipped、QLM304passed/13skipped及8个旧publication测试证据。
两repo的docs、import boundaries、paired governance、Shell语法和Git whitespace检查通过，不重复加载模型/运行physics。
历史OPD-011/012交付记录中的未commit/push属于当时状态，由本次发布记录补充，不回写原证据。

本轮仅GitHub源码发布：未连接AMD、执行Slurm/训练、加载完整5B或实际上传HF；没有模型/数据/media发布、PR或其他服务/automation操作。
真实目标ROCm/八流/Slurm、性能和正式HF权重上传仍需独立执行验收。
