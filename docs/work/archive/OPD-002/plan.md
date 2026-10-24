---
id: OPD-002
type: exec-plan
status: completed
source_map: []
---
# Independent OPD-v4 review

User authorized independent review and direct fixes on 2026-10-22. Review the method
scheme, implementation plan and executable source separately. Preserve OPD-001
historical evidence and all unrelated checkouts. No commit/push, AMD access or full
5B loading. Use CPU/tiny regression tests; do not interfere with the existing two
video decoders or repeat physics/evaluation.

## Plan and acceptance
- [x] Audit full sampler gradients, conditioning/cache isolation and full-prefix replay.
- [x] Audit persistent streaming, duplicate/terminal feedback and final stop.
- [x] Audit DDP failure consensus, checkpoint/resume/export and CPU-only workers.
- [x] Reproduce findings, fix with focused regressions, run affected suites.
- [x] Publish requirement mapping, findings, checks and remaining target-hardware limits.

Evidence: workspace runs/audit/opd-v4-independent-review-20261022-v1/.

## Findings and closure
- ExecutionAck aliases could count a physical chunk twice or strand a retry future;
  deduplicate by receipt identity and share the original pending/final result.
- Local no-sync backward and checkpoint failures lacked rank consensus; use explicit
  common error boundaries. Synchronized reducer failures retain the bounded watchdog.
- Pool membership was self-declared; authenticate source releases and reset traces,
  preserve all original reset values, and require complete resource inventories.
- Launcher could miss already-exited failures and wait indefinitely after worker exit;
  check all exit codes and enforce an overall deadline.
- Retain raw normalized actor actions in each context, separately from physical commands;
  add task/LR/version/phase metrics and failed-attempt physical metadata.

Validation: full WAM and QLM CPU suites; analytic/full-chain/cache/recompute tests,
actual localhost tiny learner resume into a new session, two-rank Gloo equivalence,
empty final modality and injected failure consensus; authenticated real train800 pool.
No GPU, full5B, AMD, formal training, commit/push or evaluation/decoder operations.
Historical OPD-001 receipts are unchanged; new source/pool hashes require reconfiguration
and new target-hardware evidence. See current review note and workspace audit report.
