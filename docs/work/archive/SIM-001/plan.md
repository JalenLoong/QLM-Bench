---
id: SIM-001
type: exec-plan
status: completed
namespace: adaptation-v2
source_map:
  - source/rambo/rambo/tasks/common/controller_runtime.py
  - source/rambo/rambo/tasks/common/snapshots.py
  - tests/rambo/test_episode_lifecycle.py
---
# Shared environment factory and recorder-independent lifecycle

## Purpose and scope

Implement the approved QLM simulator/runtime boundary while preserving accepted physics, task predicates, controller and data identities. Worktree: the dedicated QLM refactor checkout; registry reservations and final acceptance belong to the root coordinator.

## Progress (Australia/Sydney)

- [x] 2026-10-03: independent worktree and Work ID reserved by the coordinator.
- [x] 2026-10-03: capture source-backed baseline and selected CPU test acceptance (50 tests).
- [x] 2026-10-03: extract environment factory, common deterministic native9 task base, clock/outcome/command ledger and physical/terminal snapshots.
- [x] 2026-10-03: migrate three bounded collector entrypoints to factory/environment time; rewrite teleoperation around the current three tasks and the retained keyboard provider.
- [x] 2026-10-03: bind runtime imports to the active worktree without changing the shared editable installation.
- [x] 2026-10-03: affected CPU suite passes 58 tests; nine original-source/new-source predicate traces match; 17 protected contract/data/camera/predicate files are byte-identical.
- [x] 2026-10-03: first actual Push runtime reached a 32-command timeout with owned pre-reset terminal, then failed explicit reset due to an inference-mode actuator buffer; original overall summary remains failed.
- [x] 2026-10-03: unify execution/reset/state context under torch.inference_mode; 16 context/lifecycle/Recorder/worktree CPU regressions pass.
- [x] 2026-10-03: preserve the original reset/render-before-PPO order; add observer/Recorder attachment callback before the initial reset and explicit resource-ID resolution for duplicate USD-entry hashes. 24 targeted CPU checks pass.
- [ ] Final-source GPU/Isaac retry, recording equivalence and reset/terminal acceptance (root coordinator runs serially).
- [ ] Final governance/doc/integration acceptance and paired archival.

## Discoveries and decisions

The old three task predicates depended on Recorder's tick. With Recorder absent, time remained zero and timeout/success hold failed. Removing this dependency preserves the original Recorder-enabled behavior; it is an explicit lifecycle correction, not a changed success predicate.

The old common package eagerly imported Warp camera code, defeating simulator-free factory/clock imports. Its existing exported names now load lazily. The old editable simulator environment pointed at the baseline checkout; run.sh now replaces caller PYTHONPATH with this worktree's source/rambo, source/crl2 and lightweight src and checks resolved package origins.

All three current task environments use Native9TaskEnv directly. Legacy Object/Button/Pull/Shoot implementations can be removed after extraction. The coordinator owns registry and retired-capability cleanup; the resource agent owns asset preparation/closure/licensing.

The first actual runtime attempt (`runtime-after-push`) produced a passed first 32-command timeout case but an overall `passed: false`: a subsequent explicit reset attempted indexed in-place clearing of an actuator delay buffer created during inference, outside InferenceMode. The context-only fix wraps reset/render/state and the full native9 step in torch.inference_mode, while keeping module imports lazy and preserving the numerical algorithms. Real CPU inference tensors reproduce the affected reset pattern in the new regression tests; state values and context restoration after exceptions are checked. The previous failed summary is immutable and is not promoted to runtime acceptance.

## Current interfaces and recovery

After AppLauncher starts, construct `ControllerRuntime(task_id, profile, resource_root, checkpoint_path=optional, asset_id=optional, on_environment_ready=optional)`; it restores the original RAMBO inference controller. `reset()` returns owned physical/evaluator state, RGB and episode identity; `expert_command()` returns a privileged scripted request/diagnostics; `step(prepare_command(...))` executes up to two 100 Hz controls and returns command confirmation, optional sealed terminal, completed-interval status and authoritative simulation time. `close()` releases the environment. Case reconstruction stays an explicit evaluation adapter responsibility. The environment-ready callback attaches observer/Recorder after construction/foot-geometry setup and before the one original reset/render/PPO initialization; it cannot advance or reset the episode clock. Public collection begins recording after construction without adding another reset. Resource selection prioritizes an explicit argument, then profile.asset_id, then a unique entry SHA; duplicate entry hashes without an ID are rejected. The whole selected manifest inventory and any declared reviewed runtime texture hashes are checked.

The environment exposes episode_tick, simulation_time_ns, task_outcome, current_command_confirmation, executed_command_history and terminal_snapshot. Neither physical/evaluator snapshots nor controller-private observations are automatically policy-visible.

Continue from these sources and the paired ChangeSpec; do not infer state from chat. The bounded historical DATA collectors keep eligibility/provenance rules and current gates. The public generation CLI uses the same runtime through the coordinator's workflow, without treating historical Work IDs as user prerequisites.

## Validation and evidence

Evidence: workspace `runs/audit/v2/SIM-001/20261002T152636Z/{baseline.json,cpu-compatibility.json}`. These are local CPU/source records; W&B status is not_run.

Affected suite: run.sh with pytest over episode lifecycle, worktree runtime binding, collection interfaces, Recorder, three task geometry/predicate modules, teleoperation, run60 launch contract and static imports. Result: 58 passed. Import-boundary script, source AST parsing (36 files), bash syntax checks and simulator-free public help passed. Controller source differs only by the three lifecycle hooks stated in the ChangeSpec.

Actual Isaac/GPU regression now has a failed first attempt and awaits the root coordinator's retry; no new demonstrations, training, AMD connection, HF upload, commit or push was performed by this work package. Learned-policy closed loop and formal benchmark scores remain outside scope.

The first successful post-context runtime retry remains tied to its actual source attempt. Reset count/order was subsequently aligned with the original collector to preserve RNG-dependent actuator lag selection. Final runtime evidence must use the stable callback/resource-resolution source rather than claiming those prior runs validated the final code. The coordinator owns hardware attempt status and source binding.

## Outcomes

Active. Local implementation and CPU compatibility checks are complete; actual-runtime and final integration acceptance have not been claimed.

## Final local acceptance — 2026-10-03

Three actual task runtimes pass recorder on/off, repeated reset, pre-reset terminal and partial fall. Baseline/refactor terminal states, commands and timestamps match exactly; renderer pixels are not claimed byte-identical. Public diagnostic collection passes actual Raw/Canonical/media validation.
Evidence: versioned workspace runs/audit/qlm-refactor-20261003. No new usable
demonstrations, training experiment, AMD connection, remote publication or model
artifact modification. Source commits/merge/push remain pending review authorization.
