---
id: DATA-012
type: change
status: completed
namespace: adaptation-v2
source_map: []
---
# Incremental catalogue and typed publication staging

## Intent and observable behavior

Incremental catalogue and typed publication staging; implementation follows the user-approved QLM refactoring plan.

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

## Authorized cutover completed — 2026-10-03

GitHub repository1350481012 is now JalenLoong/QLM-Bench, preserving main/public
and complete history. Reviewed source was committed and fast-forward merged/pushed
to the corresponding synthesis and independent WAM v2/v3 branches. The reviewed CPU
wheel is available in the QLM wheels directory with unchanged7efc271a SHA256 lock.
HF metadata/card/catalogue/compatibility/snapshots published and fixed-revision
readback passed at856dc054a58307ea30ce85ebe1e5bcfcb57308c0. Source snapshots bind
actual code commitb9be357048ae350dd006eef9c95b4c84b7ec4e45 and clean source tree.
2292 prior remote objects and all existing release/attribute/payload identities are
unchanged. No new assets/cases/results/weights/demos, training or AMD operations.
Actual receipts: workspace runs/audit/qlm-cutover-20261003. Governance closure follows
the verified publication; historical local acceptance/pending statements remain dated.
