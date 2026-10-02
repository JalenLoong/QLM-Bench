---
id: DATA-013
type: change
status: completed
namespace: adaptation-v2
source_map: []
---
# Pinned WAM v2 QLM interface adaptation

## Intent and observable behavior

Pinned WAM v2 QLM interface adaptation; implementation follows the user-approved QLM refactoring plan.

## Compatibility and non-goals

Preserve native9/force-zero, controller and task semantics, immutable schemas, published data and WAM inputs. No training, new demonstrations, AMD access or remote publication.

## Evidence threshold and acceptance scenarios

Governance and import checks, affected unit/integration tests, actual artifact checks and required runtime regression are recorded separately.

## Migration and rollback

Work in the dedicated branch/worktree. Keep source artifacts immutable and record source-to-target mapping. Revert reviewed changes without rewriting history.

## Final local acceptance — 2026-10-03

WAM v2 fixed50-episode model-facing inputs match baseline exactly; payload trust anchor verifies456files, normalizer/model/training source is unchanged and checks pass.
Evidence: versioned workspace runs/audit/qlm-refactor-20261003. No new usable
demonstrations, training experiment, AMD connection, remote publication or model
artifact modification. Source commits/merge/push remain pending review authorization.
