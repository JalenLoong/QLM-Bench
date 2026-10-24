---
id: OPD-010
type: exec-plan
status: completed
source_map: []
---
# Publish Slurm chain and five-update observation

User authorizes committing all pending OPD-008/009 implementation,tests and docs in both OPD worktrees,
ordinary-pushing every configured origin target,and independent commit/tree/blob remote verification.
No AMD,training,full5B,Slurm submission,model/data publication,PR or unrelated services/automation.

- [x] Capture pending inventory and verify exact tested OPD-009 content.
- [x] Verify remote tips,docs/import/governance and staged contents.
- [x] Commit source,push every target and independently fetch/read back.
- [x] Archive paired publication records,push closure and verify final tips/clean worktrees.

Evidence: workspace runs/audit/opd-v4-slurm-ratio-publication-20261024-v1/.
Unchanged implementation reuses actual231pass/21skip CPU evidence;no model or simulation rerun.

## Verified publication
Source committed and ordinary-pushed to all3configured targets;independent commit/tree/blob readback passed.
Closure receives final readback in final-independent-readback.json and completion.json.
All tested implementation bytes are preserved;no AMD,Slurm,training or full5B execution.
