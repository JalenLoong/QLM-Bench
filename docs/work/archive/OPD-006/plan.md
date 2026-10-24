---
id: OPD-006
type: exec-plan
status: completed
source_map: []
---
# Independent mixed-task portability review

User authorizes independent review of OPD-005 and direct fixes with regression tests.
Preserve native1/2,3F:1S,400S,CPU-only environment and immutable model/data/history.
No AMD connection,full5B,formal training,commit/push,or changes to evaluations/automation.

- [x] Read implementation handoff and source; preserve initial dirty inventory.
- [x] Reproduce concrete path/launch/scheduler/recovery defects with CPU fixtures.
- [x] Fix confirmed defects and add regression coverage.
- [x] Run affected tests,WAM make check,QLM CPU suite and paired governance.
- [x] Deliver current report and archive paired records.

Evidence: workspace runs/audit/opd-v4-independent-review-20261024-v1/.
Target ROCm/RCCL/full-model/eight-stream acceptance remains not_run.

## Outcome
R1 concurrent deck exhaustion and R2 resource-scan timeout fixed with failing-before/passing-after tests.
WAM aggregate202pass/21skip;QLM aggregate283pass/13skip after host-loopback reruns.
OPD two-rankGloo max parameter error0. Relocated real-resource preflight and nonempty control restore pass.
See docs/current/opd-v4-independent-review-006.md and audit report for exact scope and not_run boundaries.
