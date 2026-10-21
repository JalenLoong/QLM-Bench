---
id: QLM-EVAL-004
type: change
status: completed
source_map: []
---
# SFT5000 Standard100 evaluation
Evaluate this round's MuJoCo1000 formal step5000 v2 then v3 checkpoints against frozen Standard100; retain real ego/task/observer and actual sampled video-flow latents/decoded videos for every trial.
User authorization: 2026-10-20 in the current chat.
Use dataset revision575d4a3726896d498ed4fb76710948b2fbea7cdd and the frozen100-slot protocol unchanged. NativeCPU/originalRAMBOCPU/hardwareEGL; original horizons, reset, controller, camera, sampling and terminal semantics remain.
Read-only HF acquisition. Authenticate manifests, full consumed weights, step5000 and MuJoCo1000 provenance; do not load optimizer or refit normalizers.
Run-local transparent prompt dispatch/capture may observe existing returns without changing RNG, model outputs, caches or physical commands. No training, AMD connection, source commit/push, model/data publication or deletion.
Acceptance: complete100 valid outcomes per available policy; all media present and decodable; per-task SR and successful-trial simulation completion time, explicit failure/timeout counts, comparison and evidence links. Infrastructure errors remain immutable and retry only under the frozen policy.
V3 admission is checked only after v2 completes; no partial/missing v3 upload is used.
Evidence root: workspace runs/audit/mujoco-sft5000-evaluation-20261020-v1/.

## Final verified completion2026-10-21
两版原固定Standard100各100个有效trial已经完成；v2为77success/23timeout（SR77%），v3为67success/33timeout（SR67%）。每版300个真实三视角和300个video-flow预测视频通过完整解码/帧数/哈希检查，独立复核共1200个视频及原latent/CSV绑定。

| Task | v2 SR | v3 SR | v2 success simulation均值/中位数(s) | v3 success simulation均值/中位数(s) |
|---|---:|---:|---:|---:|
| push_box | 10% | 100% | 8.88 / 8.88 | 8.63 / 8.56 |
| press_button | 70% | 70% | 14.80 / 15.12 | 15.07 / 15.36 |
| lift_basket | 100% | 100% | 16.61 / 16.49 | 15.61 / 15.49 |
| kick_ball_to_goal | 100% | 100% | 15.20 / 15.78 | 15.91 / 15.96 |
| sweep_block_to_zone | 0% | 0% | — / — | — / — |
| close_fridge_door | 100% | 100% | 27.22 / 27.08 | 34.97 / 35.27 |
| close_oven_door | 100% | 100% | 15.76 / 15.79 | 15.44 / 15.56 |
| turn_valve | 100% | 0% | 12.49 / 12.56 | — / — |
| pull_open_drawer | 90% | 100% | 35.69 / 34.64 | 26.29 / 25.38 |
| open_room_door | 100% | 0% | 18.97 / 19.08 | — / — |

完成时间只统计success的simulation time；timeout/failure没有完成时间。两版成功case集合可能不同，final-comparison.json另给共同成功case的配对均值。v2恢复28行wall_time_s明确标记executor_only_lower_bound，不用于上述完成时间。

v3 CUDA events：稳态group5–8共100个state denoise steps和200个action denoise steps。state联合video+proprioception，mean/median/P95=34.324/34.163/35.400ms；action=27.772/27.619/28.915ms。各自额外KV-cache写入均值37.516/31.705ms。原8组反馈重放全部输出逐值一致、评估文件hash保持。设备stream elapsed包括launch间隙，不包括CPU VAE/physics/media；RTX5070Ti，30blocksGPU/BF16/25–50NFEs/window8。

全部原attempt和失败历史保留，valid trial未重跑。双路离线VAE解码对照六个MP4的字节及逐帧一致后辅助发布31个trial；三进程单次诊断触及保护性allocator上限，未产生三路速度/一致性结论。当前全部GPU工作已经结束。

最终交付与权威完整性证据：delivery.md (`workspace runs/audit/mujoco-sft5000-evaluation-20261020-v1/delivery.md`)、review.html (`workspace runs/audit/mujoco-sft5000-evaluation-20261020-v1/review.html`)、completion.json (`workspace runs/audit/mujoco-sft5000-evaluation-20261020-v1/completion.json`)、final-independent-verification.json (`workspace runs/audit/mujoco-sft5000-evaluation-20261020-v1/final-independent-verification.json`)。

逐trial：v2 trials.csv (`workspace runs/audit/mujoco-sft5000-evaluation-20261020-v1/v2-EVAL-002_SFT5000-standard100/trials.csv`)、v3 trials.csv (`workspace runs/audit/mujoco-sft5000-evaluation-20261020-v1/v3-EVAL-002_SFT5000-standard100/trials.csv`)。图表及可复现Python源码在同一审计根charts/。

本次评估/诊断/收尾没有训练、AMD连接、HF/GitHub远端更改、W&B媒体/结果上传或证据清理。文档归档不改变原执行source/权重身份。
