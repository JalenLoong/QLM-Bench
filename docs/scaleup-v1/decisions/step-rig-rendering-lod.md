---
id: QLM-STEP-RIG-RENDERING-LOD
type: guide
status: accepted
source_map:
  - scripts/mujoco/tessellate_step_lod.py
  - scripts/mujoco/refine_step_lod.py
  - scripts/mujoco/build_step_rig_lod.py
  - scripts/mujoco/compare_step_rig_lod.py
---

# Protected STEP rendering LOD and three-way Observer evidence

Later user selection under [QLM-SIM-010](mujoco-default-rig.md) adopts the accepted
LOD a02 as the shared default. Default-unchanged statements below describe
QLM-SIM-009's original generation/comparison scope. Old episode payloads are now
evicted under the explicit cleanup request; all models, CAD sources and compact
comparison evidence in this guide remain.

QLM-SIM-009 is the user-requested light rendering mesh of the supplied STEP support.
The original STEP,earliest black procedural support,full STEP-derived meshes andall
historical attempts remain immutable. No camera pose/FoV/resolution/render-quality
or mass/collision settings change. There is no new physical/controller/model contract.

## Independent version and construction

Available LOD packs are workspace assets/mujoco/original-{task}-v1-step-rig-lod-a02
for Push/Press/Lift; core meshes are ethan-step-camera-rig-lod-v1-a02. The full
STEP packs remain v1-step-rig-a01; earliest restored procedural support is v1-a03.
Explicit public model paths select the LOD. This request generated andverified a
variant andcomparison; the existing live_matrix default remains full STEP pending
selection for a subsequent runtime/production task.

Rendering mesh triangles fall110683→37224 (66.37% reduction),with all4786original
CAD faces/geometry features retained. Outline,diagonal brace,plate andmount are
not substituted with primitives orhulls. The same millimetre→metre scale,rigid
CAD→base registration andsourcecolors are reused. Retessellation uses.35mm/.35rad;
12camera-near sourcefaces are copied exactly from the.20mm/.15rad master after
coarse candidates failed the strict.15mm camera-near surface gate. The mounting
frame geometry is unchanged. FaceIDs andfull/coarse provenance are saved.

Sampled bidirectional mesh-surface distance is at most.110mm;camera-near bound
.15mm andglobal.35mm gates pass. Bounding envelope delta below.001mm;allsource
faceIDs retained. These are sampled distances to the retained fine mesh,not a
formal analytic Hausdorff guarantee ordevice optical calibration.

## Actual unchanged-camera rendering and checks

LOD MJCF bytes are identical tofull STEP;onlymesh payloads andversion/provenance
sidecars differ. Compiled camera/body/joint/actuation/collision/light/vis quality
andstats checks pass. Original virtualcamera still(.30,0,.34)m,65degree downward
pitch,69.4/42.561177degreeFoV,1280x720. Native100same-input steps remain identical.
The support is visual-only,mass0/contype0/conaffinity0. Compilergeometry-derived
bounds can differ slightly; no fullcompiled-array identity is claimed.

Three tasks×two same-state fixtures pass exactpolicyRGB andObserverrig outline
IoU≥.999948;ObserverROI MAE≤.2562/255. ActualRGB uses originalMSAA/shadow quality.
The separate segmentation audit disablesMSAA only inits own context anddoesnot
become policyRGB orchangephysics/render model settings.

Three-column images show original procedural/full STEP/LOD under the same original
Observer. A saved realMuJoCo state@2.94s is imported identically andrerendered to
show theentire support. FullObservercamera pose/FoV/1280x720 isidentical across
allthree. Enlargedpanels are the same pixelcrop,not anothercamera ornewFoV.
These are currentactualNative renders,not originalrecordedvideo orAI-generated imagery.

ActualboundedCUDA load/10tick/state-transfer/OSMesasmoke and16resource/public
entrytests passed. Counterbalanced OSMesa warmdualview benchmarks:Push133.51→
120.33ms (-9.87%),Press130.18→107.96ms (-17.07%) relative tofullSTEP. These are
render-onlysingleworldtimings,notfullproduction/AMD/WAM latency acceptance.
No formal demos,training,remoteoperations orsourcepublication occurred.

## Evidence and recovery

Workspace runs/audit/step-rig-lod-20261013-v1/ includes mesh-a01/a02 failedgeometry
candidates,protected-face selection,mesh-a03 accepted hybrid,build-a04,compare-a03,
observer-standing-a01,render-benchmark-a01,surface-validation-a03,cuda-smoke-a01
andcompletion.json. Startup path/dependency errors andfailedsurfgates arepreserved;
no camera/physics/quality/visual gate wasloosened. Finalacceptedresource is a02,
not theearlier a01 candidate. Reuse the saved transform;donot redo alignment from
coarse meshes oroverwrite thefullSTEPmaster. Physicalopticalcalibration remains
separate fromthisgeometry/LOD work.
