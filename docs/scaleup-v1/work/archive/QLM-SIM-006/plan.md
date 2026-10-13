---
id: QLM-SIM-006
type: exec-plan
status: completed
source_map: []
---

# Collaborator task-camera rig in MuJoCo

User requests replacing the current task-centric camera support with the version
identified in WAM-Policy_Ethan, and comparing before/after camera pose and FoV.
Collaborator package identifies QLM commit ed8e17f and source SHA
49f25a5319a8301d0f1d54144d99e969ac67ad385ae4fb2cb68db3d3e8473655.
Its source body is recovered byte-identically from local Git, not inferred from
a CAD file or the current newer source. Five cuboids and the associated camera
mount/intrinsics are consumed directly from that verified programmatic definition.

Keep all a03 historical packs and recordings immutable. Create independently
versioned original-task packs and update current routing only after acceptance.
No camera/action/data semantics or robot/asset physics is intentionally changed.
The support stays visual-only, massless and collision-free. If an actual mount/FoV
contract difference appears, report it before promoting the new profile.

Acceptance: source provenance matches the collaborator package; all three packs
compile and pass resource closure; original camera local/world pose and FoV are
compared at identical static and moved robot states; non-rig geometry/physics and
other cameras stay identical; actual OSMesa same-state RGB/Observer comparison
records camera obstruction and verifies non-stepping rendering. Bind future live
engineering routing explicitly to the new profile; old media is historical.

Evidence: workspace runs/audit/ethan-camera-rig-replacement-20261013-v1/.
This work excludes model/RAMBO training, demonstrations, AMD, source commit/push
and external publication. WAM source/weights need no modification for this rig.

## Progress
- [x] Inspect collaborator package inventory and original source identity.
- [x] Reserve Work-ID and implement verified programmatic rig conversion.
- [x] Build three new resource profiles and measure camera/physics differences.
- [x] Capture actual paired RGB at identical static/moved states.
- [x] Update current routing/docs; run affected checks and archive evidence.

## Discovery
The current a03 support was exported from the same five-cuboid design. Source
provenance differs, and float32 USD transforms can differ from source double
precision. Zero visual or calibration change is a valid measured result.

## Completed local evidence — 2026-10-13

build-a01 preserves byte-identical source recovered from the collaborator package
inventories. Three new portable resource packs compile and verify their manifests.
compare-a03 passes all three tasks at reset and translated/rotated/articulated
fixtures: camera local/world pose and FoV deltas0; all three RGB views pixel-identical.
256 arrays/task checked; support float precision and compiler geometry-normalization
differences are explicitly reported (dof_length up to2.21e-9), not hidden as exact
model equality. Actual mass/inertia/collision and non-rig geometry stay identical.

Affected resource/public-backend tests16passed. Exact-source tamper guard passes.
Current model paths and live_matrix suffix now select v1-ethan-rig-a01; explicit
v1-a03 retains historical replay. Read decisions/ethan-camera-rig.md for source,
unchanged calibration and all limits. Final governance/docs/import/whitespace
receipts, original-resource identity verification and report are under workspace
runs/audit/ethan-camera-rig-replacement-20261013-v1/completion.json.

compare-a01 launcher error and compare-a02 strict dof_length assertion remain
preserved; the final comparison did not relax camera or RGB admission thresholds.
No GPU dynamics,real WAM rollout,training,AMD or publication was performed by this
camera-only work. Source remains local and uncommitted.
