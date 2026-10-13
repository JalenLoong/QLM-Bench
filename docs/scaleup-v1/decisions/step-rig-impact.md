---
id: QLM-STEP-RIG-IMPACT
type: guide
status: accepted
source_map: [scripts/mujoco/benchmark_step_rig.py]
---

# STEP rig: measured local impact

QLM-SIM-008 evaluates immutable old procedural/new STEP profiles. Workspace
runs/audit/step-camera-rig-impact-20261013-v1/report.md and analysis.json hold all
units,geometry/memory/initialization costs and scope. Source resources and calibration
are unchanged by this assessment. Native OSMesa/llvmpipe,dual720p,CUDA physics.

Actual warm dual-view times:Push116.0→133.3ms (+14.9%),Press100.9→129.5ms (+28.4%),
Basket490.7→506.4ms (+3.2%). CPU RSS after init adds96–186MiB; eachMjModel exposed
arrays adds20.19MiB. New rig has110683triangles,wholeSTEP/CAD robot are not loaded.
CUDA synchronized stepping median change-.23% (1world)/+.40% (2worlds),with two
counterbalanced repeats. Actual1.28s/64command paired capture,original RAMBO:
Push execution/capture25.08→27.04s (+7.8%),fullpipeline34.92→36.53s (+4.6%);
Basket59.45→60.82s (+2.3%),full69.37→70.74s (+2.0%). One complete pair/task
withfixedpackaging overhead is not production/ten-task/1000episode throughput.

Camera config is retained independently ofmesh; previous same-state tests show0
pose/FoV change,not physical optical calibration. No newmass/collision is inferred.
ShortCUDA trajectories differ slightly andactualRGB hashes are not all identical;
no all-trajectory/task-SR equivalence follows. Existing rawreport records the
registration and physics/visual limits. Observer shape/shadows and multienv CPU
memory deserve pilot coverage. Model inference/AMD/EGL were not benchmarked.

Recommendation:retain newCADshape; prepare/verifycoarser tessellation orLOD for
production as a separately authorized follow-on. Requireoutline/mount/policyROI/
shadow/RGB gates;do not altercamera/quality contracts. NoLOD was created here.
Allcaptures areengineering diagnostics,noformalcollection/training/publication.
