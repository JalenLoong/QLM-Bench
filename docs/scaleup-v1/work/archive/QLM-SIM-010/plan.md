---
id: QLM-SIM-010
type: exec-plan
status: completed
source_map: []
---

# Adopt accepted STEP rendering LOD and retire obsolete generated payloads

User selects v1-step-rig-lod-a02 for every subsequent MuJoCo rollout, collection
and evaluation. Partner works are QLM-SIM-010 and v3/DOC-006. Centralize default
three-task resource selection and pin actual accepted identities; preserve explicit
historical replay and fail closed on missing/mismatched LOD. Keep camera pose/FoV/
resolution, render quality, mass/inertia and collision unchanged. No implicit engine
fallback or production admission follows from selecting this rendering mesh.

The same request explicitly authorizes deleting local MuJoCo-generated payloads
using obsolete procedural/full STEP rigs. Inventory per-file provenance, hash and
size before deletion; never delete original STEP, any asset/model version, CAD
intermediates, source, checkpoints, encoders, prompt embeddings or Isaac reference
data. Retain receipts/manifests/scalars and compact mechanical/visual comparisons;
remove obsolete Raw/Canonical, runtime RGB/state and dependent model-input caches.
Preserve accepted LOD-generated payloads. Add an eviction record without rewriting
historical attempt identities. No remote, training, formal demonstrations, commit,
push or publication belongs to this work.

Acceptance: all current entrypoints resolve pinned LOD; CPU import boundary remains
clean; actual three-task resource checks and unchanged MJCF/compiled camera/physics
settings; exact deletion readback and protected-resource hashes; current consumer
and workspace docs describe the new defaults and evicted historical payloads.
Evidence: workspace runs/audit/mujoco-lod-default-cleanup-20261013-v1/.

## Progress
- [x] Default routing and identity gates.
- [x] Inventory and payload eviction.
- [x] Actual resource checks, protected-file readback and documentation.

## Actual completion

All shared defaults select accepted LOD a02 with pinned resources. Actual three-task
resource hashes, compiled camera/physics/render-quality settings and default CLI case
preparation pass, without physics stepping. 18 affected tests pass; three unrelated
runtime gates are skipped. Exact cleanup deletes 1901 files / 565444492 bytes;
11805 protected hashes remain unchanged. Old-case identity mismatch rejects before
runtime construction. Governed docs/import checks pass. Original settings/resources
and all historical numerical receipts are retained.

No new WAM rollout, GPU benchmark, formal demonstrations, model training, AMD,
source commit/push or publication. Current source changes remain local.

Final cache sweep additionally removes three original-scene Canonical Arrow caches
from the shared datasets cache, verified by their dataset_info source paths. Total
eviction is1904files /565587004bytes. Source/model Hub entries remain untouched.
The matrix launcher explicitly binds its own checkout, and source snapshots include
JSON configuration/pins alongside Python. Exact supplement receipt is in the same
workspace evidence root.
