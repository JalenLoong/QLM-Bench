---
id: QLM-SIM-024
type: change
status: completed
source_map: []
---
# RL-v2 LoRA and ten-demo configuration

User approved screenshot configuration on 2026-10-26. Implement LoRA rank32 alpha32 dropout0 on all30 blocks attn1/attn2/FFN only; frozen original parameters; ten-demo two-distinct-demo scheduler,8 strata each,G4; optimizer LR3e-5 warmup10 constant,weight decay0;reference .05;EMA only after optimizer updates;120 rounds/960 training candidates;validation40;checkpoint20. Validation current/EMA uses ten validation normal initial states.

Preserve prior artifacts. New schemas reject old training resume. Validation: analytical LoRA/update/EMA/warmup; multi-demo scheduler/resume; tiny backward/export/distributed; public configuration and preview.

Not run: new GT replay/calibration, full5B backward, formal training/validation, AMD/Slurm, remote publication.

## Completed implementation and verification — 2026-10-26

User screenshot implemented: LoRA32/alpha32/dropout0,300 target Linear layers across30 blocks;80,609,280 trainable parameters from real architecture meta inventory. Ten fixed train demos,8 temporal strata each,two distinct demos/G4,120-round/960-candidate cap. Warmup10 actual optimizer updates,LR3e-5,weight decay0,reference.05;flat rounds skip optimizer/scheduler/EMA. Checkpoint20 and held-out normal-initial-state current/EMA validation40 are integrated. Planned pool/preparation and six-stage previews are read-only.

Evidence: workspace runs/audit/rl-v2-lora-ten-demo-20261026-v1/. Final affected tests42 passed; full WAM suite initially199 passed/21 optional skips and one sandbox socket failure, that test passed on host; three additional tests subsequently passed. QLM affected13 passed. Two/eight-process Gloo passed with empty ranks and collective abort. Tiny CUDA continuous8 versus4+resume4 all state exact,peak reserved102MiB.

Merged LoRA BF16 sampling failed predeclared tolerance; preserved failed evidence. Replaced deploy export with typed unmerged backbone+adapter and FP32-master/BF16-forward loader; tiny CUDA current/EMA same-prefix/noise25/50 sampling exact(video/action error0). No relaxed threshold. Existing SFT loader unchanged.

No formal training, new CPU references/calibration, actual validation, AMD/Slurm or remote publication. Source remains uncommitted/unpushed. New schemas do not admit previous full-parameter/single-demo checkpoints.
