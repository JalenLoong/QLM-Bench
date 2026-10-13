---
id: QLM-MUJOCO-DEFAULT-RIG
type: guide
status: accepted
related_work: [QLM-SIM-010]
source_map:
  - src/qlm_bench/backends/mujoco/defaults.py
  - src/qlm_bench/backends/mujoco/default-models.json
  - src/qlm_bench/backends/factory.py
  - scripts/mujoco/live_matrix.py
---

# Default STEP rendering LOD and obsolete payload eviction

The later user-authorized real-model replay under QLM-SIM-011 completes six actual
default-LOD episodes and preserves18original RGB videos. See the
[current runtime evidence](../mujoco-foundation.md). No-new-rollout statements below
describe QLM-SIM-010's original selection/cleanup scope.

On 2026-10-13 the user selected `v1-step-rig-lod-a02` as the default for subsequent
MuJoCo rollout, data synthesis and evaluation. This supersedes full STEP routing
under QLM-SIM-007/009. [LOD acceptance](step-rig-rendering-lod.md) is unchanged;
no new optical, physical or render-quality calibration is introduced.

`src/qlm_bench/backends/mujoco/default-models.json` is the shared model-set authority,
pinning three complete identities from the accepted LOD receipt. Packs are workspace
`assets/mujoco/original-{task}-v1-step-rig-lod-a02/`. Public `create_runtime`, `qlm live`,
`qlm collect`, `qlm evaluate` and `live_matrix.py` use this selection. Supply `--task`
and `--model-root` (or `QLM_MUJOCO_MODEL_ROOT`) instead of a model file. The workspace
exports that resource root; installed wheels contain the selector/pins, not assets.
Missing LOD packs or changed accepted identities fail closed; no old-rig fallback.
Run source snapshots retain JSON configuration alongside Python implementation,
including the default model set. Collection accepts `--work-id` for later work.

Explicit `--model` or matrix `--model-profile-suffix` remains a historical replay/
diagnostic override. Existing EvalCases keep their original resource identity:
an old case with the new default is rejected by the reconstruction gate. Create a
new LOD case; never rewrite a historical case. Low-level migration/comparison tools
retain explicit reference paths. Future tasks require accepted LOD profiles and
pins; the seven planned tasks are not silently enabled.

After explicitly binding the MuJoCo source in `PYTHONPATH`:

```bash
python -m qlm_bench.cli evaluate prepare --backend mjwarp --task push_box \
  --model-root "$QLM_MUJOCO_MODEL_ROOT" --output NEW_CASE.json
```

Camera pose/FoV/resolution/preprocessing, render/encoding quality, robot/support
mass/inertia and collision are unchanged. Native OSMesa remains admitted; EGL retains
its per-task limitations. Native/CUDA physics and ROCm pending validation are unchanged.
Collection still requires `--diagnostic-only` until formal pilot/release admission.
This selection does not establish production throughput or learned-policy SR.

## Explicit local cleanup exception

The same request authorizes removing obsolete local MuJoCo-generated RGB,
state/trajectory, Raw/Canonical and derived VAE/Arrow payloads. This is the narrow
exception to earlier payload-retention statements. Original STEP, every full/old/
LOD asset/model version, CAD intermediates, source snapshots, receipts, manifests,
scalar results, compact mechanical/visual comparisons, Isaac references, prompt
embeddings and weights/encoders remain. LOD evidence/data is retained.

Exact inventory, before/after hashes and receipt are in workspace
`runs/audit/mujoco-lod-default-cleanup-20261013-v1/`. Affected audit roots contain
`PAYLOADS_EVICTED.md`. Old manifests describe original runs; removed paths no longer
assert local presence/readback. Previous WAM engineering acceptance remains historical;
this change does not claim a new LOD WAM rollout. No formal demonstrations, training,
AMD, remote mutation, source commit/push or publication accompanies it.
