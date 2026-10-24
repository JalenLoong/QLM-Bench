---
id: OPD-009
type: exec-plan
status: completed
source_map: []
---
# Five-update ratio observation only

User clarified:only the3:1 stability observation is5 successful student updates and record-only.
Keep single/eight-card engineering smoke,default2rounds,formal admission,Slurm DAG and400S budget unchanged.
Introduce an independent opt-in observation profile/report because no distinct ratio validation existed.
Do not launch any observation,AMD,training,full5B,Slurm,commit/push or change unrelated code.

- [x] Preserve current pending OPD-008 work and clarify exact scope.
- [x] Add fixed5S/15F observation and separate non-admission report.
- [x] Add CPU regressions;verify engineering/Slurm defaults unchanged.
- [x] Archive this narrow change with evidence.

Evidence: workspace runs/audit/opd-v4-ratio-observation-20261024-v1/.

## Result
Standalone ratio_probe fixes the observation at5S/15F and writes ratio-probe.json with admission_eligible=false.
Existing single/eight engineering smoke gates,default2rounds,Slurm DAG and learner are byte-identical to the pre-change snapshot.
Six new CPU cases pass;targeted31pass;full WAM make check231pass/21skip.
No actual ratio observation,AMD,Slurm,full5B,training task,commit/push or unrelated changes.
