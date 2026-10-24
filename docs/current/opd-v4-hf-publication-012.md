---
id: OPD-V4-HF-PUBLICATION-012
type: current-design
status: accepted
related_work: [OPD-012]
source_map: []
---
# OPD-v4训练结束后自动上传checkpoint / OPD-012

在原Stage2-only工程链末尾增加CPU publish：
`prepare(0GPU) → single-smoke(1GPU) → eight-smoke(8GPU) → formal(8GPU) → publish(0GPU)`。
默认through=publish；site必须显式声明五阶段allocations。模板publish候选8CPU/64GiB/6h。
原四阶段site/run snapshot不自动迁移；源码身份变化后需重新configure和提交新run。
Stage1=0、400S/1200F、单/八卡各2rounds工程准入与独立5S记录型观测均保持。

目标固定为 `dontKnow23456/WAM-Policy` model repo的main分支：
`checkpoints/opd-v4-quadrupedal/<logical-run-id>/<successful-formal-attempt-UUID>/`。
上传成功formal attempt保留的完整恢复点和final_student（正常为S200/S300/S400；恢复后以实际保存列表为准），
以及identity/completion/publication_manifest。S400和完整final export必须存在。
恢复点包含student/fake adapters、optimizer/scheduler、计数和rank RNG/control state；final export是部署adapter。
不包含base5B、冻结资源、reset pool、原demonstrations或smoke权重，继续依赖原已认证SFT/base资源。

prepare只读检查HF登录和model repo访问，已知read token提前拒绝；需要站点提供write-capable HF token，
fine-grained repo写授权由HF实际commit校验。凭据不得存入Git/site JSON/命令参数。
publish通过同一model环境的huggingface_hub运行，CPU job不进入learner launcher，不读取tensor或创建模型；
计算节点需HF网络访问，输出文件系统需有全部上传文件的一份回读空间，上传前检查余量。

Formal成功report绑定checkpoint/export的每份文件。publish重新校验inventory/身份/hash，再以main的parent revision
执行一次commit；同路径已有相同文件可复用，不同内容或额外文件拒绝覆盖。
按返回的immutable revision列举并下载每份文件，全部SHA256一致且revision可解析才写hf-publication.json，
然后原子发布reports/publish.json。该receipt记录确切repo/path/commit URL、逐文件hash和checkpoint steps。

上传失败保留独立attempt，完成formal的report不撤销。原source/site/config/run ID的continue-chain只补publish，
不重跑400S、不申请GPU、不接受上传阶段的--resume；commit响应丢失或回读失败后复用远端一致文件。
需要保留本地checkpoint，直到完整回读成功；不强制覆盖远端，不删除failed attempts。

完整CPU回归255 passed/21 skipped。新增21个用例覆盖LFS/Git blob、原子commit与全量回读、已有目录冲突、
不完整/被篡改/diagnostic产物拒绝、只读token/磁盘不足、回读失败/commit响应丢失后的幂等重试、
五阶段afterok/资源分配、prepare权限失败、formal证据绑定和publish-only恢复。
所有Hub/Slurm修改均为mock，未向HF实际创建目录或上传文件；未连接AMD、运行Slurm/训练或加载完整5B。
源码未commit/push。证据：workspace runs/audit/opd-v4-hf-checkpoint-publisher-20261025-v1/。
本页更新OPD-008时期的四阶段/无HF上传描述；旧证据保持其原时点含义。
