---
id: CURRENT-RESET-SOURCE-PUBLICATION
type: current
status: accepted
related_work: [DOC-009]
source_map: []
---
# Verified reset source publication

The user authorized commit/push on2026-10-07. The reviewed reset source and related
consumer/governance documents were ordinary fast-forward pushed to all five
existing GitHub branch targets and exact remote readback passed. The pending
INFRA-005/shared-v2 and INFRA-001/v3 cleanup routing records were included as
registry prerequisites. Workspace evidence/media/data/models/assets remain local.

## Immutable repaired QLM source

Use QLM commit `7ff0480b2564683eb9b5f548e317f865cd3f56d9` from
[JalenLoong/QLM-Bench](https://github.com/JalenLoong/QLM-Bench/commit/7ff0480b2564683eb9b5f548e317f865cd3f56d9)
for current live execution with SIM-003. Subsequent publication bookkeeping commits
change documents only; this is the immutable implementation identity.

```bash
git clone --branch synthesis/v2_9D-action_ego+task-centric_camera \
  https://github.com/JalenLoong/QLM-Bench.git QLM-Bench
git -C QLM-Bench checkout 7ff0480b2564683eb9b5f548e317f865cd3f56d9
python -m pip install -e './QLM-Bench[live]'
```

The earlier821105c1a490c068745ee93062229473b7aadf34 pin remains the historical
DOC-008/INFER source identity and does not contain reset repair. First training
inputs, model/normalizer/controller/camera/physics identities remain unchanged.
[Reset acceptance](reset-state-freshness.md) covers21 actual reset checks and
original v3 consumer readback; historical70 data/caches and6/10 versus5/10
outcomes remain unchanged. No new demonstrations, model rollout, training, AMD,
HF/W&B upload or formal benchmark is performed by source publication.

## Source commits and verification

QLM implementation/doc source: `7ff0480b2564683eb9b5f548e317f865cd3f56d9`. WAM v2 consumer/governance source:
`9e0b04200f59275dba0b349a07d40784de8faeb4`. WAM v3 consumer/governance source:
`b742018dc26a0e873f374b590b825cefdb311293`. Each WAM branch was independently pushed to
AIGeeksGroup and JalenLoong, with no cross-version merge. All pushes are ordinary
fast-forward updates to the existing adaptation/synthesis branches; main is unchanged.

Exact first remote verification and final bookkeeping heads are in workspace
runs/audit/reset-state-freshness-publication-20261007/first-readback.json and
completion.json. Original local reset/cleanup receipts retain their original scope.
