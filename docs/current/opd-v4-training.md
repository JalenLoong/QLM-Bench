---
id: QLM-OPD-V4-TRAINING
type: current-design
status: accepted
related_work: [OPD-005]
source_map:
  - src/qlm_bench/backends/mujoco/training_control.py
  - src/qlm_bench/backends/mujoco/training_live.py
  - src/qlm_bench/backends/mujoco/training_pool.py
---
# CPU-only mixed-task OPD training bridge

OPD-005已实现global episode-level round-robin和独立training profile，与WAM native1/2、
400S/1200F、3F→1S、100-step saving配对。[本地交付](opd-v4-implementation-005.md)、
[当前决定](../decisions/opd-v4/ADR-0003.md)、[实施接口](../design/opd-v4/OPD-v4_Streaming-OPD_implementation_plan.md)。

原认证train800 pool和资源保持，十task各80、160Clean/640Randomized，heldout不参与训练。
qlm-opd-v4-training-profile-v1独立绑定pool SHA与训练horizons：Push19.2、Press/Lift/Kick24、
Oven/Valve32、Sweep/Fridge/Drawer/RoomDoor40秒；标准benchmark时限及success predicates保持。
Worker显式使用profile.horizons，旧pool.horizon_s仅为原资源manifest历史元数据。

EpisodeSchedule使用node-local SQLite事务，优先confirmed starts最少task，平局持久化round-robin；
保留task内原shuffle deck，同task运行＋预留cap2。Ticket幂等，reset RPC成功后确认/消费UID，
失败释放未消费预留；真实terminal结束释放占用。不按context欠额、不重加权loss、不按update reset。

WAM调用make-profile/inspect-profile/schedule-init/snapshot/restore/stop公共CLI，不import模拟器实现。
SQLite锁内不运行RPC/torch/collective；5秒锁timeout。Runtime RPC保持reset/predict/feedback/end。
每worker1201 episode上限，第三feedback全rank barrier内snapshot；第400update停止新ticket和后续predict。
Checkpoint恢复使用新segment，保留confirmed/deck/cursor并取消旧active/pending，不声称物理连续恢复。

所有8条训练streams的RAMBO device=cpu、Native MuJoCo physics与OSMesa/llvmpipe rendering均CPU only。
MuJoCo首次import前设置软件GL与GPU隐藏，启动后核验controller参数和GL identity；没有GPU fallback。
500Hz physics/100Hz controller/50Hz command与RGB、模型12.5Hz子集保持。任务/camera/native9合同不改。

本地mock-policy六chunks跨两mock更新、一次reset、14frozen RPC证据已记录；无WAM模型调用。
AMD/full5B/真实八流/正式400S未运行。历史OPD-004差异报告保持当时事实，不作为当前代码状态。
