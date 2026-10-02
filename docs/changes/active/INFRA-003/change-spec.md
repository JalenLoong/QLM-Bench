---
id: INFRA-003
type: change
status: active
namespace: adaptation-v2
source_map: []
---
# Independent QLM package, resources and capability cleanup

## Intent and observable behavior

Independent QLM package, resources and capability cleanup; implementation follows the user-approved QLM refactoring plan.

## Compatibility and non-goals

Preserve native9/force-zero, controller and task semantics, immutable schemas, published data and WAM inputs. No training, new demonstrations, AMD access or remote publication.

## Evidence threshold and acceptance scenarios

Governance and import checks, affected unit/integration tests, actual artifact checks and required runtime regression are recorded separately.

## Migration and rollback

Work in the dedicated branch/worktree. Keep source artifacts immutable and record source-to-target mapping. Revert reviewed changes without rewriting history.

## Authorized cutover — 2026-10-03

The user explicitly authorized the reviewed source commit/merge/push, in-place
JalenLoong/RAMBO_Data to JalenLoong/QLM-Bench rename, and the exact metadata/card/
catalogue/compatibility/source-snapshot HF inventory. No default-branch/visibility
change, old payload rewrite, assets/cases/results upload, training or AMD access.
Authorization and execution receipts are in workspace runs/audit/qlm-cutover-20261003.
Source snapshots must bind the actual new committed source; published state remains
pending until exact branch/Hub readback passes.
