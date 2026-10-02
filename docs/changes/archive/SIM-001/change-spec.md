---
id: SIM-001
type: change
status: completed
namespace: adaptation-v2
source_map:
  - source/rambo/rambo/tasks/common/environment_factory.py
  - source/rambo/rambo/tasks/common/episode.py
  - source/rambo/rambo/tasks/direct/rambo_quadruped/native9_task_env.py
---
# Shared environment factory and recorder-independent lifecycle

## Intent and observable behavior

Collection, evaluation action providers and teleoperation use one environment factory and the fixed RAMBO execution path. Push Box, Lift Basket and Press Button derive directly from the common native9 task runtime. The environment owns episode-local time, task predicates, timeout, outcome, confirmed command history, terminal capture and reset; Recorder only consumes actual execution/state events.

`EpisodeClock` takes completed PhysX steps and an episode origin. Each controller acknowledgement is five 2-ms steps; only a completed ten-step high-level hold enters executed history. Partial terminal commands stay explicit and do not enter completed history. Terminal state/RGB/identity/outcome are copied before auto-reset and remain available as the preceding episode's sealed snapshot.

Ordinary factory/episode imports and teleoperation help do not start Kit. Runtime launch binds source to the active worktree without reinstalling the shared interpreter. New resource lookups use the exact asset SHA through the public registry and an explicit resource root. Current public teleoperation exposes three tasks and the retained keyboard/sensitivity controls; retired Button/M8/press-smoke flows are removed.

## Compatibility and non-goals

Keep the fixed controller/checkpoint, original task geometry/predicates, desired force zero, native9 order/float32 semantics, RGB mounts and 50/100/500 Hz cadence. `task_kind=lift_basket` is the existing mounted-camera configuration label, independent of which of the three task predicates runs. Published profile/spec bytes, data/checkpoint manifests and provenance remain immutable. Internal bounded DATA collection gate receipts retain their historical meaning; they are not requirements for a new user's public data generation workflow.

No high-level learned-policy server, transport, training, new demonstrations, task-result publication, simulator upgrade or controller redesign is included.

## Evidence threshold and acceptance scenarios

- Compare all three actual predicate methods with the original recorded-source baseline for success, timeout and fall traces.
- Test Recorder on/off equivalence, unique 50 Hz hold boundaries, confirmed-only history, partial terminal, owned terminal copies, and consecutive reset isolation.
- Check factory/episode/teleop help import boundaries and real interpreter source paths; run affected CPU tests and shell/source parsing checks.
- Keep original controller source unchanged except pre-control validation, completed-control acknowledgement and pre-reset terminal hooks; assert original contracts/dataset specs, camera rig and geometry helpers remain byte-identical.
- Require actual fixed-controller/task/assets/RGB runtime regressions separately before final acceptance. CPU synthetic checks do not claim actual PhysX or renderer validation.

## Migration and rollback

Work only in the dedicated QLM branch/worktree. New source mappings and actual run attempts belong in the versioned audit layer. Revert source changes if runtime regression fails; do not restore by editing frozen datasets/specs, changing checkpoint hashes or rewriting old receipts. Archive paired work documents only after the root coordinator confirms required evidence.

## Final local acceptance — 2026-10-03

Three actual task runtimes pass recorder on/off, repeated reset, pre-reset terminal and partial fall. Baseline/refactor terminal states, commands and timestamps match exactly; renderer pixels are not claimed byte-identical. Public diagnostic collection passes actual Raw/Canonical/media validation.
Evidence: versioned workspace runs/audit/qlm-refactor-20261003. No new usable
demonstrations, training experiment, AMD connection, remote publication or model
artifact modification. Source commits/merge/push remain pending review authorization.
