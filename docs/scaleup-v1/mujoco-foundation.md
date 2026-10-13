---
id: QLM-MUJOCO-FOUNDATION
type: guide
status: accepted
source_map: []
---

# MuJoCo P0–P2: current local alignment evidence

[整体阶段状态与后续交接](mujoco-progress.md) consolidates the completed local P0–P2
baseline and pending P3–P6/AMD/SFT gates. Latest reconciliation: QLM-DOC-001 /
v3/DOC-007, 2026-10-13. Historical attempts below retain their own scope.

## Final local phase closeout — QLM-SIM-013

The user-requested current-default data and hinge/randomization tails now pass.
[Final P0–P2 closeout](decisions/mujoco-p0-p2-closeout.md) binds three fresh default
LOD Raw/Canonical/frozen VAE/10D readbacks and actual Native/CUDA passive object
hinge contact,seeded state/reset/world isolation/public EvalCase reconstruction/RGB
sync. Local P0–P2 engineering acceptance is complete. OSMesa continues by explicit
user decision;the Push Box-only checkpoint's Press interaction is not a phase blocker.
No frozen predicate or model/camera/controller/physics settings change. Formal
pilots,production capacity,seven tasks,AMD and SFT remain later-stage work.

## Full-horizon first attempts — QLM-SIM-012

The later user request runs one real WAM v3 trial per task until success/fall/24s
timeout. Default LOD a02,model/prompt/sampling,camera/controller/physics parameters
are unchanged. Only live horizon admission/execution guard and bounded-memory audit
retention change:24s requires75groups; model window remains8. Full eventJSONL remains.

| Task | Actual original-predicate result | Simulation time | Commands |
|---|---|---:|---:|
| Push Box | timeout | 24.00s | 1200 |
| Press Button | task_success | 5.76s | 288 |
| Lift Basket | timeout | 24.00s | 1200 |

All three first attempts have no falls,no outcome-based retry. **Press's actual
Observer terminal shows head/front-body contact with the cap while FL is below.**
The unchanged displacement/hold predicate reports success with16.55mm displacement;
this does not validate FL pressing skill. Keep the raw result and interaction
qualification separate; no predicate/collision change is silently introduced.

Workspace `runs/audit/wam-v3-default-lod-full-rollout-20261013-v1/` retains all9
original RGB MP4s,task results,source/config identities,contact qualification and
three full previews. Aggregate2688commands/342RPC waits freeze simulation. Native
720p50Hz policy/25HzObserver media is captured live;terminal before reset,initial
velocities,source PNG/hash/frame-index/full-decode checks pass. These three nominal
single trials are not a formal statistical aggregate or pilot demonstrations.

## Actual default-LOD real WAM v3 closed loop — QLM-SIM-011

The user's replay request completed on 2026-10-13 with the pinned LOD a02 three-task
model set,CUDA-MJWarp physics and Native OSMesa. Each task runs the retained real
full-SFT v3 step1000 checkpoint twice for2.02s,101commands/7chunks per episode.
Task-correct prompts,original weights/normalizers/frozen VAE,sampling and16-block
offload are preserved. Camera/quality/mass/collision settings remain unchanged.

All96RPC waits freeze physics/controller/time. Per task:2resets,14predictions,
12feedback commits,6KV evictions and2planned horizon terminals. Six actual initial
root/joint velocity states are zero. Final chunks confirm5commands and11unexecuted
tail commands;terminal is sealed before reset. All18original720p MP4s fully decode:
Ego/task50Hz102frames,Observer25Hz51frames per episode. Frame timestamps,lossless
source PNG/terminal hashes and MP4 hashes pass.

Workspace `runs/audit/wam-v3-default-lod-rollout-20261013-v1/` contains `matrix-a01`,
`evidence-readback.json`, `preview-a01` and `review.html` linking all originals.
Previews use actual recorded MP4s,not predictions or post-run simulator rendering.
All six episodes timeout at the declared short horizon; no task SR/formal benchmark/
pilot demonstration is claimed. No training,AMD,commit/push or publication.

The earlier R01–R10 repair authorization was completed locally under
[QLM-SIM-005](work/archive/QLM-SIM-005/plan.md) and WAM v3/INFER-004. This supersedes
the earlier migration pause and overly broad initial P0–P2 acceptance. Accepted
architecture remains [the P0–P2 decision](decisions/mujoco-p0-p2.md). Original
sources, assets, model weights, attempts and historical receipts are unchanged.
Source remains uncommitted in the independent migration/mujoco-foundation worktree.

## Current resources and ownership

QLM-SIM-010 adopts the accepted LOD and records the user-authorized obsolete-payload
eviction. Historical evidence paths below retain source/metadata/scalars but no
longer all RGB/state/data payloads. The exact deletion inventory is in workspace
`runs/audit/mujoco-lod-default-cleanup-20261013-v1/`; compact three-way rig comparisons
and every model/asset file remain. This change does not claim a new WAM rollout.

Use workspace `assets/mujoco/original-{push_box,press_button,lift_basket}-v1-step-rig-lod-a02/`
and original-derived Go2 `assets/mujoco/original-isaac-go2-v1-a04/`. Earlier
Menagerie and procedural p0-v1 resources are diagnostic fixtures, not original-asset
alignment evidence. New original-asset packs retain complete portable manifests,
source provenance and license limitations; local verification is not permission
to redistribute their source assets.

CPU QLM contracts own EpisodeClock/EpisodeRuntime, task predicates, shared Canonical
conversion, evaluation and the public live protocol. Explicit controllers.rambo
owns the original 405D history, actor/normalizer,18D residual,gait/IK/QP,gravity,
smoothing,motor saturation and physics-tick delay. Native/MJWarp is the sole physics
owner. Native rendering mirrors complete timestamped state without stepping.
The original native9, force-zero, root-link/body-frame10D,500/100/50Hz,dual720p RGB,
12.5Hz model inputs and25Hz diagnostic Observer contracts remain unchanged.

## Verified local alignment

- Original19 rigid bodies,12 hinges,six fixed joints,27 primitive colliders,
  mass15.01900017kg,COM/full inertia/limits/axes and zero armature are mapped from
  actual Isaac runtime. Original visual triangles are retained except explicitly
  recorded zero-area faces. RAMBO owns final effort; no duplicate actuator PD/delay.
- Original checkpoint SHA is unchanged. Same-input original Isaac actor replay
  differs by at most1.67e-6. For0.15rad/s yaw, original Isaac gives0.14291;
  repaired Native/CUDA give0.14002/0.14591, versus initial0.0733/0.07573.
  This is bounded nominal evidence, not multi-seed or all-command equivalence.
- Box05,industrial button and OASIS basket retain original meshes,UV/textures,
  actual mass/COM/inertia and PhysX cooked convex hulls65/4/32, with no new
  decomposition. Both Native/CUDA complete all three current expert tasks.
  Lift's scripted expert explicitly changes body standoff.50→.47m; original
  timeout is preserved. Full-foot threading and physical success thresholds remain.
- Original policy mounts,K/FoV,clip.1..20m,five-piece visible camera rig and each
  task's Observer are restored. Actual RTX/MuJoCo same-state projected points
  differ by less than0.00015px in the20/40ms fixture. Original Isaac has stale
  camera pose at tick0 (10cm mismatch); the port renders the current measured state
  and does not reproduce that reference defect. Other viewpoints/tasks have source
  profile and local rendering coverage, not an exhaustive projection proof.
- Push progress is reset-relative geometric-center displacement. Actual Raw/
  Canonical preserves N+1 boundaries,N actions,terminal-before-reset,Observer and
  complete resource/backend/controller/environment/dirty-source provenance.
  Partial/error attempts preserve execution and failure evidence but cannot become
  usable Canonical. Full-interval explicit abort is diagnostic failure data.
- Original v3 checkpoint runs three tasks×two2.02s sessions through public live,
  each7chunks/101commands,102actual frames/view and51Observer frames. All96RPC
  waits freeze physics/controller/RNG/time; feedback,K/V eviction and reset pass.
  These are planned engineering timeouts, not model task success or formal scores.
- Independent per-case/per-purpose RNG, two-world future state/history/RNG and
  actual RGB/reset isolation pass. Original sampled contact history updates every
  10ms despite its5ms configured sensor period. MuJoCo retains10ms controller
  history and explicitly labels its500Hz raw normal-force diagnostics.

## Reproducible public routing

Use workspace `envs/qlm-mujoco-py312-v1/bin/python` with this worktree's `src` in
PYTHONPATH. Do not rebind shared Isaac/WAM editable environments. Set MUJOCO_GL before
import; choose separate OSMesa/EGL processes. OSMesa requires the extracted prefix
`assets/mujoco/p0-v1/osmesa/root/usr/lib/x86_64-linux-gnu` in LD_LIBRARY_PATH.
MESA_SHADER_CACHE_DIR and WARP_CACHE_PATH should point to workspace cache layers.

- `python -m qlm_bench.cli collect --backend native|mjwarp --task TASK --model SCENE
  --checkpoint RAMBO --output-dir NEW_OUTPUT --ffmpeg FFMPEG --ffprobe FFPROBE
  --commands 101 --diagnostic-only --render-backend osmesa`: actual engineering
  Raw/Canonical, bounded to24simulation seconds. Lift's expert override is explicit.
- `python -m qlm_bench.cli live --backend native|mjwarp`: public synchronous model
  driver; supply model/checkpoint/task/output/port/ffmpeg/ffprobe and OSMesa flags.
  An independently started WAM service supplies the model; it cannot advance physics.
- `python -m qlm_bench.cli evaluate prepare|run --backend native|mjwarp`: existing
  EvalCase/EvaluationRunner contracts. Exact resource/task/goal/camera/seed/initial
  state must reconstruct without stepping or silent nominal-scene substitution.
- scripts/mujoco remain explicit bounded diagnostic tools. Original-task profiles
  and resource manifests are required by public entrypoints. Public metadata imports
  do not load Torch/Isaac/MuJoCo. Optional heavy components load only on invocation.

## Explicit differences and admission limits

PhysX and MuJoCo contact models are not identical. condim3 has sliding contact and
no unintended torsional/rolling friction; source dynamic friction is mapped with
explicit pair priority. Static/dynamic transition, contact offsets and compliance
are not exact PhysX equivalents. The zero-margin MULTICCD candidate and solref/
solimp mapping have bounded behavior evidence, not universal equivalence. GPU
float32 effective tolerance differs from Native float64 and is recorded at runtime.

Native rendering retains original geometry/texture/cameras, but MDL/PBR,lighting and
shadows are not RTX pixel equivalents. A declared vertical-light profile removes
observed grazing-shadow artifacts without altering physics,cameras,meshes,textures.
OSMesa is the common accepted reference. Press passes EGL/OSMesa equivalence;
Box/Basket fail unchanged ROI MAE2/255 (max2.129/3.488). Do not admit EGL for those
profiles or weaken the camera/preprocessing/visual thresholds.

Actual2.02s CUDA+OSMesa collection including encoding/packaging takes50.79/48.00/
104.74wall seconds for Push/Press/Lift. Conditional1000×20s projections are140/132/
288hours and include short-run fixed overhead. This quantifies cost; it is not
production-capacity acceptance or a forecast for seven unimplemented tasks. The
older aggregate timer includes rendering; final code separately accounts for
controller,physics,observation,mirror refresh,render/readback and recorder callbacks.

[Platform matrix](decisions/mujoco-platform-features.md) records fixed ROCm source
inspection, preserved solver budget and MI355X/gfx950/OSMesa target smoke requirements.
AMD execution remains not_run. P3 task/pilot admission,P6 administrator bundle,
formal1000demonstrations,SFT,benchmark metrics and publication were not performed.

## Evidence and historical corrections

Workspace `runs/audit/mujoco-alignment-repair-v1/report.md` and
`completion-audit-a02/audit.json` map all ten review requirements to actual evidence.
`live-real-original-media-a01/review.html` contains original recorded model-session
RGB; `original-assets-report-a01/review.html` contains actual expert videos.
The first hash-only model runs and later reconstructed previews are still historical
and do not become actual recordings through these new runs.

Initial P0–P2 records, [checkpoint check](work/archive/QLM-SIM-003/plan.md),
[independent Isaac comparison](work/archive/QLM-SIM-004/plan.md), original review and
all failed attempts remain preserved. Current local closure does not retroactively
validate their earlier broad claims.

## Later collaborator camera-rig replacement — QLM-SIM-006

The user selected the collaborator-identified procedural definition for the current
support. [Source and before/after evidence](decisions/ethan-camera-rig.md) verify its
exact source inventory, new independent three-task resource packs and actual same-
state OSMesa images. Camera pose/FoV is unchanged; six fixtures have pixel-identical
ego/task/Observer RGB. Earlier a03 resources remain the identities used by the
archived R01–R10/WAM runs, not the current routing. live_matrix defaults to the new
suffix; --model-profile-suffix v1-a03 selects those historical scenes explicitly.
No learned-policy run or GPU dynamics rerun was needed for this camera-only evidence.

## Later supplied STEP support — QLM-SIM-007

The full support geometry was extracted from the supplied mechanical STEP assembly.
Read [the STEP source,registration and actual comparison](decisions/step-camera-rig.md).
The then-current live_matrix suffix was v1-step-rig-a01; v1-ethan-rig-a01 and v1-a03 select
historical supports explicitly. It is superseded by the accepted LOD default below.
Actual Native/CUDA load/render and same-state
comparisons pass. Optical calibration is intentionally retained; the STEP lacks
optical extrinsic/FoV data. New CAD placement is a documented rigid-registration
estimate, not device calibration. Geometry remains without mass or collision.

## Available protected STEP rendering LOD — QLM-SIM-009

The user-requested lightweight rendering variant is
assets/mujoco/original-{task}-v1-step-rig-lod-a02 at workspace level.
[Geometry/protected settings and Observer evidence](decisions/step-rig-rendering-lod.md)
record66.37% fewer triangles,unchangedcamera/physics/quality andactualcomparison.
All three previous model representations are retained. Under QLM-SIM-010 the user
selected this LOD as the shared default for runtime, collection and new evaluation
cases; [default routing and local cleanup](decisions/mujoco-default-rig.md) describes
the pinned model set and explicit historical overrides. No formal production
admission follows. Obsolete MuJoCo-generated payloads are evicted at the user's
request; historical attempt metadata/scalars remain unchanged. Exact receipt:
workspace `runs/audit/mujoco-lod-default-cleanup-20261013-v1/`.
