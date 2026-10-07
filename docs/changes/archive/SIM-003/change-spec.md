---
id: SIM-003
type: change
status: completed
namespace: adaptation-v2
source_map: []
---
# Reset-derived velocity freshness repair

## Authorization and scope

On 2026-10-07 the user explicitly requested the reset repair, superseding the
prior deferral for this task. QLM owns implementation; WAM v2 participates in
shared governance and consumer documentation. Restore the preserved v2 branch
and apply the completed INFRA-005 authority patch before allocation.

## Observable behavior and invariants

After startup/manual/automatic reset, root-link velocity and controller/public/
recorded state must reflect the simulator reset velocity, with no hidden physics
step or clock change. Retain COM setter semantics, native9/force-zero, original
controller, task predicates, cameras and all physical rates. Invalidate derived
backend caches in QLM; do not edit pinned third-party source or invent zero observations.
Old datasets/checkpoints/caches/metrics remain immutable. No new demonstrations,
training, full evaluation rerun, remote access, publication or commit/push.

## Acceptance and progress

- [x] Read reset setter/accessors and restore shared allocation authority.
- [x] Implement narrow reset-cache invalidation and meaningful regression tests.
- [x] Run bounded actual Isaac/controller reset checks for all three tasks.
- [x] Compare direct simulator twist, root-link/body state, controller observation,
      public snapshot and recorder boundary; preserve terminal before reset and RGB.
- [x] Validate exported snapshots with existing v3 10D selector/frozen normalizer.
- [x] Run affected CPU, docs/governance/import checks; archive paired records.

Evidence uses new attempts under workspace runs/audit/reset-state-freshness-20261007/.
Actual attempt manifests are created only when execution starts. Source checks,
synthetic tests and hardware evidence remain distinct; W&B upload is not_run.

## Recovery

Preserve all failed attempts. Revert only this work's diff to recover source;
restored INFRA-005 governance and pre-existing changes must remain intact.

## Actual results and discoveries

21/21 actual reset checks pass with zero simulator/public/controller velocity error;
three Raw/Canonical engineering bundles and21 frozen-normalizer state checks pass.
Three actual Push cold-start packets pass v3 LiveObservationPipeline. Negative
control reproduces all reset failures. No hidden physics advancement or source/data
publication. Earlier script import/clock errors, float32 pose bit-equality failures,
incomplete diagnostic boundary capture and timeout enum packaging failures are
preserved. Final hardware attempts accepted-*-r3 retain16 commands/17 boundaries.
Packaging-v2 maps timeout to the unchanged failure enum in a versioned diagnostic
derivative, keeping source capture state/action/media unchanged. The final diagnostic
script uses that status mapping; the core runtime repair is identical to tested source.
Affected CPU41 tests pass; v2 required130 pass/20 fixture skips; v3 required57 pass.
Socket-only sandbox failures passed individually outside sandbox, with originals
retained. W&B upload/model execution/full SFT evaluation remain not_run.
