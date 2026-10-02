# QLM-Bench agent guide

Read docs/INDEX.md, docs/current/overview.md, docs/current/contracts-v2.md,
 docs/current/publication-v2.md and .agent/PLANS.md. Follow docs/governance/documentation.md
and docs/governance/v2.md. WAM v2 reserves shared adaptation-v2 Work IDs; this repo
mirrors the declaration. QLM-Bench is the current name; RAMBO_Data remains the stable
historical registry/schema identity. Do not rewrite original governance hashes or archives.

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
do not extend those inputs. No new demonstrations, training or learned-policy bridge.

Use explicit resource roots and pinned runtime; do not reinstall shared editable bindings.
Local bounded Isaac/GPU regression is authorized by the workspace; keep actual attempts
and not_run explicit. No AMD connection/submission. Remote commit/push/rename/HF publication
uses its own authorization and exact reviewed inventory; historical publication permission
is not reused. Asset redistribution requires confirmed licensing. Run governance, docs,
import boundaries, affected CPU/artifact tests and required simulator regression before handoff.

DATA-002 remains the frozen wam-quadruped-v2.1.0 storage/terminal contract; public
QLM compatibility packaging preserves its original identity and validator.
