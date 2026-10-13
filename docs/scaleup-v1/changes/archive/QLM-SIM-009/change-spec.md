---
id: QLM-SIM-009
type: change
status: completed
source_map: []
---

# Rendering LOD and three-way Observer comparison

User explicitly requests a lighter STEP support rendering LOD, preserving outline,
diagonal brace,mount andcamera-adjacent structure,without camera pose,FoV,resolution,
render quality,mass/collision change. Compare earliest MuJoCo procedural rig,full
STEP-derived support andLOD in actual Observer RGB. Earliest restored black support
is v1-a03 (procedural variant v1-ethan-rig-a01 is essentially identical).

Create separately versioned CAD-derivedLOD and three-task resource packs. All old
resources andoriginal STEP remain immutable. Prefer coarser CAD tessellation without
removing source faces/features; protect camera-area precision. Reuse exactly the
accepted CAD→base transform andsource colors. Do not replace shape with boxes/hulls.

Acceptance: meaningful polygon reduction; all selected source faces retained;
outline/mount/camera-near geometric error checked; same-state actual RGB/rig
silhouette comparison;policycamera/root/physics/light/quality invariants and
resource closure;actual three-column original Observer RGB andsame-ROI magnification
with identical camera. Check shortCUDA compatibility andboundedrender speed.
Do not silently relax camera/physics/RGB gates if a candidate fails.

Evidence: workspace runs/audit/step-rig-lod-20261013-v1/.
NoWAM/SFT/AMD/formaldemos/commit/push/publication. This is engineering visualLOD.

## Actual completion
Accepted hybridLOD has37224triangles vs110683fullSTEP,66.37% reduction. Twelve
camera-near CADfaces retain original tessellation;allsource faces/features and
frame placement/colors are preserved. Firstcoarse candidates failed.15mm near
surface gate andremain saved; theaccepted maxsampled difference is.110mm.

Three-task actualsame-state Observer/policyRGB/physics/camera/quality checks pass.
Original/full/LODimages andsameObserverROI enlargements arein compare-a03 and
observer-standing-a01. Source realstate@2.94s isrerendered identically; noObserver
position/FoV change. Sixfixtures havepixel-identical policyRGB;outlineIoU≥.999948.
16affectedtests andCUDA10ticksmoke pass;pairedrender costdrops9.87%/17.07% for
Push/Press. See theguide,report/completion for hashes,gates andlimits.

Allsource/oldresources/failedattempts are retained. NoWAM/SFT/AMD/formaldemos or
publication. Thisgeneration/comparison request doesnotchangecurrent defaultfull
STEP routing;LODhas anexplicit selectableversion. Source stays uncommitted.
