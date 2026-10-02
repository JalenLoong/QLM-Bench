---
id: EVAL-001
type: exec-plan
status: completed
namespace: adaptation-v2
source_map:
  - src/qlm_bench/policy_interface/physical.py
  - src/qlm_bench/evaluation/runner.py
  - src/qlm_bench/evaluation/results.py
  - tests/qlm/test_evaluation_interfaces.py
---
# Policy-independent evaluation infrastructure

## Purpose and scope

Policy-independent evaluation infrastructure.

## Context and milestones

Follow the approved P0/A/B/C stage ordering; peer registry writes are serialized by WAM v2 authority.

## Progress (timestamped)

- [x] 2026-10-03: baseline verified; independent worktree created; Work ID reserved.
- [x] Implementation and affected checks passed.
- [x] Required local artifact/runtime evidence and handoff recorded.

- [x] 2026-10-03: implemented explicit physical observation/action interface,
  pure TaskSpec, EvalCase/protocol admission, complete-trial runner and result validator,
  local Parquet writer, constant-command example and lazy Isaac adapter bindings.
- [x] 2026-10-03: first CPU suite passed 23 tests, including a real local Parquet
  serialization/readback. These are engineering fixtures and are never publishable.
- [x] 2026-10-03: new EpisodeRuntime integration, concrete fixed-controller adapter,
  terminal isolation across auto-reset and the EVAL suite passed 26 CPU tests.
  Combined public core/evaluation/resource tests passed 42 tests. Repository docs
  and import-boundary checks passed separately.
- [ ] Required actual Isaac/task/controller regression, owned by the main workstream.

## Discoveries and decision log

User approved independent refactoring branches, in-place future GitHub rename, full retired-capability cleanup, and independent v3 category numbering.

Observation profiles retain the existing Canonical root-link field names, unit xyzw
orientation, world-frame velocities, body-frame projected gravity and explicit ground
reference. WAM v2 can select no state fields; WAM v3 owns the unchanged body-frame 10D
derivation and normalizers. Provider reset receives only a public ProviderContext,
not the privileged EvalCase initialization or goal.

The old common package eagerly imported camera/warp while importing EpisodeRuntime;
SIM-001 corrected that package routing and the shared CPU integration now passes.
Result publication under DATA-012 reuses validate_result and honors its
publishable flag. No formal suite, horizon or seed count was invented.

ControllerRuntimeAdapter maps the existing fixed RAMBO runtime's actual confirmed
command and owned terminal snapshot into the public interface. An explicit EvalCase
reconstruction callback remains required. Sensor names are mapped without modifying
RGB pixels; physical root-link state values are unchanged. The adapter rejects feedback
from an auto-reset episode in the previous rollout. This is separate from any future
learned high-level policy transport.

A later global docs check during parallel retired-script removal found the upstream
provenance page still pointing at the removed preview-lift-cameras script. That
unrelated routing correction belongs to the source-cleanup workstream; the final
global check must be rerun after it is corrected. EVAL's affected CPU suite and the
import-boundary check passed after the final interface validation changes.

## Validation and not_run

Baseline and check logs live in the versioned workspace audit layer. Remote publication, training, learned-policy closed loop and formal benchmark score are not_run/not_required. W&B not_run for local CPU checks.

Affected CPU command: `PYTHONPATH=src $POLICY_PYTHON -m pytest -q
tests/qlm/test_evaluation_interfaces.py`, with the workspace policy/data interpreter.
No GPU, actual Isaac rollout, AMD connection, training, HF upload, commit or push was
performed by this implementation subtask. The active work is not archived while the
separate runtime and final acceptance gates remain pending.

## Recovery

Resume from this branch, registry, paired ChangeSpec and audit manifests; do not depend on chat history.

## Outcomes and retrospective

Local implementation and acceptance complete. External publication is separately gated.

## Final local acceptance — 2026-10-03

CPU interfaces/completeness/privilege tests pass; the public runner executes one actual32-command Isaac diagnostic trial with owned terminal and no formal score/publication eligibility.
Evidence: versioned workspace runs/audit/qlm-refactor-20261003. No new usable
demonstrations, training experiment, AMD connection, remote publication or model
artifact modification. Source commits/merge/push remain pending review authorization.
