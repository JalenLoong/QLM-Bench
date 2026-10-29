---
id: OPD-014
type: change
status: completed
source_map: []
---
# Quadrupedal OPD compatibility and EMLINK repair

User authorizes removing startup-acceptance admission,retaining single/eight engineering gates,
resource/checkpoint integrity,and compatibility with administrator-owned existing smoke/run records.
Separate runtime compatibility from provenance,permit recorded operational retry settings,
keep old snapshots/reports/checkpoints immutable,and add EMLINK copy fallback in paired QLM.
Reduce redundant resource/source scanning without skipping content verification on untrusted mutable resources.
Only the quadrupedal OPD and paired QLM worktrees;no commit/push,AMD,Slurm,training or full5B load.

- [x] Register explicit legacy compatibility and semantic runtime/resource contracts.
- [x] Remove startup gate;preserve engineering admission and old report authentication.
- [x] Add immutable continuation execution snapshots and compatible checkpoint/export restore.
- [x] Fix EMLINK,profile formatting and redundant scans;retain payload checks.
- [x] Test old/new records,operations-only changes,negative compatibility/corruption cases,CPU recovery and publish-only retry.
- [x] Update administrator docs/ADR and archive paired records after checks.

Evidence: workspace runs/audit/opd-v4-compatibility-20261029-v1/.
AMD runtime reports supplied in administrator document are external evidence,not reproduced here.

WAM274pass/21skip plus final42affected checks;QLM307pass/13skip plus final10targeted checks (one new LINK_MAX case).
Original run/report fixtures stay byte-identical;tiny CPU old-checkpoint recovery gives exact student/fake parameters.
Real existing800-case resource/header verification and public5-stage preview passed,zero physics/full5B/Slurm.
See [current delivery](../../../current/opd-v4-compatibility-014.md).No commit/push or AMD connection.
