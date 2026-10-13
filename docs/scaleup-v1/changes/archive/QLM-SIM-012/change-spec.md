---
id: QLM-SIM-012
type: change
status: completed
source_map: []
---

# Three single full-horizon real WAM v3 rollouts on default LOD

User explicitly replaces the short2.02s scope with one actual rollout per Push Box,
Press Button and Lift Basket,ending on actual success/fall or24s timeout. Partner
works:QLM-SIM-012 and v3/INFER-006. Preserve default LOD a02 pinned resources,
CUDA-MJWarp/Native OSMesa,original real v3 step1000 model,normalizers,task-correct
prompts,VAE,sampling/window8/offload16,all camera/quality/mass/collision/controller
settings. Seed42 and the same nominal task profiles are retained.

Only increase the live runner horizon admission from3s to24s and ensure its chunk
execution guard covers all1200possible50Hz commands (75groups);this is not a model
window or physics parameter change. Fail closed on undersized execution budgets.
Run GPU tasks serially. One first attempt per task,without outcome-based retries.
Retain failure evidence; never force success or modify task predicates. Success/fall
can end before24s. No training,formal demonstration synthesis,AMD,upload/commit/push.

Acceptance: each actual task has a terminal success/fall/timeout result within24s;
checkpoint/source/default-profile identity and unchanged configs;allRPC waits freeze
physics/controller/time;actual three-view720p videos with authoritative50Hz policy
and25HzObserver frames,plus true terminal PNG even for100Hz partial-interval falls.
Actual command prefixes/unexecuted tails and task outcome predicates must agree.
Complete media decode/hash/reset/clock checks and playable local/native previews.
Evidence:workspace runs/audit/wam-v3-default-lod-full-rollout-20261013-v1/.

## Actual completion

One first-attempt per task completes on original configs/defaultLOD. Push24s
timeout1200commands;Press5.76s original-predicate success288commands;Lift24s
timeout1200commands. No falls or outcome retries. All2688commands/342RPC waits,
9original720p MP4s,terminal/reset/frame/hash/full-decode gates pass.

Actual Press terminal shows head/front-body contact with the cap and FL below;
16.55mm displacement satisfies the unchanged predicate but does not validate FL
pressing skill. press-interaction-audit.json and actual raw footage preserve this
qualification. No collision/predicate/model/control/camera changes or hidden retry.

Six runner guard/import CPU tests pass. Controller/physics/render source hashes
and all model/prompt configs match the previous run. First action chunk matches;
GPU trajectories are not claimed bitwise deterministic (first2.02s max root delta
75.68micrometers). Live guard and event-memory policy are the only runner changes.
Wall runtime:Push997.65s,Press232.98s,Lift1465.52s. Not a throughput benchmark.

Review/three full previews and nine raw videos remain local;no training,formal
Demonstrations,AMD,commit/push or external publication. Native in-conversation
video delivery avoids the known automated local-file browser limitation.
