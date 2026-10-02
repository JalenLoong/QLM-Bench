---
id: DATA-012
type: exec-plan
status: active
namespace: adaptation-v2
source_map: []
---
# Incremental catalogue and typed publication staging

## Purpose and scope

Incremental catalogue and typed publication staging.

## Context and milestones

Follow the approved P0/A/B/C stage ordering; peer registry writes are serialized by WAM v2 authority.

## Progress (timestamped)

- [x] 2026-10-03: baseline verified; independent worktree created; Work ID reserved.
- [ ] Implementation and affected checks.
- [ ] Required actual-artifact/runtime evidence and handoff.

- [x] 2026-10-03: public HF read-only check observed revision 05b09b89225759382e28bc3dc586f1cfb755a997 and 2293 files; downloaded only release index/small manifests with authentication disabled. No remote mutation.
- [x] 2026-10-03: three-task fixed-release catalogue and DatasetRef manifest SHA256 binding implemented. Push Box first v2/v3 pin remains 4b5e0ed9aa04cbc1143774798f63171b27d838a7; Lift/Press remain publication_only for those first runs.
- [x] 2026-10-03: actual 50/10/10 episode local publication payloads pass installed-core Canonical validation with check_media=False and real first/last Parquet reads; manifests, membership and whole-episode splits verified.
- [x] 2026-10-03: typed asset/case/result/catalogue local staging reuses original inventory/hash/resume/readback core. Case schema uses EvalCase; engineering result fixtures are rejected. No source snapshots, cases or results are promoted to a formal benchmark without actual evidence.
- [x] 2026-10-03: CPU Raw conversion, unchanged-spec validation, byte-preserving merge and local replay exposed under qlm data; collect CLI dispatch is lazy and simulator-owned.
- [x] 2026-10-03: schema/publisher tests recorded in core-publication-tests.log; actual HF publication, formal benchmark results and learned-policy closed loop remain not_run.

- [x] 2026-10-03: 141 relevant CPU checks passed; four LeRobot reads initially hit the sandbox read-only default HF cache, then all four passed with an explicit writable HF_DATASETS_CACHE. Original failure and retry logs remain separate; no source change was needed.
- [x] 2026-10-03: final owned core component source identity and all frozen spec/resource hashes passed in `core-source-identity-check.json`; new source is dirty/uncommitted and is not a formal benchmark source release.

- [x] 2026-10-03: Independent review added pinned Canonical payload verification: remote fixed-revision inventory SHA256 0d514d9709f124fd0fab915f80e4d4afc4d7c41e71da29b1150d23bc7f7579c0, byte-identical with both historical download and original DATA006 collection.
- [x] 2026-10-03: WAM v2/v3 bindings now verify full exact Canonical membership/bytes before asserting original training identity; metadata-only roots, forged inventory, changed/missing/extra files and escapes reject. Current payload verifies456 files/434899964 bytes.
- [x] 2026-10-03: Result staging applies staged-state admission while preserving original run-manifest bytes; exact code/protocol source hashes required. Verified case snapshots must bind the declared committed QLM source identity. Asset copied payload reverified after staging.

- [x] 2026-10-03: final independent review completed:24 core case/inventory checks and WAM adapter10/11 checks passed. Verified case evidence must match per-case provenance and occur in frozen actual validation material; staged source snapshots and result admission strengthened. Final owned code fingerprints are in `core-final-review-source-hashes.json`; root constructs the final wheel after remaining shared sources settle.

- [x] 2026-10-03: actual three-manifest catalogue staging exposed and fixed UID-list/count split comparison; strengthened exact episode/split membership checks.28 core tests pass, including70-row positive and duplicate/count negative cases.
- [x] 2026-10-03: local candidate stages six metadata/card files (67,922 bytes),70 unique release/episode pairs, task counts50/10/10. Parent HF commit remains05b09b89225759382e28bc3dc586f1cfb755a997;2,292 original remote files are protected, with only README proposed as an existing-path replacement.
- [x] 2026-10-03: releases.json SHA68578dc263206b054034e140c38ca37e02a29e78338fa4aecaf7a39207c7297c and .gitattributes SHAe39a562f1f84260887df7abda3d4577665f22182fee524f621d85dc14954c992 were read at the actual fixed HEAD and remain excluded from candidate writes. Original manifests/payloads/splits and WAM4b5e0... input pin remain unchanged.
- [x] 2026-10-03: candidate card introduces QLM tasks/resources/status first; preserves unknown dataset license and historical first-WAM-use declarations. Assets/cases/results are not selected. Source snapshots/publication identities remain pending root final source identity; no old HEAD is claimed as committed refactor source.
- [x] A→B gate: root accepted actual public-collection-diagnostic-r4, with32actions/33boundaries and full Raw/Canonical/media validation; eligible_demonstration=false.

## Discoveries and decision log

User approved independent refactoring branches, in-place future GitHub rename, full retired-capability cleanup, and independent v3 category numbering.

## Validation and not_run

Baseline and check logs live in workspace `runs/audit/qlm-refactor-20261003/`: `hf-readonly-state.json`, `hf-release-identities.json`, `resource-dependency-readback.json`, `cpu-data-readback.json`, `cpu-canonical-validation.json`, and `core-publication-tests.log`. Remote publication, training, learned-policy closed loop and formal benchmark score are not_run/not_required. W&B not_run for local CPU checks.

## Recovery

Resume from this branch, registry, paired ChangeSpec and audit manifests; do not depend on chat history.

## Outcomes and retrospective

Active: evidence gates have not yet been completed.

## Local acceptance and remaining cutover — 2026-10-03

Local implementation and CPU/artifact/runtime acceptance have passed. The final
public collection diagnostic has32actions/33boundaries and full Raw/Canonical/media
validation, with eligible_demonstration=false. Final wheel is hash-locked in both
WAM branches. HF metadata candidate preserves70existing episode identities/splits.
This work remains active for the explicit GitHub/HF cutover and final committed
source snapshots: reviewed source commit/merge/push, repository rename and HF
metadata publication have not been executed. No assets/cases/results or new
demonstrations are silently added. Preserve all failed attempt logs.

## Authorized cutover — 2026-10-03

The user explicitly authorized the reviewed source commit/merge/push, in-place
JalenLoong/RAMBO_Data to JalenLoong/QLM-Bench rename, and the exact metadata/card/
catalogue/compatibility/source-snapshot HF inventory. No default-branch/visibility
change, old payload rewrite, assets/cases/results upload, training or AMD access.
Authorization and execution receipts are in workspace runs/audit/qlm-cutover-20261003.
Source snapshots must bind the actual new committed source; published state remains
pending until exact branch/Hub readback passes.
