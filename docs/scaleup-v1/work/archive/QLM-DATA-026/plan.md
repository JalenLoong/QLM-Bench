---
id: QLM-DATA-026
type: exec-plan
status: completed
source_map: []
---

# Kick100最终验收与MuJoCo400 HF发布

## 用户授权与顺序
用户最终批准Kick100，累计Push100＋Press100＋Lift100＋Kick100=400/1000。先完成Kick最终receipt及治理收尾，再发布现有四task全部400条至dontKnow23456/QLM-Bench main，完整原main保留为Isaac-based。用户补充dataset已设private，保持private；现有登录已实际读私有repo且token role=write，不需新token。如权限不足按用户要求停下说明授权流程，不能要求把token贴入会话。

## 发布边界
发布400条已验收正式demonstration，包括正式批准并计入每task100的原十条pilots；不发布开发reference/范围探针、失败candidate、未批准旧Isaac数据、model/cache/checkpoints、训练产物或asset source。既有publication policy中的pilot排除继续适用于未批准开发数据，不错误排除这40条已批准正式数据。Raw/Canonical、媒体、原source/asset/controller/backend/camera身份、原checksum/50Hz action-state/command/terminal/required既有telemetry全部保留；不重跑physics或渲染、不改变contract。asset许可unknown据实保留，不宣称repo MIT自动覆盖独立资产；当前只数据/metadata，资产源payload不上传。HF实际private保持，不擅自开放访问。

## 计划与验收
- [x] Kick100独立最终批准receipt、400总数与原receipt保护；三repo当前路由同步，其他task暂不启动。
- [x] 读取远端实际old-main SHA/完整文件身份与branch/private，核对本地四task400的allowlist、80/10/10与20/80、source/已验收证据。
- [x] 构造无symlink、完整materialized Raw/Canonical400 staging、版本化task releases/catalog/schema/README/明确license信息与逐文件SHA256/Gitblob inventory。原数据/模型/源heads不变。
- [x] 在本地staging验证后，以旧main SHA创建Isaac-based并核对完整旧树；临时HF分支上传新400，逐文件校验及独立下载样本/metadata/Canonical与Raw回读通过。
- [x] 用精确旧HEAD保护将验证过的400分支切到main，核对main完整树、400/320-40-40/80Clean320Randomized、private及Isaac-based旧SHA/旧文件不变；清理仅本次创建的临时branch。
- [x] 文档/配对计划/registry/索引及发布receipt收尾，输出两branch和新revision。失败fail-closed，不提前改main或默认可见性。

复用已有publication legacy_core的safe path/hash/远端LFS或Gitblob比对，现有HF CLI/SDK和登录，不安装升级依赖。临时分支/仓库仅服务该HF dataset发布，禁止source repo commit/push、训练、AMD或新task rollout。WAM v2DOC-023/v3DOC-022只治理，已有各task一次兼容资格复用，不运行WAM或新cache。W&B not_run/local-only。


## 上传执行状态（非最终发布验收） — 2026-10-16

实际完成400条materialized staging，14054文件/17307843192bytes；local-staging-check及source identity通过。旧main SHA519725c8bc77b35fd5d3b4ac8555a3e96a8876a7已保存Isaac-based，2860原文件逐一身份一致，private保持。唯一官方hf upload-large-folder正在mujoco400-staging-20261015-v1上传；原main未切换，未产出最终publication receipt。原自定义上传器已安全停止，1260既有文件核对后交官方CLI恢复，没有两个写者。

初期约2.6–3.0MB/s有效提交率，保守预计90–110分钟余量；mujoco400-hf已ACTIVE，首轮计划悉尼2026-10-16约01:13，若未完成且正常随后15分钟安静检查。pre-uploaded批次返回与committed分开，不能据前者宣布完成。具体实际log和cache为准。

make_index/finish_publication/finalize_publication_governance及governance-finalization-handoff已准备，语法/本地恢复逻辑审查不等于实际远端验收；只有上传器退出且远端完整identity通过后才执行finisher，finisher实际退出0后才执行--apply治理归档，最后暂停monitor。本文当前保持active，相关最终验收checkbox不提前勾选。

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

