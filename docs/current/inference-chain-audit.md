---
id: CURRENT-INFERENCE-AUDIT
type: current
status: accepted
related_work: [DOC-007]
source_map: []
---
# Inference-chain audit: reset-state acceptance withdrawn

The native-aligned chunk feedback loop is implemented and exercised: v2 has483
prediction/execution/Ack pairs and473 ordinary feedback commits; v3 has524 pairs
and514 commits. All986/1068 RPC waits froze physical time. Current WAM source
bindings match the recorded r4 attempts. Model VAE/KV/RNG clearing and ordinary
fresh-feedback paths remain supported by source and actual receipts.

However, each policy has9/9 post-first reset snapshots whose root-link linear AND
angular velocities exactly equal the preceding terminal values. The pinned PhysX
COM velocity setter fails to invalidate the derived root-link velocity cache; the
reset/render path does not advance its timestamp. V3 normalizes these stale values
into its initial10D state, and shared RAMBO initial observations also read them.
The physics velocity write itself is not proven to fail; the confirmed defect is
stale observation/cache freshness at reset.

Withdraw the earlier unqualified reset-isolation/clean-episode acceptance. The
6/10(v2) and5/10(v3) outcomes remain historical observed results, with valid RGB;
they cannot support a clean independent-episode comparison until a simulator-side
repair, bounded reset-state regression and rerun. The quantitative effect on task
success remains unknown. Do not infer corrected metrics or silently edit receipts.

This documentation audit does not change simulator/model code, normalizers, weights,
sampling or old attempts, and adds no training, GPU rollouts, commits or publication.
A new repair work should verify simulator twist, public snapshot, v3 input and initial
controller observation agree at reset without adding a hidden physics warm-up step.

Native comparison uses commit7c6ffa9bfc4b83582cafc860fab4c82cc7deeeeb and its actual
RoboTwin client. Its compute_kv_cache state=action is command history, not v3's10D
measured state. WAM preserves video→action→execute→real-feedback structure while
adapting cameras, native9, chunk/window geometry and synchronous physical timing.
It is not bitwise reproduction of native RoboTwin defaults. Predicted-video/state
quality, counterfactual observation sensitivity, real-time deployment, public
benchmark aggregate and statistical superiority remain not_run/unverified.

Evidence and diagrams: workspace runs/audit/inference-chain-audit-20261003/
(index.html, evidence-audit.json, source-readback.json, delivery-receipt.json).
Archify sequence diagrams pass9/9 deterministic checks, four desktop viewport checks
and actual image review. Historical evaluation receipts stay unchanged.
