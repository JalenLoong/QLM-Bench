---
id: OPD-V4-IMPLEMENTATION-005
type: current-design
status: accepted
related_work: [OPD-005]
source_map: []
---
# OPD-005 mixed-task implementation delivery

2026-10-24。源码已适配native1/2、400S/1200F/9600contexts、3F→1S、100-step cadence，
保护完整S200/S400并保留latest2。两repo仍为原worktree，未commit/push，未连接AMD或正式训练。

## Delivered behavior

Config驱动实际scheduler与sampler manifest，贯通actor/fake fitting/learner/initialize/export/serve。
Native Euler与完整当前链、state→action detach、history/KV/replay、conditional DMD公式保持。
恢复counter按配置3:1校验；每rank三context、DDP mean8；全局task计数用SUM，loss无task或1/L权重。

QLM新增training_control：独立profile绑定原train800 pool和训练horizons；旧pool不重写。
SQLite事务维护confirmed starts、round-robin、shuffle deck与ticket，cap2、确认/取消/结束幂等。
WAM通过公共CLI控制，原四操作RPC保持。Worker强制CPU-only并从profile读取horizon，
显式max_episodes1201避免旧1000上限。Training timeout与原terminal及budget stop分别记录。

resume-v2在barrier内保存control_state和learner；新segment恢复取消旧active/pending。
student-v2导出/加载显式核对设计与sampler。旧2/4/5:1 artifacts和receipts不能静默复用。
profile/control路径支持显式relocate；DB地址不参与算法身份，模型/资源/代码内容仍绑定。

## Local evidence

权威证据：workspace runs/audit/opd-v4-mixed-task-implementation-20261024-v1/。
WAM make check通过：201passed、21skip（20旧dataset fixtures及1个可选ffmpeg integration）；
OPD定向34tests通过。QLM suite282passed、13可选skip，另一个八进程SQLite调度测试通过。
双rank CPU/Gloo参数差0，最终空模态同步通过；no_sync backward、checkpoint read/boundary、
nonfinite gradient四项共同abort通过。实际Gloo为2ranks×3contexts，8ranks/24context预算由轻量fixture核对。
Tiny CUDA两rounds约3.145秒，peak reserved27,262,976 bytes，2S/6F，未加载完整模型。
真实NativeCPU/RAMBOCPU/OSMesa mock-policy六chunks、两mock updates、一次reset、14次frozen RPC通过，
零WAM inference/真实optimizer。第一次因未提供已有OSMesa库路径在import阶段失败，零physics；
第二次显式使用已有工作区库成功，无安装/升级依赖，原失败保留。
400S/1200F/9600与safe-stop/cadence通过轻量engine fixture验证，没有执行400轮模型训练。

## Remaining boundary

真实5B/三角色AMD/ROCm/RCCL、八CPU streams、正式400S及OPD性能均not_run。
3:1是用户配置选择，不宣称优于5:1或同等稳定。正式运行需要新匹配startup/single/eight-card报告。
原SFT/model/data、历史ADR及OPD-001至004归档保持；OPD-004报告仅描述当时待实施状态。
本轮原评估/视频/automation不操作。Source bundle、逐文件hash、check日志和资源回读见证据目录。

## Resource and control integration

实际SFT transformer payload hashes、frozen VAE/text/prompt与train800 pool完整核验通过，
full_model_loaded=false、physics_steps=0。旧pool SHA仍为
 dff729244322f6a1cb4aa7c2d9e73404fe002e0879474ba0190c022644f889a1。
新training profile SHA为09b9f202c05c5d2a49414278cbfb7b1bf3715ff1e1ad6724386a0679b4ece76c。
实际公共QLM CLI完成init/snapshot/stop/新segment restore；八worker preview共享同一ledger/segment，
每worker cap1201；profile/control地址变化不改变training identity。此控制面检查没有物理执行。

## Administrator package

本轮证据目录提供amd-single-resolved.json、同目录qlm-profile、formal-process-preview.json及
opd-v4-mixed-task-runtime.tar.gz/manifest。它们是本地主机绑定和未执行的命令preview，
需relocate并供给目标原生ROCm/OSMesa环境；不构成AMD准入。Bundle不含权重、数据或虚拟环境。
