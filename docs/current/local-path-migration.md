---
id: CURRENT-LOCAL-PATH-MIGRATION
type: current
status: accepted
related_work: [INFRA-004]
source_map:
  - configs/lift_basket_v2.json
  - source/rambo/config/extension.toml
---
# Local main-checkout path

The user-approved 2026-10-07 INFRA-004 migration changes the workspace main checkout
from `repos/RAMBO_Data` to `repos/QLM-Bench`, without a compatibility symlink. The
GitHub remote already uses QLM-Bench and is not changed by this local task.

Current workspace routing, the legacy Lift config's asset location, installed
RAMBO/CRL2 editable metadata and current peer-document links use the new path.
Runtime wrappers derive the selected checkout from their own location. Other
worktree directories and the QLM data environments' refactor bindings are retained.

`RAMBO_Data` remains the frozen registry participant/schema authority. Historical
manifests, receipts, paired archives, source/resource hashes and earlier lock-stage
paths remain unchanged. WAM v2's document checker resolves only archived links
under the retired main-checkout root to the same relative target under QLM-Bench;
current links and genuinely missing targets receive no such fallback.

Actual checks and completion state are recorded in workspace
`runs/audit/qlm-local-rename-20261007/` and the paired INFRA-004 records. No package
upgrade, public interface change, reset repair, training, collection, simulator
rollout, remote operation, commit or push is part of this task.

## Later source publication

The user subsequently authorized this work's source commit/push to the existing
QLM synthesis and WAM v2 adaptation branches. This supersedes the original
local-stage publication exclusion only for repo-internal path/tests/docs/governance
changes. Workspace configuration, installed editable metadata and local audit
payloads stay local. Original migration receipts remain historical; source
publication receipts live in workspace
`runs/audit/qlm-local-rename-publication-20261007/`.
