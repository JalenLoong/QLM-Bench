---
id: OPD-007
type: change
status: completed
source_map: []
---
# Publish reviewed OPD working trees

User explicitly authorizes committing all pending implementation,fixes,tests and documentation
in both existing OPD worktrees and pushing to every configured origin push URL on the current branch.
This supersedes historical no-commit/push statements only for this publication.
No AMD,training,full5B,model/data publication,PR or evaluation/service/automation operations.

- [x] Capture pending inventory,branch/remote targets and reviewed runtime hashes.
- [x] Verify remote branch tips and publication safety;check source/docs/governance.
- [x] Commit reviewed source and ordinary-push every configured target.
- [x] Independently fetch each target into isolated Git storage and compare commit/tree/blob bytes.
- [x] Archive paired records,publish closure,verify final remote state and clean worktrees.

Evidence: workspace runs/audit/opd-v4-source-publication-20261024-v1/.
Runtime matches OPD-006 CPU evidence;no repeated model/physics run is required for unchanged bytes.

## Verified outcome
Source commits are pushed and independently verified on all three configured targets.
The final closure commit receives its own remote verification in final-independent-readback.json;
completion.json records final commit/tree identities and clean working trees.
Source matches OPD-006 tests;no model,physics,AMD or training execution.
