---
id: INFRA-004
type: change
status: completed
namespace: adaptation-v2
source_map: []
---
# Local QLM checkout path migration

## Intent and authorization

The user authorizes local repos/RAMBO_Data to repos/QLM-Bench migration on 2026-10-07,
with current paths, Git pointers and installed metadata adapted. No old-path symlink.
This is not source publication or a feature change.

## Compatibility and non-goals

Keep historical RAMBO_Data registry/schema identity, archives, manifests, receipts,
model/data/controller/asset hashes, public contracts and package versions unchanged.
Keep all other worktrees and the existing QLM data environment bindings. No commit,
push, remote operation, reset repair, training, collection or simulator rollout.

## Acceptance

New checkout exists and old path is absent. Git HEAD/branch/remotes and all linked
worktrees remain usable. Bare simulator imports and the wrapper resolve the moved
RAMBO/CRL2 source. Current paths and docs resolve; archived cross-repo links use a
restricted documentation-only relocation mapping. Docs/governance/import checks
and affected CPU tests pass. Immutable baseline hashes and package versions match.

## Migration and rollback

Back up edited metadata before moving the directory, repair Git pointers, then
change only reviewed live-path references. On failure restore this task's edits,
move the checkout back and repair pointers; retain the failed attempt receipt.
Evidence: workspace runs/audit/qlm-local-rename-20261007/.

## Acceptance evidence — 2026-10-07

Directory/Git/installed-metadata checks and affected CPU tests pass. Original
source/record hashes and versions are preserved outside the reviewed allowlist.
The sandbox-only CPU/Gloo socket failure passed on an isolated outside-sandbox
retry. Final closure checks and receipt are in workspace
runs/audit/qlm-local-rename-20261007/. This work is locally completed and uncommitted.

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
