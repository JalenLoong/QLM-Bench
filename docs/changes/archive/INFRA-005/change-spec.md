---
id: INFRA-005
type: change
status: completed
source_map: []
---
# User-authorized local worktree cleanup

## Scope and authorization

On 2026-10-07 the user requested removal of the WAM v2 main worktree and all six
merged refactor/inference worktrees. Rebind the two CPU QLM data environments,
route current v3/QLM serving to retained main checkouts, then remove each worktree
with Git. Preserve branch/commit identities, models/data/assets and historical
receipts. No feature, reset repair, training, simulator rollout, commit or push.

## Progress and evidence

- [x] Clean-source, ancestry, ignored-file and dependency baseline captured.
- [ ] Rebind installed metadata and current routing; pass scoped CPU checks.
- [x] Remove six stage worktrees, preserve cleanup-only v2 governance delta,
      then remove WAM v2 worktree.
- [x] Verify retained sources/refs/receipts and archive completed records.

Evidence: workspace runs/audit/worktree-cleanup-20261007/.

## Recovery and authority

Original branch refs are retained; a removed worktree can be recreated at its
recorded branch/commit. The v2 cleanup governance delta is retained as a versioned
workspace authority patch, so its worktree can be clean before removal. Apply
that completed patch after recreating v2 before allocating another shared Work ID.
Only source bindings, current documentation and governance metadata change;
original archives/manifests/receipts remain immutable.

## Actual completion — 2026-10-07

All seven named directories were individually removed with git worktree remove,
without force, after clean-source/generated-ignore checks. Both data environments
resolve QLM-Bench and retain package versions and the original Push Box input pin.
Current v3/QLM imports resolve the main checkouts; v2 has no local runtime checkout.
Branch/remote-tracking refs and original commits remain unchanged, as do historical
archives/manifests/receipts and implementation/model/data/asset identities.

V3 required checks pass:56 tests passed in the sandbox; one existing CPU/Gloo test
failed only at loopback socket creation, then passed alone outside the sandbox.
Two QLM wrapper/static tests and both isolated CPU data-import checks passed.
No production training, simulator rollout, feature/reset repair or remote operation.
The v2 cleanup governance delta is recoverable through authority-completed.patch
in workspace runs/audit/worktree-cleanup-20261007/. Apply it after restoring v2
before further shared Work-ID allocation. No source commit/push was performed.
