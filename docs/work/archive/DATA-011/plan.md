---
id: DATA-011
type: exec-plan
status: completed
source_map: []
---
# Publish Lift Basket and Press Button without extending first adaptation inputs

The user explicitly authorized usable DATA-009 local-ten and DATA-010 demonstrations,
related Raw/Canonical/evidence/replay publication to QLM-Bench, integration of their
RAMBO v2 source, and WAM adaptation v2 documentation/governance commits and pushes.
WAM code/scripts/configs and all WAM v3 files stay unchanged. No collection, model
cache/normalizer generation, training, model evaluation or AMD access is authorized.

First adaptation v2/v3 training, validation and evaluation remain Push Box only:
QLM-Bench revision 4b5e0ed9aa04cbc1143774798f63171b27d838a7,
release DATA-006-20260916T075451Z, 50 episodes, split 40/5/5.
New releases retain independent 8/1/1 metadata and are publication_only for current
adaptation use. Publication completion is not TRAIN/EVAL dataset admission.

Execution: preserve baselines; integrate accepted source; validate data and boundaries;
upload immutable payloads; fixed-revision integrity readback; publish catalogue;
commit/push RAMBO then WAM v2; verify remote SHA and preserve historical worktrees.
Pilots/failures/interruption/quarantine/model caches/weights/asset source are excluded.
Original source and acceptance identities remain historical and immutable.

Evidence: workspace runs/audit/v2/DATA-011. Source snapshots, published-data revision,
first-training-evaluation revision and source push receipts are recorded separately.

## Acceptance and source publication

Both staged and fixed-revision downloaded Canonical releases passed full media,
timestamps, terminal and independent LeRobot/WAM reader integrity checks. All original
Push Box remote files, metadata bytes and historical index entry are unchanged.
RAMBO CPU suite: 250 passed / 1 skipped / 1 CUDA deselected. WAM make check: 96 passed /
20 optional-fixture skips; host CPU/Gloo checks passed after sandbox socket rejection.
Import boundaries and shared governance pass. RAMBO docs-check retains exactly two
upstream broken overview links to v2 pages missing from the active WAM v3 checkout;
no new failures or unrelated repairs. Scope identity rejection checks pass, WAM v2
code/scripts/configs are unchanged and every WAM v3 tracked/untracked file plus HEAD
and working-tree status match the preserved baseline.

The user authorized ordinary fast-forward pushes to RAMBO's existing v2 target and
both WAM v2 targets. Commit hashes and actual remote readback are recorded after push
in workspace runs/audit/v2/DATA-011/github-publication.json; document acceptance does
not substitute for that external receipt. Original local-only collection receipts
are preserved and do not describe this later publication. No GPU/AMD jobs, collection,
model cache/normalization fitting or model evaluation occurred.

Published dataset revision: `05b09b89225759382e28bc3dc586f1cfb755a997`. First training/evaluation revision: `4b5e0ed9aa04cbc1143774798f63171b27d838a7` (Push Box only).
