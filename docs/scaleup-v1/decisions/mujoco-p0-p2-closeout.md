---
id: QLM-MUJOCO-P0-P2-CLOSEOUT
type: guide
status: accepted
related_work: [QLM-SIM-013]
source_map:
  - src/qlm_bench/backends/mujoco/physics.py
  - src/qlm_bench/backends/mujoco/runtime.py
  - src/qlm_bench/backends/mujoco/evaluation.py
  - src/qlm_bench/backends/mujoco/recording.py
  - scripts/mujoco/build_hinge_reset_fixture.py
  - tests/qlm/test_mujoco_initial_state.py
---

# Final local P0–P2 closeout

QLM-SIM-013 and WAM v3/DATA-002 close the two tail evidence items requested by the
user. P0–P2 local engineering acceptance is complete. This does not admit formal
pilots/data release,production capacity,seven-task development,AMD execution or SFT.

## Accepted renderer and checkpoint interpretation

The user explicitly retains OSMesa. Box/Basket EGL visual failures remain historical
and are not a blocker for the admitted Native OSMesa route. Throughput/capacity
budgets are measured/frozen with later pilots rather than declared accepted here.
The user confirms the retained WAM checkpoint is Push Box-only trained;Press's
head/front-body interaction is a diagnostic observation,not a closeout blocker.
Keep the recorded original-predicate success and interaction qualification. No
success/collision/action/observation/model contract was changed for this observation.

## Current default LOD data evidence

Each accepted default LOD a02 task produced one new CUDA-MJWarp+OSMesa short
engineering episode:101actions,102boundaries,2.02s,explicit pre-reset terminal.
All three actual Raw/Canonical/media validations pass. Provenance binds the current
complete resource identity,controller/environment/dirty source and QLM-SIM-013.
The original frozen VAE config/weights are hash-checked;actual LeRobot/video/state
readback gives latent `[1,48,7,24,20]`,root-link/body-frame state `[25,10]`,indices
0..96 by4 and80ms spacing. No normalizer fit,training or formal demonstration count.
Lift retains the earlier approved .47m expert standoff;controller/predicate are unchanged.

## Hinge and state randomization evidence

The separate `p2-closeout-hinge-reset-v1-a02` resource is a non-task diagnostic
fixture,not a fourth benchmark. It inherits Go2/LOD/cameras/assets and adds a passive
hinge panel and free striker with declared analytical mass/inertia. A declared
initial striker velocity causes real contact;all ctrl/qfrc/xfrc remain zero.
At0.12s Native hinge changes are0.207/0.232rad with26/28contact steps;CUDA gives
0.209/0.233rad with29/32steps. Robot/controller parameters and all production packs
remain unchanged. First a01 fixture lacked explicit inertia under the inherited
inertiafromgeom=false setting;it failed at load,never stepped,and remains archived.

Seeded initial root/object poses,object hinge angles and striker velocities are
serialized and reconstructed on both backends. `reset(initial_states=...)` validates
resource identity,complete finite arrays,unit quaternions and joint limits before
any mutation. Default nominal reset is unchanged. Selected-lane reset is zero-step,
other lanes remain byte-identical,and bad identity/NaN/quaternion/limit inputs are
atomically rejected. Native mirrors copy the complete articulation;RGB reflects
the same physical timestamp without advancing physics and old epochs are rejected.

The public EvalCase adapter now applies its already-declared qpos/qvel through this
explicit reset path. Actual randomized-case reconstruction on the unchanged default
Push model passes Native/CUDA without physics advancement. This is initial-state
randomization capability;P3 still freezes each task's legal ranges,pools,goals and
appearance/physics variants. Frozen model/camera/material parameters are not mutated.

## Evidence and next-stage boundary

Workspace `runs/audit/mujoco-p0-p2-closeout-20261013-v1/` contains three capture/readback
bundles,`artifact-provenance-readback.json`,serialized cases,Native/CUDA traces/RGB,
public reconstruction records and final completion/report.16affected tests pass;
the remaining explicit default-resource test is covered by actual artifact resource
pin checks. Source remains local/uncommitted. P3 formal task/pilot eligibility,asset
redistribution,production capacity and AMD/gfx950 smoke stay later gates.
