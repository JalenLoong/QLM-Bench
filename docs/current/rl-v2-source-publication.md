---
id: QLM-BENCH-RL-V2-SOURCE-PUBLICATION
type: current-design
status: accepted
source_map: []
---
# RL-v2 source publication — 2026-10-26

The user-authorized implementation, independent audit fixes, Push/Sweep dual-task
scripts, W&B/HF support and administrator documentation are published on
`rl/v2_GT-guided_chunk-level_close-loop_NFT` in both repositories.

Verified implementation commits:

- WAM: `e68e83f3d400b7b1bf6804f0411b85af50292cf6` at both AIGeeksGroup/WAM-Policy and JalenLoong/WAM-Policy.
- QLM: `38471cb58b4d322809999b38dd3e37811f82b575` at JalenLoong/QLM-Bench.

Each target was fetched into its own bare Git object database with no alternates.
Complete commit/tree and all blob bytes matched local Git objects. This release-status
closure follows the implementation commits; pull the branch HEAD for all documentation.
The final HEAD and readback receipts are recorded in workspace
runs/audit/rl-v2-source-publication-20261026-v1/completion.json.

Administrators can clone or fast-forward pull the two branches and follow the WAM
README to configure the two tasks and submit the16-job DAG with one shared smoke pair.
The required target environments and model/data/scene/controller resources remain
explicit prerequisites; source delivery does not install or bundle those payloads.

Runtime files retain the accepted local test identities. This operation did not connect
to AMD, submit Slurm, run formal RL/validation or upload HF/W&B model/data payloads.
Earlier uncommitted/unpushed statements remain evidence of their original local scope.
