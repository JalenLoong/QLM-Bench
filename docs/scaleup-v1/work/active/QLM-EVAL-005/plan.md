---
id: QLM-EVAL-005
type: exec-plan
status: active
source_map: []
---
# Execution plan

## Progress
- [x] Read user authorization, fixed protocol and prior memory-recovery evidence.
- [x] Reserve independent paired Work IDs and preserve original dirty state.
- [ ] Verify exact two-leaf config delta, checkpoint/prompt/resource identities and GPU admission.
- [ ] Run100 fresh fixed cases, preserving all valid outcomes and original capture.
- [ ] Decode original captured latents after policy exit; audit all media and metrics.
- [ ] Compare against25/50 baseline and archive paired work.

## Decisions and recovery
This is a new user-requested experiment, not recovery/replacement of previous trials. Within the new experiment only infrastructure error/not_run slots may resume, under identical sampling fingerprint. Stop rather than recover an unsealed attempt without verifying its durable rows. Keep all source/attempt/evidence.

## Validation
Use the same frozen suite source/resource validator and real zero-step hardwareEGL preflight. The formal model loader authenticates consumed weights/normalizers/prompts. Verify first real predictions use2/4. Existing numerical runtime/sampler code is copied or reused unchanged; orchestration/labels only.

## Not run
No training, AMD, HF/GitHub or W&B uploads. Results remain pending until100 trials and media audit complete.

Evidence: workspace runs/audit/mujoco-v2-sft5000-nfe2-4-evaluation-20261021-v1

## 用户暂停 —2026-10-21

用户明确要求暂停本次2/4 NFEs evaluation。已核对host无本run的controller/policy/client或service，尚无attempt目录，0trial/0physics/0模型推理。仅保存准备配置和Work记录；不自动恢复。原MuJoCo25/50 loader限制已发现，但run-local2/4准入入口尚未实现，原模型runtime源码未修改。需用户明确恢复后再完成准入、preflight及启动。权威状态：workspace runs/audit/mujoco-v2-sft5000-nfe2-4-evaluation-20261021-v1/workflow-state.json。
