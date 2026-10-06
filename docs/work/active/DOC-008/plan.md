---
id: DOC-008
type: exec-plan
status: active
source_map: []
---
# Authorized inference source publication

## Scope and authorization
On2026-10-07 the user explicitly requested commit/push of the pending changes,
following agreement to fast-forward WAM v2/v3 into their own adaptation branches
and QLM into its existing synthesis branch. No enduring inference branch is required.
The user explicitly defers the known reset velocity-cache issue; retain its limitation.
Publish code/config/tests/governance only; workspace evidence/media/models stay local.

## Progress
- [x] Confirm all pending diffs and clean destination checkouts.
- [x] Inspect current Work IDs and reserve this publication record.
- [ ] Update source-install/serving routing for integrated branches.
- [ ] Run required checks and make reviewable commits with registered Work IDs.
- [ ] Fast-forward each destination and push explicit refs to all five GitHub targets.
- [ ] Read back exact remote HEADs and record completion evidence.

## Decisions / Recovery
WAM v2/v3 are independently committed and never merged with each other. QLM returns
to synthesis/v2_9D-action_ego+task-centric_camera. Preserve all original training
identities, generic governance bytes and audit attempts. Use ordinary fast-forward
pushes; do not force, rewrite history or upload new artifacts. In case of concurrent
remote changes stop that mutation, inspect the new state and reconcile normally.
Source publication acceptance is independent of the deferred reset repair.
