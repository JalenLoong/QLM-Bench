---
id: QLM-SIM-005
type: exec-plan
status: completed
source_map: []
---

# MuJoCo alignment repairs — full R01–R10 execution

## Current authority and scope
The active user goal requires every review finding to be fixed. Earlier pauses of
asset/camera repair are superseded by this request. No training or remote execution
is authorized. QLM source: migration/mujoco-foundation at189545f plus existing local
changes; WAM peer: adaptation/v3-mujoco-sft at35d94a7 plus existing local changes.
Independent original Isaac reference: repos/QLM-Bench-scaleup-push_box at189545f.
Use explicit source bindings; never rebind shared editable installations.

## Execution order
1. Establish a single original Isaac reference dossier for robot, task, camera,
   dataset semantics and physics properties. Repair independent known semantic
   defects while the reference/export infrastructure is prepared.
2. Derive portable original-resource profiles, close robot/contact/camera alignment
   and migrate the original three tasks. Validate actual physics and rendering.
3. Unify public backend/task/recording/conversion/evaluation ownership; persist
   complete provenance and all failure paths; test independent lanes/case RNG.
4. Rerun full three-task expert/data/WAM engineering paths with actual RGB. Benchmark
   original assets, complete local platform preparation and audit every finding.

## Progress
- [x] Read current dirty worktrees, review findings and authoritative original records.
- [x] Reserve QLM-SIM-005 and v3/INFER-004; retain the entire review objective.
- [x] Original Isaac reference/export dossier.
- [x] R01 robot/contact mapping and Native/CUDA behavior acceptance.
- [x] R02 original three assets and actual expert acceptance.
- [x] R03 complete camera setup and cross-engine projection/renderer evidence.
- [x] R04 shared task-state semantics and actual data regression.
- [x] R05 resource/backend/controller/source provenance closure.
- [x] R06 failure/partial/abort record and conversion evidence.
- [x] R07 actual v3 three-task RGB/feedback/reset/terminal evidence.
- [x] R08 common public backend, collection and evaluation integration.
- [x] R09 portable model identity and model-state/GL identity enforcement.
- [x] R10 independent lanes/RNG, contact cadence and original-asset throughput.
- [x] Requirement-by-requirement completion audit.

## Evidence and recovery
New artifacts: workspace runs/audit/mujoco-alignment-repair-v1/. Each actual attempt
has an immutable identity, source hashes, inputs, outputs and failure reason. A code
fix may be unit-verified while its runtime/data acceptance is still pending; record
that distinction in findings.json. Existing primitives remain explicitly diagnostic.
Original archives and former overly broad completion receipts remain historical,
with current routing pointing here. No failed artifact is overwritten or selected
away to improve reported success. W&B/remote publication stays not_run.

## Next action
Perform the final requirement-by-requirement R01–R10 completion audit against the
current source and receipts, correct any remaining discrepancy, and then close the
paired records. No processes remain intentionally pending after the current checks.
Keep EGL admission failures, original Isaac stale reset imagery, conditional cost
projections and AMD not_run explicit; none can be turned into a broad pass claim.

## Actual progress: original robot and reference closure

- The original unchanged Isaac reference exports 19 rigid bodies, 12 active joints,
  six fixed joints, 27 primitive colliders and the original visual material groups.
  `scripts/mujoco/build_original_robot.py` creates a portable candidate from those
  runtime arrays and USD transforms. Workspace asset candidate:
  `assets/mujoco/original-isaac-go2-v1-a04/`. It retains total mass15.01900017kg,
  zero armature, per-body COM/inertia, joint limits/axes and disabled self-collision.
  Compiled reset FK errors are below0.1micrometer for position and3.4e-7 for rotation
  matrix entries. No controller math or weights changed.
- All397085 nonzero-area source visual triangles survive compilation. Only1547
  exactly zero-area source faces were removed, and one zero normal was repaired
  from its face. Original indices and full source arrays remain in the resource
  pack. Original constant-color robot shaders do not consume their partial UV sets.
  The two earlier rejected conversion attempts are preserved, not overwritten.
- Actual18s Native and CUDA runs completed9000physics ticks,1800actor calls,
  dual900-frame50Hz policy videos and450-frame25Hz diagnostic Observer videos.
  No fall/nonfinite values, weights unchanged, reset checks passed. Yaw means
  are0.14002/0.14591rad/s for0.15 requested (original Isaac0.14291). Lateral means
  are0.10842/0.10606 for0.10 requested. These are nominal single-run observations,
  not full task/multiseed equivalence. Candidate contact solref/solimp and solver
  mapping remain subject to behavior validation; no retraining is indicated now.
- Original task runtime extraction preserves actual mass, full inertia, COM,
  material/compliance, initial pose/RGB, two cameras and five rig geometries.
  PhysX's synchronous collision-representation API exports the original cooked
  convex hulls: Push65, Press4, Lift32. No policy actions or export-time physics
  steps. Original sources/assets are unchanged. This avoids a speculative new
  convex decomposition, but MJCF conversion/physical task gates are still pending.
- Resource identity now includes referenced mesh/texture/hfield files and declared
  manifest/profile hashes. Absolute external legacy fixtures are identified as
  nonportable. New packs verify every dependency and survive relocation. Snapshots
  reject changed camera/light/material/physics parameters; full mesh/texture/model
  fingerprints are checked at close. Per-frame model mutation is unsupported and
  requires a new explicit profile/runtime. Actual GL vendor/renderer/version is
  recorded. Original-model EGL/OSMesa captures and mutation-rejection checks pass;
  this is not an Isaac pixel-equivalence or original-task visual acceptance claim.
- CPU regression:22passed/1optional task-render skip; explicit actual OSMesa
  resource/mutation tests:10passed. QLM governance/docs/import boundaries and WAM
  v3 docs passed. WAM INFER-004 namespace metadata was corrected to v3/INFER-004.
- New closure guards also pass an actual two-world CUDA6s controller probe and
  selected-world reset state isolation. This does not establish future RNG-stream
  independence; R10 remains open for that requirement and original-task throughput.

Evidence root remains `runs/audit/mujoco-alignment-repair-v1/`; numerical/media
report is `robot-foundation-report-a01/`. R01/R02/R03/R09 remain in progress, and
the complete R01–R10 completion rule is unchanged.

## Actual progress: original tasks, cameras and durable recording

- `build_original_task.py` now converts original visual triangles/UV/texture
  channels, the exact65/4/32 PhysX cooked convex hulls, original runtime mass/full
  inertia/COM, and the original five-piece camera rig and Observer. Collision
  vertex errors after MuJoCo mesh normalization are below3.1e-8m. The button uses
  a physical300N/m,8Ns/m internal spring with the original40N limit; no unlimited
  joint spring, attachment, assistance wrench or task teleport was introduced.
  Original scale and rigid-root versus geometric-center semantics are explicit.
- Candidate resource packs `assets/mujoco/original-{task}-v1-a02/` pass the static
  mapping gates. Actual original-checkpoint Native expert outcomes: Push8.58s,
  Press8.38s; original Lift expert first timed out at24s. A versioned scripted
  expert candidate changes only body_standoff_m from.50 to.47m and succeeds at
 14.28s. Full-foot threading margin, asset geometry, physical success condition,
  controller/checkpoint, limits and cameras remain unchanged. Candidate rationale
  and all failed attempts are retained under `expert-candidates/`.
- CUDA actual RGB expert runs succeed at8.80/8.44/14.24s for Push/Press/Lift, with
  440/422/712 completed commands. Policy video frames are441/423/713 per view;
  original Observer25Hz frames are221/212/357. All nine videos pass full validation
  and finalization; terminal PNGs and source state/command/hash records are saved.
  Lift uses the explicit.47m expert candidate. These are engineering trajectories,
  not a success-rate estimate, pilot admission or WAM learned-policy evaluation.
- Actual RTX CameraParams and MuJoCo GL frusta match at the original20/40ms states:
  all three views pass, maximum projected-point difference below0.00015px. A new
  reference limitation was found: unchanged original Isaac reset RGB/camera pose
  is10cm below the current physical root at tick0; it becomes correct after the
  first command (pose error about1.3e-8m). Ordinary/tiled products and non-stepping
  PhysX transform synchronization were tested; the stale reset evidence is retained.
  This is not a reason to offset MuJoCo cameras or reuse a stale first frame.
- Native recording now preserves actual terminal PNGs, completed history/current
  command/partial confirmation, observer cadence, append-only events and structured
  failure receipts. Partial/error attempts do not enter the unchanged Canonical
  schema. Explicit full-interval aborts can produce valid diagnostic failure data.
  Actual OSMesa fixtures cover partial10ms, render failure after execution, encoder
  close failure and explicit abort:4passed. Missing-model startup also writes a
  verified fail-closed receipt. No dropped prefix is replaced with synthetic data.
- A32-command original-asset Push recording passes actual Raw/Canonical/video
  readback (33boundaries,64control/320physics steps,17Observer frames). Progress
  matches reset-relative geometric-center displacement with max error1.2e-16m.
  Offset-origin/rotation/reset tests also pass. Canonical provenance now retains
  actual resource/backend profile, full controller/expert source hashes, dirty
  checkout identity and a local93-file source snapshot. Subsequent producer code
  also records environment/controller configuration/normalizer identities.
- Visual inspection detected diagonal-light floor shadow artifacts in the first
  original-asset videos. Fixed-state diagnostics retain all attempts. A vertical
  spotlight removes the observed artifact while keeping real shadows. New packs
  `original-{task}-v1-a03` carry this explicit rendering profile; their physics,
  camera, mesh and texture arrays must remain identical to a02. Full EGL/OSMesa
  original-task equivalence and throughput are still pending. Earlier videos are
  actual engineering records, not production visual acceptance.

R07 actual repaired-scene WAM RGB, R08 public collect/evaluate, R10 independent
RNG/contact cadence/production throughput and final all-finding audit remain open.
No fresh training, demonstrations for release, AMD or publication has occurred.

## Actual progress: public integration and real WAM media

- Original a03 render fixtures pass geometry/reset checks on EGL and OSMesa.
  Exact RGB reset hash equality proved too strong: differences were at most one
  8-bit quantization level, with identical geometry. Failed exact-hash attempts
  remain preserved. The next fixture manifest declares a one-LSB reset limit;
  the original RGB/ROI thresholds and geometry tolerance were not relaxed.
  Press passes EGL/OSMesa equivalence. Push/Basket fail the frozen ROI MAE2/255
  gate (max2.129/3.488), although global RGB and geometry pass. Production EGL
  admission is therefore withheld for those profiles. The approved common OSMesa
  reference is used for actual collection and learned-model evaluation.
- CaseRandomStreams owns independent CPU generators per case and per motor/QP
  purpose. Motor distribution0..10physics ticks and original1e-6 QP regularizer
  remain unchanged; Isaac's legacy same-input path remains available. Frozen actor
  construction no longer consumes global RNG. Tests verify batch/lane permutation,
  stream separation and reseeding. Actual two-world CUDA probe passes future RNG,
  state/history and selected reset isolation. Contact histories update once per
  completed5physics ticks; repeated reads do not shift them. Original three-task
  Isaac readback also shows10ms sensor updates, despite configured5ms period.
  Use contact-cadence-reference-readback-a02; a01 overstated source-file identity.
- Backend readback is cached until the authoritative step/reset changes state;
  returned tensors remain owned copies. Cached versus uncached Native trajectories
  match exactly in the regression fixture. Actual readback calls drop3544→1012
  per101commands, with approximately1.9s actual GPU state readback per capture.
- Public `qlm collect --backend native|mjwarp`, `qlm live --backend ...` and
  `qlm evaluate prepare|run --backend ...` use the explicit backend factory.
  Evaluation reuses the existing EvaluationRunner and a shared controller adapter;
  cases cannot silently substitute another model/goal/camera/initial state. Three
  actual public evaluation cases pass reset reconstruction and result validation,
  each with four stand commands and explicit engineering timeout/no formal score.
  Original and MuJoCo producers now share the Canonical converter; legacy Lift
  import remains an alias. Physical goal predicates and success holds are shared.
- Public CUDA+OSMesa collection succeeds for all three original assets:
 101commands/102boundaries,202control/1010physics ticks,51Observer frames each.
  Actual frozen VAE/10D readback succeeds for each: latent[1,48,7,24,20],state[25,10].
  Final provenance capture additionally verifies actual solver options in Canonical,
  complete103-file source snapshot, environment/controller/normalizer identities.
- Native and CUDA final case-RNG expert regressions all succeed with no fall:
  Native Push444/Press501/Lift712commands; CUDA445/501/712. Lift uses the declared
 .47m scripted body-standoff candidate. No task condition or RAMBO math/weights changed.
- Original v3 step1000 checkpoint completes three tasks×two2.02s episodes through
  the public live entry, using OSMesa. Every episode has7chunks/101commands,
 102actual50Hz policy frames per view,51Observer25Hz frames and lossless terminal
  PNGs. All96RPC waits freeze physics/controller/RNG/time. Per task:2resets,
 14predictions,12feedback commits,6KV evictions,2terminals. Model task SR is not
  claimed. Review and readback: live-real-original-media-a01/review.html and
  evidence-readback.json. Full T5/tokenizer/VAE11-file identity was verified against
  the retained fixed upstream inventory before regenerating the three prompts.
- Pipeline cost is measured, not assumed:2.02simulation seconds take50.79/48.00/
 104.74wall seconds for Push/Press/Lift including packaging and validation. The
  conditional1000×20s projection is140/132/288hours; short-run fixed overhead makes
  this a conservative estimate, not a measured dataset run or ten-task capacity.
  No resolution/rate/preprocessing reduction was made. P3 production cost/admission
  still needs explicit planning; this repair only closes measurement/provenance gaps.
- Fixed ROCm source APIs were inspected locally. They retain cuda:N device aliases
  and the required world/reset/data signatures. The AMD fork silently caps HIP
  line-search iterations at10; the adapter now restores the declared50 and records
  effective float32 tolerance1e-6 versus XML1e-8. MI355X requires gfx950 build/smoke;
  candidate README's gfx942 support is not treated as MI355X validation. Read the
  platform matrix. No AMD runtime, installation or job submission was performed.
- Current verification:166CPU tests passed/12explicit optional skips;4RPC tests
  passed outside the socket-restricted sandbox; final actual fault/media tests6passed.
  WAM56CPU tests passed and its sandbox-blocked Gloo test passed separately outside,
  for57total. Actual resource relocation of all three packs into temporary paths
  outside the workspace preserves identity and compiles successfully. Governance,
  docs and import-boundary checks pass. Final closure audit remains required.

## Final local completion — 2026-10-13

The requirement-by-requirement audit and final actual OSMesa tests passed.
Evidence: workspace runs/audit/mujoco-alignment-repair-v1/completion-audit-a01/audit.json,
closure-actual-tests-a01.log (22 passed), completion-audit-a02/audit.json and report.md.
R01–R10 are closed for their authorized local repair requirements. Previous progress
paragraphs retain their chronological scope; they are not current open-gate lists.
Current routing and limitations are in the current MuJoCo guide.

Final checks additionally reject invalid lane IDs/nonfinite physics, preserve failure
evidence and separate controller/physics/observation/render/recorder timings. Actual
complex-basket two-world RGB/reset isolation and a final CUDA Raw/Canonical capture
passed. Tests, source identities, resource/media hashes and paired governance status
are recorded in the completion receipt. Source remains local and uncommitted.

EGL for Box/Basket is not admitted; OSMesa is the consistent accepted reference.
Original Isaac stale tick0 camera imagery is not copied. Physical contact-model and
RTX/Native shading differences remain explicit backend mappings, not exact-equivalence
claims. Lift uses the recorded .47m expert standoff. Production capacity, asset
redistribution, statistical task equivalence, AMD hardware and P3–P6 remain outside
this completion claim. No training, publication or formal demonstration was performed.
