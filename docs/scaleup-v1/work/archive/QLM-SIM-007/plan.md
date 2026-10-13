---
id: QLM-SIM-007
type: exec-plan
status: completed
source_map: []
---

# STEP support extraction and MuJoCo replacement

User explicitly requests extracting the new support from the collaborator STEP,
replacing the current MuJoCo support, preserving original/old versions, showing
actual before/after RGB and comparing task-centric camera pose/FoV.

Source is the supplied depth-camera assembly STEP under WAM-Policy_Ethan. Read its
assembly structure and transformations; identify support bodies and their mounting
relation to the included Go2. Do not import the CAD robot as a new dynamics model.
Create a portable, versioned visual-only derivative of current original-task packs.
Keep robot/task mass,inertia,collision,controller and all historical resources.
Current support has no modeled mass/collision; this geometric replacement does not
authorize inventing material density or a new physical load.

CAD shape placement and optical camera calibration are separate evidence. Retain
the frozen task camera unless STEP or collaborator-supplied optical frames provide
an unambiguous replacement; report any high-impact required camera contract change
before promoting it. Comparison must record actual local/world pose,intrinsics/FoV
and scene obstruction at identical authoritative physical states.

Acceptance: original STEP checksum unchanged; assembly/body selection and CAD→base
registration evidence; tessellation source/tolerance/units and portable manifests;
actual MuJoCo mesh with no unsupported geometry/implicit convex replacement;
robot/task/camera invariant checks, actual OSMesa before/after policy/Observer RGB;
affected tests,governance and explicit not_run. Update routing after verification.

Use a separate CAD preparation environment, preserving simulator/Isaac/WAM envs.
No formal dataset,SFT,AMD,source commit/push or external publication.
Evidence: workspace runs/audit/step-camera-rig-migration-20261013-v1/.

## Progress
- [x] Read current camera/resources/governance and identify absent CAD tooling.
- [x] Load STEP assembly and inspect support/frame/robot placement.
- [x] Derive and verify CAD→robot-base registration; export support mesh.
- [x] Build independent three-task MuJoCo packs and actual camera/RGB comparison.
- [x] Current routing,tests,governance and final report.

## Decisions and recovery
Retain all actual attempts,including extraction/render/registration failures.
Surface/assembly names and dimensions must be checked rather than relying only
on the filename. Camera FoV cannot be inferred from an external housing mesh.

## Completed local evidence — 2026-10-13

Selected STEP components are the base frame and support,4786faces,110683valid
triangles with original presentation colors. Source unit conversion and rigid
registration are explicit. The CAD robot is a reference only;68missing robot
reference faces and non-identical CAD/Isaac body surfaces are disclosed. Overall
reference median.622mm/p95 19.37mm is not a factory alignment guarantee; see the
chosen transform and subset residuals. No scale fitting or geometry warp occurred.

Three current portable packs v1-step-rig-a01 replace the old procedural support.
Original STEP and all old packs are unchanged. Native100same-input steps are
bit-identical in qpos/qvel on all three tasks. Camera/intrinsics/FoV and clipping
are retained; the STEP contains no optical calibration. New visual bounds alter
dof_length,explicitly reported; statistical camera scales are pinned to originals.

Three tasks×two same-state actual OSMesa fixtures pass with0camera pose/FoV delta.
Policy frames are pixel-identical in these six fixtures,while Observer and the
actual diagnostic closeup show the new shape. No rendering advances physics.
Affected tests16passed; actual CUDA load/10step/state-transfer/OSMesa smoke passed.
Current live_matrix defaults to the STEP suffix; historical suffixes remain explicit.

Read decisions/step-camera-rig.md and workspace
runs/audit/step-camera-rig-migration-20261013-v1/report.md/completion.json for checks,
source/resource/image hashes,metadata/registration limitations and preserved attempts.
No WAM rollout,demonstration,training,AMD,commit/push or publication.
