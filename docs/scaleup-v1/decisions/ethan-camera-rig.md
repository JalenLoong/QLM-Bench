---
id: QLM-ETHAN-CAMERA-RIG
type: decision
status: accepted
source_map:
  - scripts/mujoco/replace_camera_rig.py
  - scripts/mujoco/compare_camera_rig.py
  - scripts/mujoco/live_matrix.py
---

# Collaborator-identified procedural task-camera rig

This retained procedural model is a historical reference. Current defaults use
[the accepted STEP rendering LOD](mujoco-default-rig.md), with unchanged optics and
physics. The user's cleanup evicts old generated episode payloads while preserving
the source/model files and compact mechanical/visual comparisons described here.

The user requests replacing the current MuJoCo task-camera support with the version
identified by WAM-Policy_Ethan and measuring before/after pose/FoV. QLM-SIM-006 owns
this local work. WAM source/weights and the public camera/data/action contracts are
unchanged. Independent resource packs preserve every historical a03 model and RGB.

## Source and construction

The collaborator's TRAIN009-portable-v8-development-template.tar.gz contains two
matching inventories for QLM commit ed8e17f06665ac27b1575f0164dfb6cb16d34047 and
source/rambo/rambo/tasks/common/lift_camera_rig.py. The file body is absent from the
bundle and recovered byte-identically from local Git; SHA256:
49f25a5319a8301d0f1d54144d99e969ac67ad385ae4fb2cb68db3d3e8473655.
This identifies the collaborator-specified simulator design, not a newly supplied
CAD/mechanical file or an independently different support geometry.

The replacement script verifies both source inventories, preserves the original
source in each pack, and evaluates the five source cuboid definitions: mount_plate,
support,boom,camera_housing,lens_face. Dimensions and camera-related housing placement
are derived from that source, not duplicated handwritten replacement coordinates.
MuJoCo's boxes use half-sizes; the source uses full dimensions. Mount/GL axis
conversion is explicit. Support geometries remain visual-only, no mass/inertia
inference and no collision.

## Current version and measured result

Current packs are workspace assets/mujoco/original-{task}-v1-ethan-rig-a01/ for
push_box,press_button,lift_basket. The prior original-{task}-v1-a03 packs and all
previous media remain immutable. Current live_matrix defaults to suffix
v1-ethan-rig-a01; explicit --model-profile-suffix v1-a03 reproduces historical inputs.
All other public entries require an explicit model path.

Compiled camera relative to base stays XYZ(.30,0,.34)m and mount XYZW
(0,.5372996083468239,0,.8433914458128856):65degrees downward pitch. Horizontal FoV
69.4degrees,vertical42.561177083628365degrees,RGB1280x720 and nominal clip.1–20m are
unchanged. Three tasks×two fixed physical fixtures (reset and translated yaw/roll/
pitch plus articulation) have exactly zero camera position/rotation/FoV change.
Actual OSMesa RGB in ego/task/Observer is pixel-identical in all six fixtures.
Rendering advances zero physics ticks. This is fixed-state evidence, not a newly
run WAM rollout or an exhaustive all-state/renderer equivalence claim.

256 arrays per task were checked. Physical body/joint/actuator/contact and non-rig
geometry parameters remain identical. Direct source doubles replace USD float32
geometry: maximum support-position difference1.35e-8m,quaternion component4.29e-8,
size2.38e-9m. Compiler geometry normalization also changes: dof_length up to2.21e-9,
stat.meansize about1.05e-10m. These are disclosed geometry precision effects; do
not describe every compiled array as bit-identical. Camera tolerance was not relaxed.
Support mass/collision and robot mass/inertia stay unchanged.

## Evidence and reproducibility

Workspace runs/audit/ethan-camera-rig-replacement-20261013-v1/ contains build-a01
verified source/definition, compare-a03 actual images/report/review.html, affected
regression logs and completion.json. compare-a01 records a launcher path error;
compare-a02 records the initial overly strict bitwise dof_length assertion. Both
remain preserved; compare-a03 explicitly reports tiny compiler-normalization drift.
No threshold for camera/RGB acceptance was loosened to admit a changed viewpoint.

Run replacement with the exact package,reference Git repo,model root and new output;
existing destination packs are rejected. Run comparison in a separate process with
MUJOCO_GL=osmesa and the approved OSMesa library prefix. New resources have complete
portable manifests and independent profile/source identities. Earlier EGL Box/Basket
admission failures remain in effect. No GPU/AMD dynamics,WAM inference,training,
demonstration or external publication is claimed by this camera-only work.

## Later STEP geometry replacement
QLM-SIM-007 supersedes the current resource routing above with the actual supplied
CAD geometry; [current source and evidence](step-camera-rig.md). This record retains
its original procedural-source comparison and does not become STEP evidence.
