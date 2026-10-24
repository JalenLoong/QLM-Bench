---
id: OPD-011
type: exec-plan
status: completed
source_map: []
---
# HF dataset owner migration

User authorizes replacing the old dataset network location with AIGeeksGroup/QLM-Bench.
Current scope is the two quadrupedal OPD worktrees. Preserve immutable catalogue/DataRef/revision/manifest
identities and actual checkpoint,pool,model,data bytes;do not rewrite historical run receipts.
Use an explicit known-owner alias only at transport/compatible metadata boundaries.
No AMD,actual training,Slurm,full5B,HF upload/model publisher implementation,commit/push or other services.

- [x] Inspect old dataset references and distinguish historical identity from network addresses.
- [x] Read-only new-repo metadata/fixed-revision verification.
- [x] Migrate active network entrypoints/defaults and add CPU tests.
- [x] Verify old frozen inputs stay valid;docs/import/governance and CPU checks.
- [x] Archive paired work and explain actual OPD local checkpoint/export paths.

Evidence: workspace runs/audit/opd-v4-hf-dataset-owner-migration-20261025-v1/.

Completed evidence and exact scope: [current report](../../../current/opd-v4-hf-dataset-011.md).
