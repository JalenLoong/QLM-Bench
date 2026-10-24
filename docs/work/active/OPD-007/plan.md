---
id: OPD-007
type: exec-plan
status: active
source_map: []
---
# Publish reviewed OPD working trees

User explicitly authorizes committing all pending implementation,fixes,tests and documentation
in both existing OPD worktrees and pushing to every configured origin push URL on the current branch.
This supersedes historical no-commit/push statements only for this publication.
No AMD,training,full5B,model/data publication,PR or evaluation/service/automation operations.

- [x] Capture pending inventory,branch/remote targets and reviewed runtime hashes.
- [ ] Verify remote branch tips and publication safety;check source/docs/governance.
- [ ] Commit reviewed source and ordinary-push every configured target.
- [ ] Independently fetch each target into isolated Git storage and compare commit/tree/blob bytes.
- [ ] Archive paired records,publish closure,verify final remote state and clean worktrees.

Evidence: workspace runs/audit/opd-v4-source-publication-20261024-v1/.
Runtime matches OPD-006 CPU evidence;no repeated model/physics run is required for unchanged bytes.
