---
id: QLM-DOC-002
type: change
status: completed
source_map: []
---

# P0–P2 independent-branch source publication — 2026-10-13

The user explicitly authorizes committing and pushing all P0–P2 MuJoCo source
changes in both repositories, each on its own independent MuJoCo branch. This
supersedes prior local-only publication restrictions only for this source batch.

QLM publishes migration/mujoco-foundation to JalenLoong/QLM-Bench. WAM publishes
adaptation/v3-mujoco-sft to its existing AIGeeksGroup and JalenLoong WAM-Policy
targets. No merge into Isaac/main/adaptation branches and no force overwrite.
Cross-repository partners are QLM-DOC-002 and v3/DOC-008.

Scope includes RAMBOCore/Isaac adapter, Native/CUDA physics, Native rendering,
original three-task engineering/recording/evaluation, STEP/LOD generation tools,
default model pins, WAM engineering prompt/readback/service, tests, dependencies,
accepted decisions and paired P0–P2 records. Keep actual P3 code/review/active work
and local P3-only routing out of the published tree; preserve them in the worktree.
The inherited QLM scale-up foundation is the declared source baseline, not P3
MuJoCo task acceptance. Existing assets, CAD, videos, datasets, weights, encoders,
audit payloads, workspace environment/lock and prior immutable receipts stay local.
Resource pins and import/build tools are published; external resource licensing
and delivery remain a P6 gate. This is source publication, not a portable resource
release or new simulator/AMD/SFT/task-success acceptance.

## Acceptance

Verify the exact staged tree rather than the mixed local worktree. Run docs,
governance, import boundaries and affected CPU tests; WAM runs make check. Compare
P0–P2 runtime source to retained closeout snapshots, retain actual hardware receipts,
and do not rerun full model/physics experiments for unchanged source. Review staged
paths, file sizes and content; no P3 or generated resource/media/model payloads.
Create ordinary commits with registered Work IDs, push exact named branches and
read back each remote head. Archive paired records only after initial push/readback
passes, then publish the closing documentation commit and verify again.

## Evidence and recovery

Workspace runs/audit/mujoco-p0-p2-source-publication-20261013-v1/ retains before
copies/hashes, selected and excluded inventories, staged source exports, validation
logs and exact GitHub readback. Never reset dirty checkouts or rewrite old receipts.
If a remote branch exists unexpectedly, inspect ancestry and stop that target on a
non-fast-forward conflict; do not force push. No new tasks/data/training/AMD/HF
publication is authorized by this operation.

## Pre-publication validation

Validation uses isolated exports of the exact staged tree. WAM make check passes
57 tests; QLM passes108 tests with12 explicit-runtime skips and54 related RAMBO
tests with2 skips. Actual default resource pins pass. Docs/governance/import and
staged whitespace checks pass. Initial sandbox socket failures are retained and
unchanged localhost RPC/Gloo tests pass outside the sandbox. The frozen shared-v2
peer declaration matches f8eef86bb9ffe15a493b738402f32a56bd9ab527; the live peer's
later EVAL-003 is outside this branch and is preserved without registry rewriting.

All published code matches the P0–P2 source inventory; two code files only remove
a redundant final blank line. No behavioral source repair or new runtime acceptance
is introduced here. Eighteen P3-only paths and four shared-file P3 portions remain
local. No generated resource/data/model/media payload is selected. The initial
implementation commit is ready; exact remote readback remains pending.

## Actual initial source publication

Implementation commit `5d3c3b7c5d923580e35d4c531b96be6cdf758503` is published on
`migration/mujoco-foundation`. Exact git ls-remote readback passes for:

- `git@github.com:JalenLoong/QLM-Bench.git`

The selected source contains P0–P2 only. Original Isaac/main branches remain
outside all push refspecs; no merge/force push, new asset/data/model/media upload
or P3 publication was performed. First QLM push encountered a missing git-lfs
PATH entry; retry uses the existing workspace binary without bypassing hooks or
installing/rebinding dependencies. Historical LFS paths are unchanged.

The paired records are archived after initial source/readback acceptance. The
closing documentation commit and its exact remote heads are recorded in the
versioned workspace publication receipt; this page pins the implementation SHA
rather than attempting to embed its own future commit. No new hardware gate is
claimed. P6 still freezes the eventual ten-task source/resource/admin bundle.
