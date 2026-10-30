# QLM-Bench quadrupedal OPD CPU runtime agent guide

本 worktree 对应 `training/opd-v4-streaming-cpu`，服务 WAM `opd/v4_Streaming-OPD_on_WAM-Policy`，配套目录为 `../WAM-Policy-opd-v4`。使用完整分支名，不使用管理员临时编号。

先读 [docs/INDEX.md](docs/INDEX.md) 与 [当前交接状态](docs/current/opd-v4-handoff-20261029.md)，再按任务读 runtime、design 或 evidence。开始操作前确认实际 branch、HEAD、working tree 及当前用户要求。

## 稳定职责与契约

- QLM 负责任务、场景、MuJoCo physics、原 RAMBO controller、reset pool、环境通信和模型无关评估；WAM 负责模型、normalizer、训练和 checkpoint。CPU core 不隐式 import WAM / VAE / T5 / 模型框架，simulator 加载保持显式。
- 保留 Go2、FL manipulation、native9、absolute FL target、force-zero、原 controller、float32 执行、command50Hz/controller100Hz/physics500Hz，以及实际 simulation timestamps、完整 interval history 和 terminal-before-reset。不得为通过检查而改任务判据或物理参数。
- 本 OPD runtime 使用 Native MuJoCo CPU / RAMBO CPU / OSMesa-llvmpipe，环境 RPC 使用独立 socket。其他分支 stdout IPC 问题不能直接套用；不要引入 NVIDIA MJWarp 作为本路线默认 runtime。
- 本地真实 MuJoCo CPU 结果可支持 AMD 服务器 CPU 路径；ROCm 模型计算、RCCL 和 Slurm 完整运行仍以各自证据判断。区分实际证据与 mock/tiny、数值一致性与策略效果。
- 原 pool、资源 manifest、失败和已发表结果保持可追溯；hash 的记录用途不能自动变成兼容性门槛。按既定 runtime 合同保留必要内容校验，不新增无算法依据的人工签字或成功率准入。
- 使用显式 resource/source roots，不修改共享 editable environment 绑定。旧 absolute path 是历史来源，不等于当前硬依赖；先查 RETENTION 再判断 payload 是否存在。

数据存储与终止语义以 DATA-002 冻结的 `wam-quadruped-v2.1.0` 为准，见 [当前数据合同](docs/current/adaptation_v2_dataset_contract.md)；DATA-001 旧验收只作历史。

## 文档与执行

遵循 [治理协议](docs/governance/documentation.md)、[context 路由](docs/governance/context-routing.md) 和 [.agent/PLANS.md](.agent/PLANS.md)。OPD Work ID 由配套 WAM 的 docs/governance/opd-v4-work-registry.json 分配，本仓库保持配对；shared-v2 和 scaleup registry/active 目录是继承记录，不是当前执行队列。

按实际改动验证公共接口、受影响 CPU/环境行为和文档；纯文档改动不启动物理仿真或训练。远端任务、commit/push、发布和删除资源以当前用户授权为准，不复用历史一次性授权。旧入口全文见 [历史快照](docs/history/context-before-20261029/README.md)。本次文档整理 Work ID 为 workspace/WS-DOC-001。
