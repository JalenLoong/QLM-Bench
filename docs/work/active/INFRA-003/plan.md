---
id: INFRA-003
type: exec-plan
status: active
namespace: adaptation-v2
source_map: []
---
# Independent QLM package, resources and capability cleanup

## Purpose and scope

Independent QLM package, resources and capability cleanup.

## Context and milestones

Follow the approved P0/A/B/C stage ordering; peer registry writes are serialized by WAM v2 authority.

## Progress (timestamped)

- [x] 2026-10-03: baseline verified; independent worktree created; Work ID reserved.
- [ ] Implementation and affected checks.
- [ ] Required actual-artifact/runtime evidence and handoff.

- [x] 2026-10-03: CPU package 0.1.0 and independent Python >=3.10 wheel layout implemented; no base dependencies or simulator/model import on discovery.
- [x] 2026-10-03: exact frozen contracts/dataset specs retained; RAMBO compatibility imports now route to the installed CPU authority. Setup60 no longer requires or installs a WAM checkout.
- [x] 2026-10-03: 14 resource manifests generated from reviewed source USD dependencies/hashes, source/runtime attribution and authored physical properties. Controller identity is retained at the existing fixed model revision; no mirror.
- [x] 2026-10-03: OASIS gltf/pbr.mdl runtime shader dependency remains explicitly unresolved by plain USD dependency inspection; basket license remains unverified. Push Box README license declaration remains pending clarification. Both are ineligible for asset publication.
- [x] 2026-10-03: resource sources and large payloads remain unchanged; actual reset/collection regression and public installation evidence are separate required gates.

- [x] 2026-10-03: 141 relevant CPU checks passed; four LeRobot reads initially hit the sandbox read-only default HF cache, then all four passed with an explicit writable HF_DATASETS_CACHE. Original failure and retry logs remain separate; no source change was needed.
- [x] 2026-10-03: final owned core component source identity and all frozen spec/resource hashes passed in `core-source-identity-check.json`; new source is dirty/uncommitted and is not a formal benchmark source release.

- [x] 2026-10-03: Independent CPU data setup and four-package lock added; new env qlm-data-py310 contains only QLM/NumPy/Pillow/PyArrow/PyAV and no Torch/LeRobot/datasets/Isaac/WAM. Existing simulator/model environments remain unchanged.
- [x] 2026-10-03: Production CPU converter imports require no historical DATA approval gates; collection passes a separate --data-python and retains failed packaging evidence.

- [x] 2026-10-03: final independent review completed:24 core case/inventory checks and WAM adapter10/11 checks passed. Verified case evidence must match per-case provenance and occur in frozen actual validation material; staged source snapshots and result admission strengthened. Final owned code fingerprints are in `core-final-review-source-hashes.json`; root constructs the final wheel after remaining shared sources settle.

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
