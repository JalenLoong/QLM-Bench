---
id: OPD-012
type: exec-plan
status: completed
source_map: []
---
# Post-formal checkpoint publisher

User authorizes adding automatic HF checkpoint upload after formal to the existing model repo
dontKnow23456/WAM-Policy,under checkpoints in a new opd-v4-quadrupedal directory.
Upload retained complete OPD checkpoints and final student export,not base weights/data/smoke artifacts.
Keep Stage1=0,400S/1200F,2-round engineering smokes and independent non-gating5S observation.
Implementation/CPU fake-Hub and fake-Slurm tests only;no actual upload,AMD,training,Slurm or full5B.

- [x] Add immutable,collision-safe checkpoint/export publisher with readback.
- [x] Add dependent CPU publish stage and publish-only continuation.
- [x] Update current README/admin and CPU regressions.
- [x] Complete checks and paired archive.

Evidence: workspace runs/audit/opd-v4-hf-checkpoint-publisher-20261025-v1/.

Completed evidence and exact scope: [current report](../../../current/opd-v4-hf-publication-012.md).
