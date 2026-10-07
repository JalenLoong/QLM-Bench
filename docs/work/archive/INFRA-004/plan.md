---
id: INFRA-004
type: exec-plan
status: completed
namespace: adaptation-v2
source_map: []
---
# Local QLM checkout path migration

## Purpose and scope

Execute the user-approved path migration only. Shared-v2 authority remains WAM v2;
RAMBO_Data remains the registry participant alias for QLM-Bench.

## Progress

- [x] 2026-10-07: preflight clean states, Git/source/hash and installed metadata baseline saved.
- [x] 2026-10-07: INFRA-004 reserved and paired records created.
- [x] Move main checkout and repair every linked Git pointer.
- [x] Adapt reviewed current routing/config/docs/install metadata.
- [x] Pass scoped checks and compare immutable baseline.
- [x] Archive paired records; completion receipt follows final closure checks.

## Validation and not_run

Evidence: workspace runs/audit/qlm-local-rename-20261007/.
CPU/path/metadata checks only. Isaac rollout, GPU evaluation, W&B, training, remote
access/publication, commit and push are not_run and outside scope.

## Recovery

Use baseline.json and backup/ to restore exact prior metadata and tracked files.
Historical records and unmodified source snapshots are never rewritten.

## Actual outcome — 2026-10-07

The main checkout is repos/QLM-Bench with no old-path symlink. All five QLM Git
checkout identities and pointers are preserved/repaired. Bare RAMBO/CRL2 imports
resolve the moved source; installed finder/direct_url/RECORD edits retain package
versions and the data environments retain their existing bindings.

Both docs/governance/import checks pass; five archive-path tests and ten existing
wrapper/static/diagnostic tests pass. WAM v2 make check passed compilation/docs/
imports and129 tests, with20 fixture skips; one existing CPU/Gloo test initially
failed because the sandbox prohibited loopback sockets, then passed alone outside
the sandbox with the same interpreter. The initial failure and retry are retained.
These existing CPU tests use synthetic tiny-model fixtures, not formal training.

Integrity checks compare3989 tracked source files and699 historical records. Only
the reviewed path/governance files differ; original archives/specs/receipts, v3
source, other QLM worktree sources, asset/controller hashes, package versions and
historical lock fields are unchanged. No simulator rollout, feature/reset repair,
production model/data change, remote operation, commit or push was performed.

Evidence: workspace runs/audit/qlm-local-rename-20261007/; final completion.json
records closure checks and the exact local change inventory.

## Later source-publication authorization — 2026-10-07

After the completed local-only migration, the user explicitly authorized commit
and push of this work's repo-internal source, tests, docs and governance changes.
This later authorization supersedes the preceding publication exclusion only for
these changes: QLM synthesis/v2_9D-action_ego+task-centric_camera at JalenLoong,
and WAM adaptation/v2_9D-action_ego+task-centric_camera at both AIGeeksGroup
and JalenLoong. No v3 branch, workspace/environment metadata or audit payload is
published. Historical local-stage receipts and not_run statements remain unchanged.

Use ordinary fast-forward pushes. Actual commit identities and exact remote
readback are recorded separately in workspace
runs/audit/qlm-local-rename-publication-20261007/. Publication is accepted only
after each declared remote branch matches the committed source.
