---
id: EVAL-001
type: change
status: completed
namespace: adaptation-v2
source_map:
  - src/qlm_bench/policy_interface/physical.py
  - src/qlm_bench/tasks/spec.py
  - src/qlm_bench/evaluation/cases.py
  - src/qlm_bench/evaluation/runner.py
  - src/qlm_bench/evaluation/results.py
  - src/qlm_bench/backends/isaac/adapter.py
  - tests/qlm/test_evaluation_interfaces.py
---
# Policy-independent evaluation infrastructure

## Intent and observable behavior

Policy-independent evaluation infrastructure; implementation follows the user-approved QLM refactoring plan.

The public interface provides one physical native9 command per completed 20 ms
interval. It preserves requested values, float32 execution conversion and force-zero
enforcement, and admits only confirmed complete intervals into episode-local history.
It does not impose WAM's 16-command model grouping. Observation profiles explicitly
select dual RGB and optional root-link physical state; controller/evaluator-private
state and EvalCase goals are not passed to action providers, including reset callbacks.

EvalCase records bind initialization, assets, goal, cameras, runtime/controller,
seed, reset procedure and provenance. Verified cases require actual reconstruction
evidence. Protocols require explicit expected trials, command budget, error denominator
and retry selection. Draft protocols and engineering fixtures produce diagnostics,
never a formal benchmark score. Results preserve failed/error/not-run trials and
explicit retry chains. Fixtures remain local-only and cannot be published.

The lazy Isaac adapter consumes the shared environment factory and requires explicit
reconstruction, observation, controller-advance and terminal bindings. This does not
implement a learned-policy server or live network transport. Existing task predicates
remain in their accepted implementations; pure TaskSpec references their identities
without creating new task thresholds.

## Compatibility and non-goals

Preserve native9/force-zero, controller and task semantics, immutable schemas, published data and WAM inputs. No training, new demonstrations, AMD access or remote publication.

## Evidence threshold and acceptance scenarios

Governance and import checks, affected unit/integration tests, actual artifact checks and required runtime regression are recorded separately.

CPU acceptance covers private-state isolation, declared state frames, force-zero and
float32 conversion, partial/duplicate/stale acknowledgements, case/protocol admission,
complete trial tables, retry/error denominators and actual local Parquet round-trip.
Fixture outcomes are schema/engineering evidence only. Real Isaac/task/controller
regression remains a separately recorded gate and cannot be replaced with these tests.

## Migration and rollback

Work in the dedicated branch/worktree. Keep source artifacts immutable and record source-to-target mapping. Revert reviewed changes without rewriting history.

## Final local acceptance — 2026-10-03

CPU interfaces/completeness/privilege tests pass; the public runner executes one actual32-command Isaac diagnostic trial with owned terminal and no formal score/publication eligibility.
Evidence: versioned workspace runs/audit/qlm-refactor-20261003. No new usable
demonstrations, training experiment, AMD connection, remote publication or model
artifact modification. Source commits/merge/push remain pending review authorization.
