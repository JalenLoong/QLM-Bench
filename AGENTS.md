## Current MuJoCo consolidation — 2026-10-14

Read docs/scaleup-v1/decisions/mujoco-workspace.md first. Current MuJoCo branches are QLM migration/mujoco-foundation, WAM adaptation/v2-mujoco-sft and adaptation/v3-mujoco-sft. v2/v3 have equal priority and share explicit360p/50FPS input, never merge their model implementations. This cleanup authorizes ordinary source commit/push on these three branches only; no Isaac/OPD refs, remote deletion, new collection/training/AMD/model/data publication. Shared-v2 future allocation is the MuJoCo v2 worktree, mirrored only in QLM MuJoCo; original Isaac registries stay unchanged.

## Accepted RGB spatial-only adaptation — 2026-10-14

Read docs/scaleup-v1/decisions/rgb-resolution-360p.md and docs/scaleup-v1/work/archive/QLM-DATA-012/plan.md. This user-authorized work covers QLM plus v2 and v3 equally:640×360 policy RGB,50FPS,Observer720p/25FPS unchanged; old720p artifacts and checkpoint training hashes remain immutable. No formal data/training/AMD/publication/commit/push.

# QLM-Bench agent guide

## Delivered automated Push Box M0–M6 — QLM-DATA-011

Read docs/scaleup-v1/decisions/automated-synthesis.md and the archived QLM-DATA-011 paired records.
User authorizes ten formal pilots only:2Clean/8Randomized,all train,trace-only actual
CUDA physics then Native OSMesa offline state replay. No forced Recovery quota;
new failures keep lightweight logs,successful traces allow independent render retry.
Preserve historical attempts/P0–P2;do not restore discarded P3 assets. Stop at the
ten-pilot review before100episodes/other tasks. No training/AMD/commit/push/publication.

## Authorized P0–P2 source publication — QLM-DOC-002 / 2026-10-13

P0–P2 implementation commit 5d3c3b7c5d92 is published on this
independent MuJoCo branch with exact remote readback. The user explicitly authorized
this source batch. Read docs/scaleup-v1/work/archive/QLM-DOC-002/plan.md. This supersedes dated local-only statements only for that
source batch. P3 work remains local; original Isaac/main branches and all external
resource/data/model/media publication are outside this authorization.

## Current MuJoCo progress routing — 2026-10-13

Read docs/scaleup-v1/mujoco-progress.md first for phase status. QLM-SIM-013 and
v3/DATA-002 close P0–P2 local engineering; QLM-DOC-001 / v3/DOC-007 reconcile that
completion from chat 01a12ecf-e271-7573-983c-917082cd1c19. Use default LOD a02 and
OSMesa. Diagnostic bundles are not formal demos; P3 pools/pilots/capacity, P4–P6,
AMD and new SFT remain later work. Earlier investigation pauses and incomplete
P2 claims below retain their dated scope. This reconciliation does not start P3
or authorize new execution/publication. Keep existing implementation and receipts.

Read docs/INDEX.md, docs/current/overview.md, docs/current/contracts-v2.md,
 docs/current/publication-v2.md and .agent/PLANS.md. Follow docs/governance/documentation.md
and docs/governance/v2.md. WAM v2 reserves shared adaptation-v2 Work IDs; this repo
mirrors the declaration. QLM-Bench is the current name; RAMBO_Data remains the stable
historical registry/schema identity. Do not rewrite original governance hashes or archives.

The local main checkout is now workspace repos/QLM-Bench under shared-v2/INFRA-004.
Use that path for current runtime/configuration and peer links. Old local paths in
historical manifests, receipts and archived documents remain evidence of their
original attempts, not current filesystem routing. No old-path symlink is retained.

Work on the explicitly selected branch/worktree, verify actual Python import sources,
and use one paired ChangeSpec/ExecPlan for each multi-file work. Commit/PR titles start
with [CATEGORY-NNN]. Keep active plans and evidence current; archive only after gates pass.

QLM owns tasks, Isaac runtime, Go2/RAMBO adaptation, assets, experts, recording,
Raw/Canonical data and model-independent evaluation. CPU qlm_bench core must not import
Isaac, RAMBO controller, WAM, VAE/T5 or model frameworks. Simulator loading is explicit.
WAM owns model processing, normalizers and checkpoints; exchange public contracts only.

Preserve Go2/FL/native9, absolute FL target, original controller, float32 execution,
force-zero, command50Hz/controller100Hz/physics500Hz, dualRGB50Hz and diagnostic observer25Hz.
Preserve authoritative timestamps, completed-interval history and terminal-before-reset.
Task predicates and physics remain unchanged. Recorder does not own episode lifecycle.

The approved refactor removes obsolete biped/15D and nonformal tasks after extracting
shared dependencies; no legacy entry is introduced. Current controller residual/observation
dimensions and checkpoint restoration are not obsolete high-level interfaces.

All published releases, source identities and failed/quarantined attempt evidence stay
immutable. First WAM v2/v3 input remains Push Box DATA-006-20260916T075451Z at
4b5e0ed9aa04cbc1143774798f63171b27d838a7, 50 episodes/40-5-5. Later Lift/Press releases
do not extend those inputs. No new demonstrations or training. Explicit online inference work uses the public
physical-only live protocol described in docs/current/live-inference.md.

Use explicit resource roots and pinned runtime; do not reinstall shared editable bindings.
Local bounded Isaac/GPU regression is authorized by the workspace; keep actual attempts
and not_run explicit. No AMD connection/submission. Remote commit/push/rename/HF publication
uses its own authorization and exact reviewed inventory; historical publication permission
is not reused. Asset redistribution requires confirmed licensing. Run governance, docs,
import boundaries, affected CPU/artifact tests and required simulator regression before handoff.

DATA-002 remains the frozen wam-quadruped-v2.1.0 storage/terminal contract; public
QLM compatibility packaging preserves its original identity and validator.

INFER-001 shared-v2 completion is archived in docs/work/archive/INFER-001/plan.md.
Both original formal SFT WAM consumers completed real synchronous Isaac engineering
numerical/controller trials; read workspace runs/audit/close-loop-20261003/completion.json.
The previous Transformer-GPU/VAE-CPU placement failed the subsequent scene RGB gate.
Effective visual acceptance is withdrawn; current repair/evaluation evidence takes
precedence. Formal benchmark scores remain unavailable.

## Historical visual gate correction — SIM-002 / 2026-10-03

Visual inspection of EVAL-002 found almost-uniform grey ego/task/observer camera
arrays. The earlier INFER-001 task-camera terminal SHA also matches uniform238
RGB. The numerical model/controller/clock/KV/reset evidence remains factual, but
valid scene visual feedback and effective visual closed-loop acceptance are
withdrawn for that original placement. The repair and ten-trial local evaluation
are now completed under shared-v2/SIM-002/EVAL-002 and v3/EVAL-001; see the accepted
local evaluation below. The invalid first batch is preserved and excluded as an infrastructure failure,
without selecting for policy success. Do not publish a success rate from grey-camera
trials. Diagnostic artifacts/preview are in runs/audit/push-box-first-sft-eval-20261003.

## Accepted rendering repair and local evaluation

Read docs/current/push-box-first-sft-evaluation.md and completed paired
INFER-002/EVAL-002/SIM-002 records. Valid actual scene feedback requires
16 original BF16 Transformer blocks using CPU master/CUDA forward and frozen VAE CPU
on the tested16GB host. The old GPU-Transformer/VAE-CPU visual acceptance is withdrawn.
The complete ten-trial nominal-scene metrics and all media are accepted local evidence;
formal benchmark/generalization remain unverified. No source publication is implied.

## Latest inference audit correction — shared-v2/DOC-007

Read docs/current/inference-chain-audit.md. Chunk feedback is implemented, but
clean reset isolation is NOT accepted:9/9 later resets per policy carry the prior
terminal root-link velocity. V3 initial10D and shared RAMBO initial observations
are affected. Preserve6/10 and5/10 only as historical outcomes until reset repair
and rerun. Do not reuse the preceding acceptance paragraph as clean-reset evidence.

## Inference source integration — 2026-10-07

The user authorizes source commit/merge/push under shared-v2/DOC-008. Read
docs/current/inference-source-publication.md for integrated branch routing,
QLM live dependencies and the preserved reset limitation. This publication scope
supersedes prior local-only/source-publication-pending wording for these changes.
The user defers reset repair; do not perform one as part of this batch.

## Local path migration source publication — INFRA-004 / 2026-10-07

After local acceptance, the user explicitly authorized commit/push of the
repo-internal path/tests/docs/governance changes to the existing QLM synthesis
and WAM v2 adaptation targets. This supersedes the earlier local-only publication
exclusion for these changes. Workspace/environment metadata and audit payloads
stay local; v3, feature/reset changes, training, HF and simulator runs remain out
of scope. Exact source/readback receipts: workspace
runs/audit/qlm-local-rename-publication-20261007/.

## Later local reset repair — SIM-003 / 2026-10-07

The user's latest repair request supersedes the earlier deferral for this task.
Current QLM shared reset freshness passed21/21 actual three-task checks, including
controller/public/recorded state and original v3 consumer readback; see
[the accepted reset repair](docs/current/reset-state-freshness.md). The historical70 demonstrations/caches and
6/10 versus5/10 outcomes remain unchanged. No clean full-policy reevaluation or
new demonstration/training/publication is claimed. Use the repaired QLM source revision recorded by DOC-009; historical
serving pins do not include SIM-003.

## Reset source publication — DOC-009 / 2026-10-07

The user explicitly authorized commit/push of reset-related source/docs and the
prerequisite cleanup governance/routing records. Initial exact readback passed for
all five existing targets. Use docs/current/reset-source-publication.md for the
new immutable QLM repair pin; old serving pins remain historical provenance.
No data/model/media/HF publication or new execution accompanies this source batch.

## QLM-only Scale-up v1 — QLM-INFRA-001

The user explicitly scopes current scale-up work to QLM source/data only. Read
[the scale-up foundation](docs/scaleup-v1/README.md) and its independent
[QLM-only registry](docs/scaleup-v1/work-registry.json). Do not allocate these
works in WAM or modify its branches/shared-v2 registry. Historical shared governance
remains unchanged. Ten task plug-ins distinguish planned from ready; new tasks
remain unimplemented until their branch-specific gates pass. Use independent
task worktrees and explicit run60 source binding, not global editable reinstall.
Batch probes are temporary capacity checks, not demonstrations or benchmark evidence.

## Authorized MuJoCo P0–P2 — 2026-10-12

Read docs/scaleup-v1/decisions/mujoco-p0-p2.md. User authorizes local implementation and bounded physical/model
engineering gates on this independent branch. This supersedes historical no-feature/
no-rollout restrictions only for P0–P2. No full data synthesis, training, AMD or
publication. Use new versioned evidence; preserve original resources and checkouts.

## RAMBO verification before asset migration

The latest user request pauses original-task asset migration and requires RAMBO
checkpoint evidence first. Read docs/scaleup-v1/mujoco-foundation.md and archived
QLM-SIM-003. Original P2 procedural assets do not establish faithful migration or
preserved task difficulty; aggregate original-asset acceptance is incomplete. Actual
checkpoint RGB verification has a limited no-fall18s scope and weak yaw tracking.
Do not silently resume asset migration or label prior reconstructed RGB as recordings.

The later independent original-source comparison under QLM-SIM-004 supersedes
the source-of-yaw-error uncertainty: Isaac tracks0.15 with about0.143rad/s;
contact-only MuJoCo diagnostics recover most of the gap. Read the foundation
guide before interpreting this as retraining need or complete adaptation. The
contact3 diagnostic has not replaced the formal profile; migration remains paused.

## Completed local alignment repair — 2026-10-13

The user's latest active goal explicitly authorizes fixing every finding R01–R10
in the comprehensive MuJoCo review. This resumes asset/camera/physics implementation
and supersedes the earlier pause for investigation. Read docs/scaleup-v1/work/archive/QLM-SIM-005/plan.md. Preserve the
frozen action/data/model contracts and all original resources. Earlier complete
claims are historical; require per-finding actual evidence. No training, AMD,
source publication or formal demonstration collection is implied.

Local R01–R10 repairs are now complete with per-finding actual evidence. Read docs/scaleup-v1/mujoco-foundation.md and the
current evidence and workspace runs/audit/mujoco-alignment-repair-v1/report.md.
Box/Basket EGL admission failed the unchanged ROI gates; accepted engineering data
and model sessions use OSMesa. AMD execution, production capacity and formal task
statistics remain unverified. Original assets/weights/records are preserved; no
training, external publication or formal dataset synthesis was performed.

## Current collaborator camera rig — QLM-SIM-006

User selected the procedural support identified in WAM-Policy_Ethan. Read
docs/scaleup-v1/decisions/ethan-camera-rig.md. Current independent packs are
assets/mujoco/original-{task}-v1-ethan-rig-a01 at workspace level; previous a03 packs
and all recorded rollouts remain immutable. Mount/FoV,robot inertia and collision
are unchanged; actual fixed-state comparison verifies camera/three-view RGB.
No new training,inference evaluation,AMD or publication is implied.

## Current supplied STEP support — QLM-SIM-007

The latest user request replaces procedural support with the supplied STEP geometry.
Read docs/scaleup-v1/decisions/step-camera-rig.md. Current three-task packs use
v1-step-rig-a01; historical v1-ethan-rig-a01/v1-a03 and all records remain unchanged.
Source mass/density is unspecified; imported geometry has no mass contribution or
collision. Optical calibration is retained separately from the mechanical shape.
Actual same-state RGB and Native/CUDA checks passed; no new WAM/SFT/AMD/publication.

## Available rendering LOD — QLM-SIM-009

User requested a protected lightweight STEP rendering mesh andObservercomparison.
Read docs/scaleup-v1/decisions/step-rig-rendering-lod.md. Accepted engineering
LOD is v1-step-rig-lod-a02,withfullSTEP/procedural/source preserved. Camera,quality,
mass andcollision settings stay unchanged. Explicit modelselection usesLOD;
current defaultfullSTEP routing is not altered by a compare/generate request.

## Accepted LOD default and local payload cleanup — QLM-SIM-010

The latest explicit user selection supersedes the preceding default-full-STEP
statement. Read docs/scaleup-v1/decisions/mujoco-default-rig.md. Current MuJoCo
runtime/rollout/collection/new-evaluation entries default to v1-step-rig-lod-a02
through a shared pinned model set. Camera/quality/mass/collision are unchanged.
Keep explicit historical overrides and case identities; no silent old-asset fallback.

User authorizes eviction of obsolete local MuJoCo episode/media/state and dependent
caches, a narrow exception to old retention statements. All STEP/old/full/LOD models,
source/CAD intermediates, receipts/scalars, compact comparisons, Isaac references
and original weights/encoders/prompts remain. Removed historical paths describe
original runs, not local presence. Exact receipt: workspace
runs/audit/mujoco-lod-default-cleanup-20261013-v1/.
No new WAM rollout, formal collection, training, AMD, commit/push or publication.

## Current actual default-LOD WAM validation — 2026-10-13

Latest user explicitly authorizes three-task real v3 checkpoint closed loop on
LOD a02 with persisted Ego/task/Observer RGB. Read paired QLM-SIM-011 and
v3/INFER-005 archived plans in the respective local registries. This supersedes
the preceding no-new-rollout wording only for this bounded engineering matrix.
Retain original settings/weights and all new actual attempts/media. No training,
formal demonstrations, AMD, source publication or external uploads. Evidence:
workspace runs/audit/wam-v3-default-lod-rollout-20261013-v1/.

The actual matrix and media readback now pass:6episodes,18original720p videos,
606commands and96frozenRPC waits. Reset/eviction/terminal/source-frame and full
decode gates pass. Allsix short episodes end at the planned horizon,not a task-SR
acceptance. Read current MuJoCo guide and the new evidence review.

## Current full-horizon user request — QLM-SIM-012 / v3-INFER-006

Latest request supersedes the short2.02s scope:one actual rollout per task until
success/fall/24s timeout. Archived paired plans own the runner24s/75group guard and
bounded-memory full event audit. Camera/controller/physics/model parameters remain.
Keep all first outcomes/media; no outcome-selected retries. Evidence:workspace
runs/audit/wam-v3-default-lod-full-rollout-20261013-v1/. No training,formal dataset,
AMD,commit/push or external publication.

Full-horizon actual results:Push timeout24s;Press original displacement-predicate
success5.76s via visually indicated head/front-body contact;Lift timeout24s. No
falls/retries. Press is not an accepted FL skill demonstration. Nine original
videos and all2688command/342RPC freeze/media/reset/terminal gates pass. Read the
current guide,full review and interaction audit before interpreting task success.

## Final local P0–P2 closeout — QLM-SIM-013 / v3-DATA-002

The user requested both tail items and they now pass:three currentLOD diagnostic
Raw/Canonical/frozen VAE/10D readbacks plus Native/CUDA real object-hinge contact,
seeded initial states,zero-step reconstruction/reset,world isolation and RGB sync.
Read current MuJoCo guide and QLM final closeout decision. OSMesa continues by
explicit user decision. User confirms the retained checkpoint is Push Box-only;
Press body/head contact is not a closeout blocker,and the predicate stays unchanged.
Default production params/packs remain;new random state reset is explicit/validated
and nominal reset unchanged. Diagnostic hinge fixture is not a fourth task. Local
P0–P2engineering is complete;P3pilots/pools/production capacity,AMD,SFT and external
publication remain later gates. Evidence:workspace
runs/audit/mujoco-p0-p2-closeout-20261013-v1/. No formal demos/training/commit/push.

M0–M6 completed2026-10-14:ten pilots/4540actions/30videos validated;user review pending.
Use current implementation baseline/report. Stop before100/other tasks.
