---
id: QLM-STEP-CAMERA-RIG
type: guide
status: accepted
source_map:
  - scripts/mujoco/inspect_step_assembly.py
  - scripts/mujoco/tessellate_step_components.py
  - scripts/mujoco/extract_step_colors.py
  - scripts/mujoco/register_step_robot.py
  - scripts/mujoco/build_step_camera_rig.py
  - scripts/mujoco/compare_step_camera_rig.py
  - scripts/mujoco/live_matrix.py
---

# Supplied STEP support: current MuJoCo visual profile

This full-precision STEP profile is now a retained reference. Current default
rollout/collection/evaluation uses [the accepted rendering LOD](mujoco-default-rig.md).
Original STEP, full meshes and comparisons remain; old generated episode payloads
are evicted under the explicit QLM-SIM-010 cleanup authorization.

The user explicitly requests extracting the new support from the supplied STEP,
replacing the current MuJoCo support, preserving old resources and showing actual
RGB/camera comparison. QLM-SIM-007 owns this local work. The later STEP request
supersedes QLM-SIM-006's current procedural-support routing; that completed attempt
and its exact source-calibration evidence remain historical.

## Source and geometry

Source is the supplied depth-camera assembly STEP under WAM-Policy_Ethan, exported
by SolidWorks2025 as AP214 with millimetre units. It contains the assembly's Go2,
base frame and support. The new visual geometry consists of components named
基础框架最终版1-6 and 单支架. Source geometry/assembly transforms and original file
SHA are preserved in workspace runs/audit/step-camera-rig-migration-20261013-v1/.
No source STEP,old resource pack or recording was modified.

OpenCascade7.9.3.1 runs in a separate CAD environment. All4786 selected support/frame
faces triangulate at absolute linear deflection.20mm/angular.15rad.110683 valid
triangles are retained; two exactly zero-area triangles are omitted and recorded.
No mesh decimation or substitute collision hull is used for the rendered geometry.
Original STEP presentation colors are inherited from face/shell owners. The source
contains no declared mass,density or physical material properties; color is not a
material-density specification. Its local use is user-authorized; redistribution
terms have not been supplied and are not inferred.

The assembly's CAD Go2 is only a registration reference. Its imperfect exported
surfaces include68 faces without triangulation, and its body mesh is not identical
to the retained Isaac robot. It is not imported as a new physical/visual robot.
Rigid registration compares competing front/back axis hypotheses without scaling
or shape warping. The selected fit is approximately CAD-Y→base+X,CAD+X→base+Y,
CAD+Z→base+Z, with a.0101degree correction; overall reference point median distance
.622mm but p95 is19.37mm because the reference meshes differ. Detailed subset
residuals are preserved in registration-a02/surface-validation.json. This is a
reproducible visual placement estimate, not factory/device extrinsic metrology.

## Current resource and physics settings

Workspace assets/mujoco/ethan-step-camera-rig-v1-a01 stores converted CAD meshes,
source/registration/color identities and preparation reports. Current three-task
packs are assets/mujoco/original-{task}-v1-step-rig-a01. Prior v1-a03 and
v1-ethan-rig-a01 resources and all historical rollouts are retained.
The public live_matrix defaults to v1-step-rig-a01; explicit model-profile-suffix
selects historical versions. Other public entries retain explicit model paths.

The old five procedural support/housing geoms are replaced by the two actual STEP
mesh groups. Both have explicit mass0 and contype/conaffinity0, with original
robot inertials and inertiafromgeom=false. They are visual geometry; no load or
contact behavior is inferred from a CAD solid. Geometric volume does not mean that
the source specified a simulator mass. Robot/task body mass,inertia,actuation and
all physical collision parameters remain unchanged. Native100-step same-input
physics produces bit-identical qpos/qvel for all three tasks.

The visual change alters compiler-derived dof_length by approximately.02376m.
This is explicitly reported and is not described as full compiled-model identity.
Original extent,meansize,meanmass,meaninertia andcenter statistics are pinned in XML
so the visual bounds do not silently change camera clipping/visual scale.

## Optical camera and actual RGB comparison

STEP supplies external mechanical shape, not a calibrated optical center,axis or
FoV. The original virtual task camera is deliberately retained: position relative
to base(.30,0,.34)m,65degree downward pitch,horizontalFoV69.4degrees,
verticalFoV42.561177degrees,dual1280x720 and original clip.1–20m. This does not
claim the retained optical frame is calibrated to the new physical mounting plate.
A later physical-camera calibration requires actual device/optical-frame evidence.

Three tasks×two same-state fixtures compare reset and translated/rotated/articulated
robot states. Actual OSMesa captures have0position/rotation/FoV difference; the
policy images in these six fixtures are pixel-identical. Original Observer images
show the changed support, and a dedicated free diagnostic closeup clearly shows
its shape. That free camera never enters policy inputs. All render captures advance
zero physics ticks. No all-state or RTX/EGL equivalence follows from these fixtures.

## Local checks and limits

Affected resource/public-backend tests16passed. Actual CUDA-MJWarp smoke loads the
new model,steps10ticks,transfers the state and renders through Native OSMesa with
fresh scene RGB and no rendering physics advance. This is load/kernel/synchronization
coverage, not actor/task success or long-run controller acceptance. No new WAM
rollout,demonstration,training,AMD or external publication was performed.
Existing Box/Basket EGL admission failures remain in force.

Evidence: assembly-a01,mesh-a01,colors-a03,registration-a02,build-a01,compare-a01,
closeup-a01,cuda-smoke-a01 and completion.json under the new workspace audit root.
Original failures and extraction revisions remain preserved. Source stays local
and uncommitted. Reproduction uses the constrained independent CAD environment,
then the existing simulator environment; runtime/AMD requires only final portable
MJCF/mesh packs and does not need OpenCascade.
