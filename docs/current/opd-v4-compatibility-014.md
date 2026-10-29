---
id: OPD-V4-COMPATIBILITY-014
type: current-design
status: accepted
related_work: [OPD-014]
source_map: []
---
# OPD-014：训练兼容性与运行来源分离

本地修复范围仅四足WAM `opd/v4_Streaming-OPD_on_WAM-Policy` 和QLM `training/opd-v4-streaming-cpu`。
Stage1=0、native State1/Action2、3F→1S、400S/1200F、单/八卡各2rounds工程准入及独立5S记录用途保持。

## 行为变化

- 删除formal的startup acceptance文件/布尔声明门槛。旧site字段与CLI --startup允许保留但不读取文件。
- 全源码hash保留来源用途。工程兼容性使用明确列出的模型/训练/RPC/physics/controller运行文件语法树和JSON语义指纹；
  注释、排版、无关SFT/HF发布代码、离线pool复制代码不使已有smoke失效。真实数值或运行合同变化仍拒绝静默复用。
- 新smoke记录runtime compatibility和资源语义指纹；旧报告通过登记的源码版本映射接入，仍校验成功状态、
  单/八卡world、更新数、恢复通过、CPU-only、ROCm、HBM和原payload完整性。5S报告仍不能充当工程smoke。
- 旧 `run.json`、report和payload保持字节不变。续接新参数写入 `executions/<binding>.json`，ledger记录原run与执行snapshot。
  time/RAM/CPU/partition及兼容的主机路径可调整，未知job/active jobs仍阻止重复提交。
  已排队的某次执行仍冻结其env setup；只能在旧jobs退出后通过新执行记录调整，不能原地改旧snapshot。
- 已发布的OPD-013旧版已明确登记：WAM全源码指纹 `2bb8720277ae1c9ac583ff4cb3144c25f77a4cea3c07fd6a38e8ebab9ee7fc74`，
  QLM全源码指纹 `c00b6cac799900f660cbaeeba114ecd577b65e06189ec961c4b30ffe7dcdf118`。
  对应发布头WAM e7ccf34、QLM cffbd1d。映射仅表示本次经审阅和测试的兼容升级，不伪称旧smoke执行了新代码；未知版本不通配放行。
- checkpoint恢复先验证原文件hash与state内部identity对header的绑定，再比较模型/normalizer/资源、sampler、算法、
  runtime合同以及rank/RNG/optimizer状态。run名称和全源码来源不是恢复条件；原identity与manifest hash保留在恢复记录中。
  student export也保留原binding完整性并执行兼容性比较；任何真实资源或状态不匹配仍拒绝。
- 完成formal后，publish-only重试依据已绑定产物工作，不依赖当前训练pool、QLM解释器或训练源码；
  HF冲突拒绝、immutable revision和全部payload回读保持。提交时的环境与模型侧Python仍需可用。
- training profile按规范化内容判断，已审阅旧实现的固定profile合同可识别不同JSON排版；旧raw hash仍保留，
  smoke raw profile hash还必须与其绑定的stage config一致。原已发布catalog、pool manifest和payload校验不放宽。
- prepare/launch的单次preflight不再重复扫描同一pool；CPU worker每进程只计算一次producer来源/运行合同。
  不同进程仍验证实际可变资源，没有引入共享的弱校验缓存。固定CPU环境冲突在submit preview前明确报告变量与要求值。
- QLM hardlink遇到EMLINK回退copy；ENOSPC/EIO等错误继续失败。已有pool无需重建，文件/manifest内容不因存储方式变化。

## 管理员现有run的使用

待旧jobs退出后升级两repo，保留现有site/base config/run ID/output root。直接使用原OPD submit命令加
`--continue-chain`预览，再加`--execute`。无需生成startup-acceptance.json，无需修改历史hash或重跑已兼容的完成前缀。
若之前只有prepare和single-smoke完成，会先补eight-smoke；只有两份工程报告都通过才进入formal。
Unknown source/真实算法或资源变化需新的匹配证据，不应通过编辑旧receipt伪装通过。

本轮未读取AMD机器上的实际run/report文件；使用旧版相同schema和登记版本的CPU fixtures验证兼容路径。
管理员10月28日提供的运行情况属于外部记录，本地测试不等于在AMD完成验收。
代码、schema和指纹清单随分支部署，不需要Git metadata或调试机路径；新版本改变训练语义时必须同步更新合同和测试。

证据：workspace runs/audit/opd-v4-compatibility-20261029-v1/；最终测试计数及资源保护证明见completion.json。
没有commit/push、连接AMD、提交Slurm、正式训练、完整5B加载、HF/W&B远端写入或其他分支/服务/automation操作。

## 已完成的本地验证

- WAM完整make check：274 passed / 21既有可选dataset/media skips；最后执行snapshot来源绑定检查后，42个受影响用例再次通过。
- QLM完整core/public suite：307 passed / 13既有可选skips；新增LINK_MAX混合存储用例后，10个相关测试通过（合计308个不同用例通过）。
- 旧run/smoke schema无新字段接入；无startup、运维预算/环境更新、JSON不同排版、旧batch入口与publish-only重试通过。
- 算法/pool/prompt/实际runtime变化、未知legacy指纹、报告篡改和profile来源不一致均被拒绝。
- Tiny CPU旧checkpoint跨run名称恢复，后续student/fake参数逐值相同；旧student export加载通过；原artifact字节保持。
- checkpoint state内部identity被改写，即使更新文件hash，也因不再匹配原header被拒绝并共同abort。
- Python3.10/3.12对同一运行文件集的语义指纹一致；注释及离线pool复制修改不改变合同，physics代码变化会改变。
- 真实既有800-case pool/来源/冻结资源/原SFT metadata校验及公共CLI五阶段preview通过；未加载完整权重，未推进physics。
- 数值算法/模型/物理/controller、旧catalog/已归档记录与原SFT配置的保护库存hash保持；文档/governance/import检查通过。

以上测试使用CPU fixtures及fake Slurm/HF接口，不声称已在管理员机器上实际续接。没有改写管理员的历史验收数据。

两repo wheel均已包含compatibility JSON；在无.git的独立安装布局中读取运行合同成功，指纹与源码一致，未import torch。
