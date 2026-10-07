---
id: CURRENT-RESET-STATE-FRESHNESS
type: current
status: accepted
related_work: [SIM-003]
source_map: []
---
# Accepted local reset-state freshness repair

On 2026-10-07 the user requested the previously deferred repair. QLM's shared
QP reset path now invalidates the pinned PhysX derived root-link velocity and
state caches after the unchanged COM/joint writes, before controller observation.
It neither substitutes zero snapshots nor advances physics time. Pinned third-party
source, physical contracts, controller, task predicates and cameras are unchanged.

## Actual acceptance

Three real nominal tasks (Push Box, Lift Basket, Press Button) each passed startup,
three manual resets and three automatic timeout resets:21/21 checks. Independent
PhysX root COM twist, its root-link conversion, public snapshot and controller
velocity agree with zero maximum absolute error. All nine manual resets preserve
global physics step, backend timestamp and controller step count. Every task has
three0.32s engineering episodes, with a first recorded16-command/17-boundary trace;
terminal state/RGB remains owned before reset and actual scene RGB is valid.

Original frozen v3 normalization and selector pass21 physical-state readbacks;
three actual Push Box cold-start RGB/state packets pass the existing v3 live
pipeline. No Transformer/VAE model was loaded by this repair check. Three local
engineering Raw/Canonical bundles pass existing validators; Canonical first-frame
velocity is zero. These bundles are diagnostic_only and are not demonstrations.
Timeout maps to the frozen schema's failure status while terminal.reason remains
timeout; source captures/attempts and all failed diagnostic/packaging attempts remain.

Evidence: workspace runs/audit/reset-state-freshness-20261007/completion.json,
consumer-readback-v1.json, packaging-v2/acceptance.json and accepted-*-r3/report.json.
The negative control disables only cache invalidation and reproduces stale public/
controller velocity with direct simulator COM velocity zero at all three reset types.

## Historical data and evaluation limits

The historical70 published demonstrations, model caches, normalizers, checkpoints
and6/10 versus5/10 outcomes retain their original bytes and provenance. Runtime
repair does not correct their first-frame state or establish revised success rates.
A new versioned data/cache correction and a clean learned-policy evaluation remain
separate future work. No new demonstration, full SFT rollout, formal benchmark,
training, AMD access, remote publication, source commit or push was performed.

## Runtime and recovery

Current QLM source is required; old source pins and the historical CPU wheel do
not acquire this repair automatically. V2 was restored at its preserved adaptation
branch for shared governance/CPU checks, with the INFRA-005 authority patch applied.
Current workspace default routing still selects the retained v3/QLM sources.
The compatibility guard fails on an unsupported cache layout instead of continuing
with stale observations. Keep actual runtime gates when changing the pinned backend.

## Later authorized source publication — DOC-009 / 2026-10-07

The user subsequently authorized source commit/push. All five GitHub targets were
verified at the new source commits; use [the published source pin](reset-source-publication.md).
The preceding no-commit/publication statements retain the local SIM-003 scope.
Source publication does not modify old data/models/cache/metrics or rerun the policy.
