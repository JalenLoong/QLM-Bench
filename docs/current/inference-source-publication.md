---
id: CURRENT-INFERENCE-SOURCE-PUBLICATION
type: current
status: accepted
related_work: [DOC-008]
source_map: []
---
# Integrated inference source and known limits

The user authorized commit/fast-forward integration and GitHub push on2026-10-07.
WAM v2/v3 integrate into their corresponding adaptation branches independently;
QLM integrates into synthesis/v2_9D-action_ego+task-centric_camera. Temporary
inference worktrees remain local evidence/source bindings, not enduring public branches.
Publication state and exact remote identities are recorded by this work's plan and
workspace runs/audit/inference-publication-20261007/completion.json after readback.

The user explicitly defers the known reset velocity-cache issue. Core chunk feedback
remains implemented and exercised; the9/9 post-first reset carryover per policy remains
an acknowledged limitation. Source integration does not claim a reset fix, new rollout,
formal benchmark score or validated comparative benefit. Existing6/10 and5/10 outcomes
remain observations of the tested configuration. Original models, normalizers, data
pins and attempt/media evidence are unchanged. No assets/results/weights are uploaded.

The historical QLM0.1.0 CPU wheel predates qlm_bench.live. Online consumers must use
this integrated QLM source with its live optional dependencies; do not silently load
that old wheel for serving. Training/resume provenance and its original artifact
identities are preserved. Pin the QLM serving source commit in each deployment.

```bash
git clone --branch synthesis/v2_9D-action_ego+task-centric_camera \
  https://github.com/JalenLoong/QLM-Bench.git QLM-Bench
python -m pip install -e './QLM-Bench[live]'
```

The physical runtime uses QLM's scripts/rambo/run60.sh from the selected clone,
explicit simulator dependencies, resource root and checkpoint identities. Policy
processes consume only the public QLM module and remain independent of Isaac/RAMBO.
See the existing branch-specific live guide for reset/predict/feedback/end contracts.
On the tested16GB host, retain explicit16 original Transformer blocks with CPU master
parameters/CUDA forward and original frozen VAE CPU; CFG1/window8/5-10steps remain.

Evaluation result tables also require the QLM data extra in the result-writing
interpreter. If the pinned simulator interpreter lacks PyArrow, select the separate
data interpreter with --results-python; do not modify the simulator lock to publish
these changes. Raw RGB sent to the policy is independent of diagnostic MP4 encoding.
