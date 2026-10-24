---
id: OPD-V4-PORTABILITY
type: current-design
status: accepted
source_map:
  - src/qlm_bench/backends/mujoco/training_pool.py
---
# OPD-003 host portability

Locations are separate from model/data identity. Explicit path relocation never changes
approved checkpoint,normalizer,prompt or pool content hashes. Prompt identity excludes
its path; frozen encoder identity uses canonical consumed-file hashes instead of the
auxiliary manifest's formatting. Timeouts and checkpoint cadence are operational and do
not change learner identity. Algorithm/world/source bindings remain strict.

Config-relative resources resolve against the config directory; reference-config paths
resolve before configure copies them. Interpreter symlinks remain intact. relocate
reports both mapped and unmapped paths. Supply target-native Python environments and
software GL libraries; copying a local CUDA virtualenv or Ubuntu shared libraries is not
an AMD installation procedure. Preflight is not a full-model/target-training acceptance.

The prepared QLM pool is self-contained at runtime. Absolute scene paths in authenticated
trace provenance are historical text,not runtime reads. Re-preparing on another host
uses resource-map. Changing inode/mtime or losing internal hardlinks does not invalidate
content identity,although a plain expanded copy needs about126.2GiB instead of1.26GiB.
Preserve internal hardlinks with an archive or rsync -aH; do not dereference them blindly.

No .git metadata or original checkout path is required for runtime. Current code is
uncommitted: git archive HEAD/remote checkout alone omits the implementation. Transfer
the actual reviewed working-tree runtime bundle and verify its source manifest.

Evidence: workspace runs/audit/opd-v4-portability-review-20261022-v1/.
Actual AMD/ROCm/RCCL/full5B/eight-stream behavior remains not_run. Old admission receipts
cannot be reused after source changes. No GPU,AMD,physics,commit/push in this review.
