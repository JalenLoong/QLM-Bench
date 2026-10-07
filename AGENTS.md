# QLM-Bench agent guide

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
