---
id: DOC-007
type: exec-plan
status: completed
source_map: []
---
# Inference-chain audit and reset acceptance correction

## Scope
User-requested Archify diagrams and native LingBot-VA comparison. Read existing source
and actual r4 receipts, publish local audit artifacts, and correct current context.
Runtime implementation, weights and original receipts remain unchanged. No new GPU
rollouts, training, commits/pushes or external publication are performed.

## Progress
- [x] Compare pinned native7c6ffa9 server and official RoboTwin client with WAM.
- [x] Match every prediction/execution/feedback pair in existing r4 logs.
- [x] Confirm root-link reset velocity carryover at9/9 boundaries per policy.
- [x] Locate missing root-link velocity cache invalidation in the pinned PhysX setter.
- [x] Deliver checked diagrams, audit report, corrected current context and indexes.

## Discoveries / Decision Log
Chunk feedback genuinely executes, with483/524 chunks and473/514 ordinary feedback
commits. However root-link velocities at each subsequent reset exactly match prior
terminal values. The COM velocity setter does not invalidate derived root-link velocity;
reset/render does not advance the cache timestamp. V3 encodes the stale values into10D;
RAMBO initial observations in both policies also read the same source. Withdraw clean
reset-isolation acceptance and unqualified comparison; retain6/10 and5/10 as historical
observations. A separate simulator repair and bounded reset regression are required
before rerunning the declared evaluation. Do not infer a corrected success rate.

## Validation / Recovery
Read-only evidence: runs/audit/inference-chain-audit-20261003/evidence-audit.json.
Current WAM source bindings match the actual attempts; no checkpoint payload rehash.
Archify deterministic validation, browser measurements and perceptual review are
recorded separately. Previous evaluation attempts and completion receipts are immutable.

## Outcome
Audit and checked diagrams delivered; reset repair remains separate required work.
